
# Guide Monitoring Kubernetes – Windows (PowerShell)

Ce guide est une **adaptation Windows** du guide monitoring VidP.
Toutes les commandes sont compatibles **PowerShell**, **Windows 10/11**, **Minikube**, **kubectl** et **Helm**.

---

## 🧰 Prérequis Windows

### Logiciels requis

Installez **avant de commencer** :

- **Docker Desktop (avec Kubernetes désactivé)**
  https://www.docker.com/products/docker-desktop/

- **Minikube**
  https://minikube.sigs.k8s.io/docs/start/

- **kubectl**
  https://kubernetes.io/docs/tasks/tools/

- **Helm**
  https://helm.sh/docs/intro/install/

Vérification dans PowerShell :

```powershell
minikube version
kubectl version --client
helm version
```

---

## 🚀 Démarrage de Minikube (Windows)

```powershell
minikube start --cpus=4 --memory=8192 --disk-size=20g
kubectl get nodes
```

Statut attendu : `Ready`

---

## 📦 Installation du Monitoring (Automatique – Recommandé)

### Script Windows

Utilisez le script **PowerShell** :

```
setup-monitoring.ps1
```

### Autoriser l’exécution des scripts (1 seule fois)

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Installation complète

```powershell
.\setup-monitoring.ps1 install
```

⏱️ **Durée** : 5 à 10 minutes

Ce script :
- Vérifie Minikube, kubectl, Helm
- Crée le namespace `monitoring`
- Installe Prometheus + Grafana
- Affiche les identifiants Grafana

---

## 📊 Accéder à Grafana (Windows)

```powershell
.\setup-monitoring.ps1 dashboard
```

Puis ouvrez :  
👉 http://localhost:3001

Identifiants :
- **Username** : `admin`
- **Password** : affiché dans le terminal

---

## 📈 Importer le Dashboard Grafana

1. Ouvrez Grafana
2. Menu ☰ → **Dashboards** → **New** → **Import**
3. Importez : `vidp-dashboard.json`
4. Sélectionnez la datasource **Prometheus**
5. Cliquez sur **Import**

---

## 🔍 Vérifier l’état du Monitoring

```powershell
.\setup-monitoring.ps1 status
```

---

## 🧪 Tester la collecte des métriques

```powershell
.\setup-monitoring.ps1 test
```

Prometheus doit répondre correctement.

---

## 🔧 Accéder à Prometheus (Debug)

```powershell
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

Puis :  
👉 http://localhost:9090

Test PromQL :

```promql
up
```

---

## 🛑 Désinstaller le Monitoring

```powershell
.\setup-monitoring.ps1 uninstall
```

---

## ⚠️ Problèmes Courants sous Windows

### Port déjà utilisé

Changer le port Grafana :

```powershell
kubectl port-forward -n monitoring svc/prometheus-grafana 3002:80
```

### Aucun graphique visible

- Attendre **2 minutes**
- Vérifier le namespace (`vidp` ou `default`)
- Vérifier la datasource Prometheus dans Grafana

---

## ✅ Checklist Finale

- [ ] Minikube démarré
- [ ] Helm / kubectl fonctionnels
- [ ] Monitoring installé
- [ ] Grafana accessible
- [ ] Dashboard importé
- [ ] Métriques visibles

---

## 🎉 Résumé Rapide

```powershell
minikube start --cpus=4 --memory=8192
.\setup-monitoring.ps1 install
.\setup-monitoring.ps1 dashboard
```

Votre monitoring est **opérationnel sous Windows** 🚀

---

**Projet** : VidP  
**OS** : Windows  
**Shell** : PowerShell  
**Version** : Windows Edition  
