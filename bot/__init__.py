"""
Scrabbot - Bot de Scrabble Intelligent

Un bot Telegram de Scrabble avec intelligence artificielle.
"""

__version__ = "0.1.0"
__author__ = "Yoann Diguet"
__email__ = "yoann.diguet@example.com"

from .config import settings
from .bot import ScrabbotBot

__all__ = ["ScrabbotBot", "settings"]
