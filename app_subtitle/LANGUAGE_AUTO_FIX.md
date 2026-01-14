# 🐛 Fix: Unsupported language: auto

## Problème

L'API `app_subtitle` retournait une erreur 500 lors de la génération de sous-titres :

```
2026-01-14 18:08:57,853 - services.subtitle_service - ERROR - Failed to generate subtitles: Unsupported language: auto
2026-01-14 18:08:57,853 - services.video_processor - ERROR - Processing failed: Unsupported language: auto
INFO:     127.0.0.1:42394 - "POST /api/generate-subtitles/ HTTP/1.1" 500 Internal Server Error
```

### Cause Racine

Le modèle **Whisper AI** ne supporte pas la valeur `"auto"` comme paramètre de langue. Pour la détection automatique, Whisper attend :
- `None` (pas de paramètre language)
- OU l'omission totale du paramètre

Lorsque `language="auto"` était passé explicitement, Whisper levait une exception `ValueError: Unsupported language: auto`.

### Origine du Bug

Le paramètre `language="auto"` était probablement envoyé par :
- Le frontend (formulaire d'upload)
- Un service d'agrégation
- Un test manuel avec curl

## ✅ Solution Appliquée

### 1. Normalisation dans l'endpoint (routes/subtitle_routes.py)

Ajout d'une normalisation au début de l'endpoint pour convertir les valeurs invalides en `None` :

```python
@router.post("/generate-subtitles/")
async def generate_subtitles(
    # ... paramètres ...
    language: Optional[str] = Form(None),
):
    # Normalize language parameter (convert "auto" to None for Whisper)
    if language and language.lower() in ["auto", "none", ""]:
        language = None
    
    # ... reste du traitement ...
```

**Valeurs normalisées** :
- `"auto"` → `None`
- `"none"` → `None`
- `""` (chaîne vide) → `None`
- `None` → `None` (inchangé)
- Autres valeurs → Conservées (ex: `"en"`, `"fr"`)

### 2. Protection dans le service (services/subtitle_service.py)

Ajout d'une validation supplémentaire dans le service de génération de sous-titres :

```python
def generate_srt(self, audio_path: Path, model_name: str, language: Optional[str] = None):
    # ...
    
    try:
        transcribe_options: Dict[str, Any] = {
            "word_timestamps": True,
            "verbose": False,
            "task": "transcribe"
        }
        
        # Handle language parameter
        # Whisper expects None for auto-detection, not "auto"
        if language and language.lower() not in ["auto", "none", ""]:
            transcribe_options["language"] = language
            logger.info(f"Using specified language: {language}")
        else:
            logger.info("Using automatic language detection")
        
        # Transcribe audio
        result = model.transcribe(str(audio_path), **transcribe_options)
```

**Avantages de cette approche** :
- ✅ Double protection (endpoint + service)
- ✅ Logging clair du comportement (détection auto vs langue spécifiée)
- ✅ Compatible avec tous les clients (frontend, API, curl)

## 📋 Fichiers Modifiés

1. **routes/subtitle_routes.py**
   - Ligne ~30 : Ajout de normalisation `language`

2. **services/subtitle_service.py**
   - Ligne ~56-65 : Validation et logging du paramètre langue

## 🧪 Tests de Vérification

### Test 1 : Détection automatique avec "auto"
```bash
curl -X POST "http://localhost:8003/api/generate-subtitles/" \
  -F "video=@test.mp4" \
  -F "language=auto" \
  -F "output_format=json"

# Attendu : ✅ Succès, détection automatique
```

### Test 2 : Détection automatique avec None
```bash
curl -X POST "http://localhost:8003/api/generate-subtitles/" \
  -F "video=@test.mp4" \
  -F "output_format=json"

# Attendu : ✅ Succès, détection automatique
```

### Test 3 : Langue spécifique
```bash
curl -X POST "http://localhost:8003/api/generate-subtitles/" \
  -F "video=@test.mp4" \
  -F "language=en" \
  -F "output_format=json"

# Attendu : ✅ Succès, anglais forcé
```

### Test 4 : Chaîne vide
```bash
curl -X POST "http://localhost:8003/api/generate-subtitles/" \
  -F "video=@test.mp4" \
  -F "language=" \
  -F "output_format=json"

# Attendu : ✅ Succès, détection automatique
```

## 📊 Comportement Avant/Après

| Valeur `language` | Avant | Après |
|-------------------|-------|-------|
| `None` | ✅ Détection auto | ✅ Détection auto |
| `"auto"` | ❌ Erreur 500 | ✅ Détection auto |
| `"none"` | ❌ Erreur 500 | ✅ Détection auto |
| `""` (vide) | ❌ Erreur 500 | ✅ Détection auto |
| `"en"` | ✅ Anglais | ✅ Anglais |
| `"fr"` | ✅ Français | ✅ Français |

## 🔍 Langues Supportées par Whisper

Whisper supporte environ 100 langues. Codes courants :
- `en` - Anglais
- `fr` - Français
- `es` - Espagnol
- `de` - Allemand
- `it` - Italien
- `pt` - Portugais
- `ru` - Russe
- `ja` - Japonais
- `zh` - Chinois
- `ar` - Arabe
- etc.

Voir la liste complète : https://github.com/openai/whisper#available-models-and-languages

## 📝 Recommandations

### Pour le Frontend
Utilisez un sélecteur avec les options suivantes :
```javascript
const languageOptions = [
  { value: null, label: "Auto-détection" },  // Valeur par défaut
  { value: "en", label: "English" },
  { value: "fr", label: "Français" },
  { value: "es", label: "Español" },
  // ... autres langues
];
```

**Ne jamais envoyer `"auto"` comme valeur de langue.**

### Pour les Tests
```python
# ✅ Bon : Détection automatique
response = requests.post(url, files={"video": file}, data={"output_format": "json"})

# ✅ Bon : Langue spécifique
response = requests.post(url, files={"video": file}, data={"language": "en", "output_format": "json"})

# ❌ Éviter (mais maintenant géré) :
response = requests.post(url, files={"video": file}, data={"language": "auto"})
```

## 🎯 Impact

- ✅ Plus d'erreurs 500 avec `language="auto"`
- ✅ API plus robuste et tolérante aux erreurs
- ✅ Logs clairs pour le debugging
- ✅ Rétro-compatible (comportement existant préservé)

## 📅 Historique

- **2026-01-14** : Correction du bug "Unsupported language: auto"
- **2026-01-14** : Ajout de normalisation et validation double

---

**Status** : ✅ Corrigé  
**Version** : 1.0.1  
**Auteur** : VidP Team
