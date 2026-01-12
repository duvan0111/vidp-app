# Interface de Traitement Vidéo - VidP

Cette application Next.js fournit une interface utilisateur moderne pour le système de traitement vidéo VidP. Elle permet aux utilisateurs de télécharger des vidéos vers le service backend FastAPI pour traitement.

## 🎯 Objectif

Développer une interface frontend en Next.js qui sert d'interface utilisateur au service backend FastAPI, permettant aux utilisateurs de soumettre des vidéos pour le traitement initial avec un design moderne et réactif.

## 🚀 Nouveauté v1.1 : Traitement Global Intégré

L'interface intègre maintenant le **pipeline de traitement global** permettant d'orchestrer automatiquement les 3 microservices :

- 🌍 **Détection de langue** - Identifie automatiquement la langue de la vidéo
- 📐 **Compression vidéo** - Réduit la taille avec résolution configurable
- 📝 **Génération de sous-titres** - Utilise Whisper AI pour générer les sous-titres

### Fonctionnalités du traitement global

- ✅ **Mode toggle** : Basculer entre upload simple et traitement complet
- ✅ **Options configurables** : Activer/désactiver chaque étape individuellement
- ✅ **Paramètres avancés** : Résolution, qualité, modèle Whisper, langue
- ✅ **Feedback en temps réel** : Progression de l'upload et du traitement
- ✅ **Résultats détaillés** : Affichage des résultats par étape avec durée

## 🏗️ Architecture et Stack

- **Framework** : Next.js 16 (avec composants React)
- **Langage** : TypeScript
- **Styling** : Tailwind CSS
- **Design** : Thème sombre (Dark Mode)
- **API Backend** : FastAPI (http://localhost:8000)

## ✨ Fonctionnalités

### Composant VideoUploader

#### Zone de Glisser-Déposer (Drag and Drop)
- Zone cliquable et réactive
- Support du glisser-déposer de fichiers
- Validation frontend des fichiers

#### Validation Frontend
- Types de fichiers supportés : MP4, AVI, MOV
- Taille maximale : 500 MB
- Validation en temps réel

#### Affichage du Fichier
- Nom du fichier sélectionné
- Taille formatée (Bytes, KB, MB, GB)
- Aperçu avec icônes vidéo

#### États de l'Upload
- **IDLE** : En attente de sélection
- **SELECTED** : Fichier sélectionné, prêt à uploader
- **UPLOADING** : Transfert en cours avec barre de progression
- **SUCCESS** : Upload réussi avec video_id
- **ERROR** : Affichage des erreurs avec message détaillé

#### Interaction avec l'API
- URL de l'API : `http://localhost:8000/api/v1/videos/upload`
- Requêtes POST multipart/form-data
- Gestion de la progression d'upload
- Gestion des réponses JSON et des erreurs

## 🚀 Installation et Lancement

### Prérequis
- Node.js 18+ 
- npm ou yarn

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd vidp-nextjs-web

# Installer les dépendances
npm install
```

### Lancement du serveur de développement
```bash
npm run dev
```

L'application sera disponible sur [http://localhost:3000](http://localhost:3000)

### Autres commandes
```bash
# Build de production
npm run build

# Démarrer en mode production
npm run start

# Linter
npm run lint
```

## 🎨 Design et Interface

### Thème
- **Dark Mode** par défaut
- Couleurs : Palette de gris avec accents bleus et violets
- Typographie : Police système optimisée

### Composants
- Zone de drop moderne avec animations
- Barres de progression fluides
- Messages de feedback colorés (vert pour succès, rouge pour erreurs)
- Boutons avec états hover et disabled
- Responsive design pour mobile et desktop

### États Visuels
- **Zone de drop** : Changement de couleur selon l'état
- **Progression** : Barre animée avec pourcentage
- **Succès** : Notification verte avec video_id
- **Erreur** : Notification rouge avec message détaillé

## 🔧 Configuration

### Variables d'environnement
Vous pouvez modifier l'URL de l'API dans le fichier `src/app/page.tsx` :
```typescript
const API_URL = 'http://localhost:8000/api/v1/videos/upload'
```

### Tailwind CSS
Configuration personnalisée dans `tailwind.config.js` avec support du dark mode.

## 📝 Structure du Code

```
src/
├── app/
│   ├── globals.css          # Styles globaux avec Tailwind
│   ├── layout.tsx           # Layout principal
│   └── page.tsx             # Composant principal avec VideoUploader
```

### Composant VideoUploader
- **États** : Gestion complète du cycle de vie d'upload
- **Validation** : Contrôles côté client
- **Upload** : XMLHttpRequest avec progression
- **Interface** : Drag & drop, click, feedback visuel

## 🌐 Intégration Backend

L'application communique avec un service FastAPI qui doit fournir :
- Endpoint POST `/api/v1/videos/upload`
- Support multipart/form-data
- Réponses JSON avec `video_id` et `message`
- Gestion des erreurs avec `detail`

## 🎯 Fonctionnalités Futures

- [ ] Prévisualisation vidéo
- [ ] Upload multiple
- [ ] Historique des uploads
- [ ] Gestion des utilisateurs
- [ ] Notifications en temps réel
- [ ] Téléchargement des résultats traités

## 🐛 Dépannage

### Le serveur backend n'est pas accessible
Vérifiez que le service FastAPI fonctionne sur `http://localhost:8000`

### Erreurs de CORS
Configurez le backend FastAPI pour accepter les requêtes depuis `http://localhost:3000`

### Problèmes d'upload
- Vérifiez la taille du fichier (max 500 MB)
- Vérifiez le format (MP4, AVI, MOV supportés)
- Contrôlez la console navigateur pour les erreurs détaillées

## 📄 License

Ce projet fait partie du système VidP développé dans le cadre du cours INF5141 Cloud Computing.
