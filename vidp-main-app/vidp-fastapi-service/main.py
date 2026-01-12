"""
Point d'entrée principal de l'application FastAPI VidP.
Service backend pour la gestion des uploads vidéo et l'orchestration du traitement.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.endpoints_video import router as video_router
from app.api.v1.endpoints_status import router as status_router
from app.api.v1.endpoints_processing import router as processing_router
from app.db.mongodb_connector import mongodb_connector


# Création de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Service backend FastAPI pour la gestion des uploads vidéo et l'orchestration du traitement",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour permettre les requêtes depuis React
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Inclusion des routers API v1
app.include_router(video_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")
app.include_router(processing_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """
    Initialisation au démarrage de l'application.
    Établit la connexion MongoDB.
    """
    try:
        connected = await mongodb_connector.connect()
        if connected:
            print("✓ MongoDB connecté avec succès")
        else:
            print("⚠ MongoDB non disponible - fonctionnalités de stockage limitées")
    except Exception as e:
        print(f"⚠ Erreur de connexion MongoDB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Nettoyage lors de l'arrêt de l'application.
    Ferme la connexion MongoDB.
    """
    try:
        await mongodb_connector.disconnect()
        print("✓ MongoDB déconnecté")
    except Exception as e:
        print(f"⚠ Erreur lors de la déconnexion MongoDB: {e}")


@app.get("/", tags=["root"])
async def root():
    """
    Endpoint racine de l'API.
    
    Returns:
        Dict: Informations de base sur l'API
    """
    return {
        "message": "Bienvenue sur l'API VidP",
        "description": "Service backend FastAPI pour le traitement vidéo local",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload_video": "/api/v1/videos/upload",
            "video_health": "/api/v1/videos/health",
            "storage_stats": "/api/v1/videos/stats",
            "api_health": "/api/v1/status/health",
            "language_detection": "/api/v1/processing/language-detection",
            "compression": "/api/v1/processing/compression",
            "subtitles": "/api/v1/processing/subtitles",
            "animal_detection": "/api/v1/processing/animal-detection",
            "animal_detection_classes": "/api/v1/processing/animal-detection/classes",
            "processing_health": "/api/v1/processing/health"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint de vérification de l'état général de l'API.
    
    Returns:
        Dict: Statut de santé de l'API
    """
    mongodb_status = mongodb_connector.client is not None
    return {
        "status": "healthy",
        "message": "VidP FastAPI Service is running",
        "storage_configured": True,
        "mongodb_configured": mongodb_status,
        "kubernetes_configured": False  # Pour usage futur
    }


# Gestionnaire d'erreur global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Gestionnaire global des exceptions non capturées.
    
    Args:
        request: Requête HTTP
        exc: Exception levée
        
    Returns:
        JSONResponse: Réponse d'erreur formatée
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "detail": "Une erreur inattendue s'est produite",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    # Lancement du serveur de développement
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,  # Rechargement automatique en développement
        log_level="info"
    )