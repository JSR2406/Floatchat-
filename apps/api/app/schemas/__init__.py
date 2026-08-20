# Schemas Package
from app.schemas.query import (
    StructuredQuery,
    Intent,
    Region,
    BBoxRegion,
    RadiusRegion,
    NamedRegion,
    SupportedLanguage,
    QualityFilter,
    Aggregation,
    Variable,
    QueryPlanRequest,
    QueryPlanResponse,
)

from app.schemas.evidence import (
    EvidenceRecord,
    ConfidenceScore,
    ConfidenceComponents,
    NumericClaim,
    VerificationResult,
)

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMode,
    Visualizations,
    ChartVisualizationData,
    MapVisualizationData,
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
)

from app.schemas.risk import (
    RiskComponent,
    RiskBriefingResponse,
)

from app.schemas.scenario import (
    ScenarioProjectRequest,
    ScenarioResponse,
    ScenarioProjection,
    HistoricalTrend,
)

__all__ = [
    # Query
    "StructuredQuery",
    "Intent",
    "Region",
    "BBoxRegion",
    "RadiusRegion",
    "NamedRegion",
    "SupportedLanguage",
    "QualityFilter",
    "Aggregation",
    "Variable",
    "QueryPlanRequest",
    "QueryPlanResponse",
    # Evidence
    "EvidenceRecord",
    "ConfidenceScore",
    "ConfidenceComponents",
    "NumericClaim",
    "VerificationResult",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatMode",
    "Visualizations",
    "ChartVisualizationData",
    "MapVisualizationData",
    "VoiceTranscribeRequest",
    "VoiceTranscribeResponse",
    "VoiceSynthesizeRequest",
    "VoiceSynthesizeResponse",
    # Risk
    "RiskComponent",
    "RiskBriefingResponse",
    # Scenario
    "ScenarioProjectRequest",
    "ScenarioResponse",
    "ScenarioProjection",
    "HistoricalTrend",
]