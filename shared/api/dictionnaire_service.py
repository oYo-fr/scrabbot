#!/usr/bin/env python3
"""
REST API for the Scrabbot multilingual dictionary system.

This API provides REST endpoints to allow the Godot application
to access dictionaries and validate words.

Available endpoints:
- GET /api/v1/dictionnaire/fr/valider/{mot}
- GET /api/v1/dictionnaire/en/valider/{word}
- GET /api/v1/dictionnaire/fr/definition/{mot}
- GET /api/v1/dictionnaire/en/definition/{word}
- GET /api/v1/dictionnaire/fr/recherche
- GET /api/v1/dictionnaire/en/recherche
- GET /api/v1/dictionnaire/statistiques
- GET /api/v1/dictionnaire/health

Uses FastAPI for performance and automatic documentation.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import dictionary service
sys.path.append(str(PathLib(__file__).parent.parent / "models"))
from dictionary import DictionaryConstants, DictionaryService, LanguageEnum, DictionaryWord, ValidationResult

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance
dictionary_service: Optional[DictionaryService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global dictionary_service

    # Initialization at startup
    try:
        dictionary_service = DictionaryService(
            french_db_path=DictionaryConstants.DEFAULT_FRENCH_DB_PATH,
            english_db_path=DictionaryConstants.DEFAULT_ENGLISH_DB_PATH,
        )
        logger.info("Dictionary service initialized")
        yield
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise
    finally:
        # Cleanup at shutdown
        if dictionary_service:
            dictionary_service.close_connections()
            logger.info("Connections closed")


# FastAPI application
app = FastAPI(
    title="Scrabbot Dictionaries API",
    description="REST API for word validation and access to multilingual dictionaries",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Godot
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class ReponseValidation(BaseModel):
    """Response model for word validation."""

    mot: str = Field(..., description="The validated word")
    valide: bool = Field(..., description="Whether the word is valid")
    definition: Optional[str] = Field(None, description="Word definition if found")
    points: Optional[int] = Field(None, description="Scrabble points for the word")
    langue: str = Field(..., description="Dictionary language (fr/en)")
    temps_recherche_ms: Optional[float] = Field(None, description="Search time in milliseconds")


class ReponseDefinition(BaseModel):
    """Response model for a definition."""

    mot: str = Field(..., description="The searched word")
    definition: Optional[str] = Field(None, description="Word definition")
    trouve: bool = Field(..., description="Whether the word was found")
    langue: str = Field(..., description="Dictionary language")


class MotComplet(BaseModel):
    """Model for a complete word with all its information."""

    id: Optional[int] = Field(None, description="Word ID")
    mot: str = Field(..., description="The word")
    definition: str = Field(..., description="Word definition")
    categorie_grammaticale: Optional[str] = Field(None, description="Grammatical category")
    points: int = Field(..., description="Scrabble points")
    valide_scrabble: bool = Field(..., description="Valid in Scrabble")
    longueur: int = Field(..., description="Number of letters")
    premiere_lettre: str = Field(..., description="First letter")
    derniere_lettre: str = Field(..., description="Last letter")
    langue: str = Field(..., description="Word language")
    source: str = Field(..., description="Dictionary source")


class ReponseRecherche(BaseModel):
    """Response model for a search."""

    mots: List[MotComplet] = Field(..., description="List of found words")
    nb_resultats: int = Field(..., description="Number of results")
    criteres: Dict[str, Any] = Field(..., description="Search criteria used")
    langue: str = Field(..., description="Search language")


class StatistiquesPerformance(BaseModel):
    """Model for performance statistics."""

    requetes_totales: int = Field(..., description="Total number of requests")
    temps_total_ms: float = Field(..., description="Total time in milliseconds")
    temps_moyen_ms: float = Field(..., description="Average time per request")
    requetes_cache: int = Field(..., description="Requests served by cache")


class ReponseStatistiques(BaseModel):
    """Response model for statistics."""

    performance: StatistiquesPerformance = Field(..., description="Performance statistics")
    bases_disponibles: Dict[str, bool] = Field(..., description="Database availability")
    timestamp: str = Field(..., description="Response timestamp")


class ReponseHealth(BaseModel):
    """Response model for health check."""

    statut: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="API version")
    bases: Dict[str, bool] = Field(..., description="Database status")
    timestamp: str = Field(..., description="Check timestamp")


# ============================================================================
# UTILITIES
# ============================================================================


def get_service() -> DictionaryService:
    """Gets the dictionary service instance."""
    if dictionary_service is None:
        raise HTTPException(status_code=500, detail="Dictionary service not initialized")
    return dictionary_service


def convert_validation_result(
    resultat: ValidationResult,
) -> ReponseValidation:
    """Converts a ResultatValidation to ReponseValidation."""
    return ReponseValidation(
        mot=resultat.word,
        valide=resultat.is_valid,
        definition=resultat.definition,
        points=resultat.points,
        langue=resultat.language.value if resultat.language else "unknown",
        temps_recherche_ms=resultat.search_time_ms,
    )


def convert_dictionary_word(mot: DictionaryWord) -> MotComplet:
    """Converts a MotDictionnaire to MotComplet."""
    return MotComplet(
        id=mot.id,
        mot=mot.word,
        definition=mot.definition,
        categorie_grammaticale=mot.part_of_speech,
        points=mot.points,
        valide_scrabble=mot.is_valid_scrabble,
        longueur=mot.length,
        premiere_lettre=mot.first_letter,
        derniere_lettre=mot.last_letter,
        langue=mot.language.value,
        source=mot.source,
    )


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionnaire/fr/valider/{mot}",
    response_model=ReponseValidation,
    summary="Validate French word",
    description="Validates a word in the French dictionary and returns its definition if found",
    tags=["Validation"],
)
async def validate_french_word(mot: str = Path(..., description="Word to validate", min_length=1, max_length=15)) -> ReponseValidation:
    """Validates a French word."""
    try:
        service = get_service()
        resultat = service.validate_word(mot, LanguageEnum.FRENCH)
        return convert_validation_result(resultat)
    except Exception as e:
        logger.error(f"French word validation error '{mot}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/valider/{word}",
    response_model=ReponseValidation,
    summary="Validate English word",
    description="Validates a word in the English dictionary and returns its definition if found",
    tags=["Validation"],
)
async def validate_english_word(word: str = Path(..., description="Word to validate", min_length=1, max_length=15)) -> ReponseValidation:
    """Validates an English word."""
    try:
        service = get_service()
        resultat = service.validate_word(word, LanguageEnum.ENGLISH)
        return convert_validation_result(resultat)
    except Exception as e:
        logger.error(f"English word validation error '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# DEFINITION ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionnaire/fr/definition/{mot}",
    response_model=ReponseDefinition,
    summary="Get French definition",
    description="Retrieves the definition of a French word",
    tags=["Definitions"],
)
async def get_french_definition(mot: str = Path(..., description="Word to get definition for")) -> ReponseDefinition:
    """Gets the definition of a French word."""
    try:
        service = get_service()
        definition = service.get_definition(mot, LanguageEnum.FRENCH)
        return ReponseDefinition(
            mot=mot.upper(),
            definition=definition,
            trouve=definition is not None,
            langue="fr",
        )
    except Exception as e:
        logger.error(f"French definition retrieval error '{mot}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/definition/{word}",
    response_model=ReponseDefinition,
    summary="Get English definition",
    description="Retrieves the definition of an English word",
    tags=["Definitions"],
)
async def get_english_definition(word: str = Path(..., description="Word to get definition for")) -> ReponseDefinition:
    """Gets the definition of an English word."""
    try:
        service = get_service()
        definition = service.get_definition(word, LanguageEnum.ENGLISH)
        return ReponseDefinition(
            mot=word.upper(),
            definition=definition,
            trouve=definition is not None,
            langue="en",
        )
    except Exception as e:
        logger.error(f"English definition retrieval error '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionnaire/fr/recherche",
    response_model=ReponseRecherche,
    summary="Search French words",
    description="Searches French words according to criteria",
    tags=["Search"],
)
async def search_french_words(
    longueur: Optional[int] = Query(None, ge=2, le=15, description="Word length"),
    commence_par: Optional[str] = Query(None, min_length=1, max_length=1, description="First letter"),
    finit_par: Optional[str] = Query(None, min_length=1, max_length=1, description="Last letter"),
    limite: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> ReponseRecherche:
    """Searches French words according to criteria."""
    try:
        service = get_service()

        # Parameter normalization
        commence_par_norm = commence_par.upper() if commence_par else None
        finit_par_norm = finit_par.upper() if finit_par else None

        mots = service.search_words_by_criteria(
            language=LanguageEnum.FRENCH,
            length=longueur,
            starts_with=commence_par_norm,
            ends_with=finit_par_norm,
            limit=limite,
        )

        mots_convertis = [convert_dictionary_word(mot) for mot in mots]

        criteres = {
            "longueur": longueur,
            "commence_par": commence_par_norm,
            "finit_par": finit_par_norm,
            "limite": limite,
        }

        return ReponseRecherche(
            mots=mots_convertis,
            nb_resultats=len(mots_convertis),
            criteres=criteres,
            langue="fr",
        )

    except Exception as e:
        logger.error(f"French search error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/recherche",
    response_model=ReponseRecherche,
    summary="Search English words",
    description="Searches English words according to criteria",
    tags=["Search"],
)
async def search_english_words(
    length: Optional[int] = Query(None, ge=2, le=15, description="Word length"),
    starts_with: Optional[str] = Query(None, min_length=1, max_length=1, description="First letter"),
    ends_with: Optional[str] = Query(None, min_length=1, max_length=1, description="Last letter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> ReponseRecherche:
    """Searches English words according to criteria."""
    try:
        service = get_service()

        # Parameter normalization
        starts_with_norm = starts_with.upper() if starts_with else None
        ends_with_norm = ends_with.upper() if ends_with else None

        mots = service.search_words_by_criteria(
            language=LanguageEnum.ENGLISH,
            length=length,
            starts_with=starts_with_norm,
            ends_with=ends_with_norm,
            limit=limit,
        )

        mots_convertis = [convert_dictionary_word(mot) for mot in mots]

        criteres = {
            "length": length,
            "starts_with": starts_with_norm,
            "ends_with": ends_with_norm,
            "limit": limit,
        }

        return ReponseRecherche(
            mots=mots_convertis,
            nb_resultats=len(mots_convertis),
            criteres=criteres,
            langue="en",
        )

    except Exception as e:
        logger.error(f"English search error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionnaire/statistiques",
    response_model=ReponseStatistiques,
    summary="Service statistics",
    description="Returns performance and usage statistics",
    tags=["Monitoring"],
)
async def get_statistics() -> ReponseStatistiques:
    """Gets service statistics."""
    try:
        service = get_service()
        stats_perf = service.get_performance_statistics()

        # Check database availability
        bases_dispo = {
            "francais": PathLib(DictionaryConstants.DEFAULT_FRENCH_DB_PATH).exists(),
            "anglais": PathLib(DictionaryConstants.DEFAULT_ENGLISH_DB_PATH).exists(),
        }

        return ReponseStatistiques(
            performance=StatistiquesPerformance(**stats_perf),
            bases_disponibles=bases_dispo,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/health",
    response_model=ReponseHealth,
    summary="Health check",
    description="Checks the service health status",
    tags=["Monitoring"],
)
async def health_check() -> ReponseHealth:
    """Service health check."""
    try:
        # Database verification
        bases = {
            "francais": PathLib(DictionaryConstants.DEFAULT_FRENCH_DB_PATH).exists(),
            "anglais": PathLib(DictionaryConstants.DEFAULT_ENGLISH_DB_PATH).exists(),
        }

        # Global status determination
        statut = "healthy" if any(bases.values()) else "unhealthy"

        return ReponseHealth(
            statut=statut,
            version="1.0.0",
            bases=bases,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return ReponseHealth(
            statut="unhealthy",
            version="1.0.0",
            bases={"francais": False, "anglais": False},
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionnaire/",
    summary="API documentation",
    description="Returns the list of available endpoints",
    tags=["Utilities"],
)
async def api_documentation():
    """Documentation of available endpoints."""
    return {
        "api": "Scrabbot Dictionaries",
        "version": "1.0.0",
        "endpoints": {
            "validation": {
                "fr": "/api/v1/dictionnaire/fr/valider/{mot}",
                "en": "/api/v1/dictionnaire/en/valider/{word}",
            },
            "definitions": {
                "fr": "/api/v1/dictionnaire/fr/definition/{mot}",
                "en": "/api/v1/dictionnaire/en/definition/{word}",
            },
            "search": {
                "fr": "/api/v1/dictionnaire/fr/recherche",
                "en": "/api/v1/dictionnaire/en/recherche",
            },
            "monitoring": {
                "statistics": "/api/v1/dictionnaire/statistiques",
                "health": "/api/v1/dictionnaire/health",
            },
        },
        "documentation": "/docs",
        "openapi": "/openapi.json",
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.exception_handler(Exception)
async def global_error_handler(request, exc):
    """Global error handler."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


# ============================================================================
# LAUNCH SCRIPT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "dictionnaire_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
