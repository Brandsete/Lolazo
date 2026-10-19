from pydantic import BaseModel, Field


class KdaStats(BaseModel):
    """KDA statistics and averages."""

    kills_avg: float = Field(..., description="Average kills per match")
    deaths_avg: float = Field(..., description="Average deaths per match")
    assists_avg: float = Field(..., description="Average assists per match")
    kda_ratio: float = Field(
        ...,
        description="Calculated KDA ratio: (kills + assists) / max(1, deaths)",
    )
    total_kills: int = Field(..., description="Total kills across matches")
    total_deaths: int = Field(..., description="Total deaths across matches")
    total_assists: int = Field(..., description="Total assists across matches")
    perfect_kda: bool = Field(
        default=False,
        description="True if zero deaths occurred across analyzed matches",
    )


class GoldStats(BaseModel):
    """Economy statistics."""

    average_gold: float = Field(..., description="Average gold earned per match")
    gold_per_min: float = Field(..., description="Average gold earned per minute")
    total_gold: int = Field(..., description="Total gold across analyzed matches")


class VisionStats(BaseModel):
    """Vision scoring statistics."""

    average_vision_score: float = Field(
        ...,
        description="Average vision score per match",
    )
    total_vision_score: int = Field(
        ...,
        description="Total vision score accumulated",
    )


class ObjectiveStats(BaseModel):
    """Objective participation statistics when team data is available."""

    is_available: bool = Field(
        ...,
        description="Indicates whether reliable objective data was present",
    )
    dragon_participation: float | None = Field(
        default=None,
        description="Dragon takedown participation percentage (0-100)",
    )
    baron_participation: float | None = Field(
        default=None,
        description="Baron Nashor takedown participation percentage (0-100)",
    )
    turret_participation: float | None = Field(
        default=None,
        description="Turret destruction participation percentage (0-100)",
    )
    notes: str | None = Field(
        default=None,
        description="Explanatory notes regarding objective calculation",
    )


class PlayerOverallStatsResponse(BaseModel):
    """Consolidated statistical analysis across a player's match history."""

    game_name: str
    tag_line: str
    puuid: str
    region: str
    regional_cluster: str
    matches_requested: int
    matches_analyzed: int
    match_ids: list[str]
    queue_filter: str
    wins: int
    losses: int
    win_rate: float = Field(..., description="Win rate percentage (0 - 100)")
    kda: KdaStats
    cs_per_min: float = Field(..., description="Average creep score per minute")
    total_cs: int = Field(..., description="Total CS across analyzed matches")
    gold: GoldStats
    vision: VisionStats
    objectives: ObjectiveStats


class ChampionStatsEntry(BaseModel):
    """Aggregated statistics for a specific champion."""

    champion_id: int
    champion_name: str
    champion_icon_url: str
    matches_played: int
    wins: int
    losses: int
    win_rate: float
    kills_avg: float
    deaths_avg: float
    assists_avg: float
    kda_ratio: float
    cs_per_min: float
    gold_per_min: float


class PlayerChampionsResponse(BaseModel):
    """Breakdown of most played champions."""

    game_name: str
    tag_line: str
    puuid: str
    region: str
    matches_requested: int
    matches_analyzed: int
    champions: list[ChampionStatsEntry]


class RoleDistributionEntry(BaseModel):
    """Distribution for a lane/position."""

    role: str
    display_name: str
    matches_count: int
    percentage: float
    wins: int
    losses: int
    win_rate: float


class PlayerRolesResponse(BaseModel):
    """Position / lane distribution breakdown."""

    game_name: str
    tag_line: str
    puuid: str
    region: str
    matches_requested: int
    matches_analyzed: int
    roles: list[RoleDistributionEntry]


class PlayerMatchSummary(BaseModel):
    """Individual parsed match summary for a player."""

    match_id: str
    game_creation: int
    game_duration_seconds: int
    game_mode: str
    queue_id: int
    queue_name: str
    is_victory: bool
    champion_id: int
    champion_name: str
    champion_level: int
    champion_icon_url: str
    kills: int
    deaths: int
    assists: int
    kda_ratio: float
    total_cs: int
    cs_per_min: float
    gold_earned: int
    vision_score: int
    items: list[int]
    summoner_spells: list[int]
    kill_participation: float | None = None


class PlayerMatchesResponse(BaseModel):
    """Recent matches list with player specific data."""

    game_name: str
    tag_line: str
    puuid: str
    region: str
    matches_count: int
    matches: list[PlayerMatchSummary]


class MatchDetailResponse(BaseModel):
    """Full detail of a match by match ID."""

    match_id: str
    regional_cluster: str
    game_creation: int
    game_duration_seconds: int
    game_mode: str
    game_version: str
    queue_id: int
    teams: list[dict]
    participants: list[dict]
