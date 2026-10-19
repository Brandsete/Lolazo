import asyncio
import time
from collections import defaultdict

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.schemas.error import ErrorResponse


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per client IP address."""

    def __init__(
        self, requests_per_minute: int = 60, window_seconds: float = 60.0
    ) -> None:
        self.limit = requests_per_minute
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()

    def _cleanup_old_records(self, now: float) -> None:
        """Evict IP buckets that have no activity within the sliding window."""
        cutoff = now - self.window_seconds
        stale_ips = []
        for ip, timestamps in self._history.items():
            valid_stamps = [t for t in timestamps if t > cutoff]
            if valid_stamps:
                self._history[ip] = valid_stamps
            else:
                stale_ips.append(ip)
        for ip in stale_ips:
            self._history.pop(ip, None)
        self._last_cleanup = now

    def check(self, client_ip: str) -> tuple[bool, int, int, int]:
        """Check if request from client_ip is allowed.

        Returns:
            (allowed: bool, limit: int, remaining: int, retry_after: int)
        """
        now = time.monotonic()

        # Periodically clean up stale records every 2 minutes
        if now - self._last_cleanup > 120.0:
            self._cleanup_old_records(now)

        cutoff = now - self.window_seconds
        timestamps = [t for t in self._history[client_ip] if t > cutoff]
        self._history[client_ip] = timestamps

        if len(timestamps) >= self.limit:
            # Exceeded limit
            oldest = timestamps[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            return False, self.limit, 0, retry_after

        # Record this request
        timestamps.append(now)
        self._history[client_ip] = timestamps
        remaining = max(0, self.limit - len(timestamps))
        return True, self.limit, remaining, 0

    async def acheck(self, client_ip: str) -> tuple[bool, int, int, int]:
        """Thread-safe async rate check."""
        async with self._lock:
            return self.check(client_ip)

    def reset(self) -> None:
        """Clear all rate limiting history."""
        self._history.clear()


rate_limiter = InMemoryRateLimiter(
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60.0,
)


def get_client_ip(request: Request) -> str:
    """Extract client IP, taking into account common reverse proxy headers safely."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Use leftmost IP in X-Forwarded-For
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware to throttle incoming HTTP requests."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Do not rate limit CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = get_client_ip(request)
        allowed, limit, remaining, retry_after = await rate_limiter.acheck(client_ip)

        if not allowed:
            from datetime import UTC, datetime

            error = ErrorResponse(
                detail=f"Rate limit exceeded. Maximum {limit} req/min allowed.",
                error_code="RATE_LIMIT_EXCEEDED",
                status_code=429,
                timestamp=datetime.now(UTC),
            )

            response = JSONResponse(
                status_code=429,
                content=error.model_dump(mode="json"),
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
