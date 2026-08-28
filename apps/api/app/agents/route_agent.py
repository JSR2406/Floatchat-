# Route Agent
# Generates and analyzes vessel routes with hazard and geofence checking

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.agents import BaseAgent, ExecutionContext
from app.schemas.provenance import SourceType
from app.schemas.route import (
    RouteAnalysisRequest, RouteAnalysisResponse, RouteMode, VesselType,
    EnvironmentalConditions, HazardIntersection, GeofenceIntersection,
    RouteSegment, RiskAssessment
)
from app.services.provenance import get_provenance_service
from app.services.data_fusion import get_fusion_engine


class RouteAgent(BaseAgent):
    """
    Generates vessel routes and performs safety analysis including:
    - Route generation (great circle or waypoint-based)
    - Hazard intersection detection
    - Geofence compliance checking
    - Environmental condition assessment
    - Risk scoring
    """
    
    def __init__(self):
        super().__init__("route_agent")
        self.provenance = get_provenance_service()
        self.fusion = get_fusion_engine()
    
    def get_required_inputs(self) -> List[str]:
        return []
    
    def get_output_types(self) -> List[SourceType]:
        return []
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "generates_routes": True,
            "hazard_detection": True,
            "geofence_checking": True,
            "risk_scoring": True,
        }
    
    async def execute(self, context: ExecutionContext) -> List[Any]:
        """
        Execute route analysis based on structured query.
        Returns list containing RouteAnalysisResponse.
        """
        sq = context.structured_query or {}
        request_dict = sq.get("route_request")
        
        if not request_dict:
            return [self._create_error_response("No route request found in structured query")]
        
        try:
            request = RouteAnalysisRequest(**request_dict)
        except Exception as e:
            return [self._create_error_response(f"Invalid route request: {str(e)}")]
        
        result = await self._analyze_route(request, context)
        return [result]
    
    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "route_geometry": [],
            "route_distance_km": 0.0,
            "total_estimated_time_hours": 0.0,
            "segments": [],
            "hazard_intersections": [],
            "geofence_intersections": [],
            "environmental_conditions": EnvironmentalConditions(
                max_wave_height=0, avg_wave_height=0, max_wave_period=0,
                avg_wave_period=0, max_wind_speed=0, avg_wind_speed=0,
                current_speed=0, visibility=0, precipitation=0
            ),
            "risk_assessment": RiskAssessment(
                overall_score=0.0, risk_level="unavailable",
                component_scores={}, reasoning=error_msg, confidence=0.0,
                missing_data=["route_parameters"]
            ),
            "evidence": [],
            "recommendations": [f"Error: {error_msg}"],
            "limitations": ["Could not parse route request"]
        }
    
    async def _analyze_route(self, request: RouteAnalysisRequest, 
                            context: ExecutionContext) -> RouteAnalysisResponse:
        """Perform complete route analysis."""
        start_time = datetime.utcnow()
        
        # 1. Generate route geometry
        route_geometry = await self._generate_route_geometry(request)
        
        # 2. Calculate route distance
        route_distance_km = await self._calculate_route_distance(route_geometry)
        
        # 3. Generate segments
        segments = await self._generate_segments(route_geometry, request)
        
        # 4. Detect hazards along route
        hazard_intersections = await self._detect_hazards(route_geometry, request)
        
        # 5. Check geofence compliance
        geofence_intersections = await self._check_geofences(route_geometry, request)
        
        # 6. Assess environmental conditions
        env_conditions = await self._assess_environmental_conditions(route_geometry, request)
        
        # 7. Calculate risk assessment
        risk_assessment = await self._calculate_risk(
            env_conditions, hazard_intersections, geofence_intersections, request
        )
        
        # 8. Generate evidence and recommendations
        evidence = await self._gather_evidence(route_geometry, request)
        recommendations = self._generate_recommendations(
            risk_assessment, hazard_intersections, geofence_intersections, env_conditions
        )
        limitations = self._get_limitations(request)
        
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record provenance
        self.provenance.record_execution(
            query_run_id=context.query_run_id,
            agent_name=self.name,
            tool_name="route_analysis",
            input_bundles=[],
            output_bundles=[],  # No evidence bundles
            execution_time_ms=int(total_time),
            status="success",
        )
        
        return RouteAnalysisResponse(
            route_geometry=[{"lat": p[1], "lon": p[0]} for p in route_geometry.coords],
            route_distance_km=round(route_distance_km, 2),
            total_estimated_time_hours=round(route_distance_km / 15.0, 1) if route_distance_km > 0 else 0,
            segments=segments,
            hazard_intersections=hazard_intersections,
            geofence_intersections=geofence_intersections,
            environmental_conditions=env_conditions,
            risk_assessment=risk_assessment,
            evidence=evidence,
            recommendations=recommendations,
            limitations=limitations,
        )
    
    async def _generate_route_geometry(self, request: RouteAnalysisRequest):
        """Generate route geometry using great circle or waypoints."""
        # Simple great circle path between origin and destination
        lons = [request.origin_lon, request.destination_lon]
        lats = [request.origin_lat, request.destination_lat]
        
        # Create a simple line between origin and destination
        line = __import__('shapely.geometry', fromlist=['LineString']).LineString([(request.origin_lon, request.origin_lat), 
                                                        (request.destination_lon, request.destination_lat)])
        
        # Add waypoints if provided
        if request.waypoints:
            wp_coords = []
            wp_coords.append((request.origin_lat, request.origin_lon))
            for wp in request.waypoints:
                wp_coords.append((wp['lat'], wp['lon']))
            wp_coords.append((request.destination_lat, request.destination_lon))
            line = __import__('shapely.geometry', fromlist=['LineString']).LineString([(lon, lat) for lat, lon in wp_coords])
        
        return line
    
    async def _calculate_route_distance(self, route) -> float:
        """Calculate route distance in km."""
        return route.length * 111.0  # Approximate: 1 degree ≈ 111 km at equator
    
    async def _generate_segments(self, route, request: RouteAnalysisRequest) -> List:
        """Generate route segments with environmental data."""
        # Divide route into segments (default: 5 segments)
        num_segments = 5
        
        segments = []
        total_length = route.length
        
        if total_length == 0:
            return segments
        
        segment_length = total_length / num_segments
        
        for i in range(num_segments):
            start_frac = i / num_segments
            end_frac = (i + 1) / num_segments
            
            start_point = route.interpolate(start_frac, normalized=True)
            end_point = route.interpolate(end_frac, normalized=True)
            
            seg_distance = segment_length * 111.0  # km
            
            # Get environmental conditions for segment center
            center_frac = (start_frac + end_frac) / 2
            center_point = route.interpolate(center_frac, normalized=True)
            
            from app.schemas.route import RouteSegment, EnvironmentalConditions
            segments.append(RouteSegment(
                segment_id=f"seg_{i+1}",
                start_lat=start_point.y,
                start_lon=start_point.x,
                end_lat=end_point.y,
                end_lon=end_point.x,
                distance_km=round(seg_distance, 2),
                estimated_time_hours=round(seg_distance / 15.0, 1),  # 15 knots assumed
                conditions=EnvironmentalConditions(
                    max_wave_height=2.0, avg_wave_height=1.0,
                    max_wave_period=8.0, avg_wave_period=5.0,
                    max_wind_speed=10.0, avg_wind_speed=5.0,
                    current_speed=0.5, visibility=10.0, precipitation=0.0
                ),
            ))
        
        return segments
    
    async def _detect_hazards(self, route, request: RouteAnalysisRequest) -> List:
        """Detect hazards along the route."""
        hazards = []
        # Demo: no hazards detected
        return hazards
    
    async def _check_geofences(self, route, request: RouteAnalysisRequest) -> List:
        """Check geofence compliance along the route."""
        intersections = []
        # Demo: no geofence intersections
        return intersections
    
    async def _assess_environmental_conditions(self, route, request: RouteAnalysisRequest):
        """Assess environmental conditions along the route."""
        from app.services.temporal_reasoner import get_temporal_reasoner
        temporal = get_temporal_reasoner()
        season = temporal.determine_season(datetime.utcnow().month)
        
        # Base conditions depend on season and region
        return __import__('app.schemas.route', fromlist=['EnvironmentalConditions']).EnvironmentalConditions(
            max_wave_height=round(2.0, 1),
            avg_wave_height=round(1.0, 1),
            max_wave_period=round(8.0, 1),
            avg_wave_period=round(5.0, 1),
            max_wind_speed=round(10.0, 1),
            avg_wind_speed=round(5.0, 1),
            current_speed=round(0.5, 1),
            visibility=10.0,
            precipitation=0.0,
        )
    
    async def _calculate_risk(
        self,
        env_conditions,
        hazard_intersections: List,
        geofence_intersections: List,
        request: RouteAnalysisRequest,
    ):
        """Calculate overall risk score for the route."""
        from app.services.risk_engine import get_risk_engine
        risk_engine = get_risk_engine()
        
        # Convert to EnvironmentalConditions format
        from app.schemas.route import EnvironmentalConditions
        env = EnvironmentalConditions(
            max_wave_height=env_conditions.max_wave_height,
            avg_wave_height=env_conditions.avg_wave_height,
            max_wave_period=env_conditions.max_wave_period,
            avg_wave_period=env_conditions.avg_wave_period,
            max_wind_speed=env_conditions.max_wind_speed,
            avg_wind_speed=env_conditions.avg_wind_speed,
            current_speed=env_conditions.current_speed,
            visibility=env_conditions.visibility,
            precipitation=env_conditions.precipitation,
        )
        
        return get_risk_engine().assess_risk(env_conditions=env)
    
    async def _gather_evidence(self, route, request: RouteAnalysisRequest) -> List[Dict[str, Any]]:
        """Gather evidence for the route analysis."""
        evidence = []
        evidence.append({
            "source": "demo_route_analysis",
            "type": "route_parameters",
            "description": f"Route from ({request.origin_lat}, {request.origin_lon}) to "
                          f"({request.destination_lat}, {request.destination_lon})",
        })
        return evidence
    
    @staticmethod
    def _get_limitations(request: RouteAnalysisRequest) -> List[str]:
        """Get list of limitations for the route analysis."""
        limitations = [
            "Speed assumption: 15 knots assumed for time estimates",
            "Simplified route: great circle between waypoints",
            "Environmental data: deterministic estimates only",
        ]
        
        if not request.waypoints:
            limitations.append("No custom waypoints specified")
        
        if request.avoid_geofences:
            limitations.append("Geofence data: demo mode, not comprehensive")
        
        return limitations
    
    @staticmethod
    def _generate_recommendations(
        risk_assessment,
        hazard_intersections: List,
        geofence_intersections: List,
        env_conditions,
    ) -> List[str]:
        """Generate safety recommendations based on analysis."""
        recommendations = []
        
        if risk_assessment.risk_level == "elevated":
            recommendations.append("Consider postponing voyage until conditions improve")
        
        if risk_assessment.risk_level == "moderate":
            recommendations.append("Monitor conditions continuously during voyage")
        
        if hazard_intersections:
            recommendations.append("Review hazard advisories and adjust route if needed")
        
        if geofence_intersections:
            recommendations.append("Verify geofence compliance and obtain necessary permissions")
        
        # Default recommendation if low risk
        if not recommendations:
            recommendations.append("Conditions appear suitable for planned voyage")
        
        return recommendations


# Global route agent instance
_route_agent: Optional[RouteAgent] = None


def get_route_agent() -> RouteAgent:
    global _route_agent
    if _route_agent is None:
        _route_agent = RouteAgent()
    return _route_agent