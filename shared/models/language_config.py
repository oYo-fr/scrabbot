#!/usr/bin/env python3
"""
Language configuration loader for Scrabble rules and letter values.

Dynamically loads language-specific configurations from YAML files.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class LanguageConfig:
    """Configuration for a specific language in Scrabble."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize from configuration data."""
        self.language_code: str = config_data["language_code"]
        self.language_name: str = config_data["language_name"]
        self.letter_values: Dict[str, int] = config_data["letter_values"]
        self.letter_frequencies: Dict[str, float] = config_data["letter_frequencies"]
        self.tile_distribution: Dict[str, int] = config_data["tile_distribution"]
        self.special_rules: Dict[str, Any] = config_data["special_rules"]

    @property
    def vowels(self) -> List[str]:
        """Get vowels for this language."""
        return self.special_rules.get("vowels", [])

    @property
    def high_value_letters(self) -> List[str]:
        """Get high-value letters for this language."""
        return self.special_rules.get("high_value_letters", [])

    @property
    def common_letters(self) -> List[str]:
        """Get common letters for this language."""
        return self.special_rules.get("common_letters", [])

    @property
    def max_word_length(self) -> int:
        """Get maximum word length."""
        return self.special_rules.get("max_word_length", 15)

    @property
    def bingo_bonus(self) -> int:
        """Get bingo bonus points."""
        return self.special_rules.get("bingo_bonus", 50)

    @property
    def rack_size(self) -> int:
        """Get rack size."""
        return self.special_rules.get("rack_size", 7)


class LanguageConfigLoader:
    """Loader for language configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize with configuration directory."""
        self.config_dir = config_dir or Path("data")
        self._configs: Dict[str, LanguageConfig] = {}

    def load_language_config(self, language_code: str) -> LanguageConfig:
        """
        Load configuration for a specific language.

        Args:
            language_code: Language code (e.g., 'fr', 'en', 'es')

        Returns:
            LanguageConfig for the specified language

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config format is invalid
        """
        if language_code in self._configs:
            return self._configs[language_code]

        config_file = self.config_dir / f"{language_code}_config.yaml"

        if not config_file.exists():
            # Try alternative naming
            config_file = self.config_dir / f"{language_code.lower()}_config.yaml"
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found for language '{language_code}' in {self.config_dir}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            config = LanguageConfig(config_data)
            self._configs[language_code] = config

            logger.info(f"Loaded configuration for {config.language_name} ({language_code})")
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_file}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required key in {config_file}: {e}")

    def get_available_languages(self) -> List[str]:
        """Get list of available language codes."""
        languages = []
        for config_file in self.config_dir.glob("*_config.yaml"):
            language_code = config_file.stem.replace("_config", "")
            languages.append(language_code)
        return sorted(languages)

    def preload_all_configs(self) -> Dict[str, LanguageConfig]:
        """Preload all available language configurations."""
        available_languages = self.get_available_languages()

        for lang_code in available_languages:
            try:
                self.load_language_config(lang_code)
            except Exception as e:
                logger.error(f"Failed to load config for {lang_code}: {e}")

        return self._configs.copy()


# Global instance
_config_loader: Optional[LanguageConfigLoader] = None


def get_config_loader(config_dir: Optional[Path] = None) -> LanguageConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = LanguageConfigLoader(config_dir)
    return _config_loader


def get_language_config(language_code: str, config_dir: Optional[Path] = None) -> LanguageConfig:
    """
    Get configuration for a specific language.

    Args:
        language_code: Language code (e.g., 'fr', 'en')
        config_dir: Optional config directory override

    Returns:
        LanguageConfig for the specified language
    """
    loader = get_config_loader(config_dir)
    return loader.load_language_config(language_code)
