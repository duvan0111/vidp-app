# Rapport d'Architecture Technique - Plateforme VidP

## 1. Introduction

La plateforme VidP (Video Processing) est une application distribuée conçue pour le traitement automatisé de vidéos. Elle s'articule autour d'une architecture microservices déployée sur Kubernetes (Minikube pour le développement), offrant des fonctionnalités telles que la détection de langue, la détection d'animaux, la compression vidéo et la génération/incrustation de sous-titres. Ce rapport vise à détailler l'architecture du projet, les choix technologiques et les méthodes de déploiement, ainsi que les solutions apportées aux défis rencontrés.

## 2. Vue d'Ensemble Architecturale

VidP est orchestrée par une application principale (FastAPI) qui interagit avec plusieurs microservices spécialisés.

### 2.1. Architecture Microservices Générale

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

## 3. Déploiement Kubernetes (Minikube)

Le projet VidP est conçu pour être déployé sur un cluster Kubernetes. Pour le développement et les tests locaux, Minikube est utilisé.

### 3.1. Architecture Kubernetes

L'architecture Kubernetes de VidP est structurée autour d'un namespace `vidp` qui contient tous les déploiements de microservices, leurs services internes, une base de données MongoDB, et un Ingress pour l'accès externe.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                            Kubernetes Cluster                                          │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                        │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Namespace: vidp                                                                                     │  │
│  │                                                                                                    │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │  │                                      Ingress (vidp.local, api.vidp.local)                      │  │
│  │  └────────────────────────────────────┬───────────────────────────────────────────────────────────┘  │
│  │                                        │                                                             │  │
│  │       ┌────────────────────────────┐   │   ┌────────────────────────────────┐                        │  │
│  │       │ Frontend (Next.js)         │◄───┼──▶│ Main-App (FastAPI Orchestrator)  │                        │  │
│  │       │   (vidp.local:3000)        │    │    │    (api.vidp.local:8000)         │                        │  │
│  │       └────────────────────────────┘    │    └───────────────┬────────────────┘                        │  │
│  │                                         │                     │ (HTTP POST - Upload file)               │  │
│  │                                         │                     ▼                                         │  │
│  │  ┌───────────────────────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐  │  │
│  │  │ animal-detect             │  │ downscale │  │ langscale │  │ subtitle  │  │ mongodb               │  │  │
│  │  │   (Service: :8004)        │  │ (Service: │  │ (Service: │  │ (Service: │  │   (Service: :27017)   │  │  │
│  │  │   (emptyDir)              │  │  :8001)   │  │  :8002)   │  │  :8003)   │  │   (PVC)               │  │  │
│  │  └───────────────────────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────────────────┘  │  │
│  │                                                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Choix technologiques et justifications :**

*   **Kubernetes (Minikube)** : Fournit un environnement de conteneurisation et d'orchestration robuste. Minikube permet de simuler un cluster K8s localement pour le développement et les tests.
*   **Helm** : Utilisé pour simplifier le déploiement et la gestion des applications Kubernetes, notamment la stack de monitoring Prometheus-Grafana.
*   **Docker** : Technologie de conteneurisation sous-jacente pour empaqueter chaque microservice.

### 3.2. Principe clé : Upload de fichiers, pas de partage de chemins

Une décision architecturale fondamentale pour garantir la robustesse et la scalabilité en production est l'utilisation de **requêtes HTTP multipart/form-data pour le transfert de fichiers entre microservices**, plutôt que de s'appuyer sur des volumes partagés.

*   **Problématique du partage de chemins** : En environnement distribué (Kubernetes), un chemin de fichier local sur un Pod A n'est pas accessible directement par un Pod B. Tenter de le faire conduit à des erreurs `FileNotFound`.
*   **Solution implémentée** : Chaque microservice reçoit les fichiers nécessaires via un upload HTTP. Le `main-app` lit la vidéo depuis son stockage temporaire, l'envoie au microservice cible (par exemple, `langscale`), qui la traite et renvoie le résultat.

**Avantage** : Cette approche découple les services des contraintes de stockage sous-jacent et rend l'architecture plus résiliente, scalable et agnostique à l'infrastructure.

### 3.3. Gestion du stockage en Kubernetes

*   **`emptyDir` pour le stockage temporaire** : La plupart des microservices (sauf MongoDB) utilisent des volumes `emptyDir`. Ce type de volume est créé lorsque le Pod est assigné à un nœud et existe tant que le Pod s'exécute sur ce nœud. Les données sont perdues si le Pod redémarre, ce qui est acceptable pour le stockage temporaire de fichiers vidéo en cours de traitement, car le `main-app` gère la persistance des métadonnées dans MongoDB et la vidéo finale via le service d'agrégation.
*   **`PersistentVolumeClaim (PVC)` pour MongoDB** : MongoDB, nécessitant un stockage persistant, utilise un `PersistentVolumeClaim` pour s'assurer que ses données ne sont pas perdues lors des redémarrages de Pods ou de nœuds.

### 3.4. Processus de Déploiement

Le déploiement est automatisé via des scripts shell (`deploy-minikube.sh` pour Linux/macOS, `deploy-minikube.ps1` pour Windows) qui utilisent Kustomize.

**Étapes générales :**
1.  **Démarrage de Minikube** : Initialisation du cluster local.
2.  **Configuration du Docker daemon de Minikube** : Pour que Docker puisse construire des images directement dans l'environnement de Minikube.
3.  **Construction des images Docker** : Chaque microservice est construit en tant qu'image Docker locale.
4.  **Déploiement Kustomize** : Application des manifestes Kubernetes (`k8s/`) via Kustomize pour créer le namespace `vidp`, ConfigMaps, Secrets, Deployments, Services et Ingress.

## 4. Détails des Microservices

### 4.1. `vidp-main-app` (Orchestrateur Principal)

*   **Rôle** : Point d'entrée principal de l'API, orchestrateur des workflows de traitement, gestion des uploads vidéo, persistance des métadonnées dans MongoDB, et communication avec les autres microservices.
*   **Technologies** : FastAPI, Python, httpx, Motor (client MongoDB).
*   **Déploiement** : `main-app` Deployment, `main-app-service` (NodePort), Ingress (`api.vidp.local`).
*   **Remarque** : Gère l'orchestration séquentielle des appels aux microservices, le stockage temporaire (`emptyDir`) des vidéos en cours de traitement, et la persistance des résultats dans MongoDB.

### 4.2. `app_langscale` (Détection de Langue)

*   **Rôle** : Détecte la langue parlée dans la piste audio d'une vidéo.
*   **Technologies** : FastAPI, Python, Google Speech Recognition.
*   **Déploiement** : `langscale` Deployment, `langscale-service` (ClusterIP).

### 4.3. `app_downscale` (Compression Vidéo)

*   **Rôle** : Compresse les vidéos à différentes résolutions et niveaux de qualité.
*   **Technologies** : FastAPI, Python, FFmpeg.
*   **Déploiement** : `downscale` Deployment, `downscale-service` (ClusterIP).

### 4.4. `app_subtitle` (Génération de Sous-titres)

*   **Rôle** : Génère automatiquement des sous-titres (SRT) à partir de la piste audio d'une vidéo.
*   **Technologies** : FastAPI, Python, `openai-whisper` (IA de transcription d'OpenAI), FFmpeg.
*   **Déploiement** : `subtitle` Deployment, `subtitle-service` (ClusterIP).

### 4.5. `app_animal_detect` (Détection d'Animaux)

*   **Rôle** : Détecte et identifie des animaux (et autres objets) dans des vidéos ou des images.
*   **Technologies** : FastAPI, Python, `ultralytics` (YOLOv8), OpenCV.
*   **Déploiement** : `animal-detect` Deployment, `animal-detect-service` (ClusterIP).

### 4.6. Service d'Agrégation (Cloud-hosted)

*   **Rôle** : Combine la vidéo traitée avec les sous-titres générés (et d'autres métadonnées) pour produire une vidéo finale avec incrustation des sous-titres. C'est le point final du pipeline, générant une URL de streaming.
*   **Technologies** : Non détaillé ici (car cloud-hosted), mais communique via HTTP/HTTPS avec le `main-app`.
*   **Déploiement** : Externe au cluster Minikube local.

### 4.7. `vidp-nextjs-web` (Frontend)

*   **Rôle** : Interface utilisateur web pour interagir avec l'API principale de VidP.
*   **Technologies** : Next.js, React.
*   **Déploiement** : `frontend` Deployment, `frontend-service` (NodePort), Ingress (`vidp.local`).

## 5. Monitoring avec Prometheus et Grafana

Un système de monitoring est essentiel pour observer la santé et les performances des microservices. VidP utilise la stack Prometheus-Grafana déployée via Helm.

### 5.1. Composants

*   **Prometheus** : Collecte les métriques en "scrapant" les endpoints `metrics` exposés par les services Kubernetes.
*   **Grafana** : Fournit des tableaux de bord personnalisables pour visualiser les métriques collectées par Prometheus.
*   **`kube-prometheus-stack` (Helm Chart)** : Simplifie le déploiement de Prometheus, Grafana, Alertmanager, Node Exporter et Kube-State-Metrics.

### 5.2. Déploiement

Le déploiement du monitoring est automatisé via les scripts `setup-monitoring.sh` (Linux/macOS) et `setup-monitoring.ps1` (Windows).

**Étapes clés :**
1.  Installation du Helm chart `kube-prometheus-stack` dans un namespace `monitoring` dédié.
2.  Configuration de Grafana avec un mot de passe administrateur.
3.  Mise en place du port-forward pour accéder aux interfaces Prometheus et Grafana localement.

### 5.3. Tableau de bord personnalisé Grafana

Le fichier `vidp-grafana_dashboard.json` fournit un tableau de bord préconfiguré pour visualiser les métriques clés des pods VidP (CPU, mémoire, réseau, état des pods, redémarrages).

**Flexibilité du Namespace** : Le tableau de bord a été modifié pour inclure une variable de templating `namespace`, permettant de sélectionner dynamiquement le namespace où les applications VidP sont déployées (par défaut `vidp`), garantissant ainsi la visibilité des métriques quel que soit le namespace utilisé.

## 6. Défis et Solutions Implémentées

Au cours du développement et de l'intégration, plusieurs défis ont été rencontrés et résolus :

*   **Optimisation de la taille et du temps de build Docker (`animal-detect`)** :
    *   **Problème** : L'image `app_animal_detect` était très volumineuse et longue à construire principalement à cause des dépendances lourdes comme `torch` et `opencv-python` tirées par `ultralytics`.
    *   **Solution** : Utilisation d'une image de base pré-construite (`ultralytics/ultralytics:latest-cpu`) qui inclut déjà ces bibliothèques, réduisant drastiquement le temps de build et la taille de l'image finale.
*   **Dépendance `lap` dans `app_animal_detect`** :
    *   **Problème** : La fonction `model.track` d'`ultralytics` tentait d'utiliser des algorithmes de tracking qui pouvaient dépendre de `lap`, même si le tracking n'était pas l'objectif principal.
    *   **Solution** : Modification du code pour ne réaliser qu'une détection simple (`model(...)`) et suppression de la dépendance `lap` des `requirements.txt`.
*   **`ffprobe` manquant dans `vidp-main-app`** :
    *   **Problème** : L'orchestrateur `vidp-main-app` utilise `ffprobe` pour vérifier la présence d'une piste audio avant de lancer la détection de langue. `ffprobe` n'était pas installé dans son conteneur Docker.
    *   **Solution** : Ajout de l'installation de `ffmpeg` (qui inclut `ffprobe`) dans le `Dockerfile` de `vidp-main-app`.
*   **Timeouts des microservices** :
    *   **Problème** : Les vidéos de longue durée n'arrivaient pas à la fin du traitement en raison de timeouts HTTP lors des appels inter-microservices.
    *   **Solution** : Augmentation de la valeur par défaut du `microservices_timeout` (de 9000s à 18000s) dans la configuration du `vidp-main-app`.
*   **Incompatibilité de version `whisper` dans `app_subtitle`** :
    *   **Problème** : L'API `app_subtitle` générait une erreur `DecodingOptions.__init__() got an unexpected keyword argument 'word_timestamps'`, indiquant une incompatibilité avec la version installée de la bibliothèque `whisper`.
    *   **Solution** : Remplacement de la dépendance `whisper-openai` par `openai-whisper` (la bibliothèque officielle) dans les `requirements.txt` de `app_subtitle`.
*   **`ModuleNotFoundError: No module named 'ffmpeg'` dans `app_subtitle`** :
    *   **Problème** : Malgré l'installation de `ffmpeg` (outil en ligne de commande), le binding Python `ffmpeg-python` n'était pas installé, causant une erreur d'importation dans le code Python.
    *   **Solution** : Ajout de `ffmpeg-python` aux `requirements.txt` de `app_subtitle`.
*   **Problèmes de connectivité du dépôt Helm** :
    *   **Problème** : Le script d'installation du monitoring ne parvenait pas à ajouter le dépôt Helm `prometheus-community` en raison de problèmes de réseau (firewall/proxy).
    *   **Solution** : Amélioration du script `setup-monitoring.ps1`/`.sh` pour une meilleure gestion des erreurs et l'introduction d'une logique de détection de chart Helm local. Si le dépôt distant n'est pas accessible, le script peut utiliser un chart téléchargé manuellement.
*   **Absence de graphiques Grafana** :
    *   **Problème** : Après l'importation du tableau de bord Grafana, aucun graphique ne s'affichait. Le tableau de bord était configuré pour un namespace `vidp` fixe, tandis que les pods pouvaient être dans un autre namespace.
    *   **Solution** : Modification du `vidp-grafana_dashboard.json` pour ajouter une variable de templating `namespace`, permettant de sélectionner dynamiquement le namespace des applications dans Grafana.
*   **Robustesse des scripts PowerShell/Bash** :
    *   **Problème** : Erreurs de parsing PowerShell (`AmpersandNotAllowed`) et gestion peu fiable des processus `port-forward` en arrière-plan.
    *   **Solution** : Correction de la syntaxe PowerShell et refactoring des fonctions `Test-Metrics` et `Port-Forward` (dans les scripts de monitoring et déploiement respectivement) pour utiliser des mécanismes robustes (`Start-Process`/`Start-Job` avec `try-finally` pour PowerShell, `&`/`trap` pour Bash) pour la gestion des processus en arrière-plan et leur nettoyage.
*   **Cohérence du namespace Kubernetes dans la documentation** :
    *   **Problème** : Le document `KUBERNETES_ARCHITECTURE.md` utilisait `vidp-production` tandis que les scripts utilisaient `vidp`.
    *   **Solution** : Harmonisation de tous les documents pour utiliser le namespace `vidp`.

## 7. Conclusion

Le projet VidP présente une architecture microservices moderne et scalable, conçue pour être déployée efficacement sur Kubernetes. Les choix d'outils (FastAPI, Docker, Kubernetes, Prometheus, Grafana, YOLOv8, Whisper AI) ont été guidés par les besoins de performance, de flexibilité et de facilité de maintenance en environnement distribué. Les défis rencontrés et les solutions apportées ont renforcé la robustesse de l'implémentation, offrant une plateforme complète pour le traitement vidéo intelligent.

---
**Date du rapport** : jeudi 22 janvier 2026 (Adapté à la locale utilisateur)
**Auteur** : Gemini CLI Agent (pour le compte de l'utilisateur)