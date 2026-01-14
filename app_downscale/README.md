# 🎬 Video Compression API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.123.8-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

API professionnelle de compression vidéo construite avec FastAPI. Compressez vos vidéos à partir d'URLs, de fichiers locaux ou par upload direct avec un contrôle total sur la qualité et la résolution.

## ✨ Fonctionnalités

- 🌐 **Compression depuis URL** : Téléchargez et compressez des vidéos directement depuis Internet
- 📂 **Compression de fichiers locaux** : Compressez des fichiers vidéo déjà présents sur le serveur
- 📤 **Upload et compression** : Uploadez vos propres vidéos et compressez-les
- 🎯 **Résolutions multiples** : Support de 240p à 1080p
- ⚙️ **Qualité ajustable** : Contrôle CRF (18-30) pour équilibrer qualité et taille
- 🔄 **Traitement asynchrone** : Gestion des jobs avec suivi de statut en temps réel
- 🗑️ **Nettoyage automatique** : Les vidéos d'entrée sont automatiquement supprimées après compression
- 📊 **API RESTful** : Documentation interactive avec Swagger UI
- 🚀 **Performant** : Optimisé avec FFmpeg et MoviePy
- 🔒 **Confidentialité** : Seules les vidéos compressées sont conservées

## 📋 Table des matières

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Démarrage](#démarrage)
- [Utilisation](#utilisation)
- [Endpoints API](#endpoints-api)
- [Exemples](#exemples)
- [Structure du projet](#structure-du-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Contribution](#contribution)
- [Licence](#licence)

## 🔧 Prérequis

- **Python** 3.10 ou supérieur
- **FFmpeg** installé sur le système
- **pip** pour la gestion des packages Python

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
Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html) et ajoutez au PATH.

## 📦 Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd app_downscale
```

2. **Créer un environnement virtuel** (recommandé)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

L'application utilise des paramètres configurables dans `config/settings.py` :

| Paramètre | Valeur par défaut | Description |
|-----------|-------------------|-------------|
| `API_TITLE` | "Video Compression API" | Nom de l'API |
| `API_VERSION` | "1.1.0" | Version de l'API |
| `DEFAULT_RESOLUTION` | "360p" | Résolution par défaut |
| `DEFAULT_CRF_VALUE` | 28 | Qualité CRF par défaut |
| `MIN_CRF_VALUE` | 18 | CRF minimum (meilleure qualité) |
| `MAX_CRF_VALUE` | 30 | CRF maximum (plus compressé) |
| `MAX_UPLOAD_SIZE` | 1 GB | Taille maximale d'upload |

### Résolutions supportées

- **1080p** : Full HD (1920x1080)
- **720p** : HD (1280x720)
- **480p** : SD (854x480)
- **360p** : Mobile (640x360)
- **240p** : Basse résolution (426x240)

### Formats vidéo supportés

`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`, `.wmv`

## 🚀 Démarrage

### Démarrage simple

```bash
python main.py
```

L'API sera accessible sur `http://localhost:8001`

### Démarrage avec Uvicorn (recommandé pour la production)

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Options utiles :
- `--reload` : Rechargement automatique lors de modifications (développement)
- `--workers 4` : Nombre de workers (production)
- `--log-level info` : Niveau de logging

### Vérification du démarrage

Accédez à `http://localhost:8001` pour vérifier que l'API est en ligne.

## 📖 Utilisation

### Documentation interactive

Une fois l'API démarrée, accédez à :
- **Swagger UI** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc

### Workflow typique

1. **Soumettre une vidéo** via l'un des endpoints de compression
2. **Récupérer le job_id** dans la réponse
3. **Vérifier le statut** avec `/api/status/{job_id}`
4. **Télécharger le résultat** avec `/api/download/{job_id}` une fois terminé

## 🔌 Endpoints API

### Compression

#### POST `/api/compress/url`
Compresse une vidéo depuis une URL.

**Body :**
```json
{
  "video_url": "https://example.com/video.mp4",
  "resolution": "360p",
  "crf_value": 28,
  "custom_filename": "my_video"
}
```

#### POST `/api/compress/local`
Compresse un fichier vidéo local.

**Body :**
```json
{
  "local_path": "/path/to/video.mp4",
  "resolution": "720p",
  "crf_value": 25
}
```

#### POST `/api/compress/upload`
Upload et compresse une vidéo.

**Form Data :**
- `file` : Fichier vidéo (multipart/form-data)
- `resolution` : Résolution cible (optionnel)
- `crf_value` : Valeur CRF (optionnel)
- `custom_filename` : Nom personnalisé (optionnel)

### Statut et Téléchargement

#### GET `/api/status/{job_id}`
Récupère le statut d'un job de compression.

**Réponse :**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "message": "Compression completed",
  "progress": 100,
  "output_path": "/path/to/compressed/video.mp4",
  "metadata": {
    "original_size": "10.5 MB",
    "compressed_size": "3.2 MB",
    "compression_ratio": "69.5%"
  }
}
```

#### GET `/api/download/{job_id}`
Télécharge la vidéo compressée.

#### DELETE `/api/cleanup/{job_id}`
Supprime les fichiers associés à un job.

### Utilitaires

#### GET `/`
Point d'entrée de l'API avec informations sur le service.

#### GET `/api/test/local`
Endpoint de test pour la compression locale.

#### GET `/video_storage/{path}`
Accès direct aux fichiers vidéo stockés.

## 💡 Exemples

### Exemple avec cURL

**Compression depuis URL :**
```bash
curl -X POST "http://localhost:8001/api/compress/url" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://sample-videos.com/video.mp4",
    "resolution": "480p",
    "crf_value": 26
  }'
```

**Vérifier le statut :**
```bash
curl -X GET "http://localhost:8001/api/status/{job_id}"
```

**Télécharger la vidéo :**
```bash
curl -X GET "http://localhost:8001/api/download/{job_id}" \
  -o compressed_video.mp4
```

### Exemple avec Python

```python
import requests

# 1. Soumettre la compression
response = requests.post(
    "http://localhost:8001/api/compress/url",
    json={
        "video_url": "https://example.com/video.mp4",
        "resolution": "360p",
        "crf_value": 28
    }
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# 2. Vérifier le statut
import time
while True:
    status_response = requests.get(
        f"http://localhost:8001/api/status/{job_id}"
    )
    status = status_response.json()
    
    print(f"Status: {status['status']} - {status['message']}")
    
    if status["status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)

# 3. Télécharger si réussi
if status["status"] == "completed":
    download_response = requests.get(
        f"http://localhost:8001/api/download/{job_id}"
    )
    with open("compressed_video.mp4", "wb") as f:
        f.write(download_response.content)
    print("Vidéo téléchargée avec succès!")
```

### Exemple avec JavaScript (Fetch API)

```javascript
async function compressVideo() {
  // 1. Soumettre la compression
  const response = await fetch('http://localhost:8001/api/compress/url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      video_url: 'https://example.com/video.mp4',
      resolution: '360p',
      crf_value: 28
    })
  });
  
  const { job_id } = await response.json();
  console.log('Job ID:', job_id);
  
  // 2. Vérifier le statut
  while (true) {
    const statusResponse = await fetch(
      `http://localhost:8001/api/status/${job_id}`
    );
    const status = await statusResponse.json();
    
    console.log(`Status: ${status.status} - ${status.message}`);
    
    if (status.status === 'completed' || status.status === 'failed') {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  // 3. Télécharger la vidéo
  window.location.href = `http://localhost:8001/api/download/${job_id}`;
}
```

### Exemple d'upload de fichier (HTML + JavaScript)

```html
<!DOCTYPE html>
<html>
<head>
  <title>Video Compression</title>
</head>
<body>
  <h1>Upload et compresser une vidéo</h1>
  
  <form id="uploadForm">
    <input type="file" id="videoFile" accept="video/*" required>
    <select id="resolution">
      <option value="240p">240p</option>
      <option value="360p" selected>360p</option>
      <option value="480p">480p</option>
      <option value="720p">720p</option>
      <option value="1080p">1080p</option>
    </select>
    <input type="number" id="crf" value="28" min="18" max="30">
    <button type="submit">Compresser</button>
  </form>
  
  <div id="status"></div>
  
  <script>
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData();
      formData.append('file', document.getElementById('videoFile').files[0]);
      formData.append('resolution', document.getElementById('resolution').value);
      formData.append('crf_value', document.getElementById('crf').value);
      
      const response = await fetch('http://localhost:8001/api/compress/upload', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      document.getElementById('status').innerHTML = 
        `Job ID: ${result.job_id} - Status: ${result.status}`;
    });
  </script>
</body>
</html>
```

## 📁 Structure du projet

```
app_downscale/
├── main.py                     # Point d'entrée de l'application
├── requirements.txt            # Dépendances Python
├── video_api.log              # Fichier de logs
│
├── config/                    # Configuration
│   ├── __init__.py
│   ├── settings.py           # Paramètres de l'application
│   └── constants.py          # Constantes
│
├── models/                    # Modèles de données
│   ├── __init__.py
│   ├── enums.py              # Énumérations (résolutions, statuts)
│   ├── request_models.py     # Modèles de requêtes
│   └── response_models.py    # Modèles de réponses
│
├── routes/                    # Routes API
│   ├── __init__.py
│   ├── compression_routes.py # Endpoints de compression
│   ├── status_routes.py      # Endpoints de statut
│   ├── test_routes.py        # Endpoints de test
│   └── static_routes.py      # Routes pour fichiers statiques
│
├── services/                  # Logique métier
│   ├── __init__.py
│   ├── video_downscaler.py   # Service de compression vidéo
│   └── job_manager.py        # Gestion des jobs
│
├── utils/                     # Utilitaires
│   ├── __init__.py
│   ├── file_utils.py         # Utilitaires fichiers
│   └── logging_config.py     # Configuration du logging
│
├── middleware/                # Middlewares
│   ├── __init__.py
│   └── cors.py               # Configuration CORS
│
└── video_storage/            # Stockage des vidéos
    ├── downloads/            # Vidéos téléchargées
    ├── uploads/              # Vidéos uploadées
    └── compressed/           # Vidéos compressées
        ├── 240p/
        ├── 360p/
        ├── 480p/
        ├── 720p/
        └── 1080p/
```

## 📈 Performance

- Compression moyenne : 60-80% de réduction de taille
- Temps de traitement : ~10-30 secondes pour 1 minute de vidéo (1080p → 360p)
- Support du traitement parallèle avec Uvicorn workers

## 🔒 Confidentialité et Gestion des Fichiers

### Gestion automatique des fichiers temporaires

- ✅ **Suppression automatique** : Les vidéos uploadées/téléchargées sont supprimées après compression
- ✅ **Seules les vidéos compressées sont conservées** : dans `video_storage/compressed/`
- ✅ **Nettoyage garanti** : Bloc `finally` pour assurer la suppression même en cas d'erreur
- ✅ **Pas de log fichier** : Logging uniquement en console (stdout)

### Structure de stockage

```
video_storage/
├── uploads/          # Fichiers temporaires (nettoyés automatiquement)
├── downloads/        # Fichiers temporaires (nettoyés automatiquement)
└── compressed/       # Vidéos compressées (conservées)
    ├── 240p/
    ├── 360p/
    ├── 480p/
    ├── 720p/
    └── 1080p/
```

### Recommandations pour la production

- Implémentez un système de nettoyage périodique pour `compressed/`
- Configurez des limites de quota par utilisateur
- Ajoutez une authentification (OAuth2, JWT)
- Implémentez un rate limiting
- Utilisez HTTPS pour le chiffrement
- Configurez un système de backup pour les vidéos compressées

## 🔄 Mises à jour futures

- [ ] Support de la compression par lots
- [ ] Prévisualisation des vidéos
- [ ] Authentification et autorisation
- [ ] Webhooks pour notifications
- [ ] Support des sous-titres
- [ ] Interface web complète
- [ ] API pour la découpe de vidéos

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteurs

**VidP Team**
- Version: 1.1.0
- Contact: [Votre email ou lien]

## 🙏 Remerciements

- FastAPI pour le framework excellent
- FFmpeg pour les capacités de traitement vidéo
- La communauté open source

---

Made with ❤️ by VidP Team | [Documentation](http://localhost:8001/docs) | [GitHub](https://github.com/your-repo)
