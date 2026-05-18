#!/bin/bash
# Rollback script for AI Daily Brief v4
# Usage: bash scripts/rollback.sh [backup_name]
#
# If backup_name is not specified, rolls back to the most recent backup

set -e

# Configuration
PROJECT_DIR="/home/tomabc/ai-brief-site-new"
BACKUP_DIR="$PROJECT_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "  AI Daily Brief v4 - Rollback Script"
echo "=========================================="
echo ""

# Change to project directory
cd "$PROJECT_DIR" || { log_error "Project directory not found: $PROJECT_DIR"; exit 1; }

# List available backups
list_backups() {
    echo "Available backups:"
    echo "------------------"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        ls -1t "$BACKUP_DIR" | head -n 10
    else
        echo "No backups found"
        exit 1
    fi
}

# Determine which backup to restore
if [ -n "$1" ]; then
    RESTORE_PATH="$BACKUP_DIR/$1"
    if [ ! -d "$RESTORE_PATH" ]; then
        log_error "Backup not found: $1"
        list_backups
        exit 1
    fi
else
    # Find most recent backup
    LATEST_BACKUP=$(ls -1t "$BACKUP_DIR" 2>/dev/null | head -n 1)
    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No backups available for rollback"
        exit 1
    fi
    RESTORE_PATH="$BACKUP_DIR/$LATEST_BACKUP"
    log_info "Using most recent backup: $LATEST_BACKUP"
fi

echo ""
log_warn "This will rollback the application to a previous state."
log_warn "Current data will be replaced with backup data."
echo ""
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Rollback cancelled"
    exit 0
fi

# Step 1: Stop current container
log_info "Stopping current container..."
docker-compose down

# Step 2: Restore database
log_info "Restoring database..."
if [ -d "$RESTORE_PATH/data" ]; then
    rm -rf data
    cp -r "$RESTORE_PATH/data" .
    log_info "Database restored from backup"
else
    log_warn "No database backup found in $RESTORE_PATH"
fi

# Step 3: Restore docker-compose.yml if exists
if [ -f "$RESTORE_PATH/docker-compose.yml" ]; then
    cp "$RESTORE_PATH/docker-compose.yml" .
    log_info "docker-compose.yml restored"
fi

# Step 4: Rebuild and restart
log_info "Rebuilding and restarting..."
docker-compose build
docker-compose up -d

# Step 5: Wait for startup
log_info "Waiting for application to start..."
sleep 10

# Step 6: Health check
log_info "Running health check..."
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8080/health > /dev/null; then
        log_info "Health check passed!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_warn "Health check failed, attempt $RETRY_COUNT/$MAX_RETRIES"

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Rollback health check failed!"
        exit 1
    fi

    sleep 5
done

echo ""
log_info "=========================================="
log_info "  Rollback completed successfully!"
log_info "=========================================="
echo ""
echo "Application URL: http://localhost:8080"
echo "Health endpoint: http://localhost:8080/health"