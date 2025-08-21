#!/usr/bin/env python3
"""
Dictionary analytics and statistics system for Scrabbot.

This module provides:
- Comprehensive dictionary statistics
- Word frequency analysis
- Letter distribution analysis
- Scrabble strategy insights
- Performance analytics
"""

import logging
import sqlite3
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
import statistics

logger = logging.getLogger(__name__)


@dataclass
class LanguageStatistics:
    """Complete statistics for a language dictionary."""
    language_code: str
    total_words: int
    average_word_length: float
    letter_frequency: Dict[str, float]
    length_distribution: Dict[int, int]
    point_distribution: Dict[int, int]
    most_common_words: List[Tuple[str, int]]
    highest_scoring_words: List[Tuple[str, int]]
    letter_rarity: Dict[str, float]
    scrabble_insights: Dict[str, Any]


@dataclass
class WordPattern:
    """Analysis of word patterns and formations."""
    pattern: str
    count: int
    examples: List[str]
    average_points: float


@dataclass
class ScrabbleStrategy:
    """Strategic insights for Scrabble gameplay."""
    high_value_short_words: List[Tuple[str, int]]
    common_prefixes: List[Tuple[str, int]]
    common_suffixes: List[Tuple[str, int]]
    vowel_heavy_words: List[str]
    consonant_clusters: List[str]
    seven_letter_words: List[str]
    q_without_u_words: List[str]


class DictionaryAnalytics:
    """
    Comprehensive analytics engine for dictionary analysis.
    
    Provides detailed statistics, patterns, and strategic insights
    for both French and English Scrabble dictionaries.
    """
    
    def __init__(self, french_db_path: str, english_db_path: str):
        self.french_db_path = french_db_path
        self.english_db_path = english_db_path
        self.analytics_cache: Dict[str, Any] = {}
        self.last_analysis_time: Dict[str, float] = {}
        
        logger.info("Dictionary analytics engine initialized")
    
    def analyze_language_statistics(self, language: str, force_refresh: bool = False) -> LanguageStatistics:
        """
        Generate comprehensive statistics for a language.
        
        Args:
            language: Language code ('fr' or 'en')
            force_refresh: Force regeneration of cached statistics
            
        Returns:
            Complete language statistics
        """
        cache_key = f"lang_stats_{language}"
        
        # Check cache
        if not force_refresh and cache_key in self.analytics_cache:
            cache_age = time.time() - self.last_analysis_time.get(cache_key, 0)
            if cache_age < 3600:  # Cache for 1 hour
                return self.analytics_cache[cache_key]
        
        logger.info(f"Analyzing {language} dictionary statistics")
        start_time = time.time()
        
        db_path = self.french_db_path if language == 'fr' else self.english_db_path
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Determine table name based on language
                table_name = "mots_fr" if language == 'fr' else "mots_en"
                word_col = "mot" if language == 'fr' else "word"
                
                # Basic statistics
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_words = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT AVG(longueur) FROM {table_name}" if language == 'fr' 
                              else f"SELECT AVG(length) FROM {table_name}")
                avg_length = cursor.fetchone()[0] or 0.0
                
                # Get all words with metadata
                cursor.execute(f"""
                    SELECT {word_col}, points, longueur as length, 
                           premiere_lettre as first_letter, derniere_lettre as last_letter
                    FROM {table_name}
                """ if language == 'fr' else f"""
                    SELECT word, points, length, first_letter, last_letter
                    FROM {table_name}
                """)
                
                words_data = cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Database error analyzing {language}: {e}")
            return self._create_empty_statistics(language)
        
        # Analyze collected data
        letter_counts = defaultdict(int)
        length_dist = defaultdict(int)
        point_dist = defaultdict(int)
        all_words = []
        
        total_letters = 0
        
        for word, points, length, first_letter, last_letter in words_data:
            all_words.append((word, points))
            length_dist[length] += 1
            point_dist[points] += 1
            
            # Count letters
            for letter in word:
                letter_counts[letter.upper()] += 1
                total_letters += 1
        
        # Calculate letter frequencies
        letter_frequency = {
            letter: count / total_letters for letter, count in letter_counts.items()
        }
        
        # Sort words by different criteria
        most_common = Counter([word for word, _ in all_words]).most_common(20)
        highest_scoring = sorted(all_words, key=lambda x: x[1], reverse=True)[:20]
        
        # Calculate letter rarity (inverse frequency)
        max_freq = max(letter_frequency.values()) if letter_frequency else 1.0
        letter_rarity = {
            letter: max_freq / freq for letter, freq in letter_frequency.items()
        }
        
        # Generate Scrabble insights
        scrabble_insights = self._generate_scrabble_insights(words_data, language)
        
        # Create statistics object
        stats = LanguageStatistics(
            language_code=language,
            total_words=total_words,
            average_word_length=round(avg_length, 2),
            letter_frequency=letter_frequency,
            length_distribution=dict(length_dist),
            point_distribution=dict(point_dist),
            most_common_words=most_common,
            highest_scoring_words=highest_scoring,
            letter_rarity=letter_rarity,
            scrabble_insights=scrabble_insights
        )
        
        # Cache results
        self.analytics_cache[cache_key] = stats
        self.last_analysis_time[cache_key] = time.time()
        
        elapsed_time = time.time() - start_time
        logger.info(f"{language} analysis completed in {elapsed_time:.2f}s")
        
        return stats
    
    def _generate_scrabble_insights(self, words_data: List[Tuple], language: str) -> Dict[str, Any]:
        """Generate Scrabble-specific strategic insights."""
        insights = {}
        
        # High-value short words (2-4 letters, high points)
        short_high_value = [
            (word, points) for word, points, length, _, _ in words_data
            if 2 <= length <= 4 and points >= 8
        ]
        short_high_value.sort(key=lambda x: x[1], reverse=True)
        insights["high_value_short_words"] = short_high_value[:15]
        
        # Seven-letter words (for bingo bonus)
        seven_letter = [word for word, _, length, _, _ in words_data if length == 7]
        insights["seven_letter_words_count"] = len(seven_letter)
        insights["seven_letter_sample"] = seven_letter[:20]
        
        # Q without U words (rare but valuable)
        q_without_u = [
            word for word, _, _, _, _ in words_data 
            if 'Q' in word and 'U' not in word
        ]
        insights["q_without_u_words"] = q_without_u
        
        # Vowel-heavy words (useful for vowel-heavy racks)
        vowel_heavy = []
        vowels = set('AEIOU')
        for word, points, length, _, _ in words_data:
            vowel_count = sum(1 for char in word if char in vowels)
            if length > 3 and vowel_count / length > 0.6:
                vowel_heavy.append((word, vowel_count, points))
        
        vowel_heavy.sort(key=lambda x: (x[1], x[2]), reverse=True)
        insights["vowel_heavy_words"] = vowel_heavy[:20]
        
        # Words ending in common suffixes
        common_endings = ['-ING', '-TION', '-ED', '-ER', '-LY'] if language == 'en' else ['-TION', '-MENT', '-ABLE', '-IQUE']
        ending_analysis = {}
        
        for ending in common_endings:
            suffix = ending[1:]  # Remove dash
            matching_words = [
                word for word, _, _, _, _ in words_data 
                if word.endswith(suffix)
            ]
            ending_analysis[ending] = {
                "count": len(matching_words),
                "examples": matching_words[:10]
            }
        
        insights["suffix_analysis"] = ending_analysis
        
        # Letter combination frequency
        bigrams = defaultdict(int)
        trigrams = defaultdict(int)
        
        for word, _, _, _, _ in words_data:
            if len(word) >= 2:
                for i in range(len(word) - 1):
                    bigrams[word[i:i+2]] += 1
            if len(word) >= 3:
                for i in range(len(word) - 2):
                    trigrams[word[i:i+3]] += 1
        
        insights["common_bigrams"] = Counter(bigrams).most_common(15)
        insights["common_trigrams"] = Counter(trigrams).most_common(15)
        
        return insights
    
    def analyze_word_patterns(self, language: str, min_occurrences: int = 5) -> List[WordPattern]:
        """
        Analyze common word patterns and formations.
        
        Args:
            language: Language code
            min_occurrences: Minimum occurrences for a pattern to be included
            
        Returns:
            List of word patterns with statistics
        """
        logger.info(f"Analyzing word patterns for {language}")
        
        db_path = self.french_db_path if language == 'fr' else self.english_db_path
        patterns = defaultdict(lambda: {"words": [], "points": []})
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                table_name = "mots_fr" if language == 'fr' else "mots_en"
                word_col = "mot" if language == 'fr' else "word"
                
                cursor.execute(f"SELECT {word_col}, points FROM {table_name}")
                words_data = cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error analyzing patterns for {language}: {e}")
            return []
        
        # Generate patterns
        for word, points in words_data:
            if len(word) >= 3:
                # Create pattern (consonants as C, vowels as V)
                pattern = ""
                vowels = set('AEIOU')
                for char in word:
                    pattern += 'V' if char in vowels else 'C'
                
                patterns[pattern]["words"].append(word)
                patterns[pattern]["points"].append(points)
        
        # Convert to WordPattern objects
        result_patterns = []
        for pattern, data in patterns.items():
            if len(data["words"]) >= min_occurrences:
                avg_points = statistics.mean(data["points"]) if data["points"] else 0
                result_patterns.append(WordPattern(
                    pattern=pattern,
                    count=len(data["words"]),
                    examples=data["words"][:10],
                    average_points=round(avg_points, 1)
                ))
        
        # Sort by frequency
        result_patterns.sort(key=lambda x: x.count, reverse=True)
        
        return result_patterns[:50]  # Top 50 patterns
    
    def generate_scrabble_strategy_guide(self, language: str) -> ScrabbleStrategy:
        """
        Generate comprehensive Scrabble strategy guide.
        
        Args:
            language: Language code
            
        Returns:
            Strategic insights for Scrabble gameplay
        """
        logger.info(f"Generating Scrabble strategy guide for {language}")
        
        db_path = self.french_db_path if language == 'fr' else self.english_db_path
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                table_name = "mots_fr" if language == 'fr' else "mots_en"
                word_col = "mot" if language == 'fr' else "word"
                length_col = "longueur" if language == 'fr' else "length"
                
                # High-value short words (2-4 letters)
                cursor.execute(f"""
                    SELECT {word_col}, points 
                    FROM {table_name} 
                    WHERE {length_col} BETWEEN 2 AND 4 AND points >= 6
                    ORDER BY points DESC, {length_col} ASC
                    LIMIT 25
                """)
                high_value_short = cursor.fetchall()
                
                # Seven-letter words for bingo bonus
                cursor.execute(f"""
                    SELECT {word_col}
                    FROM {table_name}
                    WHERE {length_col} = 7
                    ORDER BY points DESC
                    LIMIT 50
                """)
                seven_letter = [row[0] for row in cursor.fetchall()]
                
                # Get all words for analysis
                cursor.execute(f"SELECT {word_col}, points, {length_col} FROM {table_name}")
                all_words = cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error generating strategy guide for {language}: {e}")
            return ScrabbleStrategy([], [], [], [], [], [], [])
        
        # Analyze prefixes and suffixes
        prefix_counts = defaultdict(int)
        suffix_counts = defaultdict(int)
        vowel_heavy = []
        consonant_clusters = []
        q_without_u = []
        
        vowels = set('AEIOU')
        
        for word, points, length in all_words:
            # Prefixes (2-3 characters)
            if length >= 4:
                prefix_counts[word[:2]] += 1
                prefix_counts[word[:3]] += 1
            
            # Suffixes (2-3 characters)
            if length >= 4:
                suffix_counts[word[-2:]] += 1
                suffix_counts[word[-3:]] += 1
            
            # Vowel-heavy words
            vowel_count = sum(1 for char in word if char in vowels)
            if length >= 4 and vowel_count / length > 0.6:
                vowel_heavy.append(word)
            
            # Consonant clusters
            consonant_count = sum(1 for char in word if char not in vowels)
            if length >= 4 and consonant_count / length > 0.7:
                consonant_clusters.append(word)
            
            # Q without U
            if 'Q' in word and 'U' not in word:
                q_without_u.append(word)
        
        # Get top prefixes and suffixes
        common_prefixes = Counter(prefix_counts).most_common(20)
        common_suffixes = Counter(suffix_counts).most_common(20)
        
        return ScrabbleStrategy(
            high_value_short_words=high_value_short,
            common_prefixes=common_prefixes,
            common_suffixes=common_suffixes,
            vowel_heavy_words=vowel_heavy[:30],
            consonant_clusters=consonant_clusters[:30],
            seven_letter_words=seven_letter,
            q_without_u_words=q_without_u
        )
    
    def compare_languages(self) -> Dict[str, Any]:
        """
        Compare statistics between French and English dictionaries.
        
        Returns:
            Comparative analysis between languages
        """
        logger.info("Generating comparative analysis between languages")
        
        fr_stats = self.analyze_language_statistics('fr')
        en_stats = self.analyze_language_statistics('en')
        
        comparison = {
            "basic_comparison": {
                "total_words": {
                    "french": fr_stats.total_words,
                    "english": en_stats.total_words,
                    "difference": abs(fr_stats.total_words - en_stats.total_words),
                    "larger_dictionary": "french" if fr_stats.total_words > en_stats.total_words else "english"
                },
                "average_word_length": {
                    "french": fr_stats.average_word_length,
                    "english": en_stats.average_word_length,
                    "difference": round(abs(fr_stats.average_word_length - en_stats.average_word_length), 2)
                }
            },
            "letter_frequency_comparison": self._compare_letter_frequencies(fr_stats, en_stats),
            "length_distribution_comparison": self._compare_distributions(
                fr_stats.length_distribution, en_stats.length_distribution
            ),
            "scrabble_insights_comparison": {
                "french_high_value_words": len(fr_stats.scrabble_insights.get("high_value_short_words", [])),
                "english_high_value_words": len(en_stats.scrabble_insights.get("high_value_short_words", [])),
                "french_seven_letter_count": fr_stats.scrabble_insights.get("seven_letter_words_count", 0),
                "english_seven_letter_count": en_stats.scrabble_insights.get("seven_letter_words_count", 0)
            }
        }
        
        return comparison
    
    def _compare_letter_frequencies(self, fr_stats: LanguageStatistics, 
                                   en_stats: LanguageStatistics) -> Dict[str, Any]:
        """Compare letter frequencies between languages."""
        common_letters = set(fr_stats.letter_frequency.keys()) & set(en_stats.letter_frequency.keys())
        
        differences = {}
        for letter in common_letters:
            fr_freq = fr_stats.letter_frequency[letter]
            en_freq = en_stats.letter_frequency[letter]
            differences[letter] = {
                "french": round(fr_freq * 100, 2),
                "english": round(en_freq * 100, 2),
                "difference": round(abs(fr_freq - en_freq) * 100, 2)
            }
        
        # Find biggest differences
        biggest_diffs = sorted(
            differences.items(),
            key=lambda x: x[1]["difference"],
            reverse=True
        )[:10]
        
        return {
            "all_letters": differences,
            "biggest_differences": dict(biggest_diffs)
        }
    
    def _compare_distributions(self, dist1: Dict[int, int], dist2: Dict[int, int]) -> Dict[str, Any]:
        """Compare two distributions."""
        all_keys = set(dist1.keys()) | set(dist2.keys())
        
        comparison = {}
        for key in sorted(all_keys):
            val1 = dist1.get(key, 0)
            val2 = dist2.get(key, 0)
            comparison[str(key)] = {
                "french": val1,
                "english": val2,
                "difference": abs(val1 - val2)
            }
        
        return comparison
    
    def _create_empty_statistics(self, language: str) -> LanguageStatistics:
        """Create empty statistics object for error cases."""
        return LanguageStatistics(
            language_code=language,
            total_words=0,
            average_word_length=0.0,
            letter_frequency={},
            length_distribution={},
            point_distribution={},
            most_common_words=[],
            highest_scoring_words=[],
            letter_rarity={},
            scrabble_insights={}
        )
    
    def export_analytics_report(self, output_file: str = "dictionary_analytics_report.json"):
        """
        Export comprehensive analytics report to JSON file.
        
        Args:
            output_file: Output file path
        """
        logger.info(f"Generating comprehensive analytics report: {output_file}")
        
        report = {
            "metadata": {
                "generated_at": time.time(),
                "generator": "Scrabbot Dictionary Analytics",
                "version": "1.0"
            },
            "french_statistics": self._stats_to_dict(self.analyze_language_statistics('fr')),
            "english_statistics": self._stats_to_dict(self.analyze_language_statistics('en')),
            "comparative_analysis": self.compare_languages(),
            "french_word_patterns": [
                self._pattern_to_dict(p) for p in self.analyze_word_patterns('fr')[:20]
            ],
            "english_word_patterns": [
                self._pattern_to_dict(p) for p in self.analyze_word_patterns('en')[:20]
            ],
            "french_strategy_guide": self._strategy_to_dict(self.generate_scrabble_strategy_guide('fr')),
            "english_strategy_guide": self._strategy_to_dict(self.generate_scrabble_strategy_guide('en'))
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Analytics report exported to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
    
    def _stats_to_dict(self, stats: LanguageStatistics) -> Dict[str, Any]:
        """Convert LanguageStatistics to dictionary."""
        return {
            "language_code": stats.language_code,
            "total_words": stats.total_words,
            "average_word_length": stats.average_word_length,
            "letter_frequency": stats.letter_frequency,
            "length_distribution": stats.length_distribution,
            "point_distribution": stats.point_distribution,
            "most_common_words": stats.most_common_words,
            "highest_scoring_words": stats.highest_scoring_words,
            "letter_rarity": stats.letter_rarity,
            "scrabble_insights": stats.scrabble_insights
        }
    
    def _pattern_to_dict(self, pattern: WordPattern) -> Dict[str, Any]:
        """Convert WordPattern to dictionary."""
        return {
            "pattern": pattern.pattern,
            "count": pattern.count,
            "examples": pattern.examples,
            "average_points": pattern.average_points
        }
    
    def _strategy_to_dict(self, strategy: ScrabbleStrategy) -> Dict[str, Any]:
        """Convert ScrabbleStrategy to dictionary."""
        return {
            "high_value_short_words": strategy.high_value_short_words,
            "common_prefixes": strategy.common_prefixes,
            "common_suffixes": strategy.common_suffixes,
            "vowel_heavy_words": strategy.vowel_heavy_words,
            "consonant_clusters": strategy.consonant_clusters,
            "seven_letter_words": strategy.seven_letter_words,
            "q_without_u_words": strategy.q_without_u_words
        }


# Factory function
def create_analytics_engine(french_db_path: str, english_db_path: str) -> DictionaryAnalytics:
    """Create and return a new analytics engine."""
    return DictionaryAnalytics(french_db_path, english_db_path)
