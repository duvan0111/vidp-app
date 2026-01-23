# 🚀 Architecture Kubernetes - VidP Microservices

## Vue d'ensemble

Ce document décrit l'architecture de déploiement de VidP sur Kubernetes, reflétant l'organisation actuelle du projet où chaque microservice est déployé sur des pods dédiés.

## 🏗️ Architecture de Production

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

## 🎯 Principe clé : Upload de fichiers, pas de partage de chemins

### ❌ Ce qui NE fonctionne PAS en production

```python
# MAUVAISE approche (développement local uniquement)
payload = {
    "video_path": "/local_storage/videos/abc123.mp4"  # ⚠️ N'existe que sur Pod A!
}
response = await client.post("http://langscale:8002/api/detect/local", json=payload)
```

**Problème** : Le Pod `langscale` (Pod B) ne peut pas accéder au chemin de fichier du `main-app` (Pod A) sans un système de fichiers partagé.

### ✅ Solution implémentée

```python
# BONNE approche (fonctionne en développement ET production)
with open(video_path, 'rb') as video_file:
    files = {'file': (filename, video_file, 'video/mp4')}
    data = {'duration': '30', 'test_all_languages': 'true'}
    response = await client.post(
        "http://langscale-service:8002/api/detect/upload", # Utilisation du service K8s DNS
        files=files,
        data=data
    )
```

**Avantage** : Le fichier est envoyé via HTTP, indépendamment de l'emplacement des pods.

## 📁 Gestion du stockage en Kubernetes

Notre architecture privilégie l'**Upload HTTP** pour le transfert de fichiers entre microservices. Pour le stockage persistant, seul MongoDB utilise un PersistentVolumeClaim (PVC). Les autres microservices utilisent des `emptyDir` pour leur stockage temporaire, ce qui signifie que les données sont éphémères et liées au cycle de vie du pod.

### PersistentVolumeClaim (PVC) pour MongoDB

```yaml
# mongodb-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongodb-pvc
  namespace: vidp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### Stockage Éphémère (emptyDir) pour les Microservices

```yaml
# Exemple pour main-app et d'autres microservices
volumeMounts:
  - name: video-storage
    mountPath: /app/local_storage
volumes:
  - name: video-storage
    emptyDir: {} # Les données sont perdues si le pod redémarre
```

## 🔄 Flux de traitement en production

### Étape 1 : Upload initial d'une vidéo via Frontend
```
Client (Navigateur) → Ingress → Frontend → Main-App
│
└─> Main-App sauvegarde la vidéo dans son emptyDir local
    └─> Main-App enregistre les métadonnées vidéo dans MongoDB
```

### Étape 2 : Détection de langue
```
Main-App → langscale (via HTTP POST)
│
├─> Main-App lit le fichier depuis son emptyDir
├─> Main-App upload le fichier via HTTP multipart/form-data au service langscale
└─> langscale traite et retourne le résultat (langue détectée)
    └─> Main-App sauvegarde le résultat de la détection de langue dans MongoDB
```

### Étape 3 : Compression (exemple)
```
Main-App → downscale (via HTTP POST)
│
├─> Main-App lit le fichier depuis son emptyDir
├─> Main-App upload le fichier via HTTP multipart/form-data au service downscale
└─> downscale compresse la vidéo et retourne l'URL du fichier compressé
    └─> Main-App sauvegarde l'URL du fichier compressé et les métadonnées dans MongoDB
```
Ce flux est appliqué de manière similaire pour les services `subtitle` et `animal-detect`.

## 🛠️ Configuration Kubernetes (Exemples Simplifiés)

Chaque service est configuré via des Deployments et Services. Les configurations sont gérées par Kustomize dans le répertoire `k8s/`.

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vidp
  labels:
    app: vidp
    environment: development
```

### ConfigMaps et Secrets

Les variables d'environnement des microservices sont gérées par ConfigMaps et Secrets.

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vidp-config
  namespace: vidp
data:
  LANGSCALE_SERVICE_URL: "http://langscale-service:8002"
  DOWNSCALE_SERVICE_URL: "http://downscale-service:8001"
  SUBTITLE_SERVICE_URL: "http://subtitle-service:8003"
  ANIMAL_DETECTION_SERVICE_URL: "http://animal-detect-service:8004"
  APP_NAME: "VidP Kubernetes API"
  CORS_ORIGINS: '["http://localhost:3000","http://frontend-service:3000","*"]'
  # ... autres configs
```

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: vidp-secrets
  namespace: vidp
type: Opaque
stringData:
  MONGODB_USERNAME: "vidp_admin"
  MONGODB_PASSWORD: "vidp_password_2024"
  MONGODB_URL: "mongodb://vidp_admin:vidp_password_2024@mongodb-service:27017/vidp_db?authSource=admin"
```

### Ingress (Exposition externe)

L'Ingress permet d'exposer les services `frontend` et `main-app` via des noms de domaine locaux (`vidp.local`, `api.vidp.local`).

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vidp-ingress
  namespace: vidp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-body-size: "500m" # Taille max upload
    nginx.ingress.kubernetes.io/proxy-read-timeout: "9000"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "9000"
spec:
  ingressClassName: nginx
  rules:
    - host: vidp.local # Accès au Frontend
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 3000
    - host: api.vidp.local # Accès à l'API principale
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: main-app-service
                port:
                  number: 8000
```

## 📊 Avantages de notre architecture

### ✅ Scalabilité
- Chaque service peut scaler indépendamment en ajustant le nombre de `replicas`.
- Exemple : `kubectl scale deployment langscale -n vidp --replicas=5`

### ✅ Isolation
- Un crash ou un problème dans un microservice n'affecte pas directement les autres.
- Les mises à jour peuvent être effectuées de manière indépendante (rolling updates).

### ✅ Flexibilité
- Fonctionne avec des stockages `emptyDir` pour l'éphémère et `PVC` pour la persistance.
- La communication via HTTP est un protocole standard et flexible.

### ✅ Monitoring
- Le `kube-prometheus-stack` est configuré pour collecter les métriques de tous les pods dans le namespace `vidp`.
- Exemple de `ServiceMonitor` (implicite dans Prometheus Operator pour les deployments standard) :
```yaml
# Exemple (ServiceMonitor n'est pas créé manuellement dans les YAMLs fournis,
# mais est géré automatiquement par Prometheus Operator pour les services K8s)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vidp-metrics-main-app
  namespace: vidp
spec:
  selector:
    matchLabels:
      app: main-app
  endpoints:
  - port: http # Doit correspondre à un nom de port dans le Service
    path: /health # Ou un endpoint de métriques si disponible
```

## 🔍 Communication inter-services

### DNS interne Kubernetes
Les microservices communiquent entre eux en utilisant le DNS interne de Kubernetes. Par exemple, `main-app` accède à `langscale` via son nom de service.

```python
# Dans vidp-main-app
# La variable d'environnement LANGSCALE_SERVICE_URL est configurée via ConfigMap
# LANGSCALE_SERVICE_URL: "http://langscale-service:8002"
#                                   ^^^^^^^^^^^^^^
#                                 Nom du Service K8s
```

### Service Discovery automatique
- Le DNS de Kubernetes résout automatiquement `langscale-service` en l'adresse IP du Service correspondant.
- Le load balancing automatique est appliqué entre les pods du service cible.

## 📈 Performance et optimisation

### 1. Limites et Requêtes de ressources (Resource Requests/Limits)
Définir des requêtes et limites de CPU et mémoire aide à la stabilité du cluster et à l'allocation des ressources.

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```
*(Exemple générique, les valeurs réelles sont définies par service dans `k8s/*.yaml`)*

### 2. Readiness & Liveness Probes
Ces sondes garantissent que les pods sont sains et prêts à recevoir du trafic.

```yaml
# Exemple de livenessProbe pour main-app
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20

# Exemple de readinessProbe pour main-app
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

### 3. Horizontal Pod Autoscaling (HPA)
Bien que non activé par défaut dans les `k8s/*.yaml` fournis, l'architecture supporte le HPA pour scaler les pods en fonction de la charge CPU/mémoire.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vidp-main-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: main-app # Cible le déploiement main-app
  minReplicas: 1 # Réplicas minimum (actuellement 1)
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🚀 Déploiement

Le déploiement de l'application VidP dans le cluster Kubernetes `vidp` est orchestré via Kustomize (`k8s/kustomization.yaml`).

```bash
# S'assurer que le namespace est créé
kubectl create namespace vidp

# Appliquer tous les manifestes Kubernetes via Kustomize
kubectl apply -k k8s/

# Alternativement, appliquer les fichiers individuellement dans l'ordre de dépendance:
# 1. Namespace (créé par kustomize ou manuellement)
# kubectl apply -f k8s/namespace.yaml

# 2. ConfigMaps et Secrets
# kubectl apply -f k8s/configmap.yaml
# kubectl apply -f k8s/secrets.yaml

# 3. Déployer MongoDB (PVC d'abord)
# kubectl apply -f k8s/mongodb.yaml

# 4. Déployer les microservices et le frontend
# kubectl apply -f k8s/animal-detect.yaml
# kubectl apply -f k8s/downscale.yaml
# kubectl apply -f k8s/langscale.yaml
# kubectl apply -f k8s/subtitle.yaml
# kubectl apply -f k8s/main-app.yaml
# kubectl apply -f k8s/frontend.yaml

# 5. Configurer l'Ingress
# kubectl apply -f k8s/ingress.yaml

# 6. Vérifier les pods
kubectl get pods -n vidp
```

## 🎯 Conclusion

Notre implémentation actuelle est conçue pour être compatible avec Kubernetes :
- ✅ Pas de dépendance sur chemins de fichiers locaux partagés entre pods.
- ✅ Communication inter-services via HTTP standard et DNS interne Kubernetes.
- ✅ Configuration externalisée via ConfigMaps et Secrets.
- ✅ Services indépendants et largement stateless (à l'exception de MongoDB).
- ✅ Utilisation de `emptyDir` pour le stockage temporaire des microservices.

---