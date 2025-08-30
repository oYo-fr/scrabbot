"""
Scrabbot bot configuration.

Exposes a lazy constructor to avoid initializing
environment variables at import time (useful in tests).
"""

from .settings import Settings


def get_settings() -> Settings:
    """Returns a freshly initialized settings instance."""
    return Settings()


__all__ = ["get_settings", "Settings"]
