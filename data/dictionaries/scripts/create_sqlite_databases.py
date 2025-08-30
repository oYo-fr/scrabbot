#!/usr/bin/env python3
"""
Creates SQLite databases from WiktionaryX XML files
Automatically downloads the XML files from redac.univ-tlse2.fr if needed
"""

import logging
import re
import sqlite3
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from unidecode import unidecode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WiktionaryDBCreator:
    def __init__(self):
        self.wiktionary_dir = Path(__file__).parent.parent / "wiktionary"
        self.db_dir = Path(__file__).parent.parent / "databases"
        self.db_dir.mkdir(exist_ok=True)
        self.wiktionary_dir.mkdir(exist_ok=True)

        # Download URLs from redac.univ-tlse2.fr
        self.download_urls = {
            "fr": "http://redac.univ-tlse2.fr/lexiques/wiktionaryX/wiktionaryXfr2010.7z",
            "en": "http://redac.univ-tlse2.fr/lexiques/wiktionaryX/wiktionaryXen2010.7z",
        }

        # Part of speech mapping (English)
        self.pos_mapping = {
            "N": "noun",
            "V": "verb",
            "Adj": "adjective",
            "Adv": "adverb",
            "Prep": "preposition",
            "Conj": "conjunction",
            "Pron": "pronoun",
            "Det": "determiner",
            "Intj": "interjection",
            "Art": "article",
        }

    def download_and_extract(self, language):
        """Downloads and extracts the 7z file for the given language"""
        url = self.download_urls[language]
        archive_path = self.wiktionary_dir / f"wiktionaryX{language}2010.7z"
        xml_path = self.wiktionary_dir / f"wiktionaryX{language}2010.xml"

        # Check if XML file already exists
        if xml_path.exists():
            logger.info(f"✅ XML file already exists: {xml_path}")
            return xml_path

        logger.info(f"📥 Downloading {language.upper()} WiktionaryX from {url}...")

        try:
            # Download the 7z file
            urllib.request.urlretrieve(url, archive_path)
            logger.info(f"✅ Downloaded: {archive_path}")

            # Extract the 7z file
            logger.info(f"📦 Extracting {archive_path}...")
            result = subprocess.run(
                [
                    "7z",
                    "x",
                    str(archive_path),
                    f"-o{self.wiktionary_dir}",
                    "-y",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"❌ Failed to extract {archive_path}: {result.stderr}")
                return None

            logger.info(f"✅ Extracted: {xml_path}")

            # Clean up the 7z file
            archive_path.unlink()
            logger.info(f"🗑️ Cleaned up: {archive_path}")

            return xml_path

        except Exception as e:
            logger.error(f"❌ Error downloading/extracting {language}: {e}")
            return None

    def normalize_word(self, word):
        """Normalizes a word: uppercase, no accents"""
        if not word:
            return ""

        # Remove accents and convert to uppercase
        normalized = unidecode(word.strip()).upper()
        return normalized

    def is_valid_word(self, word):
        """Checks if a word meets import criteria"""
        if not word:
            return False

        # Only keep alphabetic characters
        if not re.match(r"^[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÑÇ]+$", word.upper(), re.IGNORECASE):
            return False

        # No digits
        if re.search(r"\d", word):
            return False

        # No special characters (hyphens, apostrophes, etc.)
        if re.search(r'[-\'.,;:!?()\[\]{}"\s]', word):
            return False

        # Not too short
        if len(word) < 2:
            return False

        # Not too long (probably compound or error)
        if len(word) > 25:
            return False

        return True

    def clean_text(self, text):
        """Cleans definition text"""
        if not text:
            return ""

        # Remove remaining HTML/XML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
        # Normalize spaces
        text = re.sub(r"\s+", " ", text).strip()
        # Remove strange HTML entities
        text = text.replace("&amp;lt;!--", "").replace("--&amp;gt;", "")
        text = text.replace("&amp;", "&")

        return text

    def extract_definition(self, defs_element):
        """Extracts definitions from a defs element"""
        definitions = []

        for toplevel_def in defs_element.findall(".//toplevel-def"):
            gloss = toplevel_def.find("gloss")
            if gloss is not None and gloss.text:
                definition = self.clean_text(gloss.text)
                if definition and len(definition) > 10:  # Substantial definitions
                    definitions.append(definition)

        return definitions

    def create_database_schema(self, db_path):
        """Creates the database schema"""
        logger.info(f"🗄️ Creating schema: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Words table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_normalized TEXT UNIQUE NOT NULL,
                word_original TEXT NOT NULL
            )
        """
        )

        # Index on normalized word
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_word_normalized ON words(word_normalized)
        """
        )

        # Definitions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                part_of_speech TEXT NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words (id)
            )
        """
        )

        # Index on word_id
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_definitions_word_id ON definitions(word_id)
        """
        )

        conn.commit()
        conn.close()

        logger.info(f"✅ Schema created: {db_path}")

    def process_xml_to_db(self, xml_file, db_path, language):
        """Parses XML and creates database"""
        logger.info(f"🔍 Processing: {xml_file} → {db_path}")

        if not xml_file.exists():
            logger.error(f"❌ XML file not found: {xml_file}")
            return False

        # Create schema
        self.create_database_schema(db_path)

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Statistics
        total_entries = 0
        valid_words = 0
        total_definitions = 0

        try:
            # Parse XML iteratively
            context = ET.iterparse(xml_file, events=("start", "end"))
            context = iter(context)
            event, root = next(context)

            for event, elem in context:
                if event == "end" and elem.tag == "entry":
                    total_entries += 1

                    if total_entries % 50000 == 0:
                        logger.info(f"📊 Processed {total_entries:,} entries...")

                    # Extract word
                    word_original = elem.get("form", "").strip()
                    if not word_original:
                        root.clear()
                        continue

                    # Check validity
                    if not self.is_valid_word(word_original):
                        root.clear()
                        continue

                    # Normalize
                    word_normalized = self.normalize_word(word_original)
                    if not word_normalized:
                        root.clear()
                        continue

                    # Insert or get word
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO words (word_normalized, word_original)
                        VALUES (?, ?)
                    """,
                        (word_normalized, word_original),
                    )

                    cursor.execute(
                        """
                        SELECT id FROM words WHERE word_normalized = ?
                    """,
                        (word_normalized,),
                    )

                    word_id = cursor.fetchone()
                    if not word_id:
                        root.clear()
                        continue

                    word_id = word_id[0]
                    word_added = False

                    # Process all lexemes
                    for lexeme in elem.findall(".//lexeme"):
                        pos_code = lexeme.get("pos", "").strip()
                        pos = self.pos_mapping.get(
                            pos_code,
                            pos_code.lower() if pos_code else "unknown",
                        )

                        # Extract definitions
                        defs_element = lexeme.find("defs")
                        if defs_element is not None:
                            definitions = self.extract_definition(defs_element)

                            for definition in definitions:
                                # Insert definition
                                cursor.execute(
                                    """
                                    INSERT INTO definitions (word_id, text, part_of_speech)
                                    VALUES (?, ?, ?)
                                """,
                                    (word_id, definition, pos),
                                )

                                total_definitions += 1
                                word_added = True

                    if word_added:
                        valid_words += 1

                    # Regular commit
                    if total_entries % 10000 == 0:
                        conn.commit()

                    # Free memory
                    root.clear()

            # Final commit
            conn.commit()

            logger.info(f"✅ Processing completed: {language}")
            logger.info(f"📊 XML entries processed: {total_entries:,}")
            logger.info(f"📊 Valid words imported: {valid_words:,}")
            logger.info(f"📊 Definitions created: {total_definitions:,}")

        except Exception as e:
            logger.error(f"❌ Error during processing: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()

        return True

    def analyze_database(self, db_path, language):
        """Analyzes the created database"""
        logger.info(f"📊 Analyzing {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Number of words
            cursor.execute("SELECT COUNT(*) FROM words")
            nb_words = cursor.fetchone()[0]

            # Number of definitions
            cursor.execute("SELECT COUNT(*) FROM definitions")
            nb_definitions = cursor.fetchone()[0]

            # Top 10 parts of speech
            cursor.execute(
                """
                SELECT part_of_speech, COUNT(*) as nb
                FROM definitions
                GROUP BY part_of_speech
                ORDER BY nb DESC
                LIMIT 10
            """
            )
            top_categories = cursor.fetchall()

            # Sample words
            cursor.execute(
                """
                SELECT w.word_normalized, w.word_original, d.text, d.part_of_speech
                FROM words w
                JOIN definitions d ON w.id = d.word_id
                LIMIT 5
            """
            )
            examples = cursor.fetchall()

            logger.info(f"\n📊 === STATISTICS {language.upper()} ===")
            logger.info(f"📁 Database: {db_path.name}")
            logger.info(f"📊 Unique words: {nb_words:,}")
            logger.info(f"📊 Total definitions: {nb_definitions:,}")
            logger.info(f"📊 Average definitions/word: {nb_definitions/nb_words:.1f}")

            logger.info(f"\n📋 Top parts of speech:")
            for cat, nb in top_categories:
                logger.info(f"  • {cat}: {nb:,}")

            logger.info(f"\n📝 Sample words:")
            for word_norm, word_orig, definition, cat in examples:
                definition_short = definition[:80] + "..." if len(definition) > 80 else definition
                logger.info(f"  • {word_norm} ({word_orig}) [{cat}]: {definition_short}")

        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")

        finally:
            conn.close()

    def process_language(self, language):
        """Processes a specific language"""
        if language == "fr":
            xml_file = self.wiktionary_dir / "wiktionaryXfr2010.xml"
            db_file = self.db_dir / "fr.db"
        elif language == "en":
            xml_file = self.wiktionary_dir / "wiktionaryXen2010.xml"
            db_file = self.db_dir / "en.db"
        else:
            logger.error(f"❌ Unsupported language: {language}")
            return False

        # Download and extract if XML doesn't exist
        if not xml_file.exists():
            xml_file = self.download_and_extract(language)
            if not xml_file:
                logger.error(f"❌ Failed to download/extract {language} XML")
                return False

        # Remove old database if exists
        if db_file.exists():
            db_file.unlink()
            logger.info(f"🗑️ Old database removed: {db_file}")

        # Process XML to database
        success = self.process_xml_to_db(xml_file, db_file, language)

        if success:
            # Analyze created database
            self.analyze_database(db_file, language)

        return success


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Creates SQLite databases from WiktionaryX XML files")
    parser.add_argument(
        "--language",
        choices=["fr", "en", "both"],
        default="both",
        help="Language to process (default: both)",
    )

    args = parser.parse_args()

    logger.info("🚀 === CREATING SQLITE DATABASES ===")
    logger.info("📥 Will auto-download XML files from redac.univ-tlse2.fr if needed")

    creator = WiktionaryDBCreator()

    success = True

    if args.language in ["fr", "both"]:
        logger.info("\n🇫🇷 === PROCESSING FRENCH ===")
        if not creator.process_language("fr"):
            success = False

    if args.language in ["en", "both"]:
        logger.info("\n🇺🇸 === PROCESSING ENGLISH ===")
        if not creator.process_language("en"):
            success = False

    if success:
        logger.info("\n🎉 === DATABASES CREATED SUCCESSFULLY ===")
        logger.info("📁 SQLite databases created in data/dictionaries/databases/")
    else:
        logger.error("\n❌ === ERRORS DURING CREATION ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
