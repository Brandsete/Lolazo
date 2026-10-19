from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Schema for system health check endpoint."""

    status: str = Field(default="healthy", description="Current backend status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application semantic version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the health check",
    )
    cache_ttl_seconds: int = Field(..., description="Configured cache TTL in seconds")
    max_matches: int = Field(..., description="Max matches retrieved per summoner")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "RiftTracker API",
                "version": "0.1.0",
                "timestamp": "2026-10-16T12:00:00Z",
                "cache_ttl_seconds": 300,
                "max_matches": 20,
            }
        }
    }
