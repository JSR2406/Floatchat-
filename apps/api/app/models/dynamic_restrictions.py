# Phase 5 - first-class DYNAMIC RESTRICTIONS.
#
# Runtime restrictions (NAVAREA/NAVTEX advisories, naval/firing exercises,
# temporary closures) are authoritative official inputs with validity windows.
# They follow the SAME window semantics as static restrictions but are live:
# only a refreshed, still-valid window may ever be treated as active.  Expired
# restrictions must never remain active.
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.common import utcnow
from app.models.marine_contract import DataClass
from app.models.warnings import WarningStatus, evaluate_window_status


@dataclass
class DynamicRestriction:
    source: str
    source_record_id: str
    restriction_id: str
    name: str
    restriction_type: str
    severity: str
    geometry: Dict[str, Any]
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    official: bool = True
    data_class: str = DataClass.ADVISORY.value
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    ingested_at: Optional[datetime] = None
    refreshed_at: Optional[datetime] = None
    expired: bool = False

    def natural_key(self) -> Tuple[str, str]:
        return (self.source, self.source_record_id)

    def status(self, at: Optional[datetime] = None) -> WarningStatus:
        if self.expired:
            return WarningStatus.EXPIRED
        return evaluate_window_status(
            self.valid_from, self.valid_until, at or utcnow())

    def distance_to(self, lat: float, lon: float) -> Optional[float]:
        """Approximate distance (m) to this restriction geometry (0 when inside)."""
        from app.services.geospatial_service import point_to_polygon_distance_m
        return point_to_polygon_distance_m(lat, lon, self.geometry or {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_record_id": self.source_record_id,
            "restriction_id": self.restriction_id,
            "name": self.name,
            "restriction_type": self.restriction_type,
            "severity": self.severity,
            "geometry": self.geometry,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "official": self.official,
            "data_class": self.data_class,
            "description": self.description,
            "metadata": self.metadata,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "refreshed_at": self.refreshed_at.isoformat() if self.refreshed_at else None,
            "expired": self.expired,
        }