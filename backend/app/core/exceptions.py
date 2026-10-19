import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorResponse

logger = logging.getLogger("rifttracker.exceptions")


class RiftTrackerException(Exception):
    """Base application exception with consistent error formatting."""

    def __init__(
        self,
        detail: str,
        error_code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code


class ResourceNotFoundException(RiftTrackerException):
    """Exception raised when an entity or resource is not found (HTTP 404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
        )


class InvalidRegionException(RiftTrackerException):
    """Exception raised when an unsupported platform region is queried (HTTP 400)."""

    def __init__(self, detail: str = "Unsupported region requested") -> None:
        super().__init__(
            detail=detail,
            error_code="INVALID_REGION",
            status_code=400,
        )


class InvalidRiotIdException(RiftTrackerException):
    """Exception raised when a Riot ID is invalid (HTTP 400)."""

    def __init__(self, detail: str = "Invalid Riot ID format") -> None:
        super().__init__(
            detail=detail,
            error_code="INVALID_RIOT_ID",
            status_code=400,
        )


class InvalidQueryParameterException(RiftTrackerException):
    """Exception raised when a query parameter fails validation (HTTP 400)."""

    def __init__(self, detail: str = "Invalid query parameter supplied") -> None:
        super().__init__(
            detail=detail,
            error_code="INVALID_QUERY_PARAMETER",
            status_code=400,
        )


class ConfigurationException(RiftTrackerException):
    """Exception raised when there is an application configuration issue (HTTP 500)."""

    def __init__(self, detail: str = "Configuration error") -> None:
        super().__init__(
            detail=detail,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
        )


class RateLimitExceededException(RiftTrackerException):
    """Exception raised when client requests exceed rate limit (HTTP 429)."""

    def __init__(
        self,
        detail: str = "Application rate limit exceeded. Please retry shortly.",
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
        self.retry_after = retry_after


# -----------------------------------------------------------------------------
# Upstream Riot Games API Exceptions Hierarchy
# -----------------------------------------------------------------------------
class RiotApiException(RiftTrackerException):
    """Base exception for upstream errors returned by the Riot Games API."""

    def __init__(
        self,
        detail: str,
        error_code: str = "RIOT_API_ERROR",
        status_code: int = 502,
    ) -> None:
        super().__init__(detail=detail, error_code=error_code, status_code=status_code)


class RiotBadRequestException(RiotApiException):
    """Exception raised when Riot Games API responds with HTTP 400."""

    def __init__(
        self,
        detail: str = "Riot Games API rejected the request with HTTP 400.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_BAD_REQUEST",
            status_code=400,
        )


class RiotUnauthorizedException(RiotApiException):
    """Exception raised when Riot Games API rejects credentials (HTTP 401)."""

    def __init__(
        self,
        detail: str = "Riot Games API authentication token is missing or unauthorized.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_UNAUTHORIZED",
            status_code=401,
        )


class RiotForbiddenException(RiotApiException):
    """Exception raised when Riot Games API forbids resource access (HTTP 403)."""

    def __init__(
        self,
        detail: str = "Riot Games API key is missing, invalid or expired.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_API_AUTH_ERROR",
            status_code=403,
        )



# Backward-compatible alias for existing tests
class RiotAuthException(RiotForbiddenException):
    """Alias for RiotForbiddenException preserved for backward compatibility."""

    pass


class RiotPlayerNotFoundException(RiotApiException):
    """Exception raised when a player/account/summoner is not found (HTTP 404)."""

    def __init__(
        self,
        detail: str = "Player not found in Riot Games database.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="PLAYER_NOT_FOUND",
            status_code=404,
        )


class RiotMatchNotFoundException(RiotApiException):
    """Exception raised when a specific match ID is not found (HTTP 404)."""

    def __init__(
        self,
        detail: str = "Match not found in Riot Games database.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="MATCH_NOT_FOUND",
            status_code=404,
        )


class RiotRateLimitException(RiotApiException):
    """Exception raised when Riot Games API rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        detail: str = "Riot Games API rate limit exceeded. Please retry shortly.",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
        self.retry_after = retry_after


class RiotServerException(RiotApiException):
    """Exception raised when Riot Games API responds with 5xx error (HTTP 502)."""

    def __init__(
        self,
        detail: str = "Riot Games upstream service unavailable.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_UPSTREAM_ERROR",
            status_code=502,
        )


class RiotServiceUnavailableException(RiotApiException):
    """Exception raised when Riot Games API indicates temporary downtime (HTTP 503)."""

    def __init__(
        self,
        detail: str = "Riot Games API is currently unavailable.",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_SERVICE_UNAVAILABLE",
            status_code=503,
        )
        self.retry_after = retry_after


class RiotTimeoutException(RiotApiException):
    """Exception raised when a request to Riot Games API times out (HTTP 504)."""

    def __init__(
        self,
        detail: str = "Request to Riot Games API timed out.",
    ) -> None:
        super().__init__(
            detail=detail,
            error_code="RIOT_API_TIMEOUT",
            status_code=504,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI with safe outputs."""

    @app.exception_handler(RiftTrackerException)
    async def rifttracker_exception_handler(
        _request: Request, exc: RiftTrackerException
    ) -> JSONResponse:
        error = ErrorResponse(
            detail=exc.detail,
            error_code=exc.error_code,
            status_code=exc.status_code,
            timestamp=datetime.now(UTC),
        )
        headers = {}
        if hasattr(exc, "retry_after") and exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=exc.status_code,
            content=error.model_dump(mode="json"),
            headers=headers if headers else None,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        error = ErrorResponse(
            detail=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            status_code=exc.status_code,
            timestamp=datetime.now(UTC),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Sanitize validation errors to avoid leaking internal state or raw input
        safe_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            msg = err.get("msg", "Invalid parameter")
            safe_errors.append(f"{loc}: {msg}")

        detail_msg = f"Validation error: {'; '.join(safe_errors)}"
        error = ErrorResponse(
            detail=detail_msg,
            error_code="VALIDATION_ERROR",
            status_code=422,
            timestamp=datetime.now(UTC),
        )
        return JSONResponse(
            status_code=422,
            content=error.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all handler ensuring internal 500 exceptions NEVER leak secrets."""
        logger.error("Unhandled server exception occurred: %s", type(exc).__name__)
        error = ErrorResponse(
            detail="An unexpected internal server error occurred.",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500,
            timestamp=datetime.now(UTC),
        )
        return JSONResponse(
            status_code=500,
            content=error.model_dump(mode="json"),
        )

