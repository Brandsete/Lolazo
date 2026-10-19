import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.cache import (
    InMemoryCache,
    build_champions_key,
    build_league_key,
    build_match_ids_key,
    build_match_key,
    build_matches_summary_key,
    build_profile_key,
    build_roles_key,
    build_stats_key,
    cache,
)
from app.main import app


def test_in_memory_cache_set_get_and_expiration():
    """Verify basic caching, TTL calculation, and expiration."""
    test_cache = InMemoryCache(max_entries=10, default_ttl=1)

    # Set item with 0.1s TTL
    test_cache.set("test_key", {"data": "hello"}, ttl_seconds=0.1)

    # Immediate get should hit
    assert test_cache.get("test_key") == {"data": "hello"}
    stats = test_cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0

    # Wait for expiration
    time.sleep(0.15)

    # Should expire and return None
    assert test_cache.get("test_key") is None
    stats = test_cache.stats()
    assert stats["misses"] == 1


def test_in_memory_cache_eviction_on_capacity():
    """Verify oldest items are evicted when capacity limit is reached."""
    small_cache = InMemoryCache(max_entries=5, default_ttl=60)

    for i in range(5):
        small_cache.set(f"key_{i}", i)

    assert small_cache.stats()["size"] == 5

    # Adding a 6th key should trigger eviction
    small_cache.set("key_new", 999)
    assert small_cache.get("key_new") == 999
    assert small_cache.stats()["evictions"] >= 1
    assert small_cache.stats()["size"] <= 5


def test_cache_delete_and_clear():
    """Verify deleting keys and clearing cache."""
    test_cache = InMemoryCache(max_entries=10, default_ttl=60)
    test_cache.set("item1", "val1")
    test_cache.set("item2", "val2")

    assert test_cache.delete("item1") is True
    assert test_cache.get("item1") is None
    assert test_cache.get("item2") == "val2"

    test_cache.clear()
    assert test_cache.get("item2") is None
    assert test_cache.stats()["size"] == 0


def test_cache_key_helpers():
    """Verify deterministic and sanitized cache key generators."""
    assert build_profile_key("LA1", "Josedeodo", "LAN") == "profile:la1:josedeodo:lan"
    assert build_league_key("LA1", "summoner-123") == "league:la1:summoner-123"
    assert build_match_key("americas", "LA1_12345") == "match:americas:la1_12345"
    assert (
        build_match_ids_key("americas", "puuid-1", 10, "ranked")
        == "match_ids:americas:puuid-1:10:ranked"
    )
    assert (
        build_stats_key("la1", "Faker", "KR1", "ranked", 20)
        == "stats:la1:faker:kr1:ranked:20"
    )
    assert (
        build_champions_key("la1", "Faker", "KR1", 20) == "champions:la1:faker:kr1:20"
    )
    assert build_roles_key("la1", "Faker", "KR1", 20) == "roles:la1:faker:kr1:20"
    assert (
        build_matches_summary_key("la1", "Faker", "KR1", 10)
        == "matches_summary:la1:faker:kr1:10"
    )


@pytest.mark.asyncio
async def test_player_profile_caching_integration():
    """Verify repeated player profile calls use cache and avoid redundant Riot calls."""
    cache.clear()

    mock_account = {
        "puuid": "mock-puuid-cache-test",
        "gameName": "CacheTester",
        "tagLine": "LAN",
    }
    mock_summoner = {
        "id": "mock-summoner-id",
        "accountId": "mock-account-id",
        "puuid": "mock-puuid-cache-test",
        "profileIconId": 50,
        "summonerLevel": 100,
    }

    with (
        patch(
            "app.services.player_service.riot_client.get_account_by_riot_id",
            new_callable=AsyncMock,
            return_value=mock_account,
        ) as mock_acc,
        patch(
            "app.services.player_service.riot_client.get_summoner_by_puuid",
            new_callable=AsyncMock,
            return_value=mock_summoner,
        ) as mock_sum,
        patch(
            "app.services.player_service.riot_client.get_league_entries_by_summoner",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request - cache miss, calls external client
            res1 = await client.get("/api/players/CacheTester/LAN?region=la1")
            assert res1.status_code == 200
            assert mock_acc.call_count == 1
            assert mock_sum.call_count == 1

            # Second request - cache hit, does not call external client again
            res2 = await client.get("/api/players/CacheTester/LAN?region=la1")
            assert res2.status_code == 200
            assert mock_acc.call_count == 1
            assert mock_sum.call_count == 1
            assert res1.json() == res2.json()

    cache.clear()
