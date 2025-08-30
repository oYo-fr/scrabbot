"""
Scrabbot - Intelligent Scrabble Bot

A Telegram Scrabble bot with artificial intelligence.
"""

__version__ = "0.1.0"
__author__ = "Yoann Diguet"
__email__ = "yoann.diguet@example.com"

from .bot import ScrabbotBot
from .config import get_settings

__all__ = ["ScrabbotBot", "get_settings"]
