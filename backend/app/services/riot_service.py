from app.core.config import settings
from app.schemas.riot_status import RiotStatusResponse

PLACEHOLDER_SUBSTRINGS = (
    "00000000",
    "your-api-key",
    "placeholder",
    "example",
)


class RiotService:
    """Service to evaluate Riot Games API configuration status safely."""

    @staticmethod
    def get_api_status() -> RiotStatusResponse:
        """Inspect RIOT_API_KEY without exposing secret contents."""
        key = (settings.RIOT_API_KEY or "").strip()

        if not key:
            return RiotStatusResponse(
                is_configured=False,
                status="missing",
                message="RIOT_API_KEY is not defined. Add it to your .env file.",
                key_format_valid=False,
            )

        # Check standard Riot API key prefix format ('RGAPI-...')
        has_rgapi_prefix = key.upper().startswith("RGAPI-")
        is_placeholder = any(sub in key.lower() for sub in PLACEHOLDER_SUBSTRINGS)

        if is_placeholder:
            return RiotStatusResponse(
                is_configured=False,
                status="placeholder",
                message=(
                    "RIOT_API_KEY is currently set to a placeholder value. "
                    "Obtain a personal key at https://developer.riotgames.com/."
                ),
                key_format_valid=has_rgapi_prefix,
            )

        # If it has a non-placeholder value and valid prefix
        if has_rgapi_prefix and len(key) >= 20:
            return RiotStatusResponse(
                is_configured=True,
                status="configured",
                message="Riot API key is configured and ready for Phase 2.",
                key_format_valid=True,
            )

        # Non-standard key or invalid format
        return RiotStatusResponse(
            is_configured=False,
            status="invalid_format",
            message="RIOT_API_KEY does not follow standard 'RGAPI-...' prefix.",
            key_format_valid=False,
        )


riot_service = RiotService()
