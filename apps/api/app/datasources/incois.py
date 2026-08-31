# INCOIS adapter - Indian National Centre for Ocean Information Services.
#
# Products: ocean conditions (waves / currents / SST / chlorophyll), tides,
# PFZ advisories, fishing/cyclone warnings.
#
# Endpoints and auth differ per provider contract.  Until real endpoints and
# credentials are enabled in settings, every product fetch raises
# SourceNotConfiguredError and availability reports "not configured".
import logging
from typing import Dict, List, Optional

from app.config import Settings
from app.datasources.base import BaseMarineDataSource
from app.datasources.errors import SourceInvalidDataError
from app.datasources.http import HttpDataTransport
from app.datasources.normalize import (
    ensure_list,
    parse_datetime,
    take_coordinates,
    take_numeric,
    take_string,
)
from app.models.common import QualityStatus
from app.models.ocean import OceanConditions
from app.models.pfz import PFZZone
from app.models.source import SourceCapability, SourceType
from app.models.tides import TidePrediction, TideType
from app.models.warnings import MarineWarning, WarningSeverity, WarningType

logger = logging.getLogger(__name__)


class INCOISAdapter(BaseMarineDataSource):
    name = "incois"
    display_name = "Indian National Centre for Ocean Information Services"
    source_type = SourceType.INCOIS

    # Placeholder endpoint schema. Confirm paths + auth with the provider
    # before enabling; fetch raises "configuration required" until then.
    PRODUCT_ENDPOINTS: Dict[str, str] = {
        "ocean": "/api/ocean/conditions",
        "tides": "/api/tides/predictions",
        "pfz": "/api/pfz/advisories",
        "warnings": "/api/advisories/marine",
    }

    def __init__(self, settings: Settings, transport: Optional[HttpDataTransport] = None):
        super().__init__(settings, transport)

    @property
    def base_url(self) -> str:
        return self.settings.incois_base_url

    @property
    def api_key(self) -> Optional[str]:
        return self.settings.incois_api_key or None

    @property
    def enabled(self) -> bool:
        return self.settings.incois_enabled

    @property
    def capabilities(self) -> List[SourceCapability]:
        return [
            SourceCapability(
                name="ocean_conditions",
                description="Wave height/period/direction, currents, SST, chlorophyll",
                data_product="ocean",
                config_required=True,
            ),
            SourceCapability(
                name="tide_predictions",
                description="Tide predictions for Indian coast",
                data_product="tides",
                config_required=True,
            ),
            SourceCapability(
                name="pfz_advisories",
                description="Potential Fishing Zone advisories",
                data_product="pfz",
                config_required=True,
            ),
            SourceCapability(
                name="marine_warnings",
                description="Fishing / cyclone / navigational warnings",
                data_product="warnings",
                config_required=True,
            ),
        ]

    # ------------------------------------------------------------------ ocean
    async def fetch_ocean(
        self, *, lat: float, lon: float, time=None, **kw
    ) -> List[OceanConditions]:
        self._ensure_configured("ocean")
        payload = await self._fetch_json(
            self._endpoint("ocean"),
            params={"lat": lat, "lon": lon, "time": time},
        )
        return self.normalize_ocean(payload)

    def normalize_ocean(self, payload: dict) -> List[OceanConditions]:
        results: List[OceanConditions] = []
        raw_list = ensure_list(payload)
        for i, raw in enumerate(raw_list):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(
                    f"INCOIS ocean payload item {i} is not an object"
                )
            try:
                lat, lon = take_coordinates(raw)
            except SourceInvalidDataError:
                continue
            results.append(OceanConditions(
                latitude=lat,
                longitude=lon,
                observation_time=parse_datetime(
                    raw.get("observation_time", raw.get("time", raw.get("datetime")))
                ),
                source_timestamp=parse_datetime(raw.get("source_timestamp", raw.get("timestamp"))),
                sst_c=take_numeric(raw, "sst_c", "sst", "temperature"),
                chlorophyll=take_numeric(raw, "chlorophyll", "chl"),
                wave_height_m=take_numeric(raw, "wave_height_m", "wave_height", "swh"),
                wave_period_s=take_numeric(raw, "wave_period_s", "wave_period", "mwd_period"),
                wave_direction_deg=take_numeric(raw, "wave_direction_deg", "wave_direction", "mwd"),
                current_speed_ms=take_numeric(raw, "current_speed_ms", "current_speed", "speed"),
                current_direction_deg=take_numeric(raw, "current_direction_deg", "current_direction", "direction"),
                salinity_psu=take_numeric(raw, "salinity_psu", "salinity", "sss"),
                source=self.name,
                source_record_id=take_string(raw, "id", "record_id", "station_id") or None,
                quality=self._to_quality(raw),
                raw_payload=raw,
            ))
        return results

    # ------------------------------------------------------------------ tides
    async def fetch_tides(
        self, *, lat: float, lon: float, start=None, end=None, **kw
    ) -> List[TidePrediction]:
        self._ensure_configured("tides")
        payload = await self._fetch_json(
            self._endpoint("tides"),
            params={"lat": lat, "lon": lon, "start": start, "end": end},
        )
        return self.normalize_tides(payload, lat, lon)

    def normalize_tides(self, payload: dict, lat: float, lon: float) -> List[TidePrediction]:
        results: List[TidePrediction] = []
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"INCOIS tide payload item {i} is not an object")
            kind = str(raw.get("type", raw.get("tide_type", ""))).strip().lower()
            if kind in ("low", "l"):
                tide_type = TideType.LOW
            elif kind in ("high", "h"):
                tide_type = TideType.HIGH
            else:
                tide_type = TideType.HIGH if "high" in take_string(raw, "status").lower() else TideType.LOW
            results.append(TidePrediction(
                location_name=take_string(raw, "station", "location_name") or None,
                latitude=float(raw.get("latitude", lat)),
                longitude=float(raw.get("longitude", lon)),
                event_time=parse_datetime(raw.get("event_time", raw.get("time", raw.get("datetime")))),
                tide_height_m=take_numeric(raw, "height", "tide_height_m", "predicted_height"),
                tide_type=tide_type,
                is_prediction=raw.get("is_prediction", True),
                source_timestamp=parse_datetime(raw.get("source_timestamp", raw.get("timestamp"))),
                source=self.name,
                source_record_id=take_string(raw, "id", "record_id") or None,
                quality=self._to_quality(raw),
                raw_payload=raw,
            ))
        return results

    # --------------------------------------------------------------------- pfz
    async def fetch_pfz(
        self, *, lat: float = None, lon: float = None, date=None, **kw
    ) -> List[PFZZone]:
        self._ensure_configured("pfz")
        payload = await self._fetch_json(
            self._endpoint("pfz"),
            params={"lat": lat, "lon": lon, "date": date},
        )
        return self.normalize_pfz(payload)

    def normalize_pfz(self, payload: dict) -> List[PFZZone]:
        from app.geo_utils import geojson_centroid_long_lat
        results: List[PFZZone] = []
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"INCOIS PFZ payload item {i} is not an object")
            geometry = raw.get("geometry") or raw.get("geojson") or raw.get("polygon")
            if not geometry:
                raise SourceInvalidDataError(f"INCOIS PFZ item {i} has no geometry")
            lon_c, lat_c = geojson_centroid_long_lat(geometry)
            results.append(PFZZone(
                geometry=geometry,
                centroid={"latitude": lat_c, "longitude": lon_c},
                generated_at=parse_datetime(raw.get("generated_at", raw.get("valid_from"))),
                valid_from=parse_datetime(raw.get("valid_from")),
                valid_until=parse_datetime(raw.get("valid_until")),
                species=[s for s in (raw.get("species") or raw.get("target_species") or []) if isinstance(s, str)],
                confidence=float(raw.get("confidence", raw.get("probability", 0.5))),
                metadata={k: v for k, v in raw.items() if k not in (
                    "geometry", "geojson", "polygon", "centroid", "source", "source_record_id")},
                source=self.name,
                source_record_id=take_string(raw, "id", "advisory_id", "record_id") or None,
                quality=self._to_quality(raw),
                raw_payload=raw,
            ))
        return results

    # --------------------------------------------------------------- warnings
    async def fetch_warnings(
        self, *, lat: float = None, lon: float = None, **kw
    ) -> List[MarineWarning]:
        self._ensure_configured("warnings")
        payload = await self._fetch_json(
            self._endpoint("warnings"),
            params={"lat": lat, "lon": lon},
        )
        return self.normalize_warnings(payload)

    def normalize_warnings(self, payload: dict) -> List[MarineWarning]:
        results: List[MarineWarning] = []
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"INCOIS warning payload item {i} is not an object")
            geometry = raw.get("geometry") or raw.get("geojson")
            if not geometry:
                raise SourceInvalidDataError(f"INCOIS warning item {i} has no geometry (or geo-bounding-box)")
            warnings_type = _map_warning_type(take_string(raw, "warning_type", "type"))
            results.append(MarineWarning(
                warning_id=take_string(raw, "warning_id", "id"),
                warning_type=warnings_type,
                severity=_map_severity(take_string(raw, "severity")),
                geometry=geometry,
                valid_from=parse_datetime(raw.get("valid_from")),
                valid_until=parse_datetime(raw.get("valid_until", raw.get("expires_at"))),
                issued_at=parse_datetime(raw.get("issued_at")),
                updated_at=parse_datetime(raw.get("updated_at")),
                description=take_string(raw, "description", "message"),
                source=self.name,
                source_record_id=take_string(raw, "record_id") or None,
                metadata={k: v for k, v in raw.items() if k not in (
                    "geometry", "geojson", "description", "message")},
                raw_payload=None,
            ))
        return results


def _map_warning_type(value: str) -> WarningType:
    lowered = value.lower()
    if "cyclone" in lowered:
        return WarningType.CYCLONE
    if "fishing" in lowered or "fish" in lowered:
        return WarningType.FISHING_WARNING
    if "storm" in lowered:
        return WarningType.STORM_WARNING
    if "nav" in lowered:
        return WarningType.NAVIGATIONAL_WARNING
    if "restrict" in lowered:
        return WarningType.RESTRICTION
    return WarningType.OTHER


def _map_severity(value: str) -> WarningSeverity:
    lowered = value.lower()
    for severity in (WarningSeverity.CRITICAL, WarningSeverity.HIGH,
                     WarningSeverity.MODERATE, WarningSeverity.LOW):
        if severity.value in lowered:
            return severity
    return WarningSeverity.UNKNOWN