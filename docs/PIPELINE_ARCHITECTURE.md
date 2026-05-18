# AI Daily Brief v4 - Article Processing Pipeline Architecture

## Overview

This document describes the architecture for upgrading the article processing pipeline to support full content reading and LLM-powered translation/summarization with structured Chinese output.

---

## 1. System Architecture

```
                                    +---------------------------+
                                    |      User Browser         |
                                    +-------------+-------------+
                                                  |
                                                  | HTTPS
                                                  v
                                    +---------------------------+
                                    |       Nginx               |
                                    |  ai.tomabc.com            |
                                    +-------------+-------------+
                                                  |
                                                  v
+---------------------------+     +---------------------------+
|      Static Files         |     |      FastAPI App          |
|  /static/*                 |<----|  :8000                    |
+---------------------------+     +-------------+-------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    |                             |                             |
                    v                             v                             v
        +-------------------+         +-------------------+         +-------------------+
        |   Article Fetch   |         |   LLM Processing  |         |   Storage Layer   |
        |   Pipeline        |-------->|   Pipeline        |-------->|   (SQLite +       |
        |                   |         |                   |         |    LanceDB)       |
        +-------------------+         +-------------------+         +-------------------+
                    |                             |
                    v                             v
        +-------------------+         +-------------------+
        |   External APIs   |         |   LLM APIs        |
        |   RSS/arXiv/      |         |   GLM/Claude      |
        |   GitHub/Web      |         |                   |
        +-------------------+         +-------------------+
```

---

## 2. Pipeline Stages

### Stage 1: Article Fetch Flow

```
RSS Feed / arXiv / GitHub / Web URL
            |
            v
    +-------------------+
    |  URL Extraction   |  <-- Get article URLs from feeds
    +-------------------+
            |
            v
    +-------------------+
    |  Content Fetcher  |  <-- Parallel fetch with rate limiting
    +-------------------+
            |
            v
    +-------------------+
    |  HTML Parser      |  <-- Extract main content, strip noise
    +-------------------+
            |
            v
    +-------------------+
    |  Text Extractor   |  <-- Clean text, remove ads/nav
    +-------------------+
            |
            v
    Article: {url, title, content, source, published_at}
```

#### 2.1 Content Extraction Strategy

| Source Type | Extraction Method | Notes |
|------------|------------------|-------|
| RSS Feed | feedparser + full article fetch | Get URL from feed, fetch full page |
| arXiv | arXiv API + abstract + PDF link | Use abstract as content |
| GitHub | GitHub API release notes | Already structured |
| Web Page | newspaper3k / trafilatura | Fallback for non-RSS sources |

#### 2.2 Rate Limiting & Retry

```python
# Configuration
FETCH_CONFIG = {
    "max_concurrent": 10,        # Concurrent fetches
    "timeout_per_request": 30,  # Seconds
    "retry_attempts": 3,
    "retry_backoff": [1, 2, 4], # Exponential backoff seconds
    "rate_limit_per_domain": {
        "arxiv.org": 1,          # 1 request per second
        "github.com": 2,
        "default": 3
    }
}
```

---

### Stage 2: LLM Processing Flow

```
Article Content (English)
            |
            v
    +-------------------+
    |  Content Chunking |  <-- Split long articles (max 8k tokens)
    +-------------------+
            |
            v
    +-------------------+
    |  LLM API Call     |  <-- GLM-4 / Claude API
    +-------------------+
            |
            v
    +-------------------+
    |  Structured Parse |  <-- JSON extraction
    +-------------------+
            |
            v
    Chinese Structured Output:
    {
        "核心观点": [str, str, str],
        "技术要点": str,
        "应用场景": str,
        "行业影响": str,
        "中文摘要": str (300-500 chars)
    }
```

#### 2.1 LLM Provider Configuration

```python
LLM_CONFIG = {
    "primary": {
        "provider": "zhipu",
        "model": "glm-4-flash",
        "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "max_tokens": 4096,
        "temperature": 0.3,
        "cost_per_1k_tokens": 0.001  # CNY
    },
    "fallback": {
        "provider": "anthropic",
        "model": "claude-3-haiku-20240307",
        "api_url": "https://api.anthropic.com/v1/messages",
        "max_tokens": 4096,
        "temperature": 0.3,
        "cost_per_1k_tokens": 0.00025  # USD
    }
}
```

#### 2.2 Prompt Template

```python
SUMMARY_PROMPT = """你是一位专业的AI技术编辑。请阅读以下英文文章，用中文整理关键信息。

文章标题: {title}
文章来源: {source}
文章内容:
{content}

请严格按照以下JSON格式输出（不要添加任何其他文字）:
{{
    "chinese_title": "中文标题",
    "核心观点": ["观点1", "观点2", "观点3"],
    "技术要点": "技术要点描述，如无则填'无'",
    "应用场景": "实际应用场景描述",
    "行业影响": "对AI行业的影响分析",
    "中文摘要": "300-500字的中文摘要"
}}
"""
```

#### 2.3 Content Chunking for Long Articles

```
Article (20k tokens)
        |
        v
    +------------------+
    | Token Estimator  |  <-- Count tokens (approx 4 chars/token for Chinese)
    +------------------+
        |
        v
    If > 8000 tokens?
        |
        +---- YES ----> Split into chunks
        |                    |
        v                    v
    Process whole        Process chunks in parallel
        |                    |
        v                    v
    Single output        Aggregate outputs
                            |
                            v
                        Merge summaries
```

---

### Stage 3: Vector Deduplication

```
Processed Articles (with Chinese summaries)
            |
            v
    +-------------------+
    |  Embedding Gen    |  <-- GLM embedding-3 API
    +-------------------+
            |
            v
    +-------------------+
    |  LanceDB Lookup   |  <-- Check if similar exists
    +-------------------+
            |
            v
    Similarity > 0.85?
        |           |
       YES          NO
        |           |
        v           v
     Skip        Store to LanceDB
                    |
                    v
                Add to result
```

#### 3.1 Dedup Strategy

```python
DEDUP_CONFIG = {
    "similarity_threshold": 0.85,    # Cosine similarity
    "embedding_field": "中文摘要",   # Use Chinese summary for dedup
    "cache_in_memory": True,         # L1 cache
    "cache_ttl_hours": 24             # Memory cache expiry
}
```

---

### Stage 4: Scoring & Ranking

```
Unique Articles
        |
        v
+-------------------+
|  Source Weight    |  <-- Tier 1: 10, Tier 2: 7, Tier 3: 5
+-------------------+
        |
        v
+-------------------+
|  Freshness Score  |  <-- <6h: +3, <24h: +2, <48h: +1
+-------------------+
        |
        v
+-------------------+
|  Multi-Source     |  <-- Same topic from multiple sources: +5
+-------------------+
        |
        v
+-------------------+
|  Category Bonus   |  <-- Product/Research news: +3
+-------------------+
        |
        v
    Total Score
        |
        v
    Sort & Select Top N
```

---

## 3. Data Storage Design

### 3.1 SQLite Schema (Enhanced)

```sql
-- Articles table (new)
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    original_title TEXT NOT NULL,
    chinese_title TEXT,
    source_id TEXT,                    -- Reference to curated-sources.json
    source_name TEXT,
    category TEXT DEFAULT 'unknown',
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_content TEXT,             -- Full English content
    processed_at TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',  -- pending/processing/completed/failed
    embedding_id TEXT,                -- LanceDB reference
    UNIQUE(url)
);

CREATE INDEX idx_articles_status ON articles(processing_status);
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_source ON articles(source_id);

-- Processed content table (new)
CREATE TABLE article_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id),
    核心观点 TEXT,                     -- JSON array of 3 strings
    技术要点 TEXT,
    应用场景 TEXT,
    行业影响 TEXT,
    中文摘要 TEXT,
    llm_provider TEXT,                -- 'glm-4' or 'claude-3-haiku'
    llm_model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article_id)
);

-- Briefs table (enhanced)
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,            -- HTML formatted
    article_count INTEGER DEFAULT 0,
    style TEXT DEFAULT 'lobster',     -- Brief style
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Brief-article junction table (new)
CREATE TABLE brief_articles (
    brief_id INTEGER REFERENCES briefs(id),
    article_id INTEGER REFERENCES articles(id),
    score INTEGER,
    rank INTEGER,                      -- Position in brief
    PRIMARY KEY (brief_id, article_id)
);

-- Processing logs (new)
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id),
    stage TEXT,                        -- 'fetch', 'chunk', 'llm', 'store'
    status TEXT,                       -- 'started', 'completed', 'failed'
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 LanceDB Schema (Enhanced)

```python
from lancedb.pydantic import LanceModel, Vector
from typing import Optional
import pydantic

class ArticleEmbedding(LanceModel):
    """Vector storage for article deduplication"""
    id: str                           # MD5(url + chinese_title)
    article_id: int                   # SQLite reference
    url: str
    chinese_title: str
    chinese_summary: str              # 中文摘要 (used for similarity)
    vector: Vector(2048)              # GLM embedding-3
    source_id: str
    category: str
    published_at: Optional[str]
```

---

## 4. API Endpoints Design

### 4.1 Article Processing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/articles/fetch` | Trigger article fetch from sources |
| GET | `/api/articles` | List articles with filters |
| GET | `/api/articles/{id}` | Get single article with summary |
| POST | `/api/articles/{id}/process` | Process single article through LLM |
| GET | `/api/articles/pending` | List articles pending processing |

### 4.2 Brief Generation Endpoints (Enhanced)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/brief/generate` | Generate brief (enhanced with style) |
| GET | `/api/brief/{date}/articles` | Get articles in a brief |
| GET | `/api/brief/{date}/page` | Get formatted HTML page |

### 4.3 Request/Response Models

```python
# POST /api/brief/generate
class GenerateBriefRequest(BaseModel):
    date: Optional[str] = None        # YYYY-MM-DD, defaults to today
    style: str = "lobster"            # lobster/news/tech/academic/flash
    max_articles: int = 20            # Max articles per brief
    categories: Optional[List[str]]   # Filter by category
    min_score: int = 5                # Minimum article score

class GenerateBriefResponse(BaseModel):
    status: str                       # "generating" | "exists" | "error"
    date: str
    brief_id: Optional[int]
    articles_queued: int
    estimated_time_seconds: int

# GET /api/articles/{id}
class ArticleDetailResponse(BaseModel):
    id: int
    url: str
    original_title: str
    chinese_title: Optional[str]
    source_name: str
    category: str
    published_at: Optional[str]
    original_content: Optional[str]
    核心观点: Optional[List[str]]
    技术要点: Optional[str]
    应用场景: Optional[str]
    行业影响: Optional[str]
    中文摘要: Optional[str]
    processing_status: str
```

---

## 5. Processing Pipeline Flow

### 5.1 Complete Pipeline Sequence

```
POST /api/brief/generate
        |
        v
+-------------------+
| 1. Validate       |  <-- Check date format, style validity
+-------------------+
        |
        v
+-------------------+
| 2. Check Exists   |  <-- If brief exists, return immediately
+-------------------+
        |
        v
+-------------------+
| 3. Fetch Sources  |  <-- Parallel fetch from all tiers
|    - RSS feeds    |
|    - arXiv API    |
|    - GitHub API   |
|    - Web pages    |
+-------------------+
        |
        v
+-------------------+
| 4. Extract URLs   |  <-- Get article URLs from feeds
+-------------------+
        |
        v
+-------------------+
| 5. Fetch Content  |  <-- Parallel with rate limiting
|    - HTML fetch   |
|    - Parse main   |
|    - Clean text   |
+-------------------+
        |
        v
+-------------------+
| 6. Store Articles |  <-- Insert to SQLite (pending status)
+-------------------+
        |
        v
+-------------------+
| 7. LLM Processing |  <-- Parallel with rate limiting
|    - Chunk if big |
|    - Call API     |
|    - Parse JSON    |
+-------------------+
        |
        v
+-------------------+
| 8. Generate Embed |  <-- For dedup, store to LanceDB
+-------------------+
        |
        v
+-------------------+
| 9. Deduplicate    |  <-- Remove similar articles
+-------------------+
        |
        v
+-------------------+
| 10. Score & Rank  |  <-- Apply scoring rules
+-------------------+
        |
        v
+-------------------+
| 11. Format Output |  <-- Apply style template
+-------------------+
        |
        v
+-------------------+
| 12. Store Brief   |  <-- Update SQLite, mark articles
+-------------------+
        |
        v
+-------------------+
| 13. Return Result |
+-------------------+
```

### 5.2 Background Processing Strategy

```python
# For large batches, use background tasks
async def generate_brief_pipeline(request: GenerateBriefRequest):
    # Quick validation
    if await brief_exists(request.date):
        return {"status": "exists", "brief_id": get_brief_id(request.date)}

    # Create processing job
    job_id = await create_job(date=request.date, style=request.style)

    # Queue background tasks
    background_tasks.add_task(process_pipeline, job_id, request)

    return {
        "status": "processing",
        "job_id": job_id,
        "status_url": f"/api/jobs/{job_id}"
    }

async def process_pipeline(job_id: str, request: GenerateBriefRequest):
    """Background task for full pipeline"""
    try:
        # Update job status
        await update_job(job_id, stage="fetching")

        # Stage 1: Fetch
        articles = await fetch_all_articles()

        # Stage 2: Process through LLM
        await update_job(job_id, stage="processing", total=len(articles))
        for i, article in enumerate(articles):
            await process_article(article)
            await update_job(job_id, processed=i+1)

        # Stage 3: Generate brief
        await update_job(job_id, stage="generating")
        brief = await generate_brief(articles, request.style)

        # Complete
        await update_job(job_id, stage="completed", brief_id=brief.id)

    except Exception as e:
        await update_job(job_id, stage="failed", error=str(e))
```

---

## 6. Error Handling & Resilience

### 6.1 Retry Strategy

```python
RETRY_CONFIG = {
    "llm_api": {
        "max_attempts": 3,
        "backoff": [1, 2, 4],
        "fallback_provider": True    # Switch to fallback LLM
    },
    "content_fetch": {
        "max_attempts": 2,
        "backoff": [1, 3],
        "fallback_method": "rss_summary"  # Use RSS summary if full fetch fails
    }
}
```

### 6.2 Fallback Chain

```
LLM Processing Failure:
1. Retry with same provider (3x with backoff)
2. Switch to fallback provider (GLM -> Claude or vice versa)
3. Use template-based extraction (regex patterns)
4. Mark article as 'partial' with available data

Content Fetch Failure:
1. Retry with different user-agent
2. Try archived version (web.archive.org)
3. Fall back to RSS summary
4. Skip article and log error
```

### 6.3 Monitoring & Alerts

```python
# Key metrics to track
METRICS = {
    "fetch_success_rate": "target > 95%",
    "llm_api_latency_p95": "target < 5s",
    "llm_api_error_rate": "target < 2%",
    "processing_success_rate": "target > 90%",
    "dedup_rate": "expected 10-30%",
    "brief_generation_time": "target < 5min"
}
```

---

## 7. Module Structure

```
app/
├── services/
│   ├── __init__.py
│   ├── fetcher.py              # RSS/HTTP fetch (existing, enhance)
│   ├── arxiv_fetcher.py        # arXiv fetcher (existing)
│   ├── github_fetcher.py       # GitHub fetcher (existing)
│   ├── content_extractor.py   # NEW: Full article extraction
│   ├── llm_processor.py       # NEW: LLM API integration
│   ├── article_processor.py   # NEW: Article processing pipeline
│   ├── embedding.py           # Vector embedding (existing)
│   └── brief_generator.py     # Brief generation (enhance)
├── routes/
│   ├── __init__.py
│   ├── brief.py               # Brief API (enhance)
│   ├── health.py              # Health check (existing)
│   └── articles.py            # NEW: Article API
├── models/
│   ├── __init__.py
│   ├── article.py             # NEW: Article models
│   └── brief.py               # NEW: Brief models
└── utils/
    ├── __init__.py
    ├── text_utils.py          # NEW: Text processing utilities
    └── rate_limiter.py        # NEW: Rate limiting
```

---

## 8. Configuration

### 8.1 Environment Variables

```bash
# Existing
GLM_API_KEY=xxx                    # GLM embedding API key
GLM_API_URL=https://open.bigmodel.cn/api/paas/v4/embeddings
API_PORT=8000

# New for LLM processing
LLM_API_KEY=xxx                     # LLM API key (GLM or Claude)
LLM_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
LLM_MODEL=glm-4-flash               # Primary LLM model
LLM_FALLBACK_KEY=xxx                # Fallback API key
LLM_FALLBACK_URL=https://api.anthropic.com/v1/messages
LLM_FALLBACK_MODEL=claude-3-haiku-20240307

# Processing limits
MAX_ARTICLES_PER_BRIEF=20
MAX_CONCURRENT_LLM_CALLS=5
MAX_TOKENS_PER_ARTICLE=8000
```

### 8.2 Processing Thresholds

```python
THRESHOLDS = {
    "max_content_length": 50000,       # Characters
    "max_chunk_tokens": 6000,         # For LLM input
    "min_content_length": 500,         # Skip too short articles
    "dedup_similarity": 0.85,
    "min_summary_length": 100,         # Characters for Chinese summary
    "max_summary_length": 500,
    "核心观点_count": 3
}
```

---

## 9. Deployment Considerations

### 9.1 Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| FastAPI App | 1 core | 512MB | - |
| SQLite | - | - | 100MB/1000 articles |
| LanceDB | - | 200MB | 500MB/1000 vectors |

### 9.2 Scaling Strategy

```
Current (Single Instance):
- SQLite for metadata
- LanceDB embedded
- In-memory rate limiting

Future (Horizontal Scale):
- PostgreSQL for metadata
- LanceDB on shared storage
- Redis for rate limiting & caching
- Task queue (Celery/RQ) for background jobs
```

### 9.3 Cost Estimation

```
LLM API Costs (per 100 articles):
- GLM-4-Flash: ~$0.10 (100k tokens)
- Claude Haiku: ~$0.25 (100k tokens)

Embedding API Costs (per 100 articles):
- GLM embedding-3: ~$0.01 (20k tokens)

Monthly estimate (20 articles/day):
- LLM: ~$0.60-1.50/month
- Embedding: ~$0.10/month
```

---

## 10. Implementation Phases

### Phase 1: Content Extraction (Week 1)
- [ ] Create `content_extractor.py`
- [ ] Implement full article fetch with retry
- [ ] Add HTML parsing (newspaper3k/trafilatura)
- [ ] Store full content in SQLite

### Phase 2: LLM Integration (Week 2)
- [ ] Create `llm_processor.py`
- [ ] Implement GLM-4 API integration
- [ ] Add Claude fallback
- [ ] Create prompt templates
- [ ] Implement content chunking

### Phase 3: Pipeline Integration (Week 3)
- [ ] Create `article_processor.py`
- [ ] Integrate fetch -> process -> store flow
- [ ] Add background task queue
- [ ] Implement processing status tracking

### Phase 4: API & Output (Week 4)
- [ ] Create `articles.py` routes
- [ ] Enhance brief generation
- [ ] Add style templates
- [ ] Update frontend integration

---

## Appendix A: Prompt Templates

### A.1 Article Summary Prompt

```python
ARTICLE_SUMMARY_PROMPT = """你是一位专业的AI技术编辑。请阅读以下英文文章，用中文整理关键信息。

文章标题: {title}
文章来源: {source}
发布时间: {published_at}

文章内容:
{content}

请严格按照以下JSON格式输出（不要添加任何其他文字，不要使用markdown代码块）:
{{
    "chinese_title": "简洁的中文标题（不超过30字）",
    "核心观点": ["观点1（不超过50字）", "观点2（不超过50字）", "观点3（不超过50字）"],
    "技术要点": "关键技术点描述（100字以内），如无技术内容则填'无'",
    "应用场景": "实际应用场景描述（100字以内）",
    "行业影响": "对AI行业的影响分析（100字以内）",
    "中文摘要": "300-500字的完整中文摘要"
}}

要求：
1. 核心观点必须是3条独立的观点
2. 中文摘要要准确传达原文核心内容
3. 技术要点和应用场景要具体，避免泛泛而谈
"""
```

### A.2 Paper Summary Prompt

```python
PAPER_SUMMARY_PROMPT = """你是一位AI学术研究员。请阅读以下arXiv论文摘要，用中文整理关键信息。

论文标题: {title}
作者: {authors}
arXiv ID: {arxiv_id}

摘要:
{abstract}

请严格按照以下JSON格式输出:
{{
    "chinese_title": "中文论文标题",
    "核心观点": ["核心贡献1", "核心贡献2", "核心贡献3"],
    "技术要点": "主要技术方法描述",
    "应用场景": "可能的应用领域",
    "行业影响": "对研究领域的意义",
    "中文摘要": "300-500字的中文概述"
}}
"""
```

---

## Appendix B: Style Templates

### B.1 lobster Style (Default)

```markdown
# AI Daily Brief - {date}

## TOP 3
{top_3_articles}

## 行业动态
{industry_news}

## 技术前沿
{tech_news}

---
Generated by AI Daily Brief
```

### B.2 flash Style

```text
{date} AI快讯：

1. {article_1_title}: {one_sentence_summary}
2. {article_2_title}: {one_sentence_summary}
3. {article_3_title}: {one_sentence_summary}
...
```