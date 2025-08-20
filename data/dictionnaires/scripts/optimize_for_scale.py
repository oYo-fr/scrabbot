#!/usr/bin/env python3
"""
Database optimization for large-scale Scrabble dictionaries.

This script optimizes SQLite databases for handling hundreds of thousands
of dictionary words with maximum performance.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Optimize SQLite databases for large-scale dictionary operations.
    
    Applies advanced indexing, query optimization, and performance tuning
    for databases with 100k+ words.
    """
    
    def __init__(self):
        self.optimization_queries = {
            'performance_settings': [
                "PRAGMA journal_mode = WAL",           # Write-Ahead Logging for better concurrency
                "PRAGMA synchronous = NORMAL",         # Balance between safety and speed  
                "PRAGMA cache_size = 10000",           # 10MB cache
                "PRAGMA temp_store = MEMORY",          # Store temp tables in memory
                "PRAGMA mmap_size = 268435456",        # 256MB memory-mapped I/O
                "PRAGMA page_size = 4096",             # Optimal page size
            ],
            
            'french_indexes': [
                "CREATE INDEX IF NOT EXISTS idx_fr_mot ON mots_fr(mot)",
                "CREATE INDEX IF NOT EXISTS idx_fr_longueur ON mots_fr(longueur)",
                "CREATE INDEX IF NOT EXISTS idx_fr_points ON mots_fr(points)",
                "CREATE INDEX IF NOT EXISTS idx_fr_premiere_lettre ON mots_fr(premiere_lettre)",
                "CREATE INDEX IF NOT EXISTS idx_fr_derniere_lettre ON mots_fr(derniere_lettre)",
                "CREATE INDEX IF NOT EXISTS idx_fr_valide ON mots_fr(valide_scrabble)",
                "CREATE INDEX IF NOT EXISTS idx_fr_composite ON mots_fr(longueur, premiere_lettre)",
                "CREATE INDEX IF NOT EXISTS idx_fr_search ON mots_fr(mot, valide_scrabble, points)",
            ],
            
            'english_indexes': [
                "CREATE INDEX IF NOT EXISTS idx_en_word ON mots_en(word)",
                "CREATE INDEX IF NOT EXISTS idx_en_length ON mots_en(length)",
                "CREATE INDEX IF NOT EXISTS idx_en_points ON mots_en(points)",
                "CREATE INDEX IF NOT EXISTS idx_en_first_letter ON mots_en(first_letter)",
                "CREATE INDEX IF NOT EXISTS idx_en_last_letter ON mots_en(last_letter)",
                "CREATE INDEX IF NOT EXISTS idx_en_valid ON mots_en(scrabble_valid)",
                "CREATE INDEX IF NOT EXISTS idx_en_composite ON mots_en(length, first_letter)",
                "CREATE INDEX IF NOT EXISTS idx_en_search ON mots_en(word, scrabble_valid, points)",
            ],
            
            'optimization_views': [
                # French optimized views
                """CREATE VIEW IF NOT EXISTS v_mots_fr_optimized AS
                   SELECT mot, definition, points, longueur, premiere_lettre, derniere_lettre
                   FROM mots_fr 
                   WHERE valide_scrabble = 1
                   ORDER BY longueur, mot""",
                
                # English optimized views
                """CREATE VIEW IF NOT EXISTS v_mots_en_optimized AS
                   SELECT word, definition, points, length, first_letter, last_letter
                   FROM mots_en 
                   WHERE scrabble_valid = 1
                   ORDER BY length, word""",
                
                # High-value words view
                """CREATE VIEW IF NOT EXISTS v_high_value_words AS
                   SELECT 'fr' as language, mot as word, points, longueur as length
                   FROM mots_fr 
                   WHERE valide_scrabble = 1 AND points >= 10
                   UNION ALL
                   SELECT 'en' as language, word, points, length
                   FROM mots_en 
                   WHERE scrabble_valid = 1 AND points >= 10
                   ORDER BY points DESC""",
            ]
        }
        
        logger.info("Database optimizer initialized")
    
    def optimize_database(self, db_path: str, language: str = None) -> Dict[str, any]:
        """
        Apply comprehensive optimization to a database.
        
        Args:
            db_path: Path to SQLite database
            language: Language code ('fr' or 'en') or None for auto-detect
            
        Returns:
            Optimization results and metrics
        """
        db_path = Path(db_path)
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        logger.info(f"Optimizing database: {db_path}")
        start_time = time.time()
        
        # Detect language if not specified
        if language is None:
            language = self._detect_language(str(db_path))
        
        results = {
            'database': str(db_path),
            'language': language,
            'optimization_start': start_time
        }
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                # 1. Apply performance settings
                logger.info("Applying performance settings...")
                for query in self.optimization_queries['performance_settings']:
                    cursor.execute(query)
                    logger.debug(f"Applied: {query}")
                
                # 2. Create indexes
                logger.info("Creating optimized indexes...")
                index_key = f'{language}_indexes'
                if index_key in self.optimization_queries:
                    for query in self.optimization_queries[index_key]:
                        cursor.execute(query)
                        logger.debug(f"Created index: {query}")
                
                # 3. Create optimization views
                logger.info("Creating optimization views...")
                for query in self.optimization_queries['optimization_views']:
                    cursor.execute(query)
                
                # 4. Analyze database for query optimization
                logger.info("Analyzing database statistics...")
                cursor.execute("ANALYZE")
                
                # 5. Get database statistics
                stats = self._get_database_stats(cursor, language)
                results.update(stats)
                
                # 6. Run VACUUM to optimize storage
                logger.info("Optimizing database storage...")
                conn.commit()
                
            # VACUUM must be done outside transaction
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("VACUUM")
            
            results['optimization_time'] = time.time() - start_time
            results['status'] = 'success'
            
            logger.info(f"Database optimization completed in {results['optimization_time']:.2f}s")
            
        except sqlite3.Error as e:
            logger.error(f"Database optimization failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def benchmark_database(self, db_path: str, iterations: int = 1000) -> Dict[str, any]:
        """
        Benchmark database performance with various queries.
        
        Args:
            db_path: Path to database
            iterations: Number of test iterations
            
        Returns:
            Performance benchmark results
        """
        logger.info(f"Benchmarking database: {db_path}")
        
        # Sample test queries
        test_queries = {
            'word_lookup': [
                "SELECT * FROM mots_fr WHERE mot = 'SCRABBLE' LIMIT 1",
                "SELECT * FROM mots_en WHERE word = 'SCRABBLE' LIMIT 1"
            ],
            'prefix_search': [
                "SELECT mot FROM mots_fr WHERE mot LIKE 'SCRAB%' LIMIT 10",
                "SELECT word FROM mots_en WHERE word LIKE 'SCRAB%' LIMIT 10"
            ],
            'length_filter': [
                "SELECT mot FROM mots_fr WHERE longueur = 7 LIMIT 20",
                "SELECT word FROM mots_en WHERE length = 7 LIMIT 20"
            ],
            'high_score': [
                "SELECT mot, points FROM mots_fr WHERE points >= 15 ORDER BY points DESC LIMIT 10",
                "SELECT word, points FROM mots_en WHERE points >= 15 ORDER BY points DESC LIMIT 10"
            ],
            'letter_filter': [
                "SELECT mot FROM mots_fr WHERE premiere_lettre = 'Q' LIMIT 10",
                "SELECT word FROM mots_en WHERE first_letter = 'Q' LIMIT 10"
            ]
        }
        
        benchmark_results = {
            'database': str(db_path),
            'iterations': iterations,
            'query_results': {}
        }
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                
                # Detect available tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for query_type, queries in test_queries.items():
                    logger.info(f"Benchmarking {query_type} queries...")
                    
                    for query in queries:
                        # Skip query if table doesn't exist
                        table_name = None
                        if 'mots_fr' in query and 'mots_fr' not in tables:
                            continue
                        if 'mots_en' in query and 'mots_en' not in tables:
                            continue
                        
                        # Run benchmark
                        times = []
                        for _ in range(min(iterations, 100)):  # Limit iterations for benchmarking
                            start = time.time()
                            try:
                                cursor.execute(query)
                                results = cursor.fetchall()
                                elapsed = (time.time() - start) * 1000  # Convert to ms
                                times.append(elapsed)
                            except sqlite3.Error:
                                break
                        
                        if times:
                            benchmark_results['query_results'][f"{query_type}_{query[:20]}"] = {
                                'query': query,
                                'avg_time_ms': statistics.mean(times),
                                'min_time_ms': min(times),
                                'max_time_ms': max(times),
                                'median_time_ms': statistics.median(times),
                                'iterations': len(times)
                            }
        
        except sqlite3.Error as e:
            logger.error(f"Benchmark failed: {e}")
            benchmark_results['error'] = str(e)
        
        return benchmark_results
    
    def _detect_language(self, db_path: str) -> str:
        """Detect database language from filename or table structure."""
        path_lower = str(db_path).lower()
        
        if 'french' in path_lower or 'fr' in path_lower or 'ods' in path_lower:
            return 'fr'
        elif 'english' in path_lower or 'en' in path_lower or 'sowpods' in path_lower or 'twl' in path_lower:
            return 'en'
        
        # Check table structure
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'mots_fr' in tables:
                    return 'fr'
                elif 'mots_en' in tables:
                    return 'en'
        except:
            pass
        
        return 'unknown'
    
    def _get_database_stats(self, cursor: sqlite3.Cursor, language: str) -> Dict[str, any]:
        """Get comprehensive database statistics."""
        stats = {}
        
        try:
            # Get table info
            if language == 'fr':
                table_name = 'mots_fr'
                word_col = 'mot'
                length_col = 'longueur'
                points_col = 'points'
            else:
                table_name = 'mots_en'
                word_col = 'word'
                length_col = 'length'
                points_col = 'points'
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                stats['error'] = f"Table {table_name} not found"
                return stats
            
            # Total words
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            stats['total_words'] = cursor.fetchone()[0]
            
            # Average word length
            cursor.execute(f"SELECT AVG({length_col}) FROM {table_name}")
            stats['avg_word_length'] = round(cursor.fetchone()[0] or 0, 2)
            
            # Word length distribution
            cursor.execute(f"SELECT {length_col}, COUNT(*) FROM {table_name} GROUP BY {length_col} ORDER BY {length_col}")
            stats['length_distribution'] = dict(cursor.fetchall())
            
            # Points distribution
            cursor.execute(f"SELECT {points_col}, COUNT(*) FROM {table_name} GROUP BY {points_col} ORDER BY {points_col}")
            stats['points_distribution'] = dict(cursor.fetchall())
            
            # High-value words count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {points_col} >= 15")
            stats['high_value_words'] = cursor.fetchone()[0]
            
            # Database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            stats['database_size_bytes'] = cursor.fetchone()[0]
            stats['database_size_mb'] = round(stats['database_size_bytes'] / 1024 / 1024, 2)
            
        except sqlite3.Error as e:
            stats['stats_error'] = str(e)
        
        return stats
    
    def optimize_all_databases(self, databases_dir: str) -> Dict[str, any]:
        """
        Optimize all databases in a directory.
        
        Args:
            databases_dir: Directory containing database files
            
        Returns:
            Results for all optimizations
        """
        databases_dir = Path(databases_dir)
        
        if not databases_dir.exists():
            raise FileNotFoundError(f"Directory not found: {databases_dir}")
        
        db_files = list(databases_dir.glob("*.db"))
        
        if not db_files:
            logger.warning(f"No database files found in {databases_dir}")
            return {}
        
        logger.info(f"Found {len(db_files)} database files to optimize")
        
        results = {}
        
        for db_file in db_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Optimizing {db_file.name}")
            logger.info(f"{'='*60}")
            
            try:
                result = self.optimize_database(str(db_file))
                results[db_file.name] = result
                
                if result['status'] == 'success':
                    logger.info(f"✅ {db_file.name} optimized successfully")
                    logger.info(f"   Words: {result.get('total_words', 'N/A'):,}")
                    logger.info(f"   Size: {result.get('database_size_mb', 'N/A')} MB")
                    logger.info(f"   Time: {result.get('optimization_time', 'N/A'):.2f}s")
                else:
                    logger.error(f"❌ {db_file.name} optimization failed")
                    
            except Exception as e:
                logger.error(f"❌ {db_file.name} failed with exception: {e}")
                results[db_file.name] = {'status': 'failed', 'error': str(e)}
        
        return results


def main():
    """CLI interface for database optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize Scrabble dictionary databases")
    parser.add_argument('--database', help="Specific database file to optimize")
    parser.add_argument('--directory', default="data/dictionnaires/databases", 
                       help="Directory containing databases")
    parser.add_argument('--benchmark', action='store_true', help="Run performance benchmarks")
    parser.add_argument('--iterations', type=int, default=1000, help="Benchmark iterations")
    
    args = parser.parse_args()
    
    optimizer = DatabaseOptimizer()
    
    if args.database:
        # Optimize single database
        result = optimizer.optimize_database(args.database)
        
        if args.benchmark:
            benchmark = optimizer.benchmark_database(args.database, args.iterations)
            print("\nBenchmark Results:")
            for query_name, metrics in benchmark.get('query_results', {}).items():
                print(f"  {query_name}: {metrics['avg_time_ms']:.3f}ms avg")
        
        if result['status'] == 'success':
            print(f"\n✅ Database optimized successfully!")
            print(f"Words: {result.get('total_words', 'N/A'):,}")
            print(f"Size: {result.get('database_size_mb', 'N/A')} MB")
        else:
            print(f"\n❌ Optimization failed: {result.get('error', 'Unknown error')}")
    
    else:
        # Optimize all databases in directory
        results = optimizer.optimize_all_databases(args.directory)
        
        successful = sum(1 for r in results.values() if r.get('status') == 'success')
        total = len(results)
        
        print(f"\n📊 OPTIMIZATION SUMMARY")
        print(f"{'='*50}")
        print(f"Databases processed: {total}")
        print(f"Successful optimizations: {successful}")
        print(f"Failed optimizations: {total - successful}")
        
        if successful == total:
            print("\n🎉 All databases optimized successfully!")
        else:
            print(f"\n⚠️  {total - successful} optimizations failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
