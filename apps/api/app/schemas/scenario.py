# Scenario projection schemas
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class ScenarioProjectRequest(BaseModel):
    variable: str
    region: Dict[str, Any]
    depth_m: float
    trend_window: Dict[str, str]
    projection_years: int = Field(ge=1, le=50)
    model: Literal["linear_trend", "polynomial", "theil_sen"] = "linear_trend"
    assumptions: List[str] = Field(default_factory=list)


class ScenarioProjection(BaseModel):
    years: List[int]
    values: List[float]
    uncertainty_lower: List[float]
    uncertainty_upper: List[float]


class HistoricalTrend(BaseModel):
    slope_per_year: float
    intercept: float
    r_squared: float
    p_value: float
    residual_std: float


class ScenarioResponse(BaseModel):
    variable: str
    region: Dict[str, Any]
    depth_m: float
    historical_trend: HistoricalTrend
    projection: ScenarioProjection
    model: str
    assumptions: List[str]
    uncertainty_method: str
    label: str
    confidence: Dict[str, Any]