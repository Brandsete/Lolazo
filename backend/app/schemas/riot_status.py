from pydantic import BaseModel, Field


class RiotStatusResponse(BaseModel):
    """Schema indicating Riot API key configuration status without leaking keys."""

    is_configured: bool = Field(
        ...,
        description="Whether a valid, non-placeholder Riot API key is configured",
    )
    status: str = Field(
        ...,
        description="Status descriptor: 'configured', 'placeholder', or 'missing'",
        examples=["configured", "placeholder", "missing"],
    )
    message: str = Field(
        ...,
        description="Human readable explanation of the API key status",
    )
    key_format_valid: bool = Field(
        ...,
        description="Indicates whether the key starts with the standard RGAPI prefix",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_configured": False,
                "status": "placeholder",
                "message": (
                    "Riot API key is using placeholder. Set RIOT_API_KEY in .env."
                ),
                "key_format_valid": True,
            }
        }
    }
