"""
FastAPI server example demonstrating flaredantic with SSE notifications.
Run: uvicorn server:app --reload
"""
import asyncio
import json
from queue import Queue
from threading import Thread
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flaredantic import (
    tunnel_manager,
    TunnelProvider,
    NotifyEvent,
    NotifyData,
)


# Event queue for SSE
event_queue: Queue[NotifyData] = Queue()


def notification_handler(data: NotifyData) -> None:
    """Handler that puts notifications into the queue for SSE"""
    event_queue.put(data)


# Subscribe to notifications
tunnel_manager.subscribe(notification_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cleanup on shutdown"""
    yield
    tunnel_manager.stop()


app = FastAPI(
    title="Flaredantic Demo",
    description="Live tunnel management with SSE notifications",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TunnelRequest(BaseModel):
    provider: str = "cloudflare"
    port: int = 8000
    verbose: bool = False


class TunnelResponse(BaseModel):
    status: str
    url: Optional[str] = None
    provider: Optional[str] = None
    message: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the frontend"""
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/events")
async def events():
    """SSE endpoint for live notifications"""
    async def event_generator():
        while True:
            try:
                # Non-blocking check with timeout
                await asyncio.sleep(0.1)
                if not event_queue.empty():
                    data = event_queue.get_nowait()
                    event_dict = {
                        "event": data.event.value,
                        "message": data.message,
                        "data": data.data
                    }
                    yield f"data: {json.dumps(event_dict)}\n\n"
            except asyncio.CancelledError:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/tunnel/start", response_model=TunnelResponse)
async def start_tunnel(request: TunnelRequest):
    """Start a tunnel with the specified provider"""
    try:
        # Validate provider
        try:
            provider = TunnelProvider(request.provider)
        except ValueError:
            raise HTTPException(400, f"Invalid provider: {request.provider}")

        # Build config based on provider
        config = {
            "port": request.port,
            "verbose": request.verbose
        }

        # Add provider-specific config
        if provider == TunnelProvider.MICROSOFT:
            config["tunnel_id"] = "flaredantic-demo"

        # Start tunnel in background thread to not block
        def start():
            try:
                tunnel_manager.create_tunnel(provider, config)
            except Exception as e:
                event_queue.put(NotifyData(
                    event=NotifyEvent.ERROR,
                    message=str(e)
                ))

        thread = Thread(target=start, daemon=True)
        thread.start()

        return TunnelResponse(
            status="starting",
            provider=request.provider,
            message=f"Starting {request.provider} tunnel on port {request.port}..."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/tunnel/stop", response_model=TunnelResponse)
async def stop_tunnel():
    """Stop the current tunnel"""
    if not tunnel_manager.is_running:
        return TunnelResponse(
            status="stopped",
            message="No tunnel is running"
        )

    tunnel_manager.stop()
    return TunnelResponse(
        status="stopped",
        message="Tunnel stopped successfully"
    )


@app.get("/tunnel/status", response_model=TunnelResponse)
async def tunnel_status():
    """Get current tunnel status"""
    if tunnel_manager.is_running:
        return TunnelResponse(
            status="running",
            url=tunnel_manager.tunnel_url,
            provider=tunnel_manager.provider.value if tunnel_manager.provider else None
        )
    return TunnelResponse(
        status="stopped",
        message="No tunnel is running"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

