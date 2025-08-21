"""
Intelligent caching system for the Scrabbot dictionary.

This package provides:
- LRU/LFU/TTL cache implementations
- Dictionary-specific cache management
- Performance optimization
"""

from .intelligent_cache import DictionaryCacheManager, IntelligentCache, create_cache_manager

__all__ = [
    "IntelligentCache",
    "DictionaryCacheManager",
    "create_cache_manager",
]
