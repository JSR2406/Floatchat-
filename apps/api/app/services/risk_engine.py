# Risk Engine
# Transparent risk scoring for marine conditions

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.schemas.hazard import HazardType, HazardSeverity, HazardArea
from app.schemas.route import RiskAssessment, EnvironmentalConditions
from app.schemas.evidence import ConfidenceScore, ConfidenceComponents, ConfidenceLabel
from app.services.provenance import get_provenance_service

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Provides transparent risk scoring for marine conditions.
    All calculations are deterministic and explainable.
    """
    
    def __init__(self):
        self.provenance = get_provenance_service()
    
    def assess_risk(
        self,
        environmental_conditions: EnvironmentalConditions,
        active_hazards: Optional[List[HazardArea]] = None,
        geofence_violations: Optional[List[Any]] = None,
        route_context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """
        Assess overall risk based on environmental conditions and hazards.
        
        Returns RiskAssessment with overall score, risk level, component scores,
        and detailed reasoning.
        """
        start_time = datetime.utcnow()
        
        # Initialize component scores
        component_scores = {}
        
        # 1. Wave risk (based on max wave height)
        wave_risk = self._calc_wave_risk(environmental_conditions.max_wave_height)
        component_scores["wave"] = round(wave_risk, 2)
        
        # 2. Wind risk (based on max wind speed)
        wind_risk = self._calc_wind_risk(environmental_conditions.max_wind_speed)
        component_scores["wind"] = round(wind_risk, 2)
        
        # 3. Current risk (based on current speed)
        current_risk = self._calc_current_risk(environmental_conditions.current_speed)
        component_scores["current"] = round(current_risk, 2)
        
        # 4. Hazard risk
        hazard_risk = self._calc_hazard_risk(active_hazards or [])
        component_scores["hazard"] = round(hazard_risk, 2)
        
        # 5. Geofence risk
        geofence_risk = self._calc_geofence_risk(geofence_violations or [])
        component_scores["geofence"] = round(geofence_risk, 2)
        
        # Weighted overall score
        weights = {
            "wave": 0.35,
            "wind": 0.30,
            "current": 0.15,
            "hazard": 0.15,
            "geofence": 0.05,
        }
        
        overall_score = sum(
            weights[k] * component_scores[k]
            for k in weights.keys()
            if k in component_scores
        )
        overall_score = round(overall_score, 2)
        
        # Determine risk level
        risk_level = self._score_to_risk_level(overall_score)
        
        # Generate reasoning
        reasoning_parts = []
        if wave_risk > 0.5:
            reasoning_parts.append(f"Wave risk: {wave_risk:.0%}")
        if wind_risk > 0.5:
            reasoning_parts.append(f"Wind risk: {wind_risk:.0%}")
        if current_risk > 0.5:
            reasoning_parts.append(f"Current risk: {current_risk:.0%}")
        if hazard_risk > 0:
            reasoning_parts.append(f"Hazard risk: {hazard_risk:.0%}")
        if geofence_risk > 0:
            reasoning_parts.append(f"Geofence risk: {geofence_risk:.0%}")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Standard marine conditions, low risk"
        
        # Calculate confidence based on data completeness
        confidence = self._calc_confidence(environmental_conditions, active_hazards)
        
        # Identify missing data
        missing_data = self._identify_missing_data(environmental_conditions, active_hazards)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record provenance
        self.provenance.record_execution(
            query_run_id=route_context.get("query_run_id", "") if route_context else "",
            agent_name="risk_engine",
            tool_name="assess_risk",
            input_bundles=[],
            output_bundles=[],  # No evidence bundles directly
            execution_time_ms=int(execution_time),
            status="success",
        )
        
        return RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            component_scores=component_scores,
            reasoning=reasoning,
            confidence=confidence,
            missing_data=missing_data,
        )
    
    def _calc_wave_risk(self, max_wave_height: float) -> float:
        """Calculate wave risk score (0-1, higher = more risk)."""
        if max_wave_height <= 1.0:
            return 0.1  # Low risk
        elif max_wave_height <= 2.0:
            return 0.3  # Moderate risk
        elif max_wave_height <= 3.0:
            return 0.6  # High risk
        elif max_wave_height <= 5.0:
            return 0.8  # Very high risk
        else:
            return 1.0  # Extreme risk
    
    def _calc_wind_risk(self, max_wind_speed: float) -> float:
        """Calculate wind risk score (0-1, higher = more risk)."""
        if max_wind_speed <= 10.0:
            return 0.1  # Low risk
        elif max_wind_speed <= 20.0:
            return 0.3  # Moderate risk
        elif max_wind_speed <= 30.0:
            return 0.6  # High risk
        elif max_wind_speed <= 40.0:
            return 0.8  # Very high risk
        else:
            return 1.0  # Extreme risk
    
    def _calc_current_risk(self, current_speed: float) -> float:
        """Calculate current risk score (0-1, higher = more risk)."""
        if current_speed <= 0.5:
            return 0.1  # Low risk
        elif current_speed <= 1.0:
            return 0.3  # Moderate risk
        elif current_speed <= 1.5:
            return 0.6  # High risk
        elif current_speed <= 2.0:
            return 0.8  # Very high risk
        else:
            return 1.0  # Extreme risk
    
    def _calc_hazard_risk(self, active_hazards: List[Any]) -> float:
        """Calculate hazard risk based on active hazards."""
        if not active_hazards:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            HazardSeverity.LOW: 0.2,
            HazardSeverity.MODERATE: 0.5,
            HazardSeverity.HIGH: 0.8,
            HazardSeverity.CRITICAL: 1.0,
        }
        
        max_weight = max(
            (severity_weights.get(hazard.severity, 0) for hazard in active_hazards),
            default=0
        )
        
        return max_weight
    
    def _calc_geofence_risk(self, geofence_violations: List[Any]) -> float:
        """Calculate geofence risk based on violations."""
        if not geofence_violations:
            return 0.0
        
        # Geofence violations are significant
        return 0.5
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level string."""
        if score >= 0.7:
            return "elevated"
        elif score >= 0.4:
            return "moderate"
        elif score > 0:
            return "low"
        else:
            return "unavailable"
    
    def _calc_confidence(
        self,
        environmental_conditions: EnvironmentalConditions,
        active_hazards: Optional[List[Any]] = None,
    ) -> float:
        """Calculate confidence score for the risk assessment."""
        confidence = 0.8  # Base confidence
        
        # Reduce confidence if data is limited
        if environmental_conditions.max_wave_height == 0:
            confidence -= 0.2
        if environmental_conditions.max_wind_speed == 0:
            confidence -= 0.2
        if environmental_conditions.current_speed == 0:
            confidence -= 0.1
        
        # Adjust based on hazard data availability
        if active_hazards is not None:
            if len(active_hazards) == 0:
                confidence += 0.1  # No hazards is good news
        
        return max(0.1, min(1.0, confidence))
    
    def _identify_missing_data(
        self,
        environmental_conditions: EnvironmentalConditions,
        active_hazards: Optional[List[Any]] = None,
    ) -> List[str]:
        """Identify what data is missing from the risk assessment."""
        missing = []
        
        if environmental_conditions.max_wave_height is None or environmental_conditions.max_wave_height == 0:
            missing.append("wave height data")
        if environmental_conditions.max_wind_speed is None or environmental_conditions.max_wind_speed == 0:
            missing.append("wind speed data")
        if environmental_conditions.current_speed is None or environmental_conditions.current_speed == 0:
            missing.append("current speed data")
        
        if active_hazards is None:
            missing.append("hazard data")
        
        return missing


# Global risk engine instance
_risk_engine: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine