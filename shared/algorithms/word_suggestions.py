#!/usr/bin/env python3
"""
Word suggestion and spell-checking system for Scrabbot.

This module implements:
- Levenshtein distance for spell checking
- Word suggestions based on letter proximity
- Scrabble-specific word recommendations
- Smart auto-completion
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SuggestionResult:
    """Result of a word suggestion operation."""

    suggestions: List[Tuple[str, float]]  # (word, confidence_score)
    algorithm_used: str
    search_time_ms: float
    query: str


class WordSuggestionEngine:
    """
    Advanced word suggestion engine for Scrabble gameplay.

    Features:
    - Spell checking with edit distance
    - Letter proximity suggestions
    - Scrabble tile-aware suggestions
    - Context-aware recommendations
    """

    def __init__(self):
        self.word_sets: Dict[str, Set[str]] = {"fr": set(), "en": set()}
        self.letter_frequency: Dict[str, Dict[str, float]] = {
            "fr": {},
            "en": {},
        }
        self.common_words: Dict[str, List[str]] = {"fr": [], "en": []}

        # QWERTY keyboard layout for proximity suggestions
        self.keyboard_layout = {
            "Q": ["W", "A"],
            "W": ["Q", "E", "A", "S"],
            "E": ["W", "R", "S", "D"],
            "R": ["E", "T", "D", "F"],
            "T": ["R", "Y", "F", "G"],
            "Y": ["T", "U", "G", "H"],
            "U": ["Y", "I", "H", "J"],
            "I": ["U", "O", "J", "K"],
            "O": ["I", "P", "K", "L"],
            "P": ["O", "L"],
            "A": ["Q", "W", "S", "Z"],
            "S": ["A", "W", "E", "D", "Z", "X"],
            "D": ["S", "E", "R", "F", "X", "C"],
            "F": ["D", "R", "T", "G", "C", "V"],
            "G": ["F", "T", "Y", "H", "V", "B"],
            "H": ["G", "Y", "U", "J", "B", "N"],
            "J": ["H", "U", "I", "K", "N", "M"],
            "K": ["J", "I", "O", "L", "M"],
            "L": ["K", "O", "P", "M"],
            "Z": ["A", "S", "X"],
            "X": ["Z", "S", "D", "C"],
            "C": ["X", "D", "F", "V"],
            "V": ["C", "F", "G", "B"],
            "B": ["V", "G", "H", "N"],
            "N": ["B", "H", "J", "M"],
            "M": ["N", "J", "K", "L"],
        }

        # Scrabble letter scores for weighted suggestions
        self.scrabble_scores = {
            # French scores
            "fr": {
                "A": 1,
                "B": 3,
                "C": 3,
                "D": 2,
                "E": 1,
                "F": 4,
                "G": 2,
                "H": 4,
                "I": 1,
                "J": 8,
                "K": 10,
                "L": 1,
                "M": 2,
                "N": 1,
                "O": 1,
                "P": 3,
                "Q": 8,
                "R": 1,
                "S": 1,
                "T": 1,
                "U": 1,
                "V": 4,
                "W": 10,
                "X": 10,
                "Y": 10,
                "Z": 10,
            },
            # English scores
            "en": {
                "A": 1,
                "B": 3,
                "C": 3,
                "D": 2,
                "E": 1,
                "F": 4,
                "G": 2,
                "H": 4,
                "I": 1,
                "J": 8,
                "K": 5,
                "L": 1,
                "M": 3,
                "N": 1,
                "O": 1,
                "P": 3,
                "Q": 10,
                "R": 1,
                "S": 1,
                "T": 1,
                "U": 1,
                "V": 4,
                "W": 4,
                "X": 8,
                "Y": 4,
                "Z": 10,
            },
        }

        logger.info("Word suggestion engine initialized")

    def load_word_list(self, words: List[str], language: str):
        """
        Load word list for suggestions.

        Args:
            words: List of valid words
            language: Language code ('fr' or 'en')
        """
        start_time = time.time()

        self.word_sets[language] = set(word.upper() for word in words)

        # Calculate letter frequency
        letter_count = defaultdict(int)
        total_letters = 0

        for word in words:
            for letter in word.upper():
                letter_count[letter] += 1
                total_letters += 1

        # Convert to frequency percentages
        self.letter_frequency[language] = {letter: count / total_letters for letter, count in letter_count.items()}

        # Identify common words (frequent and short)
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word.upper()] += 1

        self.common_words[language] = sorted(
            [word for word in words if len(word) <= 6],
            key=lambda w: (-word_freq[w.upper()], len(w)),
        )[
            :1000
        ]  # Top 1000 common words

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Loaded {len(words)} {language} words for suggestions in {elapsed_ms:.1f}ms")

    def suggest_corrections(
        self,
        word: str,
        language: str,
        max_suggestions: int = 10,
        max_distance: int = 2,
    ) -> SuggestionResult:
        """
        Suggest spelling corrections for a misspelled word.

        Args:
            word: Possibly misspelled word
            language: Language code
            max_suggestions: Maximum number of suggestions
            max_distance: Maximum edit distance to consider

        Returns:
            SuggestionResult with corrections and confidence scores
        """
        start_time = time.time()
        word = word.upper()
        suggestions = []

        if word in self.word_sets[language]:
            # Word is already correct
            suggestions = [(word, 1.0)]
        else:
            # Find similar words using edit distance
            for candidate in self.word_sets[language]:
                distance = self._levenshtein_distance(word, candidate)
                if distance <= max_distance:
                    confidence = self._calculate_confidence(word, candidate, distance, language)
                    suggestions.append((candidate, confidence))

        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = suggestions[:max_suggestions]

        elapsed_ms = (time.time() - start_time) * 1000

        return SuggestionResult(
            suggestions=suggestions,
            algorithm_used="levenshtein_spell_check",
            search_time_ms=elapsed_ms,
            query=word,
        )

    def suggest_by_letters(
        self,
        available_letters: str,
        language: str,
        min_length: int = 3,
        max_suggestions: int = 20,
    ) -> SuggestionResult:
        """
        Suggest words that can be formed from available letters.

        Args:
            available_letters: Available letter tiles
            language: Language code
            min_length: Minimum word length
            max_suggestions: Maximum suggestions

        Returns:
            SuggestionResult with possible words
        """
        start_time = time.time()
        available_letters = available_letters.upper()
        letter_count = defaultdict(int)

        # Count available letters
        for letter in available_letters:
            letter_count[letter] += 1

        suggestions = []

        for word in self.word_sets[language]:
            if len(word) < min_length:
                continue

            if self._can_form_word_from_letters(word, letter_count):
                # Calculate score based on word value and likelihood
                scrabble_score = sum(self.scrabble_scores[language].get(letter, 0) for letter in word)
                length_bonus = len(word) * 2  # Longer words get bonus
                frequency_score = self.letter_frequency[language].get(word[0], 0.01) * 10

                total_score = scrabble_score + length_bonus + frequency_score
                suggestions.append((word, total_score))

        # Sort by score and limit results
        suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = suggestions[:max_suggestions]

        elapsed_ms = (time.time() - start_time) * 1000

        return SuggestionResult(
            suggestions=suggestions,
            algorithm_used="letter_combination_analysis",
            search_time_ms=elapsed_ms,
            query=available_letters,
        )

    def suggest_by_pattern(self, pattern: str, language: str, max_suggestions: int = 15) -> SuggestionResult:
        """
        Suggest words matching a pattern with known letters.

        Args:
            pattern: Pattern with known letters and wildcards (? for unknown)
            language: Language code
            max_suggestions: Maximum suggestions

        Returns:
            SuggestionResult with matching words
        """
        start_time = time.time()
        pattern = pattern.upper()
        suggestions = []

        for word in self.word_sets[language]:
            if len(word) != len(pattern):
                continue

            if self._matches_pattern(word, pattern):
                # Score based on common letters and word frequency
                common_score = self._calculate_pattern_score(word, language)
                suggestions.append((word, common_score))

        # Sort by score and limit results
        suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = suggestions[:max_suggestions]

        elapsed_ms = (time.time() - start_time) * 1000

        return SuggestionResult(
            suggestions=suggestions,
            algorithm_used="pattern_matching",
            search_time_ms=elapsed_ms,
            query=pattern,
        )

    def suggest_extensions(self, partial_word: str, language: str, max_suggestions: int = 10) -> SuggestionResult:
        """
        Suggest word completions for a partial word.

        Args:
            partial_word: Beginning of a word
            language: Language code
            max_suggestions: Maximum suggestions

        Returns:
            SuggestionResult with completions
        """
        start_time = time.time()
        partial_word = partial_word.upper()
        suggestions = []

        for word in self.word_sets[language]:
            if word.startswith(partial_word) and len(word) > len(partial_word):
                # Score based on word length and common suffixes
                completion_score = self._calculate_completion_score(word, partial_word, language)
                suggestions.append((word, completion_score))

        # Sort by score and limit results
        suggestions.sort(key=lambda x: x[1], reverse=True)
        suggestions = suggestions[:max_suggestions]

        elapsed_ms = (time.time() - start_time) * 1000

        return SuggestionResult(
            suggestions=suggestions,
            algorithm_used="word_completion",
            search_time_ms=elapsed_ms,
            query=partial_word,
        )

    def suggest_high_score_words(self, available_letters: str, language: str, max_suggestions: int = 10) -> SuggestionResult:
        """
        Suggest highest scoring words from available letters.

        Args:
            available_letters: Available letter tiles
            language: Language code
            max_suggestions: Maximum suggestions

        Returns:
            SuggestionResult with high-scoring words
        """
        result = self.suggest_by_letters(available_letters, language, max_suggestions=max_suggestions * 3)

        # Re-sort purely by Scrabble score
        high_score_suggestions = []
        for word, _ in result.suggestions:
            scrabble_score = sum(self.scrabble_scores[language].get(letter, 0) for letter in word)
            high_score_suggestions.append((word, scrabble_score))

        high_score_suggestions.sort(key=lambda x: x[1], reverse=True)
        high_score_suggestions = high_score_suggestions[:max_suggestions]

        result.suggestions = high_score_suggestions
        result.algorithm_used = "high_score_optimization"

        return result

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein (edit) distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    def _calculate_confidence(self, original: str, candidate: str, distance: int, language: str) -> float:
        """Calculate confidence score for a spelling suggestion."""
        # Base confidence decreases with edit distance
        base_confidence = 1.0 - (distance * 0.3)

        # Bonus for keyboard proximity
        proximity_bonus = self._calculate_keyboard_proximity(original, candidate) * 0.2

        # Bonus for common words
        common_bonus = 0.1 if candidate in self.common_words[language][:100] else 0.0

        # Length similarity bonus
        length_diff = abs(len(original) - len(candidate))
        length_bonus = 0.1 if length_diff <= 1 else 0.0

        return min(
            1.0,
            base_confidence + proximity_bonus + common_bonus + length_bonus,
        )

    def _calculate_keyboard_proximity(self, word1: str, word2: str) -> float:
        """Calculate keyboard proximity score for typo detection."""
        if len(word1) != len(word2):
            return 0.0

        proximity_score = 0.0
        for i, (c1, c2) in enumerate(zip(word1, word2)):
            if c1 == c2:
                proximity_score += 1.0
            elif c2 in self.keyboard_layout.get(c1, []):
                proximity_score += 0.7  # Close keys on keyboard

        return proximity_score / len(word1)

    def _can_form_word_from_letters(self, word: str, available_letters: Dict[str, int]) -> bool:
        """Check if a word can be formed from available letters."""
        word_letters = defaultdict(int)
        for letter in word:
            word_letters[letter] += 1

        for letter, needed in word_letters.items():
            if available_letters[letter] < needed:
                return False

        return True

    def _matches_pattern(self, word: str, pattern: str) -> bool:
        """Check if a word matches a pattern with wildcards."""
        if len(word) != len(pattern):
            return False

        for w_char, p_char in zip(word, pattern):
            if p_char != "?" and p_char != w_char:
                return False

        return True

    def _calculate_pattern_score(self, word: str, language: str) -> float:
        """Calculate score for pattern-matched words."""
        # Base score from letter frequency
        frequency_score = sum(self.letter_frequency[language].get(letter, 0.01) for letter in word)

        # Bonus for common words
        common_bonus = 2.0 if word in self.common_words[language][:200] else 0.0

        # Length bonus (longer words are often more valuable)
        length_bonus = len(word) * 0.5

        return frequency_score + common_bonus + length_bonus

    def _calculate_completion_score(self, word: str, partial: str, language: str) -> float:
        """Calculate score for word completions."""
        # Shorter completions are generally better
        completion_length = len(word) - len(partial)
        length_score = 10.0 / (completion_length + 1)

        # Common word bonus
        common_bonus = 3.0 if word in self.common_words[language][:300] else 0.0

        # Frequency of completion suffix
        suffix = word[len(partial) :]
        suffix_score = sum(self.letter_frequency[language].get(letter, 0.01) for letter in suffix)

        return length_score + common_bonus + suffix_score

    def get_statistics(self) -> Dict[str, Any]:
        """Get suggestion engine statistics."""
        return {
            "loaded_languages": list(self.word_sets.keys()),
            "french_words": len(self.word_sets["fr"]),
            "english_words": len(self.word_sets["en"]),
            "common_words_tracked": {lang: len(words) for lang, words in self.common_words.items()},
            "letter_frequencies_calculated": {lang: len(freq) for lang, freq in self.letter_frequency.items()},
        }


# Factory function
def create_suggestion_engine() -> WordSuggestionEngine:
    """Create and return a new word suggestion engine."""
    return WordSuggestionEngine()
