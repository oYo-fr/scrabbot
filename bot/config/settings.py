"""
Configuration du bot Scrabbot avec Pydantic.
"""

from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration du bot Scrabbot."""

    # Configuration du bot Telegram
    telegram_bot_token: str = Field("dev-token", description="Token du bot Telegram")
    telegram_webhook_url: Optional[str] = Field(None, description="URL du webhook Telegram")

    # Configuration de la base de données
    database_url: str = Field("sqlite:///./data/scrabbot.db", description="URL de la base de données")

    # Configuration Redis (optionnel)
    redis_url: Optional[str] = Field(None, description="URL Redis")

    # Configuration de l'API
    api_host: str = Field("0.0.0.0", description="Adresse d'écoute de l'API")
    api_port: int = Field(8000, description="Port d'écoute de l'API")
    api_secret_key: str = Field("dev-secret-key", description="Clé secrète de l'API")

    # Godot
    godot_executable_path: Optional[str] = Field(None, description="Chemin vers l'exécutable Godot")
    godot_project_path: str = Field("./godot", description="Chemin vers le projet Godot")
    godot_web_url: Optional[str] = Field(None, description="URL de l'application web Godot")

    # Configuration des logs
    log_level: str = Field("INFO", description="Niveau de log")
    log_file: str = Field("logs/scrabbot.log", description="Fichier de log")

    # Configuration de l'environnement
    environment: str = Field("development", description="Environnement d'exécution")
    debug: bool = Field(True, description="Mode debug")

    # Configuration des dictionnaires
    dictionary_fr_path: str = Field(
        "./data/dictionnaires/databases/french_extended.db",
        description="Chemin du dictionnaire français",
    )
    dictionary_en_path: str = Field(
        "./data/dictionnaires/databases/english_extended.db",
        description="Chemin du dictionnaire anglais",
    )

    # Configuration des tests
    testing: bool = Field(False, description="Mode test")
    test_database_url: str = Field(
        "sqlite:///./tests/test.db",
        description="URL de la base de données de test",
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",
    )

    @property
    def is_development(self) -> bool:
        """Retourne True si l'environnement est en développement."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Retourne True si l'environnement est en production."""
        return self.environment.lower() == "production"

    @property
    def is_testing(self) -> bool:
        """Retourne True si l'environnement est en test."""
        return self.testing or self.environment.lower() == "testing"
