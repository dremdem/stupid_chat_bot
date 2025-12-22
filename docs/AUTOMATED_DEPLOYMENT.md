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

### Step 1: Configure Deployment User

If you already have a `github-deploy` user from another project (e.g., [cv_profile](https://github.com/dremdem/cv_profile/blob/master/docs/AUTOMATED_DEPLOYMENT.md#step-1-create-deployment-user)), you can **reuse it**. Just grant access to the stupidbot directory:

```bash
# SSH to droplet as root
ssh root@YOUR_DROPLET_IP

# Grant existing github-deploy user access to stupidbot directory
sudo chown -R github-deploy:github-deploy /opt/stupidbot

# Verify docker access still works
sudo -u github-deploy docker ps
```

**Skip to [Step 4](#step-4-configure-github-secrets)** if reusing existing user and SSH key.

---

**If you need to create a new user** (first time setup):

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

#### If reusing existing `github-deploy` user from cv_profile:

**Note:** GitHub Secrets are write-only - you cannot view/copy values from another repo's secrets.

**Option A:** If you still have the SSH key file locally:
```bash
# Check if key exists
ls -la ~/.ssh/ | grep github-actions

# If found, use it
cat ~/.ssh/github-actions-deploy  # or your key filename
# Copy the entire content for DO_SSH_KEY
```

**Option B:** If you deleted the local key (as recommended), generate a new one:
```bash
# Generate new key
ssh-keygen -t ed25519 -C "github-actions-stupidbot" -f ~/.ssh/github-actions-stupidbot

# Add public key to droplet (append, don't replace!)
cat ~/.ssh/github-actions-stupidbot.pub | ssh root@YOUR_DROPLET_IP \
  "cat >> /home/github-deploy/.ssh/authorized_keys"

# Use private key for DO_SSH_KEY secret
cat ~/.ssh/github-actions-stupidbot
```

**For DO_HOST and DO_USER:** These aren't secrets - just use the same values:
- `DO_HOST` = your droplet IP (same as cv_profile)
- `DO_USER` = `github-deploy`

#### Required Secrets:

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

**Note:** `DO_HOST` and `DO_USER` will likely be the same as cv_profile's `DROPLET_HOST` and `DROPLET_USER`.

**If you generated a new SSH key:**
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

### Step 5: Deployment Scripts (No Manual Setup Required)

The deployment scripts are **stored in the repository** and automatically copied to the server during deployment:

- [`deploy.sh`](../deploy.sh) - Deployment script with health checks and rollback
- [`docker-compose.prod.yml`](../docker-compose.prod.yml) - Production compose file

**The workflow automatically:**
1. Copies `docker-compose.prod.yml` to `/opt/stupidbot/`
2. Copies `deploy.sh` to `/opt/stupidbot/`
3. Generates `.env` from GitHub Secrets
4. Runs `deploy.sh`

**No manual script creation needed!** Any changes to these files are automatically deployed.

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
1. Developer triggers workflow
                │
                ▼
2. Build & push images to GHCR
   - Backend image
   - Frontend image
                │
                ▼
3. SSH to droplet (github-deploy user)
                │
                ▼
4. Copy files from repo to server
   - docker-compose.prod.yml
   - deploy.sh
                │
                ▼
5. Generate .env from GitHub Secrets
   - AI_PROVIDER
   - ANTHROPIC_API_KEY
   - etc.
                │
                ▼
6. Run deploy.sh
   - Pull latest images
   - docker compose up -d
   - Health check (60s timeout)
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
   ✅ Success      ❌ Failure
   - Cleanup old   - Show logs
     images        - Attempt rollback
   - Exit 0        - Exit 1
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
