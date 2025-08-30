"""
Scrabbot bot configuration with Pydantic.
"""

from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Scrabbot bot configuration."""

    # Telegram bot configuration
    telegram_bot_token: str = Field("dev-token", description="Telegram bot token")
    telegram_webhook_url: Optional[str] = Field(None, description="Telegram webhook URL")

    # Database configuration
    database_url: str = Field("sqlite:///./data/scrabbot.db", description="Database URL")

    # Redis configuration (optional)
    redis_url: Optional[str] = Field(None, description="Redis URL")

    # API configuration
    api_host: str = Field("0.0.0.0", description="API listening address")
    api_port: int = Field(8000, description="API listening port")
    api_secret_key: str = Field("dev-secret-key", description="API secret key")

    # Godot
    godot_executable_path: Optional[str] = Field(None, description="Path to Godot executable")
    godot_project_path: str = Field("./godot", description="Path to Godot project")
    godot_web_url: Optional[str] = Field(None, description="Godot web application URL")

    # Logging configuration
    log_level: str = Field("INFO", description="Log level")
    log_file: str = Field("logs/scrabbot.log", description="Log file")

    # Environment configuration
    environment: str = Field("development", description="Runtime environment")
    debug: bool = Field(True, description="Debug mode")

    # Dictionaries configuration
    dictionaries_base_path: str = Field(
        "./data/dictionaries/databases",
        description="Base path for dictionary databases",
    )

    # Testing configuration
    testing: bool = Field(False, description="Test mode")
    test_database_url: str = Field(
        "sqlite:///./tests/test.db",
        description="Test database URL",
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
    )

    @property
    def is_development(self) -> bool:
        """Returns True if the environment is in development."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Returns True if the environment is in production."""
        return self.environment.lower() == "production"

    @property
    def is_testing(self) -> bool:
        """Returns True if the environment is in test."""
        return self.testing or self.environment.lower() == "testing"
