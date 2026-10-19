import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_all_regions():
    """Verify that /api/regions returns all supported regions and clusters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "clusters" in data
        assert "regions" in data
        assert data["total"] > 0
        assert "americas" in data["clusters"]
        assert "europe" in data["clusters"]
        assert "asia" in data["clusters"]
        assert "sea" in data["clusters"]


@pytest.mark.asyncio
async def test_region_cluster_mappings():
    """Verify platform IDs to regional clusters for Account-V1 and Match-V5."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions")
        assert response.status_code == 200
        regions = {
            r["platform_id"]: r["regional_cluster"] for r in response.json()["regions"]
        }

        # Americas routing
        assert regions["la1"] == "americas"
        assert regions["la2"] == "americas"
        assert regions["na1"] == "americas"
        assert regions["br1"] == "americas"

        # Europe routing
        assert regions["euw1"] == "europe"
        assert regions["eun1"] == "europe"

        # Asia routing
        assert regions["kr"] == "asia"
        assert regions["jp1"] == "asia"

        # SEA routing
        assert regions["oc1"] == "sea"


@pytest.mark.asyncio
async def test_filter_regions_by_valid_cluster():
    """Verify that filtering by cluster returns only matching regions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions?cluster=americas")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        assert all(r["regional_cluster"] == "americas" for r in data["regions"])


@pytest.mark.asyncio
async def test_filter_regions_by_invalid_cluster():
    """Verify filtering by invalid cluster returns HTTP 400 structured error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions?cluster=antarctica")
        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "INVALID_REGION"
        assert "antarctica" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_single_region():
    """Verify querying a specific platform region by ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions/la1")
        assert response.status_code == 200
        data = response.json()
        assert data["platform_id"] == "la1"
        assert data["regional_cluster"] == "americas"
        assert "Latin America North" in data["name"]


@pytest.mark.asyncio
async def test_get_single_region_not_found():
    """Verify querying an unsupported platform returns HTTP 400 structured error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/regions/mars1")
        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "INVALID_REGION"
