"""
Health Check Routes for SRE/SLO monitoring
"""
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
import sqlite3
import time
from pathlib import Path

from config import SQLITE_PATH, LANCEDB_PATH, SLO_ERROR_RATE_THRESHOLD, SLO_LATENCY_THRESHOLD_MS
from app.metrics import request_metrics

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic health check
    Returns 200 if all components are healthy
    """
    checks = {
        "status": "healthy",
        "components": {}
    }

    # Check SQLite
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("SELECT 1")
        conn.close()
        checks["components"]["sqlite"] = "healthy"
    except Exception as e:
        checks["components"]["sqlite"] = f"unhealthy: {str(e)}"
        checks["status"] = "degraded"

    # Check LanceDB directory
    if LANCEDB_PATH.exists():
        checks["components"]["lancedb"] = "healthy"
    else:
        checks["components"]["lancedb"] = "directory missing"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)

@router.get("/metrics")
async def metrics():
    """
    Prometheus-style metrics for SLO monitoring
    """
    total = request_metrics["total_requests"]
    errors = request_metrics["error_requests"]
    total_latency = request_metrics["total_latency_ms"]

    # Calculate current error rate
    error_rate = errors / total if total > 0 else 0

    # Calculate average latency
    avg_latency = total_latency / total if total > 0 else 0

    # SLO status
    slo_met = (
        error_rate <= SLO_ERROR_RATE_THRESHOLD and
        avg_latency <= SLO_LATENCY_THRESHOLD_MS
    )

    metrics_text = f"""
# HELP total_requests Total number of requests
# TYPE total_requests counter
total_requests {total}

# HELP error_requests Number of error requests (4xx/5xx)
# TYPE error_requests counter
error_requests {errors}

# HELP error_rate Current error rate
# TYPE error_rate gauge
error_rate {error_rate:.4f}

# HELP avg_latency_ms Average latency in milliseconds
# TYPE avg_latency_ms gauge
avg_latency_ms {avg_latency:.2f}

# HELP slo_met Whether SLO is being met
# TYPE slo_met gauge
slo_met {1 if slo_met else 0}

# HELP slo_error_threshold SLO error rate threshold
# TYPE slo_error_threshold gauge
slo_error_threshold {SLO_ERROR_RATE_THRESHOLD}

# HELP slo_latency_threshold SLO latency threshold in ms
# TYPE slo_latency_threshold gauge
slo_latency_threshold {SLO_LATENCY_THRESHOLD_MS}
"""

    return Response(content=metrics_text, media_type="text/plain")

@router.get("/ready")
async def readiness():
    """
    Readiness check - returns 200 when app can serve traffic
    """
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("SELECT 1 FROM briefs LIMIT 1")
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            content={"status": "not ready", "reason": str(e)},
            status_code=503
        )