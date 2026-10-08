"""
Unit tests for new Pipecat REST API Endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app
from backend.config import config_manager


@pytest.fixture(autouse=True)
def setup_config():
    config_manager.save({"simulated_mode": True, "callsign": "AI7HAM"})


@pytest.mark.asyncio
async def test_api_skills_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/skills
        res = await client.get("/api/skills")
        assert res.status_code == 200
        skills = res.json()
        assert len(skills) >= 4
        assert any(s["name"] == "lookup_callsign" for s in skills)

        # 2. POST /api/skills (create custom)
        new_skill = {
            "name": "test_endpoint_skill",
            "description": "A temporary skill for endpoint testing",
            "parameters": {"type": "object", "properties": {}}
        }
        res_post = await client.post("/api/skills", json=new_skill)
        assert res_post.status_code == 200

        # 3. POST /api/skills/{name}/test
        res_test = await client.post("/api/skills/lookup_callsign/test", json={"callsign": "W1AW"})
        assert res_test.status_code == 200
        test_data = res_test.json()
        assert test_data["status"] == "ok"
        assert test_data["result"]["callsign"] == "W1AW"

        # 4. DELETE /api/skills/{name}
        res_del = await client.delete("/api/skills/test_endpoint_skill")
        assert res_del.status_code == 200


@pytest.mark.asyncio
async def test_api_system_prompt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/system-prompt
        res = await client.get("/api/system-prompt")
        assert res.status_code == 200
        data = res.json()
        assert "system_prompt" in data
        assert "AI7HAM" in data["system_prompt"]

        # POST /api/system-prompt
        custom = "You are an AI station operator on 20 meters. Keep it under 1 sentence."
        res_update = await client.post("/api/system-prompt", json={"system_prompt": custom})
        assert res_update.status_code == 200
        assert res_update.json()["custom_system_prompt"] == custom

        # Verify updated
        res_check = await client.get("/api/system-prompt")
        assert res_check.json()["system_prompt"] == custom
        assert res_check.json()["is_custom"] is True

        # Revert
        await client.post("/api/system-prompt", json={"system_prompt": ""})


@pytest.mark.asyncio
async def test_api_providers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/providers
        res = await client.get("/api/providers")
        assert res.status_code == 200
        data = res.json()
        assert "active" in data
        assert "available" in data
        assert "languages" in data

        # POST /api/providers
        updates = {
            "pipeline_mode": "cascaded",
            "stt_provider": "deepgram",
            "llm_provider": "groq",
            "tts_provider": "cartesia",
            "stt_language": "es",
            "tts_language": "es"
        }
        res_post = await client.post("/api/providers", json=updates)
        assert res_post.status_code == 200
        assert res_post.json()["status"] == "ok"

        # Verify updated
        res_check = await client.get("/api/providers")
        data_check = res_check.json()
        assert data_check["active"]["llm"] == "groq"
        assert data_check["languages"]["stt"] == "es"

        # Revert
        await client.post("/api/providers", json={"stt_language": "en", "tts_language": "en", "llm_provider": "openai"})


@pytest.mark.asyncio
async def test_api_hardware_auto_detect():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_port = await client.post("/api/auto-detect-port")
        assert res_port.status_code == 200
        assert res_port.json()["status"] == "ok"

        res_audio = await client.post("/api/auto-detect-audio")
        assert res_audio.status_code == 200
        assert res_audio.json()["status"] == "ok"
