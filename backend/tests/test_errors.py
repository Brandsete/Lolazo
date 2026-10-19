import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_404_error_response_structure():
    """Verify that 404 Not Found returns consistent ErrorResponse schema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/unknown_endpoint_xyz")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error_code" in data
        assert "status_code" in data
        assert "timestamp" in data
        assert data["status_code"] == 404
        assert data["error_code"] == "HTTP_404"
