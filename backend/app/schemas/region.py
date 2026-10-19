from pydantic import BaseModel, Field


class RegionInfo(BaseModel):
    """Information about a League of Legends platform region and its cluster."""

    platform_id: str = Field(
        ...,
        description="Platform routing value for LoL (e.g. la1, na1, euw1)",
        examples=["la1", "na1", "euw1", "kr"],
    )
    name: str = Field(
        ...,
        description="Human readable regional server name",
        examples=["Latin America North", "North America", "Europe West"],
    )
    regional_cluster: str = Field(
        ...,
        description="Regional routing value for Account-V1 and Match-V5",
        examples=["americas", "europe", "asia", "sea"],
    )
    is_active: bool = Field(
        default=True,
        description="Whether this platform region is actively supported",
    )


class RegionsResponse(BaseModel):
    """Response containing supported platform regions and regional clusters."""

    total: int = Field(..., description="Total number of supported regions")
    clusters: list[str] = Field(
        ...,
        description="List of distinct regional clusters for Account-V1 & Match-V5",
    )
    regions: list[RegionInfo] = Field(
        ...,
        description="List of supported platform regions with routing details",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 16,
                "clusters": ["americas", "europe", "asia", "sea"],
                "regions": [
                    {
                        "platform_id": "la1",
                        "name": "Latin America North",
                        "regional_cluster": "americas",
                        "is_active": True,
                    },
                    {
                        "platform_id": "euw1",
                        "name": "Europe West",
                        "regional_cluster": "europe",
                        "is_active": True,
                    },
                ],
            }
        }
    }
