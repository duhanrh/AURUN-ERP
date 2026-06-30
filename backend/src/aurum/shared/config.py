"""Configuración de la aplicación (pydantic-settings).

Carga variables de entorno con prefijo ``AURUM_`` (ver ``.env.example``).
La conexión a la base de datos se define por componentes independientes
(host, puerto, usuario, contraseña, nombre) y la URL se construye aquí, aplicando
URL-encoding a usuario/contraseña (necesario si contienen caracteres especiales).
El dominio nunca importa este módulo; solo lo usan main/infraestructura.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import quote

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

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

    # ── Base de datos (componentes independientes, configurables desde .env) ──
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "aurum_app"
    db_password: str = "aurum_app"
    db_name: str = "aurum_dev"

    # ── Bootstrap: superusuario de PostgreSQL (solo para crear rol+BD) ──
    # Acepta nombres con o sin prefijo AURUM_ para comodidad del operador.
    db_superuser: str = Field(
        default="postgres",
        validation_alias=AliasChoices("AURUM_DB_SUPERUSER", "POSTGRES_SUPERUSER"),
    )
    db_superuser_password: str = Field(
        default="",
        validation_alias=AliasChoices("AURUM_DB_SUPERUSER_PASSWORD", "POSTGRES_SUPERUSER_PASSWORD"),
    )

    redis_url: str = "redis://localhost:6379/0"

    jwt_private_key_path: str = ""
    jwt_public_key_path: str = ""
    jwt_access_ttl_seconds: int = 900
    jwt_refresh_ttl_seconds: int = 1209600

    # Token compartido para la API de provisionamiento de plataforma (sección 5.7).
    # Vacío en local/dev => endpoint abierto; obligatorio fuera de local.
    platform_admin_token: str = ""

    # Reconciliación del RBAC al arrancar: la BD converge a la fuente de verdad del
    # código (catálogo de permisos + roles base) en cada despliegue. Idempotente.
    reconcile_roles_on_startup: bool = True

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv_origins(cls, value: object) -> object:
        """Permite definir CORS como lista separada por comas en el .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def _build_url(self, driver: str, user: str, password: str) -> str:
        """Construye una URL de conexión con credenciales URL-encoded."""
        return (
            f"{driver}://{quote(user, safe='')}:{quote(password, safe='')}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url(self) -> str:
        """URL async (asyncpg) que usa la aplicación como rol de aplicación."""
        return self._build_url("postgresql+asyncpg", self.db_user, self.db_password)

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada) — usar como dependencia en FastAPI."""
    return Settings()
