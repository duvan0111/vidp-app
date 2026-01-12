"""
Modèles Pydantic pour les données vidéo.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    """Statuts possibles pour une vidéo."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingType(str, Enum):
    """Types de traitement disponibles."""
    LANGUAGE_DETECTION = "language_detection"
    COMPRESSION = "compression"
    SUBTITLE_GENERATION = "subtitle_generation"
    ANIMAL_DETECTION = "animal_detection"


class ProcessingStatus(str, Enum):
    """Statuts des traitements."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Certaines étapes ont réussi, d'autres ont échoué


class ProcessingStage(str, Enum):
    """Étapes du traitement global."""
    LANGUAGE_DETECTION = "language_detection"
    COMPRESSION = "compression"
    SUBTITLE_GENERATION = "subtitle_generation"
    ANIMAL_DETECTION = "animal_detection"


class VideoUploadResponse(BaseModel):
    """Réponse après l'upload d'une vidéo."""
    video_id: str = Field(..., description="Identifiant unique de la vidéo")
    filename: str = Field(..., description="Nom original du fichier")
    file_path: str = Field(..., description="Chemin local du fichier sauvegardé")
    file_size: int = Field(..., description="Taille du fichier en octets")
    content_type: str = Field(..., description="Type MIME du fichier")
    status: VideoStatus = Field(default=VideoStatus.UPLOADED, description="Statut de la vidéo")
    upload_time: datetime = Field(default_factory=datetime.now, description="Horodatage de l'upload")
    message: str = Field(default="Vidéo uploadée avec succès", description="Message de statut")


class VideoMetadata(BaseModel):
    """Métadonnées d'une vidéo (pour usage futur avec MongoDB)."""
    video_id: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str
    status: VideoStatus
    upload_time: datetime
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    # Progression du traitement
    current_stage: Optional[str] = None  # Étape actuelle (language_detection, compression, subtitle_generation)
    stages_completed: Optional[list] = None  # Étapes terminées
    stages_failed: Optional[list] = None  # Étapes échouées
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VideoStatusResponse(BaseModel):
    """Réponse pour le statut d'une vidéo."""
    video_id: str
    status: VideoStatus
    message: str
    upload_time: Optional[datetime] = None
    processing_progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progression du traitement (0-1)")


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


class LanguageDetectionRequest(BaseModel):
    """Requête pour la détection de langue."""
    video_id: str = Field(..., description="ID de la vidéo à analyser")
    duration: int = Field(default=30, ge=5, le=60, description="Durée d'extraction audio en secondes")
    test_all_languages: bool = Field(default=True, description="Tester toutes les langues disponibles")


class LanguageDetectionResult(BaseModel):
    """Résultat de la détection de langue."""
    video_id: str
    job_id: str
    status: ProcessingStatus
    detected_language: Optional[str] = None
    language_name: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingJobResponse(BaseModel):
    """Réponse pour un job de traitement."""
    job_id: str
    video_id: str
    processing_type: ProcessingType
    status: ProcessingStatus
    message: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None


class CompressionRequest(BaseModel):
    """Requête pour la compression vidéo."""
    video_id: str = Field(..., description="ID de la vidéo à compresser")
    resolution: str = Field(default="360p", description="Résolution cible (240p, 360p, 480p, 720p, 1080p)")
    crf_value: int = Field(default=28, ge=18, le=30, description="Valeur CRF (18-30)")
    custom_filename: Optional[str] = Field(None, description="Nom de fichier personnalisé")


class CompressionResult(BaseModel):
    """Résultat de la compression vidéo."""
    video_id: str
    job_id: str
    status: ProcessingStatus
    resolution: Optional[str] = None
    original_size: Optional[str] = None
    compressed_size: Optional[str] = None
    compression_ratio: Optional[str] = None
    output_path: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SubtitleRequest(BaseModel):
    """Requête pour la génération de sous-titres."""
    video_id: str = Field(..., description="ID de la vidéo à sous-titrer")
    model_name: str = Field(default="base", description="Modèle Whisper (tiny, base, small, medium, large)")
    language: Optional[str] = Field(None, description="Code langue ISO (ex: fr, en)")


class SubtitleResult(BaseModel):
    """Résultat de la génération de sous-titres."""
    video_id: str
    job_id: str
    status: ProcessingStatus
    model_name: Optional[str] = None
    detected_language: Optional[str] = None
    subtitle_text: Optional[str] = None
    subtitle_path: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingStageResult(BaseModel):
    """Résultat d'une étape de traitement."""
    stage: ProcessingStage
    status: ProcessingStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    result: Optional[dict] = None


class GlobalProcessingRequest(BaseModel):
    """Requête pour le traitement global d'une vidéo."""
    # Paramètres de détection de langue
    enable_language_detection: bool = Field(default=True, description="Activer la détection de langue")
    language_detection_duration: int = Field(default=30, description="Durée d'extraction audio (secondes)")
    
    # Paramètres de compression
    enable_compression: bool = Field(default=True, description="Activer la compression")
    target_resolution: str = Field(default="720p", description="Résolution cible (240p, 360p, 480p, 720p, 1080p)")
    crf: int = Field(default=23, description="CRF pour la compression (18-28)")
    
    # Paramètres de sous-titres
    enable_subtitles: bool = Field(default=True, description="Activer la génération de sous-titres")
    subtitle_model: str = Field(default="tiny", description="Modèle Whisper (tiny, base, small, medium, large)")
    subtitle_language: str = Field(default="auto", description="Langue pour les sous-titres (auto détection)")
    
    # Paramètres de détection d'animaux
    enable_animal_detection: bool = Field(default=True, description="Activer la détection d'animaux")
    animal_confidence_threshold: float = Field(default=0.5, description="Seuil de confiance (0.1-1.0)")


class GlobalProcessingResult(BaseModel):
    """Résultat du traitement global."""
    video_id: str
    overall_status: ProcessingStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration: Optional[float] = None
    
    # Résultats par étape
    language_detection: Optional[ProcessingStageResult] = None
    compression: Optional[ProcessingStageResult] = None
    subtitle_generation: Optional[ProcessingStageResult] = None
    animal_detection: Optional[ProcessingStageResult] = None
    
    # Résumé
    success_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    message: str = ""


class AnimalDetectionRequest(BaseModel):
    """Requête pour la détection d'animaux."""
    video_id: str = Field(..., description="ID de la vidéo à analyser")
    confidence_threshold: float = Field(default=0.5, ge=0.1, le=1.0, description="Seuil de confiance (0.1-1.0)")
    save_video: bool = Field(default=True, description="Sauvegarder la vidéo annotée")


class AnimalDetection(BaseModel):
    """Une détection d'animal individuelle."""
    class_id: int = Field(..., description="ID de la classe YOLO")
    class_name: str = Field(..., description="Nom de la classe détectée")
    confidence: float = Field(..., description="Score de confiance")
    track_id: Optional[int] = Field(None, description="ID de tracking")


class FrameDetection(BaseModel):
    """Détections pour une frame spécifique."""
    frame: int = Field(..., description="Numéro de la frame")
    timestamp: float = Field(..., description="Timestamp en secondes")
    detections: list[AnimalDetection] = Field(default_factory=list)


class VideoAnalysisInfo(BaseModel):
    """Informations sur la vidéo analysée."""
    duration_seconds: float = Field(..., description="Durée en secondes")
    fps: int = Field(..., description="Images par seconde")
    resolution: str = Field(..., description="Résolution de la vidéo")
    total_frames: int = Field(..., description="Nombre total de frames")
    processed_frames: int = Field(..., description="Frames traitées")


class DetectionSummary(BaseModel):
    """Résumé des détections."""
    total_detections: int = Field(..., description="Nombre total de détections")
    unique_classes: int = Field(..., description="Nombre de classes uniques")
    animals_detected: dict = Field(default_factory=dict, description="Comptage par animal")
    frames_with_detections: int = Field(..., description="Frames avec des détections")


class AnimalDetectionResult(BaseModel):
    """Résultat de la détection d'animaux."""
    video_id: str
    job_id: str
    status: ProcessingStatus
    video_info: Optional[VideoAnalysisInfo] = None
    detection_summary: Optional[DetectionSummary] = None
    detailed_detections: Optional[list[FrameDetection]] = None
    output_video: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
