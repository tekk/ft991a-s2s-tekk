"""
FastAPI Server and Web Application for Yaesu FT-991A AI S2S Bridge.
Serves REST API, WebSocket telemetry, audio recordings, and compiled Web UI.
Handles port 80 binding with automatic fallback to >10000.
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import config_manager, RECORDINGS_DIR, BASE_DIR
from backend.port_finder import resolve_web_port, get_local_ip_addresses
from backend.cat.ft991a import FT991ARadio
from backend.audio.devices import get_audio_devices
from backend.recording.disk_manager import disk_manager
from backend.orchestrator import orchestrator
from backend.console_ui import run_console_dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

app = FastAPI(title="Yaesu FT-991A AI S2S Bridge")

# Allow CORS for development (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


# --- REST API Endpoints ---

@app.get("/api/config")
async def get_config():
    """Get active configuration with masked API key."""
    return config_manager.get().masked_dict()


@app.post("/api/config")
async def update_config(updates: Dict[str, Any]):
    """Update settings and re-initialize connections if needed."""
    cfg = config_manager.save(updates)
    await orchestrator.reload_radio_and_audio()
    return cfg.masked_dict()


@app.get("/api/ports")
async def list_ports():
    """List host serial ports for CAT communication."""
    return FT991ARadio.list_serial_ports()


@app.get("/api/devices")
async def list_audio_devices():
    """List host audio input and output devices."""
    return get_audio_devices()


@app.get("/api/storage")
async def get_storage_metrics():
    """Get SBC drive capacity and recordings folder metrics."""
    return disk_manager.get_storage_stats()


@app.post("/api/purge-recordings")
async def purge_recordings():
    """Trigger manual rolling purge of oldest recordings."""
    result = disk_manager.check_and_auto_roll()
    return result


@app.get("/api/recordings")
async def get_recordings():
    """List recent audio transmissions."""
    return orchestrator.transmission_log


@app.post("/api/simulate-rx")
async def trigger_simulate_rx(duration: float = 4.0):
    """Simulate an incoming radio transmission breaking squelch."""
    orchestrator.trigger_simulated_rx(duration=duration)
    return {"status": "ok", "message": f"Triggered simulated RX for {duration}s"}


@app.post("/api/ptt")
async def set_manual_ptt(payload: Dict[str, bool]):
    """Manually key or release transceiver PTT."""
    active = payload.get("active", False)
    orchestrator.set_manual_ptt(active)
    return {"status": "ok", "ptt_active": active}


# --- WebSocket Telemetry Hub ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    orchestrator.register_websocket(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "ptt":
                orchestrator.set_manual_ptt(data.get("active", False))
            elif action == "simulate_rx":
                orchestrator.trigger_simulated_rx(data.get("duration", 4.0))
            elif action == "set_threshold":
                new_thresh = int(data.get("threshold", 80))
                config_manager.save({"s_meter_threshold": new_thresh})
    except WebSocketDisconnect:
        orchestrator.unregister_websocket(websocket)
    except Exception:
        orchestrator.unregister_websocket(websocket)


# --- Static Audio Recordings Serving ---
app.mount("/recordings", StaticFiles(directory=str(RECORDINGS_DIR)), name="recordings")


# --- Frontend Serving ---
@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    # Temporary fallback landing if dist not yet built
    return JSONResponse({
        "status": "online",
        "service": "Yaesu FT-991A AI S2S Bridge",
        "info": "Frontend is building. Access /api/config or WebSocket on /ws."
    })


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


# --- Application Startup & CLI Runner ---

async def main():
    parser = argparse.ArgumentParser(description="Yaesu FT-991A OpenAI Realtime S2S Transceiver Bridge")
    parser.add_argument("--port", "-p", type=int, default=80, help="Target Web UI port (default: 80)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host binding (default: 0.0.0.0)")
    parser.add_argument("--mock", action="store_true", help="Run with simulated radio hardware")
    parser.add_argument("--no-console", action="store_true", help="Disable Rich terminal dashboard")
    args = parser.parse_args()

    if args.mock:
        config_manager.save({"simulated_mode": True})

    # 1. Resolve Port with >10000 Fallback
    target_port, was_fallback = resolve_web_port(preferred_port=args.port, host=args.host)
    if was_fallback:
        print(f"\n[NOTICE] Port {args.port} is occupied or restricted. Automatically selected free port: {target_port}")
    else:
        print(f"\n[OK] Successfully bound to target port: {target_port}")

    # 2. Announce URLs
    local_ips = get_local_ip_addresses()
    primary_url = f"http://{local_ips[0]}:{target_port}" if target_port != 80 else f"http://{local_ips[0]}"
    print(f"\n=======================================================")
    print(f" YAESU FT-991A OPENAI REALTIME S2S APPLIANCE")
    print(f" Station Callsign: {config_manager.get().callsign}")
    print(f" Web UI Reachable At:")
    for ip in local_ips:
        p_str = f":{target_port}" if target_port != 80 else ""
        print(f"   -> http://{ip}{p_str}")
    print(f"   -> http://localhost:{target_port}" if target_port != 80 else "   -> http://localhost")
    print(f"=======================================================\n")

    # 3. Start Orchestrator
    await orchestrator.start()

    # 4. Configure Uvicorn Server
    uvi_config = uvicorn.Config(
        app=app,
        host=args.host,
        port=target_port,
        log_level="warning",  # Keep quiet so Rich console or terminal is clean
        access_log=False,
    )
    server = uvicorn.Server(uvi_config)

    # 5. Run Server and Console concurrently
    server_task = asyncio.create_task(server.serve())

    if not args.no_console and sys.stdout.isatty():
        console_task = asyncio.create_task(run_console_dashboard(primary_url))
        tasks = [server_task, console_task]
    else:
        tasks = [server_task]

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("\nShutting down transceiver bridge...")
        await orchestrator.stop()
        server.should_exit = True


if __name__ == "__main__":
    asyncio.run(main())
