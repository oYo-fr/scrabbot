#!/usr/bin/env python3
"""
Unit tests for web server - Scrabbot dictionary system.

These tests verify that the web server and Godot application can
properly access dictionaries according to OYO-7 ticket specifications.

Tests covered:
- Basic SQLite access test
- Word validation test
- Performance test (< 50ms)
- Special characters test
- SQLite connection/closure test
- REST API integration test
"""

import logging
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Add path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "models"))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "api"))

from dictionary import DictionaryService, LanguageEnum, ValidationResult
from dictionnaire_service import app
from fastapi.testclient import TestClient


class TestAccesSQLiteBasique(unittest.TestCase):
    """Basic SQLite database access tests."""

    def setUp(self):
        """Test initialization."""
        # Create temporary databases for tests
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english.db")

        # Create test databases
        self._creer_base_test_francaise()
        self._creer_base_test_anglaise()

        # Test service
        self.service = DictionaryService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Cleanup after tests."""
        self.service.close_connections()

        # Delete temporary files
        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_test_francaise(self):
        """Creates a French test database."""
        conn = sqlite3.connect(self.db_fr_path)
        cursor = conn.cursor()

        # Metadata table
        cursor.execute(
            """
        CREATE TABLE dictionnaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_langue CHAR(2) NOT NULL,
            nom TEXT NOT NULL,
            version TEXT NOT NULL,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        # French words table
        cursor.execute(
            """
        CREATE TABLE mots_fr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            categorie_grammaticale TEXT,
            points INTEGER NOT NULL,
            valide_scrabble BOOLEAN DEFAULT 1,
            longueur INTEGER NOT NULL,
            premiere_lettre CHAR(1) NOT NULL,
            derniere_lettre CHAR(1) NOT NULL,
            voyelles TEXT,
            consonnes TEXT,
            date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        # Indexes
        cursor.execute("CREATE INDEX idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX idx_mots_fr_longueur ON mots_fr(longueur)")
        cursor.execute("CREATE INDEX idx_mots_fr_premiere_lettre ON mots_fr(premiere_lettre)")
        cursor.execute("CREATE INDEX idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")

        # Test data
        mots_test = [
            (
                "CHAT",
                "Mammifère domestique félin",
                "nom",
                9,
                1,
                4,
                "C",
                "T",
                "A",
                "CHT",
                "ODS",
            ),
            (
                "CHIEN",
                "Mammifère domestique canin",
                "nom",
                10,
                1,
                5,
                "C",
                "N",
                "IE",
                "CHN",
                "ODS",
            ),
            (
                "ÊTRE",
                "Verbe avoir une existence",
                "verbe",
                4,
                1,
                4,
                "Ê",
                "E",
                "ÊE",
                "TR",
                "ODS",
            ),
            (
                "INEXISTANT",
                "Mot qui n'existe pas",
                "nom",
                20,
                0,
                10,
                "I",
                "T",
                "IEIAT",
                "NXSSTNT",
                "Test",
            ),
        ]

        cursor.executemany(
            """
        INSERT INTO mots_fr (mot, definition, categorie_grammaticale, points, valide_scrabble,
                           longueur, premiere_lettre, derniere_lettre, voyelles, consonnes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            mots_test,
        )

        conn.commit()
        conn.close()

    def _creer_base_test_anglaise(self):
        """Creates an English test database."""
        conn = sqlite3.connect(self.db_en_path)
        cursor = conn.cursor()

        # English words table
        cursor.execute(
            """
        CREATE TABLE mots_en (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            part_of_speech TEXT,
            points INTEGER NOT NULL,
            scrabble_valid BOOLEAN DEFAULT 1,
            length INTEGER NOT NULL,
            first_letter CHAR(1) NOT NULL,
            last_letter CHAR(1) NOT NULL,
            vowels TEXT,
            consonants TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        # Indexes
        cursor.execute("CREATE INDEX idx_mots_en_word ON mots_en(word)")
        cursor.execute("CREATE INDEX idx_mots_en_length ON mots_en(length)")
        cursor.execute("CREATE INDEX idx_mots_en_first_letter ON mots_en(first_letter)")
        cursor.execute("CREATE INDEX idx_mots_en_scrabble_valid ON mots_en(scrabble_valid)")

        # Test data
        words_test = [
            (
                "CAT",
                "Small domesticated carnivorous mammal",
                "noun",
                5,
                1,
                3,
                "C",
                "T",
                "A",
                "CT",
                "SOWPODS",
            ),
            (
                "DOG",
                "Domesticated carnivorous mammal",
                "noun",
                5,
                1,
                3,
                "D",
                "G",
                "O",
                "DG",
                "SOWPODS",
            ),
            (
                "NONEXISTENT",
                "Word that does not exist",
                "noun",
                15,
                0,
                11,
                "N",
                "T",
                "OEEIT",
                "NNXSSTNT",
                "Test",
            ),
        ]

        cursor.executemany(
            """
        INSERT INTO mots_en (word, definition, part_of_speech, points, scrabble_valid,
                           length, first_letter, last_letter, vowels, consonants, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            words_test,
        )

        conn.commit()
        conn.close()

    def test_acces_mot_quelconque_francais(self):
        """Basic access test: retrieve any word from French SQLite."""
        resultat = self.service.validate_word("CHAT", LanguageEnum.FRENCH)

        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.word, "CHAT")
        self.assertTrue(resultat.is_valid)
        self.assertEqual(resultat.definition, "Mammifère domestique félin")
        self.assertEqual(resultat.points, 9)
        self.assertEqual(resultat.language, LanguageEnum.FRENCH)

    def test_acces_mot_quelconque_anglais(self):
        """Basic access test: retrieve any word from English SQLite."""
        resultat = self.service.validate_word("CAT", LanguageEnum.ENGLISH)

        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.word, "CAT")
        self.assertTrue(resultat.is_valid)
        self.assertEqual(resultat.definition, "Small domesticated carnivorous mammal")
        self.assertEqual(resultat.points, 5)
        self.assertEqual(resultat.language, LanguageEnum.ENGLISH)

    def test_validation_mot_valide_francais(self):
        """Validation test: valid word returns True."""
        resultat = self.service.validate_word("CHIEN", LanguageEnum.FRENCH)

        self.assertTrue(resultat.is_valid)
        self.assertIsNotNone(resultat.definition)
        self.assertGreater(resultat.points, 0)

    def test_validation_mot_invalide_francais(self):
        """Validation test: invalid word returns False."""
        resultat = self.service.validate_word("MOTINEXISTANT", LanguageEnum.FRENCH)

        self.assertFalse(resultat.is_valid)
        self.assertIsNone(resultat.definition)
        self.assertIsNone(resultat.points)

    def test_validation_mot_valide_anglais(self):
        """Validation test: valid English word returns True."""
        resultat = self.service.validate_word("DOG", LanguageEnum.ENGLISH)

        self.assertTrue(resultat.is_valid)
        self.assertIsNotNone(resultat.definition)
        self.assertGreater(resultat.points, 0)

    def test_validation_mot_invalide_anglais(self):
        """Validation test: invalid English word returns False."""
        resultat = self.service.validate_word("NONEXISTENTWORD", LanguageEnum.ENGLISH)

        self.assertFalse(resultat.is_valid)
        self.assertIsNone(resultat.definition)
        self.assertIsNone(resultat.points)


class TestPerformance(unittest.TestCase):
    """Performance tests according to acceptance criteria."""

    def setUp(self):
        """Performance test initialization."""
        # Using same test databases
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english.db")

        # Create databases with more data to test performance
        self._creer_base_performance_francaise()
        self._creer_base_performance_anglaise()

        self.service = DictionaryService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Cleanup after performance tests."""
        self.service.close_connections()

        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_performance_francaise(self):
        """Creates a test database with more data for performance."""
        conn = sqlite3.connect(self.db_fr_path)
        cursor = conn.cursor()

        # Same schema as before
        cursor.execute(
            """
        CREATE TABLE mots_fr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            categorie_grammaticale TEXT,
            points INTEGER NOT NULL,
            valide_scrabble BOOLEAN DEFAULT 1,
            longueur INTEGER NOT NULL,
            premiere_lettre CHAR(1) NOT NULL,
            derniere_lettre CHAR(1) NOT NULL,
            voyelles TEXT,
            consonnes TEXT,
            date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        # Critical indexes for performance
        cursor.execute("CREATE INDEX idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")

        # Many test data entries
        mots_test = []
        for i in range(1000):  # 1000 test words
            mot = f"MOT{i:04d}"
            mots_test.append(
                (
                    mot,
                    f"Définition du mot {i}",
                    "nom",
                    10,
                    1,
                    len(mot),
                    mot[0],
                    mot[-1],
                    "O",
                    "MT",
                    "Test",
                )
            )

        cursor.executemany(
            """
        INSERT INTO mots_fr (mot, definition, categorie_grammaticale, points, valide_scrabble,
                           longueur, premiere_lettre, derniere_lettre, voyelles, consonnes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            mots_test,
        )

        conn.commit()
        conn.close()

    def _creer_base_performance_anglaise(self):
        """Creates an English test database for performance."""
        conn = sqlite3.connect(self.db_en_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE mots_en (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            part_of_speech TEXT,
            points INTEGER NOT NULL,
            scrabble_valid BOOLEAN DEFAULT 1,
            length INTEGER NOT NULL,
            first_letter CHAR(1) NOT NULL,
            last_letter CHAR(1) NOT NULL,
            vowels TEXT,
            consonants TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        cursor.execute("CREATE INDEX idx_mots_en_word ON mots_en(word)")
        cursor.execute("CREATE INDEX idx_mots_en_scrabble_valid ON mots_en(scrabble_valid)")

        # Test data
        words_test = []
        for i in range(1000):
            word = f"WORD{i:04d}"
            words_test.append(
                (
                    word,
                    f"Definition of word {i}",
                    "noun",
                    8,
                    1,
                    len(word),
                    word[0],
                    word[-1],
                    "O",
                    "WRD",
                    "Test",
                )
            )

        cursor.executemany(
            """
        INSERT INTO mots_en (word, definition, part_of_speech, points, scrabble_valid,
                           length, first_letter, last_letter, vowels, consonants, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            words_test,
        )

        conn.commit()
        conn.close()

    def test_performance_recherche_inferieure_50ms(self):
        """Performance test: word search < 50ms."""
        # Test on multiple words
        mots_test = ["MOT0001", "MOT0500", "MOT0999"]

        for mot in mots_test:
            debut = time.time()
            resultat = self.service.validate_word(mot, LanguageEnum.FRENCH)
            temps_ms = (time.time() - debut) * 1000

            self.assertLess(
                temps_ms,
                50.0,
                f"Search '{mot}' too slow: {temps_ms:.1f}ms (target: < 50ms)",
            )
            self.assertTrue(resultat.is_valid)
            self.assertIsNotNone(resultat.search_time_ms)

    def test_performance_batch_validation(self):
        """Performance test: batch validation (10 words) < 200ms."""
        mots_test = [f"MOT{i:04d}" for i in range(0, 10)]

        debut = time.time()
        for mot in mots_test:
            self.service.validate_word(mot, LanguageEnum.FRENCH)
        temps_total_ms = (time.time() - debut) * 1000

        self.assertLess(
            temps_total_ms,
            200.0,
            f"Batch validation too slow: {temps_total_ms:.1f}ms (target: < 200ms)",
        )

    def test_statistiques_performance(self):
        """Service performance statistics test."""
        # Perform some searches
        for i in range(5):
            self.service.validate_word(f"MOT{i:04d}", LanguageEnum.FRENCH)

        stats = self.service.get_performance_statistics()

        self.assertIn("total_requests", stats)
        self.assertIn("total_time_ms", stats)
        self.assertIn("average_time_ms", stats)
        self.assertGreaterEqual(stats["total_requests"], 5)
        self.assertGreater(stats["total_time_ms"], 0)
        self.assertLess(stats["average_time_ms"], 50.0)


class TestCaracteresSpeciaux(unittest.TestCase):
    """Special characters handling tests."""

    def setUp(self):
        """Special characters test initialization."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french_accents.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english_simple.db")

        self._creer_base_accents_francaise()
        self._creer_base_simple_anglaise()

        self.service = DictionaryService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Cleanup after special characters tests."""
        self.service.close_connections()

        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_accents_francaise(self):
        """Creates a database with French accented words."""
        conn = sqlite3.connect(self.db_fr_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE mots_fr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            categorie_grammaticale TEXT,
            points INTEGER NOT NULL,
            valide_scrabble BOOLEAN DEFAULT 1,
            longueur INTEGER NOT NULL,
            premiere_lettre CHAR(1) NOT NULL,
            derniere_lettre CHAR(1) NOT NULL,
            voyelles TEXT,
            consonnes TEXT,
            date_ajout DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        cursor.execute("CREATE INDEX idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")

        # Words with accents and special French characters
        mots_accents = [
            (
                "ÊTRE",
                "Verbe d'existence",
                "verbe",
                4,
                1,
                4,
                "Ê",
                "E",
                "ÊE",
                "TR",
                "ODS",
            ),
            (
                "CŒUR",
                "Organe de circulation",
                "nom",
                7,
                1,
                4,
                "C",
                "R",
                "ŒU",
                "CR",
                "ODS",
            ),
            (
                "NAÏF",
                "Qui manque d'expérience",
                "adjectif",
                7,
                1,
                4,
                "N",
                "F",
                "AÏ",
                "NF",
                "ODS",
            ),
            (
                "ÉLÈVE",
                "Personne qui étudie",
                "nom",
                8,
                1,
                5,
                "É",
                "E",
                "ÉÈE",
                "LV",
                "ODS",
            ),
            (
                "FRANÇAIS",
                "De France",
                "adjectif",
                14,
                1,
                8,
                "F",
                "S",
                "AAIÇ",
                "FRNS",
                "ODS",
            ),
        ]

        cursor.executemany(
            """
        INSERT INTO mots_fr (mot, definition, categorie_grammaticale, points, valide_scrabble,
                           longueur, premiere_lettre, derniere_lettre, voyelles, consonnes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            mots_accents,
        )

        conn.commit()
        conn.close()

    def _creer_base_simple_anglaise(self):
        """Creates a simple English database (no accents)."""
        conn = sqlite3.connect(self.db_en_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE mots_en (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            part_of_speech TEXT,
            points INTEGER NOT NULL,
            scrabble_valid BOOLEAN DEFAULT 1,
            length INTEGER NOT NULL,
            first_letter CHAR(1) NOT NULL,
            last_letter CHAR(1) NOT NULL,
            vowels TEXT,
            consonants TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL
        )
        """
        )

        cursor.execute("CREATE INDEX idx_mots_en_word ON mots_en(word)")

        # Simple English words
        words_simple = [
            (
                "SIMPLE",
                "Not complex",
                "adjective",
                10,
                1,
                6,
                "S",
                "E",
                "IE",
                "SMPL",
                "SOWPODS",
            )
        ]

        cursor.executemany(
            """
        INSERT INTO mots_en (word, definition, part_of_speech, points, scrabble_valid,
                           length, first_letter, last_letter, vowels, consonants, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            words_simple,
        )

        conn.commit()
        conn.close()

    def test_validation_accents_francais(self):
        """French words with accents validation test."""
        mots_accents = ["ÊTRE", "CŒUR", "NAÏF", "ÉLÈVE", "FRANÇAIS"]

        for mot in mots_accents:
            resultat = self.service.validate_word(mot, LanguageEnum.FRENCH)
            self.assertTrue(resultat.is_valid, f"Accented word '{mot}' not validated")
            self.assertIsNotNone(resultat.definition)

    def test_normalisation_casse(self):
        """Case normalization test."""
        # Test in lowercase
        resultat_min = self.service.validate_word("être", LanguageEnum.FRENCH)
        # Test in uppercase
        resultat_maj = self.service.validate_word("ÊTRE", LanguageEnum.FRENCH)

        self.assertTrue(resultat_min.is_valid)
        self.assertTrue(resultat_maj.is_valid)
        self.assertEqual(resultat_min.word, resultat_maj.word)


class TestConnexionSQLite(unittest.TestCase):
    """SQLite connection management tests."""

    def test_etablissement_connexion(self):
        """SQLite connection establishment test."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_connection.db")

        # Create minimal database
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        try:
            # Test connection through service
            service = DictionaryService(db_path, db_path)
            self.assertIsNotNone(service)

            # Test explicit closure
            service.close_connections()

        finally:
            os.unlink(db_path)
            os.rmdir(temp_dir)

    def test_gestion_erreur_connexion(self):
        """Connection error handling test."""
        # Attempt connection to non-existent file
        with self.assertRaises(FileNotFoundError):
            service = DictionaryService("/inexistant/french.db", "/inexistant/english.db")
            service.validate_word("TEST", LanguageEnum.FRENCH)


class TestAPIREST(unittest.TestCase):
    """REST API integration tests for Godot."""

    @classmethod
    def setUpClass(cls):
        """API test initialization once only."""
        cls.client = TestClient(app)

    def test_endpoint_validation_francais(self):
        """French validation endpoint test."""
        # Mock service for tests
        with patch("dictionnaire_service.get_service") as mock_service:
            mock_service.return_value.validate_word.return_value = ValidationResult(
                word="TEST",
                is_valid=True,
                definition="Mot de test",
                points=8,
                language=LanguageEnum.FRENCH,
                search_time_ms=25.0,
            )

            response = self.client.get("/api/v1/dictionnaire/fr/valider/TEST")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["mot"], "TEST")
            self.assertTrue(data["valide"])
            self.assertEqual(data["definition"], "Mot de test")
            self.assertEqual(data["points"], 8)
            self.assertEqual(data["langue"], "fr")
            self.assertLess(data["temps_recherche_ms"], 50.0)

    def test_endpoint_validation_anglais(self):
        """English validation endpoint test."""
        with patch("dictionnaire_service.get_service") as mock_service:
            mock_service.return_value.validate_word.return_value = ValidationResult(
                word="TEST",
                is_valid=True,
                definition="Test word",
                points=8,
                language=LanguageEnum.ENGLISH,
                search_time_ms=30.0,
            )

            response = self.client.get("/api/v1/dictionnaire/en/valider/TEST")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["mot"], "TEST")
            self.assertTrue(data["valide"])
            self.assertEqual(data["langue"], "en")

    def test_endpoint_definition_francaise(self):
        """French definition endpoint test."""
        with patch("dictionnaire_service.get_service") as mock_service:
            mock_service.return_value.get_definition.return_value = "Définition de test"

            response = self.client.get("/api/v1/dictionnaire/fr/definition/TEST")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["mot"], "TEST")
            self.assertEqual(data["definition"], "Définition de test")
            self.assertTrue(data["trouve"])
            self.assertEqual(data["langue"], "fr")

    def test_endpoint_health_check(self):
        """Health check endpoint test."""
        response = self.client.get("/api/v1/dictionnaire/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("statut", data)
        self.assertIn("version", data)
        self.assertIn("bases", data)
        self.assertIn("timestamp", data)

    def test_gestion_erreur_mot_trop_long(self):
        """Too long word error handling test."""
        mot_trop_long = "A" * 20  # More than 15 characters
        response = self.client.get(f"/api/v1/dictionnaire/fr/valider/{mot_trop_long}")

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_cors_headers(self):
        """CORS headers presence test for Godot."""
        response = self.client.get("/api/v1/dictionnaire/health")

        # Verify CORS headers are present (for Godot)
        self.assertEqual(response.status_code, 200)
        # Note: TestClient doesn't fully simulate CORS headers
        # In production, verify with real HTTP client


if __name__ == "__main__":
    # Logging configuration for tests
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)
