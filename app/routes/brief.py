"""
Brief API Routes
"""
import logging
import asyncio
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
from datetime import datetime
from pathlib import Path

from config import SQLITE_PATH, STATIC_DIR
from app.services.brief_generator import generate_daily_brief

router = APIRouter()
logger = logging.getLogger(__name__)

# Security: Date validation pattern
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def validate_date(date: str) -> str:
    """Validate date format to prevent injection"""
    if not DATE_PATTERN.match(date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date")
    return date

class BriefRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD format

class BriefResponse(BaseModel):
    id: int
    date: str
    title: str
    content: str
    source_count: int
    created_at: str

@router.get("/sources")
async def get_sources():
    """Get distinct source names from articles for dynamic category tabs"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.execute("""
        SELECT DISTINCT source_name, COUNT(*) as count
        FROM articles
        WHERE brief_id IS NOT NULL
        GROUP BY source_name
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {"name": r[0], "count": r[1]}
        for r in rows
    ]

@router.get("/latest")
async def get_latest_brief():
    """Get the latest brief"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.execute("""
        SELECT id, date, title, content, source_count, created_at
        FROM briefs ORDER BY date DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No brief found")

    return BriefResponse(
        id=row[0], date=row[1], title=row[2],
        content=row[3], source_count=row[4], created_at=row[5]
    )

@router.get("/list")
async def list_briefs(limit: int = 30):
    """List recent briefs"""
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.execute("""
        SELECT id, date, title, source_count, created_at
        FROM briefs ORDER BY date DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0], "date": r[1], "title": r[2],
            "source_count": r[3], "created_at": r[4]
        }
        for r in rows
    ]

@router.get("/{date}")
async def get_brief_by_date(date: str):
    """Get brief by date (YYYY-MM-DD)"""
    date = validate_date(date)
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT id, date, title, content, source_count, created_at
            FROM briefs WHERE date = ?
        """, (date,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"No brief for {date}")

    return BriefResponse(
        id=row[0], date=row[1], title=row[2],
        content=row[3], source_count=row[4], created_at=row[5]
    )

@router.post("/generate")
async def generate_brief(background_tasks: BackgroundTasks, request: BriefRequest = None):
    """
    Trigger brief generation
    Runs in background to avoid timeout
    """
    date = request.date if request else datetime.now().strftime("%Y-%m-%d")

    # Check if brief already exists
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.execute("SELECT id FROM briefs WHERE date = ?", (date,))
    existing = cursor.fetchone()
    conn.close()

    if existing:
        return {"status": "exists", "date": date, "id": existing[0]}

    # Add generation task to background
    background_tasks.add_task(generate_brief_task, date)

    return {"status": "generating", "date": date}

async def generate_brief_task(date: str):
    """
    Background task to generate brief
    Fetches sources, deduplicates, generates summary, saves to database
    """
    logger.info(f"Starting brief generation for {date}")

    try:
        result = await generate_daily_brief(date)

        if result.get("status") == "success":
            logger.info(
                f"Brief generated successfully for {date}: "
                f"id={result.get('brief_id')}, items={result.get('items_count')}"
            )
        else:
            logger.warning(f"Brief generation returned non-success: {result}")

    except Exception as e:
        logger.error(f"Failed to generate brief for {date}: {e}", exc_info=True)

@router.get("/page/{date}", response_class=HTMLResponse)
async def get_brief_page(date: str):
    """Serve brief as HTML page"""
    date = validate_date(date)
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT title, content FROM briefs WHERE date = ?
        """, (date,))
        row = cursor.fetchone()

    if not row:
        try:
            content = (STATIC_DIR / "index.html").read_text()
            return HTMLResponse(content=content)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Page not found")

    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{row[0]}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <article class="brief">
        <h1>{row[0]}</h1>
        <time datetime="{date}">{date}</time>
        <div class="content">{row[1]}</div>
    </article>
</body>
</html>
"""
    return HTMLResponse(content=html)