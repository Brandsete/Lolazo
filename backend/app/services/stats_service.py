from app.schemas.stats import (
    ChampionStatsEntry,
    GoldStats,
    KdaStats,
    ObjectiveStats,
    PlayerChampionsResponse,
    PlayerOverallStatsResponse,
    PlayerRolesResponse,
    RoleDistributionEntry,
    VisionStats,
)
from app.services.ddragon_service import ddragon_service

ROLE_DISPLAY_NAMES = {
    "TOP": "Carril Superior",
    "JUNGLE": "Jungla",
    "MIDDLE": "Carril Central",
    "BOTTOM": "Tirador (ADC)",
    "UTILITY": "Soporte",
    "UNKNOWN": "Posición No Definida",
}


class StatsService:
    """Service providing mathematical and aggregation calculations.

    All formulas are strictly zero-division protected and document actual matches.
    """

    @staticmethod
    def calculate_overall_stats(
        parsed_matches: list[dict],
        match_ids: list[str],
        requested_count: int,
        queue_filter: str,
        player_context: dict,
    ) -> PlayerOverallStatsResponse:
        """Calculate aggregate performance metrics across analyzed matches.

        Formulas:
        - win_rate = (wins / total_matches) * 100
        - kda_ratio = (kills + assists) / max(1, deaths) (or exact with perfect_kda)
        - cs_per_min = total_cs / total_duration_minutes
        - gold_per_min = total_gold / total_duration_minutes
        """
        total = len(parsed_matches)

        if total == 0:
            return PlayerOverallStatsResponse(
                game_name=player_context["game_name"],
                tag_line=player_context["tag_line"],
                puuid=player_context["puuid"],
                region=player_context["region"],
                regional_cluster=player_context["regional_cluster"],
                matches_requested=requested_count,
                matches_analyzed=0,
                match_ids=[],
                queue_filter=queue_filter,
                wins=0,
                losses=0,
                win_rate=0.0,
                kda=KdaStats(
                    kills_avg=0.0,
                    deaths_avg=0.0,
                    assists_avg=0.0,
                    kda_ratio=0.0,
                    total_kills=0,
                    total_deaths=0,
                    total_assists=0,
                    perfect_kda=False,
                ),
                cs_per_min=0.0,
                total_cs=0,
                gold=GoldStats(average_gold=0.0, gold_per_min=0.0, total_gold=0),
                vision=VisionStats(average_vision_score=0.0, total_vision_score=0),
                objectives=ObjectiveStats(
                    is_available=False,
                    notes="No matches found for the requested criteria.",
                ),
            )

        wins = sum(1 for m in parsed_matches if m.get("win", False))
        losses = total - wins
        win_rate = round((wins / total) * 100, 2)

        total_kills = sum(m.get("kills", 0) for m in parsed_matches)
        total_deaths = sum(m.get("deaths", 0) for m in parsed_matches)
        total_assists = sum(m.get("assists", 0) for m in parsed_matches)

        kills_avg = round(total_kills / total, 2)
        deaths_avg = round(total_deaths / total, 2)
        assists_avg = round(total_assists / total, 2)

        perfect_kda = total_deaths == 0
        kda_ratio = (
            round((total_kills + total_assists) / total_deaths, 2)
            if total_deaths > 0
            else float(total_kills + total_assists)
        )

        total_duration_sec = sum(m.get("game_duration", 0) for m in parsed_matches)
        total_duration_min = (
            total_duration_sec / 60.0 if total_duration_sec > 0 else 1.0
        )

        total_cs = sum(m.get("cs", 0) for m in parsed_matches)
        cs_per_min = round(total_cs / total_duration_min, 2)

        total_gold = sum(m.get("gold_earned", 0) for m in parsed_matches)
        avg_gold = round(total_gold / total, 2)
        gold_per_min = round(total_gold / total_duration_min, 2)

        total_vision = sum(m.get("vision_score", 0) for m in parsed_matches)
        avg_vision = round(total_vision / total, 2)

        # Objective Participation calculation (only when team objective data is present)
        dragon_rates: list[float] = []
        baron_rates: list[float] = []
        turret_rates: list[float] = []

        for m in parsed_matches:
            obj = m.get("objectives", {})
            team_dragons = obj.get("team_dragons", 0)
            team_barons = obj.get("team_barons", 0)
            team_turrets = obj.get("team_turrets", 0)

            p_dragons = obj.get("participant_dragons", 0)
            p_barons = obj.get("participant_barons", 0)
            p_turrets = obj.get("participant_turrets", 0)

            if team_dragons > 0:
                dragon_rates.append(min(100.0, (p_dragons / team_dragons) * 100))
            if team_barons > 0:
                baron_rates.append(min(100.0, (p_barons / team_barons) * 100))
            if team_turrets > 0:
                turret_rates.append(min(100.0, (p_turrets / team_turrets) * 100))

        has_objective_data = bool(dragon_rates or baron_rates or turret_rates)
        avg_dragon_part = (
            round(sum(dragon_rates) / len(dragon_rates), 2) if dragon_rates else None
        )
        avg_baron_part = (
            round(sum(baron_rates) / len(baron_rates), 2) if baron_rates else None
        )
        avg_turret_part = (
            round(sum(turret_rates) / len(turret_rates), 2) if turret_rates else None
        )

        objectives = ObjectiveStats(
            is_available=has_objective_data,
            dragon_participation=avg_dragon_part,
            baron_participation=avg_baron_part,
            turret_participation=avg_turret_part,
            notes=(
                f"Calculated from {len(dragon_rates)} matches with active objectives."
                if has_objective_data
                else "Objective takedown breakdown not reported by match payload."
            ),
        )

        return PlayerOverallStatsResponse(
            game_name=player_context["game_name"],
            tag_line=player_context["tag_line"],
            puuid=player_context["puuid"],
            region=player_context["region"],
            regional_cluster=player_context["regional_cluster"],
            matches_requested=requested_count,
            matches_analyzed=total,
            match_ids=match_ids[:total],
            queue_filter=queue_filter,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            kda=KdaStats(
                kills_avg=kills_avg,
                deaths_avg=deaths_avg,
                assists_avg=assists_avg,
                kda_ratio=kda_ratio,
                total_kills=total_kills,
                total_deaths=total_deaths,
                total_assists=total_assists,
                perfect_kda=perfect_kda,
            ),
            cs_per_min=cs_per_min,
            total_cs=total_cs,
            gold=GoldStats(
                average_gold=avg_gold,
                gold_per_min=gold_per_min,
                total_gold=total_gold,
            ),
            vision=VisionStats(
                average_vision_score=avg_vision,
                total_vision_score=total_vision,
            ),
            objectives=objectives,
        )

    @staticmethod
    def calculate_champion_stats(
        parsed_matches: list[dict],
        requested_count: int,
        player_context: dict,
    ) -> PlayerChampionsResponse:
        """Group and calculate per-champion metrics, sorted by games played."""
        total = len(parsed_matches)
        champs_map: dict[str, dict] = {}

        for m in parsed_matches:
            name = m.get("champion_name", "Unknown")
            champ_id = m.get("champion_id", 0)

            if name not in champs_map:
                champs_map[name] = {
                    "champion_id": champ_id,
                    "champion_name": name,
                    "matches_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "total_cs": 0,
                    "total_gold": 0,
                    "duration_sec": 0,
                }

            group = champs_map[name]
            group["matches_played"] += 1
            if m.get("win", False):
                group["wins"] += 1
            else:
                group["losses"] += 1

            group["kills"] += m.get("kills", 0)
            group["deaths"] += m.get("deaths", 0)
            group["assists"] += m.get("assists", 0)
            group["total_cs"] += m.get("cs", 0)
            group["total_gold"] += m.get("gold_earned", 0)
            group["duration_sec"] += m.get("game_duration", 0)

        entries: list[ChampionStatsEntry] = []
        for name, data in champs_map.items():
            played = data["matches_played"]
            wins = data["wins"]
            losses = data["losses"]
            win_rate = round((wins / played) * 100, 2) if played > 0 else 0.0

            kills_avg = round(data["kills"] / played, 2) if played > 0 else 0.0
            deaths_avg = round(data["deaths"] / played, 2) if played > 0 else 0.0
            assists_avg = round(data["assists"] / played, 2) if played > 0 else 0.0

            kda_ratio = (
                round((data["kills"] + data["assists"]) / data["deaths"], 2)
                if data["deaths"] > 0
                else float(data["kills"] + data["assists"])
            )

            dur_min = data["duration_sec"] / 60.0 if data["duration_sec"] > 0 else 1.0
            cs_per_min = round(data["total_cs"] / dur_min, 2)
            gold_per_min = round(data["total_gold"] / dur_min, 2)

            entries.append(
                ChampionStatsEntry(
                    champion_id=data["champion_id"],
                    champion_name=name,
                    champion_icon_url=ddragon_service.get_champion_icon_url(name),
                    matches_played=played,
                    wins=wins,
                    losses=losses,
                    win_rate=win_rate,
                    kills_avg=kills_avg,
                    deaths_avg=deaths_avg,
                    assists_avg=assists_avg,
                    kda_ratio=kda_ratio,
                    cs_per_min=cs_per_min,
                    gold_per_min=gold_per_min,
                )
            )

        # Sort champions by matches played (descending), then win rate (descending)
        entries.sort(key=lambda c: (c.matches_played, c.win_rate), reverse=True)

        return PlayerChampionsResponse(
            game_name=player_context["game_name"],
            tag_line=player_context["tag_line"],
            puuid=player_context["puuid"],
            region=player_context["region"],
            matches_requested=requested_count,
            matches_analyzed=total,
            champions=entries,
        )

    @staticmethod
    def calculate_role_distribution(
        parsed_matches: list[dict],
        requested_count: int,
        player_context: dict,
    ) -> PlayerRolesResponse:
        """Calculate lane/position distribution without fabricating positions."""
        total = len(parsed_matches)
        roles_map: dict[str, dict] = {}

        for m in parsed_matches:
            # Use official teamPosition, fallback to individualPosition or UNKNOWN
            role = m.get("position")
            if not role or role in ("", "NONE", "APX"):
                role = "UNKNOWN"

            norm_role = role.upper()

            if norm_role not in roles_map:
                roles_map[norm_role] = {
                    "count": 0,
                    "wins": 0,
                    "losses": 0,
                }

            group = roles_map[norm_role]
            group["count"] += 1
            if m.get("win", False):
                group["wins"] += 1
            else:
                group["losses"] += 1

        entries: list[RoleDistributionEntry] = []
        for role, data in roles_map.items():
            count = data["count"]
            wins = data["wins"]
            losses = data["losses"]
            pct = round((count / total) * 100, 2) if total > 0 else 0.0
            wr = round((wins / count) * 100, 2) if count > 0 else 0.0

            entries.append(
                RoleDistributionEntry(
                    role=role,
                    display_name=ROLE_DISPLAY_NAMES.get(role, role),
                    matches_count=count,
                    percentage=pct,
                    wins=wins,
                    losses=losses,
                    win_rate=wr,
                )
            )

        # Sort positions by count descending
        entries.sort(key=lambda r: r.matches_count, reverse=True)

        return PlayerRolesResponse(
            game_name=player_context["game_name"],
            tag_line=player_context["tag_line"],
            puuid=player_context["puuid"],
            region=player_context["region"],
            matches_requested=requested_count,
            matches_analyzed=total,
            roles=entries,
        )


stats_service = StatsService()
