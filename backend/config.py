"""
Yuno AI Payment Operations Orchestrator — Configuration

Environment-driven settings using pydantic-settings.
All secrets and configuration are loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # ── Database ──────────────────────────────────────────
    # Default: SQLite for local dev. Set to PostgreSQL URL for production/Docker.
    database_url: str = "sqlite+aiosqlite:///./yuno.db"

    # ── OpenAI ────────────────────────────────────────────
    openai_api_key: str = ""
    default_model: str = "gpt-4o"

    # ── WhatsApp Cloud API ────────────────────────────────
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "yuno-verify-2024"

    # ── Application ───────────────────────────────────────
    app_name: str = "Yuno AI Orchestrator"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton to avoid re-parsing env on every request."""
    return Settings()
