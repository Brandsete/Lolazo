from fastapi import APIRouter

from app.schemas.riot_status import RiotStatusResponse
from app.services.riot_service import riot_service

router = APIRouter()


@router.get(
    "/riot/status",
    response_model=RiotStatusResponse,
    summary="Consultar estado de la clave de Riot Games API",
    description=(
        "Indica si la clave RIOT_API_KEY se encuentra configurada en el entorno "
        "sin revelar su valor en ningún momento."
    ),
)
async def get_riot_status() -> RiotStatusResponse:
    """Check whether RIOT_API_KEY is configured without exposing secret credentials."""
    return riot_service.get_api_status()
