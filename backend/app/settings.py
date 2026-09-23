"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MCP Server Forge API"
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "mcp_forge"
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
