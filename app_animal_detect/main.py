"""
FastAPI YOLO Animal Detection Project
=====================================
Install dependencies:
pip install fastapi uvicorn python-multipart opencv-python ultralytics lap
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
from ultralytics import YOLO
import numpy as np
from pathlib import Path
import shutil
from typing import Dict
import tempfile
import base64
import traceback

app = FastAPI(
    title="YOLO Animal Detection API",
    description="API pour détecter des animaux dans des vidéos avec YOLOv8",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Charger le modèle YOLO
model = YOLO('yolov8n.pt')

# Classes d'animaux dans COCO dataset (utilisé par YOLOv8)
ANIMAL_CLASSES = {
    15: 'chat', 16: 'chien', 17: 'cheval', 18: 'mouton', 
    19: 'vache', 20: 'éléphant', 21: 'ours', 22: 'zèbre', 
    23: 'girafe', 24: 'sac à dos', 25: 'parapluie'
}


@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "API de détection d'animaux avec YOLO",
        "endpoints": {
            "/detect": "POST - Télécharger une vidéo pour détection (pas de sauvegarde)",
            "/detect/frame": "POST - Détecter sur une seule image",
            "/animals": "GET - Liste des animaux détectables",
            "/health": "GET - Vérifier l'état de l'API"
        },
        "note": "Aucune vidéo n'est conservée sur le serveur"
    }


@app.get("/animals")
async def get_animals():
    """Retourne la liste complète des classes détectables"""
    all_classes = {id: name for id, name in model.names.items()}
    return {
        "total_classes": len(all_classes),
        "all_classes": all_classes,
        "animal_focus": ANIMAL_CLASSES
    }


@app.post("/detect")
async def detect_video(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    save_video: bool = False,
    frame_step: int = 15,
    resize_width: int = 640
):
    """
    Détecte les animaux dans une vidéo uploadée
    
    Args:
        file: Fichier vidéo à analyser
        confidence_threshold: Seuil de confiance minimum (0-1)
        save_video: Ignoré - les vidéos ne sont jamais sauvegardées
        frame_step: Le nombre de frames à sauter entre chaque analyse (1 = chaque frame, 15 = une frame sur 15, etc.)
        resize_width: Largeur pour redimensionner les frames avant l'analyse (ex: 640). Maintient le ratio.
    
    Returns:
        JSON avec statistiques et détections par frame
    """
    
    # Vérifier l'extension du fichier
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Format vidéo non supporté. Utilisez .mp4, .avi, .mov ou .mkv")
    
    if frame_step < 1:
        raise HTTPException(400, "frame_step doit être supérieur ou égal à 1")
    
    # Créer un fichier temporaire pour la vidéo uploadée
    temp_file = None
    try:
        # Créer un fichier temporaire
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
        
        # Traiter la vidéo
        results = process_video(temp_file.name, confidence_threshold, frame_step, resize_width)
        
        # Ajouter une note si save_video était demandé
        if save_video:
            results["note"] = "Le paramètre save_video est ignoré - aucune vidéo n'est jamais sauvegardée pour des raisons de confidentialité"
        
        return JSONResponse(content=results)
    
    except Exception as e:
        # Log l'erreur complète pour le débogage
        error_details = traceback.format_exc()
        print(f"Erreur lors du traitement: {error_details}")
        raise HTTPException(500, f"Erreur lors du traitement: {str(e)}")
    
    finally:
        # Nettoyer le fichier temporaire
        if temp_file and Path(temp_file.name).exists():
            try:
                Path(temp_file.name).unlink()
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier temporaire: {e}")


@app.post("/detect/frame")
async def detect_frame(file: UploadFile = File(...), confidence_threshold: float = 0.5):
    """
    Détecte les animaux sur une seule image
    
    Args:
        file: Fichier image (jpg, png)
        confidence_threshold: Seuil de confiance minimum
    
    Returns:
        JSON avec détections et image annotée en base64
    """
    
    if not file.filename.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        raise HTTPException(400, "Format image non supporté")
    
    try:
        # Lire l'image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(400, "Impossible de lire l'image")
        
        # Détecter
        results = model(frame, conf=confidence_threshold)
        
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                coords = box.xyxy[0].tolist()
                
                detections.append({
                    "class_id": class_id,
                    "class_name": model.names[class_id],
                    "confidence": round(confidence, 3),
                    "bbox": coords
                })
        
        # Image annotée
        annotated = results[0].plot()
        _, buffer = cv2.imencode('.jpg', annotated)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "detections": detections,
            "total_objects": len(detections),
            "annotated_image": img_base64
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Erreur lors du traitement de l'image: {error_details}")
        raise HTTPException(500, f"Erreur lors du traitement: {str(e)}")


def process_video(
    video_path: str, 
    conf_threshold: float,
    frame_step: int = 1,
    resize_width: int = None
) -> Dict:
    """Traite la vidéo et extrait les détections"""
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError("Impossible d'ouvrir la vidéo")
    
    # Infos vidéo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Statistiques
    frame_detections = []
    animals_count = {}
    frame_idx = 0
    processed_frames_count = 0
    
    try:
        while frame_idx < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = cap.read()
            
            if not success:
                break
            
            processed_frames_count += 1
            
            # Redimensionner la frame si nécessaire
            if resize_width and resize_width < original_width:
                aspect_ratio = original_height / original_width
                new_height = int(resize_width * aspect_ratio)
                if new_height > 0:
                    frame = cv2.resize(frame, (resize_width, new_height))

            # Détection simple, car le suivi n'est pas requis
            results = model(frame, conf=conf_threshold)
            use_tracking = False
            
            frame_data = {
                "frame": frame_idx,
                "timestamp": round(frame_idx / fps, 2) if fps > 0 else 0,
                "detections": []
            }
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Compter les animaux
                    animals_count[class_name] = animals_count.get(class_name, 0) + 1
                    
                    # Track ID si disponible
                    track_id = None
                    if use_tracking and box.id is not None:
                        track_id = int(box.id[0])
                    
                    detection = {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 3)
                    }
                    
                    if track_id is not None:
                        detection["track_id"] = track_id
                    
                    frame_data["detections"].append(detection)
            
            if frame_data["detections"]:
                frame_detections.append(frame_data)
            
            frame_idx += frame_step
    
    finally:
        cap.release()
    
    # Résultats finaux
    return {
        "video_info": {
            "duration_seconds": round(total_frames / fps, 2) if fps > 0 else 0,
            "fps": fps,
            "resolution": f"{original_width}x{original_height}",
            "total_frames": total_frames,
            "processed_frames": processed_frames_count
        },
        "detection_summary": {
            "total_detections": sum(animals_count.values()),
            "unique_classes": len(animals_count),
            "animals_detected": animals_count,
            "frames_with_detections": len(frame_detections)
        },
        "detailed_detections": frame_detections[:100]  # Limiter à 100 frames pour la réponse
    }


@app.get("/health")
async def health_check():
    """Vérifie que l'API et le modèle fonctionnent"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_type": "YOLOv8n"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)