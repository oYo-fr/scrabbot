"""
Advanced algorithms for the Scrabbot dictionary system.

This package contains:
- Trie-based search algorithms
- Word suggestion and spell-checking
- Scrabble strategy optimization
"""

from .trie_search import AdvancedSearchEngine, create_search_engine
from .word_suggestions import WordSuggestionEngine, create_suggestion_engine
from .scrabble_strategy import StrategyEngine, ScrabbleBoard, create_strategy_engine

__all__ = [
    'AdvancedSearchEngine',
    'WordSuggestionEngine', 
    'StrategyEngine',
    'ScrabbleBoard',
    'create_search_engine',
    'create_suggestion_engine',
    'create_strategy_engine'
]
