"""
Configuration du bot Scrabbot.

Expose un constructeur paresseux pour éviter l'initialisation
des variables d'environnement au moment de l'import (utile en tests).
"""

from .settings import Settings


def get_settings() -> Settings:
    """Retourne une instance de paramètres fraîchement initialisée."""
    return Settings()


__all__ = ["get_settings", "Settings"]
