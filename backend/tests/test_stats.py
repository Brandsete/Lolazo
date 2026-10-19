from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.stats_service import stats_service

MOCK_PLAYER_CONTEXT = {
    "game_name": "Josedeodo",
    "tag_line": "LAN",
    "puuid": "mock-puuid-lan-1234",
    "region": "la1",
    "regional_cluster": "americas",
}


def test_stats_formulas_normal_calculation():
    """Verify standard formula calculations for win rate, KDA, CS/min and economy."""
    matches = [
        {
            "match_id": "LA1_1001",
            "win": True,
            "kills": 10,
            "deaths": 2,
            "assists": 5,
            "cs": 200,
            "gold_earned": 15000,
            "vision_score": 30,
            "game_duration": 1800,  # 30 min
            "champion_id": 222,
            "champion_name": "Jinx",
            "position": "BOTTOM",
            "objectives": {},
        },
        {
            "match_id": "LA1_1002",
            "win": False,
            "kills": 4,
            "deaths": 4,
            "assists": 2,
            "cs": 180,
            "gold_earned": 10000,
            "vision_score": 20,
            "game_duration": 1200,  # 20 min
            "champion_id": 222,
            "champion_name": "Jinx",
            "position": "BOTTOM",
            "objectives": {},
        },
    ]

    res = stats_service.calculate_overall_stats(
        parsed_matches=matches,
        match_ids=["LA1_1001", "LA1_1002"],
        requested_count=20,
        queue_filter="ranked",
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.matches_analyzed == 2
    assert res.matches_requested == 20
    assert res.wins == 1
    assert res.losses == 1
    assert res.win_rate == 50.0

    # KDA: total kills 14, deaths 6, assists 7 -> kills 7.0, deaths 3.0, assists 3.5
    assert res.kda.kills_avg == 7.0
    assert res.kda.deaths_avg == 3.0
    assert res.kda.assists_avg == 3.5
    assert res.kda.kda_ratio == 3.5  # (14 + 7) / 6 = 3.5
    assert res.kda.perfect_kda is False

    # Duration: 3000 sec = 50 min. Total CS = 380 -> 7.6 CS/min
    assert res.cs_per_min == 7.6
    assert res.total_cs == 380

    # Gold: total 25000 -> avg 12500, gold/min = 25000 / 50 = 500.0
    assert res.gold.average_gold == 12500.0
    assert res.gold.gold_per_min == 500.0

    # Vision: total 50 -> avg 25.0
    assert res.vision.average_vision_score == 25.0


def test_stats_perfect_kda_zero_deaths():
    """Verify zero deaths report perfect KDA without zero division error."""
    matches = [
        {
            "match_id": "LA1_1003",
            "win": True,
            "kills": 12,
            "deaths": 0,
            "assists": 8,
            "cs": 150,
            "gold_earned": 12000,
            "vision_score": 15,
            "game_duration": 1200,
            "champion_id": 103,
            "champion_name": "Ahri",
            "position": "MIDDLE",
            "objectives": {},
        }
    ]

    res = stats_service.calculate_overall_stats(
        parsed_matches=matches,
        match_ids=["LA1_1003"],
        requested_count=10,
        queue_filter="all",
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.kda.total_deaths == 0
    assert res.kda.perfect_kda is True
    assert res.kda.kda_ratio == 20.0  # (12 + 8)


def test_stats_empty_matches_no_division_by_zero():
    """Verify that an empty match history returns zeros safely without exceptions."""
    res = stats_service.calculate_overall_stats(
        parsed_matches=[],
        match_ids=[],
        requested_count=20,
        queue_filter="ranked",
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.matches_analyzed == 0
    assert res.wins == 0
    assert res.losses == 0
    assert res.win_rate == 0.0
    assert res.kda.kda_ratio == 0.0
    assert res.cs_per_min == 0.0
    assert res.gold.average_gold == 0.0
    assert res.objectives.is_available is False


def test_stats_objective_participation_available():
    """Verify objective calculation when team objective counts are present."""
    matches = [
        {
            "match_id": "LA1_1004",
            "win": True,
            "kills": 5,
            "deaths": 1,
            "assists": 5,
            "cs": 180,
            "gold_earned": 11000,
            "vision_score": 22,
            "game_duration": 1500,
            "champion_id": 64,
            "champion_name": "LeeSin",
            "position": "JUNGLE",
            "objectives": {
                "team_dragons": 4,
                "participant_dragons": 3,  # 75%
                "team_barons": 2,
                "participant_barons": 1,  # 50%
                "team_turrets": 8,
                "participant_turrets": 4,  # 50%
            },
        }
    ]

    res = stats_service.calculate_overall_stats(
        parsed_matches=matches,
        match_ids=["LA1_1004"],
        requested_count=10,
        queue_filter="ranked",
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.objectives.is_available is True
    assert res.objectives.dragon_participation == 75.0
    assert res.objectives.baron_participation == 50.0
    assert res.objectives.turret_participation == 50.0


def test_champion_stats_grouping_and_sorting():
    """Verify champion grouping, win rate and sorting by matches played."""
    matches = [
        {
            "champion_id": 222,
            "champion_name": "Jinx",
            "win": True,
            "kills": 10,
            "deaths": 2,
            "assists": 8,
            "cs": 250,
            "gold_earned": 14000,
            "game_duration": 1800,
        },
        {
            "champion_id": 222,
            "champion_name": "Jinx",
            "win": False,
            "kills": 2,
            "deaths": 4,
            "assists": 1,
            "cs": 180,
            "gold_earned": 8000,
            "game_duration": 1200,
        },
        {
            "champion_id": 103,
            "champion_name": "Ahri",
            "win": True,
            "kills": 8,
            "deaths": 1,
            "assists": 9,
            "cs": 210,
            "gold_earned": 12000,
            "game_duration": 1500,
        },
    ]

    res = stats_service.calculate_champion_stats(
        parsed_matches=matches,
        requested_count=20,
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.matches_analyzed == 3
    assert len(res.champions) == 2

    # Jinx has 2 matches (1W, 1L = 50.0% WR)
    jinx = res.champions[0]
    assert jinx.champion_name == "Jinx"
    assert jinx.matches_played == 2
    assert jinx.win_rate == 50.0

    # Ahri has 1 match (1W, 0L = 100.0% WR)
    ahri = res.champions[1]
    assert ahri.champion_name == "Ahri"
    assert ahri.matches_played == 1
    assert ahri.win_rate == 100.0


def test_role_distribution_unknown_handling():
    """Verify role distribution handles unknown positions without fabricating data."""
    matches = [
        {"position": "BOTTOM", "win": True},
        {"position": "MIDDLE", "win": False},
        {"position": "", "win": True},  # Missing position
    ]

    res = stats_service.calculate_role_distribution(
        parsed_matches=matches,
        requested_count=20,
        player_context=MOCK_PLAYER_CONTEXT,
    )

    assert res.matches_analyzed == 3
    roles = {r.role: r for r in res.roles}

    assert "BOTTOM" in roles
    assert "MIDDLE" in roles
    assert "UNKNOWN" in roles
    assert roles["UNKNOWN"].display_name == "Posición No Definida"
    assert roles["BOTTOM"].percentage == 33.33


# ---------------------------------------------------------------------------
# API Endpoints Integration Tests (with mocked Match-V5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_player_stats_endpoint():
    """Verify GET /api/players/{name}/{tag}/stats endpoint integration."""
    mock_parsed = [
        {
            "match_id": "KR_100",
            "win": True,
            "kills": 8,
            "deaths": 2,
            "assists": 6,
            "cs": 200,
            "gold_earned": 13000,
            "vision_score": 25,
            "game_duration": 1800,
            "champion_id": 103,
            "champion_name": "Ahri",
            "position": "MIDDLE",
            "objectives": {},
        }
    ]

    with patch(
        "app.api.v1.endpoints.players.match_service.get_player_match_history_parsed",
        new_callable=AsyncMock,
        return_value=(mock_parsed, ["KR_100"], MOCK_PLAYER_CONTEXT),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            url = "/api/players/Josedeodo/LAN/stats?region=la1&matches=5"
            resp = await client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["matches_analyzed"] == 1
            assert data["wins"] == 1
            assert data["win_rate"] == 100.0
            assert data["kda"]["kda_ratio"] == 7.0


@pytest.mark.asyncio
async def test_api_player_champions_endpoint():
    """Verify GET /api/players/{name}/{tag}/champions endpoint integration."""
    mock_parsed = [
        {
            "champion_id": 222,
            "champion_name": "Jinx",
            "win": True,
            "kills": 12,
            "deaths": 2,
            "assists": 4,
            "cs": 240,
            "gold_earned": 14000,
            "game_duration": 1600,
        }
    ]

    with patch(
        "app.api.v1.endpoints.players.match_service.get_player_match_history_parsed",
        new_callable=AsyncMock,
        return_value=(mock_parsed, ["KR_101"], MOCK_PLAYER_CONTEXT),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/players/Josedeodo/LAN/champions?region=la1&matches=5"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["champions"]) == 1
            assert data["champions"][0]["champion_name"] == "Jinx"


@pytest.mark.asyncio
async def test_api_player_roles_endpoint():
    """Verify GET /api/players/{name}/{tag}/roles endpoint integration."""
    mock_parsed = [
        {"position": "BOTTOM", "win": True},
        {"position": "BOTTOM", "win": True},
    ]

    with patch(
        "app.api.v1.endpoints.players.match_service.get_player_match_history_parsed",
        new_callable=AsyncMock,
        return_value=(mock_parsed, ["KR_102", "KR_103"], MOCK_PLAYER_CONTEXT),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/players/Josedeodo/LAN/roles?region=la1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["roles"][0]["role"] == "BOTTOM"
            assert data["roles"][0]["percentage"] == 100.0


@pytest.mark.asyncio
async def test_api_match_detail_endpoint():
    """Verify GET /api/matches/{match_id}?region=LA1 endpoint integration."""
    mock_detail = {
        "metadata": {"matchId": "LA1_123456"},
        "info": {
            "gameCreation": 1600000000,
            "gameDuration": 1850,
            "gameMode": "CLASSIC",
            "gameVersion": "14.20.1",
            "queueId": 420,
            "teams": [{"teamId": 100, "win": True}],
            "participants": [{"puuid": "p1", "championName": "Jinx"}],
        },
    }

    with patch(
        "app.services.match_service.riot_client.get_match_by_id",
        new_callable=AsyncMock,
        return_value=mock_detail,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/matches/LA1_123456?region=la1")
            assert resp.status_code == 200
            data = resp.json()
            assert data["match_id"] == "LA1_123456"
            assert data["game_duration_seconds"] == 1850
            assert len(data["teams"]) == 1
