# 🎬 VidP - Plateforme de Traitement Vidéo Distribuée

**VidP** est une plateforme de traitement vidéo basée sur une architecture microservices, conçue pour le déploiement sur Kubernetes. Le système permet la détection de langue, la détection d'animaux, la compression vidéo et la génération de sous-titres via une API REST unifiée.

## 📦 Démarrage

Pour commencer avec VidP, clonez le dépôt GitHub :

```bash
git clone https://github.com/duvan0111/vidp-app.git
cd vidp-app
```

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

## 🚀 Déploiement VidP sur Minikube

Ce guide fournit des instructions pour déployer l'application VidP sur Minikube, avec des sections spécifiques pour les environnements Linux/macOS (Bash) et Windows (PowerShell).

### Prérequis Généraux

- **Minikube** 1.30+
- **kubectl** 1.28+
- **Docker** 20+ (en cours d'exécution)
- Au moins **8 GB de RAM** disponible pour Minikube
- Au moins **4 CPUs** disponibles pour Minikube
- **20 GB d'espace disque** pour Minikube

---


### Déploiement sur Linux/macOS (Bash)

Ce guide utilise le script `deploy-minikube.sh`.

#### Démarrage rapide

```bash
# Déploiement complet en une commande
./deploy-minikube.sh all
```
Cette commande démarre Minikube, construit toutes les images Docker et déploie les services sur Kubernetes.

#### Commandes principales

| Commande | Description |
|----------|-------------|
| `./deploy-minikube.sh start` | Démarrer Minikube |
| `./deploy-minikube.sh build` | Construire toutes les images Docker |
| `./deploy-minikube.sh deploy` | Déployer (manuel) |
| `./deploy-minikube.sh kustomize` | Déployer avec Kustomize (recommandé) |
| `./deploy-minikube.sh logs <service>` | Voir les logs d'un service (ex: `main-app`) |
| `./deploy-minikube.sh urls` | Afficher les URLs d'accès (Frontend, API) |
| `./deploy-minikube.sh forward` | Port-forward les services clés (Frontend: `localhost:3000`, API: `localhost:8000`) |
| `./deploy-minikube.sh status` | Afficher le statut du cluster et des pods VidP |
| `./deploy-minikube.sh delete` | Supprimer le déploiement VidP |
| `./deploy-minikube.sh stop` | Arrêter Minikube |

#### Architecture Kubernetes Déployée

```
Namespace: vidp
├── ConfigMap: vidp-config
├── Secret: vidp-secrets
├── PVC: mongodb-pvc (5Gi)
│
├── Deployment: mongodb (1 replica)
│   └── Service: mongodb-service (ClusterIP:27017)
│
├── Deployment: langscale (1 replica)
│   └── Service: langscale-service (ClusterIP:8002)
│
├── Deployment: downscale (1 replica)
│   └── Service: downscale-service (ClusterIP:8001)
│
├── Deployment: subtitle (1 replica)
│   └── Service: subtitle-service (ClusterIP:8003)
│
├── Deployment: animal-detect (1 replica)
│   └── Service: animal-detect-service (ClusterIP:8004)
│
├── Deployment: main-app (1 replica)
│   └── Service: main-app-service (NodePort:30080)
│
├── Deployment: frontend (1 replica)
│   └── Service: frontend-service (NodePort:30030)
│
└── Ingress: vidp-ingress
```

📖 **Documentation complète pour Linux/macOS** : [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---


### Déploiement sur Windows (PowerShell)

Ce guide utilise le script `deploy-minikube.ps1`.

#### Prérequis Windows

- Windows 10 / 11 (64 bits)
- Docker Desktop (WSL2 recommandé)
- Minikube, kubectl, Helm installés et accessibles dans le PATH
- PowerShell 5+ ou PowerShell 7+

#### Autoriser l’exécution du script (1 seule fois)

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

#### Démarrage rapide

```powershell
.\deploy-minikube.ps1 all
```
Cette commande démarre Minikube, construit toutes les images Docker et déploie tous les services Kubernetes.

#### Commandes principales

| Commande | Description |
|--------|------------|
| `start` | Démarrer Minikube |
| `stop` | Arrêter Minikube |
| `status` | Statut du cluster |
| `build` | Construire toutes les images Docker |
| `deploy` | Déployer les services Kubernetes |
| `kustomize` | Déployer avec Kustomize |
| `rebuild <service>` | Rebuild et redéployer un service (ex: `main-app`) |
| `logs <service>` | Voir les logs d'un service |
| `health` | Vérifier la santé des services |
| `urls` | Afficher les URLs d'accès Minikube |
| `forward` | Port-forward (Frontend: `localhost:3000`, API: `localhost:8000`) |
| `dashboard` | Ouvrir le dashboard Kubernetes |
| `delete` | Supprimer le déploiement VidP |

📖 **Documentation complète pour Windows** : [DEPLOYMENT_GUIDE_WINDOWS.md](DEPLOYMENT_GUIDE_WINDOWS.md)

---


## 📊 Monitoring Kubernetes avec Prometheus et Grafana

Ce guide explique comment installer et configurer un système de monitoring pour votre cluster Kubernetes Minikube, en utilisant Prometheus pour la collecte de métriques et Grafana pour la visualisation.

---

### Architecture du Système de Monitoring

```
┌─────────────────────────────────────────────────────────────┐
│                    VOTRE NAVIGATEUR                         │
│                                                             │
│  http://localhost:3001  ← Interface Grafana                │
│  http://localhost:9090  ← Interface Prometheus (debug)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ (kubectl port-forward)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           CLUSTER KUBERNETES (Minikube)                     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  NAMESPACE: monitoring                             │    │
│  │                                                     │    │
│  │  ┌──────────────┐       ┌──────────────┐          │    │
│  │  │   Grafana    │◄──────│  Prometheus  │          │    │
│  │  │   (Pod)      │       │    (Pod)     │          │    │
│  │  └──────────────┘       └───────┬──────┘          │    │
│  │                                  │                 │    │
│  └──────────────────────────────────┼─────────────────┘    │
│                                     │                      │
│                                     │ (scrape métriques)   │
│                                     ↓                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  NAMESPACE: default (vos applications)             │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │animal-detect│  │  downscale  │  │ frontend  │  │    │
│  │  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │ langscale   │  │  main-app   │  │  mongodb  │  │    │
│  │  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐                                   │    │
│  │  │  subtitle   │                                   │    │
│  │  └─────────────┘                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---


### Installation sur Linux/macOS (Bash)

Ce guide utilise le script `setup-monitoring.sh`.

#### Prérequis

- Minikube, kubectl, Helm installés
- Minikube démarré avec `minikube start --cpus=4 --memory=8192 --disk-size=20g`

#### Installation automatique

```bash
# Assurez-vous que le script est exécutable
chmod +x setup-monitoring.sh

# Installation complète automatique
./setup-monitoring.sh install
```
Ce script installe Prometheus et Grafana dans le namespace `monitoring`.

#### Accéder à Grafana

```bash
./setup-monitoring.sh dashboard
```
Puis ouvrez : 👉 http://localhost:3001
Identifiants : `admin` / (affiché dans le terminal)

#### Importer le Dashboard VidP

1.  Ouvrez Grafana (http://localhost:3001).
2.  Menu ☰ → **Dashboards** → **New** → **Import**.
3.  Cliquez sur **Upload JSON file** et sélectionnez `vidp-grafana_dashboard.json`.
4.  Sélectionnez la datasource **Prometheus**.
5.  Cliquez sur **Import**.
6.  **Important** : Dans le dashboard, assurez-vous de sélectionner le **namespace correct** de vos applications (`vidp` par défaut) dans le menu déroulant "Namespace" en haut.

#### Dépannage

-   **Aucune donnée dans Grafana** : Vérifiez que les pods de vos applications sont dans le namespace sélectionné dans le dashboard. Vérifiez également que Prometheus collecte les métriques (Prometheus UI, Status -> Targets).
-   **Problèmes de port-forward** : Le port 3001 peut être déjà utilisé.

📖 **Documentation complète pour Linux/macOS** : [monitoring_guide.md](monitoring_guide.md)

---


### Installation sur Windows (PowerShell)

Ce guide utilise le script `setup-monitoring.ps1`.

#### Prérequis Windows

- Docker Desktop (avec Kubernetes désactivé)
- Minikube, kubectl, Helm installés
- Minikube démarré avec `minikube start --cpus=4 --memory=8192 --disk-size=20g`

#### Autoriser l’exécution des scripts (1 seule fois)

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Installation automatique

```powershell
.\setup-monitoring.ps1 install
```
Ce script installe Prometheus et Grafana dans le namespace `monitoring`.

#### Accéder à Grafana

```powershell
.\setup-monitoring.ps1 dashboard
```
Puis ouvrez : 👉 http://localhost:3001
Identifiants : `admin` / (affiché dans le terminal)

#### Importer le Dashboard VidP

1.  Ouvrez Grafana (http://localhost:3001).
2.  Menu ☰ → **Dashboards** → **New** → **Import**.
3.  Cliquez sur **Upload JSON file** et sélectionnez `vidp-grafana_dashboard.json`.
4.  Sélectionnez la datasource **Prometheus**.
5.  Cliquez sur **Import**.
6.  **Important** : Dans le dashboard, assurez-vous de sélectionner le **namespace correct** de vos applications (`vidp` par défaut) dans le menu déroulant "Namespace" en haut.

#### Dépannage

-   **Problème de connexion réseau** : Si `helm repo add` échoue, vérifiez votre connexion internet, proxy ou pare-feu.
-   **Aucun graphique visible** : Attendre 2 minutes, vérifier le namespace sélectionné dans Grafana (`vidp` ou `default`), vérifier la datasource Prometheus.

📖 **Documentation complète pour Windows** : [MONITORING_GUIDE_WINDOWS.md](MONITORING_GUIDE_WINDOWS.md)

---


## 🚀 Démarrage Rapide (Local)

Pour un développement local rapide sans Kubernetes, vous pouvez démarrer tous les services VidP directement.

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

### Guides Détaillés

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | ☸️ **Déploiement Minikube (Linux/macOS)** |
| [DEPLOYMENT_GUIDE_WINDOWS.md](DEPLOYMENT_GUIDE_WINDOWS.md) | 💻 **Déploiement Minikube (Windows)** |
| [monitoring_guide.md](monitoring_guide.md) | 📈 **Monitoring (Linux/macOS)** |
| [MONITORING_GUIDE_WINDOWS.md](MONITORING_GUIDE_WINDOWS.md) | 📊 **Monitoring (Windows)** |
| [START_SERVICES.md](START_SERVICES.md) | 🚀 Guide de démarrage local |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | 🧪 Tests et validation |
| [vidp-main-app/MICROSERVICES_INTEGRATION.md](vidp-main-app/MICROSERVICES_INTEGRATION.md) | 🔧 Intégration des microservices |

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

Ce projet est développé dans le cadre du cours **INF5141 Cloud Computing** à École Nationale Supérieure Polytechnique de Yaoundé (ENSPY).

---


## 👥 Équipe VidP

**Niveau 5 Humanuté Numérique - ENSPY**  
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
**Dernière mise à jour** : 23 janvier 2026