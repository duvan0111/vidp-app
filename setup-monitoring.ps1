<# 
Script d'installation du monitoring Prometheus + Grafana pour VidP
Usage:
  .\setup-monitoring.ps1 install
  .\setup-monitoring.ps1 uninstall
  .\setup-monitoring.ps1 status
  .\setup-monitoring.ps1 dashboard
  .\setup-monitoring.ps1 test
#>

$ErrorActionPreference = "Stop"

# ===== Variables =====
# ===== Variables =====
$MONITORING_NAMESPACE = "monitoring"
$VIDP_NAMESPACE = "vidp"
$GRAFANA_PORT = 3001
$LOCAL_CHART_DIR = (Get-Item -Path $PSScriptRoot).FullName + "\helm-charts" # Get absolute path
$LOCAL_KUBE_PROMETHEUS_STACK_PATTERN = "$LOCAL_CHART_DIR\kube-prometheus-stack-*.tgz"

# ===== Helpers =====
function Print-Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Cyan
}

function Print-Success($msg) {
    Write-Host "[SUCCESS] $msg" -ForegroundColor Green
}

function Print-Warning($msg) {
    Write-Host "[WARNING] $msg" -ForegroundColor Yellow
}

function Print-Error($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}

function Print-Header($title) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host " $title" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""
}

# ===== Prérequis =====
function Check-Prerequisites {
    Print-Header "Vérification des prérequis"

    if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
        Print-Error "Helm n'est pas installé"
        exit 1
    }
    Print-Success "Helm OK"

    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Print-Error "kubectl n'est pas installé"
        exit 1
    }
    Print-Success "kubectl OK"

    $minikubeStatus = minikube status --format="{{.Host}}" 2>$null
    if ($minikubeStatus -ne "Running") {
        Print-Warning "Minikube n'est pas démarré"
        Print-Info "Lance: minikube start --cpus=4 --memory=8192"
        exit 1
    }

    Print-Success "Minikube en cours d'exécution"
}

# ===== Installation =====
function Install-Monitoring {
    Print-Header "Installation Prometheus + Grafana"

    $chartSource = ""
    $localChartFile = Get-Item -Path $LOCAL_KUBE_PROMETHEUS_STACK_PATTERN -ErrorAction SilentlyContinue
    
    if ($localChartFile) {
        Print-Info "Chart Helm local trouvé: $($localChartFile.FullName). Utilisation de ce chart."
        $chartSource = $localChartFile.FullName
    }
    else {
        Print-Info "Chart Helm local non trouvé. Tentative d'ajout du repo Helm distant."
        Print-Info "Ajout du repo Helm"
        $helmAddResult = helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        if ($LASTEXITCODE -ne 0) {
            Print-Error "Échec de l'ajout du repo Helm. Veuillez vérifier votre connexion internet, proxy ou pare-feu. Détails:"
            Write-Host $helmAddResult -ForegroundColor Red
            exit 1
        }
        Print-Success "Repo Helm 'prometheus-community' ajouté."

        Print-Info "Mise à jour des repos Helm"
        $helmUpdateResult = helm repo update
        if ($LASTEXITCODE -ne 0) {
            Print-Warning "Avertissement: Échec de la mise à jour des repos Helm. Cela peut être dû à des problèmes de connexion. Détails:"
            Write-Host $helmUpdateResult -ForegroundColor Yellow
            # Ne pas quitter ici, car l'installation peut encore fonctionner si le chart spécifique est en cache.
        }
        Print-Success "Repos Helm mis à jour."
        $chartSource = "prometheus-community/kube-prometheus-stack"
    }
    
    Print-Info "Création du namespace $MONITORING_NAMESPACE"
    kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

    Print-Info "Installation de kube-prometheus-stack (5-10 min)"
    helm upgrade --install prometheus $chartSource `
        --namespace $MONITORING_NAMESPACE `
        --set prometheus.prometheusSpec.retention=7d `
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false `
        --set grafana.adminPassword=admin123 `
        --set grafana.service.type=NodePort `
        --set grafana.service.nodePort=30301 `
        --wait --timeout 10m

    Print-Success "Installation terminée"

    Print-Info "Attente des pods..."
    kubectl wait --for=condition=Ready pods --all -n $MONITORING_NAMESPACE --timeout=300s

    $password = kubectl get secret prometheus-grafana -n $MONITORING_NAMESPACE `
        -o jsonpath="{.data.admin-password}" |
        ForEach-Object { [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }

    Print-Success "MONITORING INSTALLÉ"
    Write-Host ""
    Write-Host "Grafana :" -ForegroundColor Green
    Write-Host "  Username : admin"
    Write-Host "  Password : $password"
    Write-Host ""
    Write-Host "Accès :" -ForegroundColor Green
    Write-Host "  kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-grafana $GRAFANA_PORT`:80"
    Write-Host "  http://localhost:$GRAFANA_PORT"
}

# ===== Désinstallation =====
function Uninstall-Monitoring {
    Print-Header "Désinstallation"

    helm uninstall prometheus -n $MONITORING_NAMESPACE 2>$null
    kubectl delete namespace $MONITORING_NAMESPACE --ignore-not-found

    Print-Success "Monitoring supprimé"
}

# ===== Status =====
function Show-Status {
    Print-Header "Statut du monitoring"

    kubectl get pods -n $MONITORING_NAMESPACE
    Write-Host ""
    kubectl get svc -n $MONITORING_NAMESPACE
}

# ===== Grafana =====
function Open-Grafana {
    Print-Header "Accès Grafana"

    $password = kubectl get secret prometheus-grafana -n $MONITORING_NAMESPACE `
        -o jsonpath="{.data.admin-password}" |
        ForEach-Object { [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }

    Write-Host "Username: admin"
    Write-Host "Password: $password"
    Write-Host ""
    Write-Host "CTRL+C pour arrêter"
    kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-grafana $GRAFANA_PORT`:80
}

# ===== Test métriques =====
function Test-Metrics {
    Print-Header "Test des métriques Prometheus"

    Print-Info "Démarrage de kubectl port-forward pour Prometheus (port 9090)..."
    $portForwardProcess = Start-Process kubectl -ArgumentList "port-forward -n $MONITORING_NAMESPACE svc/prometheus-operated 9090:9090" -NoNewWindow -PassThru -ErrorAction SilentlyContinue
    if (-not $portForwardProcess) {
        Print-Error "Impossible de démarrer kubectl port-forward. Assurez-vous que kubectl est configuré et que le service Prometheus est opérationnel."
        exit 1
    }
    
    Start-Sleep -Seconds 5 # Laisser le temps au port-forward de s'établir

    try {
        Print-Info "Tentative de connexion à Prometheus..."
        Invoke-RestMethod "http://localhost:9090/api/v1/query?query=up" | Out-Null
        Print-Success "Prometheus répond correctement."
    }
    catch {
        Print-Error "Erreur lors de la connexion à Prometheus: $($_.Exception.Message)"
        exit 1
    }
    finally {
        # Arrêter le processus port-forward
        if ($portForwardProcess) {
            Print-Info "Arrêt du processus kubectl port-forward."
            Stop-Process -Id $portForwardProcess.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

# ===== Main =====
switch ($args[0]) {
    "install"   { Check-Prerequisites; Install-Monitoring }
    "uninstall" { Uninstall-Monitoring }
    "status"    { Show-Status }
    "dashboard" { Open-Grafana }
    "test"      { Test-Metrics }
    default {
        Write-Host "Usage:"
        Write-Host "  .\setup-monitoring.ps1 install"
        Write-Host "  .\setup-monitoring.ps1 uninstall"
        Write-Host "  .\setup-monitoring.ps1 status"
        Write-Host "  .\setup-monitoring.ps1 dashboard"
        Write-Host "  .\setup-monitoring.ps1 test"
    }
}
