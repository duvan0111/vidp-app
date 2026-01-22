#!/bin/bash
# filepath: setup-monitoring.sh
#
# Script d'installation du monitoring Prometheus + Grafana pour VidP
# Usage: ./setup-monitoring.sh [install|uninstall|status|dashboard]

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MONITORING_NAMESPACE="monitoring"
VIDP_NAMESPACE="vidp"
GRAFANA_PORT=3001

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

check_prerequisites() {
    print_header "Vérification des Prérequis"
    
    # Vérifier Helm
    if ! command -v helm &> /dev/null; then
        print_error "Helm n'est pas installé"
        print_info "Installez Helm avec: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
        exit 1
    fi
    print_success "Helm installé: $(helm version --short)"
    
    # Vérifier kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl n'est pas installé"
        exit 1
    fi
    print_success "kubectl installé"
    
    # Vérifier Minikube
    if ! minikube status | grep -q "Running"; then
        print_warning "Minikube n'est pas en cours d'exécution"
        print_info "Démarrez-le avec: minikube start --cpus=4 --memory=8192"
        exit 1
    fi
    print_success "Minikube est en cours d'exécution"
}

install_monitoring() {
    print_header "Installation de Prometheus + Grafana"
    
    # Ajouter le repo Helm
    print_info "Ajout du référentiel Helm Prometheus..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
    helm repo update
    
    # Créer le namespace monitoring
    print_info "Création du namespace ${MONITORING_NAMESPACE}..."
    kubectl create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Installer la stack kube-prometheus
    print_info "Installation de kube-prometheus-stack (cela peut prendre 5 minutes)..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace ${MONITORING_NAMESPACE} \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set grafana.adminPassword=admin123 \
        --set grafana.service.type=NodePort \
        --set grafana.service.nodePort=30301 \
        --wait --timeout 10m
    
    print_success "Installation terminée!"
    
    # Attendre que tous les pods soient prêts
    print_info "Attente que tous les pods soient prêts..."
    kubectl wait --for=condition=Ready pods --all -n ${MONITORING_NAMESPACE} --timeout=300s
    
    print_success "Tous les pods sont prêts!"
    
    # Récupérer le mot de passe Grafana
    print_info "Récupération des identifiants Grafana..."
    GRAFANA_PASSWORD=$(kubectl get secret --namespace ${MONITORING_NAMESPACE} prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
    
    echo ""
    print_success "=== MONITORING INSTALLÉ AVEC SUCCÈS ==="
    echo ""
    echo -e "${GREEN}Grafana:${NC}"
    echo "  Username: admin"
    echo "  Password: ${GRAFANA_PASSWORD}"
    echo ""
    echo -e "${GREEN}Accès:${NC}"
    echo "  Option 1 (Port-Forward): kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-grafana ${GRAFANA_PORT}:80"
    echo "           Puis ouvrez: http://localhost:${GRAFANA_PORT}"
    echo ""
    echo "  Option 2 (NodePort):    minikube service prometheus-grafana -n ${MONITORING_NAMESPACE}"
    echo ""
    echo -e "${GREEN}Dashboard VidP:${NC}"
    echo "  Importez le fichier: vidp-dashboard.json"
    echo "  Dans Grafana: ☰ → Dashboards → New → Import"
    echo ""
}

uninstall_monitoring() {
    print_header "Désinstallation du Monitoring"
    
    print_warning "Suppression de la stack Prometheus + Grafana..."
    helm uninstall prometheus -n ${MONITORING_NAMESPACE} 2>/dev/null || true
    
    print_warning "Suppression du namespace ${MONITORING_NAMESPACE}..."
    kubectl delete namespace ${MONITORING_NAMESPACE} --ignore-not-found=true
    
    print_success "Monitoring désinstallé"
}

show_status() {
    print_header "Statut du Monitoring"
    
    # Vérifier si le namespace existe
    if ! kubectl get namespace ${MONITORING_NAMESPACE} &> /dev/null; then
        print_warning "Le namespace ${MONITORING_NAMESPACE} n'existe pas"
        print_info "Installez le monitoring avec: $0 install"
        return
    fi
    
    # Status des pods
    print_info "Pods dans ${MONITORING_NAMESPACE}:"
    kubectl get pods -n ${MONITORING_NAMESPACE} -o wide
    
    echo ""
    print_info "Services dans ${MONITORING_NAMESPACE}:"
    kubectl get services -n ${MONITORING_NAMESPACE}
    
    echo ""
    print_info "Pods VidP dans ${VIDP_NAMESPACE}:"
    kubectl get pods -n ${VIDP_NAMESPACE} 2>/dev/null || print_warning "Namespace ${VIDP_NAMESPACE} non trouvé. Déployez VidP d'abord."
    
    # Vérifier si Grafana est accessible
    echo ""
    print_info "Pour accéder à Grafana:"
    echo "  kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-grafana ${GRAFANA_PORT}:80"
    echo "  Puis: http://localhost:${GRAFANA_PORT}"
}

open_grafana() {
    print_header "Accès à Grafana"
    
    # Vérifier si Grafana existe
    if ! kubectl get deployment prometheus-grafana -n ${MONITORING_NAMESPACE} &> /dev/null; then
        print_error "Grafana n'est pas installé"
        print_info "Installez le monitoring avec: $0 install"
        exit 1
    fi
    
    # Récupérer le mot de passe
    print_info "Identifiants Grafana:"
    GRAFANA_PASSWORD=$(kubectl get secret --namespace ${MONITORING_NAMESPACE} prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)
    echo "  Username: admin"
    echo "  Password: ${GRAFANA_PASSWORD}"
    echo ""
    
    # Démarrer le port-forward
    print_info "Démarrage du port-forward sur http://localhost:${GRAFANA_PORT}"
    print_info "Appuyez sur Ctrl+C pour arrêter"
    echo ""
    
    kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-grafana ${GRAFANA_PORT}:80
}

import_dashboard() {
    print_header "Import du Dashboard VidP"
    
    # Créer le fichier JSON du dashboard
    DASHBOARD_FILE="/tmp/vidp-dashboard.json"
    
    print_info "Le dashboard a été créé dans l'artifact de Claude"
    print_info "Pour l'importer dans Grafana:"
    echo ""
    echo "1. Accédez à Grafana: http://localhost:${GRAFANA_PORT}"
    echo "2. Menu ☰ → Dashboards → New → Import"
    echo "3. Uploadez le fichier: vidp-dashboard.json"
    echo "4. Sélectionnez 'Prometheus' comme source de données"
    echo "5. Cliquez sur 'Import'"
    echo ""
    print_success "Le dashboard sera prêt après l'import!"
}

test_metrics() {
    print_header "Test des Métriques"
    
    print_info "Vérification que Prometheus collecte les métriques VidP..."
    
    # Port-forward Prometheus
    print_info "Démarrage du port-forward Prometheus..."
    kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-operated 9090:9090 &
    PF_PID=$!
    
    sleep 3
    
    # Tester quelques requêtes
    print_info "Test des métriques réseau..."
    NETWORK_METRICS=$(curl -s "http://localhost:9090/api/v1/query?query=container_network_receive_packets_total" | jq -r '.data.result | length')
    
    if [ "$NETWORK_METRICS" -gt "0" ]; then
        print_success "Métriques réseau disponibles: ${NETWORK_METRICS} séries temporelles"
    else
        print_warning "Aucune métrique réseau trouvée. Attendez 1-2 minutes."
    fi
    
    print_info "Test des métriques CPU..."
    CPU_METRICS=$(curl -s "http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total" | jq -r '.data.result | length')
    
    if [ "$CPU_METRICS" -gt "0" ]; then
        print_success "Métriques CPU disponibles: ${CPU_METRICS} séries temporelles"
    else
        print_warning "Aucune métrique CPU trouvée"
    fi
    
    # Arrêter le port-forward
    kill $PF_PID 2>/dev/null || true
    
    echo ""
    print_info "Pour voir toutes les métriques disponibles:"
    echo "  kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-operated 9090:9090"
    echo "  Puis: http://localhost:9090"
}

show_help() {
    echo "Usage: $0 <commande>"
    echo ""
    echo "Commandes disponibles:"
    echo "  install        - Installer Prometheus + Grafana"
    echo "  uninstall      - Désinstaller le monitoring"
    echo "  status         - Afficher le statut"
    echo "  dashboard      - Ouvrir Grafana (port-forward)"
    echo "  import         - Instructions pour importer le dashboard"
    echo "  test           - Tester que les métriques sont collectées"
    echo "  help           - Afficher cette aide"
    echo ""
    echo "Workflow complet:"
    echo "  1. $0 install          # Installer le monitoring (5-10 min)"
    echo "  2. $0 dashboard        # Accéder à Grafana"
    echo "  3. Importer vidp-dashboard.json dans Grafana"
    echo "  4. Profiter de votre monitoring! 🎉"
    echo ""
}

main() {
    case "$1" in
        install)
            check_prerequisites
            install_monitoring
            ;;
        uninstall)
            uninstall_monitoring
            ;;
        status)
            show_status
            ;;
        dashboard)
            open_grafana
            ;;
        import)
            import_dashboard
            ;;
        test)
            test_metrics
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            print_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"