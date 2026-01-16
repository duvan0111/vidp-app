"""
Configuration module pour l'application FastAPI VidP.
Charge les variables d'environnement depuis le fichier .env.
"""
import os
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration de l'application VidP."""
    
    # Configuration de l'application
    app_name: str = Field(default="VidP Local API", env="APP_NAME")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    
    # Configuration du stockage local
    local_storage_root: str = Field(default="./local_storage", env="LOCAL_STORAGE_ROOT")
    local_video_path: str = Field(default="./local_storage/videos", env="LOCAL_VIDEO_PATH")
    
    # Configuration MongoDB (pour usage futur)
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="vidp_db", env="MONGODB_DATABASE")
    
    # Configuration CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Configuration des microservices
    langscale_service_url: str = Field(default="http://localhost:8002", env="LANGSCALE_SERVICE_URL")
    downscale_service_url: str = Field(default="http://localhost:8001", env="DOWNSCALE_SERVICE_URL")
    subtitle_service_url: str = Field(default="http://localhost:8003", env="SUBTITLE_SERVICE_URL")
    animal_detection_service_url: str = Field(default="http://localhost:8004", env="ANIMAL_DETECTION_SERVICE_URL")
    aggregation_service_url: str = Field(default="http://100.48.20.184:8006", env="AGGREGATION_SERVICE_URL")
    # Timeout augmenté à 1 heure 30 minutes pour les traitements longs (vidéos volumineuses)
    microservices_timeout: int = Field(default=9000, env="MICROSERVICES_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Créer les dossiers de stockage s'ils n'existent pas
        self._ensure_storage_directories()
    
    def _ensure_storage_directories(self):
        """Créer les dossiers de stockage s'ils n'existent pas."""
        video_path = Path(self.local_video_path)
        video_path.mkdir(parents=True, exist_ok=True)
        
        metadata_path = Path(self.local_storage_root) / "metadata"
        metadata_path.mkdir(parents=True, exist_ok=True)


# Instance globale des paramètres
settings = Settings()
