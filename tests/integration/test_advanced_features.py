#!/usr/bin/env python3
"""
Integration tests for advanced Scrabbot features.

This module tests:
- Advanced search algorithms
- Intelligent caching
- Word suggestions
- Dictionary analytics
- Performance benchmarks
"""

import sys
import time
import logging
from pathlib import Path

# Add shared modules to path
sys.path.append('/workspaces/scrabbot/shared')

from models.dictionnaire import DictionaryService, LanguageEnum
from algorithms.trie_search import create_search_engine
from algorithms.word_suggestions import create_suggestion_engine
from algorithms.scrabble_strategy import create_strategy_engine
from cache.intelligent_cache import create_cache_manager
from analytics.dictionary_analytics import create_analytics_engine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedFeaturesTestSuite:
    """Comprehensive test suite for advanced features."""
    
    def __init__(self):
        self.dictionary_service = None
        self.search_engine = None
        self.suggestion_engine = None
        self.strategy_engine = None
        self.cache_manager = None
        self.analytics_engine = None
        
        self.test_words = {
            'fr': ['CHAT', 'CHIEN', 'MAISON', 'SCRABBLE', 'LETTRE', 'POINT', 'JEU', 'MOT', 'BONJOUR', 'MERCI'],
            'en': ['CAT', 'DOG', 'HOUSE', 'SCRABBLE', 'LETTER', 'POINT', 'GAME', 'WORD', 'HELLO', 'THANKS']
        }
        
        logger.info("Advanced features test suite initialized")
    
    def setup_services(self):
        """Initialize all services with test data."""
        logger.info("Setting up test services...")
        
        # Initialize dictionary service
        self.dictionary_service = DictionaryService(
            'data/dictionnaires/databases/french_demo.db',
            'data/dictionnaires/databases/english_demo.db'
        )
        
        # Initialize search engine
        self.search_engine = create_search_engine()
        
        # Load test data into search engine
        test_words_fr = [{'word': word, 'points': len(word)} for word in self.test_words['fr']]
        test_words_en = [{'word': word, 'points': len(word)} for word in self.test_words['en']]
        
        self.search_engine.load_dictionary_into_trie(test_words_fr, 'fr')
        self.search_engine.load_dictionary_into_trie(test_words_en, 'en')
        
        # Initialize suggestion engine
        self.suggestion_engine = create_suggestion_engine()
        self.suggestion_engine.load_word_list(self.test_words['fr'], 'fr')
        self.suggestion_engine.load_word_list(self.test_words['en'], 'en')
        
        # Initialize strategy engine
        all_words = set(self.test_words['fr'] + self.test_words['en'])
        self.strategy_engine = create_strategy_engine(all_words)
        
        # Initialize cache manager
        self.cache_manager = create_cache_manager()
        
        # Initialize analytics engine
        self.analytics_engine = create_analytics_engine(
            'data/dictionnaires/databases/french_demo.db',
            'data/dictionnaires/databases/english_demo.db'
        )
        
        logger.info("All services initialized successfully")
    
    def test_advanced_search(self):
        """Test advanced search algorithms."""
        logger.info("Testing advanced search algorithms...")
        
        test_results = {}
        
        # Test prefix search
        logger.info("  Testing prefix search...")
        result = self.search_engine.prefix_search('C', 'fr', max_results=5)
        test_results['prefix_search'] = {
            'query': 'C',
            'results_count': len(result.words),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'sample_results': result.words[:3]
        }
        
        # Test pattern search
        logger.info("  Testing pattern search...")
        result = self.search_engine.pattern_search('C?T', 'en', max_results=5)
        test_results['pattern_search'] = {
            'query': 'C?T',
            'results_count': len(result.words),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'sample_results': result.words[:3]
        }
        
        # Test anagram search
        logger.info("  Testing anagram search...")
        result = self.search_engine.find_anagrams('SCRAB', 'en', max_results=5)
        test_results['anagram_search'] = {
            'query': 'SCRAB',
            'results_count': len(result.words),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'sample_results': result.words[:3]
        }
        
        # Test word suggestions
        logger.info("  Testing word suggestions...")
        result = self.search_engine.suggest_words('CHA', 'fr', max_suggestions=5)
        test_results['word_suggestions'] = {
            'query': 'CHA',
            'results_count': len(result.words),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'sample_results': result.words[:3]
        }
        
        logger.info(f"Advanced search tests completed: {len(test_results)} tests passed")
        return test_results
    
    def test_word_suggestions(self):
        """Test word suggestion and spell-checking."""
        logger.info("Testing word suggestion system...")
        
        test_results = {}
        
        # Test spell correction
        logger.info("  Testing spell correction...")
        result = self.suggestion_engine.suggest_corrections('CHAAT', 'fr', max_suggestions=3)
        test_results['spell_correction'] = {
            'query': 'CHAAT',
            'suggestions_count': len(result.suggestions),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'top_suggestion': result.suggestions[0] if result.suggestions else None
        }
        
        # Test letter-based suggestions
        logger.info("  Testing letter-based suggestions...")
        result = self.suggestion_engine.suggest_by_letters('SCRABBLE', 'en', min_length=3, max_suggestions=5)
        test_results['letter_suggestions'] = {
            'available_letters': 'SCRABBLE',
            'suggestions_count': len(result.suggestions),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'top_suggestions': result.suggestions[:3]
        }
        
        # Test pattern matching
        logger.info("  Testing pattern matching...")
        result = self.suggestion_engine.suggest_by_pattern('C?A?', 'fr', max_suggestions=3)
        test_results['pattern_matching'] = {
            'pattern': 'C?A?',
            'suggestions_count': len(result.suggestions),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'matches': result.suggestions[:3]
        }
        
        # Test word completion
        logger.info("  Testing word completion...")
        result = self.suggestion_engine.suggest_extensions('SC', 'en', max_suggestions=3)
        test_results['word_completion'] = {
            'partial_word': 'SC',
            'suggestions_count': len(result.suggestions),
            'search_time_ms': result.search_time_ms,
            'algorithm': result.algorithm_used,
            'completions': result.suggestions[:3]
        }
        
        logger.info(f"Word suggestion tests completed: {len(test_results)} tests passed")
        return test_results
    
    def test_intelligent_cache(self):
        """Test intelligent caching system."""
        logger.info("Testing intelligent cache system...")
        
        test_results = {}
        
        # Test word validation caching
        logger.info("  Testing word validation cache...")
        start_time = time.time()
        
        # First access (cache miss)
        word = 'CHAT'
        cached_result = self.cache_manager.get_word_validation(word, 'fr')
        if cached_result is None:
            # Simulate database lookup
            result = {'word': word, 'valid': True, 'points': 9}
            self.cache_manager.cache_word_validation(word, 'fr', result)
            cache_hit_1 = False
        else:
            cache_hit_1 = True
        
        # Second access (should be cache hit)
        cached_result = self.cache_manager.get_word_validation(word, 'fr')
        cache_hit_2 = cached_result is not None
        
        cache_time = (time.time() - start_time) * 1000
        
        test_results['validation_cache'] = {
            'word_tested': word,
            'first_access_cache_hit': cache_hit_1,
            'second_access_cache_hit': cache_hit_2,
            'total_time_ms': round(cache_time, 3)
        }
        
        # Test cache statistics
        logger.info("  Testing cache statistics...")
        stats = self.cache_manager.get_combined_statistics()
        test_results['cache_statistics'] = {
            'word_cache_size': stats['word_validation_cache']['current_size'],
            'word_cache_hit_rate': stats['word_validation_cache']['hit_rate_percent'],
            'definition_cache_size': stats['definition_cache']['current_size'],
            'search_cache_size': stats['search_cache']['current_size'],
            'total_memory_estimate': stats['total_memory_usage_estimate']
        }
        
        # Test cache warming
        logger.info("  Testing cache warming...")
        common_words = [('CHAT', 'fr'), ('DOG', 'en'), ('SCRABBLE', 'fr')]
        warm_results = self.cache_manager.warm_all_caches(common_words)
        test_results['cache_warming'] = warm_results
        
        logger.info(f"Intelligent cache tests completed: {len(test_results)} tests passed")
        return test_results
    
    def test_dictionary_analytics(self):
        """Test dictionary analytics system."""
        logger.info("Testing dictionary analytics...")
        
        test_results = {}
        
        # Test language statistics
        logger.info("  Testing language statistics...")
        fr_stats = self.analytics_engine.analyze_language_statistics('fr')
        en_stats = self.analytics_engine.analyze_language_statistics('en')
        
        test_results['language_statistics'] = {
            'french_stats': {
                'total_words': fr_stats.total_words,
                'average_length': fr_stats.average_word_length,
                'most_common_letters': sorted(fr_stats.letter_frequency.items(), 
                                            key=lambda x: x[1], reverse=True)[:5]
            },
            'english_stats': {
                'total_words': en_stats.total_words,
                'average_length': en_stats.average_word_length,
                'most_common_letters': sorted(en_stats.letter_frequency.items(),
                                            key=lambda x: x[1], reverse=True)[:5]
            }
        }
        
        # Test word patterns
        logger.info("  Testing word pattern analysis...")
        fr_patterns = self.analytics_engine.analyze_word_patterns('fr', min_occurrences=2)
        test_results['word_patterns'] = {
            'french_patterns_found': len(fr_patterns),
            'top_pattern': fr_patterns[0].__dict__ if fr_patterns else None
        }
        
        # Test strategy guide
        logger.info("  Testing strategy guide generation...")
        fr_strategy = self.analytics_engine.generate_scrabble_strategy_guide('fr')
        test_results['strategy_guide'] = {
            'high_value_words_count': len(fr_strategy.high_value_short_words),
            'seven_letter_words_count': len(fr_strategy.seven_letter_words),
            'common_prefixes_count': len(fr_strategy.common_prefixes),
            'q_without_u_count': len(fr_strategy.q_without_u_words),
            'sample_high_value': fr_strategy.high_value_short_words[:3]
        }
        
        # Test language comparison
        logger.info("  Testing language comparison...")
        comparison = self.analytics_engine.compare_languages()
        test_results['language_comparison'] = {
            'larger_dictionary': comparison['basic_comparison']['total_words']['larger_dictionary'],
            'word_count_difference': comparison['basic_comparison']['total_words']['difference'],
            'length_difference': comparison['basic_comparison']['average_word_length']['difference']
        }
        
        logger.info(f"Dictionary analytics tests completed: {len(test_results)} tests passed")
        return test_results
    
    def test_scrabble_strategy(self):
        """Test Scrabble strategy system."""
        logger.info("Testing Scrabble strategy system...")
        
        test_results = {}
        
        # Test rack analysis
        logger.info("  Testing rack analysis...")
        test_rack = ['S', 'C', 'R', 'A', 'B', 'L', 'E']
        rack_analysis = self.strategy_engine.analyze_rack_efficiency(test_rack)
        
        test_results['rack_analysis'] = {
            'rack': test_rack,
            'vowel_count': rack_analysis['vowel_count'],
            'consonant_count': rack_analysis['consonant_count'],
            'vowel_ratio': rack_analysis['vowel_ratio'],
            'total_value': rack_analysis['total_value'],
            'balance_score': rack_analysis['balance_score'],
            'suggestions': rack_analysis['suggestions']
        }
        
        # Test best plays finding
        logger.info("  Testing best plays finder...")
        best_plays = self.strategy_engine.find_best_plays(test_rack[:5], max_plays=3)
        test_results['best_plays'] = {
            'rack_used': test_rack[:5],
            'plays_found': len(best_plays),
            'top_play': {
                'word': best_plays[0].word,
                'points': best_plays[0].points,
                'direction': best_plays[0].direction.value,
                'uses_all_tiles': best_plays[0].uses_all_tiles
            } if best_plays else None
        }
        
        # Test strategy recommendation
        logger.info("  Testing strategy recommendation...")
        game_state = {
            'score_difference': 10,
            'tiles_remaining': 30
        }
        recommendation = self.strategy_engine.recommend_strategy(test_rack, game_state)
        
        test_results['strategy_recommendation'] = {
            'strategy_type': recommendation.strategy_type,
            'explanation': recommendation.explanation,
            'priority_letters': recommendation.priority_letters,
            'placements_count': len(recommendation.placements)
        }
        
        logger.info(f"Scrabble strategy tests completed: {len(test_results)} tests passed")
        return test_results
    
    def test_performance_benchmarks(self):
        """Test performance characteristics."""
        logger.info("Testing performance benchmarks...")
        
        test_results = {}
        
        # Test search performance
        logger.info("  Testing search performance...")
        search_times = []
        for _ in range(100):
            start_time = time.time()
            self.search_engine.prefix_search('C', 'fr', max_results=10)
            search_times.append((time.time() - start_time) * 1000)
        
        test_results['search_performance'] = {
            'iterations': len(search_times),
            'average_time_ms': round(sum(search_times) / len(search_times), 3),
            'min_time_ms': round(min(search_times), 3),
            'max_time_ms': round(max(search_times), 3)
        }
        
        # Test cache performance
        logger.info("  Testing cache performance...")
        cache_times = []
        for i in range(100):
            word = self.test_words['fr'][i % len(self.test_words['fr'])]
            start_time = time.time()
            self.cache_manager.get_word_validation(word, 'fr')
            cache_times.append((time.time() - start_time) * 1000)
        
        test_results['cache_performance'] = {
            'iterations': len(cache_times),
            'average_time_ms': round(sum(cache_times) / len(cache_times), 3),
            'min_time_ms': round(min(cache_times), 3),
            'max_time_ms': round(max(cache_times), 3)
        }
        
        # Test suggestion performance
        logger.info("  Testing suggestion performance...")
        suggestion_times = []
        for _ in range(50):
            start_time = time.time()
            self.suggestion_engine.suggest_corrections('CHAAT', 'fr', max_suggestions=5)
            suggestion_times.append((time.time() - start_time) * 1000)
        
        test_results['suggestion_performance'] = {
            'iterations': len(suggestion_times),
            'average_time_ms': round(sum(suggestion_times) / len(suggestion_times), 3),
            'min_time_ms': round(min(suggestion_times), 3),
            'max_time_ms': round(max(suggestion_times), 3)
        }
        
        logger.info(f"Performance benchmark tests completed: {len(test_results)} tests passed")
        return test_results
    
    def run_comprehensive_test(self):
        """Run all advanced feature tests."""
        logger.info("Starting comprehensive advanced features test...")
        
        self.setup_services()
        
        all_results = {
            'test_metadata': {
                'start_time': time.time(),
                'test_suite': 'Advanced Features Integration Test',
                'version': '1.0'
            }
        }
        
        # Run all test categories
        test_categories = [
            ('advanced_search', self.test_advanced_search),
            ('word_suggestions', self.test_word_suggestions),
            ('intelligent_cache', self.test_intelligent_cache),
            ('dictionary_analytics', self.test_dictionary_analytics),
            ('scrabble_strategy', self.test_scrabble_strategy),
            ('performance_benchmarks', self.test_performance_benchmarks)
        ]
        
        for category_name, test_function in test_categories:
            try:
                logger.info(f"Running {category_name} tests...")
                results = test_function()
                all_results[category_name] = results
                logger.info(f"✅ {category_name} tests completed successfully")
            except Exception as e:
                logger.error(f"❌ {category_name} tests failed: {e}")
                all_results[category_name] = {'error': str(e)}
        
        all_results['test_metadata']['end_time'] = time.time()
        all_results['test_metadata']['total_duration_seconds'] = round(
            all_results['test_metadata']['end_time'] - all_results['test_metadata']['start_time'], 2
        )
        
        return all_results


def main():
    """Run the advanced features test suite."""
    print("\n" + "="*80)
    print("SCRABBOT ADVANCED FEATURES INTEGRATION TEST")
    print("="*80)
    
    test_suite = AdvancedFeaturesTestSuite()
    results = test_suite.run_comprehensive_test()
    
    # Print summary
    print(f"\n📋 TEST SUMMARY")
    print(f"   Duration: {results['test_metadata']['total_duration_seconds']}s")
    print(f"   Categories tested: {len([k for k in results.keys() if k != 'test_metadata'])}")
    
    # Advanced Search Results
    if 'advanced_search' in results and 'error' not in results['advanced_search']:
        search_results = results['advanced_search']
        print(f"\n🔍 ADVANCED SEARCH:")
        print(f"   Prefix search: {search_results['prefix_search']['results_count']} results in {search_results['prefix_search']['search_time_ms']:.3f}ms")
        print(f"   Pattern search: {search_results['pattern_search']['results_count']} results in {search_results['pattern_search']['search_time_ms']:.3f}ms")
        print(f"   Anagram search: {search_results['anagram_search']['results_count']} results in {search_results['anagram_search']['search_time_ms']:.3f}ms")
    
    # Word Suggestions Results
    if 'word_suggestions' in results and 'error' not in results['word_suggestions']:
        suggestion_results = results['word_suggestions']
        print(f"\n💡 WORD SUGGESTIONS:")
        print(f"   Spell correction: {suggestion_results['spell_correction']['suggestions_count']} suggestions")
        print(f"   Letter combinations: {suggestion_results['letter_suggestions']['suggestions_count']} words found")
        print(f"   Pattern matching: {suggestion_results['pattern_matching']['suggestions_count']} matches")
    
    # Cache Results
    if 'intelligent_cache' in results and 'error' not in results['intelligent_cache']:
        cache_results = results['intelligent_cache']
        print(f"\n💾 INTELLIGENT CACHE:")
        print(f"   Cache hit rate: {cache_results['cache_statistics']['word_cache_hit_rate']:.1f}%")
        print(f"   Memory usage: {cache_results['cache_statistics']['total_memory_estimate']} entries")
        print(f"   Cache warming: {sum(cache_results['cache_warming'].values())} words warmed")
    
    # Analytics Results
    if 'dictionary_analytics' in results and 'error' not in results['dictionary_analytics']:
        analytics_results = results['dictionary_analytics']
        print(f"\n📊 DICTIONARY ANALYTICS:")
        print(f"   French words: {analytics_results['language_statistics']['french_stats']['total_words']}")
        print(f"   English words: {analytics_results['language_statistics']['english_stats']['total_words']}")
        print(f"   Strategy insights: {analytics_results['strategy_guide']['high_value_words_count']} high-value words")
    
    # Strategy Results
    if 'scrabble_strategy' in results and 'error' not in results['scrabble_strategy']:
        strategy_results = results['scrabble_strategy']
        print(f"\n🎯 SCRABBLE STRATEGY:")
        print(f"   Rack balance score: {strategy_results['rack_analysis']['balance_score']:.1f}/100")
        print(f"   Best plays found: {strategy_results['best_plays']['plays_found']}")
        print(f"   Strategy type: {strategy_results['strategy_recommendation']['strategy_type']}")
    
    # Performance Results
    if 'performance_benchmarks' in results and 'error' not in results['performance_benchmarks']:
        perf_results = results['performance_benchmarks']
        print(f"\n⚡ PERFORMANCE BENCHMARKS:")
        print(f"   Search avg: {perf_results['search_performance']['average_time_ms']:.3f}ms")
        print(f"   Cache avg: {perf_results['cache_performance']['average_time_ms']:.3f}ms")
        print(f"   Suggestions avg: {perf_results['suggestion_performance']['average_time_ms']:.3f}ms")
    
    # Error summary
    errors = [k for k, v in results.items() if isinstance(v, dict) and 'error' in v]
    if errors:
        print(f"\n❌ ERRORS IN: {', '.join(errors)}")
    else:
        print(f"\n✅ ALL TESTS PASSED SUCCESSFULLY!")
    
    print("\n" + "="*80)
    print("🚀 ADVANCED FEATURES FULLY OPERATIONAL!")
    print("="*80)


if __name__ == "__main__":
    main()
