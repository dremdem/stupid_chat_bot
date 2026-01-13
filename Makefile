.PHONY: help dev build test lint format check clean install ci delete-user make-admin
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
# Database Management
#===============================================================================

delete-user: ## Delete user by email (EMAIL=user@example.com [DRY_RUN=1])
ifndef EMAIL
	$(error EMAIL is required. Usage: make delete-user EMAIL=user@example.com)
endif
ifdef DRY_RUN
	cd backend && uv run --extra dev-local invoke delete-user --email $(EMAIL) --dry-run
else
	cd backend && uv run --extra dev-local invoke delete-user --email $(EMAIL)
endif

make-admin: ## Promote user to admin (EMAIL=user@example.com [DEMOTE=1] [DRY_RUN=1])
ifndef EMAIL
	$(error EMAIL is required. Usage: make make-admin EMAIL=user@example.com)
endif
ifdef DRY_RUN
ifdef DEMOTE
	cd backend && uv run --extra dev-local invoke make-admin --email $(EMAIL) --demote --dry-run
else
	cd backend && uv run --extra dev-local invoke make-admin --email $(EMAIL) --dry-run
endif
else
ifdef DEMOTE
	cd backend && uv run --extra dev-local invoke make-admin --email $(EMAIL) --demote
else
	cd backend && uv run --extra dev-local invoke make-admin --email $(EMAIL)
endif
endif

#===============================================================================
# Wildcard Delegation - Direct Access to Ecosystem Tasks
#===============================================================================

backend-%: ## Run any backend invoke task (e.g., make backend-lint)
	cd backend && uv run --extra dev-local invoke $*

frontend-%: ## Run any frontend npm script (e.g., make frontend-dev)
	cd frontend && npm run $*
