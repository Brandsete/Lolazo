from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Riot API credentials
    RIOT_API_KEY: str = "RGAPI-00000000-0000-0000-0000-000000000000"

    # Server configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    )

    # Application limits
    MAX_MATCHES: int = 20

    # Cache TTL settings (in seconds)
    CACHE_TTL_SECONDS: int = 300
    CACHE_TTL_PROFILE_SECONDS: int = 300
    CACHE_TTL_LEAGUE_SECONDS: int = 120
    CACHE_TTL_MATCH_SECONDS: int = 3600
    CACHE_TTL_STATS_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 2000

    # External Riot Games API client settings
    RIOT_CONNECT_TIMEOUT: float = 5.0
    RIOT_READ_TIMEOUT: float = 10.0
    RIOT_MAX_CONCURRENT_REQUESTS: int = 10
    RIOT_MAX_RETRIES: int = 2
    RIOT_BACKOFF_FACTOR: float = 0.5
    RIOT_MAX_RETRY_DELAY: float = 3.0

    # Rate limiting for client requests
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # Application metadata
    PROJECT_NAME: str = "RiftTracker API"
    VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
