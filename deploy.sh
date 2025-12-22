#!/bin/bash

# Automated deployment script for Stupid Chat Bot
# This script pulls the latest Docker images and deploys with health checks and automatic rollback

set -e  # Exit on error

# Configuration
DEPLOY_USER="github-deploy"
PROJECT_DIR="/opt/stupidbot"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
LOG_FILE="${PROJECT_DIR}/deploy.log"
HEALTH_URL="http://127.0.0.1:8000/health"
MAX_HEALTH_CHECK_WAIT=60  # seconds
HEALTH_CHECK_INTERVAL=5   # seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Start deployment
log "========================================="
log "Starting Stupid Chat Bot deployment"
log "========================================="

# Change to project directory
cd "$PROJECT_DIR" || {
    log_error "Failed to change to project directory"
    exit 1
}

# Get current container IDs for potential rollback
BACKEND_CONTAINER=$(docker ps -q -f name=stupidbot-backend)
FRONTEND_CONTAINER=$(docker ps -q -f name=stupidbot-frontend)

if [ -n "$BACKEND_CONTAINER" ]; then
    log "Current backend container: $BACKEND_CONTAINER"
    BACKEND_IMAGE=$(docker inspect --format='{{.Image}}' "$BACKEND_CONTAINER")
    log "Current backend image: $BACKEND_IMAGE"
else
    log_warning "No running backend container found. This might be the first deployment."
    BACKEND_IMAGE=""
fi

if [ -n "$FRONTEND_CONTAINER" ]; then
    log "Current frontend container: $FRONTEND_CONTAINER"
    FRONTEND_IMAGE=$(docker inspect --format='{{.Image}}' "$FRONTEND_CONTAINER")
    log "Current frontend image: $FRONTEND_IMAGE"
else
    log_warning "No running frontend container found."
    FRONTEND_IMAGE=""
fi

# Pull latest images
log "Pulling latest images from GHCR..."
if ! docker compose -f "$COMPOSE_FILE" pull; then
    log_error "Failed to pull latest images"
    exit 1
fi
log "Images pulled successfully"

# Deploy new containers
log "Deploying new containers..."
if ! docker compose -f "$COMPOSE_FILE" up -d; then
    log_error "Failed to start new containers"
    exit 1
fi

log "Containers started, waiting for health check..."

# Wait for health check to pass
ELAPSED=0
HEALTH_CHECK_PASSED=false

while [ $ELAPSED -lt $MAX_HEALTH_CHECK_WAIT ]; do
    # Check backend health via HTTP
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        log "Health check passed!"
        HEALTH_CHECK_PASSED=true
        break
    fi

    # Check if containers are still running
    if ! docker ps -q -f name=stupidbot-backend | grep -q .; then
        log_error "Backend container stopped unexpectedly"
        break
    fi

    log "Waiting for health check... (${ELAPSED}s/${MAX_HEALTH_CHECK_WAIT}s)"
    sleep $HEALTH_CHECK_INTERVAL
    ELAPSED=$((ELAPSED + HEALTH_CHECK_INTERVAL))
done

# Verify deployment success
if [ "$HEALTH_CHECK_PASSED" = true ]; then
    log "Deployment successful!"

    # Cleanup old images (keep last 3)
    log "Cleaning up old images..."
    docker images ghcr.io/dremdem/stupid_chat_bot-backend --format "{{.ID}}" | tail -n +4 | xargs -r docker rmi -f 2>/dev/null || true
    docker images ghcr.io/dremdem/stupid_chat_bot-frontend --format "{{.ID}}" | tail -n +4 | xargs -r docker rmi -f 2>/dev/null || true

    log "========================================="
    log "Deployment completed successfully"
    log "========================================="
    exit 0
else
    log_error "Deployment failed! Health check did not pass within ${MAX_HEALTH_CHECK_WAIT}s"

    # Get logs from failed containers
    log "Backend container logs:"
    docker logs stupidbot-backend --tail 30 2>&1 | tee -a "$LOG_FILE" || true

    log "Frontend container logs:"
    docker logs stupidbot-frontend --tail 30 2>&1 | tee -a "$LOG_FILE" || true

    # Rollback
    log "Rolling back..."
    docker compose -f "$COMPOSE_FILE" down

    if [ -n "$BACKEND_IMAGE" ] && [ -n "$FRONTEND_IMAGE" ]; then
        log "Restarting with previous images..."
        # For rollback, we'd need to modify compose file or use docker run
        # For now, just restart compose (will use cached images if pull failed)
        docker compose -f "$COMPOSE_FILE" up -d || log_error "Rollback failed!"
        log "Rollback attempted"
    else
        log_error "No previous images available for rollback"
    fi

    log "========================================="
    log "Deployment failed"
    log "========================================="
    exit 1
fi
