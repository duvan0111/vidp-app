"""
Utilitaires pour l'analyse et le traitement des fichiers vidéo.
"""
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def check_video_has_audio(video_path: str) -> bool:
    """
    Vérifie si une vidéo contient une piste audio valide.
    
    Utilise ffprobe pour analyser les streams de la vidéo et détecter
    la présence d'une piste audio avec un codec valide.
    
    Args:
        video_path: Chemin vers le fichier vidéo
        
    Returns:
        bool: True si la vidéo contient une piste audio, False sinon
    """
    try:
        # Vérifier que le fichier existe
        if not Path(video_path).exists():
            logger.warning(f"Fichier vidéo non trouvé: {video_path}")
            return False
        
        # Utiliser ffprobe pour obtenir les informations sur les streams
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'a',  # Sélectionner uniquement les streams audio
            str(video_path)
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"ffprobe a retourné une erreur: {result.stderr}")
            return False
        
        # Parser la sortie JSON
        probe_data = json.loads(result.stdout)
        streams = probe_data.get('streams', [])
        
        # Vérifier s'il y a au moins un stream audio
        if not streams:
            logger.info(f"Aucune piste audio trouvée dans: {video_path}")
            return False
        
        # Vérifier que le stream audio a un codec valide
        for stream in streams:
            codec_name = stream.get('codec_name', '')
            codec_type = stream.get('codec_type', '')
            
            if codec_type == 'audio' and codec_name:
                # Vérifier que ce n'est pas un codec "vide" ou invalide
                duration = stream.get('duration', '0')
                try:
                    if float(duration) > 0:
                        logger.info(f"Piste audio trouvée: codec={codec_name}, durée={duration}s")
                        return True
                except (ValueError, TypeError):
                    # Si la durée n'est pas disponible, on vérifie d'autres indicateurs
                    nb_frames = stream.get('nb_frames', '0')
                    if nb_frames and int(nb_frames) > 0:
                        logger.info(f"Piste audio trouvée: codec={codec_name}, frames={nb_frames}")
                        return True
                    
                    # Dernière vérification: si le codec existe et a un sample_rate
                    sample_rate = stream.get('sample_rate', '0')
                    if sample_rate and int(sample_rate) > 0:
                        logger.info(f"Piste audio trouvée: codec={codec_name}, sample_rate={sample_rate}")
                        return True
        
        logger.info(f"Aucune piste audio valide trouvée dans: {video_path}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout lors de l'analyse de la vidéo: {video_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing JSON de ffprobe: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la vérification audio: {e}")
        return False


def get_video_info(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les informations complètes d'une vidéo via ffprobe.
    
    Args:
        video_path: Chemin vers le fichier vidéo
        
    Returns:
        Dict contenant les informations de la vidéo ou None en cas d'erreur
    """
    try:
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"ffprobe a retourné une erreur: {result.stderr}")
            return None
        
        return json.loads(result.stdout)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos vidéo: {e}")
        return None


def create_empty_srt_content() -> str:
    """
    Crée un contenu SRT vide mais valide.
    
    Utilisé pour les vidéos sans audio qui ne peuvent pas générer de sous-titres.
    
    Returns:
        str: Contenu SRT minimal valide
    """
    # Un fichier SRT vide est techniquement valide
    # Mais pour éviter des problèmes avec certains players, on crée un sous-titre invisible
    return ""


def create_placeholder_srt_content(message: str = "Cette vidéo n'a pas de piste audio") -> str:
    """
    Crée un contenu SRT avec un message placeholder.
    
    Args:
        message: Message à afficher comme sous-titre
        
    Returns:
        str: Contenu SRT avec le message
    """
    return f"""1
00:00:00,000 --> 00:00:05,000
{message}

"""
