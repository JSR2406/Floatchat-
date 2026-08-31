# Phase 4 router: autonomous agentic orchestration.
#
# POST /api/v1/orchestrate  - run the Intent -> Plan -> Execute -> Synthesize
# pipeline.  The response reports the retrieval/execution status honestly and
# verification results; it never hides partial failures.
#
# Phase 6 adds GET-style WebSocket /api/v1/orchestrate/stream - the same run
# surfaced as a sequence of sanitized execution events (execution.started ->
# intent.detected -> plan.created -> task/tool/verification events ->
# response.ready).  Only safe execution metadata is streamed; never secrets or
# hidden reasoning.
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.orchestration.orchestrator import (
    OrchestrationError, OrchestratorService,
    get_orchestrator_service)

router = APIRouter(prefix="/api/v1/orchestrate", tags=["orchestrate"])


def _reject(rid: Optional[str], cid: Optional[str], reason: str) -> dict:
    return {
        "request_id": rid,
        "conversation_id": cid,
        "intent": None,
        "status": "invalid",
        "message": reason,
        "sections": [],
        "verification": None,
        "tool_calls": 0,
        "duration_ms": 0,
        "notes": {"error": reason},
    }


def _orchestrator() -> OrchestratorService:
    return get_orchestrator_service()


@router.post("")
async def orchestrate(
    message: str,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict:
    if not message or not message.strip():
        return _reject(request_id, conversation_id,
                       "A non-empty message is required.")
    if len(message) > settings.orchestrator_max_message_chars:
        return _reject(
            request_id, conversation_id,
            f"Message exceeds {settings.orchestrator_max_message_chars} "
            "character limit.")
    try:
        response = await _orchestrator().run(
            message,
            conversation_id=conversation_id,
            request_id=request_id,
        )
    except OrchestrationError as exc:
        return {
            "request_id": request_id,
            "conversation_id": conversation_id,
            "status": "error",
            "message": str(exc),
            "sections": [],
            "verification": None,
            "tool_calls": 0,
            "duration_ms": 0,
            "notes": {"error": "orchestration_error"},
        }
    return response


@router.websocket("/stream")
async def orchestrate_stream(
    websocket: WebSocket,
    message: str = "",
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Stream one executed run as sanitized events (Phase 6 #16)."""
    await websocket.accept()
    rid = request_id or f"orch-{uuid4().hex[:12]}"

    disconnected = False

    async def sink(event) -> None:
        nonlocal disconnected
        if disconnected:
            return
        try:
            await websocket.send_json(event)
        except Exception:  # noqa: BLE001 - client gone; stop streaming
            disconnected = True

    if not message or not message.strip():
        await sink({
            "event": "execution.failed",
            "request_id": rid,
            "conversation_id": conversation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "data": {"reason": "empty_message"},
        })
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
        return

    if len(message) > settings.websocket_max_message_chars:
        await sink({
            "event": "execution.failed",
            "request_id": rid,
            "conversation_id": conversation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "data": {"reason": "message_too_long",
                     "limit": settings.websocket_max_message_chars},
        })
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
        return

    from app.orchestration.stream import stream_orchestration
    try:
        await stream_orchestration(
            message,
            conversation_id=conversation_id,
            request_id=rid,
            sink=sink,
        )
    except WebSocketDisconnect:  # noqa: F841 - client closed; nothing to send
        pass
    except Exception:  # noqa: BLE001 - execution.failed already emitted by the
        pass  #               tracer; never leak internal error details.
    finally:
        try:
            if not disconnected:
                await websocket.close()
        except Exception:  # noqa: BLE001
            pass