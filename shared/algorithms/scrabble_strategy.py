#!/usr/bin/env python3
"""
Advanced Scrabble strategy algorithms for optimal gameplay.

This module implements:
- Board analysis and placement optimization
- Word formation strategy
- Rack management algorithms
- Bonus square utilization
- Turn optimization
"""

import logging
from typing import List, Dict, Set, Optional, Tuple, NamedTuple, Any
from dataclasses import dataclass
from enum import Enum
import itertools
from collections import defaultdict

logger = logging.getLogger(__name__)


class SquareType(Enum):
    """Types of squares on the Scrabble board."""
    NORMAL = "normal"
    DOUBLE_LETTER = "double_letter"
    TRIPLE_LETTER = "triple_letter"
    DOUBLE_WORD = "double_word"
    TRIPLE_WORD = "triple_word"
    CENTER = "center"  # Starting square (double word)


class Direction(Enum):
    """Word placement directions."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class BoardSquare:
    """Individual square on the Scrabble board."""
    row: int
    col: int
    square_type: SquareType
    letter: Optional[str] = None
    is_occupied: bool = False


@dataclass
class WordPlacement:
    """A potential word placement on the board."""
    word: str
    start_row: int
    start_col: int
    direction: Direction
    points: int
    uses_all_tiles: bool
    bonus_squares_used: List[SquareType]
    tiles_needed: List[str]


@dataclass
class StrategyRecommendation:
    """Strategic recommendation for a turn."""
    placements: List[WordPlacement]
    rack_optimization: Dict[str, int]
    priority_letters: List[str]
    strategy_type: str
    explanation: str


class ScrabbleBoard:
    """
    Representation and analysis of a Scrabble board.
    
    Handles board state, placement validation, and scoring calculations.
    """
    
    def __init__(self):
        self.size = 15
        self.board = self._initialize_board()
        self.occupied_squares: Set[Tuple[int, int]] = set()
        
        # Scrabble letter values
        self.letter_values = {
            'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4, 'I': 1,
            'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3, 'Q': 10, 'R': 1,
            'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8, 'Y': 4, 'Z': 10
        }
        
        logger.info("Scrabble board initialized")
    
    def _initialize_board(self) -> List[List[BoardSquare]]:
        """Initialize the standard Scrabble board layout."""
        board = []
        
        # Standard Scrabble board special squares
        special_squares = {
            # Triple Word Score
            (0, 0): SquareType.TRIPLE_WORD, (0, 7): SquareType.TRIPLE_WORD, (0, 14): SquareType.TRIPLE_WORD,
            (7, 0): SquareType.TRIPLE_WORD, (7, 14): SquareType.TRIPLE_WORD,
            (14, 0): SquareType.TRIPLE_WORD, (14, 7): SquareType.TRIPLE_WORD, (14, 14): SquareType.TRIPLE_WORD,
            
            # Double Word Score
            (1, 1): SquareType.DOUBLE_WORD, (2, 2): SquareType.DOUBLE_WORD, (3, 3): SquareType.DOUBLE_WORD,
            (4, 4): SquareType.DOUBLE_WORD, (1, 13): SquareType.DOUBLE_WORD, (2, 12): SquareType.DOUBLE_WORD,
            (3, 11): SquareType.DOUBLE_WORD, (4, 10): SquareType.DOUBLE_WORD, (10, 4): SquareType.DOUBLE_WORD,
            (11, 3): SquareType.DOUBLE_WORD, (12, 2): SquareType.DOUBLE_WORD, (13, 1): SquareType.DOUBLE_WORD,
            (10, 10): SquareType.DOUBLE_WORD, (11, 11): SquareType.DOUBLE_WORD, (12, 12): SquareType.DOUBLE_WORD,
            (13, 13): SquareType.DOUBLE_WORD,
            
            # Center star (Double Word Score)
            (7, 7): SquareType.CENTER,
            
            # Triple Letter Score
            (1, 5): SquareType.TRIPLE_LETTER, (1, 9): SquareType.TRIPLE_LETTER,
            (5, 1): SquareType.TRIPLE_LETTER, (5, 5): SquareType.TRIPLE_LETTER,
            (5, 9): SquareType.TRIPLE_LETTER, (5, 13): SquareType.TRIPLE_LETTER,
            (9, 1): SquareType.TRIPLE_LETTER, (9, 5): SquareType.TRIPLE_LETTER,
            (9, 9): SquareType.TRIPLE_LETTER, (9, 13): SquareType.TRIPLE_LETTER,
            (13, 5): SquareType.TRIPLE_LETTER, (13, 9): SquareType.TRIPLE_LETTER,
            
            # Double Letter Score
            (0, 3): SquareType.DOUBLE_LETTER, (0, 11): SquareType.DOUBLE_LETTER,
            (2, 6): SquareType.DOUBLE_LETTER, (2, 8): SquareType.DOUBLE_LETTER,
            (3, 0): SquareType.DOUBLE_LETTER, (3, 7): SquareType.DOUBLE_LETTER,
            (3, 14): SquareType.DOUBLE_LETTER, (6, 2): SquareType.DOUBLE_LETTER,
            (6, 6): SquareType.DOUBLE_LETTER, (6, 8): SquareType.DOUBLE_LETTER,
            (6, 12): SquareType.DOUBLE_LETTER, (7, 3): SquareType.DOUBLE_LETTER,
            (7, 11): SquareType.DOUBLE_LETTER, (8, 2): SquareType.DOUBLE_LETTER,
            (8, 6): SquareType.DOUBLE_LETTER, (8, 8): SquareType.DOUBLE_LETTER,
            (8, 12): SquareType.DOUBLE_LETTER, (11, 0): SquareType.DOUBLE_LETTER,
            (11, 7): SquareType.DOUBLE_LETTER, (11, 14): SquareType.DOUBLE_LETTER,
            (12, 6): SquareType.DOUBLE_LETTER, (12, 8): SquareType.DOUBLE_LETTER,
            (14, 3): SquareType.DOUBLE_LETTER, (14, 11): SquareType.DOUBLE_LETTER
        }
        
        for row in range(self.size):
            board_row = []
            for col in range(self.size):
                square_type = special_squares.get((row, col), SquareType.NORMAL)
                board_row.append(BoardSquare(row, col, square_type))
            board.append(board_row)
        
        return board
    
    def place_letter(self, row: int, col: int, letter: str) -> bool:
        """
        Place a letter on the board.
        
        Args:
            row: Row position
            col: Column position
            letter: Letter to place
            
        Returns:
            True if placement successful, False otherwise
        """
        if not self._is_valid_position(row, col):
            return False
        
        if self.board[row][col].is_occupied:
            return False
        
        self.board[row][col].letter = letter.upper()
        self.board[row][col].is_occupied = True
        self.occupied_squares.add((row, col))
        
        return True
    
    def remove_letter(self, row: int, col: int) -> bool:
        """Remove a letter from the board."""
        if not self._is_valid_position(row, col):
            return False
        
        self.board[row][col].letter = None
        self.board[row][col].is_occupied = False
        self.occupied_squares.discard((row, col))
        
        return True
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is valid on the board."""
        return 0 <= row < self.size and 0 <= col < self.size
    
    def calculate_word_score(self, word: str, start_row: int, start_col: int, 
                           direction: Direction, new_tiles: Set[Tuple[int, int]]) -> int:
        """
        Calculate the score for placing a word on the board.
        
        Args:
            word: Word to place
            start_row: Starting row
            start_col: Starting column
            direction: Word direction
            new_tiles: Set of positions where new tiles are placed
            
        Returns:
            Total score for the word
        """
        if not self._can_place_word(word, start_row, start_col, direction):
            return 0
        
        word_score = 0
        word_multiplier = 1
        
        # Calculate main word score
        for i, letter in enumerate(word):
            if direction == Direction.HORIZONTAL:
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
            
            letter_score = self.letter_values.get(letter, 0)
            square = self.board[row][col]
            
            # Apply letter multipliers only for new tiles
            if (row, col) in new_tiles:
                if square.square_type == SquareType.DOUBLE_LETTER:
                    letter_score *= 2
                elif square.square_type == SquareType.TRIPLE_LETTER:
                    letter_score *= 3
                
                # Apply word multipliers only for new tiles
                if square.square_type in [SquareType.DOUBLE_WORD, SquareType.CENTER]:
                    word_multiplier *= 2
                elif square.square_type == SquareType.TRIPLE_WORD:
                    word_multiplier *= 3
            
            word_score += letter_score
        
        word_score *= word_multiplier
        
        # Add cross-word scores (words formed perpendicular to main word)
        cross_word_score = self._calculate_cross_words_score(
            word, start_row, start_col, direction, new_tiles
        )
        
        total_score = word_score + cross_word_score
        
        # Bingo bonus (using all 7 tiles)
        if len(new_tiles) == 7:
            total_score += 50
        
        return total_score
    
    def _can_place_word(self, word: str, start_row: int, start_col: int, 
                       direction: Direction) -> bool:
        """Check if a word can be placed at the given position."""
        # Check bounds
        if direction == Direction.HORIZONTAL:
            if start_col + len(word) > self.size:
                return False
        else:
            if start_row + len(word) > self.size:
                return False
        
        # Check for conflicts with existing letters
        for i, letter in enumerate(word):
            if direction == Direction.HORIZONTAL:
                row, col = start_row, start_col + i
            else:
                row, col = start_row + i, start_col
            
            existing_letter = self.board[row][col].letter
            if existing_letter and existing_letter != letter:
                return False
        
        return True
    
    def _calculate_cross_words_score(self, word: str, start_row: int, start_col: int,
                                   direction: Direction, new_tiles: Set[Tuple[int, int]]) -> int:
        """Calculate score from cross-words formed."""
        cross_score = 0
        
        for i, letter in enumerate(word):
            if direction == Direction.HORIZONTAL:
                row, col = start_row, start_col + i
                cross_direction = Direction.VERTICAL
            else:
                row, col = start_row + i, start_col
                cross_direction = Direction.HORIZONTAL
            
            # Only check cross-words for new tiles
            if (row, col) in new_tiles:
                cross_word = self._find_cross_word(row, col, cross_direction)
                if len(cross_word) > 1:  # More than just the single letter
                    cross_score += self._score_cross_word(cross_word, row, col, cross_direction, new_tiles)
        
        return cross_score
    
    def _find_cross_word(self, row: int, col: int, direction: Direction) -> str:
        """Find the cross-word formed at a position."""
        if direction == Direction.HORIZONTAL:
            # Find word extending left and right
            start_col = col
            while start_col > 0 and self.board[row][start_col - 1].is_occupied:
                start_col -= 1
            
            end_col = col
            while end_col < self.size - 1 and self.board[row][end_col + 1].is_occupied:
                end_col += 1
            
            word = ""
            for c in range(start_col, end_col + 1):
                letter = self.board[row][c].letter
                word += letter if letter else "?"
        
        else:  # VERTICAL
            # Find word extending up and down
            start_row = row
            while start_row > 0 and self.board[start_row - 1][col].is_occupied:
                start_row -= 1
            
            end_row = row
            while end_row < self.size - 1 and self.board[end_row + 1][col].is_occupied:
                end_row += 1
            
            word = ""
            for r in range(start_row, end_row + 1):
                letter = self.board[r][col].letter
                word += letter if letter else "?"
        
        return word
    
    def _score_cross_word(self, word: str, center_row: int, center_col: int,
                         direction: Direction, new_tiles: Set[Tuple[int, int]]) -> int:
        """Score a cross-word."""
        # This is a simplified implementation
        # In a full implementation, you'd need to track which letters are new
        # and apply multipliers only to those
        base_score = sum(self.letter_values.get(letter, 0) for letter in word)
        
        # Apply multiplier if the center tile is new and on a special square
        if (center_row, center_col) in new_tiles:
            square = self.board[center_row][center_col]
            if square.square_type in [SquareType.DOUBLE_WORD, SquareType.CENTER]:
                base_score *= 2
            elif square.square_type == SquareType.TRIPLE_WORD:
                base_score *= 3
        
        return base_score


class StrategyEngine:
    """
    Advanced strategy engine for Scrabble gameplay.
    
    Analyzes board state and player rack to recommend optimal plays.
    """
    
    def __init__(self, dictionary_words: Set[str]):
        self.dictionary = dictionary_words
        self.board = ScrabbleBoard()
        
        # Common letter frequencies for rack management
        self.letter_frequencies = {
            'E': 0.127, 'T': 0.091, 'A': 0.082, 'O': 0.075, 'I': 0.070,
            'N': 0.067, 'S': 0.063, 'H': 0.061, 'R': 0.060, 'D': 0.043,
            'L': 0.040, 'C': 0.028, 'U': 0.028, 'M': 0.024, 'W': 0.024,
            'F': 0.022, 'G': 0.020, 'Y': 0.020, 'P': 0.019, 'B': 0.015,
            'V': 0.010, 'K': 0.008, 'J': 0.002, 'X': 0.002, 'Q': 0.001, 'Z': 0.001
        }
        
        logger.info(f"Strategy engine initialized with {len(dictionary_words)} words")
    
    def find_best_plays(self, rack: List[str], max_plays: int = 10) -> List[WordPlacement]:
        """
        Find the best possible plays for a given rack.
        
        Args:
            rack: List of available letters
            max_plays: Maximum number of plays to return
            
        Returns:
            List of best word placements sorted by score
        """
        logger.info(f"Finding best plays for rack: {rack}")
        
        possible_plays = []
        
        # If board is empty, must play through center
        if not self.board.occupied_squares:
            possible_plays.extend(self._find_center_plays(rack))
        else:
            # Find plays that connect to existing words
            possible_plays.extend(self._find_connected_plays(rack))
        
        # Sort by score and return top plays
        possible_plays.sort(key=lambda x: x.points, reverse=True)
        
        return possible_plays[:max_plays]
    
    def _find_center_plays(self, rack: List[str]) -> List[WordPlacement]:
        """Find plays that go through the center square."""
        center_row, center_col = 7, 7
        plays = []
        
        # Generate all possible words from rack
        for word_length in range(2, len(rack) + 1):
            for letter_combo in itertools.permutations(rack, word_length):
                word = ''.join(letter_combo)
                if word in self.dictionary:
                    # Try horizontal placement through center
                    for start_offset in range(word_length):
                        start_col = center_col - start_offset
                        if 0 <= start_col and start_col + len(word) <= self.board.size:
                            new_tiles = {(center_row, start_col + i) for i in range(len(word))}
                            score = self.board.calculate_word_score(
                                word, center_row, start_col, Direction.HORIZONTAL, new_tiles
                            )
                            
                            plays.append(WordPlacement(
                                word=word,
                                start_row=center_row,
                                start_col=start_col,
                                direction=Direction.HORIZONTAL,
                                points=score,
                                uses_all_tiles=(len(word) == len(rack)),
                                bonus_squares_used=[self.board.board[center_row][center_col].square_type],
                                tiles_needed=list(letter_combo)
                            ))
                    
                    # Try vertical placement through center
                    for start_offset in range(word_length):
                        start_row = center_row - start_offset
                        if 0 <= start_row and start_row + len(word) <= self.board.size:
                            new_tiles = {(start_row + i, center_col) for i in range(len(word))}
                            score = self.board.calculate_word_score(
                                word, start_row, center_col, Direction.VERTICAL, new_tiles
                            )
                            
                            plays.append(WordPlacement(
                                word=word,
                                start_row=start_row,
                                start_col=center_col,
                                direction=Direction.VERTICAL,
                                points=score,
                                uses_all_tiles=(len(word) == len(rack)),
                                bonus_squares_used=[self.board.board[center_row][center_col].square_type],
                                tiles_needed=list(letter_combo)
                            ))
        
        return plays
    
    def _find_connected_plays(self, rack: List[str]) -> List[WordPlacement]:
        """Find plays that connect to existing words on the board."""
        plays = []
        
        # This is a simplified implementation
        # A full implementation would be much more complex
        
        # For each occupied square, try to extend words
        for row, col in self.board.occupied_squares:
            # Try placing before and after existing letters
            # This would require more sophisticated logic in a full implementation
            pass
        
        return plays
    
    def analyze_rack_efficiency(self, rack: List[str]) -> Dict[str, Any]:
        """
        Analyze the efficiency of the current rack.
        
        Args:
            rack: Current rack letters
            
        Returns:
            Analysis of rack composition and suggestions
        """
        rack_counter = defaultdict(int)
        for letter in rack:
            rack_counter[letter.upper()] += 1
        
        # Calculate vowel/consonant ratio
        vowels = set('AEIOU')
        vowel_count = sum(rack_counter[letter] for letter in vowels if letter in rack_counter)
        consonant_count = len(rack) - vowel_count
        
        vowel_ratio = vowel_count / len(rack) if rack else 0
        
        # Analyze letter balance
        high_value_letters = sum(rack_counter[letter] for letter in 'JQXZ' if letter in rack_counter)
        common_letters = sum(rack_counter[letter] for letter in 'ETAOINSHRDLU' if letter in rack_counter)
        
        # Calculate rack score potential
        total_value = sum(self.board.letter_values.get(letter, 0) for letter in rack)
        
        analysis = {
            "rack_composition": dict(rack_counter),
            "vowel_count": vowel_count,
            "consonant_count": consonant_count,
            "vowel_ratio": round(vowel_ratio, 2),
            "total_value": total_value,
            "high_value_letters": high_value_letters,
            "common_letters": common_letters,
            "balance_score": self._calculate_balance_score(vowel_ratio, high_value_letters, common_letters),
            "suggestions": self._generate_rack_suggestions(rack_counter, vowel_ratio)
        }
        
        return analysis
    
    def _calculate_balance_score(self, vowel_ratio: float, high_value: int, common: int) -> float:
        """Calculate a balance score for the rack (0-100)."""
        # Ideal vowel ratio is around 0.3-0.4
        vowel_score = 100 - abs(vowel_ratio - 0.35) * 200
        vowel_score = max(0, vowel_score)
        
        # Penalize too many high-value letters
        high_value_penalty = min(high_value * 20, 50)
        
        # Reward common letters
        common_bonus = min(common * 10, 50)
        
        balance_score = vowel_score - high_value_penalty + common_bonus
        return max(0, min(100, balance_score))
    
    def _generate_rack_suggestions(self, rack_counter: Dict[str, int], vowel_ratio: float) -> List[str]:
        """Generate suggestions for improving rack balance."""
        suggestions = []
        
        if vowel_ratio < 0.2:
            suggestions.append("Consider exchanging consonants for vowels")
        elif vowel_ratio > 0.6:
            suggestions.append("Consider exchanging vowels for consonants")
        
        high_value_count = sum(rack_counter[letter] for letter in 'JQXZ' if letter in rack_counter)
        if high_value_count > 2:
            suggestions.append("Too many high-value letters - consider exchanging some")
        
        if any(count > 2 for count in rack_counter.values()):
            suggestions.append("Multiple copies of same letter - consider exchanging duplicates")
        
        return suggestions
    
    def recommend_strategy(self, rack: List[str], game_state: Dict[str, Any]) -> StrategyRecommendation:
        """
        Provide comprehensive strategy recommendation.
        
        Args:
            rack: Current rack
            game_state: Current game state information
            
        Returns:
            Strategic recommendation for the turn
        """
        # Find best plays
        best_plays = self.find_best_plays(rack, max_plays=5)
        
        # Analyze rack
        rack_analysis = self.analyze_rack_efficiency(rack)
        
        # Determine strategy type based on game state
        score_difference = game_state.get('score_difference', 0)
        tiles_remaining = game_state.get('tiles_remaining', 50)
        
        if tiles_remaining < 20:
            strategy_type = "endgame"
            explanation = "Focus on high-scoring plays and blocking opponent"
        elif score_difference > 50:
            strategy_type = "conservative"
            explanation = "Maintain lead with consistent scoring"
        elif score_difference < -50:
            strategy_type = "aggressive"
            explanation = "Take risks for high-scoring opportunities"
        else:
            strategy_type = "balanced"
            explanation = "Balance offense and defense"
        
        # Priority letters based on strategy
        if strategy_type == "aggressive":
            priority_letters = ['J', 'Q', 'X', 'Z']  # High-value letters
        else:
            priority_letters = ['S', 'R', 'N', 'T']  # Versatile letters
        
        return StrategyRecommendation(
            placements=best_plays,
            rack_optimization=rack_analysis,
            priority_letters=priority_letters,
            strategy_type=strategy_type,
            explanation=explanation
        )


# Factory function
def create_strategy_engine(dictionary_words: Set[str]) -> StrategyEngine:
    """Create and return a new strategy engine."""
    return StrategyEngine(dictionary_words)
