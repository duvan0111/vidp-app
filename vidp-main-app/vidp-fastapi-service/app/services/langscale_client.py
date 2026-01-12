"""
Client HTTP pour communiquer avec le service de détection de langue (app_langscale).
"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.models.video_model import ProcessingStatus


class LanguageDetectionClient:
    """
    Client pour interagir avec le microservice de détection de langue.
    """
    
    def __init__(self):
        self.base_url = settings.langscale_service_url
        self.timeout = settings.microservices_timeout
        # Timeout spécifique pour la détection de langue
        self.video_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),  # Utilise le timeout configuré (1800s par défaut)
            write=300.0,
            pool=30.0
        )
        
    async def detect_language_from_local_file(
        self, 
        video_path: str, 
        duration: int = 30, 
        test_all_languages: bool = True
    ) -> Dict[str, Any]:
        """
        Envoie une requête de détection de langue pour un fichier local.
        
        IMPORTANT: Cette méthode upload le fichier vidéo au service de détection.
        Cela fonctionne en développement local ET en production Kubernetes où les
        services sont sur des machines différentes avec des systèmes de fichiers séparés.
        
        Args:
            video_path: Chemin du fichier vidéo local à uploader
            duration: Durée d'extraction audio en secondes
            test_all_languages: Tester toutes les langues disponibles
            
        Returns:
            Dict contenant le résultat de la détection
            
        Raises:
            httpx.HTTPError: En cas d'erreur de communication
        """
        endpoint = f"{self.base_url}/api/detect/upload"
        
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
                        'duration': str(duration),
                        'test_all_languages': str(test_all_languages).lower(),
                        'async_mode': 'false'
                    }
                    
                    # Mode synchrone pour avoir le résultat immédiatement
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
                    "error": "Timeout lors de la détection de langue",
                    "detail": str(e)
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de détection",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de l'upload du fichier",
                    "detail": str(e)
                }
    
    async def detect_language_async(
        self, 
        video_path: str, 
        duration: int = 30, 
        test_all_languages: bool = True
    ) -> Dict[str, Any]:
        """
        Envoie une requête de détection de langue en mode asynchrone.
        
        IMPORTANT: Cette méthode upload le fichier vidéo au service de détection.
        Cela fonctionne en développement local ET en production Kubernetes.
        
        Args:
            video_path: Chemin du fichier vidéo local à uploader
            duration: Durée d'extraction audio en secondes
            test_all_languages: Tester toutes les langues disponibles
            
        Returns:
            Dict contenant le job_id pour suivi ultérieur
        """
        endpoint = f"{self.base_url}/api/detect/upload"
        
        # Vérifier que le fichier existe
        video_file_path = Path(video_path)
        if not video_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier vidéo introuvable",
                "detail": f"Le fichier {video_path} n'existe pas"
            }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Préparer le fichier pour l'upload
                with open(video_file_path, 'rb') as video_file:
                    files = {
                        'file': (video_file_path.name, video_file, 'video/mp4')
                    }
                    data = {
                        'duration': str(duration),
                        'test_all_languages': str(test_all_languages).lower(),
                        'async_mode': 'true'  # Mode asynchrone
                    }
                    
                    response = await client.post(
                        endpoint,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service de détection",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur lors de l'upload du fichier",
                    "detail": str(e)
                }
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'un job de détection de langue.
        
        Args:
            job_id: Identifiant du job
            
        Returns:
            Dict contenant le statut et les résultats du job
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
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """
        Récupère la liste des langues supportées par le service.
        
        Returns:
            Dict contenant la liste des langues
        """
        endpoint = f"{self.base_url}/api/languages"
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                return {
                    "error": "Erreur lors de la récupération des langues",
                    "detail": str(e)
                }
    
    async def check_service_health(self) -> bool:
        """
        Vérifie si le service de détection de langue est accessible.
        
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
language_detection_client = LanguageDetectionClient()
