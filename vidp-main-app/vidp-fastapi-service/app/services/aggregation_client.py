"""
Client HTTP pour communiquer avec le service d'agrégation vidéo (app_agregation).

Ce service combine la vidéo compressée avec les sous-titres générés pour produire
une vidéo finale avec sous-titres incrustés (burned-in).
"""
import httpx
import io
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class AggregationClient:
    """
    Client pour interagir avec le microservice d'agrégation vidéo.
    
    Le service d'agrégation :
    1. Reçoit une vidéo compressée et une URL de fichier SRT
    2. Incruste les sous-titres dans la vidéo (burning)
    3. Stocke la vidéo finale
    4. Retourne une URL de streaming
    """
    
    def __init__(self):
        self.base_url = settings.aggregation_service_url
        self.timeout = settings.microservices_timeout
        # Timeout spécifique pour l'agrégation (traitement FFmpeg peut être long)
        self.video_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),  # Utilise le timeout configuré
            write=600.0,  # Upload de vidéo peut prendre du temps
            pool=30.0
        )
    
    async def check_service_health(self) -> bool:
        """
        Vérifie si le service d'agrégation est accessible.
        
        Returns:
            True si le service répond, False sinon
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Service d'agrégation inaccessible: {e}")
            return False
    
    async def process_video_with_subtitles(
        self,
        video_path: str,
        srt_url: str,
        resolution: str = "360p",
        crf_value: int = 23,
        source_video_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envoie une vidéo compressée et le fichier SRT au service d'agrégation pour incrustation des sous-titres.
        
        Args:
            video_path: Chemin du fichier vidéo compressé (local)
            srt_url: URL du fichier SRT depuis le service de sous-titres (sera téléchargé puis envoyé)
            resolution: Résolution cible (360p, 480p, 720p, 1080p)
            crf_value: Valeur CRF pour la qualité vidéo (0-51)
            source_video_id: ID de la vidéo source dans vidp-fastapi-service (pour référence croisée)
            
        Returns:
            Dict contenant:
            - status: "completed" ou "failed"
            - video_id: ID de la vidéo agrégée
            - streaming_url: URL pour streamer la vidéo finale
            - metadata: Informations sur la vidéo (durée, taille, résolution)
            - error: Message d'erreur (si échec)
        """
        endpoint = f"{self.base_url}/api/process-video/"
        
        # Vérifier que le fichier vidéo existe
        video_file_path = Path(video_path)
        if not video_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier vidéo introuvable",
                "detail": f"Le fichier {video_path} n'existe pas"
            }
        
        async with httpx.AsyncClient(timeout=self.video_timeout) as client:
            try:
                # Étape 1: Télécharger le fichier SRT depuis l'URL
                print(f"📥 Téléchargement du fichier SRT depuis: {srt_url}")
                try:
                    srt_response = await client.get(srt_url, timeout=30.0)
                    srt_response.raise_for_status()
                    srt_content = srt_response.content
                    print(f"   ✅ Fichier SRT téléchargé ({len(srt_content)} bytes)")
                except httpx.HTTPError as e:
                    return {
                        "status": "failed",
                        "error": "Impossible de télécharger le fichier SRT",
                        "detail": f"Erreur lors du téléchargement depuis {srt_url}: {e}"
                    }
                
                # Étape 2: Préparer les fichiers pour l'upload
                # Utiliser BytesIO pour le fichier SRT
                srt_file_obj = io.BytesIO(srt_content)
                
                with open(video_file_path, 'rb') as video_file:
                    # Lire tout le contenu vidéo pour éviter les problèmes de curseur
                    video_content = video_file.read()
                
                video_file_obj = io.BytesIO(video_content)
                
                files = {
                    'video': (video_file_path.name, video_file_obj, 'video/mp4'),
                    'srt_file': ('subtitles.srt', srt_file_obj, 'text/plain')
                }
                data = {
                    'resolution': resolution,
                    'crf_value': str(crf_value)
                }
                
                # Add source_video_id if provided (for cross-database reference)
                if source_video_id:
                    data['source_video_id'] = source_video_id
                
                print(f"📤 Envoi de la vidéo et du SRT au service d'agrégation...")
                print(f"   Vidéo: {video_file_path.name} ({len(video_content)} bytes)")
                print(f"   SRT: subtitles.srt ({len(srt_content)} bytes)")
                print(f"   Résolution: {resolution}")
                if source_video_id:
                    print(f"   Source Video ID: {source_video_id}")
                
                # Envoyer au service d'agrégation
                response = await client.post(
                    endpoint,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                response_data = response.json()
                
                return {
                    "status": "completed",
                    "job_id": response_data.get("job_id"),
                    "video_id": response_data.get("video_id"),
                    "streaming_url": response_data.get("streaming_url"),
                    "metadata": response_data.get("metadata", {}),
                    "message": response_data.get("message", "Agrégation terminée")
                }
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de l'agrégation vidéo",
                    "detail": f"Le service n'a pas répondu dans le délai imparti: {e}"
                }
            except httpx.HTTPStatusError as e:
                error_detail = str(e)
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("detail", str(e))
                except:
                    pass
                return {
                    "status": "failed",
                    "error": f"Erreur HTTP {e.response.status_code}",
                    "detail": error_detail
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service d'agrégation",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur inattendue lors de l'agrégation",
                    "detail": str(e)
                }
    
    async def process_video_with_srt_content(
        self,
        video_path: str,
        srt_content: str,
        resolution: str = "360p",
        crf_value: int = 23,
        source_video_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envoie une vidéo avec un contenu SRT direct (sans téléchargement depuis URL).
        
        Utile pour les vidéos sans audio où on génère un SRT vide/placeholder.
        
        Args:
            video_path: Chemin du fichier vidéo compressé (local)
            srt_content: Contenu du fichier SRT (chaîne de caractères)
            resolution: Résolution cible (360p, 480p, 720p, 1080p)
            crf_value: Valeur CRF pour la qualité vidéo (0-51)
            source_video_id: ID de la vidéo source dans vidp-fastapi-service (pour référence croisée)
            
        Returns:
            Dict contenant le résultat de l'agrégation
        """
        endpoint = f"{self.base_url}/api/process-video/"
        
        # Vérifier que le fichier vidéo existe
        video_file_path = Path(video_path)
        if not video_file_path.exists():
            return {
                "status": "failed",
                "error": "Fichier vidéo introuvable",
                "detail": f"Le fichier {video_path} n'existe pas"
            }
        
        async with httpx.AsyncClient(timeout=self.video_timeout) as client:
            try:
                # Préparer le fichier SRT depuis le contenu direct
                srt_bytes = srt_content.encode('utf-8')
                srt_file_obj = io.BytesIO(srt_bytes)
                
                with open(video_file_path, 'rb') as video_file:
                    video_content = video_file.read()
                
                video_file_obj = io.BytesIO(video_content)
                
                files = {
                    'video': (video_file_path.name, video_file_obj, 'video/mp4'),
                    'srt_file': ('subtitles.srt', srt_file_obj, 'text/plain')
                }
                data = {
                    'resolution': resolution,
                    'crf_value': str(crf_value)
                }
                
                # Add source_video_id if provided (for cross-database reference)
                if source_video_id:
                    data['source_video_id'] = source_video_id
                
                print(f"📤 Envoi de la vidéo avec SRT direct au service d'agrégation...")
                print(f"   Vidéo: {video_file_path.name} ({len(video_content)} bytes)")
                print(f"   SRT: contenu direct ({len(srt_bytes)} bytes)")
                print(f"   Résolution: {resolution}")
                if source_video_id:
                    print(f"   Source Video ID: {source_video_id}")
                
                response = await client.post(
                    endpoint,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                response_data = response.json()
                
                return {
                    "status": "completed",
                    "job_id": response_data.get("job_id"),
                    "video_id": response_data.get("video_id"),
                    "streaming_url": response_data.get("streaming_url"),
                    "metadata": response_data.get("metadata", {}),
                    "message": response_data.get("message", "Agrégation terminée (sans sous-titres)")
                }
                
            except httpx.TimeoutException as e:
                return {
                    "status": "failed",
                    "error": "Timeout lors de l'agrégation vidéo",
                    "detail": f"Le service n'a pas répondu dans le délai imparti: {e}"
                }
            except httpx.HTTPStatusError as e:
                error_detail = str(e)
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("detail", str(e))
                except:
                    pass
                return {
                    "status": "failed",
                    "error": f"Erreur HTTP {e.response.status_code}",
                    "detail": error_detail
                }
            except httpx.HTTPError as e:
                return {
                    "status": "failed",
                    "error": "Erreur de communication avec le service d'agrégation",
                    "detail": str(e)
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": "Erreur inattendue lors de l'agrégation",
                    "detail": str(e)
                }
    
    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une vidéo agrégée.
        
        Args:
            video_id: ID de la vidéo dans le service d'agrégation
            
        Returns:
            Dict avec les métadonnées et le statut de la vidéo
        """
        endpoint = f"{self.base_url}/api/videos/{video_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "data": response.json()
                }
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return {
                        "status": "not_found",
                        "error": f"Vidéo {video_id} non trouvée"
                    }
                return {
                    "status": "failed",
                    "error": f"Erreur HTTP {e.response.status_code}"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)
                }
    
    async def get_streaming_url(self, video_id: str) -> Optional[str]:
        """
        Récupère l'URL de streaming pour une vidéo agrégée.
        
        Args:
            video_id: ID de la vidéo
            
        Returns:
            URL de streaming ou None si non disponible
        """
        result = await self.get_video_status(video_id)
        if result.get("status") == "success":
            data = result.get("data", {})
            return data.get("link") or data.get("streaming_url")
        return None
    
    async def get_video_by_source_id(self, source_video_id: str) -> Dict[str, Any]:
        """
        Récupère une vidéo agrégée par son ID source (vidp-fastapi-service).
        
        Permet de retrouver la vidéo agrégée correspondant à une vidéo
        traitée par le service principal.
        
        Args:
            source_video_id: ID de la vidéo dans vidp-fastapi-service
            
        Returns:
            Dict avec les métadonnées de la vidéo agrégée ou une erreur
        """
        endpoint = f"{self.base_url}/api/videos/by-source/{source_video_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "data": response.json()
                }
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return {
                        "status": "not_found",
                        "error": f"Aucune vidéo agrégée trouvée pour source_video_id: {source_video_id}"
                    }
                return {
                    "status": "failed",
                    "error": f"Erreur HTTP {e.response.status_code}"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)
                }


# Instance globale du client
aggregation_client = AggregationClient()
