# 🚀 Guide de Déploiement VidP sur Minikube

Ce guide explique comment déployer l'application VidP sur Minikube avec le script `deploy-minikube.sh`.

## 📋 Prérequis

- **Minikube** installé
- **kubectl** installé
- **Docker** installé et en cours d'exécution
- Au moins **8 GB de RAM** disponible
- Au moins **4 CPUs** disponibles

## 🎯 Démarrage rapide

### Option 1 : Déploiement complet automatique

```bash
./deploy-minikube.sh all
```

Cette commande effectue :
1. Démarrage de Minikube (4 CPUs, 8GB RAM)
2. Construction de toutes les images Docker
3. Déploiement sur Kubernetes

**Durée estimée** : 15-20 minutes (premier déploiement)

### Option 2 : Déploiement étape par étape

```bash
# 1. Démarrer Minikube
./deploy-minikube.sh start

# 2. Construire les images Docker
./deploy-minikube.sh build

# 3. Déployer sur Kubernetes
./deploy-minikube.sh deploy
# OU avec Kustomize (recommandé)
./deploy-minikube.sh kustomize
```

## 📚 Commandes disponibles

### Gestion du cluster

| Commande | Description | Durée |
|----------|-------------|-------|
| `./deploy-minikube.sh start` | Démarrer Minikube | ~2 min |
| `./deploy-minikube.sh stop` | Arrêter Minikube | ~30 sec |
| `./deploy-minikube.sh status` | Afficher le statut | Instantané |

### Build et déploiement

| Commande | Description | Durée |
|----------|-------------|-------|
| `./deploy-minikube.sh build` | Construire toutes les images | ~10-15 min |
| `./deploy-minikube.sh deploy` | Déployer (manuel) | ~2 min |
| `./deploy-minikube.sh kustomize` | Déployer avec Kustomize | ~2 min |
| `./deploy-minikube.sh delete` | Supprimer le déploiement | ~30 sec |

### Gestion des services

| Commande | Description | Exemple |
|----------|-------------|---------|
| `./deploy-minikube.sh rebuild <service>` | Rebuild un service | `./deploy-minikube.sh rebuild main-app` |
| `./deploy-minikube.sh logs <service>` | Voir les logs | `./deploy-minikube.sh logs frontend` |
| `./deploy-minikube.sh health` | Vérifier la santé | - |

### Accès aux services

| Commande | Description |
|----------|-------------|
| `./deploy-minikube.sh urls` | Afficher les URLs d'accès |
| `./deploy-minikube.sh forward` | Port-forward (localhost:8000 et :3000) |
| `./deploy-minikube.sh dashboard` | Ouvrir le dashboard K8s |

## 🔧 Workflows courants

### 1️⃣ Premier déploiement

```bash
# Démarrage complet
./deploy-minikube.sh all

# Attendre que tous les pods soient prêts
watch kubectl get pods -n vidp

# Accéder aux services
./deploy-minikube.sh urls
```

### 2️⃣ Modifier et redéployer un service

```bash
# Exemple : modification du code main-app
# 1. Modifier le code dans vidp-main-app/vidp-fastapi-service/

# 2. Rebuild et redéployer
./deploy-minikube.sh rebuild main-app

# 3. Vérifier les logs
./deploy-minikube.sh logs main-app
```

### 3️⃣ Déboguer un problème

```bash
# Vérifier la santé
./deploy-minikube.sh health

# Voir les logs d'un service
./deploy-minikube.sh logs main-app

# Voir tous les événements
kubectl get events -n vidp --sort-by='.lastTimestamp'

# Décrire un pod problématique
kubectl describe pod <pod-name> -n vidp
```

### 4️⃣ Accéder aux services

#### Option A : Via NodePort (Minikube service)

```bash
# Obtenir les URLs
./deploy-minikube.sh urls

# Frontend : http://192.168.49.2:30030
# API : http://192.168.49.2:30080
```

#### Option B : Via Port-Forward

```bash
# Démarrer le port-forward
./deploy-minikube.sh forward

# Dans un autre terminal
# Frontend : http://localhost:3000
# API : http://localhost:8000
```

#### Option C : Via Minikube Tunnel (recommandé)

```bash
# Terminal 1
minikube tunnel

# Terminal 2 - Accéder aux services
curl http://main-app-service.vidp.svc.cluster.local:8000/health
```

## 🏗️ Architecture déployée

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

## 📊 Ressources allouées

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| **mongodb** | 250m | 500m | 256Mi | 512Mi |
| **langscale** | 250m | 500m | 256Mi | 512Mi |
| **downscale** | 500m | 1000m | 512Mi | 1Gi |
| **subtitle** | 500m | 1500m | 1Gi | 2Gi |
| **animal-detect** | 250m | 500m | 512Mi | 1Gi |
| **main-app** | 250m | 500m | 256Mi | 512Mi |
| **frontend** | 100m | 200m | 128Mi | 256Mi |
| **TOTAL** | **2.1 CPUs** | **4.7 CPUs** | **2.9 GB** | **5.8 GB** |

## 🐛 Résolution de problèmes

### Problème : Minikube ne démarre pas

```bash
# Vérifier Docker
docker ps

# Nettoyer et redémarrer
minikube delete
minikube start --cpus=4 --memory=8192 --driver=docker
```

### Problème : Images Docker non trouvées

```bash
# Configurer Docker pour Minikube
eval $(minikube docker-env)

# Rebuild les images
./deploy-minikube.sh build

# Vérifier les images
docker images | grep vidp
```

### Problème : Pod en CrashLoopBackOff

```bash
# Voir les logs
./deploy-minikube.sh logs <service>

# Décrire le pod
kubectl describe pod -n vidp -l app=<service>

# Rebuild si nécessaire
./deploy-minikube.sh rebuild <service>
```

### Problème : MongoDB ne se connecte pas

```bash
# Vérifier que MongoDB est prêt
kubectl get pods -n vidp -l app=mongodb

# Tester la connexion depuis main-app
MAIN_APP_POD=$(kubectl get pod -n vidp -l app=main-app -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n vidp $MAIN_APP_POD -- env | grep MONGODB
```

## 🔄 Cycle de développement

### Développement d'un microservice

```bash
# 1. Modifier le code
vim app_langscale/main.py

# 2. Rebuild et redéployer
./deploy-minikube.sh rebuild langscale

# 3. Suivre les logs en temps réel
./deploy-minikube.sh logs langscale

# 4. Tester
curl http://localhost:8000/api/v1/processing/language-detection
```

### Tests de bout en bout

```bash
# 1. Démarrer le port-forward
./deploy-minikube.sh forward &

# 2. Tester l'API
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -F "file=@test_video.mp4"

# 3. Accéder au frontend
open http://localhost:3000
```

## 📝 Notes importantes

### imagePullPolicy: Never

Tous les services utilisent `imagePullPolicy: Never` car les images sont construites localement dans le daemon Docker de Minikube. **Ne pas changer** cette valeur.

### Volumes emptyDir

La plupart des services utilisent `emptyDir` pour le stockage temporaire. Les données sont **perdues** lors du redémarrage des pods. Seul MongoDB utilise un PersistentVolume.

### Ressources minimales

Minikube doit avoir au minimum :
- **4 CPUs**
- **8 GB RAM**
- **20 GB d'espace disque**

## 🎯 Commandes utiles supplémentaires

```bash
# Voir tous les ressources
kubectl get all -n vidp

# Redémarrer un pod
kubectl delete pod -n vidp -l app=main-app

# Échelle d'un service (augmenter les replicas)
kubectl scale deployment main-app -n vidp --replicas=2

# Accéder au shell d'un pod
kubectl exec -it -n vidp <pod-name> -- /bin/sh

# Copier des fichiers depuis/vers un pod
kubectl cp <local-file> vidp/<pod-name>:/path/to/file

# Voir l'utilisation des ressources
kubectl top pods -n vidp
kubectl top nodes
```

## 📚 Ressources supplémentaires

- [Documentation Minikube](https://minikube.sigs.k8s.io/docs/)
- [Documentation Kubernetes](https://kubernetes.io/docs/)
- [Documentation Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/)

---

**VidP Team** - Cloud Computing Project 2024
