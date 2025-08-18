"""
Configuration du bot Scrabbot avec Pydantic.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration du bot Scrabbot."""
    
    # Configuration du bot Telegram
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    
    # Configuration de la base de données
    database_url: str = Field("sqlite:///./data/scrabbot.db", env="DATABASE_URL")
    
    # Configuration Redis (optionnel)
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # Configuration de l'API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_secret_key: str = Field(..., env="API_SECRET_KEY")
    
    # Configuration des logs
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/scrabbot.log", env="LOG_FILE")
    
    # Configuration de l'environnement
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    
    # Configuration des dictionnaires
    dictionary_fr_path: str = Field("./data/dictionaries/french.db", env="DICTIONARY_FR_PATH")
    dictionary_en_path: str = Field("./data/dictionaries/english.db", env="DICTIONARY_EN_PATH")
    
    # Configuration des tests
    testing: bool = Field(False, env="TESTING")
    test_database_url: str = Field("sqlite:///./tests/test.db", env="TEST_DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
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
