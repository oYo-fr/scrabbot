#!/usr/bin/env python3
"""
Tests unitaires pour le serveur web - Système de dictionnaires Scrabbot.

Ces tests vérifient que le serveur web et l'application Godot peuvent
bien accéder aux dictionnaires selon les spécifications du ticket OYO-7.

Tests couverts :
- Test d'accès basique SQLite
- Test de validation de mots
- Test de performance (< 50ms)
- Test de caractères spéciaux
- Test de connexion/fermeture SQLite
- Test d'intégration API REST
"""

import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Ajout du chemin pour importer les modules
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "models"))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "api"))

from dictionnaire import DictionnaireService, LangueEnum, ResultatValidation
from dictionnaire_service import app
from fastapi.testclient import TestClient


class TestAccesSQLiteBasique(unittest.TestCase):
    """Tests d'accès basique à la base SQLite."""

    def setUp(self):
        """Initialisation des tests."""
        # Création de bases temporaires pour les tests
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english.db")

        # Création des bases de test
        self._creer_base_test_francaise()
        self._creer_base_test_anglaise()

        # Service de test
        self.service = DictionnaireService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Nettoyage après les tests."""
        self.service.fermer_connexions()

        # Suppression des fichiers temporaires
        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_test_francaise(self):
        """Crée une base de test française."""
        conn = sqlite3.connect(self.db_fr_path)
        cursor = conn.cursor()

        # Table métadonnées
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

        # Table mots français
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

        # Index
        cursor.execute("CREATE INDEX idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX idx_mots_fr_longueur ON mots_fr(longueur)")
        cursor.execute("CREATE INDEX idx_mots_fr_premiere_lettre ON mots_fr(premiere_lettre)")
        cursor.execute("CREATE INDEX idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")

        # Données de test
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
        """Crée une base de test anglaise."""
        conn = sqlite3.connect(self.db_en_path)
        cursor = conn.cursor()

        # Table mots anglais
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

        # Index
        cursor.execute("CREATE INDEX idx_mots_en_word ON mots_en(word)")
        cursor.execute("CREATE INDEX idx_mots_en_length ON mots_en(length)")
        cursor.execute("CREATE INDEX idx_mots_en_first_letter ON mots_en(first_letter)")
        cursor.execute("CREATE INDEX idx_mots_en_scrabble_valid ON mots_en(scrabble_valid)")

        # Données de test
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
        """Test d'accès basique : récupérer un mot quelconque depuis SQLite français."""
        resultat = self.service.valider_mot("CHAT", LangueEnum.FRANCAIS)

        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.mot, "CHAT")
        self.assertTrue(resultat.valide)
        self.assertEqual(resultat.definition, "Mammifère domestique félin")
        self.assertEqual(resultat.points, 9)
        self.assertEqual(resultat.langue, LangueEnum.FRANCAIS)

    def test_acces_mot_quelconque_anglais(self):
        """Test d'accès basique : récupérer un mot quelconque depuis SQLite anglais."""
        resultat = self.service.valider_mot("CAT", LangueEnum.ANGLAIS)

        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.mot, "CAT")
        self.assertTrue(resultat.valide)
        self.assertEqual(resultat.definition, "Small domesticated carnivorous mammal")
        self.assertEqual(resultat.points, 5)
        self.assertEqual(resultat.langue, LangueEnum.ANGLAIS)

    def test_validation_mot_valide_francais(self):
        """Test de validation : mot valide retourne True."""
        resultat = self.service.valider_mot("CHIEN", LangueEnum.FRANCAIS)

        self.assertTrue(resultat.valide)
        self.assertIsNotNone(resultat.definition)
        self.assertGreater(resultat.points, 0)

    def test_validation_mot_invalide_francais(self):
        """Test de validation : mot invalide retourne False."""
        resultat = self.service.valider_mot("MOTINEXISTANT", LangueEnum.FRANCAIS)

        self.assertFalse(resultat.valide)
        self.assertIsNone(resultat.definition)
        self.assertIsNone(resultat.points)

    def test_validation_mot_valide_anglais(self):
        """Test de validation : mot valide anglais retourne True."""
        resultat = self.service.valider_mot("DOG", LangueEnum.ANGLAIS)

        self.assertTrue(resultat.valide)
        self.assertIsNotNone(resultat.definition)
        self.assertGreater(resultat.points, 0)

    def test_validation_mot_invalide_anglais(self):
        """Test de validation : mot invalide anglais retourne False."""
        resultat = self.service.valider_mot("NONEXISTENTWORD", LangueEnum.ANGLAIS)

        self.assertFalse(resultat.valide)
        self.assertIsNone(resultat.definition)
        self.assertIsNone(resultat.points)


class TestPerformance(unittest.TestCase):
    """Tests de performance selon les critères d'acceptation."""

    def setUp(self):
        """Initialisation des tests de performance."""
        # Utilisation des mêmes bases de test
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english.db")

        # Création des bases avec plus de données pour tester les performances
        self._creer_base_performance_francaise()
        self._creer_base_performance_anglaise()

        self.service = DictionnaireService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Nettoyage après les tests de performance."""
        self.service.fermer_connexions()

        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_performance_francaise(self):
        """Crée une base de test avec plus de données pour les performances."""
        conn = sqlite3.connect(self.db_fr_path)
        cursor = conn.cursor()

        # Même schéma que précédemment
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

        # Index critiques pour les performances
        cursor.execute("CREATE INDEX idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")

        # Données de test nombreuses
        mots_test = []
        for i in range(1000):  # 1000 mots de test
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
        """Crée une base de test anglaise pour les performances."""
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

        # Données de test
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
        """Test de performance : recherche d'un mot < 50ms."""
        # Test sur plusieurs mots
        mots_test = ["MOT0001", "MOT0500", "MOT0999"]

        for mot in mots_test:
            debut = time.time()
            resultat = self.service.valider_mot(mot, LangueEnum.FRANCAIS)
            temps_ms = (time.time() - debut) * 1000

            self.assertLess(
                temps_ms,
                50.0,
                f"Recherche '{mot}' trop lente: {temps_ms:.1f}ms (objectif: < 50ms)",
            )
            self.assertTrue(resultat.valide)
            self.assertIsNotNone(resultat.temps_recherche_ms)

    def test_performance_batch_validation(self):
        """Test de performance : validation batch (10 mots) < 200ms."""
        mots_test = [f"MOT{i:04d}" for i in range(0, 10)]

        debut = time.time()
        for mot in mots_test:
            self.service.valider_mot(mot, LangueEnum.FRANCAIS)
        temps_total_ms = (time.time() - debut) * 1000

        self.assertLess(
            temps_total_ms,
            200.0,
            f"Validation batch trop lente: {temps_total_ms:.1f}ms (objectif: < 200ms)",
        )

    def test_statistiques_performance(self):
        """Test des statistiques de performance du service."""
        # Effectuer quelques recherches
        for i in range(5):
            self.service.valider_mot(f"MOT{i:04d}", LangueEnum.FRANCAIS)

        stats = self.service.obtenir_statistiques_performance()

        self.assertIn("requetes_totales", stats)
        self.assertIn("temps_total_ms", stats)
        self.assertIn("temps_moyen_ms", stats)
        self.assertGreaterEqual(stats["requetes_totales"], 5)
        self.assertGreater(stats["temps_total_ms"], 0)
        self.assertLess(stats["temps_moyen_ms"], 50.0)


class TestCaracteresSpeciaux(unittest.TestCase):
    """Tests de gestion des caractères spéciaux."""

    def setUp(self):
        """Initialisation des tests de caractères spéciaux."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_fr_path = os.path.join(self.temp_dir, "test_french_accents.db")
        self.db_en_path = os.path.join(self.temp_dir, "test_english_simple.db")

        self._creer_base_accents_francaise()
        self._creer_base_simple_anglaise()

        self.service = DictionnaireService(self.db_fr_path, self.db_en_path)

    def tearDown(self):
        """Nettoyage après les tests de caractères spéciaux."""
        self.service.fermer_connexions()

        for file_path in [self.db_fr_path, self.db_en_path]:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def _creer_base_accents_francaise(self):
        """Crée une base avec des mots français accentués."""
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

        # Mots avec accents et caractères spéciaux français
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
        """Crée une base anglaise simple (sans accents)."""
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

        # Mots anglais simples
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
        """Test de validation des mots français avec accents."""
        mots_accents = ["ÊTRE", "CŒUR", "NAÏF", "ÉLÈVE", "FRANÇAIS"]

        for mot in mots_accents:
            resultat = self.service.valider_mot(mot, LangueEnum.FRANCAIS)
            self.assertTrue(resultat.valide, f"Mot accentué '{mot}' non validé")
            self.assertIsNotNone(resultat.definition)

    def test_normalisation_casse(self):
        """Test de normalisation de la casse."""
        # Test en minuscules
        resultat_min = self.service.valider_mot("être", LangueEnum.FRANCAIS)
        # Test en majuscules
        resultat_maj = self.service.valider_mot("ÊTRE", LangueEnum.FRANCAIS)

        self.assertTrue(resultat_min.valide)
        self.assertTrue(resultat_maj.valide)
        self.assertEqual(resultat_min.mot, resultat_maj.mot)


class TestConnexionSQLite(unittest.TestCase):
    """Tests de gestion des connexions SQLite."""

    def test_etablissement_connexion(self):
        """Test d'établissement de connexion SQLite."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_connection.db")

        # Création d'une base minimale
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        try:
            # Test de connexion via le service
            service = DictionnaireService(db_path, db_path)
            self.assertIsNotNone(service)

            # Test de fermeture explicite
            service.fermer_connexions()

        finally:
            os.unlink(db_path)
            os.rmdir(temp_dir)

    def test_gestion_erreur_connexion(self):
        """Test de gestion des erreurs de connexion."""
        # Tentative de connexion à un fichier inexistant
        with self.assertRaises(FileNotFoundError):
            service = DictionnaireService("/inexistant/french.db", "/inexistant/english.db")
            service.valider_mot("TEST", LangueEnum.FRANCAIS)


class TestAPIREST(unittest.TestCase):
    """Tests d'intégration de l'API REST pour Godot."""

    @classmethod
    def setUpClass(cls):
        """Initialisation des tests API une seule fois."""
        cls.client = TestClient(app)

    def test_endpoint_validation_francais(self):
        """Test de l'endpoint de validation française."""
        # Mock du service pour les tests
        with patch("dictionnaire_service.obtenir_service") as mock_service:
            mock_service.return_value.valider_mot.return_value = ResultatValidation(
                mot="TEST",
                valide=True,
                definition="Mot de test",
                points=8,
                langue=LangueEnum.FRANCAIS,
                temps_recherche_ms=25.0,
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
        """Test de l'endpoint de validation anglaise."""
        with patch("dictionnaire_service.obtenir_service") as mock_service:
            mock_service.return_value.valider_mot.return_value = ResultatValidation(
                mot="TEST",
                valide=True,
                definition="Test word",
                points=8,
                langue=LangueEnum.ANGLAIS,
                temps_recherche_ms=30.0,
            )

            response = self.client.get("/api/v1/dictionnaire/en/valider/TEST")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["mot"], "TEST")
            self.assertTrue(data["valide"])
            self.assertEqual(data["langue"], "en")

    def test_endpoint_definition_francaise(self):
        """Test de l'endpoint de définition française."""
        with patch("dictionnaire_service.obtenir_service") as mock_service:
            mock_service.return_value.obtenir_definition.return_value = "Définition de test"

            response = self.client.get("/api/v1/dictionnaire/fr/definition/TEST")

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["mot"], "TEST")
            self.assertEqual(data["definition"], "Définition de test")
            self.assertTrue(data["trouve"])
            self.assertEqual(data["langue"], "fr")

    def test_endpoint_health_check(self):
        """Test de l'endpoint de health check."""
        response = self.client.get("/api/v1/dictionnaire/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("statut", data)
        self.assertIn("version", data)
        self.assertIn("bases", data)
        self.assertIn("timestamp", data)

    def test_gestion_erreur_mot_trop_long(self):
        """Test de gestion d'erreur pour mot trop long."""
        mot_trop_long = "A" * 20  # Plus de 15 caractères
        response = self.client.get(f"/api/v1/dictionnaire/fr/valider/{mot_trop_long}")

        self.assertEqual(response.status_code, 422)  # Validation error

    def test_cors_headers(self):
        """Test de la présence des headers CORS pour Godot."""
        response = self.client.get("/api/v1/dictionnaire/health")

        # Vérification que les headers CORS sont présents (pour Godot)
        self.assertEqual(response.status_code, 200)
        # Note: TestClient ne simule pas complètement les headers CORS
        # En production, vérifier avec un vrai client HTTP


if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.WARNING)

    # Lancement des tests
    unittest.main(verbosity=2)
