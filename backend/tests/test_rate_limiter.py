import time

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limiter import InMemoryRateLimiter, rate_limiter
from app.main import app


def test_rate_limiter_unit_logic():
    """Verify sliding-window unit logic for allowing and throttling."""
    limiter = InMemoryRateLimiter(requests_per_minute=3, window_seconds=0.5)

    ip = "192.168.1.100"

    # Request 1, 2, 3: Allowed
    allowed, limit, remaining, retry_after = limiter.check(ip)
    assert allowed is True
    assert remaining == 2

    allowed, limit, remaining, retry_after = limiter.check(ip)
    assert allowed is True
    assert remaining == 1

    allowed, limit, remaining, retry_after = limiter.check(ip)
    assert allowed is True
    assert remaining == 0

    # Request 4: Throttled (exceeded limit of 3)
    allowed, limit, remaining, retry_after = limiter.check(ip)
    assert allowed is False
    assert remaining == 0
    assert retry_after >= 1

    # After window expiration (0.6s)
    time.sleep(0.55)
    allowed, limit, remaining, retry_after = limiter.check(ip)
    assert allowed is True
    assert remaining == 2


@pytest.mark.asyncio
async def test_api_rate_limiter_throttling_http_429(monkeypatch):
    """Verify that excessive requests to the FastAPI application return HTTP 429."""
    rate_limiter.reset()
    # Temporarily set limit to 3 requests for testing
    monkeypatch.setattr(rate_limiter, "limit", 3)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1st request - 200 OK
        r1 = await client.get("/api/health")
        assert r1.status_code == 200
        assert r1.headers.get("X-RateLimit-Limit") == "3"
        assert r1.headers.get("X-RateLimit-Remaining") == "2"

        # 2nd request - 200 OK
        r2 = await client.get("/api/health")
        assert r2.status_code == 200
        assert r2.headers.get("X-RateLimit-Remaining") == "1"

        # 3rd request - 200 OK
        r3 = await client.get("/api/health")
        assert r3.status_code == 200
        assert r3.headers.get("X-RateLimit-Remaining") == "0"

        # 4th request - 429 Too Many Requests
        r4 = await client.get("/api/health")
        assert r4.status_code == 429
        data = r4.json()
        assert data["status_code"] == 429
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in r4.headers
        assert r4.headers["X-RateLimit-Remaining"] == "0"

    rate_limiter.reset()
