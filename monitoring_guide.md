# Guide Complet : Monitoring Kubernetes avec Prometheus et Grafana

## 📋 Table des Matières

1. [Architecture du Système de Monitoring](#architecture)
2. [Prérequis](#prérequis)
3. [Installation Étape par Étape](#installation)
4. [Configuration du Dashboard](#dashboard)
5. [Déploiement de Vos Applications](#deploiement)
6. [Utilisation et Maintenance](#utilisation)
7. [Dépannage](#dépannage)

---

## 🏗️ Architecture du Système de Monitoring {#architecture}

```
┌─────────────────────────────────────────────────────────────┐
│                    VOTRE NAVIGATEUR                         │
│                                                             │
│  http://localhost:3001  ← Interface Grafana                │
│  http://localhost:9090  ← Interface Prometheus (debug)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ (kubectl port-forward)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           CLUSTER KUBERNETES (Minikube)                     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  NAMESPACE: monitoring                             │    │
│  │                                                     │    │
│  │  ┌──────────────┐       ┌──────────────┐          │    │
│  │  │   Grafana    │◄──────│  Prometheus  │          │    │
│  │  │   (Pod)      │       │    (Pod)     │          │    │
│  │  └──────────────┘       └───────┬──────┘          │    │
│  │                                  │                 │    │
│  └──────────────────────────────────┼─────────────────┘    │
│                                     │                      │
│                                     │ (scrape métriques)   │
│                                     ↓                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  NAMESPACE: default (vos applications)             │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │animal-detect│  │  downscale  │  │ frontend  │  │    │
│  │  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │ langscale   │  │  main-app   │  │  mongodb  │  │    │
│  │  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  │                                                     │    │
│  │  ┌─────────────┐                                   │    │
│  │  │  subtitle   │                                   │    │
│  │  └─────────────┘                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Composants

- **Prometheus** : Collecte et stocke les métriques (CPU, RAM, réseau, etc.)
- **Grafana** : Visualise les métriques avec des dashboards interactifs
- **Node Exporter** : Collecte les métriques au niveau système (installé automatiquement)
- **kube-state-metrics** : Expose les métriques Kubernetes (installé automatiquement)

---

## ✅ Prérequis {#prérequis}

### Logiciels Requis

```bash
# 1. Minikube (Kubernetes local)
minikube version
# Si non installé : https://minikube.sigs.k8s.io/docs/start/

# 2. kubectl (CLI Kubernetes)
kubectl version --client
# Si non installé : https://kubernetes.io/docs/tasks/tools/

# 3. Helm (Gestionnaire de packages Kubernetes)
helm version
# Si non installé : https://helm.sh/docs/intro/install/
```

### Ressources Système Recommandées

- **CPU** : 4 cœurs minimum
- **RAM** : 8 GB minimum
- **Espace disque** : 20 GB disponibles

### Vérification de l'Environnement

```bash
# Démarrer Minikube avec les ressources appropriées
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Vérifier que le cluster fonctionne
kubectl cluster-info
kubectl get nodes

# Résultat attendu :
# NAME       STATUS   ROLES           AGE   VERSION
# minikube   Ready    control-plane   1m    v1.xx.x
```

---

## 🚀 Installation Étape par Étape {#installation}

### 🎯 Méthode Recommandée : Script Automatique

**Nous avons créé un script `setup-monitoring.sh` qui automatise tout le processus d'installation !**

#### Téléchargement du Script

Le script `setup-monitoring.sh` est disponible dans les artifacts de cette conversation. Sauvegardez-le dans votre répertoire de projet :

```bash
cd ~/Projet\ VidP/vidp-app/

# Sauvegarder le script (copier depuis l'artifact)
# Puis le rendre exécutable
chmod +x setup-monitoring.sh
```

#### Installation en Une Commande

```bash
# Installation complète automatique
./setup-monitoring.sh install
```

**Ce script fait automatiquement :**
- ✅ Vérification des prérequis (Helm, kubectl, Minikube)
- ✅ Ajout du référentiel Helm Prometheus
- ✅ Création du namespace monitoring
- ✅ Installation de Prometheus + Grafana
- ✅ Configuration optimisée pour VidP
- ✅ Affichage des identifiants Grafana

**⏱️ Durée totale** : 5-10 minutes

#### Autres Commandes Utiles du Script

```bash
# Vérifier le statut du monitoring
./setup-monitoring.sh status

# Accéder directement à Grafana (port-forward automatique)
./setup-monitoring.sh dashboard

# Tester que les métriques sont collectées
./setup-monitoring.sh test

# Instructions pour importer le dashboard
./setup-monitoring.sh import

# Désinstaller le monitoring
./setup-monitoring.sh uninstall

# Afficher l'aide
./setup-monitoring.sh help
```

---

### 📝 Méthode Manuelle (Alternative)

Si vous préférez installer manuellement sans le script, suivez ces étapes :

#### ÉTAPE 1 : Installation de Helm (si nécessaire)

```bash
# Télécharger et installer Helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Vérifier l'installation
helm version
```

### ÉTAPE 2 : Ajouter le Référentiel Prometheus

```bash
# Ajouter le repo Prometheus Community
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Mettre à jour les repos
helm repo update

# Vérifier que le repo est ajouté
helm repo list
```

**En cas d'erreur réseau** (timeout, connection refused) :

```bash
# Option A : Augmenter le timeout
export HELM_EXPERIMENTAL_OCI=1

# Option B : Téléchargement manuel
mkdir -p ~/helm-charts
cd ~/helm-charts
wget https://github.com/prometheus-community/helm-charts/releases/download/kube-prometheus-stack-56.0.0/kube-prometheus-stack-56.0.0.tgz

# Puis installer depuis le fichier local (étape 4)
```

### ÉTAPE 3 : Créer le Namespace Monitoring

```bash
# Créer un namespace dédié pour le monitoring
kubectl create namespace monitoring

# Vérifier la création
kubectl get namespaces | grep monitoring
```

### ÉTAPE 4 : Installer la Stack Prometheus + Grafana

```bash
# Installation depuis le repo (méthode recommandée)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=7d \
  --set grafana.adminPassword=admin123

# OU depuis le fichier local (si téléchargement manuel)
cd ~/helm-charts
helm install prometheus kube-prometheus-stack-56.0.0.tgz \
  --namespace monitoring \
  --set grafana.adminPassword=admin123
```

**Options expliquées :**
- `--namespace monitoring` : Installe dans le namespace dédié
- `--set prometheus.prometheusSpec.retention=7d` : Garde 7 jours de données
- `--set grafana.adminPassword=admin123` : Définit le mot de passe admin

**⏱️ Temps d'installation** : 3-5 minutes

### ÉTAPE 5 : Vérifier l'Installation

```bash
# Vérifier que tous les pods sont en cours d'exécution
kubectl get pods -n monitoring

# Attendre que tous les pods soient "Running" (peut prendre 2-3 minutes)
kubectl wait --for=condition=Ready pods --all -n monitoring --timeout=300s
```

**Résultat attendu :**

```
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          2m
prometheus-grafana-xxxxxxxxx-xxxxx                       3/3     Running   0          2m
prometheus-kube-prometheus-operator-xxxxxxxxx-xxxxx      1/1     Running   0          2m
prometheus-kube-state-metrics-xxxxxxxxx-xxxxx            1/1     Running   0          2m
prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          2m
prometheus-prometheus-node-exporter-xxxxx                1/1     Running   0          2m
```

**En cas d'erreur** :

```bash
# Vérifier les logs d'un pod en erreur
kubectl logs -n monitoring <nom-du-pod>

# Décrire le pod pour voir les événements
kubectl describe pod -n monitoring <nom-du-pod>
```

---

## 🎯 Workflow Complet Recommandé

### Option 1 : Avec le Script Automatique (⭐ Recommandé)

```bash
# 1. Déployer VidP
cd ~/Projet\ VidP/vidp-app/
./deploy-minikube.sh all

# 2. Installer le monitoring
./setup-monitoring.sh install

# 3. Accéder à Grafana
./setup-monitoring.sh dashboard

# 4. Importer vidp-dashboard.json dans Grafana
```

**Durée totale** : 25-30 minutes (dont 15-20 min pour VidP)

### Option 2 : Installation Manuelle

Si vous préférez suivre les étapes manuelles, continuez avec les ÉTAPES 6-8 ci-dessous.

---

### ÉTAPE 6 : Récupérer les Identifiants Grafana

```bash
# Récupérer le mot de passe admin de Grafana
kubectl get secret --namespace monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

**Notez ce mot de passe** (ou utilisez `admin123` si vous l'avez défini à l'étape 4).

### ÉTAPE 7 : Accéder à Grafana

#### Option A : Via Port-Forward (Recommandé pour le développement)

```bash
# Dans un terminal dédié (laissez-le tourner)
kubectl port-forward --namespace monitoring svc/prometheus-grafana 3001:80
```

**Accédez à** : http://localhost:3001
- **Username** : `admin`
- **Password** : (celui récupéré à l'étape 6)

#### Option B : Via Service NodePort (Pour un accès permanent)

```bash
# Exposer Grafana via NodePort
kubectl patch svc prometheus-grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'

# Récupérer l'URL d'accès
minikube service prometheus-grafana -n monitoring --url
```

**Note** : Le port-forward est plus simple pour commencer.

### ÉTAPE 8 : Accéder à Prometheus (Optionnel - pour debug)

```bash
# Dans un autre terminal
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

**Accédez à** : http://localhost:9090

Testez cette requête dans la barre de recherche :
```promql
up
```

Vous devriez voir tous les services monitorés.

---

## 📊 Configuration du Dashboard {#dashboard}

### Méthode 1 : Importer le Dashboard JSON (Recommandé)

1. **Téléchargez le fichier** `vidp-dashboard.json` (fourni dans l'artifact)

2. **Dans Grafana** (http://localhost:3001) :
   - Cliquez sur **☰** (menu hamburger) en haut à gauche
   - **Dashboards** → **New** → **Import**
   - Cliquez sur **Upload JSON file**
   - Sélectionnez `vidp-dashboard.json`
   - Cliquez sur **Load**
   - Sélectionnez **Prometheus** comme source de données
   - Cliquez sur **Import**

3. **Résultat** : Vous avez un dashboard complet avec 8 panels !

### Méthode 2 : Créer Manuellement (Pour apprentissage)

#### Panel 1 : Paquets Réseau Reçus

1. **Dashboards** → **New** → **New Dashboard**
2. **Add visualization**
3. Sélectionnez **Prometheus** comme data source
4. Dans le champ **Query**, entrez :

```promql
sum by (pod) (
  rate(container_network_receive_packets_total{
    namespace="default", 
    pod=~"(animal-detect|downscale|frontend|langscale|main-app|mongodb|subtitle).*"
  }[1m])
)
```

5. **Options** :
   - **Title** : "Paquets Réseau Reçus par Seconde"
   - **Legend** : `{{pod}}`
   - **Unit** : `packets/sec (pps)`

6. **Save** en haut à droite

#### Panel 2 : Utilisation CPU

Répétez les étapes 2-6 avec cette requête :

```promql
sum by (pod) (
  rate(container_cpu_usage_seconds_total{
    namespace="default",
    pod=~"(animal-detect|downscale|frontend|langscale|main-app|mongodb|subtitle).*"
  }[1m])
) * 100
```

- **Unit** : `percent (0-100)`

#### Panel 3 : Utilisation Mémoire

```promql
sum by (pod) (
  container_memory_working_set_bytes{
    namespace="default",
    pod=~"(animal-detect|downscale|frontend|langscale|main-app|mongodb|subtitle).*"
  }
) / 1024 / 1024
```

- **Unit** : `megabytes (MB)`

### Personnalisation du Dashboard

#### Modifier le Namespace

Si vos pods ne sont PAS dans le namespace `default`, modifiez toutes les requêtes :

```promql
# Remplacer
namespace="default"

# Par (exemple)
namespace="vidp-processing"
```

#### Ajouter d'Autres Services

Modifiez le regex des noms de pods :

```promql
# Remplacer
pod=~"(animal-detect|downscale|frontend|...).*"

# Par (ajoutez vos services)
pod=~"(service1|service2|service3).*"
```

---

## 🔧 Déploiement de Vos Applications {#deploiement}

### ÉTAPE 1 : Déployer VidP avec le Script Automatique

Vous avez un script de déploiement automatique `deploy-minikube.sh` qui facilite grandement le processus.

#### Option A : Déploiement Complet (Recommandé)

```bash
# Depuis la racine du projet VidP
cd ~/Projet\ VidP/vidp-app/

# Déploiement complet : start + build + deploy
./deploy-minikube.sh all
```

**⏱️ Durée totale** : 15-20 minutes (premier déploiement)

#### Option B : Déploiement Étape par Étape

```bash
# 1. Démarrer Minikube (si pas déjà fait)
./deploy-minikube.sh start

# 2. Construire les images Docker
./deploy-minikube.sh build

# 3. Déployer sur Kubernetes avec Kustomize (recommandé)
./deploy-minikube.sh kustomize

# OU déploiement manuel
./deploy-minikube.sh deploy
```

### ÉTAPE 2 : Vérifier les Déploiements

```bash
# Vérifier que tous les pods sont "Running" dans le namespace vidp
kubectl get pods -n vidp

# OU avec le script
./deploy-minikube.sh status

# OU pour un health check complet
./deploy-minikube.sh health
```

**Résultat attendu dans le namespace `vidp` :**

```
NAME                              READY   STATUS    RESTARTS   AGE
animal-detect-xxxxx-xxxxx         1/1     Running   0          2m
downscale-xxxxx-xxxxx             1/1     Running   0          2m
frontend-xxxxx-xxxxx              1/1     Running   0          1m
langscale-xxxxx-xxxxx             1/1     Running   0          2m
main-app-xxxxx-xxxxx              1/1     Running   0          1m
mongodb-xxxxx-xxxxx               1/1     Running   0          3m
subtitle-xxxxx-xxxxx              1/1     Running   0          2m
```

**⚠️ IMPORTANT** : Vos pods sont dans le namespace **`vidp`** et non `default`.

### ÉTAPE 3 : Attendre la Collecte des Métriques

**⏱️ Prometheus collecte les métriques toutes les 30 secondes.**

Attendez 1-2 minutes, puis actualisez votre dashboard Grafana.

### ÉTAPE 4 : Vérifier les Métriques

Dans Grafana, vous devriez maintenant voir :
- ✅ Graphiques avec des données
- ✅ Courbes pour chaque pod
- ✅ Légendes avec les noms des pods

**Si aucune donnée n'apparaît**, consultez la section [Dépannage](#dépannage).

---

## 📈 Utilisation et Maintenance {#utilisation}

### Accès Quotidien au Dashboard

```bash
# Terminal 1 : Port-forward Grafana
kubectl port-forward --namespace monitoring svc/prometheus-grafana 3001:80

# Terminal 2 : Port-forward Prometheus (optionnel)
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

Puis ouvrez : http://localhost:3001

### Requêtes PromQL Utiles

#### Détecter les Pods qui Consomment le Plus

**CPU Top 3 :**
```promql
topk(3, sum by (pod) (
  rate(container_cpu_usage_seconds_total{namespace="default"}[5m])
))
```

**Mémoire Top 3 :**
```promql
topk(3, sum by (pod) (
  container_memory_working_set_bytes{namespace="default"}
))
```

#### Alertes Automatiques

**Pods qui redémarrent trop souvent :**
```promql
sum by (pod) (
  kube_pod_container_status_restarts_total{namespace="default"}
) > 5
```

**CPU > 80% :**
```promql
sum by (pod) (
  rate(container_cpu_usage_seconds_total{namespace="default"}[1m])
) * 100 > 80
```

### Exporter un Dashboard

1. Dans Grafana, ouvrez votre dashboard
2. Cliquez sur **⚙️** (Settings) en haut
3. **JSON Model** dans le menu de gauche
4. **Copy to Clipboard**
5. Sauvegardez dans un fichier `.json`

### Sauvegarder la Configuration

```bash
# Sauvegarder tous les déploiements
kubectl get all -n monitoring -o yaml > monitoring-backup.yaml

# Sauvegarder vos applications
kubectl get all -o yaml > apps-backup.yaml
```

---

## 🔍 Dépannage {#dépannage}

### Problème : Aucune Donnée dans Grafana

#### Vérification 1 : Prometheus Collecte-t-il des Métriques ?

```bash
# Accéder à Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```

Ouvrez http://localhost:9090 et testez :
```promql
container_network_receive_packets_total
```

**Si aucun résultat** :
- Prometheus ne collecte pas les métriques conteneur
- Vérifiez que `kube-state-metrics` tourne :

```bash
kubectl get pods -n monitoring | grep kube-state-metrics
```

#### Vérification 2 : Le Namespace est-il Correct ?

```bash
# Lister tous les namespaces avec des pods
kubectl get pods --all-namespaces

# Identifier le namespace de vos pods
kubectl get pods -A | grep animal-detect
```

Modifiez le dashboard avec le bon namespace.

#### Vérification 3 : Grafana Peut-il Accéder à Prometheus ?

Dans Grafana :
1. **☰** → **Connections** → **Data sources**
2. Cliquez sur **Prometheus**
3. Scrollez en bas et cliquez sur **Save & Test**

Vous devriez voir : ✅ "Data source is working"

### Problème : Port 3001 Déjà Utilisé

```bash
# Trouver le processus
sudo lsof -i :3001

# Tuer le processus (remplacez PID)
sudo kill <PID>

# OU utiliser un autre port
kubectl port-forward --namespace monitoring svc/prometheus-grafana 3002:80
```

### Problème : Pods en CrashLoopBackOff

```bash
# Voir les logs du pod
kubectl logs <nom-du-pod>

# Voir les événements
kubectl describe pod <nom-du-pod>

# Redémarrer le pod
kubectl delete pod <nom-du-pod>
```

### Problème : Helm Timeout ou Erreur Réseau

```bash
# Augmenter le timeout Helm
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --timeout 10m

# OU télécharger manuellement
wget https://github.com/prometheus-community/helm-charts/releases/download/kube-prometheus-stack-56.0.0/kube-prometheus-stack-56.0.0.tgz

helm install prometheus ./kube-prometheus-stack-56.0.0.tgz --namespace monitoring
```

### Problème : Dashboard Vide Après Import

1. Vérifiez que vous avez sélectionné **Prometheus** comme data source lors de l'import
2. Modifiez le dashboard :
   - Cliquez sur le titre d'un panel → **Edit**
   - Vérifiez que la data source est bien **Prometheus**
   - Cliquez sur **Query inspector** → **Refresh**

### Problème : Métriques Réseau Non Disponibles

Certaines métriques réseau nécessitent des configurations spéciales. Si `container_network_*` n'existe pas :

**Alternative - Utiliser les métriques nœud :**

```promql
# Trafic total du nœud
rate(node_network_receive_packets_total{device!="lo"}[1m])
```

---

## 📚 Commandes de Référence Rapide

### Scripts de Déploiement VidP

```bash
# Déploiement complet VidP
./deploy-minikube.sh all

# Vérifier l'état de VidP
./deploy-minikube.sh status

# Rebuild un service spécifique
./deploy-minikube.sh rebuild main-app

# Voir les logs
./deploy-minikube.sh logs main-app

# Health check
./deploy-minikube.sh health
```

### Scripts de Monitoring

```bash
# Installation automatique
./setup-monitoring.sh install

# Accéder à Grafana (port-forward)
./setup-monitoring.sh dashboard

# Vérifier le statut
./setup-monitoring.sh status

# Tester les métriques
./setup-monitoring.sh test

# Désinstaller
./setup-monitoring.sh uninstall
```

### Gestion du Cluster

```bash
# Démarrer Minikube
minikube start --cpus=4 --memory=8192

# Arrêter Minikube (garde les données)
minikube stop

# Supprimer le cluster (⚠️ SUPPRIME TOUT)
minikube delete

# Statut du cluster
kubectl cluster-info
kubectl get nodes
```

### Gestion du Monitoring

```bash
# Vérifier Prometheus et Grafana
kubectl get pods -n monitoring

# Redémarrer Grafana
kubectl rollout restart deployment prometheus-grafana -n monitoring

# Voir les logs Prometheus
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus

# Désinstaller la stack monitoring
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring
```

### Gestion des Applications

```bash
# Déployer toutes les apps
kubectl apply -f k8s/

# Voir l'état des pods
kubectl get pods -w

# Voir les logs d'un pod
kubectl logs -f <nom-pod>

# Redémarrer un déploiement
kubectl rollout restart deployment <nom-deployment>

# Supprimer toutes les apps
kubectl delete -f k8s/
```

### Port-Forwarding

```bash
# Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80

# Prometheus
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090

# Vos applications (exemple)
kubectl port-forward svc/frontend 8080:80
```

---

## 🎯 Checklist Finale

Avant de dire que tout fonctionne :

- [ ] Minikube démarré (`minikube status`)
- [ ] Helm installé (`helm version`)
- [ ] Namespace monitoring créé (`kubectl get ns monitoring`)
- [ ] Prometheus + Grafana déployés (`kubectl get pods -n monitoring`)
- [ ] Tous les pods monitoring sont "Running"
- [ ] Grafana accessible sur http://localhost:3001
- [ ] Dashboard importé et visible
- [ ] Vos 7 applications déployées (`kubectl get pods`)
- [ ] Métriques visibles dans le dashboard (après 2 min)
- [ ] Pas d'erreurs dans les logs

---

## 📖 Pour Aller Plus Loin

### Ressources Officielles

- **Prometheus** : https://prometheus.io/docs/
- **Grafana** : https://grafana.com/docs/
- **Kubernetes** : https://kubernetes.io/docs/
- **Helm** : https://helm.sh/docs/

### Concepts Avancés

1. **Alerting** : Configurer des alertes email/Slack avec Alertmanager
2. **Retention** : Augmenter la durée de conservation des données
3. **Service Monitors** : Exposer des métriques custom depuis vos apps
4. **Federation** : Connecter plusieurs clusters Prometheus
5. **Dashboards communautaires** : https://grafana.com/grafana/dashboards/

---

## ✅ Résumé en 10 Commandes

### Avec le Script Automatique (⭐ Méthode Recommandée)

```bash
# 1. Démarrer Minikube
minikube start --cpus=4 --memory=8192

# 2. Déployer VidP (vos 7 services)
cd ~/Projet\ VidP/vidp-app/
./deploy-minikube.sh all

# 3. Télécharger setup-monitoring.sh (depuis l'artifact)
# Puis le rendre exécutable
chmod +x setup-monitoring.sh

# 4. Installer le monitoring (une seule commande!)
./setup-monitoring.sh install

# 5. Vérifier que tout fonctionne
./setup-monitoring.sh status

# 6. Accéder à Grafana
./setup-monitoring.sh dashboard

# 7. Télécharger vidp-dashboard.json (depuis l'artifact)

# 8. Importer le dashboard dans Grafana
# Menu ☰ → Dashboards → New → Import → Upload vidp-dashboard.json

# 9. Vérifier les pods
kubectl get pods -n vidp
kubectl get pods -n monitoring

# 10. Profiter de votre monitoring! 🎉
```

**🎉 Votre monitoring est opérationnel en 30 minutes !**

---

### Avec la Méthode Manuelle (Alternative)

```bash
# 1. Démarrer Minikube
minikube start --cpus=4 --memory=8192

# 2. Installer Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 3. Déployer VidP (vos 7 services)
cd ~/Projet\ VidP/vidp-app/
./deploy-minikube.sh all

# 4. Ajouter le repo Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 5. Créer le namespace monitoring
kubectl create namespace monitoring

# 6. Installer Prometheus + Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin123

# 7. Récupérer le mot de passe Grafana
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d

# 8. Accéder à Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80

# 9. Importer vidp-dashboard.json dans Grafana
# http://localhost:3001

# 10. Vérifier que tout fonctionne
kubectl get pods -n vidp
kubectl get pods -n monitoring
```

**🎉 Votre monitoring est opérationnel !**

---

## 🚀 Workflow Rapide (Si VidP est déjà déployé)

Si vous avez déjà déployé VidP avec `./deploy-minikube.sh all`, le monitoring s'installe en 3 étapes :

```bash
# 1. Télécharger et rendre exécutable le script
chmod +x setup-monitoring.sh

# 2. Installation automatique (5-10 minutes)
./setup-monitoring.sh install

# 3. Accéder à Grafana et importer le dashboard
./setup-monitoring.sh dashboard
# Puis importer vidp-dashboard.json dans l'interface
```

**Durée totale** : 10 minutes ⚡

---

## 📦 Fichiers Fournis dans les Artifacts

Cette conversation fournit 3 artifacts essentiels :

1. **`vidp-dashboard.json`** - Dashboard Grafana prêt à importer
   - 8 panels de monitoring
   - Configuré pour le namespace `vidp`
   - Toutes les métriques des 7 services

2. **`setup-monitoring.sh`** - Script d'installation automatique
   - Installation en une commande
   - Gestion complète du monitoring
   - Commandes de diagnostic intégrées

3. **`MONITORING_GUIDE.md`** - Ce guide complet
   - Documentation pas à pas
   - Dépannage
   - Bonnes pratiques

---

**Auteur** : Guide créé pour le projet VidP  
**Date** : Janvier 2026  
**Version** : 2.0 (Intégré avec deploy-minikube.sh)