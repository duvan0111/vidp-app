"""
Client HTTP pour communiquer avec le service de compression vidéo (app_downscale).
"""
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class CompressionClient:
    """
    Client pour interagir avec le microservice de compression vidéo.
    """
    
    def __init__(self):
        self.base_url = settings.downscale_service_url
        self.timeout = settings.microservices_timeout
        # Timeout spécifique pour la compression (peut être très long pour grosses vidéos)
        self.video_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),  # Utilise le timeout configuré (1800s par défaut)
            write=300.0,
            pool=30.0
        )
    
    async def compress_video(
        self,
        video_path: str,
        resolution: str = "360p",
        crf_value: int = 28,
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compresse une vidéo en uploadant le fichier au service.
        
        IMPORTANT: Upload du fichier via HTTP pour compatibilité Kubernetes.
        
        Args:
            video_path: Chemin du fichier vidéo local
            resolution: Résolution cible (240p, 360p, 480p, 720p, 1080p)
            crf_value: Valeur CRF pour la qualité (18-30)
            custom_filename: Nom de fichier personnalisé (optionnel)
            
        Returns:
            Dict contenant le résultat de la compression
        """
        endpoint = f"{self.base_url}/api/compress/upload"
        
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
                        'file': (video_file_path.name, video_file, 'video/mp4')
                    }
                    data = {
                        'resolution': resolution,
                        'crf_value': str(crf_value)
                    }
                    
                    if custom_filename:
                        data['custom_filename'] = custom_filename
                    
                    # Upload et compression
                    response = await client.post(
                        endpoint,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return response.json()
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de la compression",
                    "detail": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de compression",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de l'upload du fichier",
                    "detail": str(e)
                }
    
    async def get_compression_status(self, job_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un job de compression.
        
        Args:
            job_id: Identifiant du job
            
        Returns:
            Dict contenant le statut et les résultats
        """
        endpoint = f"{self.base_url}/api/status/{job_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de la récupération du statut",
                    "detail": str(e)
                }
    
    async def download_compressed_video(self, job_id: str, output_path: str) -> bool:
        """
        Télécharge la vidéo compressée.
        
        Args:
            job_id: Identifiant du job
            output_path: Chemin où sauvegarder la vidéo
            
        Returns:
            bool: True si le téléchargement réussit
        """
        endpoint = f"{self.base_url}/api/download/{job_id}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
    
    async def cleanup_compression_job(self, job_id: str) -> Dict[str, Any]:
        """
        Nettoie les fichiers d'un job de compression.
        
        Args:
            job_id: Identifiant du job
            
        Returns:
            Dict avec le résultat du nettoyage
        """
        endpoint = f"{self.base_url}/api/cleanup/{job_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.delete(endpoint)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "error": "Erreur lors du nettoyage",
                    "detail": str(e)
                }
    
    async def check_service_health(self) -> bool:
        """
        Vérifie si le service de compression est accessible.
        
        Returns:
            bool: True si le service est accessible
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except:
            return False


# Instance globale du client
compression_client = CompressionClient()
