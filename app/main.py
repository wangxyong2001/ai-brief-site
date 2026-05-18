"""
FastAPI Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time
import sqlite3
from pathlib import Path

from config import (
    STATIC_DIR, DATA_DIR, SQLITE_PATH, LANCEDB_PATH,
    API_PORT, DEBUG, SLO_ERROR_RATE_THRESHOLD, SLO_LATENCY_THRESHOLD_MS
)
from app.routes import brief, health, articles
from app.metrics import request_metrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    # Ensure data directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LANCEDB_PATH.mkdir(parents=True, exist_ok=True)

    # Initialize SQLite
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'unknown',
            embedding_id TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            brief_id INTEGER REFERENCES briefs(id)
        )
    """)
    # Articles table for LLM-processed detailed content
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_link TEXT NOT NULL,
            original_title TEXT NOT NULL,
            chinese_title TEXT,
            source_name TEXT NOT NULL,
            category TEXT DEFAULT 'news',
            weight INTEGER DEFAULT 5,
            key_points TEXT,
            tech_points TEXT,
            use_cases TEXT,
            industry_impact TEXT,
            chinese_summary TEXT,
            published_at TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            brief_id INTEGER REFERENCES briefs(id),
            score INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_brief_id ON articles(brief_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
    conn.commit()
    conn.close()

    print(f"Database initialized at {SQLITE_PATH}")
    yield

app = FastAPI(
    title="AI Daily Brief",
    description="AI Daily Brief with semantic deduplication",
    version="0.4.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(brief.router, prefix="/api/brief", tags=["brief"])
app.include_router(health.router, tags=["health"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def index():
    """Serve main page"""
    return FileResponse(STATIC_DIR / "index.html")

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Collect request metrics for SLO monitoring"""
    start = time.time()
    request_metrics["total_requests"] += 1

    response = await call_next(request)

    latency_ms = (time.time() - start) * 1000
    request_metrics["total_latency_ms"] += latency_ms

    if response.status_code >= 400:
        request_metrics["error_requests"] += 1

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)