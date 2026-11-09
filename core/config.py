# core/config.py
"""
Configuration management using pydantic-settings.
Loads environment variables from .env file or system environment.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Ingestion Settings
    ingestion_source: str = Field(default="mock", alias="INGESTION_SOURCE")
    mock_target_email: str = Field(default="sarathybhas@gmail.com", alias="MOCK_TARGET_EMAIL")

    # Gmail API OAuth Paths
    gmail_credentials_path: str = Field(default="ingestion/credentials.json", alias="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str = Field(default="ingestion/token.json", alias="GMAIL_TOKEN_PATH")

    # Storage Settings
    database_path: str = Field(default="storage/emails.db", alias="DATABASE_PATH")

    # API Server Settings
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # TUDS Algorithm Defaults
    default_alpha: float = Field(default=1.5, alias="DEFAULT_ALPHA")
    default_user_weight: float = Field(default=0.8, alias="DEFAULT_USER_WEIGHT")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def absolute_db_path(self) -> Path:
        p = Path(self.database_path)
        return p if p.is_absolute() else (BASE_DIR / p)


settings = Settings()
