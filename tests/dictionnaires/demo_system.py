#!/usr/bin/env python3
"""
Script de démonstration du système de dictionnaires multilingues Scrabbot.

Ce script démontre le fonctionnement complet du système développé pour le ticket OYO-7.

Il effectue :
1. Conversion des CSV d'exemple en bases SQLite
2. Tests de validation de mots
3. Tests de performance
4. Démonstration de l'API REST

Usage:
    python demo_system.py
"""

import sys
import os
import time
import threading
import subprocess
from pathlib import Path

# Ajout des chemins pour les imports
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "models"))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "api"))
sys.path.append(str(Path(__file__).parent.parent.parent / "data" / "dictionnaires" / "scripts"))

from dictionnaire import DictionnaireService, LangueEnum
from csv_to_sqlite import ConvertisseurCSVSQLite
import requests


class DemoSystemeDictionnaires:
    """Démonstration complète du système de dictionnaires."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data" / "dictionnaires"
        self.sources_dir = self.data_dir / "sources"
        self.databases_dir = self.data_dir / "databases"
        
        # Création des répertoires si nécessaire
        self.databases_dir.mkdir(exist_ok=True)
        
        self.db_fr_path = str(self.databases_dir / "demo_french.db")
        self.db_en_path = str(self.databases_dir / "demo_english.db")
        
        self.service = None
        self.api_server_process = None
    
    def executer_demo(self):
        """Exécute la démonstration complète."""
        print("=" * 60)
        print("🎯 DÉMONSTRATION SYSTÈME DICTIONNAIRES MULTILINGUES")
        print("   Ticket OYO-7 - Scrabbot")
        print("=" * 60)
        
        try:
            # Étape 1 : Conversion CSV → SQLite
            print("\n📊 ÉTAPE 1 : Conversion CSV → SQLite")
            self.demo_conversion_csv()
            
            # Étape 2 : Tests de validation
            print("\n✅ ÉTAPE 2 : Tests de validation des mots")
            self.demo_validation_mots()
            
            # Étape 3 : Tests de performance
            print("\n⚡ ÉTAPE 3 : Tests de performance")
            self.demo_performance()
            
            # Étape 4 : Démonstration API REST
            print("\n🌐 ÉTAPE 4 : Démonstration API REST pour Godot")
            self.demo_api_rest()
            
            print("\n🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS !")
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DE LA DÉMONSTRATION : {e}")
        finally:
            self.nettoyer()
    
    def demo_conversion_csv(self):
        """Démontre la conversion CSV → SQLite."""
        print("  📝 Conversion des fichiers CSV d'exemple...")
        
        convertisseur = ConvertisseurCSVSQLite()
        
        # Conversion français
        csv_fr = str(self.sources_dir / "dictionnaire_fr_exemple.csv")
        if Path(csv_fr).exists():
            succes_fr = convertisseur.convertir_csv_vers_sqlite(
                csv_fr, self.db_fr_path, "fr", "demo-1.0"
            )
            print(f"  ✅ Conversion française : {'✓' if succes_fr else '✗'}")
        else:
            print(f"  ⚠️  Fichier CSV français introuvable : {csv_fr}")
        
        # Conversion anglaise
        csv_en = str(self.sources_dir / "dictionnaire_en_exemple.csv")
        if Path(csv_en).exists():
            succes_en = convertisseur.convertir_csv_vers_sqlite(
                csv_en, self.db_en_path, "en", "demo-1.0"
            )
            print(f"  ✅ Conversion anglaise : {'✓' if succes_en else '✗'}")
        else:
            print(f"  ⚠️  Fichier CSV anglais introuvable : {csv_en}")
        
        # Vérification des bases créées
        if Path(self.db_fr_path).exists():
            taille_fr = Path(self.db_fr_path).stat().st_size / 1024
            print(f"  📁 Base française créée : {taille_fr:.1f} KB")
        
        if Path(self.db_en_path).exists():
            taille_en = Path(self.db_en_path).stat().st_size / 1024
            print(f"  📁 Base anglaise créée : {taille_en:.1f} KB")
    
    def demo_validation_mots(self):
        """Démontre la validation des mots."""
        if not Path(self.db_fr_path).exists() or not Path(self.db_en_path).exists():
            print("  ❌ Bases de données non disponibles pour la validation")
            return
        
        print("  🔍 Initialisation du service de dictionnaires...")
        self.service = DictionnaireService(self.db_fr_path, self.db_en_path)
        
        # Tests français
        print("  \n  🇫🇷 Tests de validation française :")
        mots_test_fr = [
            ("CHAT", True, "Mot simple"),
            ("SCRABBLE", True, "Nom du jeu"),
            ("INEXISTANT", False, "Mot inexistant"),
            ("ÊTRE", True, "Mot avec accent"),
            ("API", True, "Acronyme moderne")
        ]
        
        for mot, attendu, description in mots_test_fr:
            resultat = self.service.valider_mot(mot, LangueEnum.FRANCAIS)
            statut = "✓" if resultat.valide == attendu else "✗"
            temps = f"{resultat.temps_recherche_ms:.1f}ms" if resultat.temps_recherche_ms else "N/A"
            print(f"    {statut} {mot:12} ({description}) - {temps}")
            
            if resultat.valide and resultat.definition:
                print(f"      💬 {resultat.definition[:60]}{'...' if len(resultat.definition) > 60 else ''}")
        
        # Tests anglais
        print("  \n  🇬🇧 Tests de validation anglaise :")
        mots_test_en = [
            ("CAT", True, "Simple word"),
            ("SCRABBLE", True, "Game name"),
            ("NONEXISTENT", False, "Non-existent word"),
            ("API", True, "Modern acronym"),
            ("ENGINE", True, "Technical term")
        ]
        
        for word, attendu, description in mots_test_en:
            resultat = self.service.valider_mot(word, LangueEnum.ANGLAIS)
            statut = "✓" if resultat.valide == attendu else "✗"
            temps = f"{resultat.temps_recherche_ms:.1f}ms" if resultat.temps_recherche_ms else "N/A"
            print(f"    {statut} {word:12} ({description}) - {temps}")
            
            if resultat.valide and resultat.definition:
                print(f"      💬 {resultat.definition[:60]}{'...' if len(resultat.definition) > 60 else ''}")
    
    def demo_performance(self):
        """Démontre les performances du système."""
        if not self.service:
            print("  ❌ Service de dictionnaires non initialisé")
            return
        
        print("  ⏱️  Tests de performance (objectif : < 50ms par recherche)")
        
        # Test de performance individuelle
        mots_perf = ["CHAT", "DOG", "SCRABBLE", "API", "PERFORMANCE"]
        temps_total = []
        
        for mot in mots_perf:
            debut = time.time()
            resultat = self.service.valider_mot(mot, LangueEnum.FRANCAIS)
            temps_ms = (time.time() - debut) * 1000
            temps_total.append(temps_ms)
            
            statut = "🟢" if temps_ms < 50 else "🟡" if temps_ms < 100 else "🔴"
            print(f"    {statut} {mot:12} : {temps_ms:6.2f}ms")
        
        # Statistiques globales
        temps_moyen = sum(temps_total) / len(temps_total)
        temps_max = max(temps_total)
        
        print(f"  \n  📊 Statistiques de performance :")
        print(f"    • Temps moyen    : {temps_moyen:6.2f}ms")
        print(f"    • Temps maximum  : {temps_max:6.2f}ms")
        print(f"    • Objectif       : < 50.00ms")
        print(f"    • Conformité     : {'✅ CONFORME' if temps_moyen < 50 else '⚠️ NON CONFORME'}")
        
        # Test batch (10 mots)
        print(f"  \n  🔄 Test batch (10 mots, objectif : < 200ms)")
        debut_batch = time.time()
        for i in range(10):
            self.service.valider_mot(f"MOT{i:02d}", LangueEnum.FRANCAIS)
        temps_batch = (time.time() - debut_batch) * 1000
        
        statut_batch = "✅ CONFORME" if temps_batch < 200 else "⚠️ NON CONFORME"
        print(f"    • Temps total batch : {temps_batch:6.2f}ms")
        print(f"    • Conformité        : {statut_batch}")
        
        # Statistiques du service
        stats = self.service.obtenir_statistiques_performance()
        print(f"  \n  📈 Statistiques du service :")
        for cle, valeur in stats.items():
            print(f"    • {cle:20} : {valeur}")
    
    def demo_api_rest(self):
        """Démontre l'API REST pour Godot."""
        print("  🚀 Lancement du serveur API REST...")
        
        # Démarrage du serveur en arrière-plan
        try:
            self.demarrer_serveur_api()
            time.sleep(2)  # Attendre que le serveur démarre
            
            # Tests des endpoints
            self.tester_endpoints_api()
            
        except Exception as e:
            print(f"  ❌ Erreur avec l'API REST : {e}")
        finally:
            self.arreter_serveur_api()
    
    def demarrer_serveur_api(self):
        """Démarre le serveur API en arrière-plan."""
        api_script = self.base_dir / "shared" / "api" / "dictionnaire_service.py"
        if not api_script.exists():
            print(f"  ⚠️  Script API introuvable : {api_script}")
            return
        
        # Configuration des variables d'environnement pour les bases de test
        env = os.environ.copy()
        env["SCRABBOT_DB_FR"] = self.db_fr_path
        env["SCRABBOT_DB_EN"] = self.db_en_path
        
        try:
            # Lancement du serveur avec uvicorn
            cmd = [
                sys.executable, "-m", "uvicorn",
                "dictionnaire_service:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--log-level", "warning"
            ]
            
            self.api_server_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir / "shared" / "api"),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("  ✅ Serveur API démarré sur http://127.0.0.1:8000")
            
        except Exception as e:
            print(f"  ❌ Erreur démarrage serveur : {e}")
    
    def tester_endpoints_api(self):
        """Teste les endpoints de l'API."""
        base_url = "http://127.0.0.1:8000/api/v1/dictionnaire"
        
        print("  \n  🌐 Tests des endpoints API :")
        
        # Test health check
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("    ✅ Health check : OK")
                data = response.json()
                print(f"       Statut : {data.get('statut', 'N/A')}")
            else:
                print(f"    ❌ Health check : {response.status_code}")
        except Exception as e:
            print(f"    ❌ Health check : Erreur - {e}")
        
        # Test validation française
        try:
            response = requests.get(f"{base_url}/fr/valider/CHAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Validation FR : CHAT = {data.get('valide', False)}")
                if data.get('temps_recherche_ms'):
                    print(f"       Temps : {data['temps_recherche_ms']:.1f}ms")
            else:
                print(f"    ❌ Validation FR : {response.status_code}")
        except Exception as e:
            print(f"    ❌ Validation FR : Erreur - {e}")
        
        # Test validation anglaise
        try:
            response = requests.get(f"{base_url}/en/valider/CAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Validation EN : CAT = {data.get('valide', False)}")
            else:
                print(f"    ❌ Validation EN : {response.status_code}")
        except Exception as e:
            print(f"    ❌ Validation EN : Erreur - {e}")
        
        # Test définition
        try:
            response = requests.get(f"{base_url}/fr/definition/CHAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                trouve = data.get('trouve', False)
                print(f"    ✅ Définition : CHAT trouvé = {trouve}")
                if trouve and data.get('definition'):
                    def_courte = data['definition'][:40] + "..." if len(data['definition']) > 40 else data['definition']
                    print(f"       Définition : {def_courte}")
            else:
                print(f"    ❌ Définition : {response.status_code}")
        except Exception as e:
            print(f"    ❌ Définition : Erreur - {e}")
        
        # Test recherche
        try:
            response = requests.get(f"{base_url}/fr/recherche?longueur=4&limite=3", timeout=5)
            if response.status_code == 200:
                data = response.json()
                nb_resultats = data.get('nb_resultats', 0)
                print(f"    ✅ Recherche : {nb_resultats} mots de 4 lettres trouvés")
                if data.get('mots') and len(data['mots']) > 0:
                    premier_mot = data['mots'][0].get('mot', 'N/A')
                    print(f"       Premier résultat : {premier_mot}")
            else:
                print(f"    ❌ Recherche : {response.status_code}")
        except Exception as e:
            print(f"    ❌ Recherche : Erreur - {e}")
        
        print(f"  \n  📖 Documentation interactive disponible : http://127.0.0.1:8000/docs")
    
    def arreter_serveur_api(self):
        """Arrête le serveur API."""
        if self.api_server_process:
            print("  🛑 Arrêt du serveur API...")
            self.api_server_process.terminate()
            try:
                self.api_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_server_process.kill()
            self.api_server_process = None
    
    def nettoyer(self):
        """Nettoyage des ressources."""
        if self.service:
            self.service.fermer_connexions()
        
        self.arreter_serveur_api()
        
        print(f"\n🧹 Nettoyage terminé")
        print(f"  • Bases de démonstration conservées dans : {self.databases_dir}")
        print(f"  • Logs disponibles pour analyse")


def main():
    """Point d'entrée principal."""
    print("🎮 Démonstration Système Dictionnaires Multilingues - Scrabbot")
    print("   Développé pour le ticket Linear OYO-7")
    
    # Vérification des dépendances
    try:
        import requests
        import sqlite3
    except ImportError as e:
        print(f"❌ Dépendance manquante : {e}")
        print("💡 Installer avec : pip install requests")
        return 1
    
    # Lancement de la démonstration
    demo = DemoSystemeDictionnaires()
    demo.executer_demo()
    
    return 0


if __name__ == "__main__":
    exit(main())
