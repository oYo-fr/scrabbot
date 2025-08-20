#!/usr/bin/env python3
"""
Script de conversion CSV → SQLite pour les dictionnaires Scrabbot.

Ce script convertit les fichiers CSV sources (dictionnaire_fr.csv, dictionnaire_en.csv)
en bases de données SQLite optimisées pour les performances.

Usage:
    python csv_to_sqlite.py dictionnaire_fr.csv french.db --langue fr
    python csv_to_sqlite.py dictionnaire_en.csv english.db --langue en
    python csv_to_sqlite.py --all  # Convertit tous les dictionnaires

Fonctionnalités :
- Validation des données CSV
- Création des tables optimisées avec index
- Gestion des erreurs et logging
- Statistiques de conversion
- Mode batch pour tous les dictionnaires
"""

import sqlite3
import csv
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ConvertisseurCSVSQLite:
    """
    Convertisseur CSV vers SQLite pour les dictionnaires multilingues.
    """
    
    def __init__(self):
        self.statistiques = {
            "mots_traites": 0,
            "mots_valides": 0,
            "erreurs": 0,
            "debut": None,
            "fin": None
        }
    
    def creer_schema_francais(self, cursor: sqlite3.Cursor):
        """
        Crée le schéma de base pour le dictionnaire français.
        
        Args:
            cursor: Curseur de la base SQLite
        """
        # Table des métadonnées
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionnaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_langue CHAR(2) NOT NULL,
            nom TEXT NOT NULL,
            version TEXT NOT NULL,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            UNIQUE(code_langue, version)
        )
        """)
        
        # Table principale des mots français
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mots_fr (
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
            source TEXT NOT NULL,
            CONSTRAINT check_longueur CHECK (longueur > 0),
            CONSTRAINT check_points CHECK (points >= 0)
        )
        """)
        
        # Index pour optimiser les recherches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_mot ON mots_fr(mot)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_longueur ON mots_fr(longueur)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_premiere_lettre ON mots_fr(premiere_lettre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_derniere_lettre ON mots_fr(derniere_lettre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_points ON mots_fr(points)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_fr_valide_scrabble ON mots_fr(valide_scrabble)")
        
        # Vue pour recherche rapide
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS recherche_fr AS 
        SELECT mot, definition, points, valide_scrabble, longueur, categorie_grammaticale
        FROM mots_fr 
        WHERE valide_scrabble = 1
        ORDER BY mot
        """)
        
        logger.info("Schéma français créé avec succès")
    
    def creer_schema_anglais(self, cursor: sqlite3.Cursor):
        """
        Crée le schéma de base pour le dictionnaire anglais.
        
        Args:
            cursor: Curseur de la base SQLite
        """
        # Table principale des mots anglais
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mots_en (
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
            source TEXT NOT NULL,
            CONSTRAINT check_length CHECK (length > 0),
            CONSTRAINT check_points CHECK (points >= 0)
        )
        """)
        
        # Index pour optimiser les recherches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_word ON mots_en(word)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_length ON mots_en(length)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_first_letter ON mots_en(first_letter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_last_letter ON mots_en(last_letter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_points ON mots_en(points)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mots_en_scrabble_valid ON mots_en(scrabble_valid)")
        
        # Vue pour recherche rapide
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS recherche_en AS 
        SELECT word, definition, points, scrabble_valid, length, part_of_speech
        FROM mots_en 
        WHERE scrabble_valid = 1
        ORDER BY word
        """)
        
        logger.info("Schéma anglais créé avec succès")
    
    def calculer_points_scrabble_fr(self, mot: str) -> int:
        """
        Calcule les points Scrabble pour un mot français.
        
        Args:
            mot: Le mot à évaluer
            
        Returns:
            Nombre de points selon les valeurs Scrabble française
        """
        points_lettres = {
            'A': 1, 'E': 1, 'I': 1, 'L': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'T': 1, 'U': 1,
            'D': 2, 'G': 2, 'M': 2,
            'B': 3, 'C': 3, 'P': 3,
            'F': 4, 'H': 4, 'V': 4,
            'J': 8, 'Q': 8,
            'K': 10, 'W': 10, 'X': 10, 'Y': 10, 'Z': 10
        }
        
        return sum(points_lettres.get(lettre.upper(), 0) for lettre in mot)
    
    def calculer_points_scrabble_en(self, mot: str) -> int:
        """
        Calcule les points Scrabble pour un mot anglais.
        
        Args:
            mot: Le mot à évaluer
            
        Returns:
            Nombre de points selon les valeurs Scrabble anglaise
        """
        points_lettres = {
            'A': 1, 'E': 1, 'I': 1, 'L': 1, 'N': 1, 'O': 1, 'R': 1, 'S': 1, 'T': 1, 'U': 1,
            'D': 2, 'G': 2,
            'B': 3, 'C': 3, 'M': 3, 'P': 3,
            'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
            'K': 5,
            'J': 8, 'X': 8,
            'Q': 10, 'Z': 10
        }
        
        return sum(points_lettres.get(lettre.upper(), 0) for lettre in mot)
    
    def extraire_voyelles_consonnes(self, mot: str) -> Tuple[str, str]:
        """
        Extrait les voyelles et consonnes d'un mot.
        
        Args:
            mot: Le mot à analyser
            
        Returns:
            Tuple (voyelles, consonnes)
        """
        voyelles_fr = set('AEIOUÀÉÈÊËÎÏÔÖÙÛÜ')
        voyelles_en = set('AEIOU')
        
        mot_upper = mot.upper()
        voyelles = ''.join(c for c in mot_upper if c in voyelles_fr or c in voyelles_en)
        consonnes = ''.join(c for c in mot_upper if c.isalpha() and c not in voyelles_fr and c not in voyelles_en)
        
        return voyelles, consonnes
    
    def valider_ligne_csv_fr(self, ligne: Dict[str, str]) -> Optional[Dict[str, any]]:
        """
        Valide et normalise une ligne CSV française.
        
        Args:
            ligne: Dictionnaire représentant une ligne CSV
            
        Returns:
            Dictionnaire normalisé ou None si invalide
        """
        try:
            mot = ligne.get('mot', '').strip().upper()
            definition = ligne.get('definition', '').strip()
            
            if not mot or not definition:
                logger.warning(f"Mot ou définition manquant: {ligne}")
                return None
            
            if len(mot) < 2 or len(mot) > 15:
                logger.warning(f"Longueur mot invalide '{mot}': {len(mot)} caractères")
                return None
            
            # Validation caractères français
            if not all(c.isalpha() or c in 'ÀÉÈÊËÎÏÔÖÙÛÜÇ' for c in mot):
                logger.warning(f"Caractères invalides dans '{mot}'")
                return None
            
            # Calcul des métadonnées
            points = self.calculer_points_scrabble_fr(mot)
            voyelles, consonnes = self.extraire_voyelles_consonnes(mot)
            
            return {
                'mot': mot,
                'definition': definition,
                'categorie_grammaticale': ligne.get('categorie_grammaticale', ''),
                'points': points,
                'valide_scrabble': ligne.get('valide_scrabble', 'true').lower() == 'true',
                'longueur': len(mot),
                'premiere_lettre': mot[0],
                'derniere_lettre': mot[-1],
                'voyelles': voyelles,
                'consonnes': consonnes,
                'source': ligne.get('source', 'ODS')
            }
            
        except Exception as e:
            logger.error(f"Erreur validation ligne française {ligne}: {e}")
            return None
    
    def valider_ligne_csv_en(self, ligne: Dict[str, str]) -> Optional[Dict[str, any]]:
        """
        Valide et normalise une ligne CSV anglaise.
        
        Args:
            ligne: Dictionnaire représentant une ligne CSV
            
        Returns:
            Dictionnaire normalisé ou None si invalide
        """
        try:
            word = ligne.get('word', '').strip().upper()
            definition = ligne.get('definition', '').strip()
            
            if not word or not definition:
                logger.warning(f"Word ou definition manquant: {ligne}")
                return None
            
            if len(word) < 2 or len(word) > 15:
                logger.warning(f"Longueur word invalide '{word}': {len(word)} caractères")
                return None
            
            # Validation caractères anglais
            if not all(c.isalpha() for c in word):
                logger.warning(f"Caractères invalides dans '{word}'")
                return None
            
            # Calcul des métadonnées
            points = self.calculer_points_scrabble_en(word)
            vowels, consonants = self.extraire_voyelles_consonnes(word)
            
            return {
                'word': word,
                'definition': definition,
                'part_of_speech': ligne.get('part_of_speech', ''),
                'points': points,
                'scrabble_valid': ligne.get('scrabble_valid', 'true').lower() == 'true',
                'length': len(word),
                'first_letter': word[0],
                'last_letter': word[-1],
                'vowels': vowels,
                'consonants': consonants,
                'source': ligne.get('source', 'SOWPODS')
            }
            
        except Exception as e:
            logger.error(f"Erreur validation ligne anglaise {ligne}: {e}")
            return None
    
    def convertir_csv_vers_sqlite(self, fichier_csv: str, fichier_db: str, langue: str, 
                                version: str = "1.0") -> bool:
        """
        Convertit un fichier CSV en base SQLite.
        
        Args:
            fichier_csv: Chemin vers le fichier CSV source
            fichier_db: Chemin vers la base SQLite de destination
            langue: Code langue ('fr' ou 'en')
            version: Version du dictionnaire
            
        Returns:
            True si la conversion a réussi, False sinon
        """
        self.statistiques["debut"] = time.time()
        
        try:
            # Vérification fichier source
            if not Path(fichier_csv).exists():
                logger.error(f"Fichier CSV introuvable: {fichier_csv}")
                return False
            
            # Connexion à la base
            conn = sqlite3.connect(fichier_db)
            cursor = conn.cursor()
            
            # Création du schéma
            if langue == 'fr':
                self.creer_schema_francais(cursor)
                table_name = 'mots_fr'
            else:
                self.creer_schema_anglais(cursor)
                table_name = 'mots_en'
            
            # Ajout métadonnées dictionnaire
            try:
                cursor.execute("""
                INSERT OR REPLACE INTO dictionnaires (code_langue, nom, version, source)
                VALUES (?, ?, ?, ?)
                """, (langue, f"Dictionnaire {langue.upper()}", version, fichier_csv))
            except sqlite3.IntegrityError:
                pass  # Métadonnées déjà présentes
            
            # Traitement du CSV
            with open(fichier_csv, 'r', encoding='utf-8') as f:
                lecteur = csv.DictReader(f)
                lignes_valides = []
                
                for numero_ligne, ligne in enumerate(lecteur, 1):
                    self.statistiques["mots_traites"] += 1
                    
                    # Validation selon la langue
                    if langue == 'fr':
                        ligne_validee = self.valider_ligne_csv_fr(ligne)
                    else:
                        ligne_validee = self.valider_ligne_csv_en(ligne)
                    
                    if ligne_validee:
                        lignes_valides.append(ligne_validee)
                        self.statistiques["mots_valides"] += 1
                    else:
                        self.statistiques["erreurs"] += 1
                    
                    # Traitement par batch pour les performances
                    if len(lignes_valides) >= 1000:
                        self._inserer_batch(cursor, table_name, lignes_valides, langue)
                        lignes_valides.clear()
                
                # Insertion du dernier batch
                if lignes_valides:
                    self._inserer_batch(cursor, table_name, lignes_valides, langue)
            
            # Optimisation finale
            cursor.execute("ANALYZE")
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            self.statistiques["fin"] = time.time()
            self._afficher_statistiques(fichier_csv, fichier_db)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur conversion {fichier_csv} → {fichier_db}: {e}")
            return False
    
    def _inserer_batch(self, cursor: sqlite3.Cursor, table_name: str, 
                      lignes: List[Dict], langue: str):
        """
        Insère un batch de lignes dans la base.
        
        Args:
            cursor: Curseur SQLite
            table_name: Nom de la table
            lignes: Liste des lignes à insérer
            langue: Code langue
        """
        try:
            if langue == 'fr':
                query = """
                INSERT OR REPLACE INTO mots_fr 
                (mot, definition, categorie_grammaticale, points, valide_scrabble, 
                 longueur, premiere_lettre, derniere_lettre, voyelles, consonnes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                data = [(
                    ligne['mot'], ligne['definition'], ligne['categorie_grammaticale'],
                    ligne['points'], ligne['valide_scrabble'], ligne['longueur'],
                    ligne['premiere_lettre'], ligne['derniere_lettre'],
                    ligne['voyelles'], ligne['consonnes'], ligne['source']
                ) for ligne in lignes]
            else:
                query = """
                INSERT OR REPLACE INTO mots_en 
                (word, definition, part_of_speech, points, scrabble_valid, 
                 length, first_letter, last_letter, vowels, consonants, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                data = [(
                    ligne['word'], ligne['definition'], ligne['part_of_speech'],
                    ligne['points'], ligne['scrabble_valid'], ligne['length'],
                    ligne['first_letter'], ligne['last_letter'],
                    ligne['vowels'], ligne['consonants'], ligne['source']
                ) for ligne in lignes]
            
            cursor.executemany(query, data)
            logger.debug(f"Batch de {len(lignes)} lignes inséré")
            
        except Exception as e:
            logger.error(f"Erreur insertion batch: {e}")
            self.statistiques["erreurs"] += len(lignes)
    
    def _afficher_statistiques(self, fichier_csv: str, fichier_db: str):
        """Affiche les statistiques de conversion."""
        duree = self.statistiques["fin"] - self.statistiques["debut"]
        taille_db = Path(fichier_db).stat().st_size / (1024 * 1024)  # MB
        
        logger.info("=" * 60)
        logger.info("STATISTIQUES DE CONVERSION")
        logger.info("=" * 60)
        logger.info(f"Fichier source: {fichier_csv}")
        logger.info(f"Base de destination: {fichier_db}")
        logger.info(f"Mots traités: {self.statistiques['mots_traites']}")
        logger.info(f"Mots valides: {self.statistiques['mots_valides']}")
        logger.info(f"Erreurs: {self.statistiques['erreurs']}")
        logger.info(f"Taux de succès: {(self.statistiques['mots_valides']/self.statistiques['mots_traites']*100):.1f}%")
        logger.info(f"Durée: {duree:.2f} secondes")
        logger.info(f"Vitesse: {self.statistiques['mots_traites']/duree:.0f} mots/seconde")
        logger.info(f"Taille base: {taille_db:.1f} MB")
        logger.info("=" * 60)


def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(
        description="Conversion CSV → SQLite pour dictionnaires Scrabbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s dictionnaire_fr.csv french.db --langue fr
  %(prog)s dictionnaire_en.csv english.db --langue en --version 2.0
  %(prog)s --all --force
        """
    )
    
    parser.add_argument('fichier_csv', nargs='?', 
                       help='Fichier CSV source')
    parser.add_argument('fichier_db', nargs='?',
                       help='Base SQLite de destination')
    parser.add_argument('--langue', choices=['fr', 'en'], 
                       help='Langue du dictionnaire (fr ou en)')
    parser.add_argument('--version', default='1.0',
                       help='Version du dictionnaire (défaut: 1.0)')
    parser.add_argument('--all', action='store_true',
                       help='Convertir tous les dictionnaires')
    parser.add_argument('--force', action='store_true',
                       help='Écraser les bases existantes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbeux')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    convertisseur = ConvertisseurCSVSQLite()
    
    if args.all:
        # Conversion de tous les dictionnaires
        conversions = [
            ('sources/dictionnaire_fr.csv', 'databases/french.db', 'fr'),
            ('sources/dictionnaire_en.csv', 'databases/english.db', 'en')
        ]
        
        succes_total = True
        for csv_file, db_file, langue in conversions:
            if Path(csv_file).exists():
                if args.force or not Path(db_file).exists():
                    logger.info(f"Conversion {langue.upper()}: {csv_file} → {db_file}")
                    succes = convertisseur.convertir_csv_vers_sqlite(
                        csv_file, db_file, langue, args.version
                    )
                    succes_total = succes_total and succes
                else:
                    logger.info(f"Base {db_file} existe déjà (utilisez --force pour écraser)")
            else:
                logger.warning(f"Fichier CSV introuvable: {csv_file}")
        
        return 0 if succes_total else 1
    
    # Conversion individuelle
    if not args.fichier_csv or not args.fichier_db or not args.langue:
        parser.error("Arguments manquants. Utilisez --all ou spécifiez fichier_csv, fichier_db et --langue")
    
    if not args.force and Path(args.fichier_db).exists():
        logger.error(f"Base {args.fichier_db} existe déjà. Utilisez --force pour écraser.")
        return 1
    
    succes = convertisseur.convertir_csv_vers_sqlite(
        args.fichier_csv, args.fichier_db, args.langue, args.version
    )
    
    return 0 if succes else 1


if __name__ == "__main__":
    sys.exit(main())
