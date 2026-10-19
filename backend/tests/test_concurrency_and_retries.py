import asyncio
from unittest.mock import patch

import httpx
import pytest

from app.core.config import settings
from app.core.exceptions import (
    RiotAuthException,
    RiotBadRequestException,
    RiotPlayerNotFoundException,
    RiotRateLimitException,
)
from app.services.riot_client import RiotApiClient


@pytest.mark.asyncio
async def test_concurrency_semaphore_limits_parallel_calls():
    """Verify that RiotApiClient bounds concurrent outgoing requests using semaphore."""
    client = RiotApiClient()
    # Configure tiny semaphore limit of 2
    client._concurrency_semaphore = asyncio.Semaphore(2)

    active_count = 0
    max_observed_active = 0

    async def mock_handler(request: httpx.Request):
        nonlocal active_count, max_observed_active
        active_count += 1
        max_observed_active = max(max_observed_active, active_count)
        await asyncio.sleep(0.05)
        active_count -= 1
        return httpx.Response(200, json={"success": True})

    mock_transport = httpx.MockTransport(mock_handler)
    client._client = httpx.AsyncClient(transport=mock_transport)

    with patch.object(settings, "RIOT_API_KEY", "RGAPI-valid-key-for-test-concurrency"):
        tasks = [
            client._request(f"https://americas.api.riotgames.com/test/{i}")
            for i in range(6)
        ]
        results = await asyncio.gather(*tasks)

    assert len(results) == 6
    assert max_observed_active <= 2
    await client.aclose()


@pytest.mark.asyncio
async def test_no_retry_on_client_errors_400_401_403_404():
    """Verify that HTTP 400, 401, 403, and 404 fail fast without retrying."""
    for sc, expected_exc in [
        (400, RiotBadRequestException),
        (403, RiotAuthException),
        (404, RiotPlayerNotFoundException),
    ]:
        client = RiotApiClient()
        call_count = 0

        def make_handler(target_status: int):
            async def mock_handler(_request: httpx.Request):
                nonlocal call_count
                call_count += 1
                return httpx.Response(
                    target_status,
                    json={"status": {"status_code": target_status}},
                )

            return mock_handler

        mock_transport = httpx.MockTransport(make_handler(sc))
        client._client = httpx.AsyncClient(transport=mock_transport)

        with patch.object(settings, "RIOT_API_KEY", "RGAPI-valid-test-key-no-retries"):
            with pytest.raises(expected_exc):
                await client._request("https://americas.api.riotgames.com/test")

        # Must have been invoked exactly ONCE (no retries)
        assert call_count == 1
        await client.aclose()


@pytest.mark.asyncio
async def test_retries_transient_503_and_succeeds():
    """Verify that a transient 503 triggers retry and succeeds when server recovers."""
    client = RiotApiClient()
    call_count = 0

    async def mock_handler(_request: httpx.Request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(503, json={"error": "service unavailable"})
        return httpx.Response(200, json={"recovered": True})

    mock_transport = httpx.MockTransport(mock_handler)
    client._client = httpx.AsyncClient(transport=mock_transport)

    with patch.object(settings, "RIOT_API_KEY", "RGAPI-valid-test-key-retry"):
        with patch.object(settings, "RIOT_MAX_RETRIES", 2):
            result = await client._request("https://americas.api.riotgames.com/test")

    assert call_count == 2
    assert result == {"recovered": True}
    await client.aclose()


@pytest.mark.asyncio
async def test_rate_limit_429_large_retry_after_fails_immediately():
    """Verify HTTP 429 with large Retry-After raises immediately without sleeping."""
    client = RiotApiClient()
    call_count = 0


    async def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            429,
            headers={"Retry-After": "120"},
            json={"status": {"message": "Rate limit exceeded"}},
        )

    mock_transport = httpx.MockTransport(mock_handler)
    client._client = httpx.AsyncClient(transport=mock_transport)

    with patch.object(settings, "RIOT_API_KEY", "RGAPI-valid-key-rate-limit"):
        with pytest.raises(RiotRateLimitException) as exc_info:
            await client._request("https://americas.api.riotgames.com/test")

    assert call_count == 1
    assert exc_info.value.retry_after == 120
    await client.aclose()
