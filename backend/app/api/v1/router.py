from fastapi import APIRouter

from app.api.v1.endpoints import health, matches, players, regions, riot

api_router = APIRouter()

# Mount health, regions, riot, players and matches endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(regions.router, tags=["Regions"])
api_router.include_router(riot.router, tags=["Riot API"])
api_router.include_router(players.router, tags=["Players"])
api_router.include_router(matches.router, tags=["Matches"])
