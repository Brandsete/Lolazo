import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_riot_status_endpoint_structure():
    """Verify that /api/riot/status returns HTTP 200 with required schema fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/riot/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_configured" in data
        assert isinstance(data["is_configured"], bool)
        assert "status" in data
        assert "message" in data
        assert "key_format_valid" in data


@pytest.mark.asyncio
async def test_riot_status_never_reveals_secret_key():
    """Security test: Ensure that the response NEVER leaks the actual API key string."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/riot/status")
        assert response.status_code == 200
        body_str = response.text

        # Verify exact key value is not present in response body
        assert settings.RIOT_API_KEY not in body_str
        # Verify no header leaks the key
        for header_val in response.headers.values():
            assert settings.RIOT_API_KEY not in header_val


@pytest.mark.asyncio
async def test_riot_status_when_configured(monkeypatch):
    """Verify behavior when a valid developer key format is supplied via environment."""
    dummy_key = "RGAPI-99999999-aaaa-bbbb-cccc-dddddddddddd"
    monkeypatch.setattr(settings, "RIOT_API_KEY", dummy_key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/riot/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert data["status"] == "configured"
        assert data["key_format_valid"] is True
        # Even with a simulated key, it must not be in the response
        assert dummy_key not in response.text


@pytest.mark.asyncio
async def test_riot_status_when_empty(monkeypatch):
    """Verify behavior when RIOT_API_KEY is empty."""
    monkeypatch.setattr(settings, "RIOT_API_KEY", "")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/riot/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["status"] == "missing"
