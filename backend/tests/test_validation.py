import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import (
    InvalidQueryParameterException,
    InvalidRegionException,
    InvalidRiotIdException,
)
from app.core.validation import (
    validate_cluster,
    validate_match_id,
    validate_matches_count,
    validate_queue_param,
    validate_region,
    validate_riot_id,
)
from app.main import app


def test_validate_riot_id_valid_and_invalid():
    """Verify Riot ID validation rules for name and tag."""
    # Valid Riot IDs
    name, tag = validate_riot_id("Faker", "KR1")
    assert name == "Faker" and tag == "KR1"

    name, tag = validate_riot_id("Hide on bush", "#KR1")
    assert name == "Hide on bush" and tag == "KR1"

    name, tag = validate_riot_id("Josedeodo", "LAN")
    assert name == "Josedeodo" and tag == "LAN"

    # Invalid names
    with pytest.raises(InvalidRiotIdException):
        validate_riot_id("", "KR1")

    with pytest.raises(InvalidRiotIdException):
        validate_riot_id("A" * 25, "KR1")  # >24 chars

    with pytest.raises(InvalidRiotIdException):
        validate_riot_id("Hacker<script>", "KR1")

    # Invalid tags
    with pytest.raises(InvalidRiotIdException):
        validate_riot_id("Faker", "")

    with pytest.raises(InvalidRiotIdException):
        validate_riot_id("Faker", "TAGTOOLONG99")  # >8 chars


def test_validate_region_valid_and_invalid():
    """Verify platform region validation."""
    assert validate_region("la1") == "la1"
    assert validate_region("LA1") == "la1"
    assert validate_region("kr") == "kr"
    assert validate_region("euw1") == "euw1"

    with pytest.raises(InvalidRegionException):
        validate_region("moon1")

    with pytest.raises(InvalidRegionException):
        validate_region("")


def test_validate_cluster_valid_and_invalid():
    """Verify regional cluster validation."""
    assert validate_cluster("americas") == "americas"
    assert validate_cluster("EUROPE") == "europe"
    assert validate_cluster(None) is None

    with pytest.raises(InvalidRegionException):
        validate_cluster("atlantis")


def test_validate_matches_count_bounds():
    """Verify match count bounds enforcement."""
    assert validate_matches_count(1) == 1
    assert validate_matches_count(20) == 20
    assert validate_matches_count(100) == 100

    with pytest.raises(InvalidQueryParameterException):
        validate_matches_count(0)

    with pytest.raises(InvalidQueryParameterException):
        validate_matches_count(101)


def test_validate_queue_parameter():
    """Verify queue parameter validation."""
    assert validate_queue_param("ranked") == "ranked"
    assert validate_queue_param("SOLO") == "solo"
    assert validate_queue_param("flex") == "flex"
    assert validate_queue_param("aram") == "aram"
    assert validate_queue_param(None) is None

    with pytest.raises(InvalidQueryParameterException):
        validate_queue_param("malicious_queue")


def test_validate_match_id():
    """Verify match ID format validation."""
    assert validate_match_id("LA1_1234567890") == "LA1_1234567890"
    assert validate_match_id("KR_998877") == "KR_998877"

    with pytest.raises(InvalidQueryParameterException):
        validate_match_id("../etc/passwd")

    with pytest.raises(InvalidQueryParameterException):
        validate_match_id("")


@pytest.mark.asyncio
async def test_endpoint_invalid_queue_parameter_returns_400():
    """Verify API endpoint returns HTTP 400 when an invalid queue filter is supplied."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/players/Faker/KR1/stats?region=kr&queue=bad_queue_value"
        )
        assert res.status_code == 400
        data = res.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "INVALID_QUERY_PARAMETER"
