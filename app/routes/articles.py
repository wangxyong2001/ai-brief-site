"""
Article Routes - Handle article detail and processing
"""
import json
import logging
import sqlite3
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from config import SQLITE_PATH, STATIC_DIR
from app.services.article_reader import read_article
from app.services.ai_summarizer import summarize_article

router = APIRouter()
logger = logging.getLogger(__name__)


class ArticleDetail(BaseModel):
    id: int
    original_link: str
    original_title: str
    chinese_title: Optional[str]
    source_name: str
    category: str
    key_points: Optional[str]
    tech_points: Optional[str]
    use_cases: Optional[str]
    industry_impact: Optional[str]
    chinese_summary: Optional[str]
    published_at: Optional[str]


class ProcessRequest(BaseModel):
    url: str
    source: str = "unknown"
    category: str = "news"


@router.get("/by-link")
async def get_article_by_link(url: str):
    """Get article by original link URL"""
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT id, original_link, original_title, chinese_title,
                   source_name, category, key_points, tech_points,
                   use_cases, industry_impact, chinese_summary, published_at
            FROM articles WHERE original_link = ?
        """, (url,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleDetail(
        id=row[0],
        original_link=row[1],
        original_title=row[2],
        chinese_title=row[3],
        source_name=row[4],
        category=row[5],
        key_points=row[6],
        tech_points=row[7],
        use_cases=row[8],
        industry_impact=row[9],
        chinese_summary=row[10],
        published_at=row[11]
    )


@router.get("/{article_id}")
async def get_article_detail(article_id: int):
    """Get processed article with Chinese summary"""
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT id, original_link, original_title, chinese_title,
                   source_name, category, key_points, tech_points,
                   use_cases, industry_impact, chinese_summary, published_at
            FROM articles WHERE id = ?
        """, (article_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleDetail(
        id=row[0],
        original_link=row[1],
        original_title=row[2],
        chinese_title=row[3],
        source_name=row[4],
        category=row[5],
        key_points=row[6],
        tech_points=row[7],
        use_cases=row[8],
        industry_impact=row[9],
        chinese_summary=row[10],
        published_at=row[11]
    )


@router.get("/brief/{brief_id}")
async def get_brief_articles(brief_id: int):
    """Get all articles for a brief"""
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT a.id, a.original_link, a.original_title, a.chinese_title,
                   a.source_name, a.category, a.chinese_summary, a.key_points
            FROM articles a
            JOIN briefs b ON a.brief_id = b.id
            WHERE b.id = ?
            ORDER BY a.score DESC
        """, (brief_id,))
        rows = cursor.fetchall()

    return [
        {
            "id": r[0],
            "link": r[1],
            "title": r[2],
            "chinese_title": r[3],
            "source": r[4],
            "category": r[5],
            "summary": r[6],
            "key_points": json.loads(r[7]) if r[7] else []
        }
        for r in rows
    ]


@router.post("/process")
async def process_article_url(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Fetch article, process through LLM, and store
    """
    # Check if already processed
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute(
            "SELECT id FROM articles WHERE original_link = ?",
            (request.url,)
        )
        existing = cursor.fetchone()

    if existing:
        return {"status": "exists", "article_id": existing[0]}

    # Add to background processing
    background_tasks.add_task(process_article_task, request.url, request.source, request.category)

    return {"status": "processing", "url": request.url}


async def process_article_task(url: str, source: str, category: str):
    """Background task to process article through LLM"""
    logger.info(f"Processing article: {url}")

    try:
        # 1. Fetch article content
        article = await read_article(url)
        if not article:
            logger.error(f"Failed to fetch article from {url}")
            return

        # 2. Process through LLM
        result = await summarize_article(article.get("content", article.get("text", "")))

        # 3. Store in database
        with sqlite3.connect(SQLITE_PATH) as conn:
            conn.execute("""
                INSERT INTO articles (
                    original_link, original_title, chinese_title, source_name,
                    category, key_points, tech_points, use_cases,
                    industry_impact, chinese_summary, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                article.get("title", ""),
                "",  # chinese_title from LLM if available
                source,
                category,
                result.core_points,
                result.technical_points,
                result.applications,
                result.industry_impact,
                result.chinese_summary,
                article.get("published_at", "")
            ))
            conn.commit()

        logger.info(f"Article processed successfully: {url}")

    except Exception as e:
        logger.error(f"Error processing article {url}: {e}")


@router.get("/detail/{article_id}", response_class=HTMLResponse)
async def get_article_page(article_id: int):
    """Render article detail as HTML page"""
    with sqlite3.connect(SQLITE_PATH) as conn:
        cursor = conn.execute("""
            SELECT original_link, original_title, chinese_title, source_name,
                   category, key_points, tech_points, use_cases,
                   industry_impact, chinese_summary, published_at
            FROM articles WHERE id = ?
        """, (article_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    # Parse key points if JSON
    key_points_html = ""
    if row[5]:
        try:
            points = json.loads(row[5])
            key_points_html = "".join(f"<li>{p}</li>" for p in points)
        except:
            key_points_html = f"<li>{row[5]}</li>"

    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{row[2] or row[1]} - AI Daily Brief</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="app-container">
        <header class="header">
            <div class="header-content">
                <a href="/" class="logo">
                    <h1>AI Daily Brief</h1>
                    <p class="tagline">每日AI领域动态精选</p>
                </a>
            </div>
        </header>

        <main class="main-content detail-page">
            <nav class="breadcrumb">
                <a href="/">首页</a>
                <span class="separator">/</span>
                <span class="current">文章详情</span>
            </nav>

            <article class="article-full">
                <header class="article-header">
                    <div class="article-category-badge">{row[4]}</div>
                    <h1 class="article-title">{row[2] or row[1]}</h1>
                    <div class="article-meta">
                        <time>{row[10] or datetime.now().strftime('%Y-%m-%d')}</time>
                        <span class="separator">·</span>
                        <span class="source">{row[3]}</span>
                    </div>
                </header>

                <section class="article-section">
                    <h2>摘要</h2>
                    <p>{row[9] or row[1]}</p>
                </section>

                <section class="article-section">
                    <h2>核心观点</h2>
                    <ul class="key-points">{key_points_html}</ul>
                </section>

                <section class="article-section">
                    <h2>技术要点</h2>
                    <div class="tech-points">{row[6] or '暂无'}</div>
                </section>

                <section class="article-section">
                    <h2>应用场景</h2>
                    <div class="app-scenarios">{row[7] or '暂无'}</div>
                </section>

                <section class="article-section">
                    <h2>行业影响</h2>
                    <p>{row[8] or '暂无'}</p>
                </section>

                <footer class="article-footer">
                    <a href="{row[0]}" target="_blank" rel="noopener" class="btn-primary">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                            <polyline points="15 3 21 3 21 9"/>
                            <line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                        查看原文
                    </a>
                </footer>
            </article>
        </main>

        <footer class="footer">
            <p>Powered by FastAPI + LanceDB</p>
        </footer>
    </div>

    <script src="/static/js/app.js"></script>
</body>
</html>
"""
    return HTMLResponse(content=html)