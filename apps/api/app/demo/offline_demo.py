# Offline Demo Configuration
# 5 Flagship Queries for ORCA Offline Demo

FLAGSHIP_QUERIES = [
    {
        "id": "demo_1",
        "name": "Arabian Sea Temperature & Salinity",
        "category": "Profile Search",
        "query": "Show temperature and salinity conditions in the Arabian Sea.",
        "language": "en-IN",
        "expected_intent": "profile_search",
        "expected_region": "arabian_sea",
        "expected_variables": ["temperature", "salinity"],
        "demo_response": {
            "summary": "Based on 45 ARGO profiles from the Arabian Sea (updated 6 hours ago):",
            "temperature": "28.5°C average (range: 26.2-30.1°C)",
            "salinity": "35.2 PSU average (range: 34.8-35.6 PSU)",
            "profiles": 45,
            "observations": 12450,
            "floats": 12,
            "freshness": "6 hours",
            "confidence": "high",
            "risk_level": "low",
            "recommendations": ["Conditions favorable for fishing and research activities"]
        }
    },
    {
        "id": "demo_2",
        "name": "Anomalous Conditions Near Mumbai",
        "category": "Anomaly Detection",
        "query": "Find anomalous ocean conditions near Mumbai.",
        "language": "en-IN",
        "expected_intent": "anomaly_detection",
        "expected_region": "radius",
        "expected_location": {"lat": 19.0760, "lon": 72.8777},
        "expected_radius_km": 100,
        "demo_response": {
            "summary": "Analysis of 67 profiles within 100km of Mumbai (last 30 days vs historical baseline):",
            "anomalies_found": 3,
            "details": [
                {"type": "temperature", "location": "18.9°N, 72.7°E", "anomaly": "+1.8°C above baseline", "confidence": "high"},
                {"type": "salinity", "location": "19.1°N, 73.0°E", "anomaly": "-0.4 PSU below baseline", "confidence": "moderate"},
                {"type": "chlorophyll", "location": "19.3°N, 72.5°E", "anomaly": "+45% above baseline", "confidence": "high"}
            ],
            "confidence": "high",
            "recommendations": ["Monitor for potential upwelling event", "Check for harmful algal bloom indicators"]
        }
    },
    {
        "id": "demo_3",
        "name": "Mumbai to Goa Route Safety",
        "category": "Route Analysis",
        "query": "Is it safe to travel from Mumbai to Goa tomorrow morning?",
        "language": "en-IN",
        "expected_intent": "route_analysis",
        "expected_origin": {"lat": 19.0760, "lon": 72.8777},
        "expected_destination": {"lat": 15.2993, "lon": 74.1240},
        "demo_response": {
            "summary": "Route analysis for Mumbai → Goa (580 km, ~38 hours at 15 knots):",
            "route_distance_km": 580,
            "estimated_time_hours": 38.5,
            "risk_assessment": {
                "overall_score": 0.28,
                "risk_level": "low",
                "component_scores": {
                    "wave": 0.2,
                    "wind": 0.3,
                    "current": 0.2,
                    "hazard": 0.0,
                    "geofence": 0.0
                },
                "reasoning": "Wave risk: 20%; Wind risk: 30%; Current risk: 20%"
            },
            "environmental_conditions": {
                "max_wave_height": 1.2,
                "max_wind_speed": 12.0,
                "current_speed": 0.4
            },
            "hazards": [],
            "geofences": [],
            "recommendations": ["Conditions appear suitable for planned voyage", "Monitor weather updates before departure"],
            "confidence": 0.85
        }
    },
    {
        "id": "demo_4",
        "name": "Route Risk Explanation",
        "category": "Risk Reasoning",
        "query": "Why is this route marked moderate risk?",
        "language": "en-IN",
        "expected_intent": "marine_condition_briefing",
        "context": "Follow-up to demo_3",
        "demo_response": {
            "summary": "Risk breakdown for Mumbai-Goa route (Risk Score: 0.28 → LOW):",
            "component_breakdown": {
                "wave_risk": "20% - Max wave height 1.2m (well below 2m threshold)",
                "wind_risk": "30% - Max wind speed 12 m/s (moderate, below 15 m/s caution threshold)",
                "current_risk": "20% - Current speed 0.4 m/s (favorable, below 0.5 m/s)",
                "hazard_risk": "0% - No active cyclones, storms, or warnings along route",
                "geofence_risk": "0% - Route clear of MPAs, EEZ boundaries, restricted zones"
            },
            "reasoning": "Overall low risk because all environmental factors are within safe operational thresholds for standard vessels. The moderate wind component is the primary contributor but remains well within safe limits for a 15-knot vessel.",
            "missing_data": [],
            "confidence": 0.85
        }
    },
    {
        "id": "demo_5",
        "name": "Evidence Transparency",
        "category": "Evidence Verification",
        "query": "Show me the evidence used for that decision.",
        "language": "en-IN",
        "expected_intent": "evidence_verification",
        "context": "Follow-up to demo_3 or demo_4",
        "demo_response": {
            "summary": "Evidence supporting Mumbai-Goa route assessment:",
            "evidence_items": [
                {
                    "source": "ARGO",
                    "profiles": 45,
                    "observations": 12450,
                    "floats": 12,
                    "region": "Arabian Sea (15-20°N, 70-75°E)",
                    "time_range": "2026-08-20 to 2026-08-28",
                    "freshness": "6 hours",
                    "variables": ["temperature", "salinity", "oxygen"],
                    "quality": "QC flags 1 & 2 (recommended)"
                },
                {
                    "source": "Sarvam Weather",
                    "type": "wind",
                    "data_points": 180,
                    "forecast_hours": 48,
                    "resolution": "0.25°",
                    "freshness": "2 hours"
                },
                {
                    "source": "Sarvam Wave",
                    "type": "wave",
                    "data_points": 180,
                    "forecast_hours": 72,
                    "resolution": "0.25°",
                    "freshness": "2 hours"
                },
                {
                    "source": "ElevenLabs Marine",
                    "type": "current",
                    "data_points": 180,
                    "resolution": "0.25°",
                    "freshness": "4 hours"
                }
            ],
            "verification": {
                "all_claims_verified": True,
                "numeric_claims": [
                    {"claim": "Max wave height 1.2m", "verified": True, "source": "Sarvam Wave + ARGO interpolation"},
                    {"claim": "Max wind speed 12 m/s", "verified": True, "source": "Sarvam Weather forecast"},
                    {"claim": "Current speed 0.4 m/s", "verified": True, "source": "ElevenLabs Marine model"},
                    {"claim": "Risk score 0.28", "verified": True, "source": "Risk Engine calculation"}
                ]
            },
            "limitations": [
                "Wave model resolution 0.25° (~25km) may miss localized effects",
                "Current model is climatological + forecast blend",
                "No real-time buoy validation in corridor"
            ]
        }
    },
    {
        "id": "demo_6",
        "name": "Historical Baseline Comparison",
        "category": "Comparison",
        "query": "Compare tomorrow with the historical baseline.",
        "language": "en-IN",
        "expected_intent": "anomaly_detection",
        "context": "Follow-up to demo_2",
        "demo_response": {
            "summary": "Comparison of tomorrow's forecast vs 10-year historical baseline (Aug 28):",
            "comparison": {
                "temperature": {"forecast": 28.5, "baseline": 27.8, "delta": "+0.7°C", "anomaly": "moderate"},
                "salinity": {"forecast": 35.2, "baseline": 35.1, "delta": "+0.1 PSU", "anomaly": "normal"},
                "wave_height": {"forecast": 1.2, "baseline": 1.0, "delta": "+0.2m", "anomaly": "elevated"},
                "wind_speed": {"forecast": 12, "baseline": 10, "delta": "+2 m/s", "anomaly": "moderate"}
            },
            "conclusion": "Tomorrow shows moderately elevated wave and wind conditions compared to 10-year average. Temperature anomaly of +0.7°C suggests ongoing warm anomaly in the region.",
            "confidence": 0.8,
            "recommendations": ["Consider delay if wave-sensitive operations planned", "Monitor for further escalation"]
        }
    },
    {
        "id": "demo_7",
        "name": "Scenario Projection - Departure Time Change",
        "category": "Scenario Analysis",
        "query": "What happens if the departure time changes?",
        "language": "en-IN",
        "expected_intent": "scenario_projection",
        "context": "Follow-up to demo_3",
        "demo_response": {
            "summary": "Scenario: Departure delayed by 24 hours (Aug 29 → Aug 30):",
            "scenarios": [
                {
                    "name": "Original (Aug 29 06:00)",
                    "risk_score": 0.28,
                    "risk_level": "low",
                    "travel_time_hours": 38.5,
                    "conditions": "Wave 1.2m, Wind 12 m/s"
                },
                {
                    "name": "Delayed (Aug 30 06:00)",
                    "risk_score": 0.35,
                    "risk_level": "low",
                    "travel_time_hours": 38.5,
                    "conditions": "Wave 1.5m, Wind 15 m/s"
                }
            ],
            "comparison": {
                "risk_delta": "+0.07",
                "time_delta": "0h (same distance)",
                "fuel_delta": "0% (same speed)"
            },
            "recommendation": "Both windows show low risk. Delayed departure has slightly higher wind/wave exposure but remains within safe limits. Proceed with original plan unless operational constraints require delay.",
            "confidence": 0.75
        }
    },
    {
        "id": "demo_8",
        "name": "Multilingual - Hindi",
        "category": "Multilingual",
        "query": "अरब सागर में तापमान और लवणता की स्थिति दिखाएं",
        "language": "hi-IN",
        "expected_intent": "profile_search",
        "expected_region": "arabian_sea",
        "demo_response": {
            "summary": "अरब सागर की वर्तमान स्थिति (45 ARGO प्रोफाइल, 6 घंटे पहले अपडेट):",
            "temperature": "28.5°C औसत (रेंज: 26.2-30.1°C)",
            "salinity": "35.2 PSU औसत (रेंज: 34.8-35.6 PSU)",
            "profiles": 45,
            "observations": 12450,
            "floats": 12,
            "freshness": "6 घंटे",
            "confidence": "high",
            "risk_level": "low",
            "recommendations": ["मछली पकड़ने और शोध गतिविधियों के लिए स्थितियाँ अनुकूल हैं"]
        }
    },
    {
        "id": "demo_9",
        "name": "Multilingual - Malayalam",
        "category": "Multilingual",
        "query": "അറബിക്കടലിൽ താപനിലയും ലവണതവും കാണിക്കൂ",
        "language": "ml-IN",
        "expected_intent": "profile_search",
        "expected_region": "arabian_sea",
        "demo_response": {
            "summary": "അറബിക്കടലിന്റെ നിലവിലെ സാഹചര്യം (45 ARGO പ്രൊഫൈലുകൾ, 6 മണിക്കൂർ മുമ്പ് അപ്ഡേറ്റ് ചെയ്തത്):",
            "temperature": "28.5°C ശരാശരി (രേഞ്ച്: 26.2-30.1°C)",
            "salinity": "35.2 PSU ശരാശരി (രേഞ്ച്: 34.8-35.6 PSU)",
            "profiles": 45,
            "observations": 12450,
            "floats": 12,
            "freshness": "6 മണിക്കൂർ",
            "confidence": "high",
            "risk_level": "low",
            "recommendations": ["മത്സ്യബന്ധനവും ഗവേഷണ പ്രവർത്തനങ്ങളും ചെയ്യാൻ സാഹചര്യങ്ങൾ അനുകൂലമാണ്"]
        }
    },
    {
        "id": "demo_10",
        "name": "Alert Trigger",
        "category": "Alert System",
        "query": "Trigger an alert for cyclone conditions near Kerala coast",
        "language": "en-IN",
        "expected_intent": "alert_management",
        "demo_response": {
            "summary": "Alert rule created and evaluated:",
            "rule": {
                "rule_id": "rule_demo_cyclone_kerala",
                "name": "Cyclone Watch - Kerala Coast",
                "hazard_types": ["cyclone"],
                "severity_threshold": "moderate",
                "region": {"lat": 10.0, "lon": 76.0, "radius_km": 200},
                "check_interval_minutes": 30,
                "notify_channels": ["email", "push"]
            },
            "evaluation": {
                "triggered": True,
                "event_id": "evt_demo_cyclone_001",
                "triggered_at": "2026-08-28T14:30:00Z",
                "trigger_reason": "Cyclone warning issued by IMD for Kerala coast. System moving NW at 15 km/h. Expected landfall in 36-48 hours.",
                "severity": "high",
                "location": {"lat": 10.5, "lon": 75.8},
                "notifications_sent": ["email", "push"]
            },
            "actions": [
                "Acknowledge alert",
                "Review route plans for affected vessels",
                "Monitor IMD bulletins every 3 hours"
            ]
        }
    }
]

# Demo Data Manifest
DEMO_MANIFEST = {
    "version": "1.0",
    "created": "2026-08-28T00:00:00Z",
    "description": "ORCA Offline Demo Dataset Manifest",
    "datasets": {
        "argo": {
            "description": "ARGO float profiles and observations",
            "files": [
                "data/cached/argo_profiles.parquet",
                "data/cached/argo_observations.parquet",
                "data/cached/argo_floats.parquet"
            ],
            "stats": {
                "profiles": 1184,
                "observations": 35520,
                "floats": 16,
                "time_range": "2024-01-01 to 2025-12-31",
                "regions": ["arabian_sea", "bay_of_bengal", "kerala_coast", "equatorial_indian_ocean"],
                "variables": ["temperature", "salinity", "oxygen", "chlorophyll", "nitrate", "ph"],
                "quality_flags": "QC 1 & 2 (recommended)"
            }
        },
        "weather": {
            "description": "Sarvam Weather forecast data (demo mode)",
            "coverage": "Indian Ocean region (30°S-30°N, 30°E-120°E)",
            "resolution": "0.25°",
            "forecast_hours": 48,
            "variables": ["wind_speed", "wind_direction", "air_temperature", "pressure", "precipitation"],
            "demo_mode": True
        },
        "wave": {
            "description": "Sarvam Wave forecast data (demo mode)",
            "coverage": "Indian Ocean region",
            "resolution": "0.25°",
            "forecast_hours": 72,
            "variables": ["wave_height", "wave_period", "wave_direction"],
            "demo_mode": True
        },
        "current": {
            "description": "ElevenLabs Marine Current model (demo mode)",
            "coverage": "Indian Ocean region",
            "resolution": "0.25°",
            "variables": ["current_speed", "current_direction", "sea_surface_temp"],
            "demo_mode": True
        },
        "hazard": {
            "description": "Hazard and warning data (demo mode)",
            "types": ["cyclone", "storm", "warning", "geofence"],
            "sources": ["IMD", "INCOIS", "demo"],
            "demo_mode": True
        },
        "geofence": {
            "description": "Geofence boundaries (MPA, EEZ, restricted zones)",
            "areas": [
                {"id": "gf_1", "name": "Arabian Sea MPA", "type": "mpa"},
                {"id": "gf_2", "name": "Suez Canal Zone", "type": "restricted"},
                {"id": "gf_3", "name": "Strait of Hormuz EEZ", "type": "eez"}
            ]
        }
    },
    "queries": FLAGSHIP_QUERIES,
    "flags": {
        "demo_mode": True,
        "offline": True,
        "mock_providers": True
    }
}

# Export
__all__ = ["FLAGSHIP_QUERIES", "DEMO_MANIFEST"]