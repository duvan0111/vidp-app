# 🚀 Guide de Déploiement VidP sur Minikube (Windows)

Ce guide explique comment déployer l’application **VidP** sur **Minikube sous Windows**, en utilisant **PowerShell** et le script `deploy-minikube.ps1`.

---

## 📋 Prérequis (Windows)

- Windows 10 / 11 (64 bits)  
- Docker Desktop (WSL2 recommandé)  
- Minikube installé et accessible dans le PATH  
- kubectl installé et accessible dans le PATH  
- PowerShell 5+ ou PowerShell 7+  
- **8 GB de RAM minimum**  
- **4 CPUs minimum**

### Vérification
```powershell
docker version
minikube version
kubectl version --client
```

---

## 🔐 Autoriser l’exécution du script

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 🎯 Démarrage rapide

### Déploiement automatique (recommandé)

```powershell
.\deploy-minikube.ps1 all
```

Cette commande :
1. Démarre Minikube  
2. Construit toutes les images Docker  
3. Déploie tous les services Kubernetes  

---

## 📚 Commandes principales

### Gestion du cluster

| Commande | Description |
|--------|------------|
| start | Démarrer Minikube |
| stop | Arrêter Minikube |
| status | Statut du cluster |

```powershell
.\deploy-minikube.ps1 start
```

---

### Build et déploiement

```powershell
.\deploy-minikube.ps1 build
.\deploy-minikube.ps1 deploy
.\deploy-minikube.ps1 kustomize
```

---

### Logs et debug

```powershell
.\deploy-minikube.ps1 logs main-app
.\deploy-minikube.ps1 health
```

---

## 🌐 Accès aux services

### URLs Minikube
```powershell
.\deploy-minikube.ps1 urls
```

### Port-forward
```powershell
.\deploy-minikube.ps1 forward
```

- Frontend : http://localhost:3000  
- API : http://localhost:8000  

---

## 🏗️ Architecture

```
Namespace: vidp
├─ MongoDB
├─ Microservices
├─ Main-App (FastAPI)
├─ Frontend (Next.js)
└─ Ingress
```

---

## 🐛 Dépannage

### Minikube ne démarre pas
```powershell
minikube delete
minikube start --driver=docker --cpus=4 --memory=8192
```

---

## 📝 Notes importantes

- `imagePullPolicy: Never`
- Images Docker construites dans Minikube
- Docker Desktop doit rester ouvert

---

## ✅ Conclusion

Guide officiel **Windows** pour le déploiement VidP avec Minikube et PowerShell.

---
VidP Team – Cloud Computing Project
