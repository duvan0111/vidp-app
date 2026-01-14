# 🎬 Video Language Detection API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Une API REST professionnelle pour la détection automatique de la langue parlée dans les vidéos. Développée avec FastAPI, cette solution permet d'analyser des vidéos provenant d'URLs, de fichiers locaux ou de téléchargements directs.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Technologies utilisées](#-technologies-utilisées)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Langues supportées](#-langues-supportées)
- [Architecture](#-architecture)
- [Exemples](#-exemples)
- [Dépannage](#-dépannage)
- [Confidentialité et sécurité](#-confidentialité-et-sécurité)
- [Contributeurs](#-contributeurs)

## ✨ Fonctionnalités

- 🌐 **Détection depuis URL** : Analysez des vidéos hébergées en ligne
- 📁 **Fichiers locaux** : Traitez des vidéos stockées localement
- ⬆️ **Upload de fichiers** : Téléchargez et analysez des vidéos (jusqu'à 100MB)
- 🔄 **Modes asynchrone et synchrone** : Choisissez entre traitement immédiat ou en arrière-plan
- 🌍 **15 langues supportées** : Français, Anglais, Espagnol, Allemand, et plus
- ⚡ **Détection optimisée** : Arrêt automatique dès qu'une langue est détectée (pas de tests inutiles)
- 📊 **Suivi des tâches** : Vérifiez le statut de vos jobs en temps réel
- 🧹 **Nettoyage automatique** : Gestion intelligente des fichiers temporaires
- 📈 **Statistiques API** : Suivez l'utilisation de l'API
- 📚 **Documentation interactive** : Swagger UI et ReDoc intégrés

## 🛠 Technologies utilisées

- **FastAPI** - Framework web moderne et performant
- **Uvicorn** - Serveur ASGI haute performance
- **SpeechRecognition** - Reconnaissance vocale via Google Speech API
- **MoviePy** - Traitement et manipulation de vidéos
- **FFmpeg** - Extraction et conversion audio/vidéo
- **Pydantic** - Validation des données
- **HTTPX** - Client HTTP asynchrone

## 📦 Prérequis

### Système

- **Python** 3.8 ou supérieur
- **FFmpeg** - [Télécharger FFmpeg](https://www.ffmpeg.org/download.html)

### Installation de FFmpeg

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
1. Téléchargez FFmpeg depuis [ffmpeg.org](https://www.ffmpeg.org/download.html)
2. Extrayez l'archive
3. Ajoutez le dossier `bin` à votre PATH système

Vérifiez l'installation :
```bash
ffmpeg -version
```

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone <repository-url>
cd vidp-app/app_langscale
```

### 2. Créer un environnement virtuel

```bash
# Créer l'environnement
python -m venv venv

# Activer l'environnement
# Sur Linux/macOS :
source venv/bin/activate
# Sur Windows :
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Vérifier la structure des dossiers

L'application créera automatiquement les dossiers nécessaires au démarrage :
- `language_detection_storage/videos/` - Fichiers temporaires de vidéos (nettoyés automatiquement)
- `language_detection_storage/audio/` - Fichiers audio temporaires (nettoyés automatiquement)

> ⚠️ **Note de confidentialité** : Les vidéos uploadées et les fichiers audio sont automatiquement supprimés après traitement. Les résultats de détection sont uniquement retournés via l'API (pas de sauvegarde sur disque).

## ⚙️ Configuration

Les paramètres de l'application sont définis dans `config/settings.py` :

```python
# Formats vidéo acceptés
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']

# Taille maximale d'upload
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Durée d'extraction audio par défaut
DEFAULT_DURATION = 30  # secondes

# Timeouts
DOWNLOAD_TIMEOUT = 300  # 5 minutes
PROCESSING_TIMEOUT = 600  # 10 minutes
```

## 🎯 Utilisation

### Démarrer le serveur

```bash
# Méthode 1 : Via uvicorn directement
uvicorn main:app --reload --port 8002

# Méthode 2 : Via le script Python
python main.py
```

Le serveur sera accessible sur `http://localhost:8002`

### Accéder à la documentation

- **Swagger UI** : http://localhost:8002/docs
- **ReDoc** : http://localhost:8002/redoc
- **Health Check** : http://localhost:8002/

## 🔌 API Endpoints

### 1. Détection depuis URL

**POST** `/api/detect`

Détecte la langue d'une vidéo accessible via URL.

**Body :**
```json
{
  "video_url": "https://example.com/video.mp4",
  "duration": 30,
  "test_all_languages": true
}
```

**Query Parameters :**
- `async_mode` (boolean) : `true` pour traitement asynchrone, `false` pour synchrone

**Réponse (mode asynchrone) :**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Language detection job started",
  "async_mode": true
}
```

**Réponse (mode synchrone) :**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "Language detection completed successfully",
  "detected_language": "fr-FR",
  "language_name": "French",
  "confidence": 0.95,
  "processing_time": 12.34,
  "async_mode": false
}
```

### 2. Détection depuis fichier local

**POST** `/api/detect/local`

Traite une vidéo déjà présente sur le serveur.

**Body :**
```json
{
  "video_path": "/path/to/video.mp4",
  "duration": 30,
  "test_all_languages": true
}
```

### 3. Upload et détection

**POST** `/api/detect/upload`

Télécharge une vidéo et détecte la langue.

**Form Data :**
- `file` : Fichier vidéo (max 100MB)
- `duration` : Durée d'extraction (optionnel, défaut: 30s)
- `test_all_languages` : true/false (optionnel, défaut: true)
- `async_mode` : true/false (optionnel, défaut: false)

**Exemple avec curl :**
```bash
curl -X POST "http://localhost:8002/api/detect/upload?async_mode=false" \
  -F "file=@/path/to/video.mp4" \
  -F "duration=30" \
  -F "test_all_languages=true"
```

### 4. Vérifier le statut d'un job

**GET** `/api/status/{job_id}`

Récupère le statut et les résultats d'un job.

**Exemple :**
```bash
curl http://localhost:8002/api/status/550e8400-e29b-41d4-a716-446655440000
```

### 5. Langues supportées

**GET** `/api/languages`

Liste toutes les langues détectables.

**Réponse :**
```json
{
  "total": 15,
  "languages": [
    {
      "code": "fr-FR",
      "display": "Français",
      "name": "French"
    },
    {
      "code": "en-US",
      "display": "Anglais",
      "name": "English"
    }
  ]
}
```

### 6. Nettoyer les fichiers d'un job

**DELETE** `/api/cleanup/{job_id}`

Supprime les fichiers temporaires d'un job.

### 7. Statistiques de l'API

**GET** `/api/stats`

Obtient les statistiques d'utilisation de l'API.

**Réponse :**
```json
{
  "total_jobs": 42,
  "pending": 2,
  "processing": 3,
  "completed": 35,
  "failed": 2
}
```

## 🌍 Langues supportées

L'API peut détecter 15 langues différentes :

| Code    | Langue               | English Name |
|---------|----------------------|--------------|
| fr-FR   | Français            | French       |
| en-US   | Anglais             | English      |
| es-ES   | Espagnol            | Spanish      |
| de-DE   | Allemand            | German       |
| it-IT   | Italien             | Italian      |
| pt-BR   | Portugais           | Portuguese   |
| ru-RU   | Russe               | Russian      |
| ja-JP   | Japonais            | Japanese     |
| zh-CN   | Chinois Mandarin    | Chinese      |
| ar-EG   | Arabe               | Arabic       |
| hi-IN   | Hindi               | Hindi        |
| nl-NL   | Néerlandais         | Dutch        |
| pl-PL   | Polonais            | Polish       |
| tr-TR   | Turc                | Turkish      |
| ko-KR   | Coréen              | Korean       |

## 🏗 Architecture

```
app_langscale/
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances Python
├── api/
│   ├── endpoints.py       # Définition des endpoints
│   └── router.py          # Configuration du routeur
├── config/
│   ├── settings.py        # Configuration globale
│   └── logging_config.py  # Configuration des logs
├── models/
│   ├── enums.py           # Énumérations (statuts, etc.)
│   ├── request_models.py  # Modèles de requêtes
│   └── response_models.py # Modèles de réponses
├── services/
│   ├── detector_service.py      # Service de détection
│   └── background_worker.py     # Traitement en arrière-plan
├── utils/
│   ├── constants.py       # Constantes (langues, etc.)
│   └── file_utils.py      # Utilitaires de fichiers
└── language_detection_storage/
    ├── videos/            # Vidéos téléchargées
    ├── audio/             # Fichiers audio extraits
    └── results/           # Résultats JSON
```

### Flux de traitement

1. **Réception** : L'API reçoit une requête (URL, fichier local ou upload)
2. **Validation** : Vérification du format et de la taille
3. **Téléchargement** : Si nécessaire, téléchargement de la vidéo
4. **Extraction audio** : Conversion vidéo → audio WAV via FFmpeg
5. **Détection** : Analyse de l'audio avec Google Speech Recognition
6. **Résultat** : Retour de la langue détectée avec niveau de confiance

### Optimisation des performances

⚡ **Arrêt anticipé de la détection** : 

Lorsque `test_all_languages=true`, l'API teste les langues dans l'ordre de `SUPPORTED_LANGUAGES`. Dès qu'une langue est reconnue avec succès, **le test s'arrête immédiatement** sans tester les autres langues.

**Avantages** :
- ✅ Réduction du temps de traitement (jusqu'à 93% plus rapide)
- ✅ Économie de bande passante (moins d'appels à l'API Google)
- ✅ Résultats plus rapides pour l'utilisateur

**Exemple** :
```
Langues testées : Français, Anglais, Espagnol, ...
→ Français détecté ✅
→ Arrêt du test (Anglais, Espagnol, etc. ne sont pas testés)
Temps gagné : ~13 secondes (14 langues non testées)
```

**Note** : L'ordre des langues dans `SUPPORTED_LANGUAGES` peut être ajusté selon vos besoins (placez les langues les plus fréquentes en premier).

## 📝 Exemples

### Exemple Python

```python
import requests

# Détection depuis URL (mode synchrone)
response = requests.post(
    "http://localhost:8002/api/detect",
    params={"async_mode": False},
    json={
        "video_url": "https://example.com/video.mp4",
        "duration": 30,
        "test_all_languages": True
    }
)
result = response.json()
print(f"Langue détectée : {result['language_name']}")

# Upload de fichier
with open("video.mp4", "rb") as f:
    files = {"file": f}
    data = {"duration": "30", "test_all_languages": "true"}
    response = requests.post(
        "http://localhost:8002/api/detect/upload",
        files=files,
        data=data,
        params={"async_mode": False}
    )
    print(response.json())
```

### Exemple JavaScript (Node.js)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// Détection depuis URL
async function detectFromUrl() {
  const response = await axios.post(
    'http://localhost:8002/api/detect?async_mode=false',
    {
      video_url: 'https://example.com/video.mp4',
      duration: 30,
      test_all_languages: true
    }
  );
  console.log('Résultat:', response.data);
}

// Upload de fichier
async function uploadAndDetect() {
  const form = new FormData();
  form.append('file', fs.createReadStream('video.mp4'));
  form.append('duration', '30');
  form.append('test_all_languages', 'true');
  
  const response = await axios.post(
    'http://localhost:8002/api/detect/upload?async_mode=false',
    form,
    { headers: form.getHeaders() }
  );
  console.log('Résultat:', response.data);
}
```

### Exemple cURL

```bash
# Détection depuis URL (synchrone)
curl -X POST "http://localhost:8002/api/detect?async_mode=false" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "duration": 30,
    "test_all_languages": true
  }'

# Upload de fichier
curl -X POST "http://localhost:8002/api/detect/upload?async_mode=false" \
  -F "file=@video.mp4" \
  -F "duration=30" \
  -F "test_all_languages=true"

# Vérifier le statut
curl http://localhost:8002/api/status/JOB_ID

# Obtenir les langues supportées
curl http://localhost:8002/api/languages

# Statistiques
curl http://localhost:8002/api/stats
```

## 🔧 Dépannage

### FFmpeg non trouvé

**Erreur** : `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution** :
1. Vérifiez que FFmpeg est installé : `ffmpeg -version`
2. Ajoutez FFmpeg à votre PATH
3. Redémarrez votre terminal/IDE

### Problèmes de reconnaissance vocale

**Erreur** : `speech_recognition.UnknownValueError`

**Causes possibles** :
- Audio de mauvaise qualité
- Pas de parole dans l'extrait
- Langue non supportée

**Solutions** :
- Augmentez la durée d'extraction (`duration`)
- Vérifiez la qualité de la vidéo source
- Utilisez `test_all_languages: true`

### Timeout lors du téléchargement

**Erreur** : Timeout après 5 minutes

**Solutions** :
- Vérifiez votre connexion internet
- Testez l'URL dans un navigateur
- Augmentez `DOWNLOAD_TIMEOUT` dans `settings.py`

### Fichier trop volumineux

**Erreur** : `File size exceeds maximum allowed size`

**Solutions** :
- Compressez votre vidéo
- Augmentez `MAX_UPLOAD_SIZE` dans `settings.py`
- Utilisez la détection depuis URL au lieu de l'upload

## 📊 Logs

Les logs sont enregistrés uniquement dans la console (stdout/stderr) pour faciliter l'intégration avec des systèmes de logging centralisés en production.

Niveaux de log :
- **INFO** : Opérations normales
- **WARNING** : Situations inhabituelles
- **ERROR** : Erreurs de traitement
- **DEBUG** : Informations de débogage détaillées

> 💡 **Astuce** : En production, redirigez la sortie vers un système de logging comme ELK, Loki, ou CloudWatch.

## 🔒 Confidentialité et sécurité

### Gestion des données

Cette API a été conçue avec la confidentialité et la sécurité en tête :

#### ✅ Suppression automatique des fichiers

- **Vidéos uploadées** : Supprimées immédiatement après extraction audio
- **Fichiers audio** : Supprimés immédiatement après traitement
- **Résultats de détection** : Retournés uniquement via l'API (pas de sauvegarde sur disque)
- **Fichiers temporaires** : Nettoyage garanti via blocs `finally` même en cas d'erreur

#### 📝 Logging sécurisé

- Logs en console uniquement (pas de fichier log persistant)
- Aucune information sensible dans les logs
- Compatible avec les systèmes de logging centralisés (ELK, Loki, CloudWatch)

#### 🔐 Bonnes pratiques recommandées

Pour un environnement de production :

1. **Authentification** : Ajoutez OAuth2 ou JWT
   ```python
   from fastapi.security import OAuth2PasswordBearer
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   ```

2. **Rate Limiting** : Limitez le nombre de requêtes par IP
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

3. **CORS** : Restreignez les origines autorisées
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://votre-domaine.com"],
       allow_credentials=True,
       allow_methods=["POST", "GET"],
       allow_headers=["*"],
   )
   ```

4. **HTTPS** : Utilisez un reverse proxy (Nginx, Traefik) avec certificat SSL

5. **Monitoring** : Surveillez les métriques et les erreurs
   - Prometheus + Grafana
   - DataDog
   - New Relic

### Limitations et avertissements

⚠️ **Points d'attention** :

- L'API utilise Google Speech Recognition qui envoie l'audio à Google
- Connexion internet requise pour la reconnaissance vocale
- Les vidéos sont temporairement stockées en mémoire/disque pendant le traitement
- Limite de taille : 100 MB par défaut (modifiable dans `settings.py`)

### Conformité RGPD

Pour une conformité RGPD complète :

- ✅ Minimisation des données : Seul l'audio nécessaire est extrait
- ✅ Durée de conservation : Fichiers supprimés immédiatement après traitement
- ✅ Droit à l'oubli : Aucune donnée persistante à supprimer
- ⚠️ Transfert de données : Audio envoyé à Google (hors UE) - informez vos utilisateurs

## 🔒 Sécurité

⚠️ **Notes importantes** :

- Cette API utilise Google Speech Recognition qui nécessite une connexion internet
- Les fichiers uploadés sont stockés temporairement pendant le traitement puis automatiquement supprimés
- Aucune donnée n'est conservée après le traitement
- En production, ajoutez l'authentification et limitez les CORS

## 🚀 Déploiement en production

### Avec Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```

### Avec Docker

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

```bash
docker build -t vidp-langdetect .
docker run -p 8002:8002 vidp-langdetect
```

## 👥 Contributeurs

**VidP Team**
- Projet développé dans le cadre du Master 2 Data Science
- Cours : INF5141 Cloud Computing

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## 🙏 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/) pour le framework web
- [Google Speech Recognition](https://cloud.google.com/speech-to-text) pour la reconnaissance vocale
- [FFmpeg](https://www.ffmpeg.org/) pour le traitement audio/vidéo
- [MoviePy](https://zulko.github.io/moviepy/) pour la manipulation vidéo

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation interactive sur `/docs`
- Vérifiez les logs dans la console

---

**Version** : 1.2.1  
**Date** : Janvier 2025  
**Équipe** : VidP Team

### 🔄 Changelog

**v1.2.1** (14 Janvier 2025)
- 🐛 **FIX** : Correction du nettoyage automatique en mode synchrone
- ✅ Ajout de blocs `finally` dans les 3 endpoints synchrones
- ✅ Garantie de suppression même en cas d'erreur
- ✅ Tests de vérification effectués

**v1.2.0** (Janvier 2025)
- ✅ Suppression automatique des vidéos uploadées après traitement
- ✅ Suppression automatique des fichiers audio extraits
- ✅ Résultats retournés uniquement via l'API (pas de sauvegarde disque)
- ✅ Logging en console uniquement (pas de fichier log)
- ✅ Amélioration de la confidentialité et de la sécurité
- ✅ Documentation mise à jour avec section confidentialité

**v1.1.0** (Décembre 2024)
- Support de 15 langues
- Mode asynchrone/synchrone
- Upload de fichiers jusqu'à 100MB
