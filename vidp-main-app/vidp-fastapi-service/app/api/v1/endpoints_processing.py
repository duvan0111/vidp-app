"""
Endpoints pour l'orchestration des traitements vidéo (détection de langue, compression, sous-titres, détection d'animaux).
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil

from app.models.video_model import (
    LanguageDetectionRequest,
    LanguageDetectionResult,
    CompressionRequest,
    CompressionResult,
    SubtitleRequest,
    SubtitleResult,
    AnimalDetectionRequest,
    AnimalDetectionResult,
    ProcessingJobResponse,
    ProcessingType,
    ProcessingStatus,
    VideoStatus,
    ProcessingStage,
    ProcessingStageResult,
    GlobalProcessingRequest,
    GlobalProcessingResult
)
from app.services.langscale_client import language_detection_client
from app.services.downscale_client import compression_client
from app.services.subtitle_client import subtitle_client
from app.services.animal_detection_client import animal_detection_client
from app.services.aggregation_client import aggregation_client
from app.db.mongodb_connector import mongodb_connector
from app.core.config import settings
from app.utils.language_utils import normalize_language_code
from app.utils.video_utils import check_video_has_audio, create_empty_srt_content

# Création du router pour les endpoints de traitement
router = APIRouter(prefix="/processing", tags=["processing"])


@router.post(
    "/language-detection",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la détection de langue avec upload",
    description="Lance un job de détection de langue pour une vidéo uploadée directement."
)
async def start_language_detection_with_upload(
    video_file: UploadFile = File(...),
    async_processing: str = Form("false"),
    duration: int = Form(30)
):
    """
    Lance la détection de langue avec upload direct du fichier vidéo.
    
    Args:
        video_file: Fichier vidéo à analyser
        async_processing: Mode de traitement ("true" ou "false")
        duration: Durée d'extraction audio en secondes
        
    Returns:
        ProcessingJobResponse: Informations sur le job lancé
    """
    try:
        # Générer un video_id
        video_id = str(uuid.uuid4())
        
        # Créer un répertoire temporaire pour la vidéo
        temp_dir = Path("/tmp/vidp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier temporairement
        temp_file_path = temp_dir / f"{video_id}_{video_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        # Vérifier que le service est accessible
        service_healthy = await language_detection_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de détection de langue n'est pas accessible"
            )
        
        # Lancer la détection
        result = await language_detection_client.detect_language_from_local_file(
            video_path=str(temp_file_path),
            duration=duration,
            test_all_languages=True
        )
        
        # Nettoyer le fichier temporaire
        try:
            temp_file_path.unlink()
        except:
            pass
        
        # Vérifier le résultat
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=result.get("job_id", str(uuid.uuid4())),
                video_id=video_id,
                processing_type=ProcessingType.LANGUAGE_DETECTION,
                status=ProcessingStatus.FAILED,
                message="La détection de langue a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        # Extraire les informations
        job_id = result.get("job_id", str(uuid.uuid4()))
        detected_language = result.get("detected_language")
        language_name = result.get("language_name")
        confidence = result.get("confidence", 0)
        processing_time = result.get("processing_time", 0)
        
        # Préparer le résultat
        language_result = {
            "job_id": job_id,
            "detected_language": detected_language,
            "language_name": language_name,
            "confidence": confidence,
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat()
        }
        
        # Sauvegarder le résultat dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.LANGUAGE_DETECTION.value,
                result=language_result
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde dans MongoDB: {e}")
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=video_id,
            processing_type=ProcessingType.LANGUAGE_DETECTION,
            status=ProcessingStatus.COMPLETED,
            message=f"Langue détectée: {language_name} ({detected_language})" if language_name else "Détection terminée",
            completed_at=datetime.now(),
            result=language_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la détection de langue: {str(e)}"
        )


@router.post(
    "/compression",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la compression vidéo avec upload",
    description="Lance un job de compression pour une vidéo uploadée directement."
)
async def start_compression_with_upload(
    video_file: UploadFile = File(...),
    target_resolution: str = Form("720p"),
    crf: int = Form(23)
):
    """
    Lance la compression vidéo avec upload direct.
    """
    try:
        video_id = str(uuid.uuid4())
        
        # Créer un répertoire temporaire
        temp_dir = Path("/tmp/vidp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier
        temp_file_path = temp_dir / f"{video_id}_{video_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        # Vérifier le service
        service_healthy = await compression_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de compression n'est pas accessible"
            )
        
        # Lancer la compression
        result = await compression_client.compress_video(
            video_path=str(temp_file_path),
            resolution=target_resolution,
            crf_value=crf
        )
        
        # Nettoyer
        try:
            temp_file_path.unlink()
        except:
            pass
        
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=result.get("job_id", str(uuid.uuid4())),
                video_id=video_id,
                processing_type=ProcessingType.COMPRESSION,
                status=ProcessingStatus.FAILED,
                message="La compression a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        job_id = result.get("job_id", str(uuid.uuid4()))
        
        compression_result = {
            "job_id": job_id,
            "resolution": target_resolution,
            "crf_value": crf,
            "status": result.get("status"),
            "metadata": result.get("metadata", {}),
            "output_path": result.get("output_path", ""),
            "completed_at": datetime.now().isoformat()
        }
        
        # Sauvegarder le résultat dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.COMPRESSION.value,
                result=compression_result
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde dans MongoDB: {e}")
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=video_id,
            processing_type=ProcessingType.COMPRESSION,
            status=ProcessingStatus.COMPLETED if result.get("status") == "completed" else ProcessingStatus.PROCESSING,
            message=f"Compression en résolution {target_resolution}",
            completed_at=datetime.now(),
            result=compression_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la compression: {str(e)}"
        )


@router.post(
    "/subtitles",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la génération de sous-titres avec upload",
    description="Lance un job de génération de sous-titres pour une vidéo uploadée directement."
)
async def start_subtitle_generation_with_upload(
    video_file: UploadFile = File(...),
    model_size: str = Form("tiny"),
    language: str = Form("auto")
):
    """
    Lance la génération de sous-titres avec upload direct.
    """
    try:
        # Normaliser la langue avant tout traitement
        try:
            normalized_language = normalize_language_code(language)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        video_id = str(uuid.uuid4())
        
        # Créer un répertoire temporaire
        temp_dir = Path("/tmp/vidp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier
        temp_file_path = temp_dir / f"{video_id}_{video_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        # Vérifier le service
        service_healthy = await subtitle_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de sous-titres n'est pas accessible"
            )
        
        # Lancer la génération
        result = await subtitle_client.generate_subtitles(
            video_path=str(temp_file_path),
            model_name=model_size,
            language=normalized_language  # Utiliser la langue normalisée
        )
        
        # Nettoyer
        try:
            temp_file_path.unlink()
        except:
            pass
        
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=str(uuid.uuid4()),
                video_id=video_id,
                processing_type=ProcessingType.SUBTITLE_GENERATION,
                status=ProcessingStatus.FAILED,
                message="La génération de sous-titres a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        job_id = str(uuid.uuid4())
        
        # Extraire le texte complet et créer une preview
        subtitle_text_full = result.get("full_text", "")
        subtitle_text_preview = subtitle_text_full[:500] + "..." if len(subtitle_text_full) > 500 else subtitle_text_full
        
        subtitle_result = {
            "job_id": job_id,
            "model_name": model_size,
            "language": normalized_language,  # Stocker le code ISO normalisé
            "subtitle_text": subtitle_text_full,  # Texte complet
            "subtitle_text_preview": subtitle_text_preview,  # Preview pour l'API
            "text_length": len(subtitle_text_full),  # Longueur du texte
            "srt_url": result.get("srt_url"),  # URL de téléchargement du fichier SRT
            "completed_at": datetime.now().isoformat()
        }
        
        # Sauvegarder le résultat dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.SUBTITLE_GENERATION.value,
                result=subtitle_result
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde dans MongoDB: {e}")
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=video_id,
            processing_type=ProcessingType.SUBTITLE_GENERATION,
            status=ProcessingStatus.COMPLETED,
            message=f"Sous-titres générés avec le modèle {model_size}",
            completed_at=datetime.now(),
            result=subtitle_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de sous-titres: {str(e)}"
        )


@router.post(
    "/language-detection",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la détection de langue",
    description="Lance un job de détection de langue pour une vidéo uploadée."
)
async def start_language_detection(request: LanguageDetectionRequest):
    """
    Lance la détection de langue pour une vidéo.
    
    Args:
        request: Requête contenant video_id et paramètres de détection
        
    Returns:
        ProcessingJobResponse: Informations sur le job lancé
        
    Raises:
        HTTPException: Si la vidéo n'existe pas ou erreur de traitement
    """
    try:
        # Vérifier que MongoDB est disponible
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        # Récupérer les métadonnées de la vidéo
        video_metadata = await mongodb_connector.get_video_metadata(request.video_id)
        if not video_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vidéo avec l'ID {request.video_id} non trouvée"
            )
        
        # Vérifier que le service de détection est accessible
        service_healthy = await language_detection_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de détection de langue n'est pas accessible"
            )
        
        # Lancer la détection de langue (mode synchrone)
        result = await language_detection_client.detect_language_from_local_file(
            video_path=video_metadata.file_path,
            duration=request.duration,
            test_all_languages=request.test_all_languages
        )
        
        # Vérifier le résultat
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=result.get("job_id", str(uuid.uuid4())),
                video_id=request.video_id,
                processing_type=ProcessingType.LANGUAGE_DETECTION,
                status=ProcessingStatus.FAILED,
                message="La détection de langue a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        # Extraire les informations du résultat
        job_id = result.get("job_id", str(uuid.uuid4()))
        detected_language = result.get("detected_language")
        language_name = result.get("language_name")
        confidence = result.get("confidence")
        processing_time = result.get("processing_time")
        
        # Sauvegarder le résultat dans MongoDB
        language_result = {
            "job_id": job_id,
            "detected_language": detected_language,
            "language_name": language_name,
            "confidence": confidence,
            "processing_time": processing_time,
            "completed_at": datetime.now().isoformat()
        }
        
        await mongodb_connector.save_processing_result(
            video_id=request.video_id,
            processing_type="language_detection",
            result=language_result
        )
        
        # Créer la réponse
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=request.video_id,
            processing_type=ProcessingType.LANGUAGE_DETECTION,
            status=ProcessingStatus.COMPLETED,
            message=f"Langue détectée: {language_name} ({detected_language})",
            completed_at=datetime.now(),
            result=language_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement de la détection de langue: {str(e)}"
        )


@router.get(
    "/language-detection/{video_id}",
    response_model=LanguageDetectionResult,
    summary="Récupérer le résultat de détection de langue",
    description="Récupère le résultat de la détection de langue pour une vidéo."
)
async def get_language_detection_result(video_id: str):
    """
    Récupère le résultat de la détection de langue pour une vidéo.
    
    Args:
        video_id: Identifiant de la vidéo
        
    Returns:
        LanguageDetectionResult: Résultat de la détection
        
    Raises:
        HTTPException: Si le résultat n'existe pas
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        # Récupérer le résultat de la base de données
        result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="language_detection"
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résultat de détection de langue pour la vidéo {video_id}"
            )
        
        # Construire la réponse
        return LanguageDetectionResult(
            video_id=video_id,
            job_id=result.get("job_id", ""),
            status=ProcessingStatus.COMPLETED,
            detected_language=result.get("detected_language"),
            language_name=result.get("language_name"),
            confidence=result.get("confidence"),
            processing_time=result.get("processing_time"),
            completed_at=result.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résultat: {str(e)}"
        )


@router.get(
    "/supported-languages",
    summary="Langues supportées",
    description="Récupère la liste des langues supportées par le service de détection."
)
async def get_supported_languages():
    """
    Récupère la liste des langues supportées.
    
    Returns:
        Dict: Liste des langues supportées
        
    Raises:
        HTTPException: Si le service n'est pas accessible
    """
    try:
        # Vérifier que le service est accessible
        service_healthy = await language_detection_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de détection de langue n'est pas accessible"
            )
        
        # Récupérer les langues
        result = await language_detection_client.get_supported_languages()
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des langues: {str(e)}"
        )


@router.get(
    "/health",
    summary="Santé des services de traitement",
    description="Vérifie l'état de santé des microservices de traitement."
)
async def processing_services_health():
    """
    Vérifie l'état de santé des services de traitement.
    
    Returns:
        Dict: État de santé des services
    """
    langscale_healthy = await language_detection_client.check_service_health()
    compression_healthy = await compression_client.check_service_health()
    subtitle_healthy = await subtitle_client.check_service_health()
    animal_detection_healthy = await animal_detection_client.check_service_health()
    
    all_healthy = langscale_healthy and compression_healthy and subtitle_healthy and animal_detection_healthy
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "language_detection": {
                "url": settings.langscale_service_url,
                "status": "up" if langscale_healthy else "down"
            },
            "compression": {
                "url": settings.downscale_service_url,
                "status": "up" if compression_healthy else "down"
            },
            "subtitle_generation": {
                "url": settings.subtitle_service_url,
                "status": "up" if subtitle_healthy else "down"
            },
            "animal_detection": {
                "url": settings.animal_detection_service_url,
                "status": "up" if animal_detection_healthy else "down"
            }
        }
    }


@router.post(
    "/compression",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la compression vidéo",
    description="Lance un job de compression pour une vidéo uploadée."
)
async def start_compression(request: CompressionRequest):
    """
    Lance la compression vidéo.
    
    Args:
        request: Requête contenant video_id et paramètres de compression
        
    Returns:
        ProcessingJobResponse: Informations sur le job lancé
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        # Récupérer les métadonnées de la vidéo
        video_metadata = await mongodb_connector.get_video_metadata(request.video_id)
        if not video_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vidéo avec l'ID {request.video_id} non trouvée"
            )
        
        # Vérifier que le service est accessible
        service_healthy = await compression_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de compression n'est pas accessible"
            )
        
        # Lancer la compression
        result = await compression_client.compress_video(
            video_path=video_metadata.file_path,
            resolution=request.resolution,
            crf_value=request.crf_value,
            custom_filename=request.custom_filename
        )
        
        # Vérifier le résultat
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=result.get("job_id", str(uuid.uuid4())),
                video_id=request.video_id,
                processing_type=ProcessingType.COMPRESSION,
                status=ProcessingStatus.FAILED,
                message="La compression a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        job_id = result.get("job_id", str(uuid.uuid4()))
        
        # Sauvegarder le résultat dans MongoDB
        compression_result = {
            "job_id": job_id,
            "resolution": request.resolution,
            "crf_value": request.crf_value,
            "status": result.get("status"),
            "metadata": result.get("metadata", {}),
            "completed_at": datetime.now().isoformat()
        }
        
        await mongodb_connector.save_processing_result(
            video_id=request.video_id,
            processing_type="compression",
            result=compression_result
        )
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=request.video_id,
            processing_type=ProcessingType.COMPRESSION,
            status=ProcessingStatus.COMPLETED if result.get("status") == "completed" else ProcessingStatus.PROCESSING,
            message=result.get("message", f"Compression en résolution {request.resolution}"),
            completed_at=datetime.now(),
            result=compression_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement de la compression: {str(e)}"
        )


@router.get(
    "/compression/{video_id}",
    response_model=CompressionResult,
    summary="Récupérer le résultat de compression",
    description="Récupère le résultat de la compression pour une vidéo."
)
async def get_compression_result(video_id: str):
    """
    Récupère le résultat de la compression pour une vidéo.
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="compression"
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résultat de compression pour la vidéo {video_id}"
            )
        
        # result contient déjà la structure complète
        metadata = result.get("metadata", {})
        
        # Gérer les types de données
        compression_ratio = metadata.get("compression_ratio")
        if compression_ratio is not None and not isinstance(compression_ratio, str):
            compression_ratio = str(compression_ratio)
        
        return CompressionResult(
            video_id=video_id,
            job_id=result.get("job_id", ""),
            status=ProcessingStatus.COMPLETED,
            resolution=result.get("resolution"),
            original_size=metadata.get("original_size"),
            compressed_size=metadata.get("compressed_size"),
            compression_ratio=compression_ratio,
            output_path=result.get("output_path"),
            completed_at=result.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résultat: {str(e)}"
        )


@router.post(
    "/subtitles",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la génération de sous-titres",
    description="Lance un job de génération de sous-titres pour une vidéo uploadée."
)
async def start_subtitle_generation(request: SubtitleRequest):
    """
    Lance la génération de sous-titres.
    """
    try:
        # Normaliser la langue avant tout traitement
        try:
            normalized_language = normalize_language_code(request.language)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        # Récupérer les métadonnées de la vidéo
        video_metadata = await mongodb_connector.get_video_metadata(request.video_id)
        if not video_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vidéo avec l'ID {request.video_id} non trouvée"
            )
        
        # Vérifier que le service est accessible
        service_healthy = await subtitle_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de sous-titres n'est pas accessible"
            )
        
        # Lancer la génération de sous-titres
        result = await subtitle_client.generate_subtitles(
            video_path=video_metadata.file_path,
            model_name=request.model_name,
            language=normalized_language  # Utiliser la langue normalisée
        )
        
        # Vérifier le résultat
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=str(uuid.uuid4()),
                video_id=request.video_id,
                processing_type=ProcessingType.SUBTITLE_GENERATION,
                status=ProcessingStatus.FAILED,
                message="La génération de sous-titres a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        job_id = str(uuid.uuid4())
        
        # Extraire le texte complet et créer une preview
        subtitle_text_full = result.get("full_text", "")
        subtitle_text_preview = subtitle_text_full[:500] + "..." if len(subtitle_text_full) > 500 else subtitle_text_full
        
        # Sauvegarder le résultat dans MongoDB
        subtitle_result = {
            "job_id": job_id,
            "model_name": request.model_name,
            "language": normalized_language,  # Stocker le code ISO normalisé
            "subtitle_text": subtitle_text_full,  # Texte complet
            "subtitle_text_preview": subtitle_text_preview,  # Preview pour l'API
            "text_length": len(subtitle_text_full),  # Longueur du texte
            "srt_url": result.get("srt_url"),  # URL de téléchargement du fichier SRT
            "completed_at": datetime.now().isoformat()
        }
        
        await mongodb_connector.save_processing_result(
            video_id=request.video_id,
            processing_type="subtitle_generation",
            result=subtitle_result
        )
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=request.video_id,
            processing_type=ProcessingType.SUBTITLE_GENERATION,
            status=ProcessingStatus.COMPLETED,
            message=f"Sous-titres générés avec le modèle {request.model_name}",
            completed_at=datetime.now(),
            result=subtitle_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de sous-titres: {str(e)}"
        )


@router.get(
    "/subtitles/{video_id}",
    response_model=SubtitleResult,
    summary="Récupérer le résultat de génération de sous-titres",
    description="Récupère le résultat de la génération de sous-titres pour une vidéo."
)
async def get_subtitle_result(video_id: str):
    """
    Récupère le résultat de la génération de sous-titres pour une vidéo.
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="subtitle_generation"
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résultat de sous-titres pour la vidéo {video_id}"
            )
        
        return SubtitleResult(
            video_id=video_id,
            job_id=result.get("job_id", ""),
            status=ProcessingStatus.COMPLETED,
            model_name=result.get("model_name"),
            detected_language=result.get("language"),
            subtitle_text=result.get("subtitle_text"),
            subtitle_text_preview=result.get("subtitle_text_preview"),
            completed_at=result.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résultat: {str(e)}"
        )


# ============================================================
# ENDPOINT DE TRAITEMENT GLOBAL
# ============================================================

@router.post(
    "/process-video",
    response_model=GlobalProcessingResult,
    status_code=status.HTTP_201_CREATED,
    summary="Traitement global d'une vidéo",
    description="Lance le traitement complet OBLIGATOIRE d'une vidéo : détection de langue, compression, génération de sous-titres et détection d'animaux. Si une étape échoue, le pipeline s'arrête."
)
async def process_video_global(
    video_file: UploadFile = File(...),
    language_detection_duration: int = Form(30),
    target_resolution: str = Form("720p"),
    crf: int = Form(23),
    subtitle_model: str = Form("tiny"),
    subtitle_language: str = Form("auto"),
    animal_confidence_threshold: float = Form(0.5)
):
    """
    Traitement global OBLIGATOIRE d'une vidéo uploadée.
    
    Ce endpoint orchestre les 4 étapes de traitement (TOUTES OBLIGATOIRES) :
    1. Détection de langue
    2. Compression vidéo
    3. Génération de sous-titres
    4. Détection d'animaux (YOLO)
    
    IMPORTANT: Si une étape échoue, le pipeline s'arrête immédiatement (échec global).
    
    Args:
        video_file: Fichier vidéo à traiter
        language_detection_duration: Durée d'extraction audio en secondes
        target_resolution: Résolution cible (240p, 360p, 480p, 720p, 1080p)
        crf: CRF pour la compression (18-28)
        subtitle_model: Modèle Whisper (tiny, base, small, medium, large)
        subtitle_language: Langue pour les sous-titres (auto = détection automatique)
        animal_confidence_threshold: Seuil de confiance pour la détection d'animaux (0.1-1.0)
        
    Returns:
        GlobalProcessingResult: Résultat complet du traitement
    """
    video_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Préparer la réponse
    result = GlobalProcessingResult(
        video_id=video_id,
        overall_status=ProcessingStatus.PROCESSING,
        started_at=start_time,
        message="Traitement en cours..."
    )
    
    # ============================================================
    # SAUVEGARDER LA VIDÉO DE MANIÈRE PERMANENTE (comme upload normal)
    # ============================================================
    from app.services.file_storage import FileStorageService
    
    try:
        # Utiliser le service de stockage pour sauvegarder de manière permanente
        unique_filename, permanent_file_path, file_size = await FileStorageService.save_video_file(video_file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la sauvegarde du fichier: {str(e)}"
        )
    
    # ============================================================
    # SAUVEGARDER LA VIDÉO EN MONGODB AVEC STATUT "PROCESSING"
    # ============================================================
    stages_completed = []
    stages_failed = []
    
    try:
        from app.models.video_model import VideoMetadata
        video_metadata = VideoMetadata(
            video_id=video_id,
            original_filename=video_file.filename,
            file_path=permanent_file_path,  # Chemin permanent
            file_size=file_size,
            content_type=video_file.content_type or "video/mp4",
            status=VideoStatus.PROCESSING,
            upload_time=start_time,
            processing_start_time=start_time,
            current_stage="initializing",
            stages_completed=[],
            stages_failed=[]
        )
        await mongodb_connector.save_video_metadata(video_metadata)
    except Exception as e:
        print(f"Erreur sauvegarde MongoDB (video metadata): {e}")
    
    # Utiliser le chemin permanent pour le traitement
    video_path_for_processing = permanent_file_path
    
    # ============================================================
    # DÉTECTION DE LA PISTE AUDIO
    # ============================================================
    # Vérifie si la vidéo a une piste audio pour adapter le pipeline
    has_audio = check_video_has_audio(video_path_for_processing)
    print(f"🔊 Piste audio détectée: {has_audio}")
    
    # Helper function pour échec global
    async def handle_pipeline_failure(stage_name: str, error_msg: str, stage_result: ProcessingStageResult):
        """Gère l'échec d'une étape et arrête le pipeline"""
        stages_failed.append(stage_name)
        stage_result.status = ProcessingStatus.FAILED
        stage_result.error_message = error_msg
        stage_result.completed_at = datetime.now()
        if stage_result.started_at:
            stage_result.duration = (datetime.now() - stage_result.started_at).total_seconds()
        result.failure_count += 1
        
        # Mettre à jour MongoDB avec l'échec
        try:
            await mongodb_connector.update_processing_stage(
                video_id, "failed", stages_completed, stages_failed
            )
            await mongodb_connector.update_video_status(video_id, "failed")
        except Exception as e:
            print(f"Erreur update MongoDB (failure): {e}")
        
        # Définir le statut global
        result.overall_status = ProcessingStatus.FAILED
        result.completed_at=datetime.now()
        result.total_duration = (datetime.now() - start_time).total_seconds()
        result.message = f"❌ Pipeline arrêté : échec de l'étape '{stage_name}' - {error_msg}"
        
        return result
    
    # ============================================================
    # ÉTAPE 1: DÉTECTION DE LANGUE (SAUTÉE SI PAS D'AUDIO)
    # ============================================================
    if has_audio:
        # Mettre à jour l'étape actuelle
        try:
            await mongodb_connector.update_processing_stage(
                video_id, "language_detection", stages_completed, stages_failed
            )
        except Exception as e:
            print(f"Erreur update stage: {e}")
        
        stage_start = datetime.now()
        stage_result = ProcessingStageResult(
            stage=ProcessingStage.LANGUAGE_DETECTION,
            status=ProcessingStatus.PROCESSING,
            started_at=stage_start
        )
        
        try:
            # Vérifier le service
            service_healthy = await language_detection_client.check_service_health()
            if not service_healthy:
                result.language_detection = stage_result
                return await handle_pipeline_failure(
                    "language_detection", 
                    "Service de détection de langue indisponible",
                    stage_result
                )
            
            # Lancer la détection
            lang_result = await language_detection_client.detect_language_from_local_file(
                video_path=video_path_for_processing,
                duration=language_detection_duration,
                test_all_languages=True
            )
            
            stage_end = datetime.now()
            stage_result.completed_at = stage_end
            stage_result.duration = (stage_end - stage_start).total_seconds()
            
            if lang_result.get("status") == "failed":
                result.language_detection = stage_result
                return await handle_pipeline_failure(
                    "language_detection",
                    lang_result.get("error", "Erreur inconnue lors de la détection de langue"),
                    stage_result
                )
            
            # Succès
            stage_result.status = ProcessingStatus.COMPLETED
            stage_result.result = {
                "detected_language": lang_result.get("detected_language"),
                "language_name": lang_result.get("language_name"),
                "confidence": lang_result.get("confidence")
            }
            result.success_count += 1
            stages_completed.append("language_detection")
            
            # Sauvegarder dans MongoDB
            try:
                await mongodb_connector.save_processing_result(
                    video_id=video_id,
                    processing_type=ProcessingType.LANGUAGE_DETECTION.value,
                    result=stage_result.result
                )
            except Exception as e:
                print(f"Erreur sauvegarde MongoDB (language): {e}")
        
        except Exception as e:
            result.language_detection = stage_result
            return await handle_pipeline_failure(
                "language_detection",
                str(e),
                stage_result
            )
        
        result.language_detection = stage_result
    else:
        # Pas d'audio : marquer l'étape comme sautée
        print("⏭️ Étape 1 (détection de langue) sautée : vidéo sans piste audio")
        stage_result = ProcessingStageResult(
            stage=ProcessingStage.LANGUAGE_DETECTION,
            status=ProcessingStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=0.0,
            result={
                "skipped": True,
                "reason": "no_audio_track",
                "detected_language": None,
                "language_name": "Non applicable (pas d'audio)",
                "confidence": 0.0
            }
        )
        result.language_detection = stage_result
        result.success_count += 1
        stages_completed.append("language_detection")
    
    # ============================================================
    # ÉTAPE 2: COMPRESSION VIDÉO (OBLIGATOIRE)
    # ============================================================
    # Mettre à jour l'étape actuelle
    try:
        await mongodb_connector.update_processing_stage(
            video_id, "compression", stages_completed, stages_failed
        )
    except Exception as e:
        print(f"Erreur update stage: {e}")
    
    stage_start = datetime.now()
    stage_result = ProcessingStageResult(
        stage=ProcessingStage.COMPRESSION,
        status=ProcessingStatus.PROCESSING,
        started_at=stage_start
    )
    
    try:
        # Vérifier le service
        service_healthy = await compression_client.check_service_health()
        if not service_healthy:
            result.compression = stage_result
            return await handle_pipeline_failure(
                "compression",
                "Service de compression indisponible",
                stage_result
            )
        
        # Lancer la compression
        comp_result = await compression_client.compress_video(
            video_path=video_path_for_processing,
            resolution=target_resolution,
            crf_value=crf
        )
        
        stage_end = datetime.now()
        stage_result.completed_at = stage_end
        stage_result.duration = (stage_end - stage_start).total_seconds()
        
        if comp_result.get("status") == "failed":
            result.compression = stage_result
            return await handle_pipeline_failure(
                "compression",
                comp_result.get("error", "Erreur inconnue lors de la compression"),
                stage_result
            )
        
        # Succès
        stage_result.status = ProcessingStatus.COMPLETED
        stage_result.result = {
            "job_id": comp_result.get("job_id"),
            "resolution": target_resolution,
            "output_path": comp_result.get("output_path"),
            "metadata": comp_result.get("metadata", {})
        }
        result.success_count += 1
        stages_completed.append("compression")
        
        # Sauvegarder dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.COMPRESSION.value,
                result=stage_result.result
            )
        except Exception as e:
            print(f"Erreur sauvegarde MongoDB (compression): {e}")
    
    except Exception as e:
        result.compression = stage_result
        return await handle_pipeline_failure(
            "compression",
            str(e),
            stage_result
        )
    
    result.compression = stage_result
    
    # ============================================================
    # ÉTAPE 3: GÉNÉRATION DE SOUS-TITRES (SAUTÉE SI PAS D'AUDIO)
    # ============================================================
    if has_audio:
        # Mettre à jour l'étape actuelle
        try:
            await mongodb_connector.update_processing_stage(
                video_id, "subtitle_generation", stages_completed, stages_failed
            )
        except Exception as e:
            print(f"Erreur update stage: {e}")
        
        stage_start = datetime.now()
        stage_result = ProcessingStageResult(
            stage=ProcessingStage.SUBTITLE_GENERATION,
            status=ProcessingStatus.PROCESSING,
            started_at=stage_start
        )
        
        try:
            # Vérifier le service
            service_healthy = await subtitle_client.check_service_health()
            if not service_healthy:
                result.subtitle_generation = stage_result
                return await handle_pipeline_failure(
                    "subtitle_generation",
                    "Service de sous-titres indisponible",
                    stage_result
                )
            
            # Utiliser la langue détectée si disponible
            lang_to_use = subtitle_language
            if subtitle_language == "auto" and result.language_detection and result.language_detection.result:
                detected = result.language_detection.result.get("detected_language")
                if detected:
                    lang_to_use = detected
            
            # Normaliser la langue avant de l'envoyer au microservice
            # Convertit "Espagnol" -> "es", "auto" -> None, etc.
            try:
                lang_to_use = normalize_language_code(lang_to_use)
            except ValueError as e:
                result.subtitle_generation = stage_result
                return await handle_pipeline_failure(
                    "subtitle_generation",
                    f"Langue invalide : {str(e)}",
                    stage_result
                )
            
            # Lancer la génération
            sub_result = await subtitle_client.generate_subtitles(
                video_path=video_path_for_processing,
                model_name=subtitle_model,
                language=lang_to_use
            )
            
            stage_end = datetime.now()
            stage_result.completed_at = stage_end
            stage_result.duration = (stage_end - stage_start).total_seconds()
            
            if sub_result.get("status") == "failed":
                result.subtitle_generation = stage_result
                return await handle_pipeline_failure(
                    "subtitle_generation",
                    sub_result.get("error", "Erreur inconnue lors de la génération des sous-titres"),
                    stage_result
                )
            
            # Succès
            stage_result.status = ProcessingStatus.COMPLETED
            
            # Extraire le texte complet depuis la clé "full_text"
            subtitle_text_full = sub_result.get("full_text", "")
            subtitle_text_preview = subtitle_text_full[:500] + "..." if len(subtitle_text_full) > 500 else subtitle_text_full
            
            stage_result.result = {
                "model_name": subtitle_model,
                "language": lang_to_use,
                "subtitle_text": subtitle_text_full,  # Texte complet
                "subtitle_text_preview": subtitle_text_preview,  # Preview pour l'API
                "text_length": len(subtitle_text_full),  # Longueur du texte
                "srt_url": sub_result.get("srt_url"),  # URL de téléchargement du fichier SRT
            }
            result.success_count += 1
            stages_completed.append("subtitle_generation")
            
            # Sauvegarder dans MongoDB (avec texte complet)
            try:
                await mongodb_connector.save_processing_result(
                    video_id=video_id,
                    processing_type=ProcessingType.SUBTITLE_GENERATION.value,
                    result=stage_result.result
                )
            except Exception as e:
                print(f"Erreur sauvegarde MongoDB (subtitle): {e}")
        
        except Exception as e:
            result.subtitle_generation = stage_result
            return await handle_pipeline_failure(
                "subtitle_generation",
                str(e),
                stage_result
            )
        
        result.subtitle_generation = stage_result
    else:
        # Pas d'audio : marquer l'étape comme sautée avec un SRT vide
        print("⏭️ Étape 3 (génération de sous-titres) sautée : vidéo sans piste audio")
        stage_result = ProcessingStageResult(
            stage=ProcessingStage.SUBTITLE_GENERATION,
            status=ProcessingStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=0.0,
            result={
                "skipped": True,
                "reason": "no_audio_track",
                "model_name": None,
                "language": None,
                "subtitle_text": "",
                "subtitle_text_preview": "(Pas de sous-titres - vidéo sans audio)",
                "text_length": 0,
                "srt_url": None,  # Pas de SRT disponible
                "srt_content": create_empty_srt_content()  # Contenu SRT vide pour l'agrégation
            }
        )
        result.subtitle_generation = stage_result
        result.success_count += 1
        stages_completed.append("subtitle_generation")
    
    # ============================================================
    # ÉTAPE 4: DÉTECTION D'ANIMAUX (OBLIGATOIRE)
    # ============================================================
    # Mettre à jour l'étape actuelle
    try:
        await mongodb_connector.update_processing_stage(
            video_id, "animal_detection", stages_completed, stages_failed
        )
    except Exception as e:
        print(f"Erreur update stage: {e}")
    
    stage_start = datetime.now()
    stage_result = ProcessingStageResult(
        stage=ProcessingStage.ANIMAL_DETECTION,
        status=ProcessingStatus.PROCESSING,
        started_at=stage_start
    )
    
    try:
        # Vérifier le service
        service_healthy = await animal_detection_client.check_service_health()
        if not service_healthy:
            result.animal_detection = stage_result
            return await handle_pipeline_failure(
                "animal_detection",
                "Service de détection d'animaux indisponible",
                stage_result
            )
        
        # Lancer la détection d'animaux
        animal_result = await animal_detection_client.detect_animals_in_video(
            video_path=video_path_for_processing,
            confidence_threshold=animal_confidence_threshold,
            save_video=True
        )
        
        stage_end = datetime.now()
        stage_result.completed_at = stage_end
        stage_result.duration = (stage_end - stage_start).total_seconds()
        
        if animal_result.get("status") == "failed":
            result.animal_detection = stage_result
            return await handle_pipeline_failure(
                "animal_detection",
                animal_result.get("error", "Erreur inconnue lors de la détection d'animaux"),
                stage_result
            )
        
        # Succès
        stage_result.status = ProcessingStatus.COMPLETED
        detection_summary = animal_result.get("detection_summary", {})
        stage_result.result = {
            "video_info": animal_result.get("video_info", {}),
            "detection_summary": detection_summary,
            "total_detections": detection_summary.get("total_detections", 0),
            "animals_detected": detection_summary.get("animals_detected", {}),
            "output_video": animal_result.get("output_video")
        }
        result.success_count += 1
        stages_completed.append("animal_detection")
        
        # Sauvegarder dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.ANIMAL_DETECTION.value,
                result=stage_result.result
            )
        except Exception as e:
            print(f"Erreur sauvegarde MongoDB (animal_detection): {e}")
    
    except Exception as e:
        result.animal_detection = stage_result
        return await handle_pipeline_failure(
            "animal_detection",
            str(e),
            stage_result
        )
    
    result.animal_detection = stage_result
    
    # ============================================================
    # ÉTAPE 5: AGRÉGATION VIDÉO (AVEC OU SANS SOUS-TITRES)
    # ============================================================
    # Envoie la vidéo compressée et les sous-titres au service d'agrégation
    # pour produire une vidéo finale avec sous-titres incrustés (si audio disponible)
    # ou sans sous-titres (si pas d'audio)
    
    # Mettre à jour l'étape actuelle
    try:
        await mongodb_connector.update_processing_stage(
            video_id, "aggregation", stages_completed, stages_failed
        )
    except Exception as e:
        print(f"Erreur update stage: {e}")
    
    stage_start = datetime.now()
    stage_result = ProcessingStageResult(
        stage=ProcessingStage.AGGREGATION,
        status=ProcessingStatus.PROCESSING,
        started_at=stage_start
    )
    
    try:
        # Vérifier le service
        service_healthy = await aggregation_client.check_service_health()
        if not service_healthy:
            result.aggregation = stage_result
            return await handle_pipeline_failure(
                "aggregation",
                "Service d'agrégation indisponible",
                stage_result
            )
        
        # Récupérer l'URL SRT ou le contenu SRT depuis l'étape de génération de sous-titres
        srt_url = None
        srt_content = None
        video_has_subtitles = has_audio  # Si pas d'audio, pas de vrais sous-titres
        
        if result.subtitle_generation and result.subtitle_generation.result:
            srt_url = result.subtitle_generation.result.get("srt_url")
            srt_content = result.subtitle_generation.result.get("srt_content")
        
        # Récupérer le chemin de la vidéo compressée depuis l'étape de compression
        compressed_video_path = video_path_for_processing  # Par défaut, utiliser la vidéo originale
        if result.compression and result.compression.result:
            output_path = result.compression.result.get("output_path")
            if output_path and Path(output_path).exists():
                compressed_video_path = output_path
        
        # Lancer l'agrégation selon le mode (avec URL SRT ou contenu SRT direct)
        if srt_url:
            # Mode normal : télécharger le SRT depuis l'URL
            print(f"🎬 Agrégation avec sous-titres depuis URL: {srt_url}")
            agg_result = await aggregation_client.process_video_with_subtitles(
                video_path=compressed_video_path,
                srt_url=srt_url,
                resolution=target_resolution,
                crf_value=crf,
                source_video_id=video_id  # Pass the source video ID for cross-database reference
            )
        else:
            # Mode sans audio : utiliser un SRT vide
            print("🎬 Agrégation sans sous-titres (vidéo sans piste audio)")
            # Utiliser le contenu SRT vide ou en créer un
            empty_srt = srt_content if srt_content else create_empty_srt_content()
            agg_result = await aggregation_client.process_video_with_srt_content(
                video_path=compressed_video_path,
                srt_content=empty_srt,
                resolution=target_resolution,
                crf_value=crf,
                source_video_id=video_id  # Pass the source video ID for cross-database reference
            )
        
        stage_end = datetime.now()
        stage_result.completed_at = stage_end
        stage_result.duration = (stage_end - stage_start).total_seconds()
        
        if agg_result.get("status") == "failed":
            result.aggregation = stage_result
            return await handle_pipeline_failure(
                "aggregation",
                agg_result.get("error", "Erreur inconnue lors de l'agrégation"),
                stage_result
            )
        
        # Succès
        stage_result.status = ProcessingStatus.COMPLETED
        stage_result.result = {
            "job_id": agg_result.get("job_id"),
            "aggregated_video_id": agg_result.get("video_id"),
            "streaming_url": agg_result.get("streaming_url"),
            "metadata": agg_result.get("metadata", {}),
            "message": agg_result.get("message"),
            "has_subtitles": video_has_subtitles,  # Indique si la vidéo a des sous-titres incrustés
            "no_audio": not has_audio  # Indique si la vidéo n'avait pas de piste audio
        }
        result.success_count += 1
        stages_completed.append("aggregation")
        
        # Stocker l'URL de streaming finale
        result.final_streaming_url = agg_result.get("streaming_url")
        
        # Sauvegarder dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.AGGREGATION.value,
                result=stage_result.result
            )
        except Exception as e:
            print(f"Erreur sauvegarde MongoDB (aggregation): {e}")
    
    except Exception as e:
        result.aggregation = stage_result
        return await handle_pipeline_failure(
            "aggregation",
            str(e),
            stage_result
        )
    
    result.aggregation = stage_result
    
    # ============================================================
    # FINALISATION - SUCCÈS COMPLET
    # ============================================================
    
    # Marquer comme terminé avec succès
    try:
        await mongodb_connector.update_processing_stage(
            video_id, "completed", stages_completed, stages_failed
        )
    except Exception as e:
        print(f"Erreur update stage final: {e}")
    
    # Note: On ne supprime PAS le fichier vidéo car il est stocké de manière permanente
    # pour permettre le streaming ultérieur
    
    # Calculer la durée totale
    end_time = datetime.now()
    result.completed_at = end_time
    result.total_duration = (end_time - start_time).total_seconds()
    
    # Toutes les 5 étapes ont réussi (sinon on aurait déjà retourné avec un échec)
    result.overall_status = ProcessingStatus.COMPLETED
    result.message = f"✅ Pipeline complet réussi ! (5/5 étapes en {result.total_duration:.1f}s)"
    
    # ============================================================
    # METTRE À JOUR LE STATUT FINAL DANS MONGODB
    # ============================================================
    try:
        await mongodb_connector.update_video_status(video_id, "completed")
    except Exception as e:
        print(f"Erreur mise à jour statut MongoDB: {e}")
    
    return result


@router.get(
    "/process-video/{video_id}",
    response_model=GlobalProcessingResult,
    summary="Récupérer le résultat du traitement global",
    description="Récupère tous les résultats de traitement pour une vidéo."
)
async def get_global_processing_result(video_id: str):
    """
    Récupère le résultat complet du traitement global pour une vidéo.
    
    Args:
        video_id: Identifiant de la vidéo
        
    Returns:
        GlobalProcessingResult: Résultat complet avec toutes les étapes
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        # Récupérer tous les résultats
        lang_result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="language_detection"
        )
        
        comp_result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="compression"
        )
        
        sub_result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="subtitle_generation"
        )
        
        animal_result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="animal_detection"
        )
        
        agg_result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type="aggregation"
        )
        
        # Vérifier qu'au moins un résultat existe
        if not any([lang_result, comp_result, sub_result, animal_result, agg_result]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résultat de traitement pour la vidéo {video_id}"
            )
        
        # Construire la réponse
        result = GlobalProcessingResult(
            video_id=video_id,
            overall_status=ProcessingStatus.COMPLETED,
            started_at=datetime.now(),  # Placeholder
            message="Résultats récupérés depuis la base de données"
        )
        
        # Ajouter les résultats disponibles
        if lang_result:
            result.language_detection = ProcessingStageResult(
                stage=ProcessingStage.LANGUAGE_DETECTION,
                status=ProcessingStatus.COMPLETED,
                result=lang_result
            )
            result.success_count += 1
        
        if comp_result:
            result.compression = ProcessingStageResult(
                stage=ProcessingStage.COMPRESSION,
                status=ProcessingStatus.COMPLETED,
                result=comp_result
            )
            result.success_count += 1
        
        if sub_result:
            result.subtitle_generation = ProcessingStageResult(
                stage=ProcessingStage.SUBTITLE_GENERATION,
                status=ProcessingStatus.COMPLETED,
                result=sub_result
            )
            result.success_count += 1
        
        if animal_result:
            result.animal_detection = ProcessingStageResult(
                stage=ProcessingStage.ANIMAL_DETECTION,
                status=ProcessingStatus.COMPLETED,
                result=animal_result
            )
            result.success_count += 1
        
        if agg_result:
            result.aggregation = ProcessingStageResult(
                stage=ProcessingStage.AGGREGATION,
                status=ProcessingStatus.COMPLETED,
                result=agg_result
            )
            result.success_count += 1
            # Extraire l'URL de streaming finale
            result.final_streaming_url = agg_result.get("streaming_url")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE DÉTECTION D'ANIMAUX
# ============================================================================

@router.post(
    "/animal-detection",
    response_model=ProcessingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lancer la détection d'animaux avec upload",
    description="Lance un job de détection d'animaux YOLO pour une vidéo uploadée directement."
)
async def start_animal_detection_with_upload(
    video_file: UploadFile = File(...),
    confidence_threshold: float = Form(0.5),
    save_video: bool = Form(True)
):
    """
    Lance la détection d'animaux avec upload direct du fichier vidéo.
    
    Args:
        video_file: Fichier vidéo à analyser
        confidence_threshold: Seuil de confiance minimum (0.1-1.0)
        save_video: Sauvegarder la vidéo avec annotations
        
    Returns:
        ProcessingJobResponse: Informations sur le job lancé
    """
    try:
        # Générer un video_id
        video_id = str(uuid.uuid4())
        
        # Créer un répertoire temporaire pour la vidéo
        temp_dir = Path("/tmp/vidp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier temporairement
        temp_file_path = temp_dir / f"{video_id}_{video_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        # Vérifier que le service est accessible
        service_healthy = await animal_detection_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de détection d'animaux n'est pas accessible"
            )
        
        # Lancer la détection
        result = await animal_detection_client.detect_animals_in_video(
            video_path=str(temp_file_path),
            confidence_threshold=confidence_threshold,
            save_video=save_video
        )
        
        # Nettoyer le fichier temporaire
        try:
            temp_file_path.unlink()
        except:
            pass
        
        # Vérifier le résultat
        if result.get("status") == "failed":
            return ProcessingJobResponse(
                job_id=str(uuid.uuid4()),
                video_id=video_id,
                processing_type=ProcessingType.ANIMAL_DETECTION,
                status=ProcessingStatus.FAILED,
                message="La détection d'animaux a échoué",
                error_message=result.get("error", "Erreur inconnue")
            )
        
        # Extraire les informations
        job_id = str(uuid.uuid4())
        
        # Préparer le résultat
        detection_result = {
            "job_id": job_id,
            "video_info": result.get("video_info", {}),
            "detection_summary": result.get("detection_summary", {}),
            "detailed_detections": result.get("detailed_detections", [])[:50],  # Limiter
            "output_video": result.get("output_video"),
            "completed_at": datetime.now().isoformat()
        }
        
        # Sauvegarder le résultat dans MongoDB
        try:
            await mongodb_connector.save_processing_result(
                video_id=video_id,
                processing_type=ProcessingType.ANIMAL_DETECTION.value,
                result=detection_result
            )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde dans MongoDB: {e}")
        
        # Construire le message de résumé
        summary = result.get("detection_summary", {})
        animals_detected = summary.get("animals_detected", {})
        total_detections = summary.get("total_detections", 0)
        
        if animals_detected:
            animals_list = ", ".join([f"{count}x {animal}" for animal, count in animals_detected.items()])
            message = f"Détections: {animals_list} ({total_detections} total)"
        else:
            message = "Aucun animal détecté dans la vidéo"
        
        return ProcessingJobResponse(
            job_id=job_id,
            video_id=video_id,
            processing_type=ProcessingType.ANIMAL_DETECTION,
            status=ProcessingStatus.COMPLETED,
            message=message,
            completed_at=datetime.now(),
            result=detection_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la détection d'animaux: {str(e)}"
        )


@router.get(
    "/animal-detection/classes",
    summary="Liste des classes détectables",
    description="Retourne la liste des animaux et objets détectables par le modèle YOLO."
)
async def get_detectable_classes():
    """
    Récupère la liste des classes détectables par le modèle.
    
    Returns:
        Dict: Classes détectables avec leurs IDs
    """
    try:
        # Vérifier que le service est accessible
        service_healthy = await animal_detection_client.check_service_health()
        if not service_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Le service de détection d'animaux n'est pas accessible"
            )
        
        result = await animal_detection_client.get_detectable_animals()
        
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Erreur inconnue")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des classes: {str(e)}"
        )


@router.get(
    "/animal-detection/health",
    summary="Vérifier le service de détection d'animaux",
    description="Vérifie si le service de détection d'animaux est accessible et fonctionnel."
)
async def check_animal_detection_health():
    """
    Vérifie l'état du service de détection d'animaux.
    
    Returns:
        Dict: État du service
    """
    try:
        is_healthy = await animal_detection_client.check_service_health()
        
        return {
            "service": "animal_detection",
            "status": "healthy" if is_healthy else "unhealthy",
            "url": settings.animal_detection_service_url,
            "message": "Service opérationnel" if is_healthy else "Service indisponible"
        }
    except Exception as e:
        return {
            "service": "animal_detection",
            "status": "error",
            "url": settings.animal_detection_service_url,
            "message": str(e)
        }


@router.get(
    "/animal-detection/{video_id}",
    summary="Récupérer les résultats de détection d'animaux",
    description="Récupère les résultats de détection d'animaux pour une vidéo spécifique."
)
async def get_animal_detection_results(video_id: str):
    """
    Récupère les résultats de détection d'animaux sauvegardés.
    
    Args:
        video_id: ID de la vidéo
        
    Returns:
        Dict: Résultats de la détection
    """
    try:
        if not mongodb_connector.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB n'est pas disponible"
            )
        
        result = await mongodb_connector.get_processing_result(
            video_id=video_id,
            processing_type=ProcessingType.ANIMAL_DETECTION.value
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résultat de détection d'animaux pour la vidéo {video_id}"
            )
        
        return {
            "video_id": video_id,
            "processing_type": "animal_detection",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )
