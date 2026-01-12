# 🎯 Intégration complète des microservices VidP

## Vue d'ensemble

Ce document décrit l'intégration complète des trois microservices de traitement avec l'application principale `vidp-main-app`.

## 🏗️ Architecture complète

```
┌──────────────────────────────────────────────────────────────────────┐
│                        VidP Main App (Port 8000)                      │
│                     Service d'orchestration principal                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Upload vidéo → Stockage local + MongoDB                          │
│  2. Orchestration des traitements :                                  │
│     ├─> Détection de langue (langscale)                             │
│     ├─> Compression vidéo (downscale)                               │
│     └─> Génération de sous-titres (subtitle)                        │
│  3. Stockage des résultats → MongoDB                                 │
│  4. Récupération des métadonnées complètes                           │
│                                                                       │
└───────┬───────────────────┬───────────────────┬──────────────────────┘
        │                   │                   │
        │ HTTP Upload       │ HTTP Upload       │ HTTP Upload
        ▼                   ▼                   ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  app_langscale    │ │  app_downscale    │ │  app_subtitle     │
│   (Port 8002)     │ │   (Port 8001)     │ │   (Port 8003)     │
├───────────────────┤ ├───────────────────┤ ├───────────────────┤
│ • Détection langue│ │ • Compression     │ │ • Whisper AI      │
│ • Google Speech   │ │ • FFmpeg          │ │ • Génération SRT  │
│ • 15 langues      │ │ • 240p-1080p      │ │ • Multi-langues   │
└───────────────────┘ └───────────────────┘ └───────────────────┘
```

## 🎯 Services intégrés

### 1. **Detection de langue** (`app_langscale`)

**Endpoint** : `POST /api/v1/processing/language-detection`

**Fonctionnalités** :
- Détection automatique de la langue parlée
- Support de 15 langues (FR, EN, ES, DE, IT, PT, RU, JA, ZH, AR, HI, NL, PL, TR, KO)
- Transcription audio via Google Speech Recognition
- Niveau de confiance de la détection

**Requête** :
```json
{
  "video_id": "abc123...",
  "duration": 30,
  "test_all_languages": true
}
```

**Réponse** :
```json
{
  "job_id": "xyz789...",
  "video_id": "abc123...",
  "processing_type": "language_detection",
  "status": "completed",
  "message": "Langue détectée: French (fr-FR)",
  "result": {
    "detected_language": "fr-FR",
    "language_name": "French",
    "confidence": 0.95,
    "processing_time": 12.34
  }
}
```

### 2. **Compression vidéo** (`app_downscale`)

**Endpoint** : `POST /api/v1/processing/compression`

**Fonctionnalités** :
- Compression multi-résolution (240p, 360p, 480p, 720p, 1080p)
- Contrôle de qualité via CRF (18-30)
- Réduction de taille moyenne : 60-80%
- FFmpeg & MoviePy

**Requête** :
```json
{
  "video_id": "abc123...",
  "resolution": "360p",
  "crf_value": 28,
  "custom_filename": "my_compressed_video"
}
```

**Réponse** :
```json
{
  "job_id": "comp789...",
  "video_id": "abc123...",
  "processing_type": "compression",
  "status": "completed",
  "message": "Compression en résolution 360p",
  "result": {
    "resolution": "360p",
    "metadata": {
      "original_size": "50.5 MB",
      "compressed_size": "15.2 MB",
      "compression_ratio": "69.9%"
    }
  }
}
```

### 3. **Génération de sous-titres** (`app_subtitle`)

**Endpoint** : `POST /api/v1/processing/subtitles`

**Fonctionnalités** :
- Transcription automatique via Whisper AI (OpenAI)
- Plusieurs modèles (tiny, base, small, medium, large)
- Export SRT standardisé
- Support multi-langues

**Requête** :
```json
{
  "video_id": "abc123...",
  "model_name": "base",
  "language": "fr"
}
```

**Réponse** :
```json
{
  "job_id": "sub456...",
  "video_id": "abc123...",
  "processing_type": "subtitle_generation",
  "status": "completed",
  "message": "Sous-titres générés avec le modèle base",
  "result": {
    "model_name": "base",
    "language": "fr",
    "subtitle_text": "Transcription complète de la vidéo..."
  }
}
```

## 📡 Endpoints disponibles

### Upload et gestion des vidéos

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/videos/upload` | Upload une vidéo |
| `GET` | `/api/v1/videos/{video_id}` | Récupère les métadonnées |
| `GET` | `/api/v1/videos/` | Liste toutes les vidéos |
| `GET` | `/api/v1/videos/stream/{video_id}` | Streamer une vidéo |

### Traitements vidéo

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/processing/language-detection` | Détection de langue |
| `GET` | `/api/v1/processing/language-detection/{video_id}` | Résultat détection |
| `POST` | `/api/v1/processing/compression` | Compression vidéo |
| `GET` | `/api/v1/processing/compression/{video_id}` | Résultat compression |
| `POST` | `/api/v1/processing/subtitles` | Génération sous-titres |
| `GET` | `/api/v1/processing/subtitles/{video_id}` | Résultat sous-titres |
| `GET` | `/api/v1/processing/supported-languages` | Langues supportées |
| `GET` | `/api/v1/processing/health` | Santé des microservices |

### Statut et santé

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Santé globale de l'API |
| `GET` | `/api/v1/status/health` | Statut détaillé |
| `GET` | `/api/v1/videos/health` | Santé service vidéo |
| `GET` | `/api/v1/processing/health` | Santé des microservices |

## 🔄 Workflow complet

### Scénario 1 : Traitement complet d'une vidéo

```bash
# 1. Upload de la vidéo
VIDEO_RESPONSE=$(curl -X POST "http://localhost:8000/api/v1/videos/upload" \
  -F "file=@video.mp4")

VIDEO_ID=$(echo $VIDEO_RESPONSE | jq -r '.video_id')
echo "Video ID: $VIDEO_ID"

# 2. Détection de langue
curl -X POST "http://localhost:8000/api/v1/processing/language-detection" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_id\": \"$VIDEO_ID\",
    \"duration\": 30,
    \"test_all_languages\": true
  }"

# 3. Compression en 360p
curl -X POST "http://localhost:8000/api/v1/processing/compression" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_id\": \"$VIDEO_ID\",
    \"resolution\": \"360p\",
    \"crf_value\": 28
  }"

# 4. Génération de sous-titres
curl -X POST "http://localhost:8000/api/v1/processing/subtitles" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_id\": \"$VIDEO_ID\",
    \"model_name\": \"base\",
    \"language\": \"fr\"
  }"

# 5. Récupération des résultats
curl "http://localhost:8000/api/v1/processing/language-detection/$VIDEO_ID"
curl "http://localhost:8000/api/v1/processing/compression/$VIDEO_ID"
curl "http://localhost:8000/api/v1/processing/subtitles/$VIDEO_ID"
```

### Scénario 2 : Vérification de la santé des services

```bash
# Vérifier tous les microservices
curl "http://localhost:8000/api/v1/processing/health"
```

**Réponse** :
```json
{
  "status": "healthy",
  "services": {
    "language_detection": {
      "url": "http://localhost:8002",
      "status": "up"
    },
    "compression": {
      "url": "http://localhost:8001",
      "status": "up"
    },
    "subtitle_generation": {
      "url": "http://localhost:8003",
      "status": "up"
    }
  }
}
```

## 🚀 Démarrage des services

### Développement local

```bash
# Terminal 1 : MongoDB
docker-compose up -d mongodb

# Terminal 2 : app_langscale (détection de langue)
cd app_langscale
python main.py

# Terminal 3 : app_downscale (compression)
cd app_downscale
python main.py

# Terminal 4 : app_subtitle (sous-titres)
cd app_subtitle
python main.py

# Terminal 5 : vidp-main-app (orchestrateur)
cd vidp-main-app/vidp-fastapi-service
python main.py
```

### Production Kubernetes

```bash
# Créer le namespace
kubectl create namespace vidp-production

# Déployer tous les services
kubectl apply -f k8s/
```

**Fichier `k8s/vidp-services.yaml`** :
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vidp-microservices-config
  namespace: vidp-production
data:
  LANGSCALE_SERVICE_URL: "http://langscale-service:8002"
  DOWNSCALE_SERVICE_URL: "http://downscale-service:8001"
  SUBTITLE_SERVICE_URL: "http://subtitle-service:8003"
  MICROSERVICES_TIMEOUT: "300"
```

## 📊 Architecture MongoDB

### Collections

#### 1. `video_metadata`
Métadonnées des vidéos uploadées :
```json
{
  "video_id": "abc123",
  "original_filename": "video.mp4",
  "file_path": "local_storage/videos/abc123.mp4",
  "file_size": 52428800,
  "content_type": "video/mp4",
  "status": "uploaded",
  "upload_time": "2026-01-02T10:00:00"
}
```

#### 2. `processing_results`
Résultats des traitements :
```json
{
  "video_id": "abc123",
  "processing_type": "language_detection",
  "result": {
    "job_id": "lang456",
    "detected_language": "fr-FR",
    "language_name": "French",
    "confidence": 0.95
  },
  "updated_at": "2026-01-02T10:05:00"
}
```

### Requêtes utiles

```javascript
// Récupérer tous les traitements d'une vidéo
db.processing_results.find({"video_id": "abc123"})

// Compter les vidéos par langue détectée
db.processing_results.aggregate([
  {$match: {"processing_type": "language_detection"}},
  {$group: {
    _id: "$result.language_name",
    count: {$sum: 1}
  }}
])
```

## 🔒 Sécurité et bonnes pratiques

### 1. Validation des entrées
✅ Toutes les requêtes sont validées avec Pydantic  
✅ Vérification des formats de fichiers  
✅ Limites de taille d'upload  

### 2. Gestion des erreurs
✅ Codes HTTP appropriés (404, 500, 503)  
✅ Messages d'erreur détaillés  
✅ Logging centralisé  

### 3. Performance
✅ Timeout configurables par service  
✅ Upload en streaming pour économiser la mémoire  
✅ Nettoyage automatique des fichiers temporaires  

### 4. Monitoring
✅ Health checks pour chaque service  
✅ Logs détaillés avec timestamps  
✅ Métriques de performance (temps de traitement)  

## 📈 Performance et temps de traitement

### Estimations (vidéo 1 minute, Full HD)

| Service | Opération | Temps moyen |
|---------|-----------|-------------|
| **langscale** | Détection langue (30s audio) | ~10-15s |
| **downscale** | Compression 1080p → 360p | ~20-30s |
| **subtitle** | Génération sous-titres (base) | ~30-45s |

**Total pour traitement complet** : ~60-90 secondes

### Optimisations possibles

1. **Traitement parallèle** : Lancer détection langue + sous-titres simultanément
2. **Cache** : Stocker les résultats pour éviter retraitement
3. **Queue système** : Utiliser Celery ou RabbitMQ pour jobs asynchrones

## 🐛 Dépannage

### Service non accessible

```bash
# Vérifier les services
curl http://localhost:8000/api/v1/processing/health

# Redémarrer un service
pkill -f "app_langscale"
cd app_langscale && python main.py
```

### MongoDB non disponible

```bash
# Vérifier MongoDB
docker ps | grep mongodb

# Redémarrer MongoDB
docker-compose restart mongodb
```

### Upload échoue

```bash
# Vérifier les logs
tail -f vidp-fastapi-service/vidp_api.log

# Vérifier l'espace disque
df -h
```

## 📚 Documentation détaillée

- **Architecture Kubernetes** : [`KUBERNETES_ARCHITECTURE.md`](KUBERNETES_ARCHITECTURE.md)
- **Intégration détection langue** : [`LANGUAGE_DETECTION_INTEGRATION.md`](LANGUAGE_DETECTION_INTEGRATION.md)
- **API Interactive** : http://localhost:8000/docs

## 🎯 Prochaines étapes

- [ ] Ajout d'authentification (JWT)
- [ ] Système de webhooks pour notifications
- [ ] Interface web complète (React/Next.js)
- [ ] Pipeline de traitement automatique
- [ ] Support de traitement batch
- [ ] Métriques Prometheus + Grafana
- [ ] Distributed tracing (Jaeger)

## ✅ Checklist de déploiement

### Développement
- [x] MongoDB local
- [x] Tous les microservices démarrés
- [x] Tests des endpoints
- [x] Documentation à jour

### Production
- [ ] Variables d'environnement sécurisées
- [ ] HTTPS avec certificats SSL
- [ ] Reverse proxy (Nginx/Traefik)
- [ ] Monitoring et alerting
- [ ] Sauvegardes MongoDB automatiques
- [ ] Limitation de débit (rate limiting)
- [ ] Logs centralisés (ELK Stack)

---

**Version** : 2.0.0  
**Date** : 2 Janvier 2026  
**Auteur** : VidP Team  
**Status** : ✅ Intégration complète des 3 microservices
