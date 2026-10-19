from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Consistent error response schema for API errors."""

    detail: str = Field(..., description="Human readable description of the error")
    error_code: str = Field(..., description="Application-specific error identifier")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the error occurrence",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Resource not found",
                "error_code": "RESOURCE_NOT_FOUND",
                "status_code": 404,
                "timestamp": "2026-10-16T12:00:00Z",
            }
        }
    }
