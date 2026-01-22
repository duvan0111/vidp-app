<# 
deploy-minikube.ps1
Script de déploiement VidP sur Minikube (Windows / PowerShell)

Usage:
  .\deploy-minikube.ps1 <commande> [service]

Commandes:
  start          - Démarrer Minikube
  stop           - Arrêter Minikube
  status         - Afficher le statut
  build          - Construire les images Docker
  deploy         - Déployer sur Kubernetes (manuel)
  kustomize      - Déployer avec Kustomize (recommandé)
  delete         - Supprimer le déploiement
  logs <svc>     - Afficher les logs d'un service
  rebuild <svc>  - Rebuild et redéployer un service
  health         - Vérifier la santé des services
  dashboard      - Ouvrir le dashboard Kubernetes
  urls           - Afficher les URLs des services
  forward        - Port-forward des services
  all            - start + build + deploy
  help           - Afficher cette aide

Pré-requis (Windows):
  - Docker Desktop (ou autre driver Minikube)
  - minikube, kubectl, docker dans le PATH
#>

[CmdletBinding()]
param(
  [Parameter(Position=0)]
  [string]$Command = "help",

  [Parameter(Position=1)]
  [string]$Service
)

$ErrorActionPreference = "Stop"

# Configuration
$NAMESPACE = "vidp"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Helpers (affichage) ---
function Write-Info($msg)    { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success($msg) { Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warn($msg)    { Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Err($msg)     { Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Write-Header($title) {
  Write-Host ""
  Write-Host "========================================" -ForegroundColor Cyan
  Write-Host " $title" -ForegroundColor Cyan
  Write-Host "========================================" -ForegroundColor Cyan
  Write-Host ""
}

# --- Checks ---
function Assert-CommandExists($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Err "$name n'est pas installé ou introuvable dans le PATH. $hint"
    exit 1
  }
}

function Check-Prereqs {
  Assert-CommandExists "minikube" "Installez Minikube: https://minikube.sigs.k8s.io/docs/start/"
  Assert-CommandExists "kubectl"  "Installez kubectl: https://kubernetes.io/docs/tasks/tools/"
  Assert-CommandExists "docker"   "Installez Docker Desktop: https://www.docker.com/products/docker-desktop/"
}

# --- Minikube ---
function Start-Minikube {
  Write-Header "Démarrage de Minikube"

  $status = ""
  try { $status = & minikube status 2>$null | Out-String } catch { $status = "" }

  if ($status -match "Running") {
    Write-Info "Minikube est déjà en cours d'exécution"
  } else {
    $driver = $env:MINIKUBE_DRIVER
    if ([string]::IsNullOrWhiteSpace($driver)) { $driver = "docker" }
    Write-Info "Démarrage de Minikube (cpus=4, memory=8192, driver=$driver)..."
    & minikube start --cpus=4 --memory=8192 --driver=$driver | Out-Host
  }

  Write-Info "Activation des addons..."
  & minikube addons enable ingress        | Out-Host
  & minikube addons enable metrics-server | Out-Host
  & minikube addons enable dashboard      | Out-Host

  Write-Success "Minikube démarré avec succès"
}

function Stop-Minikube {
  Write-Header "Arrêt de Minikube"
  & minikube stop | Out-Host
  Write-Success "Minikube arrêté"
}

function Status-Minikube {
  Write-Header "Statut de Minikube"
  & minikube status | Out-Host
  Write-Host ""

  Write-Info "Pods dans le namespace $NAMESPACE:"
  try { & kubectl get pods -n $NAMESPACE | Out-Host } catch { Write-Warn "Namespace $NAMESPACE non trouvé" }
  Write-Host ""

  Write-Info "Services dans le namespace $NAMESPACE:"
  try { & kubectl get services -n $NAMESPACE | Out-Host } catch { Write-Warn "Namespace $NAMESPACE non trouvé" }
}

# --- Docker in Minikube ---
function Use-MinikubeDocker {
  # Equivalent PowerShell de: eval $(minikube docker-env)
  Write-Info "Configuration de Docker pour Minikube..."
  $envCmd = & minikube docker-env --shell powershell
  if (-not $envCmd) { throw "Impossible de récupérer 'minikube docker-env'." }
  Invoke-Expression $envCmd
}

# --- Build ---
function Build-Images {
  Write-Header "Construction des images Docker"

  Use-MinikubeDocker

  Write-Info "Construction de vidp/langscale..."
  & docker build -t "vidp/langscale:latest" (Join-Path $PROJECT_DIR "app_langscale") | Out-Host

  Write-Info "Construction de vidp/downscale..."
  & docker build -t "vidp/downscale:latest" (Join-Path $PROJECT_DIR "app_downscale") | Out-Host

  Write-Info "Construction de vidp/subtitle..."
  & docker build -t "vidp/subtitle:latest" (Join-Path $PROJECT_DIR "app_subtitle") | Out-Host

  Write-Info "Construction de vidp/animal-detect..."
  & docker build -t "vidp/animal-detect:latest" (Join-Path $PROJECT_DIR "app_animal_detect") | Out-Host

  Write-Info "Construction de vidp/main-app..."
  & docker build -t "vidp/main-app:latest" (Join-Path $PROJECT_DIR "vidp-main-app/vidp-fastapi-service") | Out-Host

  Write-Info "Construction de vidp/frontend..."
  & docker build -t "vidp/frontend:latest" (Join-Path $PROJECT_DIR "vidp-main-app/vidp-nextjs-web") | Out-Host

  Write-Success "Toutes les images ont été construites"

  Write-Info "Images disponibles (filtrées sur 'vidp'):"
  & docker images | Select-String -Pattern "vidp" | ForEach-Object { $_.Line } | Out-Host
}

# --- Deploy (manifests) ---
function Deploy-K8s {
  Write-Header "Déploiement sur Kubernetes"

  & kubectl config use-context minikube | Out-Host

  Write-Info "Création du namespace..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/namespace.yaml") | Out-Host

  Write-Info "Application des ConfigMaps et Secrets..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/configmap.yaml") | Out-Host
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/secrets.yaml")   | Out-Host

  Write-Info "Déploiement de MongoDB..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/mongodb.yaml") | Out-Host

  Write-Info "Attente que MongoDB soit prêt..."
  try { & kubectl wait --for=condition=ready pod -l app=mongodb -n $NAMESPACE --timeout=120s | Out-Host } catch { }

  Write-Info "Déploiement des microservices..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/langscale.yaml")     | Out-Host
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/downscale.yaml")     | Out-Host
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/subtitle.yaml")      | Out-Host
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/animal-detect.yaml") | Out-Host

  Write-Info "Attente que les microservices démarrent..."
  Start-Sleep -Seconds 10

  Write-Info "Déploiement de l'application principale..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/main-app.yaml") | Out-Host

  Write-Info "Déploiement du frontend..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/frontend.yaml") | Out-Host

  Write-Info "Attente que les microservices soient prêts..."
  Start-Sleep -Seconds 5

  Write-Info "Configuration de l'Ingress..."
  & kubectl apply -f (Join-Path $PROJECT_DIR "k8s/ingress.yaml") | Out-Host

  Write-Success "Déploiement terminé"

  Write-Info "Attente que tous les pods soient prêts..."
  Start-Sleep -Seconds 10
  & kubectl get pods -n $NAMESPACE | Out-Host

  Write-Host ""
  Write-Info "Pour accéder aux services:"
  $frontendUrl = ""
  $apiUrl = ""
  try { $frontendUrl = (& minikube service frontend-service -n $NAMESPACE --url 2>$null | Select-Object -First 1) } catch { $frontendUrl = "En attente..." }
  try { $apiUrl      = (& minikube service main-app-service -n $NAMESPACE --url 2>$null | Select-Object -First 1) } catch { $apiUrl = "En attente..." }
  Write-Host "  - Frontend: $frontendUrl"
  Write-Host "  - API:      $apiUrl"
  Write-Host ""
  Write-Info "Ou utilisez: minikube tunnel (dans un terminal séparé)"
}

function Deploy-Kustomize {
  Write-Header "Déploiement avec Kustomize"
  & kubectl config use-context minikube | Out-Host
  Write-Info "Application de la configuration Kustomize..."
  & kubectl apply -k (Join-Path $PROJECT_DIR "k8s/") | Out-Host
  Write-Success "Déploiement Kustomize terminé"
}

function Delete-K8s {
  Write-Header "Suppression du déploiement"
  Write-Warn "Suppression de toutes les ressources dans le namespace $NAMESPACE..."
  & kubectl delete namespace $NAMESPACE --ignore-not-found=true | Out-Host
  Write-Success "Déploiement supprimé"
}

# --- Logs ---
function Show-Logs([string]$svc) {
  Write-Header "Logs des services"

  if ([string]::IsNullOrWhiteSpace($svc)) {
    Write-Info "Usage: .\deploy-minikube.ps1 logs <service>"
    Write-Info "Services disponibles: mongodb, langscale, downscale, subtitle, animal-detect, main-app, frontend"
    Write-Info ""
    Write-Info "Tous les pods:"
    & kubectl get pods -n $NAMESPACE | Out-Host
    return
  }

  Write-Info "Logs de $svc:"
  & kubectl logs -f -l ("app=" + $svc) -n $NAMESPACE --tail=100 | Out-Host
}

# --- Dashboard ---
function Open-Dashboard {
  Write-Header "Ouverture du Dashboard Kubernetes"
  Start-Process -FilePath "minikube" -ArgumentList "dashboard" -WindowStyle Normal | Out-Null
}

# --- URLs ---
function Access-Services {
  Write-Header "URLs des Services"

  Write-Info "Frontend:"
  & minikube service frontend-service -n $NAMESPACE --url | Out-Host

  Write-Info "API Backend:"
  & minikube service main-app-service -n $NAMESPACE --url | Out-Host

  Write-Host ""
  Write-Info "Pour un accès via tunnel (recommandé):"
  Write-Host "  1. Ouvrez un nouveau terminal PowerShell en mode Administrateur"
  Write-Host "  2. Exécutez: minikube tunnel"
  Write-Host "  3. Ajoutez à C:\Windows\System32\drivers\etc\hosts :"
  $ip = (& minikube ip)
  Write-Host "     $ip vidp.local api.vidp.local"
}

# --- Port-forward ---
function Port-Forward {
  Write-Header "Port-Forward des Services"

  Write-Info "Démarrage des port-forwards..."
  Write-Info "  - API:      localhost:8000"
  Write-Info "  - Frontend: localhost:3000"
  Write-Info ""
  Write-Info "Appuyez sur Ctrl+C pour arrêter"

  $job1 = Start-Job -ScriptBlock { kubectl port-forward svc/main-app-service 8000:8000 -n vidp } 
  $job2 = Start-Job -ScriptBlock { kubectl port-forward svc/frontend-service 3000:3000 -n vidp }

  try {
    Wait-Job -Job $job1, $job2 | Out-Null
  } finally {
    Get-Job -State Running | Stop-Job -Force -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
  }
}

# --- Rebuild service ---
function Rebuild-Service([string]$svc) {
  if ([string]::IsNullOrWhiteSpace($svc)) {
    Write-Err "Usage: .\deploy-minikube.ps1 rebuild <service>"
    Write-Info "Services disponibles: langscale, downscale, subtitle, animal-detect, main-app, frontend"
    return
  }

  Write-Header "Rebuild de $svc"

  Use-MinikubeDocker

  switch ($svc) {
    "langscale"     { Write-Info "Rebuild de vidp/langscale...";     & docker build -t "vidp/langscale:latest"     (Join-Path $PROJECT_DIR "app_langscale") | Out-Host }
    "downscale"     { Write-Info "Rebuild de vidp/downscale...";     & docker build -t "vidp/downscale:latest"     (Join-Path $PROJECT_DIR "app_downscale") | Out-Host }
    "subtitle"      { Write-Info "Rebuild de vidp/subtitle...";      & docker build -t "vidp/subtitle:latest"      (Join-Path $PROJECT_DIR "app_subtitle") | Out-Host }
    "animal-detect" { Write-Info "Rebuild de vidp/animal-detect..."; & docker build -t "vidp/animal-detect:latest" (Join-Path $PROJECT_DIR "app_animal_detect") | Out-Host }
    "main-app"      { Write-Info "Rebuild de vidp/main-app...";      & docker build -t "vidp/main-app:latest"      (Join-Path $PROJECT_DIR "vidp-main-app/vidp-fastapi-service") | Out-Host }
    "frontend"      { Write-Info "Rebuild de vidp/frontend...";      & docker build -t "vidp/frontend:latest"      (Join-Path $PROJECT_DIR "vidp-main-app/vidp-nextjs-web") | Out-Host }
    default         { Write-Err "Service inconnu: $svc"; return }
  }

  Write-Info "Redémarrage du pod $svc..."
  & kubectl delete pod -n $NAMESPACE -l ("app=" + $svc) | Out-Host

  Write-Info "Attente du nouveau pod..."
  try { & kubectl wait --for=condition=ready pod -l ("app=" + $svc) -n $NAMESPACE --timeout=60s | Out-Host } catch { }

  Write-Success "Service $svc mis à jour!"

  Write-Info "Logs récents:"
  & kubectl logs -n $NAMESPACE -l ("app=" + $svc) --tail=20 | Out-Host
}

# --- Health ---
function Health-Check {
  Write-Header "Vérification de la santé des services"

  Write-Info "Status des Pods:"
  & kubectl get pods -n $NAMESPACE -o wide | Out-Host

  Write-Host ""
  Write-Info "Status des Services:"
  & kubectl get services -n $NAMESPACE | Out-Host

  Write-Host ""
  Write-Info "Status des PVC:"
  & kubectl get pvc -n $NAMESPACE | Out-Host

  Write-Host ""
  Write-Info "Événements récents:"
  & kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | Select-Object -Last 10 | Out-Host
}

function Show-Help {
  Write-Host "Usage: .\deploy-minikube.ps1 <commande> [options]"
  Write-Host ""
  Write-Host "Commandes disponibles:"
  Write-Host "  start          - Démarrer Minikube"
  Write-Host "  stop           - Arrêter Minikube"
  Write-Host "  status         - Afficher le statut"
  Write-Host "  build          - Construire les images Docker"
  Write-Host "  deploy         - Déployer sur Kubernetes (manuel)"
  Write-Host "  kustomize      - Déployer avec Kustomize (recommandé)"
  Write-Host "  delete         - Supprimer le déploiement"
  Write-Host "  logs <svc>     - Afficher les logs d'un service"
  Write-Host "  rebuild <svc>  - Rebuild et redéployer un service"
  Write-Host "  health         - Vérifier la santé des services"
  Write-Host "  dashboard      - Ouvrir le dashboard Kubernetes"
  Write-Host "  urls           - Afficher les URLs des services"
  Write-Host "  forward        - Port-forward des services"
  Write-Host "  all            - start + build + deploy"
  Write-Host "  help           - Afficher cette aide"
  Write-Host ""
  Write-Host "Services disponibles pour logs/rebuild:"
  Write-Host "  - mongodb, langscale, downscale, subtitle, animal-detect, main-app, frontend"
  Write-Host ""
  Write-Host "Exemples:"
  Write-Host "  .\deploy-minikube.ps1 all              # Démarrage complet"
  Write-Host "  .\deploy-minikube.ps1 rebuild main-app # Rebuild uniquement main-app"
  Write-Host "  .\deploy-minikube.ps1 logs main-app    # Logs de l'API principale"
  Write-Host "  .\deploy-minikube.ps1 forward          # Accès local via port-forward"
  Write-Host "  .\deploy-minikube.ps1 kustomize        # Déploiement avec Kustomize"
}

# --- Main ---
Check-Prereqs

switch ($Command.ToLower()) {
  "start"     { Start-Minikube }
  "stop"      { Stop-Minikube }
  "status"    { Status-Minikube }
  "build"     { Build-Images }
  "deploy"    { Deploy-K8s }
  "kustomize" { Deploy-Kustomize }
  "delete"    { Delete-K8s }
  "logs"      { Show-Logs $Service }
  "rebuild"   { Rebuild-Service $Service }
  "health"    { Health-Check }
  "dashboard" { Open-Dashboard }
  "urls"      { Access-Services }
  "forward"   { Port-Forward }
  "all"       { Start-Minikube; Build-Images; Deploy-K8s }
  "help"      { Show-Help }
  default     { Write-Err "Commande inconnue: $Command"; Show-Help; exit 1 }
}
