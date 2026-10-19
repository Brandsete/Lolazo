from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_secure_logging
from app.core.rate_limiter import RateLimitMiddleware
from app.services.riot_client import riot_client

# Initialize secure logging to scrub API keys and sensitive tokens
setup_secure_logging()

tags_metadata = [
    {
        "name": "Health",
        "description": "Comprobaciones de salud y operatividad del backend.",
    },
    {
        "name": "Regions",
        "description": "Mapeo oficial de regiones y clústers de Riot Games.",
    },
    {
        "name": "Riot API",
        "description": "Monitoreo seguro de integración con Riot Developer Portal.",
    },
    {
        "name": "Players",
        "description": "Consultas oficiales de perfil y clasificaciones competitivas.",
    },
    {
        "name": "Matches",
        "description": "Consultas oficiales de partidas y estadísticas con Match-V5.",
    },
    {
        "name": "Root",
        "description": "Punto de entrada general de la API.",
    },
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager to handle startup and cleanup of HTTP clients."""
    yield
    # Cleanly close persistent HTTPX connection pools on shutdown
    await riot_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "League of Legends Stats Tracker API construida con FastAPI y Riot Games API. "
        "Integración oficial con Account-V1, Summoner-V4, League-V4 y Match-V5."
    ),
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register uniform error handlers for consistent HTTP status codes and responses
register_exception_handlers(app)


# Middleware: Add security headers to all responses
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Middleware: Add application-level rate limiter
app.add_middleware(RateLimitMiddleware)

# Configure restrictive CORS
origins_set = {
    settings.FRONTEND_ORIGIN.strip(),
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
for orig in settings.ALLOWED_ORIGINS.split(","):
    clean_orig = orig.strip()
    if clean_orig:
        origins_set.add(clean_orig)

allowed_origins = sorted(list(origins_set))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS", "HEAD"],
    allow_headers=["Content-Type", "Accept", "X-Requested-With", "Authorization"],
    max_age=600,
)

# Mount endpoints on /api and /api/v1
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint welcoming clients and directing to documentation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/api/health",
            "regions": "/api/regions",
            "riot_status": "/api/riot/status",
            "players": "/api/players/{game_name}/{tag_line}?region={region}",
        },
    }
