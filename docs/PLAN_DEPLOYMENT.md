# Deployment Plan: Stupid Chat Bot to DigitalOcean

This document outlines the deployment strategy for releasing the Stupid Chat Bot application to a DigitalOcean droplet.

## Architecture Overview

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│  nginx (host) - stupidbot.dremdem.ru    │
│  - SSL/TLS (Let's Encrypt)              │
│  - Reverse proxy                        │
└─────────────────────────────────────────┘
    │                           │
    │ /api/*, /ws/*             │ /*
    ▼                           ▼
┌──────────────┐        ┌──────────────┐
│   Backend    │        │   Frontend   │
│   :8000      │        │   :3000      │
│   FastAPI    │        │   nginx      │
└──────────────┘        └──────────────┘
         │
         ▼
    ┌─────────┐
    │ SQLite  │
    │ volume  │
    └─────────┘
```

## Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Production Docker Setup | 🔄 In Progress |
| 2 | SQLite Persistence | 🔄 In Progress |
| 3 | GitHub Actions (Build & Push) | 🔄 In Progress |
| 4 | Manual Server Testing | ⏳ Pending |
| 5 | Host nginx Configuration | ⏳ Pending |
| 6 | Automated Deployment | ⏳ Pending |
| 7 | Documentation | ⏳ Pending |

---

## Phase 1: Production Docker Setup

### 1.1 Frontend Dockerfile

Multi-stage build with nginx for production:

```dockerfile
# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_WS_URL
ARG VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production stage
FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### 1.2 Frontend nginx.conf

```nginx
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

### 1.3 docker-compose.prod.yml

```yaml
services:
  backend:
    image: ghcr.io/dremdem/stupid_chat_bot-backend:latest
    container_name: stupidbot-backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DATABASE_PATH=/app/data/chat.db
    env_file:
      - .env
    volumes:
      - chat_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - stupidbot-network

  frontend:
    image: ghcr.io/dremdem/stupid_chat_bot-frontend:latest
    container_name: stupidbot-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - stupidbot-network

volumes:
  chat_data:
    name: stupidbot-data

networks:
  stupidbot-network:
    driver: bridge
```

---

## Phase 2: SQLite Persistence

### 2.1 Database Path Configuration

The database path is configurable via `DATABASE_PATH` environment variable:

```python
# backend/app/database.py
import os
DATABASE_PATH = os.getenv("DATABASE_PATH", "chat.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
```

### 2.2 Health Check Endpoint

```python
# backend/app/api/health.py
@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 2.3 Volume Mount

The `chat_data` volume in docker-compose.prod.yml ensures:
- Database persists across container restarts
- Database survives redeployments
- Data stored at `/app/data/chat.db` inside container

---

## Phase 3: GitHub Actions Workflow (Build & Push)

### 3.1 Workflow File

`.github/workflows/docker-release.yml`:

```yaml
name: Build and Push to GHCR

on:
  workflow_dispatch:
    inputs:
      tag:
        description: 'Image tag (default: latest)'
        required: false
        default: 'latest'

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ghcr.io/dremdem/stupid_chat_bot-backend
  FRONTEND_IMAGE: ghcr.io/dremdem/stupid_chat_bot-frontend

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          target: prod
          push: true
          tags: |
            ${{ env.BACKEND_IMAGE }}:${{ inputs.tag }}
            ${{ env.BACKEND_IMAGE }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          target: prod
          push: true
          tags: |
            ${{ env.FRONTEND_IMAGE }}:${{ inputs.tag }}
            ${{ env.FRONTEND_IMAGE }}:${{ github.sha }}
          build-args: |
            VITE_API_URL=
            VITE_WS_URL=
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Phase 4: Manual Server Testing

### 4.1 Prerequisites on Server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Create app directory
sudo mkdir -p /opt/stupidbot
sudo chown $USER:$USER /opt/stupidbot
cd /opt/stupidbot
```

### 4.2 Authenticate with GHCR

```bash
# Create a GitHub Personal Access Token with `read:packages` scope
# https://github.com/settings/tokens/new

# Login to GHCR
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 4.3 Create Configuration Files

```bash
# Create .env file with your API keys
cat > .env << 'EOF'
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
# OPENAI_API_KEY=sk-xxxxx
# GOOGLE_API_KEY=xxxxx
# DEEPSEEK_API_KEY=xxxxx
DATABASE_PATH=/app/data/chat.db
EOF

# Download docker-compose.prod.yml
curl -o docker-compose.prod.yml https://raw.githubusercontent.com/dremdem/stupid_chat_bot/master/docker-compose.prod.yml
```

### 4.4 Pull and Run

```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Start containers
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### 4.5 Test with IP Address

```bash
# Get your server's IP
curl ifconfig.me

# Test backend health
curl http://YOUR_SERVER_IP:8000/health

# Test frontend (open in browser)
# http://YOUR_SERVER_IP:3000
```

### 4.6 Troubleshooting

```bash
# Check container logs
docker logs stupidbot-backend
docker logs stupidbot-frontend

# Check if ports are open
sudo netstat -tlnp | grep -E '3000|8000'

# Restart containers
docker compose -f docker-compose.prod.yml restart

# Full reset
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## Phase 5: Host nginx Configuration (Future)

Template for `/etc/nginx/sites-available/stupidbot.dremdem.ru`:

```nginx
server {
    listen 80;
    server_name stupidbot.dremdem.ru;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name stupidbot.dremdem.ru;

    ssl_certificate /etc/letsencrypt/live/stupidbot.dremdem.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stupidbot.dremdem.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # API and WebSocket
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Phase 6: Automated Deployment (Future)

Will add deploy job to workflow that:
1. SSH to droplet
2. Generate `.env` from GitHub Secrets
3. Pull images and restart containers
4. Health check with rollback

---

## Phase 7: Documentation (Future)

- Complete DEPLOYMENT.md guide
- Backup and restore procedures
- Monitoring and logging setup

---

## GitHub Secrets Required

| Secret | Description | Phase |
|--------|-------------|-------|
| `DO_SSH_KEY` | SSH private key | 6 |
| `DO_HOST` | Droplet IP/hostname | 6 |
| `DO_USER` | SSH user | 6 |
| `AI_PROVIDER` | AI provider name | 6 |
| `ANTHROPIC_API_KEY` | Anthropic key | 6 |
| `OPENAI_API_KEY` | OpenAI key (optional) | 6 |
| `GOOGLE_API_KEY` | Google key (optional) | 6 |
| `DEEPSEEK_API_KEY` | DeepSeek key (optional) | 6 |

**Note:** For Phase 3-4, only `GITHUB_TOKEN` is needed (auto-provided).

---

## Related Issues

- Issue #42: Automated release to DO
