"""
Integration Tests for REST API /api/regulations and Configuration Synchronization.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app
from backend.config import config_manager


@pytest.mark.asyncio
async def test_get_regulations_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Default (US / AI7HAM)
        config_manager.save({"callsign": "AI7HAM", "language": "en", "regulatory_jurisdiction": "auto"})
        res = await client.get("/api/regulations")
        assert res.status_code == 200
        data = res.json()
        assert data["active_jurisdiction"] == "US"
        assert "Federal Communications Commission" in data["active_regulation"]["authority_name"]
        assert data["detected_from_callsign"] == "US"
        assert len(data["supported_regulations"]) >= 10

        # 2. Change callsign to Slovakia (OM7TEK)
        config_manager.save({"callsign": "OM7TEK", "language": "sk"})
        res_sk = await client.get("/api/regulations")
        assert res_sk.status_code == 200
        data_sk = res_sk.json()
        assert data_sk["active_jurisdiction"] == "SK"
        assert "Úrad pre reguláciu" in data_sk["active_regulation"]["authority_name"]
        assert data_sk["detected_from_callsign"] == "SK"

        # 3. Explicit override to Germany
        config_manager.save({"callsign": "OM7TEK", "regulatory_jurisdiction": "DE"})
        res_de = await client.get("/api/regulations")
        assert res_de.status_code == 200
        data_de = res_de.json()
        assert data_de["active_jurisdiction"] == "DE"
        assert "Bundesnetzagentur" in data_de["active_regulation"]["authority_name"]

        # Revert
        config_manager.save({"callsign": "AI7HAM", "language": "en", "regulatory_jurisdiction": "auto"})
