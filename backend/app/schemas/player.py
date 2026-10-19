from pydantic import BaseModel, Field


class PlayerRankEntry(BaseModel):
    """Competitive ranking entry for a specific queue (Solo/Duo or Flex)."""

    queue_type: str = Field(
        ...,
        description="Queue identifier (e.g. RANKED_SOLO_5x5, RANKED_FLEX_SR)",
        examples=["RANKED_SOLO_5x5", "RANKED_FLEX_SR"],
    )
    tier: str = Field(
        ...,
        description="Rank tier (e.g. CHALLENGER, GRANDMASTER, DIAMOND, GOLD)",
        examples=["CHALLENGER", "DIAMOND"],
    )
    rank: str = Field(
        ...,
        description="Division rank within the tier (I, II, III, IV)",
        examples=["I", "II"],
    )
    league_points: int = Field(
        ...,
        description="Current League Points (LP)",
        examples=[450, 75],
    )
    wins: int = Field(..., description="Total ranked wins")
    losses: int = Field(..., description="Total ranked losses")
    win_rate: float = Field(
        ...,
        description="Calculated win rate percentage (0 - 100)",
        examples=[62.5],
    )
    veteran: bool = Field(default=False)
    inactive: bool = Field(default=False)
    fresh_blood: bool = Field(default=False)
    hot_streak: bool = Field(default=False)


class PlayerProfileResponse(BaseModel):
    """Consolidated player profile including account, summoner and league entries."""

    puuid: str = Field(
        ...,
        description="Encrypted Riot PUUID (Globally unique player identifier)",
    )
    game_name: str = Field(..., description="Riot ID game name", examples=["Faker"])
    tag_line: str = Field(..., description="Riot ID tag line", examples=["KR1"])
    summoner_id: str | None = Field(
        default=None,
        description="Encrypted summoner ID specific to platform region",
    )
    summoner_level: int = Field(
        default=1,
        description="Current summoner level",
        examples=[684],
    )
    profile_icon_id: int = Field(
        default=29,
        description="Profile icon ID",
        examples=[588],
    )
    profile_icon_url: str = Field(
        ...,
        description="Direct Data Dragon CDN URL for the summoner profile icon",
    )
    region: str = Field(
        ...,
        description="Platform region queried (e.g. la1, na1, euw1, kr)",
        examples=["la1", "kr"],
    )
    regional_cluster: str = Field(
        ...,
        description="Regional routing cluster (americas, europe, asia, sea)",
        examples=["americas", "asia"],
    )
    ranks: list[PlayerRankEntry] = Field(
        default_factory=list,
        description="List of competitive ranked entries",
    )
    solo_rank: PlayerRankEntry | None = Field(
        default=None,
        description="Convenience shortcut for Solo/Duo queue rank",
    )
    flex_rank: PlayerRankEntry | None = Field(
        default=None,
        description="Convenience shortcut for Flex queue rank",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "puuid": "abcdef12-3456-7890-abcd-ef1234567890",
                "game_name": "Faker",
                "tag_line": "KR1",
                "summoner_id": "encrypted-summoner-id-1234",
                "summoner_level": 684,
                "profile_icon_id": 588,
                "profile_icon_url": "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/profileicon/588.png",
                "region": "kr",
                "regional_cluster": "asia",
                "ranks": [
                    {
                        "queue_type": "RANKED_SOLO_5x5",
                        "tier": "GRANDMASTER",
                        "rank": "I",
                        "league_points": 645,
                        "wins": 142,
                        "losses": 78,
                        "win_rate": 64.55,
                        "veteran": True,
                        "inactive": False,
                        "fresh_blood": False,
                        "hot_streak": True,
                    }
                ],
                "solo_rank": {
                    "queue_type": "RANKED_SOLO_5x5",
                    "tier": "GRANDMASTER",
                    "rank": "I",
                    "league_points": 645,
                    "wins": 142,
                    "losses": 78,
                    "win_rate": 64.55,
                    "veteran": True,
                    "inactive": False,
                    "fresh_blood": False,
                    "hot_streak": True,
                },
                "flex_rank": None,
            }
        }
    }
