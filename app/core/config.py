from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json

class Settings(BaseSettings):
    APP_NAME: str = "EV-Backend"
    APP_ENV: str = "development"
    SECRET_KEY: str = "ev_super_secret_jwt_key_change_me_in_production"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # OpenRouter LLM Settings
    OPENROUTER_API_KEY: str = ""
    PRIMARY_MODEL: str = "anthropic/claude-3.5-sonnet"
    FALLBACK_MODELS: Union[List[str], str] = [
        "openai/gpt-4o",
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.3-70b-instruct"
    ]

    @field_validator("FALLBACK_MODELS", mode="before")
    def parse_fallback_models(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [m.strip() for m in v.split(",") if m.strip()]
        return v

    # DB & Cache
    DATABASE_URL: str = "postgresql+asyncpg://ev_user:ev_password@localhost:5432/ev_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Devices
    DEVICE_AUTH_SECRET: str = "ev_device_shared_secret_token_12345"
    ALLOWED_CLIENT_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
