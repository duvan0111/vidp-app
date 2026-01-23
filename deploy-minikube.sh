#!/bin/bash
# filepath: /home/dv-fk/Documents/School/Master 2 DS/INF5141 Cloud Computing/Projet VidP/vidp-app/deploy-minikube.sh
#
# Script de déploiement VidP sur Minikube
# Usage: ./deploy-minikube.sh [start|stop|status|build|deploy|delete|logs]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="vidp"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fonction d'affichage
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

# Vérifier si Minikube est installé
check_minikube() {
    if ! command -v minikube &> /dev/null; then
        print_error "Minikube n'est pas installé. Installez-le d'abord."
        exit 1
    fi
}

# Vérifier si kubectl est installé
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl n'est pas installé. Installez-le d'abord."
        exit 1
    fi
}

# Démarrer Minikube
start_minikube() {
    print_header "Démarrage de Minikube"
    
    if minikube status | grep -q "Running"; then
        print_info "Minikube est déjà en cours d'exécution"
    else
        print_info "Démarrage de Minikube avec 4 CPUs et 8GB RAM..."
        minikube start --cpus=4 --memory=8192 --driver=docker
    fi
    
    # Activer les addons nécessaires
    print_info "Activation des addons..."
    minikube addons enable ingress
    minikube addons enable metrics-server
    minikube addons enable dashboard
    
    print_success "Minikube démarré avec succès"
}

# Arrêter Minikube
stop_minikube() {
    print_header "Arrêt de Minikube"
    minikube stop
    print_success "Minikube arrêté"
}

# Statut de Minikube
status_minikube() {
    print_header "Statut de Minikube"
    minikube status
    echo ""
    
    print_info "Pods dans le namespace ${NAMESPACE}:"
    kubectl get pods -n ${NAMESPACE} 2>/dev/null || print_warning "Namespace ${NAMESPACE} non trouvé"
    echo ""
    
    print_info "Services dans le namespace ${NAMESPACE}:"
    kubectl get services -n ${NAMESPACE} 2>/dev/null || print_warning "Namespace ${NAMESPACE} non trouvé"
}

# Construire les images Docker
build_images() {
    print_header "Construction des images Docker"
    
    # Configurer Docker pour utiliser le daemon de Minikube
    print_info "Configuration de Docker pour Minikube..."
    eval $(minikube docker-env)
    
    # Build app_langscale
    print_info "Construction de vidp/langscale..."
    docker build -t vidp/langscale:latest "${PROJECT_DIR}/app_langscale"
    
    # Build app_downscale
    print_info "Construction de vidp/downscale..."
    docker build -t vidp/downscale:latest "${PROJECT_DIR}/app_downscale"
    
    # Build app_subtitle
    print_info "Construction de vidp/subtitle..."
    docker build -t vidp/subtitle:latest "${PROJECT_DIR}/app_subtitle"
    
    # Build app_animal_detect
    print_info "Construction de vidp/animal-detect..."
    docker build -t vidp/animal-detect:latest "${PROJECT_DIR}/app_animal_detect"
    
    # Build main-app
    print_info "Construction de vidp/main-app..."
    docker build -t vidp/main-app:latest "${PROJECT_DIR}/vidp-main-app/vidp-fastapi-service"
    
    # Build frontend
    print_info "Construction de vidp/frontend..."
    docker build -t vidp/frontend:latest "${PROJECT_DIR}/vidp-main-app/vidp-nextjs-web"
    
    print_success "Toutes les images ont été construites"
    
    print_info "Images disponibles:"
    docker images | grep vidp
}

# Déployer sur Kubernetes
deploy_k8s() {
    print_header "Déploiement sur Kubernetes"
    
    # S'assurer que le contexte est Minikube
    kubectl config use-context minikube
    
    # Appliquer les manifestes dans l'ordre
    print_info "Création du namespace..."
    kubectl apply -f "${PROJECT_DIR}/k8s/namespace.yaml"
    
    print_info "Application des ConfigMaps et Secrets..."
    kubectl apply -f "${PROJECT_DIR}/k8s/configmap.yaml"
    kubectl apply -f "${PROJECT_DIR}/k8s/secrets.yaml"
    
    print_info "Déploiement de MongoDB..."
    kubectl apply -f "${PROJECT_DIR}/k8s/mongodb.yaml"
    
    print_info "Attente que MongoDB soit prêt..."
    kubectl wait --for=condition=ready pod -l app=mongodb -n ${NAMESPACE} --timeout=120s || true
    
    print_info "Déploiement des microservices..."
    kubectl apply -f "${PROJECT_DIR}/k8s/langscale.yaml"
    kubectl apply -f "${PROJECT_DIR}/k8s/downscale.yaml"
    kubectl apply -f "${PROJECT_DIR}/k8s/subtitle.yaml"
    kubectl apply -f "${PROJECT_DIR}/k8s/animal-detect.yaml"
    
    print_info "Attente que les microservices démarrent..."
    sleep 10
    
    print_info "Déploiement de l'application principale..."
    kubectl apply -f "${PROJECT_DIR}/k8s/main-app.yaml"
    
    print_info "Déploiement du frontend..."
    kubectl apply -f "${PROJECT_DIR}/k8s/frontend.yaml"
    
    print_info "Attente que les microservices soient prêts..."
    sleep 5
    
    print_info "Configuration de l'Ingress..."
    kubectl apply -f "${PROJECT_DIR}/k8s/ingress.yaml"
    
    print_success "Déploiement terminé"
    
    print_info "Attente que tous les pods soient prêts..."
    sleep 10
    kubectl get pods -n ${NAMESPACE}
    
    echo ""
    print_info "Pour accéder aux services:"
    echo "  - Frontend: $(minikube service frontend-service -n ${NAMESPACE} --url 2>/dev/null || echo 'En attente...')"
    echo "  - API: $(minikube service main-app-service -n ${NAMESPACE} --url 2>/dev/null || echo 'En attente...')"
    echo ""
    print_info "Ou utilisez: minikube tunnel (dans un terminal séparé)"
}

# Déployer avec Kustomize (recommandé)
deploy_kustomize() {
    print_header "Déploiement avec Kustomize"
    
    # S'assurer que le contexte est Minikube
    kubectl config use-context minikube
    
    print_info "Application de la configuration Kustomize..."
    kubectl apply -k "${PROJECT_DIR}/k8s/"
    
    print_success "Déploiement Kustomize terminé"
    
    print_info "Attente que MongoDB soit prêt..."
    kubectl wait --for=condition=ready pod -l app=mongodb -n ${NAMESPACE} --timeout=120s || true
    
    print_info "Attente que tous les pods soient prêts..."
    sleep 15
    kubectl get pods -n ${NAMESPACE}
    
    echo ""
    print_info "Pour accéder aux services:"
    echo "  - Frontend: $(minikube service frontend-service -n ${NAMESPACE} --url 2>/dev/null || echo 'En attente...')"
    echo "  - API: $(minikube service main-app-service -n ${NAMESPACE} --url 2>/dev/null || echo 'En attente...')"
    echo ""
    print_info "Ou utilisez: minikube tunnel (dans un terminal séparé)"
}

# Supprimer le déploiement
delete_k8s() {
    print_header "Suppression du déploiement"
    
    print_warning "Suppression de tous les ressources dans le namespace ${NAMESPACE}..."
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
    
    print_success "Déploiement supprimé"
}

# Afficher les logs
show_logs() {
    print_header "Logs des services"
    
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "Usage: $0 logs <service>"
        print_info "Services disponibles: mongodb, langscale, downscale, subtitle, animal-detect, main-app, frontend"
        print_info ""
        print_info "Tous les pods:"
        kubectl get pods -n ${NAMESPACE}
        return
    fi
    
    print_info "Logs de ${service}:"
    kubectl logs -f -l app=${service} -n ${NAMESPACE} --tail=100
}

# Ouvrir le dashboard
open_dashboard() {
    print_header "Ouverture du Dashboard Kubernetes"
    minikube dashboard &
}

# Accéder aux services
access_services() {
    print_header "URLs des Services"
    
    print_info "Frontend:"
    minikube service frontend-service -n ${NAMESPACE} --url
    
    print_info "API Backend:"
    minikube service main-app-service -n ${NAMESPACE} --url
    
    echo ""
    print_info "Pour un accès via tunnel (recommandé):"
    echo "  1. Ouvrez un nouveau terminal"
    echo "  2. Exécutez: minikube tunnel"
    echo "  3. Ajoutez à /etc/hosts:"
    echo "     $(minikube ip) vidp.local api.vidp.local"
}

# Port-forward pour accès local
port_forward() {
    print_header "Port-Forward des Services"
    
    print_info "Démarrage des port-forwards..."
    print_info "  - API: localhost:8000"
    print_info "  - Frontend: localhost:3000"
    print_info ""
    print_info "Appuyez sur Ctrl+C pour arrêter"
    
    # Store PIDs
    local pids=()

    # Trap for cleanup on exit
    trap "kill ${pids[@]} 2>/dev/null; print_info 'Port-forwards arrêtés.'" EXIT INT TERM
    
    # Lancer les port-forwards en arrière-plan
    kubectl port-forward svc/main-app-service 8000:8000 -n ${NAMESPACE} &
    pids+=($!) # Get PID of last background command
    
    kubectl port-forward svc/frontend-service 3000:3000 -n ${NAMESPACE} &
    pids+=($!) # Get PID of last background command
    
    # Attendre indéfiniment (until Ctrl+C)
    wait
}

# Rebuild et redeploy un microservice spécifique
rebuild_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_error "Usage: $0 rebuild <service>"
        print_info "Services disponibles: langscale, downscale, subtitle, animal-detect, main-app, frontend"
        return 1
    fi
    
    print_header "Rebuild de ${service}"
    
    # Configurer Docker pour Minikube
    eval $(minikube docker-env)
    
    # Mapper les noms de services aux chemins
    case "$service" in
        langscale)
            print_info "Rebuild de vidp/langscale..."
            docker build -t vidp/langscale:latest "${PROJECT_DIR}/app_langscale"
            ;;
        downscale)
            print_info "Rebuild de vidp/downscale..."
            docker build -t vidp/downscale:latest "${PROJECT_DIR}/app_downscale"
            ;;
        subtitle)
            print_info "Rebuild de vidp/subtitle..."
            docker build -t vidp/subtitle:latest "${PROJECT_DIR}/app_subtitle"
            ;;
        animal-detect)
            print_info "Rebuild de vidp/animal-detect..."
            docker build -t vidp/animal-detect:latest "${PROJECT_DIR}/app_animal_detect"
            ;;
        main-app)
            print_info "Rebuild de vidp/main-app..."
            docker build -t vidp/main-app:latest "${PROJECT_DIR}/vidp-main-app/vidp-fastapi-service"
            ;;
        frontend)
            print_info "Rebuild de vidp/frontend..."
            docker build -t vidp/frontend:latest "${PROJECT_DIR}/vidp-main-app/vidp-nextjs-web"
            ;;
        *)
            print_error "Service inconnu: ${service}"
            return 1
            ;;
    esac
    
    # Restart le pod
    print_info "Redémarrage du pod ${service}..."
    kubectl delete pod -n ${NAMESPACE} -l app=${service}
    
    print_info "Attente du nouveau pod..."
    kubectl wait --for=condition=ready pod -l app=${service} -n ${NAMESPACE} --timeout=60s || true
    
    print_success "Service ${service} mis à jour!"
    
    # Afficher les logs
    print_info "Logs récents:"
    kubectl logs -n ${NAMESPACE} -l app=${service} --tail=20
}

# Vérifier la santé de tous les services
health_check() {
    print_header "Vérification de la santé des services"
    
    print_info "Status des Pods:"
    kubectl get pods -n ${NAMESPACE} -o wide
    
    echo ""
    print_info "Status des Services:"
    kubectl get services -n ${NAMESPACE}
    
    echo ""
    print_info "Status des PVC:"
    kubectl get pvc -n ${NAMESPACE}
    
    echo ""
    print_info "Événements récents:"
    kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp' | tail -10
}

# Afficher l'aide
show_help() {
    echo "Usage: $0 <commande> [options]"
    echo ""
    echo "Commandes disponibles:"
    echo "  start          - Démarrer Minikube"
    echo "  stop           - Arrêter Minikube"
    echo "  status         - Afficher le statut"
    echo "  build          - Construire les images Docker"
    echo "  deploy         - Déployer sur Kubernetes (manuel)"
    echo "  kustomize      - Déployer avec Kustomize (recommandé)"
    echo "  delete         - Supprimer le déploiement"
    echo "  logs <svc>     - Afficher les logs d'un service"
    echo "  rebuild <svc>  - Rebuild et redéployer un service"
    echo "  health         - Vérifier la santé des services"
    echo "  dashboard      - Ouvrir le dashboard Kubernetes"
    echo "  urls           - Afficher les URLs des services"
    echo "  forward        - Port-forward des services"
    echo "  all            - start + build + deploy"
    echo "  help           - Afficher cette aide"
    echo ""
    echo "Services disponibles pour logs/rebuild:"
    echo "  - mongodb, langscale, downscale, subtitle, animal-detect, main-app, frontend"
    echo ""
    echo "Exemples:"
    echo "  $0 all                    # Démarrage complet"
    echo "  $0 rebuild main-app       # Rebuild uniquement main-app"
    echo "  $0 logs main-app          # Logs de l'API principale"
    echo "  $0 forward                # Accès local via port-forward"
    echo "  $0 kustomize              # Déploiement avec Kustomize"
}

# Main
main() {
    check_minikube
    check_kubectl
    
    case "$1" in
        start)
            start_minikube
            ;;
        stop)
            stop_minikube
            ;;
        status)
            status_minikube
            ;;
        build)
            build_images
            ;;
        deploy)
            deploy_k8s
            ;;
        kustomize)
            deploy_kustomize
            ;;
        delete)
            delete_k8s
            ;;
        logs)
            show_logs "$2"
            ;;
        rebuild)
            rebuild_service "$2"
            ;;
        health)
            health_check
            ;;
        dashboard)
            open_dashboard
            ;;
        urls)
            access_services
            ;;
        forward)
            port_forward
            ;;
        all)
            start_minikube
            build_images
            deploy_k8s
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécution
main "$@"
