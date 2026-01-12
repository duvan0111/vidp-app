"""
Endpoints pour la gestion des vidéos - Upload et statut.
"""
import uuid
from datetime import datetime
from typing import List
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse

from app.models.video_model import VideoUploadResponse, VideoStatus, VideoMetadata, ErrorResponse
from app.services.file_storage import FileStorageService
from app.db.mongodb_connector import mongodb_connector
from app.core.config import settings

# Création du router pour les endpoints vidéo
router = APIRouter(prefix="/videos", tags=["videos"])


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload d'une vidéo",
    description="Permet d'uploader une vidéo qui sera stockée localement pour traitement ultérieur."
)
async def upload_video(file: UploadFile = File(..., description="Fichier vidéo à uploader")):
    """
    Endpoint pour uploader une vidéo.
    
    Args:
        file: Fichier vidéo uploadé
        
    Returns:
        VideoUploadResponse: Informations sur la vidéo uploadée
        
    Raises:
        HTTPException: En cas d'erreur lors de l'upload
    """
    try:
        # Génération d'un ID unique pour la vidéo
        video_id = str(uuid.uuid4())
        
        # Sauvegarde du fichier via le service de stockage
        unique_filename, full_path, file_size = await FileStorageService.save_video_file(file)
        
        # Création des métadonnées
        upload_time = datetime.now()
        metadata = VideoMetadata(
            video_id=video_id,
            original_filename=file.filename,
            file_path=full_path,
            file_size=file_size,
            content_type=file.content_type,
            status=VideoStatus.UPLOADED,
            upload_time=upload_time
        )
        
        # Sauvegarde dans MongoDB (si disponible)
        if mongodb_connector.client:
            await mongodb_connector.save_video_metadata(metadata)
        
        # Création de la réponse
        response = VideoUploadResponse(
            video_id=video_id,
            filename=file.filename,
            file_path=full_path,
            file_size=file_size,
            content_type=file.content_type,
            status=VideoStatus.UPLOADED,
            upload_time=upload_time,
            message=f"Vidéo '{file.filename}' uploadée avec succès"
        )
        
        return response
        
    except HTTPException:
        # Re-lever les HTTPException du service de stockage
        raise
    except Exception as e:
        # Gestion des erreurs inattendues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de l'upload: {str(e)}"
        )


@router.get(
    "/health",
    summary="Vérification de l'état du service",
    description="Endpoint de santé pour vérifier que le service vidéo fonctionne correctement."
)
async def health_check():
    """
    Endpoint de vérification de l'état du service vidéo.
    
    Returns:
        Dict: Statut du service
    """
    return {
        "status": "healthy",
        "service": "video-upload",
        "message": "Service d'upload vidéo opérationnel"
    }


@router.get(
    "/stats",
    summary="Statistiques du stockage",
    description="Retourne des statistiques sur l'utilisation du stockage local."
)
async def get_storage_stats():
    """
    Endpoint pour obtenir des statistiques sur le stockage.
    
    Returns:
        Dict: Statistiques du stockage
    """
    try:
        from pathlib import Path
        from app.core.config import settings
        
        storage_path = Path(settings.local_video_path)
        
        if not storage_path.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "storage_path": str(storage_path)
            }
        
        # Compter les fichiers et calculer la taille totale
        video_files = list(storage_path.glob("*"))
        total_files = len(video_files)
        total_size = sum(f.stat().st_size for f in video_files if f.is_file())
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(storage_path)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.get(
    "/{video_id}",
    response_model=VideoMetadata,
    summary="Récupérer les métadonnées d'une vidéo",
    description="Récupère les métadonnées d'une vidéo spécifique depuis MongoDB."
)
async def get_video_metadata(video_id: str):
    """
    Endpoint pour récupérer les métadonnées d'une vidéo.
    
    Args:
        video_id: Identifiant unique de la vidéo
        
    Returns:
        VideoMetadata: Métadonnées de la vidéo
        
    Raises:
        HTTPException: Si la vidéo n'est pas trouvée ou MongoDB non disponible
    """
    if not mongodb_connector.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB n'est pas disponible"
        )
    
    metadata = await mongodb_connector.get_video_metadata(video_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vidéo avec l'ID {video_id} non trouvée"
        )
    
    return metadata


@router.get(
    "/",
    response_model=List[VideoMetadata],
    summary="Liste toutes les vidéos",
    description="Récupère la liste de toutes les vidéos avec leurs métadonnées depuis MongoDB."
)
async def list_all_videos():
    """
    Endpoint pour lister toutes les vidéos.
    
    Returns:
        List[VideoMetadata]: Liste des métadonnées de toutes les vidéos
        
    Raises:
        HTTPException: Si MongoDB n'est pas disponible
    """
    if not mongodb_connector.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB n'est pas disponible"
        )
    
    videos = await mongodb_connector.list_all_videos()
    return videos


@router.put(
    "/{video_id}/status",
    summary="Mettre à jour le statut d'une vidéo",
    description="Met à jour le statut de traitement d'une vidéo dans MongoDB."
)
async def update_video_status(video_id: str, new_status: VideoStatus):
    """
    Endpoint pour mettre à jour le statut d'une vidéo.
    
    Args:
        video_id: Identifiant unique de la vidéo
        new_status: Nouveau statut de la vidéo
        
    Returns:
        Dict: Message de confirmation
        
    Raises:
        HTTPException: Si la vidéo n'est pas trouvée ou MongoDB non disponible
    """
    if not mongodb_connector.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB n'est pas disponible"
        )
    
    success = await mongodb_connector.update_video_status(video_id, new_status.value)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vidéo avec l'ID {video_id} non trouvée ou mise à jour échouée"
        )
    
    return {
        "message": f"Statut de la vidéo {video_id} mis à jour à {new_status.value}",
        "video_id": video_id,
        "new_status": new_status.value
    }


@router.get(
    "/stream/{video_id}",
    summary="Lire une vidéo",
    description="Permet de lire une vidéo en streaming."
)
async def stream_video(video_id: str):
    """
    Endpoint pour streamer une vidéo.
    
    Args:
        video_id: Identifiant unique de la vidéo
        
    Returns:
        FileResponse: Fichier vidéo
        
    Raises:
        HTTPException: Si la vidéo n'est pas trouvée
    """
    # Récupérer les métadonnées pour obtenir le chemin du fichier
    if mongodb_connector.client:
        metadata = await mongodb_connector.get_video_metadata(video_id)
        if metadata:
            file_path = Path(metadata.file_path)
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    media_type=metadata.content_type,
                    filename=metadata.original_filename
                )
    
    # Fallback: chercher directement dans le dossier de stockage
    video_path = Path(settings.local_video_path) / f"{video_id}.mp4"
    if not video_path.exists():
        # Essayer d'autres extensions
        for ext in ['.avi', '.mov', '.mkv']:
            alt_path = Path(settings.local_video_path) / f"{video_id}{ext}"
            if alt_path.exists():
                video_path = alt_path
                break
    
    if not video_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fichier vidéo {video_id} non trouvé"
        )
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_path.name
    )
