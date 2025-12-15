.PHONY: help dev build test lint format check clean install ci
.PHONY: backend-% frontend-%

# Default target
.DEFAULT_GOAL := help

#===============================================================================
# Main Targets - Orchestrate Both Ecosystems
#===============================================================================

help: ## Show this help message
	@echo "Multi-Ecosystem Task Runner - Stupid Chat Bot"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Wildcard delegation:"
	@echo "  backend-<task>      Run backend invoke task"
	@echo "  frontend-<task>     Run frontend npm script"

dev: ## Start development servers (backend + frontend)
	@echo "Starting development servers..."
	docker compose up

build: ## Build both frontend and backend
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Building backend Docker image..."
	docker compose build backend

test: ## Run tests for both ecosystems
	@echo "Running backend tests..."
	cd backend && uv run --extra dev-local invoke test
	@echo "Running frontend tests..."
	cd frontend && npm run test

lint: ## Run linters for both ecosystems
	@echo "Linting backend..."
	cd backend && uv run --extra dev-local invoke lint
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: ## Format code for both ecosystems
	@echo "Formatting backend..."
	cd backend && uv run --extra dev-local invoke format
	@echo "Formatting frontend..."
	cd frontend && npm run format

check: ## Run all checks (format, lint, test) for both ecosystems
	@echo "Running comprehensive checks..."
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

clean: ## Clean build artifacts and caches
	@echo "Cleaning backend..."
	cd backend && uv run --extra dev-local invoke clean
	@echo "Cleaning frontend..."
	cd frontend && npm run clean || echo "No clean script (will be added)"
	@echo "Cleaning Docker..."
	docker compose down -v

install: ## Install dependencies for both ecosystems
	@echo "Installing backend dependencies..."
	cd backend && uv sync --all-extras
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

ci: ## Run CI pipeline (matches GitHub Actions)
	@echo "Running CI pipeline..."
	cd backend && uv run --extra dev-local invoke ci
	cd frontend && npm run ci

#===============================================================================
# Wildcard Delegation - Direct Access to Ecosystem Tasks
#===============================================================================

backend-%: ## Run any backend invoke task (e.g., make backend-lint)
	cd backend && uv run --extra dev-local invoke $*

frontend-%: ## Run any frontend npm script (e.g., make frontend-dev)
	cd frontend && npm run $*
