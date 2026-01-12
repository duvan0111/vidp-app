# 🚀 Guide de Déploiement VidP sur Minikube

Ce guide explique comment déployer la plateforme VidP sur un cluster Kubernetes local avec Minikube.

## 📋 Prérequis

### Logiciels requis

1. **Minikube** - [Installation](https://minikube.sigs.k8s.io/docs/start/)
   ```bash
   # Linux
   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
   sudo install minikube-linux-amd64 /usr/local/bin/minikube
   ```

2. **kubectl** - [Installation](https://kubernetes.io/docs/tasks/tools/)
   ```bash
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   ```

3. **Docker** - [Installation](https://docs.docker.com/get-docker/)

### Configuration minimale
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disque**: 20 GB libres

## 🏗️ Architecture Kubernetes

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Kubernetes Cluster (Minikube)                       │
│                                   Namespace: vidp                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Ingress Controller                               │    │
│  │                    vidp.local / api.vidp.local                          │    │
│  └────────────────────────────┬────────────────────────────────────────────┘    │
│                               │                                                  │
│         ┌─────────────────────┴─────────────────────┐                           │
│         │                                           │                           │
│  ┌──────▼──────┐                           ┌───────▼───────┐                    │
│  │  Frontend   │                           │   Main App    │                    │
│  │  (NextJS)   │                           │  (FastAPI)    │                    │
│  │  Port 3000  │                           │  Port 8000    │                    │
│  │  NodePort   │                           │  NodePort     │                    │
│  │   30030     │                           │   30080       │                    │
│  └─────────────┘                           └───────┬───────┘                    │
│                                                    │                            │
│                    ┌───────────────────────────────┼───────────────────────┐    │
│                    │                               │                       │    │
│         ┌─────────▼────────┐           ┌──────────▼─────────┐             │    │
│         │     MongoDB      │           │   Microservices    │             │    │
│         │   Port 27017     │           │                    │             │    │
│         │   ClusterIP      │           │                    │             │    │
│         └──────────────────┘           └────────────────────┘             │    │
│                                                    │                            │
│              ┌─────────────┬───────────────┬──────┴────────┐                   │
│              │             │               │               │                    │
│       ┌──────▼─────┐ ┌─────▼─────┐ ┌──────▼─────┐ ┌───────▼──────┐             │
│       │ Langscale  │ │ Downscale │ │  Subtitle  │ │Animal Detect │             │
│       │ Port 8002  │ │ Port 8001 │ │ Port 8003  │ │  Port 8004   │             │
│       │ ClusterIP  │ │ ClusterIP │ │ ClusterIP  │ │  ClusterIP   │             │
│       └────────────┘ └───────────┘ └────────────┘ └──────────────┘             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Déploiement rapide

### Option 1: Script automatique (recommandé)

```bash
# Déploiement complet en une commande
./deploy-minikube.sh all
```

### Option 2: Makefile

```bash
# Afficher l'aide
make help

# Déploiement complet
make all
```

### Option 3: Étape par étape

```bash
# 1. Démarrer Minikube
./deploy-minikube.sh start

# 2. Construire les images Docker
./deploy-minikube.sh build

# 3. Déployer sur Kubernetes
./deploy-minikube.sh deploy
```

## 📁 Structure des fichiers Kubernetes

```
k8s/
├── namespace.yaml      # Namespace vidp
├── configmap.yaml      # Configuration (URLs des services)
├── secrets.yaml        # Secrets (credentials MongoDB)
├── mongodb.yaml        # Base de données MongoDB
├── langscale.yaml      # Service détection de langue
├── downscale.yaml      # Service compression vidéo
├── subtitle.yaml       # Service génération sous-titres
├── animal-detect.yaml  # Service détection animaux
├── main-app.yaml       # Orchestrateur principal
├── frontend.yaml       # Interface Next.js
└── ingress.yaml        # Routage externe
```

## 🔌 Communication entre services

### DNS Kubernetes interne

Les microservices communiquent via le DNS interne de Kubernetes :

| Service | DNS interne | Port |
|---------|-------------|------|
| MongoDB | `mongodb-service:27017` | 27017 |
| Langscale | `langscale-service:8002` | 8002 |
| Downscale | `downscale-service:8001` | 8001 |
| Subtitle | `subtitle-service:8003` | 8003 |
| Animal Detect | `animal-detect-service:8004` | 8004 |
| Main App | `main-app-service:8000` | 8000 |
| Frontend | `frontend-service:3000` | 3000 |

### Configuration dans main-app

Le service principal utilise ces variables d'environnement :
```yaml
LANGSCALE_SERVICE_URL: "http://langscale-service:8002"
DOWNSCALE_SERVICE_URL: "http://downscale-service:8001"
SUBTITLE_SERVICE_URL: "http://subtitle-service:8003"
ANIMAL_DETECTION_SERVICE_URL: "http://animal-detect-service:8004"
```

## 🌐 Accès aux services

### Méthode 1: Port-Forward (développement)

```bash
# Démarrer les port-forwards
./deploy-minikube.sh forward

# Ou manuellement
kubectl port-forward svc/main-app-service 8000:8000 -n vidp &
kubectl port-forward svc/frontend-service 3000:3000 -n vidp &
```

Accès :
- **Frontend** : http://localhost:3000
- **API** : http://localhost:8000
- **API Docs** : http://localhost:8000/docs

### Méthode 2: NodePort

```bash
# Obtenir les URLs
minikube service main-app-service -n vidp --url
minikube service frontend-service -n vidp --url
```

### Méthode 3: Minikube Tunnel + Ingress

```bash
# Terminal 1: Démarrer le tunnel
minikube tunnel

# Ajouter à /etc/hosts
echo "$(minikube ip) vidp.local api.vidp.local" | sudo tee -a /etc/hosts
```

Accès :
- **Frontend** : http://vidp.local
- **API** : http://api.vidp.local

## 📊 Commandes utiles

### Surveillance

```bash
# État des pods
kubectl get pods -n vidp -w

# Logs d'un service
kubectl logs -f -l app=main-app -n vidp

# Ressources utilisées
kubectl top pods -n vidp
```

### Dépannage

```bash
# Décrire un pod
kubectl describe pod <pod-name> -n vidp

# Shell dans un pod
kubectl exec -it <pod-name> -n vidp -- /bin/sh

# Événements du namespace
kubectl get events -n vidp --sort-by='.lastTimestamp'
```

### Scaling

```bash
# Augmenter les replicas
kubectl scale deployment/main-app --replicas=3 -n vidp

# Autoscaling (HPA)
kubectl autoscale deployment/main-app --min=1 --max=5 --cpu-percent=70 -n vidp
```

### Redémarrage

```bash
# Redémarrer un deployment
kubectl rollout restart deployment/main-app -n vidp

# Vérifier le rollout
kubectl rollout status deployment/main-app -n vidp
```

## 🧪 Tests

### Test de santé

```bash
# Health check global
curl http://localhost:8000/health

# Santé des microservices
curl http://localhost:8000/api/v1/processing/health
```

### Test d'upload

```bash
# Upload et détection de langue
curl -X POST "http://localhost:8000/api/v1/processing/language-detection" \
  -F "video_file=@video.mp4" \
  -F "duration=30"
```

## 🔧 Personnalisation

### Modifier les ressources

Éditez les fichiers YAML dans `k8s/` :

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Ajouter des replicas

```yaml
spec:
  replicas: 3
```

### Configurer le stockage persistant

Pour un stockage persistant des vidéos, modifiez `main-app.yaml` :

```yaml
volumes:
  - name: video-storage
    persistentVolumeClaim:
      claimName: video-pvc
```

## 🛑 Arrêt et nettoyage

```bash
# Supprimer le déploiement
./deploy-minikube.sh delete

# Arrêter Minikube
./deploy-minikube.sh stop

# Supprimer complètement Minikube
minikube delete
```

## ❓ Dépannage courant

### Pod en état "ImagePullBackOff"

```bash
# Vérifier que les images sont construites dans Minikube
eval $(minikube docker-env)
docker images | grep vidp

# Reconstruire les images
./deploy-minikube.sh build
```

### Pod en état "CrashLoopBackOff"

```bash
# Voir les logs
kubectl logs <pod-name> -n vidp --previous

# Décrire le pod
kubectl describe pod <pod-name> -n vidp
```

### Service non accessible

```bash
# Vérifier les endpoints
kubectl get endpoints -n vidp

# Vérifier les services
kubectl get svc -n vidp
```

## 📚 Ressources

- [Documentation Minikube](https://minikube.sigs.k8s.io/docs/)
- [Documentation Kubernetes](https://kubernetes.io/docs/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/docs)
