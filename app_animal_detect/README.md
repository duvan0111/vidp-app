# 🐾 YOLO Animal Detection API

API FastAPI pour la détection d'animaux dans des vidéos et images utilisant YOLOv8.

## 📋 Description

Cette application utilise le modèle YOLOv8 (You Only Look Once) pour détecter et suivre des animaux dans des vidéos et des images. L'API fournit des endpoints REST pour uploader des médias, effectuer des détections, et récupérer les résultats annotés.

## ✨ Fonctionnalités

- 🎥 **Détection vidéo** : Analyse complète de vidéos avec tracking d'objets
- 🖼️ **Détection d'images** : Détection sur des images individuelles
- 📊 **Statistiques détaillées** : Comptage des animaux, timestamps, confiance
- 🎯 **Tracking d'objets** : Suivi des animaux à travers les frames
- 🗑️ **Pas de stockage** : Aucune vidéo n'est conservée sur le serveur (fichiers temporaires uniquement)
- 🌐 **API REST** : Interface HTTP facile à utiliser
- 🔄 **CORS activé** : Compatible avec les applications web front-end
- ⚡ **Performances optimales** : Utilisation de fichiers temporaires pour un traitement rapide

## 🐕 Animaux détectables

L'API peut détecter les classes d'animaux suivantes du dataset COCO :

- Chat
- Chien
- Cheval
- Mouton
- Vache
- Éléphant
- Ours
- Zèbre
- Girafe

## 🚀 Installation

### Prérequis

- Python 3.8+
- pip
- (Optionnel) GPU CUDA pour accélération

### Installation des dépendances

```bash
pip install fastapi uvicorn python-multipart opencv-python ultralytics
```

Ou utilisez le fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

### Téléchargement du modèle

Le modèle YOLOv8n sera téléchargé automatiquement au premier lancement. Vous pouvez aussi le télécharger manuellement :

```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

## 🎮 Utilisation

### Démarrage du serveur

```bash
python main.py
```

Ou avec uvicorn directement :

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

L'API sera accessible sur : `http://localhost:8000`

### Documentation interactive

- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## 📡 Endpoints API

### `GET /`
Page d'accueil avec la liste des endpoints disponibles.

**Réponse :**
```json
{
  "message": "API de détection d'animaux avec YOLO",
  "endpoints": {
    "/detect": "POST - Télécharger une vidéo pour détection (pas de sauvegarde)",
    "/detect/frame": "POST - Détecter sur une seule image",
    "/animals": "GET - Liste des animaux détectables",
    "/health": "GET - Vérifier l'état de l'API"
  },
  "note": "Aucune vidéo n'est conservée sur le serveur"
}
```

### `GET /animals`
Liste toutes les classes détectables par le modèle.

**Réponse :**
```json
{
  "total_classes": 80,
  "all_classes": {...},
  "animal_focus": {...}
}
```

### `POST /detect`
Détecte les animaux dans une vidéo uploadée. **Aucune vidéo n'est sauvegardée** : le fichier est traité et supprimé immédiatement.

**Paramètres :**
- `file` (form-data) : Fichier vidéo (.mp4, .avi, .mov, .mkv)
- `confidence_threshold` (float, optionnel) : Seuil de confiance (0-1, défaut: 0.5)

**Exemple avec curl :**
```bash
curl -X POST "http://localhost:8000/detect?confidence_threshold=0.5" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"
```

**Exemple avec Python :**
```python
import requests

url = "http://localhost:8000/detect"
files = {"file": open("video.mp4", "rb")}
params = {"confidence_threshold": 0.5}

response = requests.post(url, files=files, params=params)
print(response.json())
```

**Réponse :**
```json
{
  "video_info": {
    "duration_seconds": 10.5,
    "fps": 30,
    "resolution": "1920x1080",
    "total_frames": 315,
    "processed_frames": 315
  },
  "detection_summary": {
    "total_detections": 42,
    "unique_classes": 3,
    "animals_detected": {
      "dog": 25,
      "cat": 15,
      "horse": 2
    },
    "frames_with_detections": 280
  },
  "detailed_detections": [...]
}
```

> **Note** : Les détections détaillées sont limitées aux 100 premières frames pour optimiser la taille de la réponse.

### `POST /detect/frame`
Détecte les animaux sur une seule image.

**Paramètres :**
- `file` (form-data) : Fichier image (.jpg, .jpeg, .png, .bmp)
- `confidence_threshold` (float, optionnel) : Seuil de confiance (défaut: 0.5)

**Exemple :**
```bash
curl -X POST "http://localhost:8000/detect/frame?confidence_threshold=0.5" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg"
```

**Réponse :**
```json
{
  "detections": [
    {
      "class_id": 16,
      "class_name": "dog",
      "confidence": 0.952,
      "bbox": [120.5, 200.3, 450.2, 600.8]
    }
  ],
  "total_objects": 1,
  "annotated_image": "base64_encoded_image..."
}
```

### `GET /health`
Vérifie l'état de santé de l'API et du modèle.

**Réponse :**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "YOLOv8n"
}
```

## 📁 Structure du projet

```
app_animal_detect/
├── main.py              # Application FastAPI principale
├── requirements.txt     # Dépendances Python
├── yolov8n.pt          # Modèle YOLOv8 (téléchargé automatiquement)
├── Dockerfile          # Configuration Docker
├── CHANGELOG.md        # Historique des modifications
└── README.md           # Ce fichier
```

> **Important** : Cette application ne crée pas de dossiers `uploads/` ou `outputs/`. Tous les fichiers sont gérés en mémoire temporaire et automatiquement supprimés après traitement.

## 🔧 Configuration

### Modifier le modèle YOLO

Pour utiliser un modèle différent, modifiez la ligne dans `main.py` :

```python
model = YOLO('yolov8n.pt')  # yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
```

Modèles disponibles :
- `yolov8n.pt` : Nano (le plus rapide, moins précis)
- `yolov8s.pt` : Small
- `yolov8m.pt` : Medium
- `yolov8l.pt` : Large
- `yolov8x.pt` : Extra large (le plus précis, plus lent)

### Modifier le port

Dans `main.py`, ligne finale :

```python
uvicorn.run(app, port=8000)  # Changez 8000 pour un autre port
```

### Configuration CORS

Pour restreindre les origines autorisées, modifiez :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Ajoutez vos domaines
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 Dépannage

### Erreur de mémoire

Si vous rencontrez des erreurs de mémoire :
- Utilisez un modèle plus petit (yolov8n.pt)
- Réduisez la résolution des vidéos
- Traitez des vidéos plus courtes
- Vérifiez l'espace disponible dans `/tmp` (utilisé pour les fichiers temporaires)

### Problèmes OpenCV

Si OpenCV ne peut pas ouvrir la vidéo :
```bash
pip install opencv-python-headless
```

### Erreur CUDA

Si vous avez un GPU mais rencontrez des erreurs CUDA :
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 📊 Performances

- **YOLOv8n** : ~45 FPS sur GPU RTX 3080, ~5 FPS sur CPU
- **YOLOv8s** : ~35 FPS sur GPU RTX 3080, ~3 FPS sur CPU
- **YOLOv8m** : ~25 FPS sur GPU RTX 3080, ~1.5 FPS sur CPU

## 🔒 Confidentialité et Sécurité

### Gestion des fichiers
- ✅ **Aucune sauvegarde** : Les vidéos uploadées ne sont jamais conservées
- ✅ **Fichiers temporaires** : Utilisation de `tempfile` avec suppression automatique
- ✅ **Nettoyage garanti** : Bloc `finally` pour assurer la suppression même en cas d'erreur
- ✅ **Pas de traces** : Aucun historique des vidéos traitées


## 🔗 Liens utiles

- [Documentation Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Dataset COCO](https://cocodataset.org/)

