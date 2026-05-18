#!/bin/bash
# Deploy script for ai-brief-site
# Usage: bash deploy.sh

set -e

echo "=== AI Brief Site Deploy ==="

# 1. Pull latest code (if git repo)
if [ -d .git ]; then
    git pull origin main
fi

# 2. Build Docker image
docker-compose build

# 3. Stop old container
docker-compose down

# 4. Start new container
docker-compose up -d

# 5. Wait for health check
echo "Waiting for container to be healthy..."
sleep 10

# 6. Verify
if curl -f http://localhost:8080/health; then
    echo "✅ Deploy successful!"
else
    echo "❌ Health check failed, rolling back..."
    docker-compose down
    exit 1
fi

echo "=== Deploy Complete ==="