# FloatChat API Main Application

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.client import init_db, close_db, get_session
from app.routers import chat, profiles, voice, health, anomalies, scenarios, risk, exports, datasets, query_runs, marine, mcp, orchestrate
from app.datasources.registry import build_registry
from app.ingestion import IngestionPipeline, SourcePollingScheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting FloatChat API...")
    scheduler: SourcePollingScheduler | None = None
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    if settings.scheduler_enabled:
        registry = build_registry(settings)
        pipeline = IngestionPipeline(settings, registry, get_session)
        scheduler = SourcePollingScheduler(settings, registry, pipeline)
        app.state.scheduler = scheduler
        app.state.scheduler_task = asyncio.create_task(scheduler.run())
        logger.info("Marine data scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down FloatChat API...")
    if scheduler is not None:
        await scheduler.shutdown()
        task = getattr(app.state, "scheduler_task", None)
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    await close_db()


app = FastAPI(
    title="FloatChat API",
    description="Voice-first, multilingual, explainable AI interface for ARGO ocean data",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.log_level == "DEBUG" else None,
    redoc_url="/redoc" if settings.log_level == "DEBUG" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(profiles.router)
app.include_router(voice.router)
app.include_router(anomalies.router)
app.include_router(scenarios.router)
app.include_router(risk.router)
app.include_router(exports.router)
app.include_router(datasets.router)
app.include_router(query_runs.router)
app.include_router(marine.router)
app.include_router(mcp.router)
app.include_router(orchestrate.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "type": "internal_error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url),
        },
    )


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "FloatChat API",
        "version": "0.1.0",
        "description": "Voice-first, multilingual, explainable AI interface for ARGO ocean data",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.log_level == "DEBUG",
        log_level=settings.log_level.lower(),
    )