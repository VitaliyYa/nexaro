.PHONY: help dev dev-down mosquitto mosquitto-logs backend test lint format frontend frontend-install frontend-test frontend-lint codegen-types emulator admin-user

.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "SmartRent Development Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

dev: mosquitto backend emulator frontend ## Start Mosquitto broker and run Backend API with hot-reload

dev-down: ## Stop Mosquitto broker container
	docker compose -f edge/mosquitto/docker-compose.yml down

mosquitto: ## Start Mosquitto broker container in background
	docker compose -f edge/mosquitto/docker-compose.yml up -d

mosquitto-logs: ## Follow Mosquitto broker container logs
	docker compose -f edge/mosquitto/docker-compose.yml logs -f

backend: ## Run only Backend FastAPI server with hot-reload
	uv run --directory backend uvicorn src.main:app --reload --port 8000

test: ## Run backend test suite
	uv run --directory backend pytest

lint: ## Run Ruff linter and format check
	uv run --directory backend ruff check .
	uv run --directory backend ruff format --check .

format: ## Auto-format code and apply safe fixes with Ruff
	uv run --directory backend ruff format .
	uv run --directory backend ruff check --fix .

frontend: ## Run Frontend Vite development server
	npm --prefix frontend run dev

frontend-install: ## Install frontend dependencies
	npm --prefix frontend install

frontend-test: ## Run frontend unit tests
	npm --prefix frontend run test:unit

frontend-lint: ## Run frontend linter
	npm --prefix frontend run lint

codegen-types: ## Generate TypeScript interfaces from SSOT JSON Schemas
	npm --prefix frontend run codegen:types

emulator: ## Run local IoT edge device emulator
	uv run --directory backend python ../scripts/dev_edge_emulator.py

admin-user: ## Create or update SuperAdmin account in Supabase
	uv run --directory backend python scripts/create_admin_user.py
