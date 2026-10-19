from fastapi import APIRouter, Query

from app.core.validation import validate_cluster, validate_region
from app.schemas.region import RegionInfo, RegionsResponse
from app.services.region_service import region_service

router = APIRouter()


@router.get(
    "/regions",
    response_model=RegionsResponse,
    summary="Listar regiones de plataforma y clústers regionales",
    description=(
        "Devuelve las regiones de plataforma admitidas para League of Legends "
        "(ej. la1, na1, euw1) y su mapeo al clúster regional correspondiente "
        "(americas, europe, asia, sea) utilizado por Account-V1 y Match-V5."
    ),
)
async def get_regions(
    cluster: str | None = Query(
        default=None,
        description=(
            "Filtrar por clúster regional específico (ej. americas, europe, asia, sea)"
        ),
        examples=["americas", "europe"],
    ),
) -> RegionsResponse:
    """Retrieve supported platform regions and their corresponding regional cluster."""
    valid_cluster = validate_cluster(cluster)
    return region_service.get_all_regions(cluster_filter=valid_cluster)


@router.get(
    "/regions/{platform_id}",
    response_model=RegionInfo,
    summary="Consultar región de plataforma por ID",
    description="Devuelve el clúster regional y datos de una plataforma específica.",
)
async def get_region_by_platform(platform_id: str) -> RegionInfo:
    """Retrieve a single platform region by platform ID with validation."""
    valid_platform = validate_region(platform_id)
    return region_service.get_region_by_platform(valid_platform)
