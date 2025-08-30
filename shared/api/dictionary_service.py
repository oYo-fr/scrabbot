#!/usr/bin/env python3
"""
REST API for the Scrabbot multilingual dictionary system.

This API provides REST endpoints to allow the Godot application
to access dictionaries and validate words.

Available endpoints:
- GET /api/v1/dictionary/validate/{word}?language={lang}
- GET /api/v1/dictionary/definition/{word}?language={lang}
- GET /api/v1/dictionary/search?language={lang}
- GET /api/v1/dictionary/statistics
- GET /api/v1/dictionary/health

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
from shared.models.dictionary import DictionaryService, DictionaryWord, ValidationResult

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance
dictionary_service: Optional[DictionaryService] = None
global_settings: Optional[Any] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    global dictionary_service

    # Initialization at startup
    try:
        # Use real database paths
        from bot.config.settings import Settings

        settings = Settings()  # type: ignore[call-arg]
        global global_settings
        global_settings = settings

        dictionary_service = DictionaryService(
            base_path=settings.dictionaries_base_path
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

    word: str = Field(..., description="The validated word")
    valid: bool = Field(..., description="Whether the word is valid")
    definition: Optional[str] = Field(None, description="Word definition if found")
    points: Optional[int] = Field(None, description="Scrabble points for the word")
    language: str = Field(..., description="Dictionary language (fr/en)")
    search_time_ms: Optional[float] = Field(
        None, description="Search time in milliseconds"
    )


class ReponseDefinition(BaseModel):
    """Response model for a definition."""

    word: str = Field(..., description="The searched word")
    definition: Optional[str] = Field(None, description="Word definition")
    found: bool = Field(..., description="Whether the word was found")
    language: str = Field(..., description="Dictionary language")


class MotComplet(BaseModel):
    """Model for a complete word with all its information."""

    id: Optional[int] = Field(None, description="Word ID")
    word: str = Field(..., description="The word")
    definition: str = Field(..., description="Word definition")
    part_of_speech: Optional[str] = Field(None, description="Grammatical category")
    points: int = Field(..., description="Scrabble points")
    scrabble_valid: bool = Field(..., description="Valid in Scrabble")
    length: int = Field(..., description="Number of letters")
    first_letter: str = Field(..., description="First letter")
    last_letter: str = Field(..., description="Last letter")
    language: str = Field(..., description="Word language")
    source: str = Field(..., description="Dictionary source")


class ReponseRecherche(BaseModel):
    """Response model for a search."""

    words: List[MotComplet] = Field(..., description="List of found words")
    results_count: int = Field(..., description="Number of results")
    criteria: Dict[str, Any] = Field(..., description="Search criteria used")
    language: str = Field(..., description="Search language")


class StatistiquesPerformance(BaseModel):
    """Model for performance statistics."""

    total_requests: int = Field(..., description="Total number of requests")
    total_time_ms: float = Field(..., description="Total time in milliseconds")
    average_time_ms: float = Field(..., description="Average time per request")
    cache_requests: int = Field(..., description="Requests served by cache")


class ReponseStatistiques(BaseModel):
    """Response model for statistics."""

    performance: StatistiquesPerformance = Field(
        ..., description="Performance statistics"
    )
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
        raise HTTPException(
            status_code=500, detail="Dictionary service not initialized"
        )
    return dictionary_service


def convert_validation_result(
    result: ValidationResult,
) -> ReponseValidation:
    """Converts a ValidationResult to ReponseValidation."""
    return ReponseValidation(
        word=result.word,
        valid=result.is_valid,
        definition=result.definition,
        points=result.points,
        language=result.language if result.language else "unknown",
        search_time_ms=result.search_time_ms,
    )


def convert_dictionary_word(mot: DictionaryWord) -> MotComplet:
    """Converts a DictionaryWord to MotComplet."""
    return MotComplet(
        id=mot.id,
        word=mot.word,
        definition=mot.definition,
        part_of_speech=mot.part_of_speech,
        points=mot.points,
        scrabble_valid=mot.is_valid_scrabble,
        length=mot.length,
        first_letter=mot.first_letter,
        last_letter=mot.last_letter,
        language=mot.language,
        source=mot.source,
    )


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionary/validate/{word}",
    response_model=ReponseValidation,
    summary="Validate word",
    description="Validates a word in the specified dictionary and returns its definition if found",
    tags=["Validation"],
)
async def validate_word(
    word: str = Path(..., description="Word to validate", min_length=1, max_length=15),
    language: str = Query(
        ..., description="Dictionary language (fr/en)", regex="^(fr|en)$"
    ),
) -> ReponseValidation:
    """Validates a word in the specified language dictionary."""
    try:
        service = get_service()
        # Language is now passed as string directly
        result = service.validate_word(word, language)
        return convert_validation_result(result)
    except Exception as e:
        logger.error(f"Word validation error '{word}' in '{language}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# DEFINITION ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionary/definition/{word}",
    response_model=ReponseDefinition,
    summary="Get word definition",
    description="Retrieves the definition of a word in the specified language",
    tags=["Definitions"],
)
async def get_definition(
    word: str = Path(..., description="Word to get definition for"),
    language: str = Query(
        ..., description="Dictionary language (fr/en)", regex="^(fr|en)$"
    ),
) -> ReponseDefinition:
    """Gets the definition of a word in the specified language."""
    try:
        service = get_service()
        # Language is now passed as string directly
        definition = service.get_definition(word, language)
        return ReponseDefinition(
            word=word.upper(),
            definition=definition,
            found=definition is not None,
            language=language,
        )
    except Exception as e:
        logger.error(f"Definition retrieval error '{word}' in '{language}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionary/search",
    response_model=ReponseRecherche,
    summary="Search words",
    description="Searches words according to criteria in the specified language",
    tags=["Search"],
)
async def search_words(
    language: str = Query(
        ..., description="Dictionary language (fr/en)", regex="^(fr|en)$"
    ),
    length: Optional[int] = Query(None, ge=2, le=15, description="Word length"),
    starts_with: Optional[str] = Query(
        None, min_length=1, max_length=1, description="First letter"
    ),
    ends_with: Optional[str] = Query(
        None, min_length=1, max_length=1, description="Last letter"
    ),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
) -> ReponseRecherche:
    """Searches words according to criteria in the specified language."""
    try:
        service = get_service()
        # Language is now passed as string directly

        # Parameter normalization
        starts_with_norm = starts_with.upper() if starts_with else None
        ends_with_norm = ends_with.upper() if ends_with else None

        mots = service.search_words_by_criteria(
            language=language,
            length=length,
            starts_with=starts_with_norm,
            ends_with=ends_with_norm,
            limit=limit,
        )

        mots_convertis = [convert_dictionary_word(mot) for mot in mots]

        criteres = {
            "language": language,
            "length": length,
            "starts_with": starts_with_norm,
            "ends_with": ends_with_norm,
            "limit": limit,
        }

        return ReponseRecherche(
            words=mots_convertis,
            results_count=len(mots_convertis),
            criteria=criteres,
            language=language,
        )

    except Exception as e:
        logger.error(f"Search error in '{language}': {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================


@app.get(
    "/api/v1/dictionary/statistics",
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
            "francais": PathLib(
                global_settings.dictionaries_base_path, "fr.db"
            ).exists()
            if global_settings
            else False,
            "anglais": PathLib(global_settings.dictionaries_base_path, "en.db").exists()
            if global_settings
            else False,
        }

        # Convert float values to int for StatistiquesPerformance
        stats_perf_converted = {
            "total_requests": int(stats_perf["total_requests"]),
            "total_time_ms": stats_perf["total_time_ms"],
            "average_time_ms": stats_perf["average_time_ms"],
            "cache_requests": int(stats_perf["cache_requests"]),
        }

        return ReponseStatistiques(
            performance=StatistiquesPerformance(**stats_perf_converted),
            bases_disponibles=bases_dispo,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get(
    "/api/v1/dictionary/health",
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
            "francais": PathLib(
                global_settings.dictionaries_base_path, "fr.db"
            ).exists()
            if global_settings
            else False,
            "anglais": PathLib(global_settings.dictionaries_base_path, "en.db").exists()
            if global_settings
            else False,
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
    "/api/v1/dictionary/",
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
            "validation": "/api/v1/dictionary/validate/{word}?language={fr|en}",
            "definitions": "/api/v1/dictionary/definition/{word}?language={fr|en}",
            "search": "/api/v1/dictionary/search?language={fr|en}",
            "monitoring": {
                "statistics": "/api/v1/dictionary/statistics",
                "health": "/api/v1/dictionary/health",
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
        "dictionary_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
