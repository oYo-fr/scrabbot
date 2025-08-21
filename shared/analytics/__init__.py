"""
Dictionary analytics and statistics system for Scrabbot.

This package provides:
- Comprehensive dictionary statistics
- Word frequency analysis
- Scrabble strategy insights
- Performance analytics
"""

from .dictionary_analytics import DictionaryAnalytics, create_analytics_engine

__all__ = [
    'DictionaryAnalytics',
    'create_analytics_engine'
]
