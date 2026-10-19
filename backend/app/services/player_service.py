from app.core.cache import build_profile_key, cache
from app.core.config import settings
from app.core.validation import (
    validate_region,
    validate_riot_id,
)
from app.schemas.player import PlayerProfileResponse, PlayerRankEntry
from app.services.ddragon_service import ddragon_service
from app.services.region_service import region_service
from app.services.riot_client import riot_client


class PlayerService:
    """Orchestrates Riot Games API lookups (Account-V1, Summoner-V4, League-V4).

    Integrates memory caching with configurable TTL and strict input validation.
    """

    @staticmethod
    def validate_riot_id(game_name: str, tag_line: str) -> tuple[str, str]:
        """Validate and sanitize Riot ID components."""
        return validate_riot_id(game_name, tag_line)

    @staticmethod
    async def get_player_profile(
        game_name: str,
        tag_line: str,
        platform_id: str,
    ) -> PlayerProfileResponse:
        """Resolve full player profile with Account-V1, Summoner-V4 and League-V4."""
        # 1. Validate inputs and region routing
        valid_name, valid_tag = PlayerService.validate_riot_id(game_name, tag_line)
        validated_platform = validate_region(platform_id)

        region_info = region_service.get_region_by_platform(validated_platform)
        cluster = region_info.regional_cluster
        platform = region_info.platform_id

        # Check in-memory cache for player profile
        cache_key = build_profile_key(platform, valid_name, valid_tag)
        cached_profile = cache.get(cache_key)
        if cached_profile is not None:
            return cached_profile

        # 2. Account-V1: Resolve PUUID on regional cluster
        account_data = await riot_client.get_account_by_riot_id(
            game_name=valid_name,
            tag_line=valid_tag,
            regional_cluster=cluster,
        )
        puuid = account_data.get("puuid")
        official_name = account_data.get("gameName", valid_name)
        official_tag = account_data.get("tagLine", valid_tag)

        # 3. Summoner-V4: Get level, icon, and encrypted summoner ID on platform
        summoner_data = await riot_client.get_summoner_by_puuid(
            puuid=puuid,
            platform_id=platform,
        )
        summoner_id = summoner_data.get("id")
        summoner_level = summoner_data.get("summonerLevel", 1)
        profile_icon_id = summoner_data.get("profileIconId", 29)

        # 4. League-V4: Fetch competitive entries if summoner_id is present
        raw_league_entries: list[dict] = []
        if summoner_id:
            try:
                raw_league_entries = await riot_client.get_league_entries_by_summoner(
                    summoner_id=summoner_id,
                    platform_id=platform,
                )
            except Exception:
                # If league entries fail or unranked, fallback to empty list
                raw_league_entries = []

        # 5. Parse and calculate ranked entries
        parsed_ranks: list[PlayerRankEntry] = []
        solo_rank: PlayerRankEntry | None = None
        flex_rank: PlayerRankEntry | None = None

        for entry in raw_league_entries:
            wins = entry.get("wins", 0)
            losses = entry.get("losses", 0)
            total = wins + losses
            win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0

            rank_obj = PlayerRankEntry(
                queue_type=entry.get("queueType", "UNKNOWN"),
                tier=entry.get("tier", "UNRANKED"),
                rank=entry.get("rank", ""),
                league_points=entry.get("leaguePoints", 0),
                wins=wins,
                losses=losses,
                win_rate=win_rate,
                veteran=entry.get("veteran", False),
                inactive=entry.get("inactive", False),
                fresh_blood=entry.get("freshBlood", False),
                hot_streak=entry.get("hotStreak", False),
            )
            parsed_ranks.append(rank_obj)

            if rank_obj.queue_type == "RANKED_SOLO_5x5":
                solo_rank = rank_obj
            elif rank_obj.queue_type == "RANKED_FLEX_SR":
                flex_rank = rank_obj

        # 6. Build official Data Dragon CDN URL for profile icon
        icon_url = ddragon_service.get_profile_icon_url(profile_icon_id)

        response = PlayerProfileResponse(
            puuid=puuid,
            game_name=official_name,
            tag_line=official_tag,
            summoner_id=summoner_id,
            summoner_level=summoner_level,
            profile_icon_id=profile_icon_id,
            profile_icon_url=icon_url,
            region=platform,
            regional_cluster=cluster,
            ranks=parsed_ranks,
            solo_rank=solo_rank,
            flex_rank=flex_rank,
        )

        # Cache profile response with configurable TTL
        cache.set(cache_key, response, settings.CACHE_TTL_PROFILE_SECONDS)
        return response


player_service = PlayerService()
