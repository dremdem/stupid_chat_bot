# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**Stupid Chat Bot** - A simple AI-powered chat application using FastAPI backend and React frontend.

## Tech Stack

- **Backend**: FastAPI (Python 3.12), WebSocket, LiteLLM for AI integration
- **Frontend**: React with Vite, hooks-based components
- **Database**: SQLAlchemy async + SQLite (Alembic migrations)
- **AI**: LiteLLM supporting Anthropic, OpenAI, Google, Meta, DeepSeek

## Quick Commands

### Development
```bash
# Docker (recommended)
docker compose up --build

# Backend manual
cd backend && uv sync && uvicorn app.main:app --reload --port 8000

# Frontend manual
cd frontend && npm install && npm run dev
```

### Backend Tasks (via invoke)
```bash
cd backend
invoke test      # Run tests (Docker)
invoke lint      # Ruff linting
invoke format    # Black formatting
invoke check     # All checks
```

### Frontend Tasks
```bash
cd frontend
npm run dev      # Dev server
npm run build    # Production build
npm run lint     # ESLint
npm run format   # Prettier
```

## Dependencies

### Adding Dependencies
```bash
# Backend
cd backend && uv add <package>  # Auto-updates uv.lock

# Frontend
cd frontend && npm install <package>
```

### Lock File
- `uv.lock` is auto-verified by pre-commit hooks
- Run `uv lock` after editing pyproject.toml manually
- CI validates lock file on every PR

## Critical Rules

### Git Workflow
- **NEVER push directly to master** - always use feature branches
- Create PR for all changes
- **ALWAYS check CI after pushing** - verify green checkmarks on PR page
- Wait for CI to pass before merging

### Code Quality
- Pre-commit hooks run automatically (Black, Ruff, ESLint, Prettier, Gitleaks)
- Run `pre-commit run --all-files` to check everything

## Development Guidelines

- Follow phased implementation in README.md
- Prioritize simplicity ("stupid" chat bot philosophy)
- Test WebSocket connections thoroughly
- Follow security best practices for API keys

## AI Provider Config

Set in `.env`:
```bash
AI_PROVIDER=anthropic  # or: openai, google, meta, deepseek
ANTHROPIC_API_KEY=your-key
```

## Additional Resources

- **Architecture & Roadmap**: See [README.md](./README.md)
- **PR Comment Workflows**: See [.claude/workflows/pr-comments.md](.claude/workflows/pr-comments.md)
- **Git Worktrees**: See [.claude/workflows/git-worktrees.md](.claude/workflows/git-worktrees.md)
