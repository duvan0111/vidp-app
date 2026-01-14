"""
Client HTTP pour communiquer avec le service de génération de sous-titres (app_subtitle).
"""
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class SubtitleClient:
    """
    Client pour interagir avec le microservice de génération de sous-titres.
    """
    
    def __init__(self):
        self.base_url = settings.subtitle_service_url
        self.timeout = settings.microservices_timeout
        # Timeout spécifique pour la transcription (peut être très long)
        self.video_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),  # Utilise le timeout configuré (1800s par défaut)
            write=300.0,
            pool=30.0
        )
    
    async def generate_subtitles(
        self,
        video_path: str,
        model_name: str = "base",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Génère des sous-titres pour une vidéo en uploadant le fichier.
        
        IMPORTANT: Upload du fichier via HTTP pour compatibilité Kubernetes.
        
        Args:
            video_path: Chemin du fichier vidéo local
            model_name: Modèle Whisper (tiny, base, small, medium, large)
            language: Code langue ISO (ex: fr, en) - optionnel
            
        Returns:
            Dict contenant le texte transcrit et les métadonnées
        """
        endpoint = f"{self.base_url}/api/generate-subtitles/"
        
        # Vérifier que le fichier existe
        video_file_path = Path(video_path)
        if not video_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier vidéo introuvable",
                "detail": f"Le fichier {video_path} n'existe pas"
            }
        
        async with httpx.AsyncClient(timeout=self.video_timeout) as client:
            try:
                # Préparer le fichier pour l'upload
                with open(video_file_path, 'rb') as video_file:
                    files = {
                        'video': (video_file_path.name, video_file, 'video/mp4')
                    }
                    data = {
                        'model_name': model_name
                    }
                    
                    if language:
                        data['language'] = language
                    
                    # Upload et génération de sous-titres
                    response = await client.post(
                        endpoint,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    
                    # La réponse est un JSON contenant full_text et srt_url
                    response_data = response.json()
                    
                    return {
                        "status": "completed",
                        "full_text": response_data.get("full_text", ""),
                        "srt_url": response_data.get("srt_url"),
                        "model_name": model_name,
                        "language": language
                    }
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de la génération de sous-titres",
                    "detail": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de sous-titres",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de l'upload du fichier",
                    "detail": str(e)
                }
    
    async def download_subtitle_file(self, filename: str, output_path: str) -> bool:
        """
        Télécharge un fichier de sous-titres SRT.
        
        Args:
            filename: Nom du fichier de sous-titres
            output_path: Chemin où sauvegarder le fichier
            
        Returns:
            bool: True si le téléchargement réussit
        """
        endpoint = f"{self.base_url}/api/download-subtitles/{filename}"
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                
                # Sauvegarder le fichier
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                return True
                
            except Exception as e:
                print(f"Erreur lors du téléchargement: {e}")
                return False
    
    async def get_api_info(self) -> Dict[str, Any]:
        """
        Récupère les informations sur l'API de sous-titres.
        
        Returns:
            Dict contenant les informations de l'API
        """
        endpoint = f"{self.base_url}/api/info"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "error": "Erreur lors de la récupération des informations",
                    "detail": str(e)
                }
    
    async def check_service_health(self) -> bool:
        """
        Vérifie si le service de sous-titres est accessible.
        
        Returns:
            bool: True si le service est accessible
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/health")
                return response.status_code == 200
        except:
            return False


# Instance globale du client
subtitle_client = SubtitleClient()
