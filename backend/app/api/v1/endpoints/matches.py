from fastapi import APIRouter, Path, Query

from app.core.validation import validate_match_id, validate_region
from app.schemas.stats import MatchDetailResponse
from app.services.match_service import match_service

router = APIRouter()


@router.get(
    "/matches/{match_id}",
    response_model=MatchDetailResponse,
    summary="Consultar detalles completos de una partida por ID",
    description=(
        "Obtiene los datos detallados de una partida oficial mediante Match-V5 "
        "(duración, modo, equipos, objetivos y los 10 participantes)."
    ),
)
async def get_match_by_id(
    match_id: str = Path(
        ...,
        description="Identificador único de la partida (ej. LA1_1234567890)",
        examples=["LA1_1234567890", "KR_7109283921"],
    ),
    region: str = Query(
        ...,
        description="Plataforma regional para resolver el clúster (ej. LA1, KR)",
        examples=["LA1", "KR", "EUW1"],
    ),
) -> MatchDetailResponse:
    """Retrieve full match detail for specified match ID with parameter validation."""
    valid_id = validate_match_id(match_id)

    valid_platform = validate_region(region)

    return await match_service.get_match_formatted_detail(
        match_id=valid_id,
        platform_id=valid_platform,
    )
