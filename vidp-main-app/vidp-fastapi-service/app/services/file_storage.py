"""
Service de gestion du stockage local des fichiers vidéo.
"""
import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Tuple

from app.core.config import settings


class FileStorageService:
    """Service pour la gestion du stockage local des fichiers."""
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """
        Génère un nom de fichier unique basé sur UUID tout en préservant l'extension.
        
        Args:
            original_filename: Nom original du fichier
            
        Returns:
            Nom de fichier unique avec extension
        """
        file_extension = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"
    
    @staticmethod
    def _validate_video_file(file: UploadFile) -> None:
        """
        Valide que le fichier uploadé est bien une vidéo.
        
        Args:
            file: Fichier uploadé
            
        Raises:
            HTTPException: Si le fichier n'est pas valide
        """
        # Types MIME acceptés pour les vidéos
        allowed_video_types = {
            "video/mp4",
            "video/avi", 
            "video/mov",
            "video/wmv",
            "video/flv",
            "video/webm",
            "video/mkv"
        }
        
        # Vérifier le type MIME
        if file.content_type not in allowed_video_types:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté: {file.content_type}. "
                       f"Types acceptés: {', '.join(allowed_video_types)}"
            )
        
        # Vérifier que le fichier n'est pas vide
        if file.size == 0:
            raise HTTPException(
                status_code=400,
                detail="Le fichier est vide"
            )
        
        # Limite de taille (500 MB par défaut)
        max_size = 500 * 1024 * 1024  # 500 MB en octets
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Taille maximale: {max_size // (1024*1024)} MB"
            )
    
    @staticmethod
    async def save_video_file(file: UploadFile) -> Tuple[str, str, int]:
        """
        Sauvegarde un fichier vidéo sur le disque local.
        
        Args:
            file: Fichier uploadé via FastAPI
            
        Returns:
            Tuple contenant:
            - unique_filename: Nom unique généré pour le fichier
            - full_path: Chemin complet vers le fichier sauvegardé
            - file_size: Taille du fichier en octets
            
        Raises:
            HTTPException: En cas d'erreur de validation ou de sauvegarde
        """
        try:
            # Validation du fichier
            FileStorageService._validate_video_file(file)
            
            # Génération d'un nom de fichier unique
            unique_filename = FileStorageService._generate_unique_filename(file.filename)
            
            # Construction du chemin complet
            storage_path = Path(settings.local_video_path)
            full_path = storage_path / unique_filename
            
            # S'assurer que le dossier existe
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarde asynchrone du fichier
            async with aiofiles.open(full_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Vérification que le fichier a bien été créé
            if not full_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Erreur lors de la sauvegarde du fichier"
                )
            
            file_size = full_path.stat().st_size
            
            return unique_filename, str(full_path), file_size
            
        except HTTPException:
            # Re-lever les HTTPException telles quelles
            raise
        except Exception as e:
            # Capturer toute autre erreur inattendue
            raise HTTPException(
                status_code=500,
                detail=f"Erreur interne lors de la sauvegarde: {str(e)}"
            )
    
    @staticmethod
    def delete_video_file(file_path: str) -> bool:
        """
        Supprime un fichier vidéo du stockage local.
        
        Args:
            file_path: Chemin vers le fichier à supprimer
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        Récupère les informations d'un fichier.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire avec les informations du fichier
        """
        try:
            path = Path(file_path)
            if path.exists():
                stat = path.stat()
                return {
                    "exists": True,
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "filename": path.name
                }
            return {"exists": False}
        except Exception:
            return {"exists": False}
