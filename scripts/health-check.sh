#!/bin/bash
# Health check script for AI Daily Brief v4
# Usage: bash scripts/health-check.sh [options]
#
# Options:
#   --json        Output in JSON format
#   --strict      Exit with non-zero code on any unhealthy component
#   --url URL     Override health check URL

set -e

# Default configuration
HEALTH_URL="${HEALTH_URL:-http://localhost:8080}"
METRICS_URL="${METRICS_URL:-http://localhost:8080/metrics}"

# Parse arguments
JSON_OUTPUT=false
STRICT_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --json) JSON_OUTPUT=true; shift ;;
        --strict) STRICT_MODE=true; shift ;;
        --url) HEALTH_URL="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Results storage
declare -A RESULTS

check_http_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}

    local response
    local http_code

    response=$(curl -sf -w "\n%{http_code}" "$url" 2>/dev/null) || {
        RESULTS[$name]="unhealthy"
        return 1
    }

    http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" = "$expected_status" ]; then
        RESULTS[$name]="healthy"
        return 0
    else
        RESULTS[$name]="unhealthy"
        return 1
    fi
}

check_docker_container() {
    local container_name=$1

    if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
        RESULTS["$container_name"]="healthy"
        return 0
    else
        RESULTS["$container_name"]="unhealthy"
        return 1
    fi
}

check_response_content() {
    local name=$1
    local url=$2
    local pattern=$3

    local response
    response=$(curl -sf "$url" 2>/dev/null) || {
        RESULTS[$name]="unhealthy"
        return 1
    }

    if echo "$response" | grep -q "$pattern"; then
        RESULTS[$name]="healthy"
        return 0
    else
        RESULTS[$name]="unhealthy"
        return 1
    fi
}

# Run checks
check_http_endpoint "health_endpoint" "$HEALTH_URL/health"
check_http_endpoint "ready_endpoint" "$HEALTH_URL/ready"
check_http_endpoint "metrics_endpoint" "$METRICS_URL"
check_docker_container "ai-brief-app"
check_response_content "api_status" "$HEALTH_URL/health" "healthy"

# Output results
if [ "$JSON_OUTPUT" = true ]; then
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"checks\": {"
    first=true
    for key in "${!RESULTS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        echo -n "    \"$key\": \"${RESULTS[$key]}\""
    done
    echo ""
    echo "  },"
    echo "  \"overall\": \"$([ "$(echo ${RESULTS[@]} | grep -o 'unhealthy' | wc -l)" -eq 0 ] && echo 'healthy' || echo 'degraded')\""
    echo "}"
else
    echo "=========================================="
    echo "  Health Check Results"
    echo "=========================================="
    echo ""
    for key in "${!RESULTS[@]}"; do
        if [ "${RESULTS[$key]}" = "healthy" ]; then
            echo -e "  [$GREEN OK $NC] $key"
        else
            echo -e "  [$RED FAIL $NC] $key"
        fi
    done
    echo ""

    # Overall status
    unhealthy_count=$(echo "${RESULTS[@]}" | grep -o 'unhealthy' | wc -l)
    if [ "$unhealthy_count" -eq 0 ]; then
        echo -e "Overall Status: $GREEN HEALTHY $NC"
    else
        echo -e "Overall Status: $RED DEGRADED $NC"
    fi
fi

# Exit with appropriate code
if [ "$STRICT_MODE" = true ]; then
    unhealthy_count=$(echo "${RESULTS[@]}" | grep -o 'unhealthy' | wc -l)
    if [ "$unhealthy_count" -gt 0 ]; then
        exit 1
    fi
fi

exit 0