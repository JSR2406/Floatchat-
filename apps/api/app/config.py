# Backend Configuration
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database - PostgreSQL with PostGIS
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/floatchat"
    geom_srid: int = 4326

    # Supabase (managed PostgreSQL/PostGIS)
    supabase_url: str = ""
    supabase_project_ref: str = ""
    supabase_publishable_key: str = ""
    supabase_jwks_url: str = ""

    # LLM - OpenRouter for free tier access
    llm_provider: str = "openrouter"
    llm_api_key: str = ""
    llm_model: str = "anthropic/claude-3.5-sonnet"
    llm_temperature: float = 0.1

    # Voice Providers - Sarvam + ElevenLabs
    stt_provider: str = "sarvam"
    stt_api_key: str = ""
    tts_provider: str = "elevenlabs"
    tts_api_key: str = ""
    translation_provider: str = "google"
    translation_api_key: str = ""

    # Data Sources
    argo_gdac_url: str = "https://data-argo.ifremer.fr/argo"
    erddap_url: str = "https://erddap.ifremer.fr/erddap"
    argovis_url: str = "https://argovis.colorado.edu"
    # Legacy ARGO/Parquet cache location (CacheManager, ArgoClient).
    cached_data_path: str = "data/cached"

    # Real-time marine sources (INCOIS / IMD / MOSDAC)
    # Leave API keys empty -> adapter reports "not connected" (no fake data).
    incois_base_url: str = "https://incois.gov.in"
    incois_api_key: str = ""
    incois_enabled: bool = False
    imd_base_url: str = "https://mausam.imd.gov.in"
    imd_api_key: str = ""
    imd_enabled: bool = False
    mosdac_base_url: str = "https://mosdac.gov.in"
    mosdac_api_key: str = ""
    mosdac_enabled: bool = False

    # Data acquisition behaviour
    data_timeout_seconds: float = 30.0
    data_retry_limit: int = 3
    data_retry_backoff_seconds: float = 2.0
    # Default poll interval seconds (used when a source has no specific interval).
    data_poll_interval_seconds: int = 900
    # Per-source poll interval overrides, e.g. {"incois": 1800, "imd": 3600}
    source_poll_interval_seconds: Dict[str, int] = {}

    # Minimal polling scheduler
    scheduler_enabled: bool = True
    scheduler_idle_wait_seconds: int = 60

    # Freshness thresholds (seconds) - data older than the threshold is STALE.
    ocean_freshness_seconds: int = 6 * 3600        # 6h
    weather_freshness_seconds: int = 3 * 3600      # 3h
    wave_freshness_seconds: int = 6 * 3600         # 6h
    tide_freshness_seconds: int = 24 * 3600        # 24h
    pfz_freshness_seconds: int = 24 * 3600         # 24h
    warning_freshness_seconds: int = 3 * 3600      # 3h

    # Physical plausibility bounds for validation (configurable)
    sst_min_c: float = -2.5
    sst_max_c: float = 45.0
    wave_max_m: float = 20.0
    wind_max_ms: float = 70.0
    current_max_ms: float = 5.0

    # Embeddings (hybrid RAG). Leave empty -> retrieval is FTS-only.
    embeddings_api_key: str = ""
    embeddings_endpoint: str = ""
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dimensions: int = 1536

    # Orchestration (Phase 4) execution bounds.
    orchestrator_max_tasks: int = 12
    orchestrator_max_tool_calls: int = 30
    orchestrator_max_retries: int = 2
    orchestrator_max_total_retries: int = 6
    orchestrator_max_repairs: int = 2
    orchestrator_parallel: int = 4
    orchestrator_timeout_seconds: float = 60.0
    orchestrator_task_timeout_seconds: float = 30.0
    orchestrator_planner_llm_enabled: bool = False

    # Phase 7 input guards - bound request size at the edge so no single
    # message can create unbounded parsing/embedding work.
    orchestrator_max_message_chars: int = 4000
    websocket_max_message_chars: int = 4000

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    max_audio_size_mb: int = 10
    rate_limit_rpm: int = 60
    cors_origins: List[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # ------------------------------------------------------------------
    # Phase 11 - Proactive marine intelligence & autonomous operations.
    # ------------------------------------------------------------------
    # Bounded proactive engine (event/alert scheduling).  One worker processes
    # the event queue deterministically; multiple workers would duplicate work,
    # so this must be 1 in production or run behind a leader lock.
    proactive_enabled: bool = True
    proactive_worker_queue_size: int = 128
    proactive_tick_seconds: int = 60            # event/alert evaluation cadence
    proactive_source_refresh_seconds: int = 900 # source refresh cadence

    # Geofence monitoring
    geofence_approach_km: float = 25.0          # distance at which APPROACHING fires
    geofence_refresh_seconds: int = 120
    geofence_max_active: int = 64               # bounded set of monitored vessels

    # Restriction monitoring
    restriction_scan_seconds: int = 300
    restriction_max_active: int = 256

    # Alert lifecycle bounds
    alert_dedupe_window_seconds: int = 3600     # identical events deduped within
    alert_default_ttl_seconds: int = 24 * 3600  # default validity if none given
    alert_max_escalations: int = 3              # CAUTION->WARNING->HIGH->CRITICAL
    alert_escalation_step_seconds: int = 3600   # min time before an escalation

    # Material-change threshold (Phase 12 ML integration): do not raise an alert
    # purely because an ML score changed by less than this (0..1).
    alert_ml_material_change: float = 0.10

    # Source health : consecutive failures that flip AVAILABLE -> FAILED.
    source_failure_threshold: int = 3
    source_recovery_ticks: int = 2               # successful ticks to flip RECOVERED

    # User alert preferences default mode per category.
    alert_default_mode: str = "important_only"   # immediate|important_only|digest|disabled


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()