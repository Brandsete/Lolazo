import asyncio
import logging
import random

import httpx

from app.core.config import settings
from app.core.exceptions import (
    RiotApiException,
    RiotAuthException,
    RiotBadRequestException,
    RiotMatchNotFoundException,
    RiotPlayerNotFoundException,
    RiotRateLimitException,
    RiotServerException,
    RiotServiceUnavailableException,
    RiotTimeoutException,
    RiotUnauthorizedException,
)

logger = logging.getLogger("rifttracker.riot_client")


class RiotApiClient:
    """Asynchronous HTTP client for Riot Games official APIs.

    Features:
    - Centralized error response handling (400, 401, 403, 404, 429, 5xx)
    - External request timeouts and concurrency limits (via asyncio.Semaphore)
    - Selective retries for transient errors only, respecting Retry-After
    - Strict protection of secrets from logs and exceptions
    """

    def __init__(self, timeout: httpx.Timeout | None = None) -> None:
        self.timeout = timeout or httpx.Timeout(
            timeout=settings.RIOT_READ_TIMEOUT,
            connect=settings.RIOT_CONNECT_TIMEOUT,
        )
        self._client: httpx.AsyncClient | None = None
        self._concurrency_semaphore = asyncio.Semaphore(
            settings.RIOT_MAX_CONCURRENT_REQUESTS
        )

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize persistent async HTTPX client with pool limits."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_connections=settings.RIOT_MAX_CONCURRENT_REQUESTS * 2,
                max_keepalive_connections=settings.RIOT_MAX_CONCURRENT_REQUESTS,
            )
            self._client = httpx.AsyncClient(timeout=self.timeout, limits=limits)
        return self._client


    async def aclose(self) -> None:
        """Properly close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> dict[str, str]:
        """Construct request headers with X-Riot-Token exclusively from settings."""
        key = (settings.RIOT_API_KEY or "").strip()
        return {
            "X-Riot-Token": key,
            "Accept": "application/json",
            "User-Agent": "RiftTracker/0.1.0",
        }

    def _validate_api_key(self) -> None:
        """Fail fast if key is missing or is the default placeholder."""
        key = (settings.RIOT_API_KEY or "").strip()
        if not key or "00000000" in key:
            raise RiotAuthException(
                "Riot Games API key is not configured or using default placeholder. "
                "Please configure RIOT_API_KEY in your .env file."
            )

    def _handle_error_response(self, response: httpx.Response, url: str) -> None:
        """Centralized and differentiated treatment of Riot API HTTP error codes."""
        status = response.status_code

        if status == 400:
            raise RiotBadRequestException(
                "Riot API rejected the request for resource with HTTP 400."
            )

        if status == 401:
            raise RiotUnauthorizedException(
                "Riot Games API key is unauthorized or missing (HTTP 401)."
            )

        if status == 403:
            raise RiotAuthException(
                "Invalid, missing or expired RIOT_API_KEY. "
                "Ensure your developer key is active at developer.riotgames.com."
            )

        if status == 404:
            if "/match/v5/matches/" in url:
                raise RiotMatchNotFoundException()
            raise RiotPlayerNotFoundException()

        if status == 429:
            retry_after_hdr = response.headers.get("Retry-After")
            retry_seconds = (
                int(retry_after_hdr)
                if retry_after_hdr and retry_after_hdr.isdigit()
                else None
            )
            raise RiotRateLimitException(
                detail="Riot Games API rate limit exceeded.",
                retry_after=retry_seconds,
            )

        if status == 503:
            retry_after_hdr = response.headers.get("Retry-After")
            retry_seconds = (
                int(retry_after_hdr)
                if retry_after_hdr and retry_after_hdr.isdigit()
                else None
            )
            raise RiotServiceUnavailableException(
                detail="Riot Games upstream service is temporarily unavailable.",
                retry_after=retry_seconds,
            )

        if status >= 500:
            raise RiotServerException(
                f"Riot Games upstream service error (HTTP {status})"
            )

        raise RiotApiException(
            detail=f"Unexpected response from Riot API (HTTP {status})",
            status_code=status,
        )

    async def _request(self, url: str) -> dict | list:
        """Execute request with concurrency limits, timeouts, and selective retries."""
        self._validate_api_key()
        client = await self.get_client()
        headers = self._get_headers()

        max_retries = max(0, settings.RIOT_MAX_RETRIES)
        attempt = 0

        while True:
            attempt += 1
            try:
                # Wrap in concurrency semaphore to limit parallel outgoing calls
                async with self._concurrency_semaphore:
                    response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.json()

                # Differentiate status codes
                status = response.status_code

                # Non-retryable client errors: fail immediately
                if status in (400, 401, 403, 404):
                    self._handle_error_response(response, url)

                # Upstream Rate Limit 429: Retry ONLY IF retry_after is small
                if status == 429:
                    retry_after_hdr = response.headers.get("Retry-After")
                    retry_seconds = (
                        int(retry_after_hdr)
                        if retry_after_hdr and retry_after_hdr.isdigit()
                        else None
                    )
                    if (
                        attempt <= max_retries
                        and retry_seconds is not None
                        and retry_seconds <= settings.RIOT_MAX_RETRY_DELAY
                    ):
                        logger.warning(
                            "Riot API 429 received. Retrying after %ds (%d/%d)",
                            retry_seconds,
                            attempt,
                            max_retries,
                        )
                        await asyncio.sleep(retry_seconds)
                        continue

                    self._handle_error_response(response, url)

                # Upstream 5xx errors: retry if attempts remaining
                if status in (500, 502, 503, 504) and attempt <= max_retries:
                    retry_after_hdr = response.headers.get("Retry-After")
                    delay = (
                        int(retry_after_hdr)
                        if retry_after_hdr and retry_after_hdr.isdigit()
                        else min(
                            settings.RIOT_MAX_RETRY_DELAY,
                            settings.RIOT_BACKOFF_FACTOR * (2 ** (attempt - 1))
                            + random.uniform(0.05, 0.2),
                        )
                    )
                    logger.warning(
                        "Upstream Riot error %d. Retrying in %.2fs (%d/%d)",
                        status,
                        delay,
                        attempt,
                        max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue

                self._handle_error_response(response, url)

            except (RiotApiException, RiotAuthException):
                raise
            except httpx.TimeoutException as exc:
                if attempt <= max_retries:
                    delay = min(
                        settings.RIOT_MAX_RETRY_DELAY,
                        settings.RIOT_BACKOFF_FACTOR * (2 ** (attempt - 1)),
                    )
                    logger.warning(
                        "Riot API timed out. Retrying in %.2fs (%d/%d)",
                        delay,
                        attempt,
                        max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RiotTimeoutException(
                    f"Riot API request timed out after {self.timeout.read}s"
                ) from exc
            except httpx.RequestError as exc:
                if attempt <= max_retries:
                    delay = min(
                        settings.RIOT_MAX_RETRY_DELAY,
                        settings.RIOT_BACKOFF_FACTOR * (2 ** (attempt - 1)),
                    )
                    logger.warning(
                        "Network error on Riot API. Retrying in %.2fs (%d/%d)",
                        delay,
                        attempt,
                        max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise RiotServerException(
                    "Failed to establish connection to Riot Games API servers"
                ) from exc


    # -------------------------------------------------------------------------
    # Account-V1: Uses Regional Cluster (americas, europe, asia, sea)
    # -------------------------------------------------------------------------
    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str, regional_cluster: str
    ) -> dict:
        """Resolve Riot ID to PUUID using Account-V1 on the regional cluster."""
        cluster = regional_cluster.lower().strip()
        url = (
            f"https://{cluster}.api.riotgames.com/riot/account/v1/accounts"
            f"/by-riot-id/{game_name}/{tag_line}"
        )
        return await self._request(url)

    # -------------------------------------------------------------------------
    # Summoner-V4: Uses Platform Region (la1, na1, euw1, kr, etc.)
    # -------------------------------------------------------------------------
    async def get_summoner_by_puuid(self, puuid: str, platform_id: str) -> dict:
        """Fetch summoner profile (level, icon, id) using Summoner-V4."""
        platform = platform_id.lower().strip()
        url = (
            f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners"
            f"/by-puuid/{puuid}"
        )
        return await self._request(url)

    # -------------------------------------------------------------------------
    # League-V4: Uses Platform Region (la1, na1, euw1, kr, etc.)
    # -------------------------------------------------------------------------
    async def get_league_entries_by_summoner(
        self, summoner_id: str, platform_id: str
    ) -> list[dict]:
        """Fetch competitive rank entries (Solo/Duo, Flex) using League-V4."""
        platform = platform_id.lower().strip()
        url = (
            f"https://{platform}.api.riotgames.com/lol/league/v4/entries"
            f"/by-summoner/{summoner_id}"
        )
        result = await self._request(url)
        return result if isinstance(result, list) else []

    # -------------------------------------------------------------------------
    # Match-V5: Uses Regional Cluster (americas, europe, asia, sea)
    # -------------------------------------------------------------------------
    async def get_match_ids_by_puuid(
        self,
        puuid: str,
        regional_cluster: str,
        start: int = 0,
        count: int = 20,
        queue: int | None = None,
    ) -> list[str]:
        """Fetch match IDs list for a given PUUID using Match-V5."""
        cluster = regional_cluster.lower().strip()
        url = (
            f"https://{cluster}.api.riotgames.com/lol/match/v5/matches"
            f"/by-puuid/{puuid}/ids?start={start}&count={count}"
        )
        if queue is not None:
            url += f"&queue={queue}"
        result = await self._request(url)
        return result if isinstance(result, list) else []

    async def get_match_by_id(self, match_id: str, regional_cluster: str) -> dict:
        """Fetch detailed match data by match ID using Match-V5."""
        cluster = regional_cluster.lower().strip()
        url = f"https://{cluster}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return await self._request(url)


riot_client = RiotApiClient()
