#!/usr/bin/env python3
"""
Checks the content of created SQLite databases
"""

import sqlite3
from pathlib import Path


def check_database(db_path, language):
    """Checks a database"""
    print(f"\n📊 === DATABASE {language.upper()} : {db_path.name} ===")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"📁 Size: {size_mb:.1f} MB")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Number of words
        cursor.execute("SELECT COUNT(*) FROM words")
        nb_words = cursor.fetchone()[0]

        # Number of definitions
        cursor.execute("SELECT COUNT(*) FROM definitions")
        nb_definitions = cursor.fetchone()[0]

        print(f"📊 Unique words: {nb_words:,}")
        print(f"📊 Total definitions: {nb_definitions:,}")
        print(f"📊 Average definitions/word: {nb_definitions / nb_words:.1f}")

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

        print("\n📋 Top parts of speech:")
        for cat, nb in top_categories:
            print(f"  • {cat}: {nb:,}")

        # Sample words with their definitions
        cursor.execute(
            """
            SELECT w.word_normalized, w.word_original, d.text, d.part_of_speech
            FROM words w
            JOIN definitions d ON w.id = d.word_id
            WHERE LENGTH(w.word_normalized) BETWEEN 5 AND 10
            ORDER BY RANDOM()
            LIMIT 10
        """
        )
        examples = cursor.fetchall()

        print("\n📝 Sample words:")
        for word_norm, word_orig, definition, cat in examples:
            definition_short = (
                definition[:60] + "..." if len(definition) > 60 else definition
            )
            print(f"  • {word_norm} ({word_orig}) [{cat}]")
            print(f"    → {definition_short}")

        # Some statistics on word lengths
        cursor.execute(
            """
            SELECT
                MIN(LENGTH(word_normalized)) as min_len,
                MAX(LENGTH(word_normalized)) as max_len,
                AVG(LENGTH(word_normalized)) as avg_len
            FROM words
        """
        )
        len_stats = cursor.fetchone()
        print("\n📏 Word lengths:")
        print(f"  • Min: {len_stats[0]} characters")
        print(f"  • Max: {len_stats[1]} characters")
        print(f"  • Average: {len_stats[2]:.1f} characters")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        conn.close()


def main():
    """Main function"""
    db_dir = Path(__file__).parent.parent / "databases"

    print("🔍 === DATABASE VERIFICATION ===")

    # Check both databases
    fr_db = db_dir / "fr.db"
    en_db = db_dir / "en.db"

    check_database(fr_db, "French")
    check_database(en_db, "English")

    print("\n✅ Verification completed!")


if __name__ == "__main__":
    main()
