"""
Endpoints pour la gestion des statuts - Pour usage futur avec React.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.models.video_model import VideoStatusResponse, VideoStatus

# Création du router pour les endpoints de statut
router = APIRouter(prefix="/status", tags=["status"])


@router.get(
    "/health",
    summary="Vérification globale de l'état de l'API",
    description="Endpoint principal pour vérifier que l'API fonctionne correctement."
)
async def api_health_check():
    """
    Endpoint de vérification de l'état global de l'API.
    
    Returns:
        Dict: Statut global de l'API
    """
    return {
        "status": "healthy",
        "api_name": "VidP FastAPI Service",
        "version": "1.0.0",
        "message": "API VidP opérationnelle",
        "services": {
            "video_upload": "operational",
            "file_storage": "operational",
            "mongodb": "not_configured",
            "kubernetes": "not_configured"
        }
    }


@router.get(
    "/video/{video_id}",
    response_model=VideoStatusResponse,
    summary="Statut d'une vidéo spécifique",
    description="Retourne le statut de traitement d'une vidéo par son ID."
)
async def get_video_status(video_id: str):
    """
    Endpoint pour récupérer le statut d'une vidéo spécifique.
    
    Args:
        video_id: Identifiant unique de la vidéo
        
    Returns:
        VideoStatusResponse: Statut de la vidéo
    """
    try:
        response = VideoStatusResponse(
            video_id=video_id,
            status=VideoStatus.UPLOADED,
            message="Vidéo en attente de traitement",
            processing_progress=0.0
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )


@router.get(
    "/videos/all",
    response_model=List[VideoStatusResponse],
    summary="Statut de toutes les vidéos",
    description="Retourne le statut de toutes les vidéos en cours de traitement."
)
async def get_all_videos_status():
    """
    Endpoint pour récupérer le statut de toutes les vidéos.
    
    Returns:
        List[VideoStatusResponse]: Liste des statuts de toutes les vidéos
    """
    try:
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statuts: {str(e)}"
        )
