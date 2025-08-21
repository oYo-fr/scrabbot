#!/usr/bin/env python3
"""
Data models for the Scrabbot multilingual dictionary system.

This module contains classes and data structures for managing:
- French and English dictionaries
- Word validation
- Definitions
- SQLite database interface
"""

import logging
import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LanguageEnum(Enum):
    """Enumeration of supported languages."""

    FRENCH = "fr"
    ENGLISH = "en"


@dataclass
class DictionaryWord:
    """
    Class representing a word in the dictionary.

    Attributes:
        word: The word (in French or English)
        definition: Definition of the word
        part_of_speech: Grammatical type (noun, verb, etc.)
        points: Scrabble points
        is_valid_scrabble: Whether the word is allowed in Scrabble
        length: Number of letters
        first_letter: First letter of the word
        last_letter: Last letter of the word
        language: Language of the word
        source: Dictionary source (ODS, SOWPODS, etc.)
        date_added: Date added to dictionary
    """

    word: str
    definition: str
    part_of_speech: Optional[str]
    points: int
    is_valid_scrabble: bool
    length: int
    first_letter: str
    last_letter: str
    language: LanguageEnum
    source: str
    date_added: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ValidationResult:
    """
    Result of word validation.

    Attributes:
        word: The validated word
        is_valid: Whether the word is valid
        definition: Definition of the word (if found)
        points: Scrabble points (if valid)
        language: Language of the word
        search_time_ms: Search time in milliseconds
    """

    word: str
    is_valid: bool
    definition: Optional[str] = None
    points: Optional[int] = None
    language: Optional[LanguageEnum] = None
    search_time_ms: Optional[float] = None


class DictionaryService:
    """
    Main service for multilingual dictionary management.

    This class handles:
    - SQLite database connections
    - Word validation
    - Definition retrieval
    - Performance statistics
    """

    def __init__(self, french_db_path: str, english_db_path: str):
        """
        Initialize the dictionary service.

        Args:
            french_db_path: Path to the French SQLite database
            english_db_path: Path to the English SQLite database
        """
        self.french_db_path = Path(french_db_path)
        self.english_db_path = Path(english_db_path)
        self._connection_cache = {}
        self._performance_stats = {
            "total_requests": 0,
            "total_time_ms": 0.0,
            "cache_requests": 0,
        }

        logger.info("Dictionary service initialized")
        logger.info(f"  French DB: {self.french_db_path}")
        logger.info(f"  English DB: {self.english_db_path}")

    def _get_connection(self, language: LanguageEnum) -> sqlite3.Connection:
        """
        Get a database connection for the specified language.

        Args:
            language: Dictionary language

        Returns:
            SQLite connection

        Raises:
            FileNotFoundError: If the database does not exist
            sqlite3.Error: In case of connection error
        """
        db_path = self.french_db_path if language == LanguageEnum.FRENCH else self.english_db_path

        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        if language not in self._connection_cache:
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row  # To access columns by name
                self._connection_cache[language] = conn
                logger.debug(f"Connection established to database {language.value}")
            except sqlite3.Error as e:
                logger.error(f"Connection error for database {language.value}: {e}")
                raise

        return self._connection_cache[language]

    def validate_word(self, word: str, language: LanguageEnum) -> ValidationResult:
        """
        Validate a word in the specified dictionary.

        Args:
            word: The word to validate
            language: Dictionary language

        Returns:
            Validation result with definition if found
        """
        start_time = time.time()
        normalized_word = word.upper().strip()

        try:
            conn = self._get_connection(language)

            # Query according to language
            if language == LanguageEnum.FRENCH:
                query = """
                SELECT mot as word, definition, points, valide_scrabble as is_valid_scrabble, categorie_grammaticale as part_of_speech
                FROM mots_fr
                WHERE mot = ? AND valide_scrabble = 1
                """
            else:
                query = """
                SELECT word, definition, points, scrabble_valid as is_valid_scrabble, part_of_speech
                FROM mots_en
                WHERE word = ? AND scrabble_valid = 1
                """

            cursor = conn.cursor()
            cursor.execute(query, (normalized_word,))
            result = cursor.fetchone()

            elapsed_ms = (time.time() - start_time) * 1000
            self._performance_stats["total_requests"] += 1
            self._performance_stats["total_time_ms"] += elapsed_ms

            if result:
                return ValidationResult(
                    word=normalized_word,
                    is_valid=True,
                    definition=result["definition"],
                    points=result["points"],
                    language=language,
                    search_time_ms=elapsed_ms,
                )
            else:
                return ValidationResult(
                    word=normalized_word,
                    is_valid=False,
                    language=language,
                    search_time_ms=elapsed_ms,
                )

        except Exception as e:
            logger.error(f"Error validating word '{word}' in {language.value}: {e}")
            return ValidationResult(
                word=normalized_word,
                is_valid=False,
                language=language,
                search_time_ms=(time.time() - start_time) * 1000,
            )

    def get_definition(self, word: str, language: LanguageEnum) -> Optional[str]:
        """
        Retrieve the definition of a word.

        Args:
            word: The word to get definition for
            language: Dictionary language

        Returns:
            Word definition or None if not found
        """
        result = self.validate_word(word, language)
        return result.definition if result.is_valid else None

    def search_words_by_criteria(
        self,
        language: LanguageEnum,
        length: Optional[int] = None,
        starts_with: Optional[str] = None,
        ends_with: Optional[str] = None,
        limit: int = 100,
    ) -> List[DictionaryWord]:
        """
        Search for words according to specific criteria.

        Args:
            language: Dictionary language
            length: Word length
            starts_with: Word prefix
            ends_with: Word suffix
            limit: Maximum number of results

        Returns:
            List of words matching the criteria
        """
        try:
            conn = self._get_connection(language)

            # Dynamic query construction
            conditions = []
            params = []

            if language == LanguageEnum.FRENCH:
                table = "mots_fr"
                word_col = "mot"
                length_col = "longueur"
                first_col = "premiere_lettre"
                last_col = "derniere_lettre"
                valid_col = "valide_scrabble"
            else:
                table = "mots_en"
                word_col = "word"
                length_col = "length"
                first_col = "first_letter"
                last_col = "last_letter"
                valid_col = "scrabble_valid"

            conditions.append(f"{valid_col} = 1")

            if length:
                conditions.append(f"{length_col} = ?")
                params.append(length)

            if starts_with:
                conditions.append(f"{first_col} = ?")
                params.append(starts_with.upper())

            if ends_with:
                conditions.append(f"{last_col} = ?")
                params.append(ends_with.upper())

            query = f"""
            SELECT * FROM {table}
            WHERE {' AND '.join(conditions)}
            ORDER BY {word_col}
            LIMIT ?
            """
            params.append(limit)

            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert to DictionaryWord objects
            words = []
            for row in results:
                if language == LanguageEnum.FRENCH:
                    word = DictionaryWord(
                        id=row["id"],
                        word=row["mot"],
                        definition=row["definition"],
                        part_of_speech=row["categorie_grammaticale"],
                        points=row["points"],
                        is_valid_scrabble=bool(row["valide_scrabble"]),
                        length=row["longueur"],
                        first_letter=row["premiere_lettre"],
                        last_letter=row["derniere_lettre"],
                        language=language,
                        source=row["source"],
                        date_added=row["date_ajout"],
                    )
                else:
                    word = DictionaryWord(
                        id=row["id"],
                        word=row["word"],
                        definition=row["definition"],
                        part_of_speech=row["part_of_speech"],
                        points=row["points"],
                        is_valid_scrabble=bool(row["scrabble_valid"]),
                        length=row["length"],
                        first_letter=row["first_letter"],
                        last_letter=row["last_letter"],
                        language=language,
                        source=row["source"],
                        date_added=row["date_added"],
                    )
                words.append(word)

            return words

        except Exception as e:
            logger.error(f"Error searching by criteria in {language.value}: {e}")
            return []

    def get_performance_statistics(self) -> Dict[str, float]:
        """
        Return the service performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        stats = self._performance_stats.copy()
        if stats["total_requests"] > 0:
            stats["average_time_ms"] = stats["total_time_ms"] / stats["total_requests"]
        else:
            stats["average_time_ms"] = 0.0

        return stats

    def close_connections(self):
        """Close all database connections."""
        for language, conn in self._connection_cache.items():
            try:
                conn.close()
                logger.debug(f"Connection closed for {language.value}")
            except Exception as e:
                logger.error(f"Error closing connection for {language.value}: {e}")

        self._connection_cache.clear()

    def __del__(self):
        """Destructor - automatically close connections."""
        self.close_connections()


# Utility class for constants
class DictionaryConstants:
    """Constants used by the dictionary system."""

    # Default paths
    DEFAULT_FRENCH_DB_PATH = "data/dictionaries/databases/french.db"
    DEFAULT_ENGLISH_DB_PATH = "data/dictionaries/databases/english.db"

    # Performance limits
    MAX_SEARCH_TIME_MS = 50.0
    MAX_DB_SIZE_MB = 100.0

    # Dictionary sources
    FRENCH_SOURCES = ["ODS", "Larousse", "Wiktionnaire"]
    ENGLISH_SOURCES = ["SOWPODS", "TWL", "Wiktionary"]

    # Grammatical categories
    FRENCH_CATEGORIES = [
        "nom",
        "verbe",
        "adjectif",
        "adverbe",
        "déterminant",
        "préposition",
        "conjonction",
        "interjection",
    ]
    ENGLISH_CATEGORIES = [
        "noun",
        "verb",
        "adjective",
        "adverb",
        "determiner",
        "preposition",
        "conjunction",
        "interjection",
    ]


def create_dictionary_service() -> DictionaryService:
    """
    Factory to create a dictionary service instance with default configuration.

    Returns:
        Configured dictionary service instance
    """
    return DictionaryService(
        french_db_path=DictionaryConstants.DEFAULT_FRENCH_DB_PATH,
        english_db_path=DictionaryConstants.DEFAULT_ENGLISH_DB_PATH,
    )
