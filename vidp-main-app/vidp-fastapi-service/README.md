# VidP FastAPI Service

## Description

Service backend FastAPI pour la phase de prétraitement locale (VidP), capable de recevoir et stocker physiquement les fichiers vidéo uploadés par l'interface React. Ce service sert d'API pour la gestion future des métadonnées (MongoDB) et l'orchestration du traitement (Kubernetes).

## 🏗️ Architecture

```
vidp-fastapi-service/
├── .env                     # Configuration (ports, clés, chemins de stockage)
├── main.py                  # Point d'entrée principal de l'application
├── requirements.txt         # Dépendances Python
├── test_api.py             # Script de test de l'API
│
├── /app
│   ├── /api
│   │   └── /v1
│   │       ├── endpoints_video.py    # Endpoints d'upload de vidéo
│   │       └── endpoints_status.py   # Endpoints de statut
│   │
│   ├── /core
│   │   └── config.py        # Chargement des variables d'environnement
│   │
│   ├── /db
│   │   └── mongodb_connector.py # Gestion MongoDB (futur)
│   │
│   ├── /models
│   │   └── video_model.py   # Modèles Pydantic
│   │
│   └── /services
│       ├── file_storage.py  # Logique du stockage local
│       └── orchestrator.py  # Interaction avec K8s (futur)
│
└── /local_storage
    ├── /videos              # Dossier de destination des vidéos uploadées
    └── /metadata            # Dossier pour les métadonnées
```

## 🚀 Installation

### 1. Cloner et naviguer vers le projet
```bash
cd vidp-fastapi-service
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer l'environnement
Le fichier `.env` est déjà configuré avec les valeurs par défaut :
```env
APP_NAME=VidP Local API
APP_HOST=0.0.0.0
APP_PORT=8000
LOCAL_STORAGE_ROOT=./local_storage
LOCAL_VIDEO_PATH=./local_storage/videos
```

### 4. Lancer l'application
```bash
python3 main.py
```

L'API sera disponible sur : `http://localhost:8000`

## 📚 Documentation de l'API

### Endpoints principaux

- **Documentation Swagger** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

### Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/` | Informations de base sur l'API |
| `GET` | `/health` | Santé générale de l'API |
| `POST` | `/api/v1/videos/upload` | **Upload de vidéo** |
| `GET` | `/api/v1/videos/` | Liste toutes les vidéos |
| `GET` | `/api/v1/videos/{video_id}` | Récupère une vidéo spécifique |
| `PUT` | `/api/v1/videos/{video_id}/status` | Met à jour le statut d'une vidéo |
| `GET` | `/api/v1/videos/health` | Santé du service vidéo |
| `GET` | `/api/v1/videos/stats` | Statistiques de stockage |
| `GET` | `/api/v1/status/health` | Santé globale du système |

## 🎬 Upload de vidéo

### Utilisation avec curl
```bash
curl -X POST "http://localhost:8000/api/v1/videos/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@votre_video.mp4;type=video/mp4"
```

### Réponse d'upload réussie
```json
{
  "video_id": "ba21a3fe-fa5f-4d50-a2d4-01bfdc51df34",
  "filename": "votre_video.mp4",
  "file_path": "local_storage/videos/f60e0320-3d76-4920-b50b-11697a88af94.mp4",
  "file_size": 1024000,
  "content_type": "video/mp4",
  "status": "uploaded",
  "upload_time": "2025-11-12T05:20:03.324667",
  "message": "Vidéo 'votre_video.mp4' uploadée avec succès"
}
```

### Types de fichiers supportés
- MP4 (`video/mp4`)
- AVI (`video/avi`)
- MOV (`video/mov`)
- WMV (`video/wmv`)
- FLV (`video/flv`)
- WebM (`video/webm`)
- MKV (`video/mkv`)

### Limitations
- Taille maximale : **500 MB** par fichier
- Le fichier ne peut pas être vide

## 🧪 Tests

### Lancer les tests automatiques
```bash
python3 test_api.py
```

### Test manuel avec curl
```bash
# Créer un fichier de test
echo "fake video content" > test.mp4

# Uploader le fichier
curl -X POST "http://localhost:8000/api/v1/videos/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.mp4;type=video/mp4"

# Vérifier les statistiques
curl -X GET "http://localhost:8000/api/v1/videos/stats"
```

## ⚙️ Configuration

### Variables d'environnement (.env)

| Variable | Description | Défaut |
|----------|-------------|---------|
| `APP_NAME` | Nom de l'application | `VidP Local API` |
| `APP_HOST` | Host du serveur | `0.0.0.0` |
| `APP_PORT` | Port du serveur | `8000` |
| `LOCAL_STORAGE_ROOT` | Racine du stockage | `./local_storage` |
| `LOCAL_VIDEO_PATH` | Dossier des vidéos | `./local_storage/videos` |
| `CORS_ORIGINS` | Origins CORS autorisées | `["http://localhost:3000"]` |

## 💾 MongoDB - Stockage des métadonnées

### Installation de MongoDB

#### Option 1 : Avec Docker Compose (recommandé)
```bash
# Démarrer MongoDB
docker-compose up -d

# Vérifier l'état
docker-compose ps

# Arrêter MongoDB
docker-compose down
```

#### Option 2 : Avec le script fourni
```bash
# Rendre le script exécutable
chmod +x start_mongodb.sh

# Démarrer MongoDB
./start_mongodb.sh
```

#### Option 3 : Installation locale
Suivez la documentation officielle MongoDB : https://docs.mongodb.com/manual/installation/

### Configuration MongoDB

Les variables d'environnement MongoDB sont définies dans `.env` :
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=vidp_db
```

### Endpoints MongoDB

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/videos/` | Liste toutes les vidéos avec métadonnées |
| `GET` | `/api/v1/videos/{video_id}` | Récupère les métadonnées d'une vidéo |
| `PUT` | `/api/v1/videos/{video_id}/status` | Met à jour le statut d'une vidéo |

### Test de l'intégration MongoDB

```bash
# Lancer les tests MongoDB
python3 test_mongodb.py
```

### Exemple d'utilisation

#### Récupérer toutes les vidéos
```bash
curl -X GET "http://localhost:8000/api/v1/videos/"
```

#### Récupérer une vidéo spécifique
```bash
curl -X GET "http://localhost:8000/api/v1/videos/{video_id}"
```

#### Mettre à jour le statut
```bash
curl -X PUT "http://localhost:8000/api/v1/videos/{video_id}/status?new_status=processing"
```

### Métadonnées stockées

Pour chaque vidéo uploadée, MongoDB stocke :
- `video_id` : Identifiant unique
- `original_filename` : Nom du fichier original
- `file_path` : Chemin de stockage local
- `file_size` : Taille en octets
- `content_type` : Type MIME
- `status` : Statut actuel (uploaded, processing, completed, failed)
- `upload_time` : Date et heure d'upload
- `processing_start_time` : Début du traitement (optionnel)
- `processing_end_time` : Fin du traitement (optionnel)
- `error_message` : Message d'erreur (optionnel)

## 🔮 Fonctionnalités futures

### Kubernetes (en préparation)
- Orchestration des jobs de traitement
- Scaling automatique
- Gestion des ressources

## 🛠️ Développement

### Structure modulaire
- **`/api`** : Endpoints REST
- **`/core`** : Configuration et utilitaires
- **`/db`** : Connecteurs base de données
- **`/models`** : Modèles Pydantic
- **`/services`** : Logique métier

### Ajouter un nouvel endpoint
1. Créer la fonction dans `/api/v1/`
2. Définir les modèles dans `/models/`
3. Implémenter la logique dans `/services/`
4. Ajouter les tests correspondants

## 📋 Statuts de retour

| Code | Description |
|------|-------------|
| `200` | Succès |
| `201` | Créé (upload réussi) |
| `400` | Erreur de requête (fichier invalide) |
| `413` | Fichier trop volumineux |
| `500` | Erreur serveur |

## 🚨 Gestion d'erreurs

L'API retourne des erreurs au format JSON :
```json
{
  "error": "Type de fichier non supporté",
  "detail": "video/xyz n'est pas un type MIME accepté",
  "timestamp": "2025-11-12T05:20:03.324667"
}
```

## 🔗 Intégration avec React

### Configuration CORS
Le serveur est configuré pour accepter les requêtes depuis `http://localhost:3000` (port par défaut de React).

### Exemple d'intégration React
```javascript
const uploadVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/v1/videos/upload', {
    method: 'POST',
    body: formData,
  });
  
  return response.json();
};
```

---

**Développé pour le projet VidP - Master 2 DS - INF5141 Cloud Computing**
