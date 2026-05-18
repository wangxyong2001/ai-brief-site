#!/bin/bash
# Deploy script for AI Daily Brief v4
# Usage: bash scripts/deploy.sh [options]
#
# Options:
#   --skip-backup    Skip backup creation
#   --skip-tests     Skip health tests
#   --rollback       Rollback to previous version if health check fails

set -e

# Configuration
PROJECT_DIR="/home/tomabc/ai-brief-site-new"
BACKUP_DIR="$PROJECT_DIR/backups"
MAX_BACKUPS=10
HEALTH_RETRIES=5
HEALTH_INTERVAL=5
ROLLBACK_ON_FAILURE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
SKIP_BACKUP=false
SKIP_TESTS=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup) SKIP_BACKUP=true; shift ;;
        --skip-tests) SKIP_TESTS=true; shift ;;
        --no-rollback) ROLLBACK_ON_FAILURE=false; shift ;;
        *) shift ;;
    esac
done

echo "=========================================="
echo "  AI Daily Brief v4 - Deployment Script"
echo "=========================================="
echo ""

# Change to project directory
cd "$PROJECT_DIR" || { log_error "Project directory not found: $PROJECT_DIR"; exit 1; }

# Get current commit for reference
CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log_info "Current commit: $CURRENT_COMMIT"

# Step 1: Create backup
if [ "$SKIP_BACKUP" = false ]; then
    log_info "Creating backup..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"

    # Backup database
    if [ -d "data" ]; then
        cp -r data "$BACKUP_PATH/"
        log_info "Database backed up to $BACKUP_PATH/data"
    fi

    # Backup docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_PATH/"
    fi

    # Cleanup old backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
        log_info "Cleaning up old backups..."
        ls -1t "$BACKUP_DIR" | tail -n +$((MAX_BACKUPS + 1)) | while read dir; do
            rm -rf "$BACKUP_DIR/$dir"
        done
    fi
fi

# Step 2: Pull latest code
log_info "Pulling latest code..."
if [ -d ".git" ]; then
    git fetch origin
    git reset --hard origin/main
    NEW_COMMIT=$(git rev-parse --short HEAD)
    log_info "Updated to commit: $NEW_COMMIT"
else
    log_warn "Not a git repository, skipping git pull"
fi

# Step 3: Build Docker image
log_info "Building Docker image..."
docker-compose build --no-cache

# Step 4: Stop current container
log_info "Stopping current container..."
docker-compose down

# Step 5: Start new container
log_info "Starting new container..."
docker-compose up -d

# Step 6: Wait for startup
log_info "Waiting for application to start..."
sleep 10

# Step 7: Health check
if [ "$SKIP_TESTS" = false ]; then
    log_info "Running health check..."
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $HEALTH_RETRIES ]; do
        if curl -sf http://localhost:8080/health > /dev/null; then
            log_info "Health check passed!"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "Health check failed, attempt $RETRY_COUNT/$HEALTH_RETRIES"

        if [ $RETRY_COUNT -eq $HEALTH_RETRIES ]; then
            log_error "Health check failed after $HEALTH_RETRIES attempts"

            if [ "$ROLLBACK_ON_FAILURE" = true ] && [ "$SKIP_BACKUP" = false ]; then
                log_warn "Attempting rollback..."
                docker-compose down

                if [ -f "$BACKUP_PATH/docker-compose.yml" ]; then
                    cp "$BACKUP_PATH/docker-compose.yml" .
                fi

                if [ -d "$BACKUP_PATH/data" ]; then
                    rm -rf data
                    cp -r "$BACKUP_PATH/data" .
                fi

                docker-compose up -d
                sleep 10

                if curl -sf http://localhost:8080/health > /dev/null; then
                    log_info "Rollback successful!"
                else
                    log_error "Rollback failed!"
                fi
            fi

            exit 1
        fi

        sleep $HEALTH_INTERVAL
    done
fi

# Step 8: Verify deployment
log_info "Verifying deployment..."
CONTAINER_STATUS=$(docker ps --filter "name=ai-brief-app" --format "{{.Status}}")
log_info "Container status: $CONTAINER_STATUS"

# Step 9: Cleanup
log_info "Cleaning up unused Docker images..."
docker image prune -f

echo ""
log_info "=========================================="
log_info "  Deployment completed successfully!"
log_info "=========================================="
echo ""
echo "Application URL: http://localhost:8080"
echo "Health endpoint: http://localhost:8080/health"
echo "Metrics endpoint: http://localhost:8080/metrics"