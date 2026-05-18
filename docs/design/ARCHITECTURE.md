# AI Daily Brief v4 系统架构设计文档

## 1. 系统架构图

```
                                    +---------------------------+
                                    |      用户浏览器            |
                                    +-------------+-------------+
                                                  |
                                                  | HTTPS
                                                  v
                                    +---------------------------+
                                    |       Nginx               |
                                    |  (反向代理 + SSL终止)      |
                                    |  ai.tomabc.com            |
                                    +-------------+-------------+
                                                  |
                                                  | HTTP :8080
                                                  v
+---------------------------+     +---------------------------+
|      静态资源              |     |      FastAPI 应用         |
|  /static/css, /static/js  |<----|  Python 3.11 + Uvicorn    |
+---------------------------+     +-------------+-------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    |                             |                             |
                    v                             v                             v
        +-------------------+         +-------------------+         +-------------------+
        |   SQLite          |         |   LanceDB         |         |   GLM Embedding   |
        |   (元数据存储)     |         |   (向量存储)       |         |   API (外部)      |
        |   metadata.db     |         |   /data/lancedb   |         |   embedding-3     |
        +-------------------+         +-------------------+         +-------------------+

                    +-----------------------------+-----------------------------+
                    |                             |                             |
                    v                             v                             v
        +-------------------+         +-------------------+         +-------------------+
        |   RSS Feeds       |         |   arXiv API       |         |   GitHub API      |
        |   (Anthropic,     |         |   (cs.AI, cs.CL,  |         |   (热门AI项目)    |
        |    OpenAI, etc)   |         |    cs.LG, cs.CV)  |         |                   |
        +-------------------+         +-------------------+         +-------------------+
```

## 2. 模块划分与职责

### 2.1 目录结构

```
ai-brief-site/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── metrics.py           # SLO监控指标
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── brief.py         # 简报API路由
│   │   └── health.py        # 健康检查路由
│   └── services/
│       ├── __init__.py
│       ├── embedding.py     # 向量化与语义去重
│       ├── brief_generator.py # 简报生成服务
│       ├── fetcher.py       # RSS/数据源抓取
│       ├── arxiv_fetcher.py # arXiv论文抓取
│       └── github_fetcher.py # GitHub Release抓取
├── config.py                # 全局配置
├── data/
│   ├── metadata.db          # SQLite数据库
│   └── lancedb/             # LanceDB向量存储
├── static/                  # 静态资源
├── templates/               # 模板文件
├── docs/                    # 文档
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### 2.2 核心模块职责

| 模块 | 职责 | 关键技术 |
|------|------|----------|
| `main.py` | 应用入口、生命周期管理、中间件 | FastAPI Lifespan |
| `routes/brief.py` | 简报CRUD API、HTML页面渲染 | FastAPI Router |
| `routes/health.py` | 健康检查、SLO指标暴露 | Prometheus格式 |
| `services/embedding.py` | 向量化、语义去重、缓存 | LanceDB, GLM API |
| `services/brief_generator.py` | 简报生成流程编排 | asyncio |
| `services/fetcher.py` | RSS Feed抓取 | feedparser, httpx |
| `services/arxiv_fetcher.py` | arXiv论文抓取 | arXiv API |
| `services/github_fetcher.py` | GitHub Release抓取 | GitHub API |

### 2.3 服务层架构

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (routes/)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   brief.py  │  │  health.py  │  │     main.py          │  │
│  │  /api/brief │  │  /health    │  │  middleware/metrics  │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │
          v
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (services/)                  │
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ BriefGenerator  │──│ Embedding   │  │ RSSFetcher      │  │
│  │                 │  │ Service     │  │ ArxivFetcher    │  │
│  └────────┬────────┘  └──────┬──────┘  │ GitHubFetcher   │  │
│           │                  │         └────────┬────────┘  │
└───────────┼──────────────────┼──────────────────┼───────────┘
            │                  │                  │
            v                  v                  v
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SQLite    │  │   LanceDB   │  │   External APIs     │  │
│  │ metadata.db │  │   vectors   │  │ GLM/arXiv/GitHub    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 3. 数据流设计

### 3.1 简报生成流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   触发生成   │───>│  并行抓取    │───>│  语义去重    │
│  POST /api/  │    │  RSS/arXiv/  │    │  LanceDB +    │
│  brief/generate│   │  GitHub      │    │  GLM API      │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               v
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   返回结果   │<───│  存储元数据  │<───│  生成HTML    │
│  brief_id   │    │  SQLite      │    │  格式化      │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 3.2 语义去重流程

```
输入: items (List[Dict])
     │
     v
┌─────────────────┐
│  遍历每个item   │
│  提取title字段  │
└────────┬────────┘
         │
         v
┌─────────────────┐     命中
│  内存缓存查询   │──────────> 返回vector
│  (hash -> vec)  │
└────────┬────────┘
         │ 未命中
         v
┌─────────────────┐     命中
│  LanceDB查询   │──────────> 缓存到内存, 返回vector
│  id=hash(text)  │
└────────┬────────┘
         │ 未命中
         v
┌─────────────────┐
│  GLM API调用   │
│  embedding-3   │
│  2048维向量    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  存储到LanceDB  │
│  缓存到内存     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  余弦相似度计算 │
│  与已见向量比较 │
│  threshold=0.85 │
└────────┬────────┘
         │
         v
    是否重复? ──是──> 跳过
         │
        否
         │
         v
    加入结果列表
```

### 3.3 API请求处理流程

```
HTTP Request
     │
     v
┌─────────────────────────────────────────┐
│            Nginx (ai.tomabc.com)        │
│  - SSL终止                              │
│  - 反向代理到 localhost:8080            │
│  - 静态资源服务                         │
└────────────────────┬────────────────────┘
                     │
                     v
┌─────────────────────────────────────────┐
│            FastAPI Application          │
│  - metrics_middleware (请求统计)       │
│  - 路由匹配                             │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┼───────────┐
         v           v           v
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ /api/   │ │ /health │ │ /metrics│
    │ brief/* │ │ /ready  │ │         │
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
         v           v           v
    SQLite/LanceDB  健康检查   指标输出
```

## 4. API设计规范

### 4.1 API端点

| 方法 | 路径 | 描述 | 响应格式 |
|------|------|------|----------|
| GET | `/` | 主页 | HTML |
| GET | `/api/brief/latest` | 获取最新简报 | JSON |
| GET | `/api/brief/list` | 简报列表 | JSON |
| GET | `/api/brief/{date}` | 按日期获取简报 | JSON |
| POST | `/api/brief/generate` | 触发简报生成 | JSON |
| GET | `/api/brief/page/{date}` | 简报HTML页面 | HTML |
| GET | `/health` | 健康检查 | JSON |
| GET | `/metrics` | Prometheus指标 | Text |
| GET | `/ready` | 就绪检查 | JSON |

### 4.2 响应模型

```python
# BriefResponse
{
    "id": int,
    "date": "YYYY-MM-DD",
    "title": str,
    "content": str,       # HTML格式
    "source_count": int,
    "created_at": "ISO8601"
}

# BriefList Response
[
    {
        "id": int,
        "date": "YYYY-MM-DD",
        "title": str,
        "source_count": int,
        "created_at": "ISO8601"
    }
]

# Generate Response
{
    "status": "generating" | "exists",
    "date": "YYYY-MM-DD",
    "id": int  # 如果已存在
}

# Health Response
{
    "status": "healthy" | "degraded",
    "components": {
        "sqlite": "healthy" | "unhealthy: {error}",
        "lancedb": "healthy" | "directory missing"
    }
}
```

### 4.3 错误处理

```python
# 标准错误响应
{
    "detail": "错误描述"
}

# HTTP状态码规范
200 OK          - 成功
201 Created     - 资源创建成功
400 Bad Request - 请求参数错误
404 Not Found   - 资源不存在
500 Internal    - 服务器内部错误
503 Service     - 服务不可用(健康检查失败)
```

### 4.4 请求头规范

```
# 必需
Content-Type: application/json

# 可选
Accept-Language: zh-CN  # 国际化预留
X-Request-ID: uuid      # 请求追踪
```

## 5. 数据库Schema设计

### 5.1 SQLite (元数据存储)

```sql
-- 简报表
CREATE TABLE briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,        -- YYYY-MM-DD
    title TEXT NOT NULL,              -- 简报标题
    content TEXT NOT NULL,            -- HTML内容
    source_count INTEGER DEFAULT 0,   -- 来源数量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_briefs_date ON briefs(date);

-- 来源表 (关联简报)
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,         -- 来源URL
    title TEXT NOT NULL,              -- 标题
    category TEXT DEFAULT 'unknown',  -- 分类
    embedding_id TEXT,                -- LanceDB中的向量ID
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    brief_id INTEGER REFERENCES briefs(id)
);

CREATE INDEX idx_sources_brief_id ON sources(brief_id);
CREATE INDEX idx_sources_category ON sources(category);
```

### 5.2 LanceDB (向量存储)

```python
# Pydantic模型定义
class EmbeddingRecord(LanceModel):
    """向量存储记录"""
    id: str              # MD5(text) 作为主键
    text: str            # 原始文本 (截断到1000字符)
    vector: Vector(2048) # GLM embedding-3 向量

# 表结构
Table: embeddings
├── id: string (主键)
├── text: string
└── vector: fixed_size_list<float>[2048]

# 索引 (自动创建)
- 向量索引: IVF-PQ (默认)
- 用于近似最近邻搜索
```

### 5.3 数据关系图

```
┌─────────────────┐       ┌─────────────────┐
│     briefs      │       │    sources      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │<──────│ brief_id (FK)   │
│ date (UNIQUE)   │       │ id (PK)         │
│ title           │       │ url (UNIQUE)    │
│ content         │       │ title           │
│ source_count    │       │ category        │
│ created_at      │       │ embedding_id    │
└─────────────────┘       │ fetched_at      │
                          └────────┬────────┘
                                   │
                                   │ embedding_id
                                   v
                          ┌─────────────────┐
                          │   LanceDB       │
                          │   embeddings    │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ text            │
                          │ vector[2048]    │
                          └─────────────────┘
```

## 6. 部署架构

### 6.1 Docker部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-brief-app:
    build: .
    container_name: ai-brief-app
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8000"  # 仅本地暴露
    volumes:
      - ./data:/app/data        # 持久化数据库
    environment:
      - API_PORT=8000
      - DEBUG=false
      - GLM_API_KEY=${GLM_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 6.2 Nginx配置

```nginx
# /etc/nginx/sites-available/ai-brief
server {
    listen 443 ssl http2;
    server_name ai.tomabc.com;

    # SSL配置
    ssl_certificate /etc/letsencrypt/live/ai.tomabc.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.tomabc.com/privkey.pem;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 反向代理
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location /static/ {
        proxy_pass http://127.0.0.1:8080/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name ai.tomabc.com;
    return 301 https://$server_name$request_uri;
}
```

### 6.3 部署流程

```
┌─────────────────┐
│  开发环境       │
│  git push       │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  VPS服务器      │
│  ai.tomabc.com  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────────┐
│                部署流程                      │
│  1. git pull                                │
│  2. export GLM_API_KEY=xxx                  │
│  3. docker-compose build                    │
│  4. docker-compose up -d                    │
│  5. curl -f http://localhost:8080/health    │
└─────────────────────────────────────────────┘
         │
         v
┌─────────────────┐
│  运行中服务    │
│  :443 Nginx    │
│  :8080 FastAPI │
└─────────────────┘
```

### 6.4 健康检查与监控

```
# SLO定义
SLO_ERROR_RATE_THRESHOLD = 0.01    # 1% 错误率
SLO_LATENCY_THRESHOLD_MS = 2000    # 2s 最大延迟

# 监控端点
GET /health  -> 组件健康状态
GET /metrics -> Prometheus格式指标
GET /ready   -> K8s就绪检查

# Prometheus指标示例
# HELP total_requests Total number of requests
# TYPE total_requests counter
total_requests 1234

# HELP error_requests Number of error requests (4xx/5xx)
# TYPE error_requests counter
error_requests 12

# HELP avg_latency_ms Average latency in milliseconds
# TYPE avg_latency_ms gauge
avg_latency_ms 156.78

# HELP slo_met Whether SLO is being met
# TYPE slo_met gauge
slo_met 1
```

## 7. 扩展性设计

### 7.1 水平扩展方案

```
当前架构 (单实例):
┌─────────────────────────────────────┐
│  单容器 + 嵌入式数据库               │
│  适合: 低流量, 简单部署              │
└─────────────────────────────────────┘

扩展架构 (多实例):
                    ┌─────────────┐
                    │   负载均衡   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           v               v               v
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  FastAPI #1 │ │  FastAPI #2 │ │  FastAPI #3 │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │ v
                    ┌──────┴──────┐
                    │  PostgreSQL │ (替换SQLite)
                    │  外部数据库  │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  LanceDB    │
                    │  共享存储   │
                    └─────────────┘
```

### 7.2 数据源扩展

```python
# 添加新数据源示例
# 1. 创建新的fetcher
class NewSourceFetcher:
    async def fetch_all(self) -> List[Dict]:
        # 实现抓取逻辑
        return items

# 2. 注册到BriefGenerator
class BriefGenerator:
    async def fetch_all_sources(self) -> List[Dict]:
        rss = RSSFetcher()
        arxiv = ArxivFetcher()
        github = GitHubReleaseFetcher()
        new_source = NewSourceFetcher()  # 新增

        results = await asyncio.gather(
            rss.fetch_all(),
            arxiv.fetch_all_as_dict(),
            github.fetch_all(),
            new_source.fetch_all(),  # 新增
        )
        return [item for items in results for item in items]
```

### 7.3 Embedding模型扩展

```python
# 支持多种Embedding模型
class EmbeddingService:
    PROVIDERS = {
        "glm": {
            "url": "https://open.bigmodel.cn/api/paas/v4/embeddings",
            "model": "embedding-3",
            "dimension": 2048,
        },
        "openai": {
            "url": "https://api.openai.com/v1/embeddings",
            "model": "text-embedding-3-small",
            "dimension": 1536,
        },
        # 可扩展其他模型...
    }

    def __init__(self, provider: str = "glm"):
        self.config = self.PROVIDERS[provider]
        # 根据provider初始化
```

### 7.4 缓存层扩展

```
当前: 内存缓存 + LanceDB
┌─────────────────────────────────────┐
│  EmbeddingService                   │
│  - _cache: Dict[str, List[float]]   │
│  - LanceDB持久化                    │
└─────────────────────────────────────┘

扩展: Redis缓存层
┌─────────────────────────────────────┐
│  EmbeddingService                   │
│  - Redis缓存 (跨进程共享)           │
│  - LanceDB持久化                    │
│  - 本地LRU缓存 (进程内)             │
└─────────────────────────────────────┘

查询顺序:
1. 本地LRU缓存 (ns级)
2. Redis缓存 (ms级)
3. LanceDB (ms级)
4. API调用 (100ms级)
```

### 7.5 功能扩展路线图

| 阶段 | 功能 | 技术方案 |
|------|------|----------|
| v4.1 | 定时任务 | APScheduler / Cron |
| v4.2 | 用户订阅 | SQLite用户表 + 邮件通知 |
| v4.3 | Webhook通知 | 异步任务队列 |
| v4.4 | 多语言支持 | i18n中间件 |
| v4.5 | AI摘要生成 | GLM-4 API集成 |
| v4.6 | 历史分析 | LanceDB向量搜索增强 |

### 7.6 性能优化方向

```
1. 并发优化
   - asyncio.gather() 并行抓取
   - 连接池复用 (httpx.AsyncClient)
   - 批量Embedding请求

2. 缓存优化
   - 多级缓存 (L1内存 + L2 Redis)
   - 缓存预热
   - 缓存失效策略

3. 数据库优化
   - SQLite WAL模式
   - LanceDB索引调优
   - 定期VACUUM

4. 网络优化
   - HTTP/2支持
   - 响应压缩 (gzip)
   - CDN静态资源
```

---

## 附录

### A. 环境变量

```bash
# 必需
GLM_API_KEY=your_glm_api_key

# 可选
API_PORT=8000
DEBUG=false
GLM_API_URL=https://open.bigmodel.cn/api/paas/v4/embeddings
```

### B. 依赖版本

```
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
feedparser>=6.0.0
lancedb>=0.3.0
pydantic>=2.0.0
```

### C. 常用命令

```bash
# 开发
python -m uvicorn app.main:app --reload

# Docker构建
docker-compose build

# Docker启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 健康检查
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```