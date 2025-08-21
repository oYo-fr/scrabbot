---
description: MANDATORY - All code must be written in English only
globs: ["**/*.py", "**/*.js", "**/*.ts", "**/*.gd", "**/*.cs"]
alwaysApply: true
priority: 1000
---

# MANDATORY RULE: English-Only Code

## Overview
This rule is **IMPERATIVE** and **OVERRIDES** all other naming conventions. All code in this project MUST be written in English.

## Code Standards

### Variable Names
- **REQUIRED**: Use English snake_case for variables
- **FORBIDDEN**: French variable names
```python
# ✅ CORRECT
word_count = 10
dictionary_service = DictionaryService()
is_valid = True

# ❌ FORBIDDEN
nb_mots = 10
service_dictionnaire = ServiceDictionnaire()
est_valide = True
```

### Function Names
- **REQUIRED**: Use English snake_case for functions
- **FORBIDDEN**: French function names
```python
# ✅ CORRECT
def validate_word(word: str) -> bool:
    pass

def get_definition(word: str) -> str:
    pass

# ❌ FORBIDDEN
def valider_mot(mot: str) -> bool:
    pass

def obtenir_definition(mot: str) -> str:
    pass
```

### Class Names
- **REQUIRED**: Use English PascalCase for classes
- **FORBIDDEN**: French class names
```python
# ✅ CORRECT
class DictionaryService:
    pass

class WordValidator:
    pass

# ❌ FORBIDDEN
class ServiceDictionnaire:
    pass

class ValidateurMot:
    pass
```

### Comments and Documentation
- **REQUIRED**: All comments in English
- **REQUIRED**: All docstrings in English
- **FORBIDDEN**: French comments or documentation

```python
# ✅ CORRECT
def validate_word(word: str) -> bool:
    """
    Validates a word against the dictionary.
    
    Args:
        word: The word to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check if word exists in database
    return word in dictionary

# ❌ FORBIDDEN
def validate_word(mot: str) -> bool:
    """
    Valide un mot contre le dictionnaire.
    
    Args:
        mot: Le mot à valider
        
    Returns:
        True si valide, False sinon
    """
    # Vérifier si le mot existe en base
    return mot in dictionnaire
```

### Database Schema
- **REQUIRED**: English column names
- **REQUIRED**: English table names
```sql
-- ✅ CORRECT
CREATE TABLE french_words (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL,
    is_valid_scrabble BOOLEAN
);

-- ❌ FORBIDDEN  
CREATE TABLE mots_fr (
    id INTEGER PRIMARY KEY,
    mot TEXT NOT NULL,
    definition TEXT NOT NULL,
    valide_scrabble BOOLEAN
);
```

### Constants
- **REQUIRED**: English UPPER_CASE constants
```python
# ✅ CORRECT
MAX_WORD_LENGTH = 15
DEFAULT_LANGUAGE = "fr"
SCRABBLE_LETTER_POINTS = {...}

# ❌ FORBIDDEN
LONGUEUR_MAX_MOT = 15
LANGUE_DEFAUT = "fr" 
POINTS_LETTRES_SCRABBLE = {...}
```

## File Naming
- **REQUIRED**: English file names
- **EXAMPLES**: 
  - `dictionary_service.py` ✅
  - `word_validator.py` ✅
  - `test_dictionary_api.py` ✅
  - `service_dictionnaire.py` ❌

## API Endpoints
- **REQUIRED**: English endpoint names
```python
# ✅ CORRECT
@app.get("/api/v1/dictionary/fr/validate/{word}")
@app.get("/api/v1/dictionary/en/validate/{word}")

# ❌ FORBIDDEN
@app.get("/api/v1/dictionnaire/fr/valider/{mot}")
@app.get("/api/v1/dictionnaire/en/valider/{word}")
```

## Exceptions
- **User-facing content**: Can be in French (messages, UI text)
- **Domain-specific terms**: Keep original language (e.g., "Scrabble" remains "Scrabble")
- **External APIs**: Follow their naming convention

## Enforcement
- This rule is **MANDATORY** and **NON-NEGOTIABLE**
- All code reviews must enforce this rule
- Any French code must be refactored immediately
- No exceptions without explicit approval

## Migration
When refactoring existing French code:
1. Update variable names to English
2. Update function names to English  
3. Update class names to English
4. Update comments to English
5. Update docstrings to English
6. Update database schema if needed
7. Update API endpoints if needed
