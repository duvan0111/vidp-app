"""
Connecteur MongoDB pour la gestion des métadonnées vidéo.
Module préparé pour l'intégration future avec MongoDB.
"""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from app.core.config import settings
from app.models.video_model import VideoMetadata


class MongoDBConnector:
    """
    Gestionnaire de connexion MongoDB pour les métadonnées vidéo.
    
    Note: Ce module est préparé pour l'intégration future avec MongoDB.
    Pour l'instant, il n'est pas utilisé dans le workflow principal.
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
    
    async def connect(self) -> bool:
        """
        Établit la connexion à MongoDB.
        
        Returns:
            bool: True si la connexion est réussie, False sinon
        """
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            # Test de la connexion
            await self.client.admin.command('ping')
            self.database = self.client[settings.mongodb_database]
            self.collection = self.database.video_metadata
            return True
        except ConnectionFailure:
            return False
    
    async def disconnect(self):
        """Ferme la connexion à MongoDB."""
        if self.client:
            self.client.close()
    
    async def save_video_metadata(self, metadata: VideoMetadata) -> bool:
        """
        Sauvegarde les métadonnées d'une vidéo.
        
        Args:
            metadata: Métadonnées de la vidéo
            
        Returns:
            bool: True si la sauvegarde est réussie
        """
        try:
            if self.collection is None:
                return False
            
            # Convertir en dict et gérer les dates
            metadata_dict = metadata.model_dump()
            await self.collection.insert_one(metadata_dict)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des métadonnées: {e}")
            return False
    
    async def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Récupère les métadonnées d'une vidéo par son ID.
        
        Args:
            video_id: Identifiant de la vidéo
            
        Returns:
            VideoMetadata ou None si non trouvé
        """
        try:
            if self.collection is None:
                return None
            
            doc = await self.collection.find_one({"video_id": video_id})
            if doc:
                # Supprimer le champ _id de MongoDB pour éviter les problèmes de sérialisation
                doc.pop('_id', None)
                return VideoMetadata(**doc)
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération des métadonnées: {e}")
            return None
    
    async def update_video_status(self, video_id: str, new_status: str) -> bool:
        """
        Met à jour le statut d'une vidéo.
        
        Args:
            video_id: Identifiant de la vidéo
            new_status: Nouveau statut
            
        Returns:
            bool: True si la mise à jour est réussie
        """
        try:
            if self.collection is None:
                return False
            
            result = await self.collection.update_one(
                {"video_id": video_id},
                {"$set": {"status": new_status}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def update_processing_stage(
        self, 
        video_id: str, 
        current_stage: str,
        stages_completed: list = None,
        stages_failed: list = None
    ) -> bool:
        """
        Met à jour l'étape de traitement actuelle d'une vidéo.
        
        Args:
            video_id: Identifiant de la vidéo
            current_stage: Étape actuelle (language_detection, compression, subtitle_generation)
            stages_completed: Liste des étapes terminées avec succès
            stages_failed: Liste des étapes échouées
            
        Returns:
            bool: True si la mise à jour est réussie
        """
        try:
            if self.collection is None:
                return False
            
            update_data = {"current_stage": current_stage}
            if stages_completed is not None:
                update_data["stages_completed"] = stages_completed
            if stages_failed is not None:
                update_data["stages_failed"] = stages_failed
            
            result = await self.collection.update_one(
                {"video_id": video_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Erreur lors de la mise à jour de l'étape: {e}")
            return False
    
    async def list_all_videos(self) -> List[VideoMetadata]:
        """
        Liste toutes les vidéos en base.
        
        Returns:
            List[VideoMetadata]: Liste des métadonnées
        """
        try:
            if self.collection is None:
                return []
            
            cursor = self.collection.find({}).sort("upload_time", -1)  # Tri par date décroissante
            videos = []
            async for doc in cursor:
                # Supprimer le champ _id de MongoDB
                doc.pop('_id', None)
                videos.append(VideoMetadata(**doc))
            return videos
        except Exception as e:
            print(f"Erreur lors de la liste des vidéos: {e}")
            return []
    
    async def save_processing_result(
        self, 
        video_id: str, 
        processing_type: str, 
        result: dict
    ) -> bool:
        """
        Sauvegarde le résultat d'un traitement pour une vidéo.
        
        Args:
            video_id: Identifiant de la vidéo
            processing_type: Type de traitement (language_detection, compression, subtitle_generation)
            result: Résultat du traitement
            
        Returns:
            bool: True si la sauvegarde est réussie
        """
        try:
            if self.database is None:
                return False
            
            processing_collection = self.database.processing_results
            
            # Créer ou mettre à jour le résultat
            await processing_collection.update_one(
                {"video_id": video_id, "processing_type": processing_type},
                {"$set": {
                    "video_id": video_id,
                    "processing_type": processing_type,
                    "result": result,
                    "updated_at": result.get("completed_at")
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du résultat de traitement: {e}")
            return False
    
    async def get_processing_result(
        self, 
        video_id: str, 
        processing_type: str
    ) -> Optional[dict]:
        """
        Récupère le résultat d'un traitement pour une vidéo.
        
        Args:
            video_id: Identifiant de la vidéo
            processing_type: Type de traitement
            
        Returns:
            dict ou None si non trouvé
        """
        try:
            if self.database is None:
                return None
            
            processing_collection = self.database.processing_results
            
            doc = await processing_collection.find_one({
                "video_id": video_id,
                "processing_type": processing_type
            })
            
            if doc:
                return doc.get("result")
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du résultat de traitement: {e}")
            return None
    
    async def list_all_processing_results(self, video_id: str) -> List[dict]:
        """
        Liste tous les résultats de traitement pour une vidéo.
        
        Args:
            video_id: Identifiant de la vidéo
            
        Returns:
            List[dict]: Liste des résultats de traitement
        """
        try:
            if self.database is None:
                return []
            
            processing_collection = self.database.processing_results
            
            cursor = processing_collection.find({"video_id": video_id})
            results = []
            async for doc in cursor:
                doc.pop('_id', None)
                results.append(doc)
            return results
        except Exception as e:
            print(f"Erreur lors de la liste des résultats de traitement: {e}")
            return []


# Instance globale du connecteur (à utiliser quand MongoDB sera configuré)
mongodb_connector = MongoDBConnector()
