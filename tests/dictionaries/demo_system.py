#!/usr/bin/env python3
"""
Demonstration script for Scrabbot multilingual dictionaries system.

This script demonstrates the complete operation of the system developed for ticket OYO-7.

It performs:
1. Conversion of example CSV files to SQLite databases
2. Word validation tests
3. Performance tests
4. REST API demonstration

Usage:
    python demo_system.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "models"))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "api"))
sys.path.append(str(Path(__file__).parent.parent.parent / "data" / "dictionaries" / "scripts"))

import requests
from csv_to_sqlite import CSVToSQLiteConverter
from dictionary import DictionaryService, LanguageEnum


class DictionarySystemDemo:
    """Complete demonstration of the dictionary system."""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data" / "dictionaries"
        self.sources_dir = self.data_dir / "sources"
        self.databases_dir = self.data_dir / "databases"

        # Create directories if necessary
        self.databases_dir.mkdir(exist_ok=True)

        self.db_fr_path = str(self.databases_dir / "demo_french.db")
        self.db_en_path = str(self.databases_dir / "demo_english.db")

        self.service = None
        self.api_server_process = None

    def run_demo(self):
        """Runs the complete demonstration."""
        print("=" * 60)
        print("🎯 MULTILINGUAL DICTIONARY SYSTEM DEMONSTRATION")
        print("   Ticket OYO-7 - Scrabbot")
        print("=" * 60)

        try:
            # Step 1: CSV to SQLite conversion
            print("\n📊 STEP 1: CSV to SQLite conversion")
            self.demo_csv_conversion()

            # Step 2: Validation tests
            print("\n✅ STEP 2: Word validation tests")
            self.demo_word_validation()

            # Step 3: Performance tests
            print("\n⚡ STEP 3: Performance tests")
            self.demo_performance()

            # Step 4: REST API demonstration
            print("\n🌐 STEP 4: REST API demonstration for Godot")
            self.demo_rest_api()

            print("\n🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")

        except Exception as e:
            print(f"\n❌ ERROR DURING DEMONSTRATION: {e}")
        finally:
            self.cleanup()

    def demo_csv_conversion(self):
        """Demonstrates CSV to SQLite conversion."""
        print("  📝 Converting example CSV files...")

        converter = CSVToSQLiteConverter()

        # French conversion
        csv_fr = str(self.sources_dir / "dictionnaire_fr_exemple.csv")
        if Path(csv_fr).exists():
            success_fr = converter.convert_csv_to_sqlite(csv_fr, self.db_fr_path, "fr", "demo-1.0")
            print(f"  ✅ French conversion: {'✓' if success_fr else '✗'}")
        else:
            print(f"  ⚠️  French CSV file not found: {csv_fr}")

        # English conversion
        csv_en = str(self.sources_dir / "dictionnaire_en_exemple.csv")
        if Path(csv_en).exists():
            success_en = converter.convert_csv_to_sqlite(csv_en, self.db_en_path, "en", "demo-1.0")
            print(f"  ✅ English conversion: {'✓' if success_en else '✗'}")
        else:
            print(f"  ⚠️  English CSV file not found: {csv_en}")

        # Verify created databases
        if Path(self.db_fr_path).exists():
            size_fr = Path(self.db_fr_path).stat().st_size / 1024
            print(f"  📁 French database created: {size_fr:.1f} KB")

        if Path(self.db_en_path).exists():
            size_en = Path(self.db_en_path).stat().st_size / 1024
            print(f"  📁 English database created: {size_en:.1f} KB")

    def demo_word_validation(self):
        """Demonstrates word validation."""
        if not Path(self.db_fr_path).exists() or not Path(self.db_en_path).exists():
            print("  ❌ Databases not available for validation")
            return

        print("  🔍 Initializing dictionary service...")
        self.service = DictionaryService(self.db_fr_path, self.db_en_path)

        # French tests
        print("  \n  🇫🇷 French validation tests:")
        test_words_fr = [
            ("CHAT", True, "Simple word"),
            ("SCRABBLE", True, "Game name"),
            ("NONEXISTENT", False, "Non-existent word"),
            ("ÊTRE", True, "Word with accent"),
            ("API", True, "Modern acronym"),
        ]

        for word, expected, description in test_words_fr:
            result = self.service.validate_word(word, LanguageEnum.FRENCH)
            status = "✓" if result.is_valid == expected else "✗"
            time_ms = f"{result.search_time_ms:.1f}ms" if result.search_time_ms else "N/A"
            print(f"    {status} {word:12} ({description}) - {time_ms}")

            if result.is_valid and result.definition:
                print(f"      💬 {result.definition[:60]}{'...' if len(result.definition) > 60 else ''}")

        # English tests
        print("  \n  🇬🇧 English validation tests:")
        test_words_en = [
            ("CAT", True, "Simple word"),
            ("SCRABBLE", True, "Game name"),
            ("NONEXISTENT", False, "Non-existent word"),
            ("API", True, "Modern acronym"),
            ("ENGINE", True, "Technical term"),
        ]

        for word, expected, description in test_words_en:
            result = self.service.validate_word(word, LanguageEnum.ENGLISH)
            status = "✓" if result.is_valid == expected else "✗"
            time_ms = f"{result.search_time_ms:.1f}ms" if result.search_time_ms else "N/A"
            print(f"    {status} {word:12} ({description}) - {time_ms}")

            if result.is_valid and result.definition:
                print(f"      💬 {result.definition[:60]}{'...' if len(result.definition) > 60 else ''}")

    def demo_performance(self):
        """Demonstrates system performance."""
        if not self.service:
            print("  ❌ Dictionary service not initialized")
            return

        print("  ⏱️  Performance tests (target: < 50ms per search)")

        # Individual performance test
        perf_words = ["CHAT", "DOG", "SCRABBLE", "API", "PERFORMANCE"]
        total_times = []

        for word in perf_words:
            start = time.time()
            self.service.validate_word(word, LanguageEnum.FRENCH)
            time_ms = (time.time() - start) * 1000
            total_times.append(time_ms)

            status = "🟢" if time_ms < 50 else "🟡" if time_ms < 100 else "🔴"
            print(f"    {status} {word:12} : {time_ms:6.2f}ms")

        # Global statistics
        avg_time = sum(total_times) / len(total_times)
        max_time = max(total_times)

        print("  \n  📊 Performance statistics:")
        print(f"    • Average time   : {avg_time:6.2f}ms")
        print(f"    • Maximum time   : {max_time:6.2f}ms")
        print("    • Target         : < 50.00ms")
        print(f"    • Compliance     : {'✅ COMPLIANT' if avg_time < 50 else '⚠️ NON-COMPLIANT'}")

        # Batch test (10 words)
        print("  \n  🔄 Batch test (10 words, target: < 200ms)")
        batch_start = time.time()
        for i in range(10):
            self.service.validate_word(f"WORD{i:02d}", LanguageEnum.FRENCH)
        batch_time = (time.time() - batch_start) * 1000

        batch_status = "✅ COMPLIANT" if batch_time < 200 else "⚠️ NON-COMPLIANT"
        print(f"    • Total batch time  : {batch_time:6.2f}ms")
        print(f"    • Compliance        : {batch_status}")

        # Service statistics
        stats = self.service.get_performance_statistics()
        print("  \n  📈 Service statistics:")
        for key, value in stats.items():
            print(f"    • {key:20} : {value}")

    def demo_rest_api(self):
        """Demonstrates the REST API for Godot."""
        print("  🚀 Starting REST API server...")

        # Start server in background
        try:
            self.start_api_server()
            time.sleep(2)  # Wait for server to start

            # Test endpoints
            self.test_api_endpoints()

        except Exception as e:
            print(f"  ❌ Error with REST API: {e}")
        finally:
            self.stop_api_server()

    def start_api_server(self):
        """Start the API server in background."""
        api_script = self.base_dir / "shared" / "api" / "dictionary_service.py"
        if not api_script.exists():
            print(f"  ⚠️  API script not found: {api_script}")
            return

        # Configure environment variables for test databases
        env = os.environ.copy()
        env["SCRABBOT_DB_FR"] = self.db_fr_path
        env["SCRABBOT_DB_EN"] = self.db_en_path

        try:
            # Launch server with uvicorn
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "dictionary_service:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--log-level",
                "warning",
            ]

            self.api_server_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir / "shared" / "api"),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print("  ✅ API server started on http://127.0.0.1:8000")

        except Exception as e:
            print(f"  ❌ Server startup error: {e}")

    def test_api_endpoints(self):
        """Test the API endpoints."""
        base_url = "http://127.0.0.1:8000/api/v1/dictionnaire"

        print("  \n  🌐 API endpoints testing:")

        # Test health check
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("    ✅ Health check: OK")
                data = response.json()
                print(f"       Status: {data.get('statut', 'N/A')}")
            else:
                print(f"    ❌ Health check: {response.status_code}")
        except Exception as e:
            print(f"    ❌ Health check: Error - {e}")

        # Test French validation
        try:
            response = requests.get(f"{base_url}/fr/valider/CHAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ French validation: CHAT = {data.get('valide', False)}")
                if data.get("search_time_ms"):
                    print(f"       Time: {data['search_time_ms']:.1f}ms")
            else:
                print(f"    ❌ French validation: {response.status_code}")
        except Exception as e:
            print(f"    ❌ French validation: Error - {e}")

        # Test English validation
        try:
            response = requests.get(f"{base_url}/en/valider/CAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ English validation: CAT = {data.get('valide', False)}")
            else:
                print(f"    ❌ English validation: {response.status_code}")
        except Exception as e:
            print(f"    ❌ English validation: Error - {e}")

        # Test definition
        try:
            response = requests.get(f"{base_url}/fr/definition/CHAT", timeout=5)
            if response.status_code == 200:
                data = response.json()
                found = data.get("trouve", False)
                print(f"    ✅ Definition: CHAT found = {found}")
                if found and data.get("definition"):
                    short_def = data["definition"][:40] + "..." if len(data["definition"]) > 40 else data["definition"]
                    print(f"       Definition: {short_def}")
            else:
                print(f"    ❌ Definition: {response.status_code}")
        except Exception as e:
            print(f"    ❌ Definition: Error - {e}")

        # Test search
        try:
            response = requests.get(f"{base_url}/fr/recherche?longueur=4&limite=3", timeout=5)
            if response.status_code == 200:
                data = response.json()
                results_count = data.get("nb_resultats", 0)
                print(f"    ✅ Search: {results_count} 4-letter words found")
                if data.get("mots") and len(data["mots"]) > 0:
                    first_word = data["mots"][0].get("mot", "N/A")
                    print(f"       First result: {first_word}")
            else:
                print(f"    ❌ Search: {response.status_code}")
        except Exception as e:
            print(f"    ❌ Search: Error - {e}")

        print("  \n  📖 Interactive documentation available: http://127.0.0.1:8000/docs")

    def stop_api_server(self):
        """Stop the API server."""
        if self.api_server_process:
            print("  🛑 Stopping API server...")
            self.api_server_process.terminate()
            try:
                self.api_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_server_process.kill()
            self.api_server_process = None

    def cleanup(self):
        """Resource cleanup."""
        if self.service:
            self.service.close_connections()

        self.stop_api_server()

        print("\n🧹 Cleanup completed")
        print(f"  • Demo databases preserved in: {self.databases_dir}")
        print("  • Logs available for analysis")


def main():
    """Main entry point."""
    print("🎮 Multilingual Dictionary System Demonstration - Scrabbot")
    print("   Developed for Linear ticket OYO-7")

    # Dependency verification
    try:
        pass

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install with: pip install requests")
        return 1

    # Launch demonstration
    demo = DictionarySystemDemo()
    demo.run_demo()

    return 0


if __name__ == "__main__":
    exit(main())
