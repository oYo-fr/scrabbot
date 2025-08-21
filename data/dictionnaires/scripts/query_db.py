#!/usr/bin/env python3
"""
Utility script to query dictionary SQLite databases
"""

import sqlite3
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

class DictionaryQuery:
    def __init__(self, language: str):
        self.language = language.lower()
        self.db_path = Path(__file__).parent.parent / "databases" / f"{self.language}.db"

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def connect(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_path)

    def search_word(self, word: str) -> List[Tuple]:
        """Search for a specific word"""
        word_normalized = word.upper().strip()

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT w.word_normalized, w.word_original, d.text, d.part_of_speech
            FROM words w
            JOIN definitions d ON w.id = d.word_id
            WHERE w.word_normalized = ?
            ORDER BY d.part_of_speech
        ''', (word_normalized,))

        results = cursor.fetchall()
        conn.close()

        return results

    def search_pattern(self, pattern: str, limit: int = 20) -> List[Tuple]:
        """Search for words with a pattern (uses LIKE)"""
        pattern_normalized = pattern.upper().strip()

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT w.word_normalized, w.word_original
            FROM words w
            WHERE w.word_normalized LIKE ?
            ORDER BY w.word_normalized
            LIMIT ?
        ''', (pattern_normalized, limit))

        results = cursor.fetchall()
        conn.close()

        return results

    def random_words(self, count: int = 10) -> List[Tuple]:
        """Get random words with their definitions"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT w.word_normalized, w.word_original, d.text, d.part_of_speech
            FROM words w
            JOIN definitions d ON w.id = d.word_id
            WHERE LENGTH(w.word_normalized) BETWEEN 4 AND 12
            ORDER BY RANDOM()
            LIMIT ?
        ''', (count,))

        results = cursor.fetchall()
        conn.close()

        return results

    def stats(self) -> dict:
        """Get database statistics"""
        conn = self.connect()
        cursor = conn.cursor()

        # Number of words
        cursor.execute("SELECT COUNT(*) FROM words")
        nb_words = cursor.fetchone()[0]

        # Number of definitions
        cursor.execute("SELECT COUNT(*) FROM definitions")
        nb_definitions = cursor.fetchone()[0]

        # Top categories
        cursor.execute('''
            SELECT part_of_speech, COUNT(*) as nb
            FROM definitions
            GROUP BY part_of_speech
            ORDER BY nb DESC
            LIMIT 10
        ''')
        top_categories = cursor.fetchall()

        # Lengths
        cursor.execute('''
            SELECT
                MIN(LENGTH(word_normalized)) as min_len,
                MAX(LENGTH(word_normalized)) as max_len,
                AVG(LENGTH(word_normalized)) as avg_len
            FROM words
        ''')
        len_stats = cursor.fetchone()

        conn.close()

        return {
            'nb_words': nb_words,
            'nb_definitions': nb_definitions,
            'top_categories': top_categories,
            'len_stats': len_stats
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Query dictionary databases")
    parser.add_argument('--language', '-l', choices=['fr', 'en'], default='fr',
                        help='Database language (default: fr)')
    parser.add_argument('--word', '-w', type=str,
                        help='Search for a specific word')
    parser.add_argument('--pattern', '-p', type=str,
                        help='Search with a pattern (ex: "CHAT*")')
    parser.add_argument('--random', '-r', type=int, metavar='N', default=0,
                        help='Show N random words')
    parser.add_argument('--stats', '-s', action='store_true',
                        help='Show database statistics')
    parser.add_argument('--limit', type=int, default=20,
                        help='Limit for results (default: 20)')

    args = parser.parse_args()

    try:
        db = DictionaryQuery(args.language)

        if args.stats:
            print(f"\n📊 === STATISTICS {args.language.upper()} ===")
            stats = db.stats()
            print(f"📊 Unique words: {stats['nb_words']:,}")
            print(f"📊 Total definitions: {stats['nb_definitions']:,}")
            print(f"📊 Average definitions/word: {stats['nb_definitions']/stats['nb_words']:.1f}")

            print(f"\n📋 Top parts of speech:")
            for cat, nb in stats['top_categories']:
                print(f"  • {cat}: {nb:,}")

            len_stats = stats['len_stats']
            print(f"\n📏 Word lengths:")
            print(f"  • Min: {len_stats[0]} characters")
            print(f"  • Max: {len_stats[1]} characters")
            print(f"  • Average: {len_stats[2]:.1f} characters")

        elif args.word:
            results = db.search_word(args.word)
            if results:
                print(f"\n🔍 === DEFINITIONS OF '{args.word.upper()}' ===")
                for word_norm, word_orig, definition, cat in results:
                    print(f"\n🔸 {word_norm} ({word_orig}) [{cat}]")
                    # Limit definition length for display
                    if len(definition) > 100:
                        definition = definition[:100] + "..."
                    print(f"   → {definition}")
            else:
                print(f"❌ Word '{args.word}' not found in {args.language} database")

        elif args.pattern:
            pattern = args.pattern.replace('*', '%').replace('?', '_')
            results = db.search_pattern(pattern, args.limit)
            if results:
                print(f"\n🔍 === WORDS MATCHING '{args.pattern}' ===")
                for i, (word_norm, word_orig) in enumerate(results, 1):
                    print(f"{i:2d}. {word_norm} ({word_orig})")
            else:
                print(f"❌ No words found for pattern '{args.pattern}'")

        elif args.random > 0:
            results = db.random_words(args.random)
            print(f"\n🎲 === {args.random} RANDOM WORDS ===")
            for i, (word_norm, word_orig, definition, cat) in enumerate(results, 1):
                if len(definition) > 80:
                    definition = definition[:80] + "..."
                print(f"{i:2d}. {word_norm} ({word_orig}) [{cat}]")
                print(f"    → {definition}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()