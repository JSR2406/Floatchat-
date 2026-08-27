# Backend Configuration
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/floatchat"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_storage_bucket: str = "floatchat-data"

    # LLM - OpenRouter for free tier access
    llm_provider: str = "openrouter"
    llm_api_key: str = ""
    llm_model: str = "anthropic/claude-3.5-sonnet"  # Best free tier model on OpenRouter
    llm_temperature: float = 0.1

    # Voice Providers - Sarvam + ElevenLabs for free tier
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

    # Demo Mode
    demo_mode: bool = False
    cached_data_path: str = "/app/data/cached"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    max_audio_size_mb: int = 10
    rate_limit_rpm: int = 60
    cors_origins: List[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()