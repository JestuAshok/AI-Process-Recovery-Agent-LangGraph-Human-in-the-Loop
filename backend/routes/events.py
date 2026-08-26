import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api", tags=["Real-time Streaming"])

# Global event queue for broadcasting to connected SSE clients
_subscribers = set()


async def event_generator() -> AsyncGenerator[str, None]:
    """Streams server-sent events to frontend UI clients."""
    queue = asyncio.Queue()
    _subscribers.add(queue)
    try:
        # Send initial connected greeting
        yield f"data: {json.dumps({'type': 'CONNECTED', 'message': 'SSE real-time stream established'})}\n\n"

        while True:
            # Check for event with 15s heartbeat
            try:
                data = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat
                yield f": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        _subscribers.discard(queue)


def broadcast_event(event_type: str, payload: dict):
    """Utility to broadcast an event to all connected UI clients."""
    data = {"type": event_type, "payload": payload}
    for queue in list(_subscribers):
        try:
            queue.put_nowait(data)
        except Exception:
            pass


@router.get("/events")
async def stream_events():
    """SSE endpoint for live UI updates."""
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
