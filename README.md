# 🎬 VidP - Plateforme de Traitement Vidéo Distribuée

**VidP** est une plateforme de traitement vidéo basée sur une architecture microservices, conçue pour le déploiement sur Kubernetes. Le système permet la détection de langue, la détection d'animaux, la compression vidéo et la génération de sous-titres via une API REST unifiée.

## 📋 Vue d'Ensemble

### Architecture Microservices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         vidp-main-app (Port 8000)                           │
│              Service Principal d'Orchestration & API Gateway                │
│                           MongoDB Integration                               │
└─────────┬───────────────┬───────────────┬───────────────┬───────────────────┘
          │               │               │               │
  ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────────────┐
  │app_langscale │ │app_downscale│ │ app_subtitle│ │ app_animal_detect  │
  │  Port 8002   │ │  Port 8001  │ │  Port 8003  │ │     Port 8004      │
  │ ──────────── │ │ ─────────── │ │ ─────────── │ │ ────────────────── │
  │ • Détection  │ │ • Compress° │ │ • Génération│ │ • Détection YOLO   │
  │   langue     │ │   vidéo     │ │   sous-tit. │ │   animaux/objets   │
  │ • 15 langues │ │ • 240p-1080p│ │ • Whisper   │ │ • Tracking vidéo   │
  │ • Async/Sync │ │ • CRF 18-30 │ │ • SRT, VTT  │ │ • Annotations      │
  └──────────────┘ └─────────────┘ └─────────────┘ └────────────────────┘
```

---

## ☸️ Déploiement Kubernetes (Minikube)

### Prérequis Kubernetes

- **Minikube** 1.30+
- **kubectl** 1.28+
- **Docker** 20+

### Déploiement rapide

```bash
# Déploiement complet en une commande
./deploy-minikube.sh all

# Ou avec Make
make all
```

### Commandes principales

```bash
# Démarrer Minikube
./deploy-minikube.sh start

# Construire les images Docker
./deploy-minikube.sh build

# Déployer sur Kubernetes
./deploy-minikube.sh deploy

# Accéder aux services
./deploy-minikube.sh forward
# → Frontend: http://localhost:3000
# → API: http://localhost:8000

# Voir les logs
./deploy-minikube.sh logs main-app

# Statut du cluster
./deploy-minikube.sh status

# Supprimer le déploiement
./deploy-minikube.sh delete
```

### Architecture K8s

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes (Minikube)                     │
│                      Namespace: vidp                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────────────────────────┐    │
│  │  Frontend   │────▶│        Main App (Gateway)       │    │
│  │  NodePort   │     │         NodePort 30080          │    │
│  │   30030     │     └───────────────┬─────────────────┘    │
│  └─────────────┘                     │                      │
│                                      │                      │
│         ┌───────────┬────────────────┼────────────┬─────┐   │
│         │           │                │            │     │   │
│    ┌────▼───┐ ┌─────▼────┐ ┌────────▼────┐ ┌─────▼───┐ │   │
│    │MongoDB │ │Langscale │ │  Downscale  │ │Subtitle │ │   │
│    │ :27017 │ │  :8002   │ │   :8001     │ │  :8003  │ │   │
│    └────────┘ └──────────┘ └─────────────┘ └─────────┘ │   │
│                                                         │   │
│                                            ┌────────────▼┐  │
│                                            │Animal Detect│  │
│                                            │    :8004    │  │
│                                            └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

📖 **Documentation complète** : [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md)

---

## 🚀 Démarrage Rapide

### Prérequis

- **Python** 3.8+ 
- **MongoDB** 4.4+
- **FFmpeg** 4.4+
- **Ports libres** : 8000, 8001, 8002, 8003, 8004

### Installation en 3 étapes

```bash
# 1. Cloner le projet (si nécessaire)
cd /path/to/vidp-app

# 2. Installer les dépendances de tous les services
for service in vidp-main-app/vidp-fastapi-service app_langscale app_downscale app_subtitle app_animal_detect; do
    cd $service && pip install -r requirements.txt && cd -
done

# 3. Démarrer tous les services
./start_all_services.sh
```

### Vérification

```bash
# Health check global
curl http://localhost:8000/api/v1/processing/health | jq

# Résultat attendu :
# {
#   "status": "healthy",
#   "services": {
#     "language_detection": {"status": "up"},
#     "compression": {"status": "up"},
#     "subtitle_generation": {"status": "up"},
#     "animal_detection": {"status": "up"}
#   }
# }
```

---

## 📚 Documentation

### Guides Principaux

| Document | Description |
|----------|-------------|
| [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md) | ☸️ **Déploiement Minikube** |
| [START_SERVICES.md](START_SERVICES.md) | 🚀 Guide de démarrage local |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | 🧪 Tests et validation |
| [MICROSERVICES_INTEGRATION.md](vidp-main-app/MICROSERVICES_INTEGRATION.md) | 🔧 Intégration des microservices |

### Documentation API

- **API Principale** : http://localhost:8000/docs
- **Langscale API** : http://localhost:8002/docs
- **Downscale API** : http://localhost:8001/docs
- **Subtitle API** : http://localhost:8003/docs
- **Animal Detect API** : http://localhost:8004/docs

---

## 🎯 Exemples d'Utilisation

### 1. Détection de Langue

```bash
# Upload et détection synchrone
curl -X POST "http://localhost:8000/api/v1/processing/language-detection" \
  -F "video_file=@video.mp4" \
  -F "async_processing=false" \
  -F "duration=30" | jq
```

**Réponse** :
```json
{
  "video_id": "abc123",
  "status": "completed",
  "result": {
    "language": "fr-FR",
    "confidence": 0.95,
    "display": "Français"
  }
}
```

### 2. Compression Vidéo

```bash
# Compression en 720p, qualité CRF 23
curl -X POST "http://localhost:8000/api/v1/processing/compression" \
  -F "video_file=@video.mp4" \
  -F "target_resolution=720p" \
  -F "crf=23" | jq
```

**Réponse** :
```json
{
  "video_id": "def456",
  "job_id": "compression-job-123",
  "status": "processing",
  "processing_type": "compression"
}
```

### 3. Génération de Sous-titres

```bash
# Génération avec Whisper (modèle tiny)
curl -X POST "http://localhost:8000/api/v1/processing/subtitles" \
  -F "video_file=@video.mp4" \
  -F "model_size=tiny" \
  -F "language=auto" | jq
```

**Réponse** :
```json
{
  "video_id": "ghi789",
  "status": "completed",
  "result": {
    "subtitle_text": "1\n00:00:00,000 --> 00:00:03,000\nBonjour...",
    "detected_language": "fr",
    "duration": 120.5
  }
}
```

---

## 🛠️ Gestion des Services

### Démarrer les Services

```bash
./start_all_services.sh
```

### Arrêter les Services

```bash
./stop_all_services.sh
```

### Redémarrer un Service Spécifique

```bash
# Exemple : Redémarrer app_langscale
lsof -ti:8002 | xargs kill -9
cd app_langscale
uvicorn main:app --host 127.0.0.1 --port 8002 &
```

### Voir les Logs

```bash
# Tous les logs en temps réel
tail -f app_langscale/langscale.log \
         app_downscale/downscale.log \
         app_subtitle/subtitle.log \
         vidp-main-app/vidp-fastapi-service/main.log
```

---

## 🏗️ Structure du Projet

```
vidp-app/
├── start_all_services.sh          # Script de démarrage
├── stop_all_services.sh           # Script d'arrêt
├── test_integration.py            # Tests d'intégration Python
├── test_quick.sh                  # Tests rapides Bash
├── START_SERVICES.md              # Guide de démarrage
├── TESTING_GUIDE.md               # Guide de test
├── README.md                      # Ce fichier
│
├── vidp-main-app/                 # Service principal
│   ├── vidp-fastapi-service/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── .env
│   │   └── app/
│   │       ├── api/v1/            # Endpoints API
│   │       ├── services/          # Clients microservices
│   │       ├── models/            # Modèles Pydantic
│   │       └── db/                # Connexion MongoDB
│   ├── MICROSERVICES_INTEGRATION.md
│   ├── KUBERNETES_ARCHITECTURE.md
│   └── README.md
│
├── app_langscale/                 # Détection de langue
│   ├── main.py
│   ├── api/endpoints.py
│   ├── services/detector_service.py
│   └── README.md
│
├── app_downscale/                 # Compression vidéo
│   ├── main.py
│   ├── routes/compression_routes.py
│   ├── services/video_downscaler.py
│   └── README.md
│
└── app_subtitle/                  # Génération de sous-titres
    ├── main.py
    ├── routes/subtitle_routes.py
    ├── services/subtitle_service.py
    └── README.md
```

---

## 🔧 Configuration

### Variables d'Environnement

Fichier `.env` dans `vidp-main-app/vidp-fastapi-service/` :

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=vidp_database

# Microservices
LANGSCALE_SERVICE_URL=http://localhost:8002
DOWNSCALE_SERVICE_URL=http://localhost:8001
SUBTITLE_SERVICE_URL=http://localhost:8003
MICROSERVICES_TIMEOUT=300

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## ☸️ Déploiement Kubernetes

Pour déployer sur Kubernetes, suivre le guide détaillé :

```bash
# Voir KUBERNETES_ARCHITECTURE.md
cat vidp-main-app/KUBERNETES_ARCHITECTURE.md
```

**Composants K8s inclus** :
- Deployments (4 services)
- Services (ClusterIP + LoadBalancer)
- ConfigMaps (configuration)
- Secrets (credentials)
- Ingress (routing)
- HPA (auto-scaling)
- Persistent Volumes (MongoDB)

---

## 🧪 Tests

### Tests Automatisés

```bash
# Tests Python complets
python3 test_integration.py

# Tests Bash rapides
./test_quick.sh
```

### Tests Manuels

Voir [TESTING_GUIDE.md](TESTING_GUIDE.md) pour des exemples détaillés.

---

## 🤝 Contribution

### Workflow de Développement

1. **Créer une branche** : `git checkout -b feature/ma-feature`
2. **Développer** : Modifier le code
3. **Tester** : `./test_quick.sh`
4. **Commit** : `git commit -m "feat: ajout de ma fonctionnalité"`
5. **Push** : `git push origin feature/ma-feature`

### Standards de Code

- **Python** : PEP 8, type hints
- **API** : RESTful, OpenAPI 3.0
- **Commits** : Conventional Commits

---

## 📊 Performances

| Opération | Temps Moyen | Notes |
|-----------|-------------|-------|
| Détection langue | 10-30s | Dépend de la durée audio |
| Compression 720p | 30-120s | Dépend de la taille vidéo |
| Sous-titres (tiny) | 60-300s | Modèle Whisper tiny |
| Sous-titres (base) | 120-600s | Modèle Whisper base |

---

## 🛡️ Sécurité

- ✅ Authentification JWT
- ✅ Validation des uploads (taille, format)
- ✅ Sanitization des inputs
- ✅ CORS configuré
- ⚠️ HTTPS recommandé en production
- ⚠️ Secrets à configurer via K8s Secrets

---

## 📝 License

Ce projet est développé dans le cadre du cours **INF5141 Cloud Computing** à l'Université de Technologie de Compiègne (UTC).

---

## 👥 Équipe VidP

**Master 2 Data Science - UTC**  
**Projet Cloud Computing - Janvier 2025**

---

## 🔗 Liens Utiles

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Whisper AI](https://github.com/openai/whisper)

---

**Version** : 1.0.0  
**Dernière mise à jour** : 3 janvier 2025
