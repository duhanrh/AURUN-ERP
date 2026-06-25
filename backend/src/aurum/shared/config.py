"""Configuración de la aplicación (pydantic-settings).

Carga variables de entorno con prefijo ``AURUM_`` (ver ``.env.example``).
El dominio nunca importa este módulo; solo lo usan main/infraestructura.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "development", "staging", "production"]


class Settings(BaseSettings):
    """Parámetros de configuración del backend, resueltos desde el entorno."""

    model_config = SettingsConfigDict(
        env_prefix="AURUM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Environment = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aurum_dev"
    redis_url: str = "redis://localhost:6379/0"

    jwt_private_key_path: str = ""
    jwt_public_key_path: str = ""
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 1209600

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) — usar como dependencia en FastAPI."""
    return Settings()
