"""
Client HTTP pour communiquer avec le service de détection d'animaux (app_animal_detect).
"""
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class AnimalDetectionClient:
    """
    Client pour interagir avec le microservice de détection d'animaux YOLO.
    """
    
    def __init__(self):
        self.base_url = settings.animal_detection_service_url
        self.timeout = settings.microservices_timeout
        # Timeout spécifique pour la détection d'animaux (peut être très long)
        # connect: 30s pour établir la connexion
        # read: timeout principal pour attendre la réponse
        # write: 300s pour l'upload de gros fichiers
        # pool: 30s pour obtenir une connexion du pool
        self.video_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),  # Utilise le timeout configuré (1800s par défaut)
            write=300.0,
            pool=30.0
        )
    
    async def detect_animals_in_video(
        self,
        video_path: str,
        confidence_threshold: float = 0.5,
        save_video: bool = True
    ) -> Dict[str, Any]:
        """
        Détecte les animaux dans une vidéo en uploadant le fichier.
        
        IMPORTANT: Upload du fichier via HTTP pour compatibilité Kubernetes.
        
        Args:
            video_path: Chemin du fichier vidéo local
            confidence_threshold: Seuil de confiance minimum (0-1)
            save_video: Sauvegarder la vidéo annotée
            
        Returns:
            Dict contenant les détections et métadonnées
        """
        endpoint = f"{self.base_url}/detect"
        
        # Vérifier que le fichier existe
        video_file_path = Path(video_path)
        if not video_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier vidéo introuvable",
                "detail": f"Le fichier {video_path} n'existe pas"
            }
        
        # Utiliser le timeout spécifique pour les traitements vidéo longs
        async with httpx.AsyncClient(timeout=self.video_timeout) as client:
            try:
                # Préparer le fichier pour l'upload
                with open(video_file_path, 'rb') as video_file:
                    files = {
                        'file': (video_file_path.name, video_file, 'video/mp4')
                    }
                    params = {
                        'confidence_threshold': confidence_threshold,
                        'save_video': str(save_video).lower()
                    }
                    
                    # Upload et détection
                    response = await client.post(
                        endpoint,
                        files=files,
                        params=params
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    result["status"] = "completed"
                    return result
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de la détection d'animaux",
                    "detail": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de détection d'animaux",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de l'upload du fichier",
                    "detail": str(e)
                }
    
    async def detect_animals_in_frame(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Détecte les animaux sur une seule image.
        
        Args:
            image_path: Chemin du fichier image local
            confidence_threshold: Seuil de confiance minimum (0-1)
            
        Returns:
            Dict contenant les détections et l'image annotée en base64
        """
        endpoint = f"{self.base_url}/detect/frame"
        
        # Vérifier que le fichier existe
        image_file_path = Path(image_path)
        if not image_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier image introuvable",
                "detail": f"Le fichier {image_path} n'existe pas"
            }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Préparer le fichier pour l'upload
                with open(image_file_path, 'rb') as image_file:
                    files = {
                        'file': (image_file_path.name, image_file, 'image/jpeg')
                    }
                    params = {
                        'confidence_threshold': confidence_threshold
                    }
                    
                    response = await client.post(
                        endpoint,
                        files=files,
                        params=params
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    result["status"] = "completed"
                    return result
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de la détection d'animaux",
                    "detail": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de détection d'animaux",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de la détection",
                    "detail": str(e)
                }
    
    async def get_detectable_animals(self) -> Dict[str, Any]:
        """
        Récupère la liste des animaux détectables par le modèle.
        
        Returns:
            Dict contenant les classes détectables
        """
        endpoint = f"{self.base_url}/animals"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de la récupération des classes",
                    "detail": str(e)
                }
    
    async def download_annotated_video(
        self,
        filename: str,
        output_path: str
    ) -> bool:
        """
        Télécharge une vidéo annotée depuis le service.
        
        Args:
            filename: Nom du fichier de sortie sur le service
            output_path: Chemin local de destination
            
        Returns:
            bool: True si le téléchargement a réussi
        """
        endpoint = f"{self.base_url}/output/{filename}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return True
            except Exception as e:
                print(f"Erreur téléchargement vidéo annotée: {e}")
                return False
    
    async def check_service_health(self) -> bool:
        """
        Vérifie que le service de détection d'animaux est accessible.
        
        Returns:
            bool: True si le service est accessible
        """
        endpoint = f"{self.base_url}/health"
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                health_data = response.json()
                return health_data.get("status") == "healthy"
            except Exception as e:
                print(f"Erreur health check animal detection: {e}")
                return False


# Instance globale du client
animal_detection_client = AnimalDetectionClient()
