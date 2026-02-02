.PHONY: up down build logs shell clean dev help init

# Default target
help:
	@echo "Local Transcript App - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make build    - Build/rebuild all containers"
	@echo "  make logs     - Follow logs from all services"
	@echo "  make shell    - Open bash in api container"
	@echo "  make clean    - Remove containers, volumes, and build cache"
	@echo "  make dev      - Start in development mode (with rebuild)"
	@echo "  make init     - Initialize data directories and .env"
	@echo ""
	@echo "Service-specific:"
	@echo "  make logs-api    - Follow API logs only"
	@echo "  make logs-worker - Follow worker logs only"
	@echo "  make logs-web    - Follow web logs only"
	@echo "  make shell-api   - Shell into api container"
	@echo "  make shell-worker- Shell into worker container"
	@echo "  make shell-web   - Shell into web container"
	@echo ""

# Initialize project
init:
	@echo "Initializing project..."
	@mkdir -p data/uploads data/outputs data/db
	@test -f .env || cp .env.example .env
	@echo "Done! Edit .env if needed, then run 'make up'"

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build/rebuild containers
build:
	docker compose build

# Development mode - rebuild and start with logs
dev:
	docker compose up --build

# Follow all logs
logs:
	docker compose logs -f

# Service-specific logs
logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

logs-web:
	docker compose logs -f web

# Shell into containers
shell: shell-api

shell-api:
	docker compose exec api /bin/bash

shell-worker:
	docker compose exec worker /bin/bash

shell-web:
	docker compose exec web /bin/sh

# Clean everything
clean:
	docker compose down -v --rmi local --remove-orphans
	@echo "Containers and images removed."
	@echo "Data in ./data/ preserved. Remove manually if needed."

# Validate docker-compose config
config:
	docker compose config

# Health check
status:
	@echo "Service Status:"
	@docker compose ps
	@echo ""
	@echo "API Health:"
	@curl -s http://localhost:$${API_PORT:-8000}/health || echo "API not responding"
