"""Configuración central leída desde variables de entorno (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CineGame AI"
    database_url: str = "sqlite:///./local.db"

    # Seguridad
    jwt_secret: str = "cambia-esta-clave-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 8

    # IA (cualquier proveedor compatible con la API de OpenAI: Groq, OpenAI, etc.)
    llm_provider: str = "groq"  # groq | openai | fake
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"

    # Datos iniciales
    admin_username: str = "admin"
    admin_password: str = "Admin123!"
    default_token_limit: int = 50000

    # Memoria conversacional: cuántos intercambios previos se envían al modelo
    memory_turns: int = 6
    rag_top_k: int = 8

    cors_origins: str = "*"
    app_timezone: str = "America/Guatemala"


@lru_cache
def get_settings() -> Settings:
    return Settings()
