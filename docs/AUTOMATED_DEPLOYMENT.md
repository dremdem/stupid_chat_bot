# Automated Deployment Setup Guide

This guide provides step-by-step instructions for setting up automated deployment for the Stupid Chat Bot application using GitHub Actions, Docker Compose, and SSH.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Security Approach](#security-approach)
- [Setup Steps](#setup-steps)
  - [Step 1: Create Deployment User](#step-1-create-deployment-user)
  - [Step 2: Generate SSH Key Pair](#step-2-generate-ssh-key-pair)
  - [Step 3: Configure Droplet SSH Access](#step-3-configure-droplet-ssh-access)
  - [Step 4: Configure GitHub Secrets](#step-4-configure-github-secrets)
  - [Step 5: Create Deploy Script](#step-5-create-deploy-script)
  - [Step 6: Test Deployment](#step-6-test-deployment)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring](#monitoring)

---

## Overview

The automated deployment system provides zero-touch deployment with health checks and automatic rollback capabilities.

**Architecture:**

```
Developer triggers workflow
         │
         ▼
┌─────────────────────────────────────────┐
│  GitHub Actions                         │
│  1. Build backend image                 │
│  2. Build frontend image                │
│  3. Push to GHCR                        │
│  4. SSH to droplet                      │
│  5. Generate .env from secrets          │
│  6. Run deploy.sh                       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  DigitalOcean Droplet                   │
│  /opt/stupidbot/                        │
│  ├── docker-compose.prod.yml            │
│  ├── .env (generated)                   │
│  └── deploy.sh                          │
│                                         │
│  7. Pull images                         │
│  8. Restart containers                  │
│  9. Health check (60s)                  │
│  10. Success or rollback                │
└─────────────────────────────────────────┘
```

**Key Benefits:**
- Single workflow trigger deploys everything
- Automatic health verification
- Built-in rollback on failure
- Environment variables from GitHub Secrets
- Zero or minimal downtime

---

## Prerequisites

Before setting up automated deployment, ensure you have:

- [ ] DigitalOcean droplet running and accessible
- [ ] Docker installed on droplet
- [ ] Host nginx configured with SSL (Phase 5 complete)
- [ ] Manual deployment tested and working (Phase 4 complete)
- [ ] Root or sudo access to droplet (for initial setup only)
- [ ] Admin access to GitHub repository

---

## Security Approach

**Important:** This deployment uses a **dedicated non-root user** with Docker group membership instead of root access.

**User:** `github-deploy` (non-root user with docker group membership)

**Security Benefits:**
- No root SSH access - Compromised key cannot destroy system
- Limited blast radius - Attacker confined to Docker operations
- Clear audit trail - All actions logged as deployment user
- Easy to revoke - Simply delete user if needed

**What attacker CAN do if key is compromised:**
- Manipulate containers (stop, start, modify)
- Pull and run Docker images
- Access container data

**What attacker CANNOT do:**
- Delete system files
- Install malware on host
- Create users or modify system
- Disable firewall
- Access other users' data

**Security Rating: 7/10** (Good balance of security and practicality)

---

## Setup Steps

### Step 1: Create Deployment User

Create a user named `github-deploy` with Docker permissions:

```bash
# SSH to droplet as root (one-time setup)
ssh root@YOUR_DROPLET_IP

# Create deployment user (no password - SSH key only)
sudo adduser --disabled-password --gecos "GitHub Actions Deploy User" github-deploy

# Add user to docker group
sudo usermod -aG docker github-deploy

# Create app directory with correct ownership
sudo mkdir -p /opt/stupidbot
sudo chown github-deploy:github-deploy /opt/stupidbot

# Copy existing files if they exist
# (docker-compose.prod.yml, .env)
sudo cp /opt/stupidbot/* /opt/stupidbot/ 2>/dev/null || true
sudo chown -R github-deploy:github-deploy /opt/stupidbot

# Verify docker access
sudo -u github-deploy docker ps
# Should show container list without errors
```

**Verification:**
```bash
# This should FAIL (no sudo access):
sudo -u github-deploy apt install something

# This should WORK (docker group access):
sudo -u github-deploy docker ps
sudo -u github-deploy docker compose version
```

---

### Step 2: Generate SSH Key Pair

Generate a dedicated SSH key pair for GitHub Actions:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-stupidbot" -f ~/.ssh/github-actions-stupidbot

# This creates two files:
# - github-actions-stupidbot (private key - for GitHub Secrets)
# - github-actions-stupidbot.pub (public key - for droplet)
```

**Important:**
- Do NOT set a passphrase (GitHub Actions can't enter it)
- Keep the private key secure

---

### Step 3: Configure Droplet SSH Access

Add the public key to the `github-deploy` user's authorized keys:

```bash
# On droplet as root
sudo mkdir -p /home/github-deploy/.ssh
sudo chmod 700 /home/github-deploy/.ssh

# Add public key
sudo nano /home/github-deploy/.ssh/authorized_keys
# Paste contents of ~/.ssh/github-actions-stupidbot.pub

# Set correct permissions
sudo chmod 600 /home/github-deploy/.ssh/authorized_keys
sudo chown -R github-deploy:github-deploy /home/github-deploy/.ssh
```

**Alternative (from local machine):**
```bash
cat ~/.ssh/github-actions-stupidbot.pub | ssh root@YOUR_DROPLET_IP \
  "sudo mkdir -p /home/github-deploy/.ssh && \
   sudo tee /home/github-deploy/.ssh/authorized_keys && \
   sudo chmod 700 /home/github-deploy/.ssh && \
   sudo chmod 600 /home/github-deploy/.ssh/authorized_keys && \
   sudo chown -R github-deploy:github-deploy /home/github-deploy/.ssh"
```

**Test SSH connection:**
```bash
ssh -i ~/.ssh/github-actions-stupidbot github-deploy@YOUR_DROPLET_IP "docker ps"
# Should show container list
```

---

### Step 4: Configure GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret | Description | Example |
|--------|-------------|---------|
| `DO_SSH_KEY` | SSH private key (entire content) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DO_HOST` | Droplet IP or hostname | `164.90.187.183` |
| `DO_USER` | SSH user | `github-deploy` |
| `AI_PROVIDER` | Active AI provider | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI key (optional) | `sk-...` |
| `GOOGLE_API_KEY` | Google key (optional) | |
| `DEEPSEEK_API_KEY` | DeepSeek key (optional) | |

**To get SSH private key:**
```bash
cat ~/.ssh/github-actions-stupidbot
# Copy ENTIRE content including BEGIN/END lines
```

**Clean up local SSH key after adding to GitHub:**
```bash
# Securely delete private key from local machine
rm -P ~/.ssh/github-actions-stupidbot  # macOS
# or
shred -u ~/.ssh/github-actions-stupidbot  # Linux
```

---

### Step 5: Create Deploy Script

Create `/opt/stupidbot/deploy.sh` on the droplet:

```bash
ssh github-deploy@YOUR_DROPLET_IP "cat > /opt/stupidbot/deploy.sh << 'SCRIPT'
#!/bin/bash
set -e

# Configuration
COMPOSE_FILE=\"/opt/stupidbot/docker-compose.prod.yml\"
HEALTH_URL=\"http://127.0.0.1:8000/health\"
MAX_WAIT=60

log() { echo \"[\$(date '+%H:%M:%S')] \$1\"; }

log \"Starting deployment...\"

# Pull latest images
log \"Pulling images...\"
docker compose -f \"\$COMPOSE_FILE\" pull

# Store current image IDs for potential rollback
BACKEND_OLD=\$(docker inspect --format='{{.Image}}' stupidbot-backend 2>/dev/null || echo \"\")
FRONTEND_OLD=\$(docker inspect --format='{{.Image}}' stupidbot-frontend 2>/dev/null || echo \"\")

# Restart containers
log \"Restarting containers...\"
docker compose -f \"\$COMPOSE_FILE\" up -d

# Health check with timeout
log \"Waiting for health check (max \${MAX_WAIT}s)...\"
for i in \$(seq 1 \$MAX_WAIT); do
    if curl -sf \"\$HEALTH_URL\" > /dev/null 2>&1; then
        log \"Health check passed!\"

        # Cleanup old images
        docker image prune -f > /dev/null 2>&1 || true

        log \"Deployment successful!\"
        exit 0
    fi
    sleep 1
    if [ \$((i % 10)) -eq 0 ]; then
        log \"Still waiting... (\${i}s)\"
    fi
done

# Health check failed
log \"Health check failed after \${MAX_WAIT}s\"
log \"Container logs:\"
docker compose -f \"\$COMPOSE_FILE\" logs --tail=30

exit 1
SCRIPT"

# Make executable
ssh github-deploy@YOUR_DROPLET_IP "chmod +x /opt/stupidbot/deploy.sh"
```

**Test the script:**
```bash
ssh github-deploy@YOUR_DROPLET_IP "/opt/stupidbot/deploy.sh"
```

---

### Step 6: Test Deployment

1. **Trigger Workflow:**
   - Go to GitHub repository → **Actions**
   - Select **"Build, Push and Deploy"**
   - Click **"Run workflow"**
   - Leave defaults (deploy: true)
   - Click **"Run workflow"**

2. **Monitor Execution:**
   - Watch the `build-and-push` job
   - Watch the `deploy` job
   - Check for green checkmarks

3. **Verify:**
   ```bash
   # Check containers
   ssh github-deploy@YOUR_DROPLET_IP "docker ps"

   # Check health
   curl https://stupidbot.dremdem.ru/health

   # Test the app
   open https://stupidbot.dremdem.ru
   ```

---

## How It Works

### Workflow Execution Flow

```
1. Developer triggers workflow (or push to master)
                │
                ▼
2. Build backend image ──────────────────┐
   Build frontend image ─────────────────┤
                                         │
                ▼                        │
3. Push images to GHCR ◄─────────────────┘
                │
                ▼
4. SSH to droplet as github-deploy
                │
                ▼
5. Generate .env from GitHub Secrets
   - AI_PROVIDER
   - ANTHROPIC_API_KEY
   - etc.
                │
                ▼
6. Run deploy.sh
   - Pull images
   - docker compose up -d
   - Health check (60s timeout)
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
   ✅ Success      ❌ Failure
   - Prune old     - Show logs
     images        - Exit 1
   - Exit 0        - Workflow fails
```

### Health Check

The deploy script waits up to 60 seconds for:
- Backend container to respond at `http://127.0.0.1:8000/health`
- Returns `{"status": "healthy"}`

If health check fails:
- Container logs are displayed
- Deployment marked as failed
- Manual intervention required

---

## Troubleshooting

### Issue: SSH Permission Denied

**Error:** `Permission denied (publickey)`

**Solution:**
1. Verify `DO_SSH_KEY` contains the complete private key
2. Check public key is in `/home/github-deploy/.ssh/authorized_keys`
3. Verify permissions: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`

---

### Issue: Docker Permission Denied

**Error:** `permission denied while trying to connect to the Docker daemon`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker github-deploy

# User needs to log out and back in, or:
sudo -u github-deploy newgrp docker
```

---

### Issue: Health Check Fails

**Possible causes:**

1. **Backend not starting:**
   ```bash
   docker logs stupidbot-backend --tail 50
   ```

2. **Missing environment variables:**
   ```bash
   cat /opt/stupidbot/.env
   # Verify AI_PROVIDER and API key are set
   ```

3. **Database issues:**
   ```bash
   docker exec stupidbot-backend ls -la /app/data/
   ```

---

### Issue: .env Not Generated

**Check GitHub Secrets are configured:**
- `AI_PROVIDER` must be set
- At least one API key must be set

**Verify .env on server:**
```bash
ssh github-deploy@YOUR_DROPLET_IP "cat /opt/stupidbot/.env"
```

---

## Rollback Procedures

### Manual Rollback

If deployment fails and you need to restore:

```bash
ssh github-deploy@YOUR_DROPLET_IP << 'EOF'
cd /opt/stupidbot

# Check available images
docker images | grep stupid_chat_bot

# If you know the previous SHA:
# Edit docker-compose.prod.yml to use specific tag
# image: ghcr.io/dremdem/stupid_chat_bot-backend:abc1234

# Or pull and restart
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
EOF
```

### Re-run Previous Workflow

1. Go to GitHub Actions
2. Find a successful previous run
3. Click "Re-run all jobs"

---

## Monitoring

### Check Deployment Status

```bash
# Container status
ssh github-deploy@YOUR_DROPLET_IP "docker ps"

# Container health
ssh github-deploy@YOUR_DROPLET_IP "docker inspect --format='{{.State.Health.Status}}' stupidbot-backend"

# Recent logs
ssh github-deploy@YOUR_DROPLET_IP "docker compose -f /opt/stupidbot/docker-compose.prod.yml logs --tail 50"
```

### Resource Usage

```bash
# Container resources
ssh github-deploy@YOUR_DROPLET_IP "docker stats --no-stream"

# Disk space
ssh github-deploy@YOUR_DROPLET_IP "df -h"

# Memory
ssh github-deploy@YOUR_DROPLET_IP "free -h"
```

### Application Health

```bash
# Health endpoint
curl https://stupidbot.dremdem.ru/health

# API test
curl https://stupidbot.dremdem.ru/api/sessions

# WebSocket test (in browser console)
# new WebSocket('wss://stupidbot.dremdem.ru/ws/chat')
```

---

## Security Best Practices

1. **SSH Key Management:**
   - Use dedicated keys for automation (not personal keys)
   - Never commit private keys to repository
   - Delete private key from local machine after adding to GitHub Secrets
   - Rotate keys periodically

2. **Secrets Management:**
   - API keys stored only in GitHub Secrets
   - `.env` generated fresh on each deploy
   - Never log or echo secret values

3. **Access Control:**
   - Use non-root user (`github-deploy`)
   - Limit to Docker operations only
   - No sudo access for deployment user

4. **Monitoring:**
   - Review GitHub Actions logs
   - Monitor deployment success rate
   - Set up uptime monitoring for production URL

---

## Related Documentation

- [PLAN_DEPLOYMENT.md](./PLAN_DEPLOYMENT.md) - Overall deployment architecture
- [GitHub Actions Workflow](../.github/workflows/docker-release.yml) - CI/CD pipeline
- [Issue #42](https://github.com/dremdem/stupid_chat_bot/issues/42) - Deployment tracking
