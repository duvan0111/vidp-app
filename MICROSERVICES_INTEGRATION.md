# 🎯 Intégration complète des microservices VidP

## Vue d'ensemble

Ce document décrit l'intégration et le flux de communication entre les différents microservices de traitement vidéo et l'application principale `vidp-main-app`, qui agit comme orchestrateur central. L'architecture est conçue pour être modulaire et évolutive, indépendamment de la plateforme d'orchestration (comme Kubernetes).

## 🏗️ Architecture des Microservices VidP

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  VidP Main App (Orchestrateur)                                  │
│                 Manages workflow, data persistence (MongoDB), and external API                 │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                │
│  1. Upload Vidéo (via API) → Stockage temporaire + Métadonnées MongoDB                         │
│  2. Orchestration des traitements (chaque étape reçoit la vidéo via HTTP POST) :               │
│     ├─> Étape 1: Détection de langue (app_langscale)                                           │
│     ├─> Étape 2: Compression vidéo (app_downscale)                                             │
│     ├─> Étape 3: Génération de sous-titres (app_subtitle)                                      │
│     ├─> Étape 4: Détection d'animaux (app_animal_detect)                                       │
│     └─> Étape 5: Agrégation vidéo (service d'agrégation cloud-hosted)                          │
│  3. Stockage des résultats de chaque étape → MongoDB                                            │
│  4. Récupération des métadonnées complètes et streaming de la vidéo finale                     │
│                                                                                                │
└─────────┬───────────────┬────────────────┬────────────────┬─────────────────┬──────────────────┘
          │               │                │                │                 │
          │ HTTP Upload   │ HTTP Upload    │ HTTP Upload    │ HTTP Upload     │ HTTP Upload
          ▼               ▼                ▼                ▼                 ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  app_langscale    │ │  app_downscale    │ │  app_subtitle     │ │  app_animal_detect│ │  Aggregation      │
│   (Port 8002)     │ │   (Port 8001)     │ │   (Port 8003)     │ │   (Port 8004)     │ │   (Cloud-hosted)  │
├───────────────────┤ ├───────────────────┤ ├───────────────────┤ ├───────────────────┤ ├───────────────────┤
│ • Détection langue│ │ • Compression     │ │ • Whisper AI      │ │ • YOLOv8          │ │ • Burn Subtitles  │
│ • Google Speech   │ │ • FFmpeg          │ │ • Génération SRT  │ │ • Animal Detection│ │ • Combine Streams │
│ • 15 langues      │ │ • 240p-1080p      │ │ • Multi-langues   │ │ • Image/Video     │ │ • Final Output    │
└───────────────────┘ └───────────────────┘ └───────────────────┘ └───────────────────┘ └───────────────────┘
```

## 🎯 Services intégrés

Le `vidp-main-app` orchestre les flux de traitement en communiquant avec les microservices suivants via des requêtes HTTP (généralement des uploads de fichiers).

### 1. **Détection de langue** (`app_langscale`)

**Rôle** : Détecte la langue parlée dans la piste audio d'une vidéo.
**Endpoint principal** : `POST /api/detect/upload`
**Fonctionnalités** :
-   Détection automatique de la langue parlée (plus de 15 langues).
-   Utilisation de la reconnaissance vocale pour l'analyse.
-   Retourne la langue détectée avec un niveau de confiance.

**Exemple de Requête (`vidp-main-app` vers `app_langscale`)** :
```python
# Fichier vidéo envoyé via HTTP multipart/form-data
response = await client.post(
    f"{settings.langscale_service_url}/api/detect/upload",
    files={'file': ('video.mp4', video_data, 'video/mp4')},
    data={'duration': '30', 'test_all_languages': 'true'}
)
```
**Exemple de Réponse** :
```json
{
  "status": "completed",
  "detected_language": "fr",
  "language_name": "French",
  "confidence": 0.98
}
```

### 2. **Compression vidéo** (`app_downscale`)

**Rôle** : Compresse les vidéos à différentes résolutions et niveaux de qualité.
**Endpoint principal** : `POST /api/compress/upload`
**Fonctionnalités** :
-   Compression multi-résolution (240p, 360p, 480p, 720p, 1080p).
-   Contrôle de qualité via CRF (Constant Rate Factor).
-   Réduit significativement la taille des fichiers vidéo.

**Exemple de Requête (`vidp-main-app` vers `app_downscale`)** :
```python
# Fichier vidéo envoyé via HTTP multipart/form-data
response = await client.post(
    f"{settings.downscale_service_url}/api/compress/upload",
    files={'file': ('video.mp4', video_data, 'video/mp4')},
    data={'resolution': '720p', 'crf_value': '23'}
)
```
**Exemple de Réponse** :
```json
{
  "status": "completed",
  "output_path": "/path/to/compressed_video.mp4",
  "metadata": {"original_size": "100MB", "final_size_mb": 25.0}
}
```

### 3. **Génération de sous-titres** (`app_subtitle`)

**Rôle** : Génère automatiquement des sous-titres (SRT) à partir de la piste audio d'une vidéo.
**Endpoint principal** : `POST /api/generate-subtitles/`
**Fonctionnalités** :
-   Transcription audio vers texte via Whisper AI (OpenAI).
-   Support de plusieurs modèles Whisper (tiny, base, small, medium, large).
-   Génère des fichiers SRT standardisés.

**Exemple de Requête (`vidp-main-app` vers `app_subtitle`)** :
```python
# Fichier vidéo envoyé via HTTP multipart/form-data
response = await client.post(
    f"{settings.subtitle_service_url}/api/generate-subtitles/",
    files={'video': ('video.mp4', video_data, 'video/mp4')},
    data={'model_name': 'base', 'language': 'fr'}
)
```
**Exemple de Réponse** :
```json
{
  "status": "success",
  "srt_url": "http://subtitle-service:8003/api/download-subtitles/subtitles_xyz.srt",
  "full_text": "Transcription complète..."
}
```

### 4. **Détection d'animaux** (`app_animal_detect`)

**Rôle** : Détecte et identifie des animaux (et autres objets) dans des vidéos ou des images.
**Endpoint principal** : `POST /detect`
**Fonctionnalités** :
-   Utilise le modèle YOLOv8 pour la détection en temps réel.
-   Capable de détecter un large éventail d'espèces animales (basé sur le dataset COCO).
-   Fournit des informations sur les objets détectés par image ou par vidéo.

**Exemple de Requête (`vidp-main-app` vers `app_animal_detect`)** :
```python
# Fichier vidéo envoyé via HTTP multipart/form-data
response = await client.post(
    f"{settings.animal_detection_service_url}/detect",
    files={'file': ('video.mp4', video_data, 'video/mp4')},
    params={'confidence_threshold': 0.5, 'save_video': 'true'}
)
```
**Exemple de Réponse** :
```json
{
  "status": "completed",
  "video_info": {"duration_seconds": 60, ...},
  "detection_summary": {"animals_detected": {"dog": 5, "cat": 2}, ...},
  "output_video": "base64_encoded_image_or_url"
}
```

### 5. **Service d'agrégation vidéo** (`Aggregation Service`)

**Rôle** : Combine la vidéo traitée avec les sous-titres générés (et d'autres métadonnées) pour produire une vidéo finale avec incrustation des sous-titres ("burned-in subtitles"). Ce service est hébergé dans le cloud et est le dernier point du pipeline de traitement.
**Endpoint principal** : `POST /api/process-video/`
**Fonctionnalités** :
-   Incrustation de sous-titres SRT dans la vidéo.
-   Peut combiner différentes sorties des autres microservices (vidéo compressée, sous-titres, informations de détection d'animaux, langue détectée).
-   Génère une URL de streaming pour la vidéo finale.

**Exemple de Requête (`vidp-main-app` vers `Aggregation Service`)** :
```python
# Fichiers vidéo et SRT envoyés via HTTP multipart/form-data
response = await client.post(
    f"{settings.aggregation_service_url}/api/process-video/",
    files={
        'video': ('compressed_video.mp4', compressed_video_data, 'video/mp4'),
        'srt_file': ('subtitles.srt', srt_data, 'text/plain')
    },
    data={
        'resolution': '720p',
        'crf_value': '23',
        'detected_language': 'fr',
        'animals_detected': '{"dog": 5}'
    }
)
```
**Exemple de Réponse** :
```json
{
  "status": "completed",
  "video_id": "agg_xyz",
  "streaming_url": "http://cloud-storage/agg_video.mp4",
  "message": "Agrégation terminée"
}
```

## 📡 Endpoints d'orchestration (`vidp-main-app`)

Le `vidp-main-app` expose des endpoints pour l'upload initial et pour lancer le **workflow global de traitement**.

### Upload et gestion des vidéos initiales

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/videos/upload` | Upload une vidéo initiale à `vidp-main-app` |
| `GET` | `/api/v1/videos/{video_id}` | Récupère les métadonnées d'une vidéo |
| `GET` | `/api/v1/videos/` | Liste toutes les vidéos |
| `GET` | `/api/v1/videos/stream/{video_id}` | Streamer une vidéo brute (avant traitement) |

### Orchestration des traitements (Endpoints du `vidp-main-app`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/processing/process-video` | **Lance le workflow global de traitement** (détection langue, compression, sous-titres, détection animaux, agrégation) |
| `GET` | `/api/v1/processing/process-video/{video_id}` | Récupère les résultats du workflow global pour une vidéo |
| `GET` | `/api/v1/processing/language-detection/{video_id}` | Résultat détection langue |
| `GET` | `/api/v1/processing/compression/{video_id}` | Résultat compression vidéo |
| `GET` | `/api/v1/processing/subtitles/{video_id}` | Résultat génération sous-titres |
| `GET` | `/api/v1/processing/animal-detection/{video_id}` | Résultat détection d'animaux |
| `GET` | `/api/v1/processing/supported-languages` | Langues supportées par `app_langscale` |
| `GET` | `/api/v1/processing/health` | Santé de tous les microservices |

### Statut et santé globaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Santé globale de l'API `vidp-main-app` |
| `GET` | `/api/v1/status/health` | Statut détaillé de `vidp-main-app` |

## 🔄 Workflow de traitement complet (via `/api/v1/processing/process-video`)

Ce workflow est orchestré par le `vidp-main-app` et enchaîne les appels aux microservices. Chaque étape utilise la vidéo traitée de l'étape précédente ou l'originale si pas de modification.

```mermaid
graph TD
    A[Client Uploads Video] --> B(vidp-main-app: /api/v1/videos/upload)
    B --> C{Save Video to Local Temp Storage<br>+ Record Metadata in MongoDB}
    C --> D(vidp-main-app: /api/v1/processing/process-video)
    D --> E{Check Audio Track}
    E -- Has Audio --> F(Call app_langscale: Language Detection)
    E -- No Audio --> F_SKIP[Skip Language Detection]
    F --> G(Record Language Detection Result in MongoDB)
    F_SKIP --> G

    G --> H(Call app_downscale: Video Compression)
    H --> I(Record Compression Result in MongoDB)

    I --> J{Check Audio Track}
    J -- Has Audio --> K(Call app_subtitle: Subtitle Generation)
    J -- No Audio --> K_SKIP[Skip Subtitle Generation<br>(Generate empty SRT)]
    K --> L(Record Subtitle Result in MongoDB)
    K_SKIP --> L

    L --> M(Call app_animal_detect: Animal Detection)
    M --> N(Record Animal Detection Result in MongoDB)

    N --> O(Call Aggregation Service: Final Video Processing)
    O --> P(Record Aggregation Result in MongoDB<br>+ Get Final Streaming URL)
    P --> Q[Return Global Processing Result to Client]
```

## 🚀 Démarrage des services (Développement local)

Pour lancer tous les microservices en développement local :

```bash
# S'assurer que MongoDB est démarré (ex: via Docker)
docker-compose up -d mongodb

# Utiliser le script de démarrage global du projet
./start_all_services.sh
```

## 📊 Architecture MongoDB

### Collections gérées par `vidp-main-app`

#### 1. `video_metadata`
Stocke les métadonnées initiales de chaque vidéo uploadée, ainsi que les statuts de traitement globaux.

**Exemple** :
```json
{
  "video_id": "abc123",
  "original_filename": "video.mp4",
  "file_path": "/app/local_storage/videos/abc123.mp4",
  "file_size": 52428800,
  "content_type": "video/mp4",
  "status": "processing",
  "upload_time": "2026-01-02T10:00:00",
  "current_stage": "animal_detection",
  "stages_completed": ["language_detection", "compression", "subtitle_generation"],
  "stages_failed": []
}
```

#### 2. `processing_results`
Stocke les résultats détaillés de chaque étape de traitement (langue, compression, sous-titres, détection animale, agrégation) pour chaque `video_id`.

**Exemple (Détection de langue)** :
```json
{
  "video_id": "abc123",
  "processing_type": "language_detection",
  "result": {
    "job_id": "lang456",
    "detected_language": "fr",
    "language_name": "French",
    "confidence": 0.98,
    "processing_time": 12.34
  },
  "updated_at": "2026-01-02T10:05:00"
}
```

## 🔒 Sécurité et bonnes pratiques

### 1. Validation des entrées
✅ Toutes les requêtes API sont validées avec Pydantic.
✅ Vérification des formats et tailles de fichiers uploadés.

### 2. Gestion des erreurs
✅ Utilisation de codes HTTP appropriés (400, 404, 500, 503).
✅ Messages d'erreur détaillés pour faciliter le débogage.

### 3. Performance
✅ Timeouts configurables pour les appels inter-microservices.
✅ Gestion des fichiers en streaming ou temporaires pour optimiser la mémoire.

### 4. Monitoring et Observabilité
✅ Chaque microservice expose un endpoint `/health`.
✅ Logs détaillés avec timestamps pour le débogage et l'audit.

## 📈 Performance et temps de traitement

### Estimations (vidéo 1 minute, Full HD)

| Service | Opération | Temps moyen |
|---------|-----------|-------------|
| **app_langscale** | Détection langue (30s audio) | ~10-15s |
| **app_downscale** | Compression 1080p → 360p | ~20-30s |
| **app_subtitle** | Génération sous-titres (base) | ~30-45s |
| **app_animal_detect** | Détection d'animaux (YOLOv8n) | ~20-60s |
| **Aggregation Service** | Incrustation sous-titres | ~10-20s |

**Total pour traitement complet** : ~90-170 secondes (variable selon le contenu vidéo et les modèles)

### Optimisations possibles

1.  **Traitement parallèle** : Exécuter des étapes indépendantes (ex: détection langue et détection d'animaux) en parallèle.
2.  **Cache** : Mettre en cache les résultats de traitement pour éviter des recalculs.
3.  **Système de files d'attente** : Utiliser des systèmes comme Celery ou RabbitMQ pour gérer des jobs asynchrones et des traitements en arrière-plan.

## 🐛 Dépannage

### Service non accessible

```bash
# Vérifier l'état de tous les services via l'orchestrateur
curl http://localhost:8000/api/v1/processing/health

# Redémarrer un service spécifique (exemple pour app_langscale)
pkill -f "app_langscale"
cd app_langscale && python main.py # Ou via Docker/Kubernetes si déployé ainsi
```

---

**Version** : 2.0  
**Date** : 23 Janvier 2026  
**Auteur** : VidP Team