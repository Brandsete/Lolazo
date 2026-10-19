import logging
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.logging_config import SensitiveDataFilter, sanitize_sensitive_data
from app.main import app


def test_sensitive_data_redaction_utility():
    """Verify that sanitize_sensitive_data redacts API keys and tokens."""
    raw_message = (
        "Request sent with key RGAPI-11223344-5566-7788-9900-aabbccddeeff to upstream"
    )
    sanitized = sanitize_sensitive_data(raw_message)
    assert "RGAPI-11223344-5566-7788-9900-aabbccddeeff" not in sanitized
    assert "RGAPI-[REDACTED]" in sanitized

    token_header = "Headers: X-Riot-Token: RGAPI-secret-token-value-here"
    sanitized_header = sanitize_sensitive_data(token_header)
    assert "secret-token-value-here" not in sanitized_header


def test_sensitive_data_logging_filter():
    """Verify that logging filter scrubs sensitive keys from log records."""
    log_filter = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Error authenticating with RGAPI-secret-key-1234567890",
        args=(),
        exc_info=None,
    )
    result = log_filter.filter(record)
    assert result is True
    assert "RGAPI-secret-key-1234567890" not in record.msg
    assert "RGAPI-[REDACTED]" in record.msg


@pytest.mark.asyncio
async def test_security_headers_present_on_all_responses():
    """Verify security headers are attached to API responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert res.headers.get("X-XSS-Protection") == "1; mode=block"
        assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_cors_restrictive_methods_preflight():
    """Verify CORS preflight restricts methods to safe read-only operations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Preflight OPTIONS request
        res = await client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        allow_methods = res.headers.get("Access-Control-Allow-Methods", "")
        # Should NOT allow destructive POST/PUT/DELETE
        assert "DELETE" not in allow_methods
        assert "PUT" not in allow_methods


@pytest.mark.asyncio
async def test_unhandled_500_exception_never_leaks_traceback_or_secrets():
    """Verify unhandled internal errors return clean schema without leaking secrets."""

    with patch(
        "app.services.player_service.PlayerService.get_player_profile",
        side_effect=RuntimeError(f"Database crash with secret {settings.RIOT_API_KEY}"),
    ):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/players/Faker/KR1?region=kr")
            assert res.status_code == 500
            data = res.json()
            assert data["status_code"] == 500
            assert data["error_code"] == "INTERNAL_SERVER_ERROR"
            # Ensure secret key is NEVER leaked in response text
            assert settings.RIOT_API_KEY not in res.text
            assert "Database crash" not in res.text
            assert "Traceback" not in res.text
