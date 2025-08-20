#!/usr/bin/env python3
"""
Script de validation des données pour les dictionnaires Scrabbot.

Ce script valide :
- L'intégrité des fichiers CSV
- La cohérence des bases SQLite
- Les performances de recherche
- La qualité des données

Usage:
    python validate_data.py --csv dictionnaire_fr.csv
    python validate_data.py --db french.db --langue fr
    python validate_data.py --all --performance
    python validate_data.py --fix --backup
"""

import sqlite3
import csv
import argparse
import logging
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidateurDonnees:
    """
    Validateur pour les données des dictionnaires multilingues.
    """
    
    def __init__(self):
        self.rapport = {
            "timestamp": datetime.now().isoformat(),
            "validations": {},
            "erreurs": [],
            "avertissements": [],
            "statistiques": {},
            "performances": {}
        }
    
    def valider_csv(self, fichier_csv: str, langue: str) -> bool:
        """
        Valide un fichier CSV.
        
        Args:
            fichier_csv: Chemin vers le fichier CSV
            langue: Code langue ('fr' ou 'en')
            
        Returns:
            True si valide, False sinon
        """
        logger.info(f"Validation CSV: {fichier_csv}")
        
        if not Path(fichier_csv).exists():
            self._ajouter_erreur(f"Fichier CSV introuvable: {fichier_csv}")
            return False
        
        try:
            stats = {
                "lignes_totales": 0,
                "lignes_valides": 0,
                "mots_uniques": set(),
                "longueurs": {},
                "categories": {},
                "erreurs_format": 0
            }
            
            champs_requis_fr = ['mot', 'definition']
            champs_requis_en = ['word', 'definition']
            champs_requis = champs_requis_fr if langue == 'fr' else champs_requis_en
            
            with open(fichier_csv, 'r', encoding='utf-8') as f:
                lecteur = csv.DictReader(f)
                
                # Vérification en-têtes
                if not all(champ in lecteur.fieldnames for champ in champs_requis):
                    self._ajouter_erreur(f"Champs manquants dans CSV. Requis: {champs_requis}")
                    return False
                
                for numero_ligne, ligne in enumerate(lecteur, 1):
                    stats["lignes_totales"] += 1
                    
                    # Validation ligne
                    if self._valider_ligne_csv(ligne, langue, numero_ligne):
                        stats["lignes_valides"] += 1
                        
                        # Statistiques
                        mot = ligne.get('mot' if langue == 'fr' else 'word', '').strip().upper()
                        if mot:
                            stats["mots_uniques"].add(mot)
                            longueur = len(mot)
                            stats["longueurs"][longueur] = stats["longueurs"].get(longueur, 0) + 1
                            
                            categorie = ligne.get(
                                'categorie_grammaticale' if langue == 'fr' else 'part_of_speech', 
                                'inconnu'
                            )
                            stats["categories"][categorie] = stats["categories"].get(categorie, 0) + 1
                    else:
                        stats["erreurs_format"] += 1
            
            # Conversion set en int pour JSON
            stats["mots_uniques_count"] = len(stats["mots_uniques"])
            del stats["mots_uniques"]
            
            # Calcul métriques qualité
            taux_validite = (stats["lignes_valides"] / stats["lignes_totales"]) * 100
            
            self.rapport["validations"][f"csv_{langue}"] = {
                "fichier": fichier_csv,
                "statut": "VALID" if taux_validite >= 95 else "WARNING" if taux_validite >= 80 else "ERROR",
                "taux_validite": round(taux_validite, 2),
                "statistiques": stats
            }
            
            if taux_validite < 95:
                self._ajouter_avertissement(
                    f"Taux de validité CSV faible: {taux_validite:.1f}% ({fichier_csv})"
                )
            
            logger.info(f"CSV validé: {stats['lignes_valides']}/{stats['lignes_totales']} lignes valides")
            return taux_validite >= 80
            
        except Exception as e:
            self._ajouter_erreur(f"Erreur validation CSV {fichier_csv}: {e}")
            return False
    
    def valider_base_sqlite(self, fichier_db: str, langue: str) -> bool:
        """
        Valide une base SQLite.
        
        Args:
            fichier_db: Chemin vers la base SQLite
            langue: Code langue ('fr' ou 'en')
            
        Returns:
            True si valide, False sinon
        """
        logger.info(f"Validation SQLite: {fichier_db}")
        
        if not Path(fichier_db).exists():
            self._ajouter_erreur(f"Base SQLite introuvable: {fichier_db}")
            return False
        
        try:
            conn = sqlite3.connect(fichier_db)
            cursor = conn.cursor()
            
            # Vérification schéma
            if not self._verifier_schema(cursor, langue):
                return False
            
            # Statistiques base
            stats = self._calculer_statistiques_base(cursor, langue)
            
            # Tests intégrité
            integrite_ok = self._tester_integrite_donnees(cursor, langue)
            
            # Tests performance
            performances = self._tester_performances_base(cursor, langue)
            
            conn.close()
            
            # Évaluation globale
            statut = "VALID"
            if not integrite_ok:
                statut = "ERROR"
            elif performances.get("temps_moyen_ms", 100) > 50:
                statut = "WARNING"
            
            self.rapport["validations"][f"sqlite_{langue}"] = {
                "fichier": fichier_db,
                "statut": statut,
                "statistiques": stats,
                "performances": performances,
                "integrite": integrite_ok
            }
            
            logger.info(f"Base validée: {stats.get('nb_mots', 0)} mots, {statut}")
            return statut != "ERROR"
            
        except Exception as e:
            self._ajouter_erreur(f"Erreur validation base {fichier_db}: {e}")
            return False
    
    def _valider_ligne_csv(self, ligne: Dict[str, str], langue: str, numero: int) -> bool:
        """Valide une ligne CSV."""
        try:
            mot_col = 'mot' if langue == 'fr' else 'word'
            mot = ligne.get(mot_col, '').strip()
            definition = ligne.get('definition', '').strip()
            
            if not mot or not definition:
                self._ajouter_avertissement(f"Ligne {numero}: Mot ou définition manquant")
                return False
            
            if len(mot) < 2 or len(mot) > 15:
                self._ajouter_avertissement(f"Ligne {numero}: Longueur mot invalide '{mot}'")
                return False
            
            # Validation caractères selon langue
            if langue == 'fr':
                if not all(c.isalpha() or c in 'ÀÉÈÊËÎÏÔÖÙÛÜÇ' for c in mot.upper()):
                    self._ajouter_avertissement(f"Ligne {numero}: Caractères invalides '{mot}'")
                    return False
            else:
                if not mot.isalpha():
                    self._ajouter_avertissement(f"Ligne {numero}: Caractères invalides '{mot}'")
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _verifier_schema(self, cursor: sqlite3.Cursor, langue: str) -> bool:
        """Vérifie le schéma de la base."""
        try:
            # Tables requises
            tables_requises = ['dictionnaires']
            if langue == 'fr':
                tables_requises.append('mots_fr')
            else:
                tables_requises.append('mots_en')
            
            for table in tables_requises:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    self._ajouter_erreur(f"Table manquante: {table}")
                    return False
            
            # Index requis
            index_pattern = 'idx_mots_fr%' if langue == 'fr' else 'idx_mots_en%'
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE ?", (index_pattern,))
            indexes = cursor.fetchall()
            
            if len(indexes) < 4:  # Au moins 4 index requis
                self._ajouter_avertissement(f"Index insuffisants trouvés: {len(indexes)}")
            
            return True
            
        except Exception as e:
            self._ajouter_erreur(f"Erreur vérification schéma: {e}")
            return False
    
    def _calculer_statistiques_base(self, cursor: sqlite3.Cursor, langue: str) -> Dict:
        """Calcule les statistiques de la base."""
        stats = {}
        
        try:
            table = 'mots_fr' if langue == 'fr' else 'mots_en'
            mot_col = 'mot' if langue == 'fr' else 'word'
            longueur_col = 'longueur' if langue == 'fr' else 'length'
            valide_col = 'valide_scrabble' if langue == 'fr' else 'scrabble_valid'
            
            # Nombre total de mots
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats["nb_mots"] = cursor.fetchone()[0]
            
            # Mots valides au Scrabble
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {valide_col} = 1")
            stats["nb_mots_valides"] = cursor.fetchone()[0]
            
            # Distribution longueurs
            cursor.execute(f"SELECT {longueur_col}, COUNT(*) FROM {table} GROUP BY {longueur_col} ORDER BY {longueur_col}")
            stats["distribution_longueurs"] = dict(cursor.fetchall())
            
            # Mots avec définition
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE definition IS NOT NULL AND definition != ''")
            stats["nb_mots_avec_definition"] = cursor.fetchone()[0]
            
            # Taille base en MB
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            taille_bytes = cursor.fetchone()[0]
            stats["taille_mb"] = round(taille_bytes / (1024 * 1024), 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul statistiques: {e}")
        
        return stats
    
    def _tester_integrite_donnees(self, cursor: sqlite3.Cursor, langue: str) -> bool:
        """Teste l'intégrité des données."""
        try:
            table = 'mots_fr' if langue == 'fr' else 'mots_en'
            mot_col = 'mot' if langue == 'fr' else 'word'
            
            # Vérification doublons
            cursor.execute(f"SELECT {mot_col}, COUNT(*) FROM {table} GROUP BY {mot_col} HAVING COUNT(*) > 1")
            doublons = cursor.fetchall()
            
            if doublons:
                self._ajouter_avertissement(f"Doublons détectés: {len(doublons)} mots")
                return False
            
            # Vérification cohérence longueurs
            longueur_col = 'longueur' if langue == 'fr' else 'length'
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE LENGTH({mot_col}) != {longueur_col}")
            incoherences = cursor.fetchone()[0]
            
            if incoherences > 0:
                self._ajouter_erreur(f"Incohérences longueur: {incoherences} mots")
                return False
            
            return True
            
        except Exception as e:
            self._ajouter_erreur(f"Erreur test intégrité: {e}")
            return False
    
    def _tester_performances_base(self, cursor: sqlite3.Cursor, langue: str) -> Dict:
        """Teste les performances de la base."""
        table = 'mots_fr' if langue == 'fr' else 'mots_en'
        mot_col = 'mot' if langue == 'fr' else 'word'
        
        # Récupération échantillon de mots
        cursor.execute(f"SELECT {mot_col} FROM {table} ORDER BY RANDOM() LIMIT 100")
        mots_test = [row[0] for row in cursor.fetchall()]
        
        # Test recherche individuelle
        temps_recherches = []
        for mot in mots_test[:10]:  # Test sur 10 mots
            debut = time.time()
            cursor.execute(f"SELECT * FROM {table} WHERE {mot_col} = ?", (mot,))
            cursor.fetchone()
            temps_ms = (time.time() - debut) * 1000
            temps_recherches.append(temps_ms)
        
        # Test recherche par longueur
        debut = time.time()
        longueur_col = 'longueur' if langue == 'fr' else 'length'
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {longueur_col} = 5")
        cursor.fetchone()
        temps_longueur_ms = (time.time() - debut) * 1000
        
        return {
            "temps_moyen_ms": round(sum(temps_recherches) / len(temps_recherches), 2),
            "temps_max_ms": round(max(temps_recherches), 2),
            "temps_recherche_longueur_ms": round(temps_longueur_ms, 2),
            "nb_tests": len(temps_recherches)
        }
    
    def tester_performance_globale(self, fichier_db_fr: str, fichier_db_en: str) -> bool:
        """
        Teste les performances globales du système.
        
        Args:
            fichier_db_fr: Base française
            fichier_db_en: Base anglaise
            
        Returns:
            True si performances acceptables
        """
        logger.info("Test performance globale du système")
        
        try:
            # Import du service (simulation)
            sys.path.append(str(Path(__file__).parent.parent.parent.parent / "shared" / "models"))
            from dictionnaire import DictionnaireService, LangueEnum
            
            service = DictionnaireService(fichier_db_fr, fichier_db_en)
            
            # Mots de test
            mots_test_fr = ["CHAT", "CHIEN", "MAISON", "INEXISTANT"]
            mots_test_en = ["CAT", "DOG", "HOUSE", "NONEXISTENT"]
            
            temps_total = []
            
            # Test validation français
            for mot in mots_test_fr:
                debut = time.time()
                resultat = service.valider_mot(mot, LangueEnum.FRANCAIS)
                temps_ms = (time.time() - debut) * 1000
                temps_total.append(temps_ms)
                
                logger.debug(f"FR '{mot}': {resultat.valide} en {temps_ms:.1f}ms")
            
            # Test validation anglais
            for mot in mots_test_en:
                debut = time.time()
                resultat = service.valider_mot(mot, LangueEnum.ANGLAIS)
                temps_ms = (time.time() - debut) * 1000
                temps_total.append(temps_ms)
                
                logger.debug(f"EN '{mot}': {resultat.valide} en {temps_ms:.1f}ms")
            
            service.fermer_connexions()
            
            # Analyse performances
            temps_moyen = sum(temps_total) / len(temps_total)
            temps_max = max(temps_total)
            
            self.rapport["performances"]["globale"] = {
                "temps_moyen_ms": round(temps_moyen, 2),
                "temps_max_ms": round(temps_max, 2),
                "objectif_ms": 50.0,
                "conforme": temps_moyen <= 50.0
            }
            
            if temps_moyen > 50:
                self._ajouter_avertissement(f"Performance dégradée: {temps_moyen:.1f}ms (objectif: 50ms)")
                return False
            
            logger.info(f"Performance OK: {temps_moyen:.1f}ms moyen, {temps_max:.1f}ms max")
            return True
            
        except Exception as e:
            self._ajouter_erreur(f"Erreur test performance: {e}")
            return False
    
    def generer_rapport(self, fichier_sortie: Optional[str] = None) -> str:
        """
        Génère un rapport de validation.
        
        Args:
            fichier_sortie: Fichier de sortie (optionnel)
            
        Returns:
            Contenu du rapport JSON
        """
        # Résumé global
        self.rapport["resume"] = {
            "nb_validations": len(self.rapport["validations"]),
            "nb_erreurs": len(self.rapport["erreurs"]),
            "nb_avertissements": len(self.rapport["avertissements"]),
            "statut_global": "ERROR" if self.rapport["erreurs"] else 
                            "WARNING" if self.rapport["avertissements"] else "VALID"
        }
        
        rapport_json = json.dumps(self.rapport, indent=2, ensure_ascii=False)
        
        if fichier_sortie:
            with open(fichier_sortie, 'w', encoding='utf-8') as f:
                f.write(rapport_json)
            logger.info(f"Rapport sauvegardé: {fichier_sortie}")
        
        return rapport_json
    
    def _ajouter_erreur(self, message: str):
        """Ajoute une erreur au rapport."""
        self.rapport["erreurs"].append(message)
        logger.error(message)
    
    def _ajouter_avertissement(self, message: str):
        """Ajoute un avertissement au rapport."""
        self.rapport["avertissements"].append(message)
        logger.warning(message)


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Validation des données dictionnaires Scrabbot"
    )
    
    parser.add_argument('--csv', help='Valider un fichier CSV')
    parser.add_argument('--db', help='Valider une base SQLite')
    parser.add_argument('--langue', choices=['fr', 'en'], help='Langue du dictionnaire')
    parser.add_argument('--all', action='store_true', help='Valider tous les fichiers')
    parser.add_argument('--performance', action='store_true', help='Tester les performances')
    parser.add_argument('--rapport', help='Fichier rapport JSON de sortie')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mode verbeux')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validateur = ValidateurDonnees()
    succes_global = True
    
    if args.all:
        # Validation complète
        fichiers = [
            ('sources/dictionnaire_fr.csv', 'databases/french.db', 'fr'),
            ('sources/dictionnaire_en.csv', 'databases/english.db', 'en')
        ]
        
        for csv_file, db_file, langue in fichiers:
            if Path(csv_file).exists():
                succes = validateur.valider_csv(csv_file, langue)
                succes_global = succes_global and succes
            
            if Path(db_file).exists():
                succes = validateur.valider_base_sqlite(db_file, langue)
                succes_global = succes_global and succes
        
        if args.performance:
            if Path('databases/french.db').exists() and Path('databases/english.db').exists():
                succes = validateur.tester_performance_globale(
                    'databases/french.db', 'databases/english.db'
                )
                succes_global = succes_global and succes
    
    else:
        # Validation individuelle
        if args.csv:
            if not args.langue:
                parser.error("--langue requis avec --csv")
            succes_global = validateur.valider_csv(args.csv, args.langue)
        
        if args.db:
            if not args.langue:
                parser.error("--langue requis avec --db")
            succes_global = validateur.valider_base_sqlite(args.db, args.langue)
    
    # Génération rapport
    rapport_file = args.rapport or f"rapport_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    validateur.generer_rapport(rapport_file)
    
    # Affichage résumé
    resume = validateur.rapport["resume"]
    logger.info("=" * 50)
    logger.info("RÉSUMÉ VALIDATION")
    logger.info("=" * 50)
    logger.info(f"Statut global: {resume['statut_global']}")
    logger.info(f"Validations: {resume['nb_validations']}")
    logger.info(f"Erreurs: {resume['nb_erreurs']}")
    logger.info(f"Avertissements: {resume['nb_avertissements']}")
    logger.info("=" * 50)
    
    return 0 if succes_global else 1


if __name__ == "__main__":
    sys.exit(main())
