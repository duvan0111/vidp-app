# 🚀 Architecture Kubernetes - VidP Microservices

## Vue d'ensemble

Ce document décrit l'architecture de déploiement de VidP en production avec Kubernetes, où chaque microservice est déployé sur des pods/machines différents.

## 🏗️ Architecture de Production

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Namespace: vidp-production                                 │   │
│  │                                                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │   │
│  │  │   Pod A     │  │   Pod B     │  │   Pod C     │       │   │
│  │  │ vidp-main   │  │ langscale   │  │ downscale   │       │   │
│  │  │   :8000     │  │   :8002     │  │   :8003     │       │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │   │
│  │         │                 │                 │              │   │
│  │         │    HTTP POST    │                 │              │   │
│  │         │  (Upload file)  │                 │              │   │
│  │         ├────────────────>│                 │              │   │
│  │         │                 │                 │              │   │
│  │         │    Response     │                 │              │   │
│  │         │<────────────────┤                 │              │   │
│  │         │                 │                 │              │   │
│  └─────────┼─────────────────┼─────────────────┼──────────────┘   │
│            │                 │                 │                   │
│  ┌─────────▼─────────────────▼─────────────────▼──────────────┐   │
│  │           Persistent Volumes (PV)                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │   │
│  │  │  MongoDB │  │  Vidéos  │  │ Résultats│                 │   │
│  │  │   Data   │  │  Storage │  │  Cache   │                 │   │
│  │  └──────────┘  └──────────┘  └──────────┘                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
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

**Problème** : Le Pod B (langscale) ne peut pas accéder au chemin de fichier du Pod A (vidp-main).

### ✅ Solution implémentée

```python
# BONNE approche (fonctionne en développement ET production)
with open(video_path, 'rb') as video_file:
    files = {'file': (filename, video_file, 'video/mp4')}
    data = {'duration': '30', 'test_all_languages': 'true'}
    response = await client.post(
        "http://langscale:8002/api/detect/upload",
        files=files,
        data=data
    )
```

**Avantage** : Le fichier est envoyé via HTTP, indépendamment de l'emplacement des pods.

## 📁 Gestion du stockage en Kubernetes

### Option 1 : Persistent Volumes (PV) partagés

```yaml
# pv-shared-storage.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: vidp-shared-storage
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany  # Partagé entre pods
  nfs:
    server: nfs-server.example.com
    path: /vidp/storage
```

**Cas d'usage** : Si vous avez un NFS ou un système de fichiers distribué.

### Option 2 : Upload HTTP (Recommandé) ✅

**Implémenté dans notre architecture actuelle** :
- Chaque service est indépendant
- Les fichiers transitent via HTTP
- Pas de dépendance sur un stockage partagé
- Plus flexible et scalable

## 🔄 Flux de traitement en production

### Étape 1 : Upload initial
```
Client → vidp-main-app (Pod A)
│
└─> Sauvegarde dans PV local du Pod A
    └─> Métadonnées dans MongoDB
```

### Étape 2 : Détection de langue
```
vidp-main-app (Pod A) → langscale (Pod B)
│
├─> Lit le fichier depuis son stockage local
├─> Upload le fichier via HTTP multipart/form-data
└─> langscale traite et retourne le résultat
    └─> vidp-main-app sauvegarde le résultat dans MongoDB
```

### Étape 3 : Compression (futur)
```
vidp-main-app (Pod A) → downscale (Pod C)
│
├─> Upload le fichier via HTTP
└─> downscale compresse et retourne l'URL
    └─> vidp-main-app sauvegarde dans MongoDB
```

## 🛠️ Configuration Kubernetes

### Services (ClusterIP)

```yaml
# vidp-main-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: vidp-main
  namespace: vidp-production
spec:
  selector:
    app: vidp-main
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

```yaml
# langscale-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: langscale
  namespace: vidp-production
spec:
  selector:
    app: langscale
  ports:
    - port: 8002
      targetPort: 8002
  type: ClusterIP
```

### Deployments

```yaml
# vidp-main-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vidp-main
  namespace: vidp-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vidp-main
  template:
    metadata:
      labels:
        app: vidp-main
    spec:
      containers:
      - name: vidp-main
        image: vidp/main-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: LANGSCALE_SERVICE_URL
          value: "http://langscale:8002"  # Service DNS interne
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: vidp-secrets
              key: mongodb-url
        volumeMounts:
        - name: video-storage
          mountPath: /app/local_storage
      volumes:
      - name: video-storage
        persistentVolumeClaim:
          claimName: vidp-main-storage
```

```yaml
# langscale-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langscale
  namespace: vidp-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: langscale
  template:
    metadata:
      labels:
        app: langscale
    spec:
      containers:
      - name: langscale
        image: vidp/langscale:latest
        ports:
        - containerPort: 8002
        volumeMounts:
        - name: langscale-storage
          mountPath: /app/language_detection_storage
      volumes:
      - name: langscale-storage
        emptyDir: {}  # Stockage éphémère (fichiers temporaires)
```

## 🔐 ConfigMaps et Secrets

```yaml
# vidp-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vidp-config
  namespace: vidp-production
data:
  LANGSCALE_SERVICE_URL: "http://langscale:8002"
  DOWNSCALE_SERVICE_URL: "http://downscale:8003"
  SUBTITLE_SERVICE_URL: "http://subtitle:8004"
  MICROSERVICES_TIMEOUT: "300"
```

```yaml
# vidp-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: vidp-secrets
  namespace: vidp-production
type: Opaque
data:
  mongodb-url: bW9uZ29kYjovL3VzZXI6cGFzc0Btb25nb2RiOjI3MDE3L3ZpZHBfZGI=  # base64
```

## 🌐 Ingress (Exposition externe)

```yaml
# vidp-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vidp-ingress
  namespace: vidp-production
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "500m"  # Max upload size
spec:
  rules:
  - host: api.vidp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vidp-main
            port:
              number: 8000
```

## 📊 Avantages de notre architecture

### ✅ Scalabilité
- Chaque service peut scaler indépendamment
- `kubectl scale deployment langscale --replicas=5`

### ✅ Isolation
- Un crash du service de détection n'affecte pas les autres
- Mises à jour indépendantes (rolling updates)

### ✅ Flexibilité
- Fonctionne avec ou sans stockage partagé
- Les fichiers transitent via HTTP (protocole standard)

### ✅ Monitoring
```yaml
# Service Monitor pour Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vidp-metrics
spec:
  selector:
    matchLabels:
      app: vidp-main
  endpoints:
  - port: metrics
    path: /metrics
```

## 🔍 Communication inter-services

### DNS interne Kubernetes
```python
# Dans vidp-main-app
settings.langscale_service_url = "http://langscale:8002"
#                                         ^^^^^^^^
#                                    Nom du Service K8s
```

### Service Discovery automatique
- Kubernetes DNS résout `langscale` → IP du Service
- Load balancing automatique entre les pods

## 📈 Performance et optimisation

### 1. Limite de ressources
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### 2. Readiness & Liveness Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/processing/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### 3. Horizontal Pod Autoscaling (HPA)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vidp-main-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vidp-main
  minReplicas: 2
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

```bash
# 1. Créer le namespace
kubectl create namespace vidp-production

# 2. Appliquer les secrets
kubectl apply -f k8s/secrets/

# 3. Déployer MongoDB
kubectl apply -f k8s/mongodb/

# 4. Déployer les microservices
kubectl apply -f k8s/deployments/

# 5. Créer les services
kubectl apply -f k8s/services/

# 6. Configurer l'ingress
kubectl apply -f k8s/ingress/

# 7. Vérifier les pods
kubectl get pods -n vidp-production
```

## 📝 Résumé des modifications pour Kubernetes

### ✅ Implémenté
1. **Upload HTTP** : Les fichiers transitent via HTTP, pas de chemins partagés
2. **Service Discovery** : URLs configurables via variables d'environnement
3. **Health checks** : Endpoints `/health` pour probes K8s
4. **Scalabilité** : Architecture stateless compatible avec HPA

### 🔄 À venir (pour compression et sous-titres)
- Même pattern d'upload HTTP
- ConfigMap centralisé pour toutes les URLs
- Monitoring et métriques Prometheus
- Distributed tracing (Jaeger/Zipkin)

## 🎯 Conclusion

Notre implémentation actuelle **est déjà prête pour Kubernetes** car :
- ✅ Pas de dépendance sur chemins de fichiers locaux
- ✅ Communication via HTTP standard
- ✅ Configuration externalisée
- ✅ Services indépendants et stateless

---

**Version** : 1.0.0  
**Date** : 2 Janvier 2026  
**Auteur** : VidP Team
