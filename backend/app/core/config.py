from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Part Dataset Studio"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://studio:studio@postgres:5432/studio"
    redis_url: str = "redis://redis:6379/0"
    storage_root: Path = Path("/data/storage")
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
