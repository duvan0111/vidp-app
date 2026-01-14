# 🎬 VidP - Video Processing Platform

Application complète de traitement et gestion de vidéos développée avec FastAPI, Next.js et MongoDB.

## 📋 Vue d'ensemble

VidP est une plateforme web pour l'upload, le stockage et le traitement de fichiers vidéo. L'application est conteneurisée avec Docker pour un déploiement simple et portable.

**🚀 Nouveauté v1.1 : Traitement Global Automatisé**
- 🔄 **Un seul endpoint** pour orchestrer les 3 microservices automatiquement
- 🎯 Détection de langue → Compression → Génération de sous-titres
- 📊 Gestion intelligente des erreurs (statut partiel si échec partiel)
- 💾 Sauvegarde MongoDB après chaque étape

**✨ Fonctionnalités clés :**
- 🎥 Upload et gestion des vidéos
- 🌍 Détection automatique de langue (15 langues supportées)
- 📐 Compression vidéo multi-résolutions (240p-1080p)
- 📝 Génération de sous-titres avec Whisper AI
- ⚙️ Suivi en temps réel des traitements
- 🎨 Interface moderne et intuitive

**📚 Documentation complète disponible :**
- [`INTERFACE_GUIDE.md`](INTERFACE_GUIDE.md) - Guide d'utilisation complet
- [`INTERFACE_FEATURES.md`](vidp-nextjs-web/INTERFACE_FEATURES.md) - Détails techniques
- [`MICROSERVICES_INTEGRATION.md`](MICROSERVICES_INTEGRATION.md) - Intégration des microservices
- [`SUBTITLE_METADATA_UPDATE.md`](SUBTITLE_METADATA_UPDATE.md) - Mise à jour structure MongoDB sous-titres
- [`SUBTITLE_FORMAT_UPDATE.md`](SUBTITLE_FORMAT_UPDATE.md) - Alignement format de retour app_subtitle

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VidP Application                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend   │  │   Backend    │  │   MongoDB    │  │ Microservices │  │
│  │   Next.js    │◄─┤   FastAPI    │◄─┤   Database   │  │  Traitement   │  │
│  │   Port 3000  │  │   Port 8000  │  │   Port 27017 │  │  8001-8003    │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └───────┬────────┘  │
│                            │                                     │           │
│                            └─────────────────────────────────────┘           │
│                              • Détection langue (8002)                       │
│                              • Compression vidéo (8001)                      │
│                              • Génération sous-titres (8003)                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Microservices intégrés

| Service | Port | Description |
|---------|------|-------------|
| **`vidp-main-app`** | 8000 | Service principal (upload, orchestration, MongoDB) |
| **`app_langscale`** | 8002 | Détection de langue (15 langues, Google Speech) |
| **`app_downscale`** | 8001 | Compression vidéo (240p-1080p, FFmpeg) |
| **`app_subtitle`** | 8003 | Génération sous-titres (Whisper AI, multi-langues) |

### Technologies

- **Backend** : FastAPI (Python 3.11)
- **Frontend** : Next.js 16 (React 19, TypeScript)
- **Base de données** : MongoDB 7.0
- **Conteneurisation** : Docker & Docker Compose
- **Stockage** : Volumes Docker persistants

## 🚀 Démarrage rapide

### Prérequis

- Docker 20.10+
- Docker Compose 2.0+

### Installation en 3 étapes

1. **Cloner et naviguer vers le projet**
   ```bash
   cd "/home/dv-fk/Documents/School/Master 2 DS/INF5141 Cloud Computing/Projet VidP/vidp-main-app"
   ```

2. **Configurer les variables d'environnement** (optionnel)
   ```bash
   cp .env.example .env
   # Éditer .env si nécessaire
   ```

3. **Démarrer l'application**
   
   **Option A : Avec les scripts automatiques (recommandé)**
   ```bash
   # Démarrer tous les services
   ./start-services.sh
   
   # Arrêter tous les services
   ./stop-services.sh
   ```
   
   **Option B : Avec le script de déploiement Docker**
   ```bash
   ./deploy.sh
   ```
   
   **Option C : Avec Make**
   ```bash
   make up-build
   ```
   
   **Option D : Avec Docker Compose directement**
   ```bash
   docker-compose up --build -d
   ```

### Accès aux services

Une fois démarré, accédez à :

- 🌐 **Frontend** : http://localhost:3000
- 🔌 **API Backend** : http://localhost:8000
- 📖 **Documentation API (Swagger)** : http://localhost:8000/docs
- 📘 **Documentation API (ReDoc)** : http://localhost:8000/redoc

## 🔄 Traitement Global (Nouveau)

### Endpoint unique d'orchestration

Le nouvel endpoint `/api/v1/processing/process-video` permet de traiter une vidéo en une seule requête :

```bash
curl -X POST "http://localhost:8000/api/v1/processing/process-video" \
  -F "video_file=@ma_video.mp4" \
  -F "enable_language_detection=true" \
  -F "enable_compression=true" \
  -F "enable_subtitles=true" \
  -F "target_resolution=720p" \
  -F "subtitle_model=tiny"
```

### Workflow automatique

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   1. Détection  │────▶│  2. Compression │────▶│  3. Sous-titres │
│     Langue      │     │     Vidéo       │     │    (Whisper)    │
│    (8002)       │     │    (8001)       │     │    (8003)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │                    MongoDB (Sauvegarde)                  │
   └─────────────────────────────────────────────────────────┘
```

### Paramètres disponibles

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `video_file` | File | - | Fichier vidéo à traiter (obligatoire) |
| `enable_language_detection` | bool | true | Activer la détection de langue |
| `language_detection_duration` | int | 30 | Durée d'extraction audio (secondes) |
| `enable_compression` | bool | true | Activer la compression |
| `target_resolution` | string | 720p | Résolution cible (240p-1080p) |
| `crf` | int | 23 | Qualité de compression (18-28) |
| `enable_subtitles` | bool | true | Activer les sous-titres |
| `subtitle_model` | string | tiny | Modèle Whisper (tiny/base/small/medium/large) |
| `subtitle_language` | string | auto | Langue (auto = utilise la langue détectée) |

### Exemple de réponse

```json
{
  "video_id": "49b60095-5f8d-4e44-b670-732da25cca2d",
  "overall_status": "completed",
  "message": "✅ Traitement complet réussi (3/3 étapes)",
  "total_duration": 125.5,
  "success_count": 3,
  "failure_count": 0,
  "language_detection": {
    "stage": "language_detection",
    "status": "completed",
    "result": {
      "detected_language": "fr",
      "language_name": "Français",
      "confidence": 0.95
    }
  },
  "compression": {
    "stage": "compression",
    "status": "completed",
    "result": {
      "resolution": "720p",
      "output_path": "/video_storage/compressed/..."
    }
  },
  "subtitle_generation": {
    "stage": "subtitle_generation",
    "status": "completed",
    "result": {
      "model_name": "tiny",
      "language": "fr"
    }
  }
}
```

### Récupérer les résultats

```bash
curl "http://localhost:8000/api/v1/processing/process-video/{video_id}"
```

## 📦 Structure du projet

```
vidp-main-app/
├── vidp-fastapi-service/       # Service Backend FastAPI
│   ├── app/
│   │   ├── api/                # Endpoints API
│   │   ├── core/               # Configuration
│   │   ├── db/                 # Connecteur MongoDB
│   │   ├── models/             # Modèles de données
│   │   └── services/           # Services métier
│   ├── local_storage/          # Stockage local des vidéos
│   ├── main.py                 # Point d'entrée
│   ├── requirements.txt
│   └── Dockerfile
│
├── vidp-nextjs-web/            # Application Frontend Next.js
│   ├── src/
│   │   ├── app/                # Pages et layouts Next.js
│   │   └── types/              # Types TypeScript
│   ├── public/                 # Assets statiques
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # Orchestration des services
├── Makefile                    # Commandes simplifiées
├── deploy.sh                   # Script de déploiement
├── .env.example                # Exemple de configuration
├── DOCKER_DEPLOYMENT.md        # Guide détaillé de déploiement
└── README.md                   # Ce fichier
```

## 🎮 Commandes utiles

<!-- ### Avec Make (recommandé) -->

<!-- ```bash
make help           # Afficher l'aide
make up-build       # Construire et démarrer
make up             # Démarrer les services
make down           # Arrêter les services
make restart        # Redémarrer les services
make logs           # Voir les logs
make ps             # État des services
make clean          # Nettoyer les conteneurs
make backup-mongo   # Sauvegarder MongoDB 
``` -->

### Avec Docker Compose

```bash
# Construire et démarrer
docker-compose up --build -d

# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Voir les logs
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mongodb

# État des services
docker compose ps

# Redémarrer un service
docker compose restart backend

# Option 1 : Reconstruire uniquement le backend
docker compose up --build backend -d
```

<!-- ### Avec le script de déploiement

```bash
./deploy.sh
# Menu interactif avec options :
# 1. Démarrage complet
# 2. Démarrage rapide
# 3. Arrêter
# 4. Voir logs
# 5. Nettoyer
# 6. État
``` -->

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à partir de `.env.example` :

```bash
# Backend
APP_NAME=VidP Docker API
APP_HOST=0.0.0.0
APP_PORT=8000
MONGODB_URL=mongodb://vidp_admin:vidp_password_2024@mongodb:27017/vidp_db?authSource=admin
MONGODB_DATABASE=vidp_db

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# MongoDB
MONGO_INITDB_ROOT_USERNAME=vidp_admin
MONGO_INITDB_ROOT_PASSWORD=vidp_password_2024
```

⚠️ **En production** : Changez les mots de passe par défaut !

## 💾 Gestion des données

### Volumes persistants

Les données sont stockées dans des volumes Docker :

- `mongodb_data` : Données de la base MongoDB
- `video_storage` : Fichiers vidéos uploadés
- `metadata_storage` : Métadonnées des vidéos

### Sauvegardes

**Sauvegarder MongoDB** :
```bash
make backup-mongo
# ou
docker run --rm -v vidp-main-app_mongodb_data:/data \
  -v $(pwd)/backups:/backup busybox \
  tar czf /backup/mongodb-$(date +%Y%m%d).tar.gz /data
```

**Restaurer MongoDB** :
```bash
docker run --rm -v vidp-main-app_mongodb_data:/data \
  -v $(pwd)/backups:/backup busybox \
  tar xzf /backup/mongodb-YYYYMMDD.tar.gz
```

## 🔍 Développement

### Développement local sans Docker

**Backend** :
```bash
cd vidp-fastapi-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend** :
```bash
cd vidp-nextjs-web
npm install
npm run dev
```

### Debug

**Accéder à un conteneur** :
```bash
# Backend
docker compose exec backend bash

# Frontend
docker compose exec frontend sh

# MongoDB
docker compose exec mongodb mongosh -u vidp_admin -p vidp_password_2024 --authenticationDatabase admin
```

**Voir les ressources utilisées** :
```bash
docker stats
# ou
make stats
```

## 🐛 Dépannage

### Problèmes courants

**Port déjà utilisé** :
```bash
# Trouver le processus
sudo lsof -i :8000
sudo lsof -i :3000

# Ou modifier le port dans docker-compose.yml
```

**MongoDB ne démarre pas** :
```bash
# Voir les logs
docker compose logs mongodb

# Réinitialiser les volumes
docker compose down -v
docker compose up -d
```

**Manque d'espace disque** :
```bash
# Nettoyer
docker system prune -a
docker volume prune

# Voir l'utilisation
docker system df
```

**Réinitialisation complète** :
```bash
docker compose down -v --remove-orphans
docker system prune -a
docker-compose up --build -d
```

## 📚 Documentation

- **Guide de déploiement détaillé** : [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **Documentation API** : http://localhost:8000/docs (une fois l'app démarrée)
- **Tests Frontend** : [vidp-nextjs-web/TESTING.md](vidp-nextjs-web/TESTING.md)

## 🏭 Production

Pour le déploiement en production :

1. ✅ Changez tous les mots de passe
2. ✅ Configurez HTTPS avec un reverse proxy (Nginx/Traefik)
3. ✅ Mettez en place des sauvegardes automatiques
4. ✅ Configurez le monitoring (Prometheus/Grafana)
5. ✅ Limitez les ressources des conteneurs
6. ✅ Sécurisez les accès réseau

Voir [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) section Production pour plus de détails.

## 🧪 Tests

**Backend** :
```bash
docker-compose exec backend pytest
```

**Frontend** :
```bash
docker-compose exec frontend npm test
```

## 📊 Monitoring

**Vérifier la santé des services** :
```bash
docker-compose ps
# ou
make health
```

**Statistiques temps réel** :
```bash
docker stats
```

## 🤝 Contribution

Ce projet est développé dans le cadre du Master 2 Data Science - INF5141 Cloud Computing.

## 📄 Licence

Usage éducatif - Master 2 Data Science

---

## 💡 Astuces

- Utilisez `make help` pour voir toutes les commandes disponibles
- Les logs sont accessibles avec `docker-compose logs -f`
- Pour un rebuild complet : `make rebuild`
- Pour sauvegarder avant des tests : `make backup-mongo`

## 🔗 Liens utiles

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [MongoDB Documentation](https://docs.mongodb.com/)

---

**Version** : 1.1.0  
**Date** : Janvier 2026  
**Auteur** : Master 2 DS - INF5141 Cloud Computing

### Changelog

#### v1.1.0 (Janvier 2026)
- ✨ **Traitement Global** : Nouvel endpoint `/process-video` pour orchestrer les 3 microservices
- 🔄 Gestion intelligente des erreurs avec statut partiel
- 💾 Sauvegarde MongoDB après chaque étape de traitement
- 📊 Nouveaux modèles Pydantic (`GlobalProcessingResult`, `ProcessingStageResult`)
- 🧪 Script de test interactif `test_global_processing.py`

#### v1.0.0 (Décembre 2024)
- 🎬 Version initiale avec upload et gestion des vidéos
- 🌍 Intégration détection de langue (app_langscale)
- 📐 Intégration compression vidéo (app_downscale)
- 📝 Intégration génération sous-titres (app_subtitle)
- 🎨 Interface Next.js moderne
