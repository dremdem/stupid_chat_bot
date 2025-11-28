# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the "Stupid Chat Bot" - a simple, straightforward AI-powered chat application. The project demonstrates a clean implementation of a modern chat bot using FastAPI for the backend and React for the frontend.

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
  - WebSocket support for real-time messaging
  - AI integration with streaming responses
  - RESTful API design

- **Frontend**: [React](https://react.dev/) with [Vite](https://vite.dev/)
  - Modern [hooks](https://react.dev/reference/react/hooks)-based components (Hooks are functions that let you use state and other React features without writing classes)
  - Real-time WebSocket communication
  - Rich markdown and code rendering

- **AI Integration**: LLM APIs (OpenAI, Anthropic, or similar)

## Development Commands

### Backend
```bash
cd backend
uv pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Docker (Recommended for local development)
```bash
docker-compose up --build
```

This will start both backend and frontend services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### Linting and Formatting

#### Backend
```bash
cd backend
# Format code with black
black .

# Check with ruff
ruff check .
```

#### Frontend
```bash
cd frontend
# Lint with ESLint
npm run lint

# Format with Prettier
npx prettier --write .
```

### Pre-commit Hooks

Pre-commit hooks are configured to automatically check code quality before commits.

#### Setup
```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hook scripts
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

#### What's Checked
- **Backend**: Black formatting, Ruff linting
- **Frontend**: ESLint, Prettier formatting
- **Security**: Gitleaks secret detection, private key detection
- **General**: Trailing whitespace, file sizes, YAML validation, merge conflicts

The pre-commit hooks will automatically run when you commit. If any check fails, the commit will be blocked until you fix the issues.

## Architecture

### High-Level Design
- **Frontend**: React SPA connecting via WebSocket
- **Backend**: FastAPI server handling WebSocket connections and AI proxy
- **AI Service**: External LLM API for chat responses
- **Storage**: Database for chat history (to be implemented in Phase 5)

### Key Components
- WebSocket Manager for real-time bidirectional communication
- Chat Service for message processing
- AI Client with streaming support
- Message persistence layer
- Rich UI with animations and markdown rendering

See [README.md](./README.md) for detailed architecture diagrams and component descriptions.

## Implementation Status

The project is currently in **Phase 1.5** (Code Quality & CI - In Progress). See README.md for the complete 7-phase implementation roadmap.

### Completed Phases
- **Phase 0**: Documentation Phase ✓
- **Phase 1**: Foundation Setup ✓
  - Backend structure with FastAPI
  - Frontend structure with React + Vite
  - Docker setup
  - Linting and formatting configuration

### Current Phase
- **Phase 1.5**: Code Quality & CI (In Progress)
  - Pre-commit hooks for code quality
  - GitHub Actions CI workflow
  - Security scanning (Gitleaks, Trivy)
  - Development dependencies

### Next Phase
- **Phase 2**: Basic Chat Functionality - WebSocket implementation and simple chat UI

## Important Notes

### Git Workflow
- **NEVER push directly to the master branch**
- Always create a feature branch for your changes
- Push to the feature branch and create a Pull Request
- Wait for CI checks to pass before merging
- All changes must go through the PR review process

### Development Guidelines
- Follow the phased implementation approach outlined in README.md
- Prioritize simplicity ("stupid" chat bot philosophy)
- Use TypeScript for frontend in later phases
- Implement proper error handling and user feedback
- Test WebSocket connections thoroughly
- Follow security best practices for API key management
- Consider rate limiting for AI API calls
