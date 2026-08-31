# Phase 5 - dynamic restriction ingestion + query surface.
#
# RestrictionSourceAdapter instances model OFFICIAL feeds (NAVAREA/NAVTEX,
# coastguard temporary closures, exercise zones).  refresh() upserts
# idempotently (natural key source + source_record_id), then expires anything
# a source stopped publishing so expirations never linger in the active view.
# The service is DB-free by default (in-memory store) and stays the same shape
# when a Postgres-backed store is swapped in.
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

from app.models.common import utcnow
from app.models.dynamic_restrictions import DynamicRestriction
from app.services.dynamic_restriction_store import (
    DynamicRestrictionStore, InMemoryDynamicRestrictionStore)
from app.services.geofence_catalog import GeofenceCatalog, get_geofence_catalog
from app.services.geospatial_service import point_in_polygon


class RestrictionSourceAdapter(Protocol):
    def source_name(self) -> str:
        ...

    async def fetch(self, now: datetime) -> List[DynamicRestriction]:
        ...


def _box(lat: float, lon: float, span_deg: float = 0.5) -> Dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[
            [lon - span_deg, lat - span_deg],
            [lon + span_deg, lat - span_deg],
            [lon + span_deg, lat + span_deg],
            [lon - span_deg, lat + span_deg],
            [lon - span_deg, lat - span_deg],
        ]],
    }


class NavareaAdvisoryAdapter:
    """NAVAREA-VII style advisory feed (deterministic given `now`).

    Demonstrates official advisories with validity windows; the window rotates
    by day-of-year so live demos show both active and expired states over time.
    """

    def source_name(self) -> str:
        return "navarea"

    async def fetch(self, now: Optional[datetime] = None) -> List[DynamicRestriction]:
        now = now or utcnow()
        day = now.toordinal() % 3
        candidates = [
            DynamicRestriction(
                source="navarea",
                source_record_id=f"NAVAREA-2026-{100 + day}",
                restriction_id=f"navarea-2026-{100 + day}",
                name=f"Naval exercise zone {day + 1} (off Mumbai)",
                restriction_type="naval_exercise",
                severity="high",
                geometry=_box(18.5 + day * 0.4, 72.0 + day * 0.3),
                valid_from=now - timedelta(hours=6),
                valid_until=now + timedelta(days=1),
                issued_at=now - timedelta(hours=8),
                official=True,
                description="Exercise activity reported by the zone authority; "
                            "vessels advised to keep clear.",
                metadata={"zone": f"exercises/{day + 1}", "cadence": "daily"},
            ),
            DynamicRestriction(
                source="navarea",
                source_record_id="NAVAREA-2026-002",
                restriction_id="navarea-2026-002",
                name="Submarine operation - Arabian Sea",
                restriction_type="submarine_operation",
                severity="critical",
                geometry=_box(16.0, 71.0),
                valid_from=now - timedelta(hours=24),
                valid_until=now + timedelta(hours=30),
                issued_at=now - timedelta(days=1),
                official=True,
                description="Submarine operations; navigation restricted.",
                metadata={"zone": "sub_ops/02"},
            ),
        ]
        return candidates


class TemporaryClosureAdapter:
    """Coastguard temporary fishing-expedition closure feed (official)."""

    def source_name(self) -> str:
        return "coastguard"

    async def fetch(self, now: Optional[datetime] = None) -> List[DynamicRestriction]:
        now = now or utcnow()
        return [
            DynamicRestriction(
                source="coastguard",
                source_record_id="COASTGUARD-TC-221",
                restriction_id="coastguard-tc-221",
                name="Temporary fishing closure - Gulf of Mannar approach",
                restriction_type="firing_exercise",
                severity="moderate",
                geometry=_box(8.9, 79.0, 0.35),
                valid_from=now - timedelta(hours=2),
                valid_until=now + timedelta(hours=6),
                issued_at=now - timedelta(hours=3),
                official=True,
                description="Temporary closure for scheduled exercise; "
                            "fishing boats advised to stand off.",
                metadata={"notice": "CG/2026/221"},
            ),
        ]


class DynamicRestrictionService:
    def __init__(
        self,
        store: Optional[DynamicRestrictionStore] = None,
        catalog: Optional[GeofenceCatalog] = None,
        adapters: Optional[List[RestrictionSourceAdapter]] = None,
        refresh_grace_seconds: int = 6 * 3600,
    ) -> None:
        self.store = store or InMemoryDynamicRestrictionStore()
        self.catalog = catalog or get_geofence_catalog()
        self.adapters = adapters if adapters is not None else [
            NavareaAdvisoryAdapter(), TemporaryClosureAdapter()]
        self.refresh_grace_seconds = refresh_grace_seconds

    async def refresh(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        now = now or utcnow()
        summary = {"at": now.isoformat(), "sources": [], "inserted": 0,
                   "updated": 0, "expired": 0}
        refreshed_sources: List[str] = []
        for adapter in self.adapters:
            source = adapter.source_name()
            try:
                items = await adapter.fetch(now)
            except Exception:
                continue
            refreshed_sources.append(source)
            counts = await self.store.upsert_many(items, fetched_at=now)
            summary["sources"].append({
                "source": source, "fetched": len(items), **counts})
            summary["inserted"] += counts["inserted"]
            summary["updated"] += counts["updated"]
        expired = await self.store.expire_unrefreshed(
            refreshed_sources, at=now, grace_seconds=self.refresh_grace_seconds)
        summary["expired"] = expired
        return summary

    def static_geofence_hits(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        return self.catalog.hits(lat, lon)

    def list_static_geofences(self) -> List[Dict[str, Any]]:
        return self.catalog.list_geofences()

    async def active_at(
        self, lat: float, lon: float, at: Optional[datetime] = None
    ) -> List[DynamicRestriction]:
        active = await self.store.list_active(at)
        return [r for r in active if point_in_polygon(lat, lon, r.geometry or {})]

    async def active_near_route(
        self, route: Sequence[Tuple[float, float]], at: Optional[datetime] = None
    ) -> List[DynamicRestriction]:
        from shapely.geometry import LineString, shape

        if not route:
            return []
        active = await self.store.list_active(at)
        if not active:
            return []
        try:
            line = LineString([(lon, lat) for lat, lon in route])
        except Exception:
            return []
        hits = []
        for item in active:
            try:
                geom = shape(item.geometry or {})
            except Exception:
                continue
            if geom.is_empty or not geom.intersects(line):
                continue
            hits.append(item)
        return hits

    async def list_active(self, at: Optional[datetime] = None) -> List[DynamicRestriction]:
        return await self.store.list_active(at)