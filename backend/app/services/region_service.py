from app.core.exceptions import InvalidRegionException
from app.schemas.region import RegionInfo, RegionsResponse

# Official Riot Games Platform to Regional Cluster mapping
# Used for routing League of Legends requests between Platform endpoints
# (Summoner-V4, League-V4) and Regional Cluster endpoints (Account-V1, Match-V5)
SUPPORTED_REGIONS: list[RegionInfo] = [
    # Americas Cluster
    RegionInfo(
        platform_id="la1",
        name="Latin America North",
        regional_cluster="americas",
        is_active=True,
    ),
    RegionInfo(
        platform_id="la2",
        name="Latin America South",
        regional_cluster="americas",
        is_active=True,
    ),
    RegionInfo(
        platform_id="na1",
        name="North America",
        regional_cluster="americas",
        is_active=True,
    ),
    RegionInfo(
        platform_id="br1",
        name="Brazil",
        regional_cluster="americas",
        is_active=True,
    ),
    # Europe Cluster
    RegionInfo(
        platform_id="euw1",
        name="Europe West",
        regional_cluster="europe",
        is_active=True,
    ),
    RegionInfo(
        platform_id="eun1",
        name="Europe Nordic & East",
        regional_cluster="europe",
        is_active=True,
    ),
    RegionInfo(
        platform_id="tr1",
        name="Turkey",
        regional_cluster="europe",
        is_active=True,
    ),
    RegionInfo(
        platform_id="ru",
        name="Russia",
        regional_cluster="europe",
        is_active=True,
    ),
    RegionInfo(
        platform_id="me1",
        name="Middle East",
        regional_cluster="europe",
        is_active=True,
    ),
    # Asia Cluster
    RegionInfo(
        platform_id="kr",
        name="Korea",
        regional_cluster="asia",
        is_active=True,
    ),
    RegionInfo(
        platform_id="jp1",
        name="Japan",
        regional_cluster="asia",
        is_active=True,
    ),
    # SEA / Oceania Cluster
    RegionInfo(
        platform_id="oc1",
        name="Oceania",
        regional_cluster="sea",
        is_active=True,
    ),
    RegionInfo(
        platform_id="ph2",
        name="Philippines",
        regional_cluster="sea",
        is_active=True,
    ),
    RegionInfo(
        platform_id="sg2",
        name="Singapore, Malaysia, Indonesia",
        regional_cluster="sea",
        is_active=True,
    ),
    RegionInfo(
        platform_id="th2",
        name="Thailand",
        regional_cluster="sea",
        is_active=True,
    ),
    RegionInfo(
        platform_id="tw2",
        name="Taiwan, Hong Kong, Macao",
        regional_cluster="sea",
        is_active=True,
    ),
    RegionInfo(
        platform_id="vn2",
        name="Vietnam",
        regional_cluster="sea",
        is_active=True,
    ),
]

SUPPORTED_CLUSTERS = sorted(
    list({region.regional_cluster for region in SUPPORTED_REGIONS})
)


class RegionService:
    """Service to handle LoL platform and regional cluster mapping."""

    @staticmethod
    def get_all_regions(cluster_filter: str | None = None) -> RegionsResponse:
        """Return all supported platform regions, optionally filtered by cluster."""
        regions = SUPPORTED_REGIONS
        if cluster_filter:
            norm_cluster = cluster_filter.lower().strip()
            if norm_cluster not in SUPPORTED_CLUSTERS:
                clusters_str = ", ".join(SUPPORTED_CLUSTERS)
                raise InvalidRegionException(
                    f"Cluster '{cluster_filter}' is invalid. Supported: {clusters_str}"
                )
            regions = [r for r in regions if r.regional_cluster == norm_cluster]

        return RegionsResponse(
            total=len(regions),
            clusters=SUPPORTED_CLUSTERS,
            regions=regions,
        )

    @staticmethod
    def get_region_by_platform(platform_id: str) -> RegionInfo:
        """Find a region by its platform ID (e.g. 'la1', 'euw1')."""
        norm_id = platform_id.lower().strip()
        for region in SUPPORTED_REGIONS:
            if region.platform_id == norm_id:
                return region
        valid_ids = ", ".join([r.platform_id for r in SUPPORTED_REGIONS])
        raise InvalidRegionException(
            f"Platform '{platform_id}' is unsupported. Valid platforms: {valid_ids}"
        )

    @staticmethod
    def get_cluster_for_platform(platform_id: str) -> str:
        """Resolve regional cluster (americas/europe/asia/sea) for routing."""
        region = RegionService.get_region_by_platform(platform_id)
        return region.regional_cluster


region_service = RegionService()
