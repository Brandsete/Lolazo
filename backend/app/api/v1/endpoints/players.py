from fastapi import APIRouter, Path, Query

from app.core.cache import (
    build_champions_key,
    build_matches_summary_key,
    build_roles_key,
    build_stats_key,
    cache,
)
from app.core.config import settings
from app.core.validation import (
    validate_matches_count,
    validate_queue_param,
    validate_region,
    validate_riot_id,
)
from app.schemas.player import PlayerProfileResponse
from app.schemas.stats import (
    PlayerChampionsResponse,
    PlayerMatchesResponse,
    PlayerOverallStatsResponse,
    PlayerRolesResponse,
)
from app.services.match_service import match_service
from app.services.player_service import player_service
from app.services.stats_service import stats_service

router = APIRouter()


@router.get(
    "/players/{game_name}/{tag_line}",
    response_model=PlayerProfileResponse,
    summary="Consultar perfil y clasificación competitiva de un jugador",
    description=(
        "Consulta la información del jugador mediante la API oficial de Riot Games. "
        "Utiliza Account-V1 para resolver el Riot ID a PUUID, "
        "Summoner-V4 para nivel e icono, "
        "y League-V4 para las clasificaciones competitivas."
    ),
)
async def get_player_profile(
    game_name: str = Path(
        ...,
        description="Nombre de juego del Riot ID (Game Name)",
        examples=["Faker", "Josedeodo"],
    ),
    tag_line: str = Path(
        ...,
        description="Etiqueta del Riot ID (sin el símbolo #)",
        examples=["KR1", "LAN"],
    ),
    region: str = Query(
        ...,
        description="Plataforma regional (ej. LA1, LA2, NA1, EUW1, KR)",
        examples=["LA1", "KR", "NA1", "EUW1"],
    ),
) -> PlayerProfileResponse:
    """Retrieve player account, summoner info and ranked ladder entries."""
    valid_name, valid_tag = validate_riot_id(game_name, tag_line)
    valid_region = validate_region(region)

    return await player_service.get_player_profile(
        game_name=valid_name,
        tag_line=valid_tag,
        platform_id=valid_region,
    )


@router.get(
    "/players/{game_name}/{tag_line}/stats",
    response_model=PlayerOverallStatsResponse,
    summary="Análisis estadístico global del jugador en partidas recientes",
    description=(
        "Calcula victorias, derrotas, porcentaje de victorias, KDA global, "
        "CS por minuto, oro promedio, visión y participación en objetivos "
        "a partir de partidas reales consultadas en Match-V5."
    ),
)
async def get_player_stats(
    game_name: str = Path(..., description="Nombre de juego del Riot ID"),
    tag_line: str = Path(..., description="Etiqueta del Riot ID"),
    region: str = Query(..., description="Plataforma regional (ej. LA1, KR)"),
    queue: str = Query(
        default="ranked",
        description="Filtro de cola: ranked, solo, flex, normal, aram, all",
    ),
    matches: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Cantidad de partidas a analizar (1 - 100)",
    ),
) -> PlayerOverallStatsResponse:
    """Compute consolidated statistical metrics over recent matches with caching."""
    valid_name, valid_tag = validate_riot_id(game_name, tag_line)
    valid_region = validate_region(region)
    valid_queue = validate_queue_param(queue) or "ranked"
    valid_matches = validate_matches_count(matches, 1, 100)

    # Check cache for aggregated player stats
    cache_key = build_stats_key(
        valid_region, valid_name, valid_tag, valid_queue, valid_matches
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    parsed, ids, context = await match_service.get_player_match_history_parsed(
        game_name=valid_name,
        tag_line=valid_tag,
        platform_id=valid_region,
        count=valid_matches,
        queue=valid_queue,
    )
    result = stats_service.calculate_overall_stats(
        parsed_matches=parsed,
        match_ids=ids,
        requested_count=valid_matches,
        queue_filter=valid_queue,
        player_context=context,
    )
    cache.set(cache_key, result, settings.CACHE_TTL_STATS_SECONDS)
    return result


@router.get(
    "/players/{game_name}/{tag_line}/champions",
    response_model=PlayerChampionsResponse,
    summary="Campeones más utilizados con win rate y KDA",
    description=(
        "Agrupa las partidas analizadas por campeón y calcula partidas jugadas, "
        "win rate, KDA individual, CS por minuto y oro por minuto."
    ),
)
async def get_player_champions(
    game_name: str = Path(..., description="Nombre de juego del Riot ID"),
    tag_line: str = Path(..., description="Etiqueta del Riot ID"),
    region: str = Query(..., description="Plataforma regional (ej. LA1, KR)"),
    matches: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Cantidad de partidas a analizar (1 - 100)",
    ),
) -> PlayerChampionsResponse:
    """Aggregate champion statistics across recent matches with caching."""
    valid_name, valid_tag = validate_riot_id(game_name, tag_line)
    valid_region = validate_region(region)
    valid_matches = validate_matches_count(matches, 1, 100)

    cache_key = build_champions_key(valid_region, valid_name, valid_tag, valid_matches)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    parsed, _ids, context = await match_service.get_player_match_history_parsed(
        game_name=valid_name,
        tag_line=valid_tag,
        platform_id=valid_region,
        count=valid_matches,
    )
    result = stats_service.calculate_champion_stats(
        parsed_matches=parsed,
        requested_count=valid_matches,
        player_context=context,
    )
    cache.set(cache_key, result, settings.CACHE_TTL_STATS_SECONDS)
    return result


@router.get(
    "/players/{game_name}/{tag_line}/roles",
    response_model=PlayerRolesResponse,
    summary="Distribución de posiciones y carriles jugados",
    description=(
        "Calcula la distribución porcentual de posiciones (TOP, JUNGLE, MID, "
        "ADC, SUPPORT) y su respectiva tasa de victoria."
    ),
)
async def get_player_roles(
    game_name: str = Path(..., description="Nombre de juego del Riot ID"),
    tag_line: str = Path(..., description="Etiqueta del Riot ID"),
    region: str = Query(..., description="Plataforma regional (ej. LA1, KR)"),
    matches: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Cantidad de partidas a analizar (1 - 100)",
    ),
) -> PlayerRolesResponse:
    """Calculate role/lane distribution based on Match-V5 position data with caching."""
    valid_name, valid_tag = validate_riot_id(game_name, tag_line)
    valid_region = validate_region(region)
    valid_matches = validate_matches_count(matches, 1, 100)

    cache_key = build_roles_key(valid_region, valid_name, valid_tag, valid_matches)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    parsed, _ids, context = await match_service.get_player_match_history_parsed(
        game_name=valid_name,
        tag_line=valid_tag,
        platform_id=valid_region,
        count=valid_matches,
    )
    result = stats_service.calculate_role_distribution(
        parsed_matches=parsed,
        requested_count=valid_matches,
        player_context=context,
    )
    cache.set(cache_key, result, settings.CACHE_TTL_STATS_SECONDS)
    return result


@router.get(
    "/players/{game_name}/{tag_line}/matches",
    response_model=PlayerMatchesResponse,
    summary="Historial de partidas recientes del jugador",
    description=(
        "Devuelve las partidas recientes parseadas con el rendimiento individual "
        "del jugador (resultado, KDA, CS, objetos, hechizos y duración)."
    ),
)
async def get_player_matches(
    game_name: str = Path(..., description="Nombre de juego del Riot ID"),
    tag_line: str = Path(..., description="Etiqueta del Riot ID"),
    region: str = Query(..., description="Plataforma regional (ej. LA1, KR)"),
    count: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Cantidad de partidas a consultar",
    ),
) -> PlayerMatchesResponse:
    """Retrieve parsed recent matches for the specified player with caching."""
    valid_name, valid_tag = validate_riot_id(game_name, tag_line)
    valid_region = validate_region(region)
    valid_count = validate_matches_count(count, 1, 100)

    cache_key = build_matches_summary_key(
        valid_region, valid_name, valid_tag, valid_count
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    parsed, _ids, context = await match_service.get_player_match_history_parsed(
        game_name=valid_name,
        tag_line=valid_tag,
        platform_id=valid_region,
        count=valid_count,
    )

    summaries = []
    for m in parsed:
        raw = m.get("raw_data")
        if raw:
            summary = match_service.parse_player_match_summary(raw, context["puuid"])
            if summary:
                summaries.append(summary)

    response = PlayerMatchesResponse(
        game_name=context["game_name"],
        tag_line=context["tag_line"],
        puuid=context["puuid"],
        region=context["region"],
        matches_count=len(summaries),
        matches=summaries,
    )
    cache.set(cache_key, response, settings.CACHE_TTL_STATS_SECONDS)
    return response
