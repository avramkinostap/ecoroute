"""Application settings loaded from environment variables (or a .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EcoRoute API"
    database_url: str = "sqlite:///./ecoroute.db"
    # Comma-separated list of origins allowed by CORS.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # External services (free, no API key required).
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    weather_url: str = "https://api.open-meteo.com/v1/forecast"
    http_timeout_s: float = 6.0

    # Optional AI advisor. Without a key the app falls back to a rule-based advisor.
    anthropic_api_key: str | None = None
    ai_model: str = "claude-haiku-5-5"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
