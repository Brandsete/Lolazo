import re

from app.core.exceptions import (
    InvalidQueryParameterException,
    InvalidRegionException,
    InvalidRiotIdException,
)
from app.services.region_service import SUPPORTED_CLUSTERS, region_service

# Riot ID game name: 1-24 characters, Unicode alphanumeric, spaces, dots, dashes
RIOT_ID_NAME_REGEX = re.compile(r"^[\w\s\.\-_]{1,24}$", re.UNICODE)
# Riot ID tag line: 1-8 characters, Unicode alphanumeric
RIOT_ID_TAG_REGEX = re.compile(r"^[\w]{1,8}$", re.UNICODE)

# Match ID format: e.g. LA1_1234567890, KR_987654321
MATCH_ID_REGEX = re.compile(r"^[A-Za-z0-9]+_\d{1,20}$")

VALID_QUEUES = {
    "ranked",
    "solo",
    "flex",
    "normal",
    "blind",
    "aram",
    "all",
    "any",
    "420",
    "440",
    "400",
    "430",
    "450",
    "490",
    "1700",
}


def validate_riot_id(game_name: str, tag_line: str) -> tuple[str, str]:
    """Validate and sanitize Riot ID components against security constraints."""
    if not game_name or not isinstance(game_name, str):
        raise InvalidRiotIdException("Riot ID game name cannot be empty.")

    if not tag_line or not isinstance(tag_line, str):
        raise InvalidRiotIdException("Riot ID tag line cannot be empty.")

    cleaned_name = game_name.strip()
    cleaned_tag = tag_line.lstrip("#").strip()

    if not cleaned_name or not RIOT_ID_NAME_REGEX.match(cleaned_name):
        raise InvalidRiotIdException(
            f"Invalid Riot ID game name '{game_name}'. Must be 1-24 characters."
        )

    if not cleaned_tag or not RIOT_ID_TAG_REGEX.match(cleaned_tag):
        raise InvalidRiotIdException(
            f"Invalid Riot ID tag line '{tag_line}'. Must be 1-8 characters."
        )


    return cleaned_name, cleaned_tag


def validate_region(platform_id: str) -> str:
    """Validate that the platform region is officially supported."""
    if not platform_id or not isinstance(platform_id, str):
        raise InvalidRegionException("Region parameter cannot be empty.")

    norm_region = platform_id.lower().strip()
    # region_service.get_region_by_platform will raise InvalidRegionException if invalid
    region_info = region_service.get_region_by_platform(norm_region)
    return region_info.platform_id


def validate_cluster(cluster: str | None) -> str | None:
    """Validate that the regional cluster is valid."""
    if not cluster:
        return None
    norm_cluster = cluster.lower().strip()
    if norm_cluster not in SUPPORTED_CLUSTERS:
        valid_str = ", ".join(SUPPORTED_CLUSTERS)
        raise InvalidRegionException(
            f"Cluster '{cluster}' is invalid. Supported: {valid_str}"
        )
    return norm_cluster


def validate_matches_count(count: int, min_val: int = 1, max_val: int = 100) -> int:
    """Validate and enforce bounds for match count query parameters."""
    if not isinstance(count, int) or count < min_val or count > max_val:
        raise InvalidQueryParameterException(
            f"Parameter must be an integer between {min_val} and {max_val}."
        )
    return count


def validate_queue_param(queue: str | None) -> str | None:
    """Validate queue filter query parameter against allowed game modes."""
    if not queue:
        return None
    norm_queue = queue.lower().strip()
    if norm_queue not in VALID_QUEUES:
        allowed_str = ", ".join(sorted(VALID_QUEUES))
        raise InvalidQueryParameterException(
            f"Invalid queue parameter '{queue}'. Allowed values: {allowed_str}"
        )
    return norm_queue


def validate_match_id(match_id: str) -> str:
    """Validate match ID format and length to prevent injections or traversal."""
    if not match_id or not isinstance(match_id, str):
        raise InvalidQueryParameterException("Match ID cannot be empty.")

    cleaned_id = match_id.strip()
    if len(cleaned_id) > 40 or not MATCH_ID_REGEX.match(cleaned_id):
        raise InvalidQueryParameterException(
            f"Invalid match ID format '{match_id}'. Format like 'LA1_1234567890'."
        )
    return cleaned_id

