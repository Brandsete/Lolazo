import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify that /api/health returns HTTP 200 and matches schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "cache_ttl_seconds" in data
        assert "max_matches" in data


@pytest.mark.asyncio
async def test_health_check_v1_alias():
    """Verify that /api/v1/health is also accessible as an alias."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify that root endpoint returns HTTP 200 and links to docs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["docs"] == "/docs"
        assert "/api/health" in data["endpoints"].values()
