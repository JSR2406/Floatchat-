# MOSDAC adapter - Meteorological & Oceanographic Satellite Data Archival Centre.
#
# Products: satellite-derived ocean products (SST / chlorophyll) and
# PFZ-related advisories.  Endpoint contract to be confirmed with provider;
# until configured every product fetch raises SourceNotConfiguredError.
from typing import Dict, List, Optional

from app.config import Settings
from app.datasources.base import BaseMarineDataSource
from app.datasources.errors import SourceInvalidDataError
from app.datasources.http import HttpDataTransport
from app.datasources.incois import _map_severity, _map_warning_type
from app.datasources.normalize import (
    ensure_list,
    parse_datetime,
    take_coordinates,
    take_numeric,
    take_string,
)
from app.models.ocean import OceanConditions
from app.models.pfz import PFZZone
from app.models.source import SourceCapability, SourceType
from app.models.warnings import MarineWarning


class MOSDACAdapter(BaseMarineDataSource):
    name = "mosdac"
    display_name = "MOSDAC (ISRO) Satellite Ocean Products"
    source_type = SourceType.MOSDAC

    PRODUCT_ENDPOINTS: Dict[str, str] = {
        "ocean": "/api/ocean/satellite",
        "pfz": "/api/pfz/advisories",
        "warnings": "/api/ocean/warnings",
    }

    def __init__(self, settings: Settings, transport: Optional[HttpDataTransport] = None):
        super().__init__(settings, transport)

    @property
    def base_url(self) -> str:
        return self.settings.mosdac_base_url

    @property
    def api_key(self) -> Optional[str]:
        return self.settings.mosdac_api_key or None

    @property
    def enabled(self) -> bool:
        return self.settings.mosdac_enabled

    @property
    def capabilities(self) -> List[SourceCapability]:
        return [
            SourceCapability(
                name="satellite_ocean",
                description="Satellite-derived SST, chlorophyll, surface products",
                data_product="ocean",
                config_required=True,
            ),
            SourceCapability(
                name="pfz_advisories",
                description="PFZ-related satellite advisory zones",
                data_product="pfz",
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
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"MOSDAC ocean item {i} is not an object")
            try:
                lat, lon = take_coordinates(raw)
            except SourceInvalidDataError:
                continue
            results.append(OceanConditions(
                latitude=lat,
                longitude=lon,
                observation_time=parse_datetime(raw.get("observation_time", raw.get("time", raw.get("datetime")))),
                source_timestamp=parse_datetime(raw.get("source_timestamp", raw.get("timestamp"))),
                sst_c=take_numeric(raw, "sst_c", "sst", "sea_surface_temperature"),
                chlorophyll=take_numeric(raw, "chlorophyll", "chl", "chlorophyll_a"),
                source=self.name,
                source_record_id=take_string(raw, "id", "record_id", "granule_id") or None,
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
                raise SourceInvalidDataError(f"MOSDAC PFZ item {i} is not an object")
            geometry = raw.get("geometry") or raw.get("geojson") or raw.get("polygon")
            if not geometry:
                raise SourceInvalidDataError(f"MOSDAC PFZ item {i} has no geometry")
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
                    "geometry", "geojson", "polygon", "centroid")},
                source=self.name,
                source_record_id=take_string(raw, "id", "advisory_id") or None,
                quality=self._to_quality(raw),
                raw_payload=raw,
            ))
        return results

    # ---------------------------------------------------------------- warnings
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
                raise SourceInvalidDataError(f"MOSDAC warning item {i} is not an object")
            geometry = raw.get("geometry") or raw.get("geojson")
            if not geometry:
                raise SourceInvalidDataError(f"MOSDAC warning item {i} has no geometry")
            results.append(MarineWarning(
                warning_id=take_string(raw, "warning_id", "id"),
                warning_type=_map_warning_type(take_string(raw, "warning_type", "type")),
                severity=_map_severity(take_string(raw, "severity")),
                geometry=geometry,
                valid_from=parse_datetime(raw.get("valid_from")),
                valid_until=parse_datetime(raw.get("valid_until", raw.get("expires_at"))),
                issued_at=parse_datetime(raw.get("issued_at")),
                updated_at=parse_datetime(raw.get("updated_at")),
                description=take_string(raw, "description", "message"),
                source=self.name,
                source_record_id=take_string(raw, "record_id") or None,
                metadata={k: v for k, v in raw.items() if k not in ("geometry", "geojson")},
                raw_payload=None,
            ))
        return results