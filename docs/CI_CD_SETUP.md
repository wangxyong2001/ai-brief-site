# CI/CD Configuration Guide

## GitHub Secrets Configuration

Navigate to: Repository → Settings → Secrets and variables → Actions → New repository secret

### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `VPS_HOST` | VPS hostname or IP | `tomabc.com` |
| `VPS_PORT` | SSH port | `60022` |
| `VPS_USER` | SSH username | `tomabc` |
| `VPS_SSH_KEY` | Private SSH key for VPS access | (See below) |
| `VPS_PROJECT_PATH` | Project directory on VPS | `/home/tomabc/ai-brief-site-new` |
| `GLM_API_KEY` | GLM API key for brief generation | `your-api-key` |

### Optional Secrets

| Secret Name | Description | Default |
|-------------|-------------|---------|
| `SLACK_WEBHOOK_URL` | Slack notification webhook | None |

### SSH Key Setup

1. Generate a dedicated deployment key (if not already done):
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy
   ```

2. Add the public key to VPS:
   ```bash
   ssh-copy-id -i ~/.ssh/github_actions_deploy.pub -p 60022 tomabc@tomabc.com
   ```

3. Copy the private key content for GitHub Secret:
   ```bash
   cat ~/.ssh/github_actions_deploy
   ```

4. Add as `VPS_SSH_KEY` in GitHub Secrets (include the `-----BEGIN` and `-----END` lines)

## VPS Prerequisites

Before the first deployment, ensure on VPS:

```bash
# SSH to VPS
ssh -p 60022 tomabc@tomabc.com

# Clone the repository
cd /home/tomabc
git clone https://github.com/YOUR_USERNAME/ai-brief-site-new.git ai-brief-site-new
cd ai-brief-site-new

# Make scripts executable
chmod +x scripts/*.sh deploy.sh

# Create required directories
mkdir -p backups data/lancedb

# Test Docker access
docker ps
```

## Workflow Triggers

### Deploy Workflow (deploy.yml)

| Trigger | Description |
|---------|-------------|
| Push to `main` | Automatic deployment on merge |
| Manual dispatch | Via GitHub Actions UI |

### Schedule Workflow (schedule.yml)

| Trigger | Description |
|---------|-------------|
| Cron: `0 0 * * *` | Daily at 00:00 UTC (08:00 Beijing time) |
| Manual dispatch | Via GitHub Actions UI with optional date parameter |

## Deployment Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Lint      │────▶│   Build     │────▶│   Test      │────▶│   Deploy    │
│  (Code QA)  │     │  (Docker)   │     │  (Health)   │     │   (VPS)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                    │
                                                              ┌─────▼─────┐
                                                              │  Verify   │
                                                              │ (Health)  │
                                                              └───────────┘
```

## Rollback Procedure

### Automatic Rollback

The deployment script automatically rolls back if:
1. Health check fails after max retries (5 attempts)
2. Previous backup exists in `backups/` directory

### Manual Rollback

```bash
# SSH to VPS
ssh -p 60022 tomabc@tomabc.com
cd /home/tomabc/ai-brief-site-new

# List available backups
ls -la backups/

# Rollback to specific backup
bash scripts/rollback.sh 20240101_120000

# Or rollback to most recent backup
bash scripts/rollback.sh
```

## Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Overall health | `{"status": "healthy"}` |
| `/ready` | Readiness check | `{"status": "ready"}` |
| `/metrics` | Prometheus metrics | Plain text metrics |

## Troubleshooting

### Common Issues

1. **SSH Permission Denied**
   - Verify `VPS_SSH_KEY` is correctly set
   - Check public key is in VPS `~/.ssh/authorized_keys`

2. **Docker Permission Denied**
   - User must be in `docker` group: `sudo usermod -aG docker tomabc`

3. **Health Check Timeout**
   - Increase `sleep` time in deploy script
   - Check container logs: `docker logs ai-brief-app`

4. **Git Pull Fails**
   - Ensure VPS has access to the repository
   - For private repos, configure deploy keys

### Viewing Logs

```bash
# Container logs
docker logs -f ai-brief-app

# Deployment logs (on VPS)
cd /home/tomabc/ai-brief-site-new
cat backups/*/deploy.log 2>/dev/null || echo "No deploy logs found"
```

## Security Recommendations

1. **Never commit secrets** to the repository
2. **Use GitHub Environments** for production/staging separation
3. **Rotate SSH keys** periodically
4. **Limit SSH key access** to specific commands if possible
5. **Enable branch protection** rules for `main` branch