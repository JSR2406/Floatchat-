# Minimal asyncio polling scheduler for configured marine data sources.
#
# The scheduler only tracks *configured* live sources (no credentials/config ->
# it logs an idle state and stops.  It is a thin orchestration shell; all real
# behaviour lives in adapters + pipeline, keeping the layer testable.
import asyncio
import time
from typing import Dict, Optional

import structlog

from app.config import Settings
from app.datasources.registry import SourceRegistry
from app.ingestion.pipeline import IngestionPipeline

logger = structlog.get_logger(__name__)

# products that need explicit lat/lon fetch parameters we do not synthesize
_COORDINATE_REQUIRED = {"ocean", "tides", "weather_observation", "weather_forecast"}


class SourcePollingScheduler:
    """Polls configured live sources on per-source intervals.

    fetch_params: optional mapping {"source": {"product": {...kwargs}}} that a
    live deployment must supply (e.g. lat/lon centres).  Without them,
    coordinate-required products are skipped explicitly (no fabricated requests).
    """

    def __init__(
        self,
        settings: Settings,
        registry: SourceRegistry,
        pipeline: IngestionPipeline,
        fetch_params: Optional[Dict[str, Dict[str, Dict]]] = None,
    ):
        self.settings = settings
        self.registry = registry
        self.pipeline = pipeline
        self.fetch_params = fetch_params or {}
        self._stop = asyncio.Event()

    async def run(self) -> None:
        configured = [s for s in self.registry.list() if s.is_configured]
        if not configured:
            logger.info("scheduler_idle_no_configured_sources")
            await self._stop.wait()
            return
        logger.info("scheduler_start", sources=[s.name for s in configured])
        tasks = [asyncio.create_task(self._poll_loop(source_name, self._stop))
                 for source_name in (s.name for s in configured)]
        try:
            await self._stop.wait()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def shutdown(self) -> None:
        self._stop.set()

    async def _poll_loop(self, source_name: str, stop: asyncio.Event) -> None:
        interval = self.settings.source_poll_interval_seconds.get(
            source_name, self.settings.data_poll_interval_seconds)
        while not stop.is_set():
            started = time.monotonic()
            await self._poll_source(source_name)
            elapsed = time.monotonic() - started
            await asyncio.wait_for(
                asyncio.sleep(max(1.0, interval - elapsed)),
                timeout=None,
            )

    async def _poll_source(self, source_name: str) -> None:
        source = self.registry.get(source_name)
        params_map = self.fetch_params.get(source_name, {})
        for cap in source.capabilities:
            product = cap.data_product
            product_params = dict(params_map.get(product, {}))
            if product in _COORDINATE_REQUIRED and not product_params.get("lat"):
                logger.info("scheduler_skip_requires_coordinates",
                            source=source_name, product=product)
                continue
            try:
                await self.pipeline.run_product(source_name, product, product_params)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("scheduler_poll_error", source=source_name,
                               product=product, error=str(exc))