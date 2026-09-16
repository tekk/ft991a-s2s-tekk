"""
Integration Tests for REST API Endpoints, WebSocket Telemetry, and State Machine.
"""

import time
import json
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app import app
from backend.config import config_manager
from backend.orchestrator import orchestrator


@pytest.fixture(autouse=True)
async def setup_orchestrator():
    config_manager.save({"simulated_mode": True, "callsign": "AI7HAM"})
    await orchestrator.start()
    yield
    await orchestrator.stop()


@pytest.mark.asyncio
async def test_api_config_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/config
        res = await client.get("/api/config")
        assert res.status_code == 200
        data = res.json()
        assert data["callsign"] == "AI7HAM"
        assert "openai_api_key_masked" in data

        # POST /api/config
        update_payload = {"callsign": "W1AW", "s_meter_threshold": 95}
        res_post = await client.post("/api/config", json=update_payload)
        assert res_post.status_code == 200
        data_post = res_post.json()
        assert data_post["callsign"] == "W1AW"
        assert data_post["s_meter_threshold"] == 95

        # Revert
        await client.post("/api/config", json={"callsign": "AI7HAM", "s_meter_threshold": 80})


@pytest.mark.asyncio
async def test_api_hardware_discovery_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ports
        res_ports = await client.get("/api/ports")
        assert res_ports.status_code == 200
        assert isinstance(res_ports.json(), list)

        # Devices
        res_dev = await client.get("/api/devices")
        assert res_dev.status_code == 200
        devices = res_dev.json()
        assert "inputs" in devices
        assert "outputs" in devices


@pytest.mark.asyncio
async def test_api_storage_and_purge():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/storage")
        assert res.status_code == 200
        data = res.json()
        assert "free_mb" in data
        assert "recordings_mb" in data

        # Purge endpoint
        res_purge = await client.post("/api/purge-recordings")
        assert res_purge.status_code == 200
        assert "purged" in res_purge.json()


@pytest.mark.asyncio
async def test_api_ptt_and_simulate_rx():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Manual PTT
        res_ptt = await client.post("/api/ptt", json={"active": True})
        assert res_ptt.status_code == 200
        assert orchestrator.radio.poll_telemetry()["ptt_active"] is True

        res_unkey = await client.post("/api/ptt", json={"active": False})
        assert res_unkey.status_code == 200
        assert orchestrator.radio.poll_telemetry()["ptt_active"] is False

        # Simulate RX
        res_sim = await client.post("/api/simulate-rx?duration=1.0")
        assert res_sim.status_code == 200
        assert res_sim.json()["status"] == "ok"
