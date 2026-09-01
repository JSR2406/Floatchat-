# Phase 11 - versioned proactive alert API.
#
# GET  /api/v1/alerts              - list (filter by status/severity/type)
# GET  /api/v1/alerts/{id}         - fetch one alert
# POST /api/v1/alerts/{id}/acknowledge - lifecycle ack
# POST /api/v1/alerts/preferences  - user alert preferences
# GET  /api/v1/events              - recent normalized events (observable)
#
# Realtime delivery rides the existing /api/v1/orchestrate/stream WS surface;
# alert lifecycle events are emitted through it when a frontend is attached.
# This router NEVER exposes chain-of-thought, internal prompts, DB queries,
# credentials, or raw internal tool arguments.
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query

from app.agents.proactive_agent import get_proactive_engine
from app.services.alert_repository import AlertRepository

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["alerts"])


def _repo() -> AlertRepository:
    """Return the alert repository this process exposes.  Prefer the app-bound
    repository; fall back to the proactive engine's own persistence so an
    ingested alert is always visible to the API (single source of truth)."""
    bound = getattr(_app_state, "alert_repository", None)
    if bound is not None:
        return bound
    engine_repo = get_proactive_engine().persistence
    return engine_repo or _default_repo


_default_repo = AlertRepository()
_app_state = None


def bind_alert_state(state: Any) -> None:
    """Wire the app-level alert services (engine + repository) exposed by the
    lifespan/holder so the router and realtime stream share one state."""
    global _app_state
    _app_state = state


@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None, description="created|active|..."),
    severity: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    try:
        rows = await _repo().list_alerts(status=status, limit=limit,
                                         offset=offset)
    except Exception as exc:  # noqa: BLE001 - never leak internals
        logger.exception("alerts_list_error")
        raise HTTPException(status_code=500,
                            detail="Failed to list alerts")
    if severity:
        rows = [r for r in rows if r.get("severity") == severity]
    if type:
        rows = [r for r in rows if r.get("type") == type]
    return {"alerts": rows, "total": len(rows)}


@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str) -> Dict[str, Any]:
    try:
        row = await _repo().get_alert(alert_id)
    except Exception:  # noqa: BLE001
        logger.exception("alerts_get_error")
        raise HTTPException(status_code=500, detail="Failed to get alert")
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": row}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> Dict[str, Any]:
    try:
        updated = await _repo().update_alert(
            alert_id, status="acknowledged",
            acknowledged_at=datetime.now(timezone.utc).isoformat())
        # also run the in-memory lifecycle transition on the live engine alert
        engine = get_proactive_engine()
        live = engine.acknowledge(alert_id)
    except Exception:  # noqa: BLE001
        logger.exception("alerts_ack_error")
        raise HTTPException(status_code=500, detail="Failed to acknowledge")
    if updated is None and live is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "id": alert_id}


@router.get("/events")
async def list_events(limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    engine = get_proactive_engine()
    try:
        events = await _repo().list_recent_events(limit=limit)
    except Exception:  # noqa: BLE001
        events = engine.recent_events(limit=limit)
    return {"events": events, "total": len(events)}


@router.post("/alerts/preferences")
async def set_preferences(body: Dict[str, str]) -> Dict[str, Any]:
    user_id = body.get("user_id", "default")
    changes = {k: v for k, v in body.items()
               if k in ("cyclone", "lightning", "waves", "weather",
                        "restrictions", "geofence", "pfz", "forecast",
                        "sources", "data") and v in
               ("immediate", "important_only", "digest", "disabled")}
    prefs = {}
    for category, mode in changes.items():
        prefs = await _repo().set_preference(user_id, category, mode)
    return {"user_id": user_id, "preferences": prefs}


@router.get("/proactive")
async def proactive_status() -> Dict[str, Any]:
    engine = get_proactive_engine()
    return engine.stats()