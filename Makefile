.PHONY: build up down logs shell django-shell makemigrations migrate createsuperuser collectstatic test lint format backup

# Variables
COMPOSE = docker-compose
COMPOSE_RUN = $(COMPOSE) run --rm
COMPOSE_EXEC = $(COMPOSE) exec
WEB = web
DB = db
MANAGE_PY = python manage.py

# Docker commands
build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

# Django app commands
shell:
	$(COMPOSE_EXEC) $(WEB) bash

django-shell:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) shell

startapp:
	@read -p "App name: " app_name; \
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) startapp $$app_name

makemigrations:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) makemigrations

migrate:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) migrate

createsuperuser:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) createsuperuser

collectstatic:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) collectstatic --no-input

# Development tools
test:
	$(COMPOSE_EXEC) $(WEB) $(MANAGE_PY) test

lint:
	$(COMPOSE_EXEC) $(WEB) flake8 .

format:
	$(COMPOSE_EXEC) $(WEB) black .

format-check:
	$(COMPOSE_EXEC) $(WEB) black --check .

lint-all: format lint

# Database
backup:
	$(COMPOSE_EXEC) $(DB) pg_dump -U postgres postgres > backup_$$(date +%Y-%m-%d_%H-%M-%S).sql

restore:
	@read -p "Backup file: " backup_file; \
	cat $$backup_file | $(COMPOSE_EXEC) -T $(DB) psql -U postgres postgres

# Project setup
create-project:
	$(COMPOSE_RUN) $(WEB) django-admin startproject core .

# Production
prod-up:
	$(COMPOSE) -f docker-compose.prod.yml up -d

prod-down:
	$(COMPOSE) -f docker-compose.prod.yml down

prod-build:
	$(COMPOSE) -f docker-compose.prod.yml build

# Celery commands
celery-worker:
	$(COMPOSE_EXEC) celery celery -A core worker -l info

celery-beat:
	$(COMPOSE_EXEC) celery celery -A core beat -l info

# Help command
help:
	@echo "Available commands:"
	@echo "  build            - Build Docker images"
	@echo "  up               - Start all containers"
	@echo "  down             - Stop all containers"
	@echo "  down-v           - Stop all containers and remove volumes"
	@echo "  logs             - View logs for all containers"
	@echo "  ps               - List running containers"
	@echo "  shell            - Open bash shell in web container"
	@echo "  django-shell     - Open Django shell"
	@echo "  startapp         - Create a new Django app"
	@echo "  makemigrations   - Generate database migrations"
	@echo "  migrate          - Apply database migrations"
	@echo "  createsuperuser  - Create Django admin user"
	@echo "  collectstatic    - Collect static files"
	@echo "  test             - Run tests"
	@echo "  lint             - Run code linting"
	@echo "  format           - Format code"
	@echo "  backup           - Backup database"
	@echo "  restore          - Restore database from backup"
	@echo "  create-project   - Create a new Django project"
	@echo "  prod-up          - Start production containers"
	@echo "  prod-down        - Stop production containers"
	@echo "  prod-build       - Build production images"
	@echo "  celery-worker    - Run Celery worker"
	@echo "  celery-beat      - Run Celery beat scheduler"