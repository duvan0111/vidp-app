# Makefile pour faciliter les commandes Docker Compose
# Usage: make [commande]

.PHONY: help build up down restart logs ps clean rebuild

# Couleurs pour les messages
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Afficher l'aide
	@echo "$(BLUE)VidP Docker - Commandes disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

build: ## Construire les images Docker
	@echo "$(BLUE)Construction des images...$(NC)"
	docker-compose build

up: ## Démarrer tous les services
	@echo "$(BLUE)Démarrage des services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services démarrés!$(NC)"
	@make ps

up-build: ## Construire et démarrer tous les services
	@echo "$(BLUE)Construction et démarrage...$(NC)"
	docker-compose up --build -d
	@echo "$(GREEN)✓ Services démarrés!$(NC)"
	@make ps
	@echo ""
	@echo "$(GREEN)Accès aux services:$(NC)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend: http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

down: ## Arrêter tous les services
	@echo "$(BLUE)Arrêt des services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services arrêtés$(NC)"

restart: ## Redémarrer tous les services
	@echo "$(BLUE)Redémarrage des services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Services redémarrés$(NC)"

logs: ## Afficher les logs de tous les services
	docker-compose logs -f

logs-backend: ## Afficher les logs du backend
	docker-compose logs -f backend

logs-frontend: ## Afficher les logs du frontend
	docker-compose logs -f frontend

logs-mongo: ## Afficher les logs de MongoDB
	docker-compose logs -f mongodb

ps: ## Afficher l'état des services
	@docker-compose ps

clean: ## Arrêter et supprimer les conteneurs (conserve les volumes)
	@echo "$(YELLOW)Nettoyage des conteneurs...$(NC)"
	docker-compose down --remove-orphans
	@echo "$(GREEN)✓ Conteneurs supprimés$(NC)"

clean-all: ## Arrêter et supprimer conteneurs + volumes (⚠️ PERTE DE DONNÉES)
	@echo "$(YELLOW)⚠️  ATTENTION: Cela va supprimer tous les volumes!$(NC)"
	@read -p "Êtes-vous sûr? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --remove-orphans; \
		echo "$(GREEN)✓ Nettoyage complet terminé$(NC)"; \
	else \
		echo "Annulé"; \
	fi

rebuild: ## Reconstruire et redémarrer (sans cache)
	@echo "$(BLUE)Reconstruction complète...$(NC)"
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)✓ Reconstruction terminée$(NC)"

exec-backend: ## Ouvrir un shell dans le conteneur backend
	docker-compose exec backend bash

exec-frontend: ## Ouvrir un shell dans le conteneur frontend
	docker-compose exec frontend sh

exec-mongo: ## Ouvrir mongosh dans MongoDB
	docker-compose exec mongodb mongosh -u vidp_admin -p vidp_password_2024 --authenticationDatabase admin

stats: ## Afficher les statistiques des conteneurs
	docker stats --no-stream

volumes: ## Lister les volumes Docker
	@echo "$(BLUE)Volumes Docker:$(NC)"
	@docker volume ls | grep vidp

backup-mongo: ## Sauvegarder la base de données MongoDB
	@echo "$(BLUE)Sauvegarde de MongoDB...$(NC)"
	@mkdir -p ./backups
	@docker run --rm -v vidp-main-app_mongodb_data:/data \
		-v $$(pwd)/backups:/backup busybox \
		tar czf /backup/mongodb-backup-$$(date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "$(GREEN)✓ Sauvegarde créée dans ./backups/$(NC)"

system-prune: ## Nettoyer le système Docker (images, conteneurs non utilisés)
	@echo "$(YELLOW)Nettoyage du système Docker...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Nettoyage terminé$(NC)"

health: ## Vérifier la santé des services
	@echo "$(BLUE)État de santé des services:$(NC)"
	@docker-compose ps --format json | python3 -m json.tool 2>/dev/null || docker-compose ps

setup: ## Configuration initiale (créer .env depuis .env.example)
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Création du fichier .env...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ Fichier .env créé$(NC)"; \
		echo "$(YELLOW)⚠️  Pensez à modifier les valeurs dans .env si nécessaire$(NC)"; \
	else \
		echo "$(YELLOW)Le fichier .env existe déjà$(NC)"; \
	fi

# Commande par défaut
.DEFAULT_GOAL := help
