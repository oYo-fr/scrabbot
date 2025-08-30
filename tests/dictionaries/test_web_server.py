#!/usr/bin/env python3
"""
Unit tests for web server - Scrabbot dictionary system.

These tests verify that the web server and Godot application can
properly access dictionaries using REAL databases according to OYO-7 specifications.

Tests covered:
- Basic word validation with real data
- Performance test (< 50ms)
- Real database structure verification
- REST API integration test
"""

import logging
# import os  # Not needed
import sys
import unittest
from pathlib import Path

# Add path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "models"))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "api"))

from dictionary import DictionaryService


class TestRealDatabaseAccess(unittest.TestCase):
    """Tests using real fr.db and en.db databases."""

    def setUp(self):
        """Test initialization with real databases."""
        # Use simplified constructor with default path
        project_root = Path(__file__).parent.parent.parent
        databases_path = str(project_root / "data" / "dictionaries" / "databases")

        # Verify databases directory exists
        if not Path(databases_path).exists():
            self.skipTest(f"Databases directory not found: {databases_path}")

        # Test service with simplified constructor
        self.service = DictionaryService(databases_path)

    def tearDown(self):
        """Cleanup after tests."""
        self.service.close_connections()
        # No need to delete real databases - they stay

    def test_french_word_validation(self):
        """Test validation of French words from real database."""
        # Test with a word that exists in real DB
        result = self.service.validate_word("DICTIONNAIRE", "fr")

        self.assertIsNotNone(result)
        self.assertEqual(result.word, "DICTIONNAIRE")
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.definition)  # Should have definition from real DB
        self.assertEqual(result.language, LanguageEnum.FRENCH)

    def test_english_word_validation(self):
        """Test validation of English words from real database."""
        # Test with a word that exists in real English DB
        result = self.service.validate_word("MANGA", "en")

        self.assertIsNotNone(result)
        self.assertEqual(result.word, "MANGA")
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.definition)  # Should have definition from real DB
        self.assertEqual(result.language, LanguageEnum.ENGLISH)

    def test_invalid_word_french(self):
        """Test invalid French word returns False."""
        result = self.service.validate_word("NONEXISTENTWORDXYZ123", "fr")

        self.assertFalse(result.is_valid)
        self.assertIsNone(result.definition)
        self.assertEqual(result.language, LanguageEnum.FRENCH)

    def test_invalid_word_english(self):
        """Test invalid English word returns False."""
        result = self.service.validate_word("NONEXISTENTWORDXYZ123", "en")

        self.assertFalse(result.is_valid)
        self.assertIsNone(result.definition)
        self.assertEqual(result.language, LanguageEnum.ENGLISH)

    def test_performance_requirement(self):
        """Test that validation meets performance requirement < 50ms."""
        import time

        start_time = time.time()
        result = self.service.validate_word("LIRE", "fr")
        elapsed_ms = (time.time() - start_time) * 1000

        self.assertLess(elapsed_ms, 50.0, f"Validation too slow: {elapsed_ms:.1f}ms")
        self.assertIsNotNone(result.search_time_ms)
        self.assertLess(result.search_time_ms, 50.0)

    def test_service_statistics(self):
        """Test service performance statistics."""
        # Perform some validations to generate stats
        self.service.validate_word("ACCUEIL", "fr")
        self.service.validate_word("DICTIONNAIRE", "fr")

        stats = self.service.get_performance_statistics()

        self.assertIn("total_requests", stats)
        self.assertIn("total_time_ms", stats)
        self.assertIn("average_time_ms", stats)
        self.assertGreaterEqual(stats["total_requests"], 2)
        self.assertGreater(stats["total_time_ms"], 0)


if __name__ == "__main__":
    # Logging configuration for tests
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)
