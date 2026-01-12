# Makefile pour VidP - Déploiement Kubernetes sur Minikube

.PHONY: help start stop status build deploy delete logs dashboard urls forward all clean

# Variables
NAMESPACE = vidp
SCRIPT = ./deploy-minikube.sh

# Couleurs
BLUE = \033[0;34m
NC = \033[0m

help: ## Afficher cette aide
	@echo ""
	@echo "$(BLUE)VidP - Commandes Makefile$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

start: ## Démarrer Minikube
	@$(SCRIPT) start

stop: ## Arrêter Minikube
	@$(SCRIPT) stop

status: ## Afficher le statut du cluster
	@$(SCRIPT) status

build: ## Construire les images Docker
	@$(SCRIPT) build

deploy: ## Déployer sur Kubernetes
	@$(SCRIPT) deploy

delete: ## Supprimer le déploiement
	@$(SCRIPT) delete

logs: ## Afficher les logs (usage: make logs SVC=main-app)
	@$(SCRIPT) logs $(SVC)

logs-main: ## Logs de l'API principale
	@$(SCRIPT) logs main-app

logs-langscale: ## Logs du service langscale
	@$(SCRIPT) logs langscale

logs-downscale: ## Logs du service downscale
	@$(SCRIPT) logs downscale

logs-subtitle: ## Logs du service subtitle
	@$(SCRIPT) logs subtitle

logs-animal: ## Logs du service animal-detect
	@$(SCRIPT) logs animal-detect

logs-frontend: ## Logs du frontend
	@$(SCRIPT) logs frontend

logs-mongodb: ## Logs de MongoDB
	@$(SCRIPT) logs mongodb

dashboard: ## Ouvrir le dashboard Kubernetes
	@$(SCRIPT) dashboard

urls: ## Afficher les URLs des services
	@$(SCRIPT) urls

forward: ## Port-forward des services (API:8000, Frontend:3000)
	@$(SCRIPT) forward

all: ## Démarrage complet (start + build + deploy)
	@$(SCRIPT) all

clean: delete ## Nettoyer le déploiement (alias de delete)

# Commandes kubectl directes
pods: ## Lister tous les pods
	@kubectl get pods -n $(NAMESPACE) -o wide

services: ## Lister tous les services
	@kubectl get services -n $(NAMESPACE)

describe-pod: ## Décrire un pod (usage: make describe-pod POD=main-app-xxx)
	@kubectl describe pod $(POD) -n $(NAMESPACE)

shell: ## Shell dans un pod (usage: make shell POD=main-app-xxx)
	@kubectl exec -it $(POD) -n $(NAMESPACE) -- /bin/sh

restart: ## Redémarrer un deployment (usage: make restart APP=main-app)
	@kubectl rollout restart deployment/$(APP) -n $(NAMESPACE)

scale: ## Scaler un deployment (usage: make scale APP=main-app REPLICAS=3)
	@kubectl scale deployment/$(APP) --replicas=$(REPLICAS) -n $(NAMESPACE)

# Tests
test-api: ## Tester l'API (après forward)
	@curl -s http://localhost:8000/health | jq

test-services: ## Tester la santé de tous les microservices
	@curl -s http://localhost:8000/api/v1/processing/health | jq
