import logging

from app.core.cache import build_match_key, cache
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException
from app.core.validation import (
    validate_match_id,
    validate_matches_count,
    validate_queue_param,
    validate_region,
)
from app.schemas.stats import MatchDetailResponse, PlayerMatchSummary
from app.services.ddragon_service import ddragon_service
from app.services.region_service import region_service
from app.services.riot_client import riot_client

logger = logging.getLogger("rifttracker.match_service")

# Official Queue IDs mapping in League of Legends
QUEUE_MAPPINGS = {
    "solo": 420,  # Ranked Solo/Duo
    "flex": 440,  # Ranked Flex
    "normal": 400,  # Normal Draft Pick
    "blind": 430,  # Blind Pick
    "aram": 450,  # ARAM
}

QUEUE_NAMES = {
    420: "Ranked Solo/Duo",
    440: "Ranked Flex",
    400: "Normal Draft",
    430: "Normal Blind",
    450: "ARAM",
    490: "Quickplay",
    1700: "Arena",
}


class MatchService:
    """Service to query, cache and parse Match-V5 games from Riot Games API.

    Features:
    - Thread-safe memory caching with configurable TTL for immutable matches
    - Strict validation of match IDs, queues, and counts
    - Resilient partial data handling when individual match lookups fail
    """

    def __init__(self) -> None:
        # In-memory match cache (kept for backward compatibility with existing tests)
        self._match_cache: dict[str, dict] = {}

    def get_cached_match(self, match_id: str) -> dict | None:
        """Retrieve match from local in-memory cache if available."""
        return self._match_cache.get(match_id)

    def cache_match(self, match_id: str, match_data: dict) -> None:
        """Store immutable match in memory, trimming cache size if needed."""
        if len(self._match_cache) > 500:
            # Drop oldest 100 entries to prevent unbounded memory growth
            drop_keys = list(self._match_cache.keys())[:100]
            for k in drop_keys:
                self._match_cache.pop(k, None)
        self._match_cache[match_id] = match_data

    @staticmethod
    def resolve_queue_id(queue_param: str | None) -> int | None:
        """Resolve queue string parameter to official League of Legends queue ID."""
        if not queue_param:
            return None
        norm = queue_param.lower().strip()
        if norm in ("all", "any"):
            return None
        if norm.isdigit():
            return int(norm)
        return QUEUE_MAPPINGS.get(norm)

    async def get_player_match_ids(
        self,
        puuid: str,
        regional_cluster: str,
        count: int = 20,
        queue: str | None = None,
    ) -> list[str]:
        """Fetch list of match IDs for a player, applying queue filters and limits."""
        # Validate count and queue param
        clamped_count = validate_matches_count(count, min_val=1, max_val=100)
        max_allowed = max(1, settings.MAX_MATCHES)
        clamped_count = min(clamped_count, max_allowed)

        norm_queue = validate_queue_param(queue) if queue else None

        # If user specified "ranked", fetch Solo/Duo by default
        queue_id = None
        if norm_queue == "ranked":
            queue_id = 420
        elif norm_queue:
            queue_id = self.resolve_queue_id(norm_queue)

        return await riot_client.get_match_ids_by_puuid(
            puuid=puuid,
            regional_cluster=regional_cluster,
            count=clamped_count,
            queue=queue_id,
        )

    async def get_match_detail(
        self,
        match_id: str,
        regional_cluster: str,
    ) -> dict:
        """Fetch match details using Match-V5, leveraging memory cache with TTL."""
        valid_id = validate_match_id(match_id)
        cluster = regional_cluster.lower().strip()
        cache_key = build_match_key(cluster, valid_id)

        # Check central TTL cache first, then fallback to local cache
        cached = cache.get(cache_key) or self.get_cached_match(valid_id)
        if cached:
            return cached

        data = await riot_client.get_match_by_id(
            match_id=valid_id,
            regional_cluster=cluster,
        )
        if not data or "info" not in data:
            raise ResourceNotFoundException(f"Match '{valid_id}' not found")

        # Save to both central TTL cache and legacy match cache
        cache.set(cache_key, data, settings.CACHE_TTL_MATCH_SECONDS)
        self.cache_match(valid_id, data)
        return data

    @staticmethod
    def find_participant_by_puuid(match_data: dict, puuid: str) -> dict | None:
        """Find the participant dictionary belonging to the player's PUUID."""
        info = match_data.get("info", {})
        participants = info.get("participants", [])
        for p in participants:
            if p.get("puuid") == puuid:
                return p
        return None

    @staticmethod
    def parse_player_match_summary(
        match_data: dict,
        puuid: str,
    ) -> PlayerMatchSummary | None:
        """Extract a single player's performance summary from a match payload."""
        info = match_data.get("info", {})
        participant = MatchService.find_participant_by_puuid(match_data, puuid)
        if not participant:
            return None

        match_id = match_data.get("metadata", {}).get("matchId", "UNKNOWN")
        duration_sec = info.get("gameDuration", 0)
        # Handle Riot API v5 millisecond edge-case in legacy matches
        if duration_sec > 10000:
            duration_sec = int(duration_sec / 1000)

        duration_min = duration_sec / 60.0 if duration_sec > 0 else 1.0

        kills = participant.get("kills", 0)
        deaths = participant.get("deaths", 0)
        assists = participant.get("assists", 0)
        kda_ratio = (
            round((kills + assists) / deaths, 2)
            if deaths > 0
            else float(kills + assists)
        )

        minions = participant.get("totalMinionsKilled", 0)
        neutral_minions = participant.get("neutralMinionsKilled", 0)
        total_cs = minions + neutral_minions
        cs_per_min = round(total_cs / duration_min, 2)

        champ_name = participant.get("championName", "Unknown")
        champ_icon = ddragon_service.get_champion_icon_url(champ_name)

        items = [participant.get(f"item{i}", 0) for i in range(7)]
        spells = [
            participant.get("summoner1Id", 0),
            participant.get("summoner2Id", 0),
        ]

        queue_id = info.get("queueId", 0)
        queue_name = QUEUE_NAMES.get(queue_id, f"Cola #{queue_id}")

        challenges = participant.get("challenges", {})
        kp = challenges.get("killParticipation")
        kill_participation = round(kp * 100, 1) if kp is not None else None

        return PlayerMatchSummary(
            match_id=match_id,
            game_creation=info.get("gameCreation", 0),
            game_duration_seconds=duration_sec,
            game_mode=info.get("gameMode", "CLASSIC"),
            queue_id=queue_id,
            queue_name=queue_name,
            is_victory=bool(participant.get("win", False)),
            champion_id=participant.get("championId", 0),
            champion_name=champ_name,
            champion_level=participant.get("champLevel", 1),
            champion_icon_url=champ_icon,
            kills=kills,
            deaths=deaths,
            assists=assists,
            kda_ratio=kda_ratio,
            total_cs=total_cs,
            cs_per_min=cs_per_min,
            gold_earned=participant.get("goldEarned", 0),
            vision_score=participant.get("visionScore", 0),
            items=items,
            summoner_spells=spells,
            kill_participation=kill_participation,
        )

    async def get_match_formatted_detail(
        self,
        match_id: str,
        platform_id: str,
    ) -> MatchDetailResponse:
        """Fetch and return standardized MatchDetailResponse with validation."""
        valid_id = validate_match_id(match_id)
        valid_platform = validate_region(platform_id)
        region_info = region_service.get_region_by_platform(valid_platform)
        cluster = region_info.regional_cluster
        data = await self.get_match_detail(valid_id, cluster)
        info = data.get("info", {})

        return MatchDetailResponse(
            match_id=data.get("metadata", {}).get("matchId", valid_id),
            regional_cluster=cluster,
            game_creation=info.get("gameCreation", 0),
            game_duration_seconds=info.get("gameDuration", 0),
            game_mode=info.get("gameMode", "CLASSIC"),
            game_version=info.get("gameVersion", "unknown"),
            queue_id=info.get("queueId", 0),
            teams=info.get("teams", []),
            participants=info.get("participants", []),
        )

    async def get_player_match_history_parsed(
        self,
        game_name: str,
        tag_line: str,
        platform_id: str,
        count: int = 20,
        queue: str | None = None,
    ) -> tuple[list[dict], list[str], dict]:
        """Fetch and parse match history specifically for the queried player.

        Handles partial failures gracefully: if individual matches cannot be fetched
        or parsed, they are safely skipped while keeping successful ones.
        """
        from app.services.player_service import player_service

        valid_name, valid_tag = player_service.validate_riot_id(game_name, tag_line)
        valid_platform = validate_region(platform_id)
        valid_count = validate_matches_count(count, min_val=1, max_val=100)
        valid_queue = validate_queue_param(queue) if queue else None

        region_info = region_service.get_region_by_platform(valid_platform)
        cluster = region_info.regional_cluster
        platform = region_info.platform_id

        # 1. Resolve PUUID via Account-V1
        account = await riot_client.get_account_by_riot_id(
            game_name=valid_name,
            tag_line=valid_tag,
            regional_cluster=cluster,
        )
        puuid = account.get("puuid")

        player_context = {
            "game_name": account.get("gameName", valid_name),
            "tag_line": account.get("tagLine", valid_tag),
            "puuid": puuid,
            "region": platform,
            "regional_cluster": cluster,
        }

        # 2. Resolve match IDs
        match_ids = await self.get_player_match_ids(
            puuid=puuid,
            regional_cluster=cluster,
            count=valid_count,
            queue=valid_queue,
        )

        parsed_matches: list[dict] = []
        for mid in match_ids:
            try:
                m_data = await self.get_match_detail(mid, cluster)
                participant = self.find_participant_by_puuid(m_data, puuid)
                if not participant:
                    continue

                info = m_data.get("info", {})
                duration_sec = info.get("gameDuration", 0)
                if duration_sec > 10000:
                    duration_sec = int(duration_sec / 1000)

                # Extract team objectives
                team_id = participant.get("teamId")
                team_obj = {}
                for t in info.get("teams", []):
                    if t.get("teamId") == team_id:
                        team_obj = t.get("objectives", {})
                        break

                challenges = participant.get("challenges", {})
                p_drag = challenges.get(
                    "dragonTakedowns", participant.get("dragonKills", 0)
                )
                p_baron = challenges.get(
                    "baronTakedowns", participant.get("baronKills", 0)
                )
                p_turret = challenges.get(
                    "turretTakedowns", participant.get("turretKills", 0)
                )

                t_drag = team_obj.get("dragon", {}).get("kills", 0)
                t_baron = team_obj.get("baron", {}).get("kills", 0)
                t_turret = team_obj.get("tower", {}).get("kills", 0)

                pos = (
                    participant.get("teamPosition")
                    or participant.get("individualPosition")
                    or "UNKNOWN"
                )

                total_cs = participant.get("totalMinionsKilled", 0) + participant.get(
                    "neutralMinionsKilled", 0
                )

                parsed_matches.append(
                    {
                        "match_id": mid,
                        "win": bool(participant.get("win", False)),
                        "kills": participant.get("kills", 0),
                        "deaths": participant.get("deaths", 0),
                        "assists": participant.get("assists", 0),
                        "cs": total_cs,
                        "gold_earned": participant.get("goldEarned", 0),
                        "vision_score": participant.get("visionScore", 0),
                        "game_duration": duration_sec,
                        "champion_id": participant.get("championId", 0),
                        "champion_name": participant.get("championName", "Unknown"),
                        "position": pos,
                        "objectives": {
                            "team_dragons": t_drag,
                            "team_barons": t_baron,
                            "team_turrets": t_turret,
                            "participant_dragons": p_drag,
                            "participant_barons": p_baron,
                            "participant_turrets": p_turret,
                        },
                        "raw_data": m_data,
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Failed to parse match %s gracefully: %s", mid, type(exc).__name__
                )
                continue

        return parsed_matches, match_ids, player_context


match_service = MatchService()
