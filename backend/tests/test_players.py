from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.exceptions import (
    RiotAuthException,
    RiotPlayerNotFoundException,
    RiotRateLimitException,
    RiotTimeoutException,
)
from app.main import app


@pytest.mark.asyncio
async def test_get_player_profile_success():
    """Verify player profile retrieval with mocked official Riot APIs."""
    mock_account = {
        "puuid": "mock-puuid-9999",
        "gameName": "Josedeodo",
        "tagLine": "LAN",
    }
    mock_summoner = {
        "id": "mock-summoner-id-1234",
        "accountId": "mock-account-id",
        "puuid": "mock-puuid-9999",
        "profileIconId": 588,
        "summonerLevel": 412,
    }
    mock_leagues = [
        {
            "queueType": "RANKED_SOLO_5x5",
            "tier": "CHALLENGER",
            "rank": "I",
            "leaguePoints": 920,
            "wins": 150,
            "losses": 80,
            "veteran": True,
            "inactive": False,
            "freshBlood": False,
            "hotStreak": True,
        }
    ]

    with (
        patch(
            "app.services.player_service.riot_client.get_account_by_riot_id",
            new_callable=AsyncMock,
            return_value=mock_account,
        ) as mock_acc_call,
        patch(
            "app.services.player_service.riot_client.get_summoner_by_puuid",
            new_callable=AsyncMock,
            return_value=mock_summoner,
        ) as mock_sum_call,
        patch(
            "app.services.player_service.riot_client.get_league_entries_by_summoner",
            new_callable=AsyncMock,
            return_value=mock_leagues,
        ) as mock_lea_call,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/players/Josedeodo/LAN?region=la1")

            assert response.status_code == 200
            data = response.json()

            # Verify resolved data
            assert data["puuid"] == "mock-puuid-9999"
            assert data["game_name"] == "Josedeodo"
            assert data["tag_line"] == "LAN"
            assert data["region"] == "la1"
            assert data["regional_cluster"] == "americas"
            assert data["summoner_level"] == 412
            assert data["profile_icon_id"] == 588
            assert "ddragon.leagueoflegends.com" in data["profile_icon_url"]

            # Verify Solo/Duo rank
            assert data["solo_rank"] is not None
            assert data["solo_rank"]["tier"] == "CHALLENGER"
            assert data["solo_rank"]["league_points"] == 920
            assert data["solo_rank"]["win_rate"] == 65.22

            # Verify correct regional cluster was passed to Account-V1
            mock_acc_call.assert_awaited_once_with(
                game_name="Josedeodo",
                tag_line="LAN",
                regional_cluster="americas",
            )
            # Verify correct platform was passed to Summoner-V4
            mock_sum_call.assert_awaited_once_with(
                puuid="mock-puuid-9999",
                platform_id="la1",
            )
            # Verify correct summoner ID was passed to League-V4
            mock_lea_call.assert_awaited_once_with(
                summoner_id="mock-summoner-id-1234",
                platform_id="la1",
            )


@pytest.mark.asyncio
async def test_player_not_found_404():
    """Verify that a nonexistent player returns HTTP 404 standard error."""
    with patch(
        "app.services.player_service.riot_client.get_account_by_riot_id",
        new_callable=AsyncMock,
        side_effect=RiotPlayerNotFoundException("Player not found."),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            url = "/api/players/NonExistentPlayer/0000?region=la1"
            response = await client.get(url)

            assert response.status_code == 404
            data = response.json()
            assert data["status_code"] == 404
            assert data["error_code"] == "PLAYER_NOT_FOUND"


@pytest.mark.asyncio
async def test_unauthorized_key_403_never_leaks_key():
    """Verify that invalid/expired key returns 403 and never leaks key."""
    with patch(
        "app.services.player_service.riot_client.get_account_by_riot_id",
        new_callable=AsyncMock,
        side_effect=RiotAuthException("Invalid or expired RIOT_API_KEY."),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/players/Faker/KR1?region=kr")

            assert response.status_code == 403
            data = response.json()
            assert data["status_code"] == 403
            assert data["error_code"] == "RIOT_API_AUTH_ERROR"

            # Critical security check: Key is never exposed
            assert settings.RIOT_API_KEY not in response.text
            for val in response.headers.values():
                assert settings.RIOT_API_KEY not in val


@pytest.mark.asyncio
async def test_rate_limit_exceeded_429_with_retry_after():
    """Verify that HTTP 429 returns standard error and Retry-After header."""
    with patch(
        "app.services.player_service.riot_client.get_account_by_riot_id",
        new_callable=AsyncMock,
        side_effect=RiotRateLimitException(
            detail="Riot Games API rate limit exceeded.",
            retry_after=45,
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/players/Caps/EUW?region=euw1")

            assert response.status_code == 429
            data = response.json()
            assert data["status_code"] == 429
            assert data["error_code"] == "RIOT_RATE_LIMIT_EXCEEDED"
            assert response.headers.get("Retry-After") == "45"


@pytest.mark.asyncio
async def test_riot_api_timeout_504():
    """Verify that timeouts to upstream Riot API return HTTP 504."""
    with patch(
        "app.services.player_service.riot_client.get_account_by_riot_id",
        new_callable=AsyncMock,
        side_effect=RiotTimeoutException("Riot API request timed out."),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/players/Faker/KR1?region=kr")

            assert response.status_code == 504
            data = response.json()
            assert data["status_code"] == 504
            assert data["error_code"] == "RIOT_API_TIMEOUT"


@pytest.mark.asyncio
async def test_invalid_region_parameter_400():
    """Verify that providing an unsupported platform region returns HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/players/Faker/KR1?region=moon1")

        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "INVALID_REGION"
        assert "moon1" in data["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_riot_id_format_400():
    """Verify that malformed Riot ID game name or tag line returns HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid characters in gameName
        response = await client.get("/api/players/Faker$$$$$$$/KR1?region=kr")

        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "INVALID_RIOT_ID"
