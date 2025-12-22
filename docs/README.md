# Documentation Index

This directory contains technical documentation for the Stupid Chat Bot project.

## Table of Contents

- [Quick Links](#quick-links)
- [Documentation Overview](#documentation-overview)
- [Deployment](#deployment)
- [Architecture & Design](#architecture--design)
- [Development](#development)
- [Guidelines](#guidelines)

---

## Quick Links

| Document | Description |
|----------|-------------|
| [Main README](../README.md) | Project overview, setup, and usage |
| [CLAUDE.md](../CLAUDE.md) | AI assistant guidelines for this codebase |
| [Backend README](../backend/README.md) | Python/FastAPI backend documentation |
| [Frontend README](../frontend/README.md) | React frontend documentation |

---

## Documentation Overview

```mermaid
graph TB
    subgraph Root["Project Root"]
        README["README.md<br/>Project Overview"]
        CLAUDE["CLAUDE.md<br/>AI Guidelines"]
    end

    subgraph Docs["docs/"]
        INDEX["README.md<br/>This Index"]
        DEPLOY["Deployment"]
        ARCH["Architecture"]
        DEV["Development"]
    end

    subgraph Deploy["Deployment Docs"]
        PLAN["PLAN_DEPLOYMENT.md"]
        AUTO["AUTOMATED_DEPLOYMENT.md"]
    end

    subgraph Arch["Architecture Docs"]
        TASK["multi-ecosystem-task-runner.md"]
    end

    subgraph Dev["Development Docs"]
        DOCKER["docker-dev-environment-implementation-plan.md"]
        UV["uv-lock-migration-plan.md"]
    end

    README --> INDEX
    INDEX --> DEPLOY
    INDEX --> ARCH
    INDEX --> DEV
    DEPLOY --> PLAN
    DEPLOY --> AUTO
    ARCH --> TASK
    DEV --> DOCKER
    DEV --> UV
```

---

## Deployment

Documentation for deploying the application to production.

| Document | Description | Status |
|----------|-------------|--------|
| [PLAN_DEPLOYMENT.md](./PLAN_DEPLOYMENT.md) | Deployment architecture and phases overview | Reference |
| [AUTOMATED_DEPLOYMENT.md](./AUTOMATED_DEPLOYMENT.md) | Step-by-step automated deployment setup guide | Active |

### Key Topics
- DigitalOcean droplet setup
- Docker container deployment
- GitHub Actions CI/CD
- SSL/TLS configuration
- Health checks and rollback

---

## Architecture & Design

Documentation covering system architecture and design decisions.

| Document | Description |
|----------|-------------|
| [multi-ecosystem-task-runner.md](./multi-ecosystem-task-runner.md) | Task runner architecture (Make + Invoke + npm) |

### Key Topics
- Multi-ecosystem coordination
- Task automation patterns
- Development workflow

---

## Development

Documentation for development environment and tooling.

| Document | Description |
|----------|-------------|
| [docker-dev-environment-implementation-plan.md](./docker-dev-environment-implementation-plan.md) | Docker development environment analysis |
| [uv-lock-migration-plan.md](./uv-lock-migration-plan.md) | Python dependency management with uv |

### Key Topics
- Docker development workflow
- Dependency management
- Reproducible builds

---

## Guidelines

### Documentation Standards

All documentation in this project should follow these guidelines:

1. **Table of Contents**: Every document should have a TOC at the top
2. **Mermaid Diagrams**: Use [Mermaid.js](https://mermaid.js.org/) for all diagrams
3. **Cross-References**: Link to related documents where applicable
4. **Code Examples**: Include runnable examples where possible
5. **Keep Updated**: Update docs when code changes

### Adding New Documentation

1. Create the markdown file in the appropriate location
2. Add a TOC at the top
3. Use Mermaid for any diagrams
4. Add entry to this index
5. Cross-reference from related docs

---

## Related Resources

- [GitHub Repository](https://github.com/dremdem/stupid_chat_bot)
- [Issue Tracker](https://github.com/dremdem/stupid_chat_bot/issues)
- [Pull Requests](https://github.com/dremdem/stupid_chat_bot/pulls)
