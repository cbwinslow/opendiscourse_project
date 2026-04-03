import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # Database
    database_url: str = "postgresql+asyncpg://cbwinslow:password@localhost:5432/opendiscourse"
    database_url_sync: str = "postgresql+psycopg2://cbwinslow:password@localhost:5432/opendiscourse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API Keys
    congress_gov_api_key: str = ""
    govinfo_api_key: str = ""
    fec_api_key: str = ""
    opensecrets_api_key: str = ""
    finnhub_api_key: str = ""
    fmp_api_key: str = ""
    apify_api_token: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Ingestion
    ingestion_concurrency: int = 5
    ingestion_batch_size: int = 1000
    ingestion_rate_limit_delay: float = 0.1

    # Data directory
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
