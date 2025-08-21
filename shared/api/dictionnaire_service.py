#!/usr/bin/env python3
"""
API REST pour le système de dictionnaires multilingues Scrabbot.

Cette API fournit les endpoints REST pour permettre à l'application Godot
d'accéder aux dictionnaires et de valider des mots.

Endpoints disponibles :
- GET /api/v1/dictionnaire/fr/valider/{mot}
- GET /api/v1/dictionnaire/en/valider/{word}
- GET /api/v1/dictionnaire/fr/definition/{mot}
- GET /api/v1/dictionnaire/en/definition/{word}
- GET /api/v1/dictionnaire/fr/recherche
- GET /api/v1/dictionnaire/en/recherche
- GET /api/v1/dictionnaire/statistiques
- GET /api/v1/dictionnaire/health

Utilisation avec FastAPI pour les performances et la documentation automatique.
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys
import logging
from pathlib import Path as PathLib
import time
from contextlib import asynccontextmanager

# Import du service dictionnaire
sys.path.append(str(PathLib(__file__).parent.parent / "models"))
from dictionnaire import DictionnaireService, LangueEnum, ResultatValidation, MotDictionnaire, ConstantesDictionnaire

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance globale du service
service_dictionnaire: Optional[DictionnaireService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application."""
    global service_dictionnaire
    
    # Initialisation au démarrage
    try:
        service_dictionnaire = DictionnaireService(
            chemin_base_fr=ConstantesDictionnaire.CHEMIN_BASE_FR_DEFAUT,
            chemin_base_en=ConstantesDictionnaire.CHEMIN_BASE_EN_DEFAUT
        )
        logger.info("Service dictionnaire initialisé")
        yield
    except Exception as e:
        logger.error(f"Erreur initialisation service: {e}")
        raise
    finally:
        # Nettoyage à la fermeture
        if service_dictionnaire:
            service_dictionnaire.fermer_connexions()
            logger.info("Connexions fermées")


# Application FastAPI
app = FastAPI(
    title="API Dictionnaires Scrabbot",
    description="API REST pour la validation de mots et l'accès aux dictionnaires multilingues",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour Godot
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ============================================================================
# MODÈLES PYDANTIC
# ============================================================================

class ReponseValidation(BaseModel):
    """Modèle de réponse pour la validation d'un mot."""
    mot: str = Field(..., description="Le mot validé")
    valide: bool = Field(..., description="Si le mot est valide")
    definition: Optional[str] = Field(None, description="Définition du mot si trouvé")
    points: Optional[int] = Field(None, description="Points Scrabble du mot")
    langue: str = Field(..., description="Langue du dictionnaire (fr/en)")
    temps_recherche_ms: Optional[float] = Field(None, description="Temps de recherche en millisecondes")


class ReponseDefinition(BaseModel):
    """Modèle de réponse pour une définition."""
    mot: str = Field(..., description="Le mot recherché")
    definition: Optional[str] = Field(None, description="Définition du mot")
    trouve: bool = Field(..., description="Si le mot a été trouvé")
    langue: str = Field(..., description="Langue du dictionnaire")


class MotComplet(BaseModel):
    """Modèle pour un mot complet avec toutes ses informations."""
    id: Optional[int] = Field(None, description="ID du mot")
    mot: str = Field(..., description="Le mot")
    definition: str = Field(..., description="Définition du mot")
    categorie_grammaticale: Optional[str] = Field(None, description="Catégorie grammaticale")
    points: int = Field(..., description="Points Scrabble")
    valide_scrabble: bool = Field(..., description="Valide au Scrabble")
    longueur: int = Field(..., description="Nombre de lettres")
    premiere_lettre: str = Field(..., description="Première lettre")
    derniere_lettre: str = Field(..., description="Dernière lettre")
    langue: str = Field(..., description="Langue du mot")
    source: str = Field(..., description="Source du dictionnaire")


class ReponseRecherche(BaseModel):
    """Modèle de réponse pour une recherche."""
    mots: List[MotComplet] = Field(..., description="Liste des mots trouvés")
    nb_resultats: int = Field(..., description="Nombre de résultats")
    criteres: Dict[str, Any] = Field(..., description="Critères de recherche utilisés")
    langue: str = Field(..., description="Langue de recherche")


class StatistiquesPerformance(BaseModel):
    """Modèle pour les statistiques de performance."""
    requetes_totales: int = Field(..., description="Nombre total de requêtes")
    temps_total_ms: float = Field(..., description="Temps total en millisecondes")
    temps_moyen_ms: float = Field(..., description="Temps moyen par requête")
    requetes_cache: int = Field(..., description="Requêtes servies par le cache")


class ReponseStatistiques(BaseModel):
    """Modèle de réponse pour les statistiques."""
    performance: StatistiquesPerformance = Field(..., description="Statistiques de performance")
    bases_disponibles: Dict[str, bool] = Field(..., description="Disponibilité des bases")
    timestamp: str = Field(..., description="Timestamp de la réponse")


class ReponseHealth(BaseModel):
    """Modèle de réponse pour le health check."""
    statut: str = Field(..., description="Statut du service (healthy/unhealthy)")
    version: str = Field(..., description="Version de l'API")
    bases: Dict[str, bool] = Field(..., description="Statut des bases de données")
    timestamp: str = Field(..., description="Timestamp du check")


# ============================================================================
# UTILITAIRES
# ============================================================================

def obtenir_service() -> DictionnaireService:
    """Obtient l'instance du service dictionnaire."""
    if service_dictionnaire is None:
        raise HTTPException(
            status_code=500,
            detail="Service dictionnaire non initialisé"
        )
    return service_dictionnaire


def convertir_resultat_validation(resultat: ResultatValidation) -> ReponseValidation:
    """Convertit un ResultatValidation en ReponseValidation."""
    return ReponseValidation(
        mot=resultat.mot,
        valide=resultat.valide,
        definition=resultat.definition,
        points=resultat.points,
        langue=resultat.langue.value if resultat.langue else "unknown",
        temps_recherche_ms=resultat.temps_recherche_ms
    )


def convertir_mot_dictionnaire(mot: MotDictionnaire) -> MotComplet:
    """Convertit un MotDictionnaire en MotComplet."""
    return MotComplet(
        id=mot.id,
        mot=mot.mot,
        definition=mot.definition,
        categorie_grammaticale=mot.categorie_grammaticale,
        points=mot.points,
        valide_scrabble=mot.valide_scrabble,
        longueur=mot.longueur,
        premiere_lettre=mot.premiere_lettre,
        derniere_lettre=mot.derniere_lettre,
        langue=mot.langue.value,
        source=mot.source
    )


# ============================================================================
# ENDPOINTS DE VALIDATION
# ============================================================================

@app.get(
    "/api/v1/dictionnaire/fr/valider/{mot}",
    response_model=ReponseValidation,
    summary="Valider un mot français",
    description="Valide un mot dans le dictionnaire français et retourne sa définition si trouvé",
    tags=["Validation"]
)
async def valider_mot_francais(
    mot: str = Path(..., description="Mot à valider", min_length=1, max_length=15)
) -> ReponseValidation:
    """Valide un mot français."""
    try:
        service = obtenir_service()
        resultat = service.valider_mot(mot, LangueEnum.FRANCAIS)
        return convertir_resultat_validation(resultat)
    except Exception as e:
        logger.error(f"Erreur validation mot français '{mot}': {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/valider/{word}",
    response_model=ReponseValidation,
    summary="Valider un mot anglais",
    description="Valide un mot dans le dictionnaire anglais et retourne sa définition si trouvé",
    tags=["Validation"]
)
async def valider_mot_anglais(
    word: str = Path(..., description="Word to validate", min_length=1, max_length=15)
) -> ReponseValidation:
    """Valide un mot anglais."""
    try:
        service = obtenir_service()
        resultat = service.valider_mot(word, LangueEnum.ANGLAIS)
        return convertir_resultat_validation(resultat)
    except Exception as e:
        logger.error(f"Erreur validation mot anglais '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# ============================================================================
# ENDPOINTS DE DÉFINITIONS
# ============================================================================

@app.get(
    "/api/v1/dictionnaire/fr/definition/{mot}",
    response_model=ReponseDefinition,
    summary="Obtenir définition française",
    description="Récupère la définition d'un mot français",
    tags=["Définitions"]
)
async def obtenir_definition_francaise(
    mot: str = Path(..., description="Mot dont on veut la définition")
) -> ReponseDefinition:
    """Obtient la définition d'un mot français."""
    try:
        service = obtenir_service()
        definition = service.obtenir_definition(mot, LangueEnum.FRANCAIS)
        return ReponseDefinition(
            mot=mot.upper(),
            definition=definition,
            trouve=definition is not None,
            langue="fr"
        )
    except Exception as e:
        logger.error(f"Erreur récupération définition française '{mot}': {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/definition/{word}",
    response_model=ReponseDefinition,
    summary="Obtenir définition anglaise",
    description="Récupère la définition d'un mot anglais",
    tags=["Définitions"]
)
async def obtenir_definition_anglaise(
    word: str = Path(..., description="Word to get definition for")
) -> ReponseDefinition:
    """Obtient la définition d'un mot anglais."""
    try:
        service = obtenir_service()
        definition = service.obtenir_definition(word, LangueEnum.ANGLAIS)
        return ReponseDefinition(
            mot=word.upper(),
            definition=definition,
            trouve=definition is not None,
            langue="en"
        )
    except Exception as e:
        logger.error(f"Erreur récupération définition anglaise '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# ============================================================================
# ENDPOINTS DE RECHERCHE
# ============================================================================

@app.get(
    "/api/v1/dictionnaire/fr/recherche",
    response_model=ReponseRecherche,
    summary="Rechercher mots français",
    description="Recherche des mots français selon des critères",
    tags=["Recherche"]
)
async def rechercher_mots_francais(
    longueur: Optional[int] = Query(None, ge=2, le=15, description="Longueur du mot"),
    commence_par: Optional[str] = Query(None, min_length=1, max_length=1, description="Première lettre"),
    finit_par: Optional[str] = Query(None, min_length=1, max_length=1, description="Dernière lettre"),
    limite: int = Query(50, ge=1, le=500, description="Nombre maximum de résultats")
) -> ReponseRecherche:
    """Recherche des mots français selon des critères."""
    try:
        service = obtenir_service()
        
        # Normalisation des paramètres
        commence_par_norm = commence_par.upper() if commence_par else None
        finit_par_norm = finit_par.upper() if finit_par else None
        
        mots = service.rechercher_mots_par_criteres(
            langue=LangueEnum.FRANCAIS,
            longueur=longueur,
            commence_par=commence_par_norm,
            finit_par=finit_par_norm,
            limite=limite
        )
        
        mots_convertis = [convertir_mot_dictionnaire(mot) for mot in mots]
        
        criteres = {
            "longueur": longueur,
            "commence_par": commence_par_norm,
            "finit_par": finit_par_norm,
            "limite": limite
        }
        
        return ReponseRecherche(
            mots=mots_convertis,
            nb_resultats=len(mots_convertis),
            criteres=criteres,
            langue="fr"
        )
        
    except Exception as e:
        logger.error(f"Erreur recherche française: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/en/recherche",
    response_model=ReponseRecherche,
    summary="Rechercher mots anglais",
    description="Recherche des mots anglais selon des critères",
    tags=["Recherche"]
)
async def rechercher_mots_anglais(
    length: Optional[int] = Query(None, ge=2, le=15, description="Word length"),
    starts_with: Optional[str] = Query(None, min_length=1, max_length=1, description="First letter"),
    ends_with: Optional[str] = Query(None, min_length=1, max_length=1, description="Last letter"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
) -> ReponseRecherche:
    """Recherche des mots anglais selon des critères."""
    try:
        service = obtenir_service()
        
        # Normalisation des paramètres
        starts_with_norm = starts_with.upper() if starts_with else None
        ends_with_norm = ends_with.upper() if ends_with else None
        
        mots = service.rechercher_mots_par_criteres(
            langue=LangueEnum.ANGLAIS,
            longueur=length,
            commence_par=starts_with_norm,
            finit_par=ends_with_norm,
            limite=limit
        )
        
        mots_convertis = [convertir_mot_dictionnaire(mot) for mot in mots]
        
        criteres = {
            "length": length,
            "starts_with": starts_with_norm,
            "ends_with": ends_with_norm,
            "limit": limit
        }
        
        return ReponseRecherche(
            mots=mots_convertis,
            nb_resultats=len(mots_convertis),
            criteres=criteres,
            langue="en"
        )
        
    except Exception as e:
        logger.error(f"Erreur recherche anglaise: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


# ============================================================================
# ENDPOINTS DE MONITORING
# ============================================================================

@app.get(
    "/api/v1/dictionnaire/statistiques",
    response_model=ReponseStatistiques,
    summary="Statistiques du service",
    description="Retourne les statistiques de performance et d'utilisation",
    tags=["Monitoring"]
)
async def obtenir_statistiques() -> ReponseStatistiques:
    """Obtient les statistiques du service."""
    try:
        service = obtenir_service()
        stats_perf = service.obtenir_statistiques_performance()
        
        # Vérification disponibilité des bases
        bases_dispo = {
            "francais": PathLib(ConstantesDictionnaire.CHEMIN_BASE_FR_DEFAUT).exists(),
            "anglais": PathLib(ConstantesDictionnaire.CHEMIN_BASE_EN_DEFAUT).exists()
        }
        
        return ReponseStatistiques(
            performance=StatistiquesPerformance(**stats_perf),
            bases_disponibles=bases_dispo,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération statistiques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.get(
    "/api/v1/dictionnaire/health",
    response_model=ReponseHealth,
    summary="Health check",
    description="Vérifie l'état de santé du service",
    tags=["Monitoring"]
)
async def health_check() -> ReponseHealth:
    """Health check du service."""
    try:
        # Vérification bases de données
        bases = {
            "francais": PathLib(ConstantesDictionnaire.CHEMIN_BASE_FR_DEFAUT).exists(),
            "anglais": PathLib(ConstantesDictionnaire.CHEMIN_BASE_EN_DEFAUT).exists()
        }
        
        # Détermination du statut global
        statut = "healthy" if any(bases.values()) else "unhealthy"
        
        return ReponseHealth(
            statut=statut,
            version="1.0.0",
            bases=bases,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return ReponseHealth(
            statut="unhealthy",
            version="1.0.0",
            bases={"francais": False, "anglais": False},
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )


# ============================================================================
# ENDPOINTS UTILITAIRES
# ============================================================================

@app.get(
    "/api/v1/dictionnaire/",
    summary="Documentation de l'API",
    description="Retourne la liste des endpoints disponibles",
    tags=["Utilitaires"]
)
async def documentation_api():
    """Documentation des endpoints disponibles."""
    return {
        "api": "Dictionnaires Scrabbot",
        "version": "1.0.0",
        "endpoints": {
            "validation": {
                "fr": "/api/v1/dictionnaire/fr/valider/{mot}",
                "en": "/api/v1/dictionnaire/en/valider/{word}"
            },
            "definitions": {
                "fr": "/api/v1/dictionnaire/fr/definition/{mot}",
                "en": "/api/v1/dictionnaire/en/definition/{word}"
            },
            "recherche": {
                "fr": "/api/v1/dictionnaire/fr/recherche",
                "en": "/api/v1/dictionnaire/en/recherche"
            },
            "monitoring": {
                "statistiques": "/api/v1/dictionnaire/statistiques",
                "health": "/api/v1/dictionnaire/health"
            }
        },
        "documentation": "/docs",
        "openapi": "/openapi.json"
    }


# ============================================================================
# GESTIONNAIRE D'ERREURS
# ============================================================================

@app.exception_handler(Exception)
async def gestionnaire_erreur_globale(request, exc):
    """Gestionnaire d'erreur global."""
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "detail": "Une erreur inattendue s'est produite",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )


# ============================================================================
# SCRIPT DE LANCEMENT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "dictionnaire_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
