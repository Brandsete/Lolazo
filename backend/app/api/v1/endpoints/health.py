from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Verificar salud del backend",
    description=(
        "Comprueba que el backend de FastAPI esté en ejecución "
        "y devuelve metadatos de configuración."
    ),
)
async def get_health() -> HealthCheckResponse:
    """Check backend service health and return operational parameters."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        cache_ttl_seconds=settings.CACHE_TTL_SECONDS,
        max_matches=settings.MAX_MATCHES,
    )
