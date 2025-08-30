#!/usr/bin/env python3
"""
Advanced search algorithms for the Scrabbot dictionary system.

This module implements:
- Trie (prefix tree) for ultra-fast prefix searches
- Pattern matching for Scrabble word finding
- Anagram solver
- Word suggestion system
"""

import logging

# Import configuration loader
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.append(str(Path(__file__).parent.parent / "models"))
from language_config import LanguageConfig, get_language_config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result of an advanced search operation."""

    words: List[str]
    search_time_ms: float
    total_matches: int
    algorithm_used: str


class TrieNode:
    """Node in the Trie data structure."""

    def __init__(self):
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end_word: bool = False
        self.word: Optional[str] = None
        self.scrabble_points: Optional[int] = None
        self.definition: Optional[str] = None


class AdvancedSearchEngine:
    """
    Advanced search engine for dictionary operations.

    Implements multiple search algorithms optimized for Scrabble gameplay:
    - Trie-based prefix search
    - Pattern matching with wildcards
    - Anagram solving
    - Word completion suggestions
    """

    def __init__(self):
        self._tries: Dict[str, TrieNode] = {}
        self._language_configs: Dict[str, LanguageConfig] = {}
        self._letter_frequency: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._anagram_index: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self._loaded_languages: Set[str] = set()

        logger.info("Advanced search engine initialized")

    def load_dictionary_into_trie(self, words_data: List[Dict], language_code: str):
        """
        Load dictionary data into the appropriate Trie structure.

        Args:
            words_data: List of word dictionaries with metadata
            language_code: Language code (e.g., 'fr', 'en', 'es')
        """
        start_time = time.time()

        # Load language configuration
        if language_code not in self._language_configs:
            self._language_configs[language_code] = get_language_config(language_code)

        # Initialize trie for this language if not exists
        if language_code not in self._tries:
            self._tries[language_code] = TrieNode()

        trie = self._tries[language_code]
        word_count = 0

        for word_data in words_data:
            word = word_data.get("word", "").upper()
            if not word:
                continue

            # Insert into Trie
            current = trie
            for letter in word:
                if letter not in current.children:
                    current.children[letter] = TrieNode()
                current = current.children[letter]

                # Update letter frequency
                self._letter_frequency[language_code][letter] += 1

            # Mark end of word and store metadata
            current.is_end_word = True
            current.word = word
            current.scrabble_points = word_data.get("points", 0)
            current.definition = word_data.get("definition", "")

            # Build anagram index
            sorted_letters = "".join(sorted(word))
            self._anagram_index[language_code][sorted_letters].append(word)

            word_count += 1

        self._loaded_languages.add(language_code)
        elapsed_time = (time.time() - start_time) * 1000

        config = self._language_configs[language_code]
        logger.info(f"Loaded {word_count} {config.language_name} words into Trie in {elapsed_time:.1f}ms")

    def prefix_search(self, prefix: str, language_code: str, max_results: int = 100) -> SearchResult:
        """
        Find all words starting with the given prefix.

        Args:
            prefix: Prefix to search for
            language_code: Language code (e.g., 'fr', 'en', 'es')
            max_results: Maximum number of results to return

        Returns:
            SearchResult with matching words
        """
        start_time = time.time()
        prefix = prefix.upper()

        if language_code not in self._tries:
            return SearchResult(
                words=[],
                search_time_ms=(time.time() - start_time) * 1000,
                total_matches=0,
                algorithm_used="trie_prefix_search",
            )

        trie = self._tries[language_code]

        # Navigate to prefix node
        current = trie
        for letter in prefix:
            if letter not in current.children:
                # No words with this prefix
                return SearchResult(
                    words=[],
                    search_time_ms=(time.time() - start_time) * 1000,
                    total_matches=0,
                    algorithm_used="trie_prefix_search",
                )
            current = current.children[letter]

        # Collect all words from this node
        words = []
        self._collect_words(current, words, max_results)

        elapsed_ms = (time.time() - start_time) * 1000

        return SearchResult(
            words=words,
            search_time_ms=elapsed_ms,
            total_matches=len(words),
            algorithm_used="trie_prefix_search",
        )

    def _collect_words(self, node: TrieNode, words: List[str], max_results: int):
        """Recursively collect words from a Trie node."""
        if len(words) >= max_results:
            return

        if node.is_end_word and node.word:
            words.append(node.word)

        for child in node.children.values():
            self._collect_words(child, words, max_results)

    def pattern_search(self, pattern: str, language_code: str, max_results: int = 100) -> SearchResult:
        """
        Find words matching a pattern with wildcards.

        Pattern format:
        - Letters: exact match
        - '?': any single letter
        - '*': any sequence of letters

        Args:
            pattern: Pattern to match (e.g., "C?T", "S*E")
            language_code: Language code (e.g., 'fr', 'en', 'es')
            max_results: Maximum results

        Returns:
            SearchResult with matching words
        """
        start_time = time.time()
        pattern = pattern.upper()

        if language_code not in self._tries:
            return SearchResult(
                words=[],
                search_time_ms=(time.time() - start_time) * 1000,
                total_matches=0,
                algorithm_used="pattern_matching",
            )

        trie = self._tries[language_code]

        words = []
        self._pattern_search_recursive(trie, pattern, 0, "", words, max_results)

        elapsed_ms = (time.time() - start_time) * 1000

        return SearchResult(
            words=words,
            search_time_ms=elapsed_ms,
            total_matches=len(words),
            algorithm_used="pattern_matching",
        )

    def _pattern_search_recursive(
        self,
        node: TrieNode,
        pattern: str,
        pattern_idx: int,
        current_word: str,
        results: List[str],
        max_results: int,
    ):
        """Recursive pattern matching helper."""
        if len(results) >= max_results:
            return

        if pattern_idx == len(pattern):
            if node.is_end_word and node.word:
                results.append(node.word)
            return

        char = pattern[pattern_idx]

        if char == "?":
            # Any single letter
            for letter, child in node.children.items():
                self._pattern_search_recursive(
                    child,
                    pattern,
                    pattern_idx + 1,
                    current_word + letter,
                    results,
                    max_results,
                )
        elif char == "*":
            # Any sequence of letters (including empty)
            # Skip the * and try matching the rest
            self._pattern_search_recursive(
                node,
                pattern,
                pattern_idx + 1,
                current_word,
                results,
                max_results,
            )
            # Or consume one letter and try again
            for letter, child in node.children.items():
                self._pattern_search_recursive(
                    child,
                    pattern,
                    pattern_idx,
                    current_word + letter,
                    results,
                    max_results,
                )
        else:
            # Exact letter match
            if char in node.children:
                self._pattern_search_recursive(
                    node.children[char],
                    pattern,
                    pattern_idx + 1,
                    current_word + char,
                    results,
                    max_results,
                )

    def find_anagrams(self, letters: str, language_code: str, max_results: int = 100) -> SearchResult:
        """
        Find all anagrams (and sub-anagrams) from the given letters.

        Args:
            letters: Available letters (e.g., "SCRABBLE")
            language_code: Language code (e.g., 'fr', 'en', 'es')
            max_results: Maximum results

        Returns:
            SearchResult with anagram words
        """
        start_time = time.time()
        letters = letters.upper()
        letter_count = defaultdict(int)

        # Count available letters
        for letter in letters:
            letter_count[letter] += 1

        words = []

        # Check all anagram combinations
        for sorted_word, word_list in self._anagram_index[language_code].items():
            if self._can_form_word(sorted_word, letter_count):
                words.extend(word_list)
                if len(words) >= max_results:
                    words = words[:max_results]
                    break

        elapsed_ms = (time.time() - start_time) * 1000

        return SearchResult(
            words=words,
            search_time_ms=elapsed_ms,
            total_matches=len(words),
            algorithm_used="anagram_solver",
        )

    def _can_form_word(self, sorted_word: str, available_letters: Dict[str, int]) -> bool:
        """Check if a word can be formed from available letters."""
        word_letters = defaultdict(int)
        for letter in sorted_word:
            word_letters[letter] += 1

        for letter, needed in word_letters.items():
            if available_letters[letter] < needed:
                return False

        return True

    def suggest_words(self, partial_word: str, language_code: str, max_suggestions: int = 10) -> SearchResult:
        """
        Suggest word completions for a partial word.

        Args:
            partial_word: Partially typed word
            language_code: Language code (e.g., 'fr', 'en', 'es')
            max_suggestions: Maximum suggestions

        Returns:
            SearchResult with suggested completions
        """
        # Use prefix search for suggestions
        result = self.prefix_search(partial_word, language_code, max_suggestions)
        result.algorithm_used = "word_suggestion"
        return result

    def find_words_by_length(self, length: int, language_code: str, max_results: int = 100) -> SearchResult:
        """
        Find all words of a specific length.

        Args:
            length: Word length
            language_code: Language code (e.g., 'fr', 'en', 'es')
            max_results: Maximum results

        Returns:
            SearchResult with words of specified length
        """
        pattern = "?" * length  # Pattern with length wildcards
        result = self.pattern_search(pattern, language_code, max_results)
        result.algorithm_used = "length_search"
        return result

    def get_search_statistics(self, language_code: str) -> Dict[str, Any]:
        """
        Get statistics about the search engine for a language.

        Args:
            language_code: Language code (e.g., 'fr', 'en', 'es')

        Returns:
            Dictionary with statistics
        """
        if language_code not in self._loaded_languages:
            return {"error": f"Language {language_code} not loaded"}

        trie = self._tries[language_code]
        config = self._language_configs[language_code]

        stats = {
            "language_code": language_code,
            "language_name": config.language_name,
            "total_words": self._count_words(trie),
            "letter_frequency": dict(self._letter_frequency[language_code]),
            "anagram_groups": len(self._anagram_index[language_code]),
            "memory_loaded": language_code in self._loaded_languages,
        }

        return stats

    def _count_words(self, node: TrieNode) -> int:
        """Count total words in a Trie."""
        count = 1 if node.is_end_word else 0
        for child in node.children.values():
            count += self._count_words(child)
        return count


# Factory function for easy instantiation
def create_search_engine() -> AdvancedSearchEngine:
    """
    Create and return a new AdvancedSearchEngine instance.

    Returns:
        Configured search engine
    """
    return AdvancedSearchEngine()
