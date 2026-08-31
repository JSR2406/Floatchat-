# IMD adapter - India Meteorological Department.
#
# Products: marine weather observation / forecast, cyclone warnings.
# Endpoint contract must be confirmed with the provider before enabling; until
# then fetches raise SourceNotConfiguredError (no fabricated data).
from typing import Dict, List, Optional

from app.config import Settings
from app.datasources.base import BaseMarineDataSource
from app.datasources.errors import SourceInvalidDataError
from app.datasources.http import HttpDataTransport
from app.datasources.incois import _map_severity, _map_warning_type
from app.datasources.normalize import (
    ensure_list,
    parse_datetime,
    take_bool,
    take_coordinates,
    take_numeric,
    take_string,
)
from app.models.source import SourceCapability, SourceType
from app.models.weather import WeatherForecast, WeatherObservation
from app.models.warnings import MarineWarning


class IMDAdapter(BaseMarineDataSource):
    name = "imd"
    display_name = "India Meteorological Department"
    source_type = SourceType.IMD

    PRODUCT_ENDPOINTS: Dict[str, str] = {
        "weather_observation": "/api/marine/observation",
        "weather_forecast": "/api/marine/forecast",
        "warnings": "/api/warnings/cyclone",
    }

    def __init__(self, settings: Settings, transport: Optional[HttpDataTransport] = None):
        super().__init__(settings, transport)

    @property
    def base_url(self) -> str:
        return self.settings.imd_base_url

    @property
    def api_key(self) -> Optional[str]:
        return self.settings.imd_api_key or None

    @property
    def enabled(self) -> bool:
        return self.settings.imd_enabled

    @property
    def capabilities(self) -> List[SourceCapability]:
        return [
            SourceCapability(
                name="marine_weather",
                description="Marine weather observations",
                data_product="weather_observation",
                config_required=True,
            ),
            SourceCapability(
                name="marine_weather_forecast",
                description="Marine weather forecasts",
                data_product="weather_forecast",
                config_required=True,
            ),
            SourceCapability(
                name="cyclone_warnings",
                description="Cyclone warnings and alerts",
                data_product="warnings",
                config_required=True,
            ),
        ]

    # ----------------------------------------------------------- observations
    async def fetch_weather_observation(
        self, *, lat: float, lon: float, time=None, **kw
    ) -> List[WeatherObservation]:
        self._ensure_configured("weather_observation")
        payload = await self._fetch_json(
            self._endpoint("weather_observation"),
            params={"lat": lat, "lon": lon, "time": time},
        )
        return self.normalize_weather_observation(payload)

    def normalize_weather_observation(self, payload: dict) -> List[WeatherObservation]:
        results: List[WeatherObservation] = []
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"IMD weather-obs item {i} is not an object")
            try:
                lat, lon = take_coordinates(raw)
            except SourceInvalidDataError:
                continue
            condition = take_string(raw, "condition", "weather") or None
            results.append(WeatherObservation(
                latitude=lat,
                longitude=lon,
                valid_time=parse_datetime(raw.get("valid_time", raw.get("time", raw.get("observed_at")))),
                source_timestamp=parse_datetime(raw.get("source_timestamp", raw.get("timestamp"))),
                temperature_c=take_numeric(raw, "temperature_c", "temperature", "temp"),
                wind_speed_ms=take_numeric(raw, "wind_speed_ms", "wind_speed"),
                wind_direction_deg=take_numeric(raw, "wind_direction_deg", "wind_direction"),
                precipitation_mm=take_numeric(raw, "precipitation_mm", "precipitation", "rainfall"),
                pressure_hpa=take_numeric(raw, "pressure_hpa", "pressure", "slp"),
                humidity_pct=take_numeric(raw, "humidity_pct", "humidity"),
                visibility_m=take_numeric(raw, "visibility_m", "visibility"),
                lightning=take_bool(raw, "lightning", "is_lightning"),
                condition=condition,
                source=self.name,
                source_record_id=take_string(raw, "id", "record_id", "station_id") or None,
                quality=self._to_quality(raw),
                raw_payload=raw,
            ))
        return results

    # ---------------------------------------------------------------- forecast
    async def fetch_weather_forecast(
        self, *, lat: float, lon: float, time=None, **kw
    ) -> List[WeatherForecast]:
        self._ensure_configured("weather_forecast")
        payload = await self._fetch_json(
            self._endpoint("weather_forecast"),
            params={"lat": lat, "lon": lon, "time": time},
        )
        return self.normalize_weather_forecast(payload)

    def normalize_weather_forecast(self, payload: dict) -> List[WeatherForecast]:
        results: List[WeatherForecast] = []
        for i, raw in enumerate(ensure_list(payload)):
            if not isinstance(raw, dict):
                raise SourceInvalidDataError(f"IMD forecast item {i} is not an object")
            try:
                lat, lon = take_coordinates(raw)
            except SourceInvalidDataError:
                continue
            valid_from = parse_datetime(raw.get("valid_from", raw.get("from")))
            valid_until = parse_datetime(raw.get("valid_until", raw.get("until")))
            issue_time = parse_datetime(raw.get("issue_time", raw.get("issued_at", raw.get("timestamp"))))
            condition = take_string(raw, "condition", "weather") or None
            results.append(WeatherForecast(
                latitude=lat,
                longitude=lon,
                issue_time=issue_time,
                valid_from=valid_from,
                valid_until=valid_until,
                forecast_horizon_h=take_numeric(raw, "forecast_horizon_h", "horizon_h"),
                source_timestamp=parse_datetime(raw.get("source_timestamp", raw.get("timestamp"))),
                temperature_c=take_numeric(raw, "temperature_c", "temperature"),
                temperature_min_c=take_numeric(raw, "temperature_min_c", "temp_min"),
                temperature_max_c=take_numeric(raw, "temperature_max_c", "temp_max"),
                wind_speed_ms=take_numeric(raw, "wind_speed_ms", "wind_speed"),
                wind_direction_deg=take_numeric(raw, "wind_direction_deg", "wind_direction"),
                precipitation_mm=take_numeric(raw, "precipitation_mm", "precipitation", "rainfall"),
                pressure_hpa=take_numeric(raw, "pressure_hpa", "pressure", "slp"),
                humidity_pct=take_numeric(raw, "humidity_pct", "humidity"),
                visibility_m=take_numeric(raw, "visibility_m", "visibility"),
                lightning=take_bool(raw, "lightning", "is_lightning"),
                condition=condition,
                source=self.name,
                source_record_id=take_string(raw, "id", "forecast_id", "record_id") or None,
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
                raise SourceInvalidDataError(f"IMD warning item {i} is not an object")
            geometry = raw.get("geometry") or raw.get("geojson")
            if not geometry:
                raise SourceInvalidDataError(f"IMD warning item {i} has no geometry")
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