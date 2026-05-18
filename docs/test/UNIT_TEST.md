# AI Daily Brief v4 - 单元测试用例

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | AI Daily Brief v4 |
| 文档版本 | v1.0 |
| 创建日期 | 2026-05-19 |
| 测试框架 | pytest + httpx |

---

## 1. 数据抓取模块单元测试

### 1.1 RSS Fetcher 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-RSS-001 | 正常抓取RSS Feed | Mock HTTP响应返回有效RSS XML | 1. 调用 `RSSFetcher.fetch_feed("anthropic", url)`<br>2. 验证返回数据结构 | 返回List[Dict]，包含title/link/summary/published字段 | P0 |
| UT-RSS-002 | RSS Feed超时处理 | Mock httpx超时异常 | 1. 设置httpx.AsyncClient超时<br>2. 调用fetch_feed | 返回空列表[]，不抛出异常 | P1 |
| UT-RSS-003 | RSS Feed HTTP错误 | Mock返回500状态码 | 1. Mock响应状态码500<br>2. 调用fetch_feed | 返回空列表[]，打印错误日志 | P1 |
| UT-RSS-004 | RSS解析异常 | Mock返回无效XML | 1. Mock返回"<invalid>"<br>2. 调用fetch_feed | 返回空列表或部分解析结果 | P2 |
| UT-RSS-005 | 空Feed处理 | Mock返回空entries | 1. Mock返回空entries<br>2. 调用fetch_feed | 返回空列表[] | P2 |
| UT-RSS-006 | 并发抓取所有RSS源 | Mock所有HTTP请求成功 | 1. 调用 `RSSFetcher.fetch_all()`<br>2. 验证并发执行 | 返回合并后的列表，包含所有源数据 | P0 |
| UT-RSS-007 | 条目数量限制 | Mock返回100条entries | 1. 调用fetch_feed<br>2. 验证返回数量 | 每个源最多返回10条 | P2 |

### 1.2 arXiv Fetcher 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-ARX-001 | 正常抓取论文列表 | Mock arXiv API返回有效Atom feed | 1. 调用 `ArxivFetcher.fetch_papers("cs.AI")`<br>2. 验证Paper对象结构 | 返回List[Paper]，包含title/link/summary/authors字段 | P0 |
| UT-ARX-002 | 论文分类参数验证 | 无 | 1. 调用fetch_papers传入空分类<br>2. 调用fetch_papers传入无效分类 | 根据API行为返回空或错误处理 | P1 |
| UT-ARX-003 | arXiv API超时 | Mock TimeoutException | 1. Mock超时场景<br>2. 调用fetch_papers | 返回空列表[]，打印超时日志 | P1 |
| UT-ARX-004 | 论文摘要截断 | Mock返回超长summary | 1. Mock summary长度>500<br>2. 调用fetch_papers | summary被截断至500字符 | P2 |
| UT-ARX-005 | 多分类并发抓取 | Mock所有分类API成功 | 1. 调用 `ArxivFetcher.fetch_all()`<br>2. 验证4个分类都被调用 | 返回所有分类论文合并列表 | P0 |
| UT-ARX-006 | Paper.to_dict转换 | 创建Paper对象 | 1. 调用paper.to_dict() | 返回正确结构的字典 | P2 |
| UT-ARX-007 | max_results参数验证 | Mock API响应 | 1. 验证URL参数包含max_results<br>2. 测试边界值(0, 1, 100) | 参数正确传递到API | P2 |

### 1.3 GitHub Fetcher 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-GIT-001 | 正常抓取Release | Mock GitHub API返回release数据 | 1. 调用 `GitHubReleaseFetcher.fetch_release("anthropics/anthropic-sdk-python")` | 返回Dict，包含title/link/summary/published | P0 |
| UT-GIT-002 | 404无Release处理 | Mock返回404状态码 | 1. Mock 404响应<br>2. 调用fetch_release | 返回None，不抛出异常 | P1 |
| UT-GIT-003 | GitHub API限流 | Mock返回403 | 1. Mock 403响应<br>2. 调用fetch_release | 返回None，打印限流日志 | P1 |
| UT-GIT-004 | Release body为空 | Mock返回body=null | 1. Mock release body为null<br>2. 调用fetch_release | summary为空字符串，不报错 | P2 |
| UT-GIT-005 | 并发抓取所有项目 | Mock所有API成功 | 1. 调用 `fetch_all()`<br>2. 验证并发调用 | 返回非None的release列表 | P0 |
| UT-GIT-006 | 部分失败不影响整体 | Mock 3个成功，3个失败 | 1. 调用fetch_all<br>2. 验证返回结果 | 返回成功的3个release，忽略失败的 | P1 |

---

## 2. 语义去重模块单元测试

### 2.1 Embedding Service 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-EMB-001 | 正常获取向量 | Mock GLM API返回有效embedding | 1. 调用 `get_embedding("test text")`<br>2. 验证返回向量维度 | 返回2048维向量List[float] | P0 |
| UT-EMB-002 | 空文本处理 | 无 | 1. 调用get_embedding("")<br>2. 调用get_embedding("   ") | 返回None | P1 |
| UT-EMB-003 | API密钥未配置 | GLM_API_KEY="" | 1. 清除API密钥<br>2. 调用get_embedding | 返回None，打印警告日志 | P1 |
| UT-EMB-004 | 缓存命中-内存缓存 | 首次调用后 | 1. 首次调用get_embedding<br>2. 再次调用相同文本<br>3. 验证API调用次数 | 第2次调用从内存缓存返回，不调用API | P0 |
| UT-EMB-005 | 缓存命中-LanceDB | 重启服务后(内存缓存清空) | 1. 首次调用存入LanceDB<br>2. 重置内存缓存<br>3. 再次调用 | 从LanceDB读取缓存，不调用API | P0 |
| UT-EMB-006 | API调用失败 | Mock返回非200状态码 | 1. Mock 500错误<br>2. 调用get_embedding | 返回None，打印错误日志 | P1 |
| UT-EMB-007 | 文本hash生成 | 无 | 1. 调用 `_text_hash("test")`<br>2. 验证相同文本hash一致 | 返回32位MD5字符串 | P2 |
| UT-EMB-008 | LanceDB存储成功 | Mock LanceDB可用 | 1. 获取embedding<br>2. 验证数据存入LanceDB | 记录包含id/text/vector字段 | P1 |
| UT-EMB-009 | LanceDB存储失败 | Mock LanceDB异常 | 1. Mock LanceDB write失败<br>2. 调用get_embedding | 返回向量但不存储，打印错误日志 | P2 |

### 2.2 去重功能测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-DEDUP-001 | 正常去重-相似度高 | Mock向量相似度0.95 | 1. 传入两条相似标题<br>2. 调用 `deduplicate(items, 0.85)` | 只保留第一条，返回1条 | P0 |
| UT-DEDUP-002 | 正常去重-相似度低 | Mock向量相似度0.5 | 1. 传入两条不相似标题<br>2. 调用deduplicate | 两条都保留 | P0 |
| UT-DEDUP-003 | 阈值边界测试 | Mock相似度正好0.85 | 1. 设置相似度=0.85<br>2. 调用deduplicate | 视为重复，保留第一条 | P1 |
| UT-DEDUP-004 | 空列表处理 | 无 | 1. 调用deduplicate([]) | 返回空列表[] | P2 |
| UT-DEDUP-005 | 单条目处理 | 无 | 1. 传入单条item<br>2. 调用deduplicate | 返回单条item | P2 |
| UT-DEDUP-006 | 缺失text_field处理 | item无title字段 | 1. 传入无title的item<br>2. 调用deduplicate | 保留该条目 | P2 |
| UT-DEDUP-007 | 自定义text_field | 无 | 1. 传入含summary字段item<br>2. 调用deduplicate(items, text_field="summary") | 使用summary进行比较 | P1 |
| UT-DEDUP-008 | 多条目去重 | 10条item，其中5对相似 | Mock向量相似度 | 1. 调用deduplicate<br>2. 验证返回数量 | 返回5条不重复内容 | P0 |
| UT-DEDUP-009 | 余弦相似度计算 | 已知向量 | 1. 调用 `_cosine_similarity(v1, v2)` | 返回正确相似度值(精度6位) | P2 |
| UT-DEDUP-010 | 零向量处理 | v1或v2为零向量 | 1. 调用cosine_similarity | 返回0.0，不抛出除零异常 | P1 |

---

## 3. 简报生成模块单元测试

### 3.1 Brief Generator 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-GEN-001 | 正常生成简报 | Mock所有fetcher返回数据 | 1. 调用 `BriefGenerator.generate("2026-05-19")` | 返回success状态，包含brief_id | P0 |
| UT-GEN-002 | 无数据抓取 | Mock所有fetcher返回空 | 1. 调用generate | 返回error状态，message="无数据抓取" | P1 |
| UT-GEN-003 | 日期参数默认值 | 不传date参数 | 1. 调用generate() | 使用当天日期(YYYY-MM-DD) | P2 |
| UT-GEN-004 | 内容格式化 | 传入多种source类型 | 1. 调用 `_format_content(items)` | HTML包含正确分类标题(h3)和列表(ul) | P1 |
| UT-GEN-005 | 每类最多5条 | 某分类有10条item | 1. 调用_format_content<br>2. 验证HTML输出 | 每分类最多显示5条链接 | P2 |
| UT-GEN-006 | SQLite存储成功 | Mock数据库连接 | 1. 调用 `_save_brief()`<br>2. 验证SQL执行 | 返回brief_id，数据正确存储 | P0 |
| UT-GEN-007 | 日期重复处理 | 已存在相同日期简报 | 1. 调用generate相同日期<br>2. 验证数据库操作 | 执行INSERT OR REPLACE，更新原有记录 | P1 |
| UT-GEN-008 | 分类统计准确性 | 传入已知来源分布 | 1. 调用generate<br>2. 验证sources统计 | 统计数量与实际一致 | P1 |

---

## 4. API路由模块单元测试

### 4.1 Brief API 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-API-001 | GET /api/brief/latest-成功 | 数据库存在简报 | 1. GET /api/brief/latest<br>2. 验证响应结构 | 200，返回BriefResponse结构 | P0 |
| UT-API-002 | GET /api/brief/latest-无数据 | 数据库为空 | 1. GET /api/brief/latest | 404，detail="No brief found" | P1 |
| UT-API-003 | GET /api/brief/list-默认limit | 存在多条简报 | 1. GET /api/brief/list | 200，返回最多30条 | P0 |
| UT-API-004 | GET /api/brief/list-自定义limit | 存在50条简报 | 1. GET /api/brief/list?limit=10 | 200，返回10条 | P1 |
| UT-API-005 | GET /api/brief/{date}-成功 | 指定日期存在简报 | 1. GET /api/brief/2026-05-19 | 200，返回该日期简报 | P0 |
| UT-API-006 | GET /api/brief/{date}-不存在 | 指定日期无简报 | 1. GET /api/brief/2026-01-01 | 404，detail="No brief for 2026-01-01" | P1 |
| UT-API-007 | POST /api/brief/generate-新建 | 指定日期无简报 | 1. POST /api/brief/generate<br>2. 验证后台任务触发 | 200，status="generating" | P0 |
| UT-API-008 | POST /api/brief/generate-已存在 | 指定日期已存在简报 | 1. POST /api/brief/generate | 200，status="exists"，返回id | P1 |
| UT-API-009 | GET /api/brief/page/{date}-成功 | 指定日期存在简报 | 1. GET /api/brief/page/2026-05-19 | 200，返回完整HTML页面 | P1 |
| UT-API-010 | GET /api/brief/page/{date}-不存在 | 指定日期无简报 | 1. GET /api/brief/page/2026-01-01 | 返回默认index.html内容 | P2 |

### 4.2 Health API 测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-HLT-001 | GET /health-全部健康 | SQLite和LanceDB可用 | 1. GET /health | 200，status="healthy" | P0 |
| UT-HLT-002 | GET /health-SQLite异常 | SQLite连接失败 | 1. Mock SQLite异常<br>2. GET /health | 503，status="degraded"，sqlite="unhealthy" | P1 |
| UT-HLT-003 | GET /health-LanceDB缺失 | LanceDB目录不存在 | 1. 删除LanceDB目录<br>2. GET /health | 503，lancedb="directory missing" | P1 |
| UT-HLT-004 | GET /metrics-初始状态 | 服务刚启动 | 1. GET /metrics | total_requests=0，error_rate=0 | P0 |
| UT-HLT-005 | GET /metrics-有请求后 | 已处理若干请求 | 1. 发送多个请求<br>2. GET /metrics | 正确统计total/error/avg_latency | P0 |
| UT-HLT-006 | GET /metrics-SLO状态-满足 | 错误率<1%，延迟<2s | 1. GET /metrics | slo_met=1 | P1 |
| UT-HLT-007 | GET /metrics-SLO状态-不满足 | 错误率>=1% | 1. GET /metrics | slo_met=0 | P1 |
| UT-HLT-008 | GET /ready-数据库可用 | SQLite可查询 | 1. GET /ready | 200，status="ready" | P0 |
| UT-HLT-009 | GET /ready-数据库不可用 | SQLite查询失败 | 1. Mock数据库异常<br>2. GET /ready | 503，status="not ready" | P1 |

---

## 5. 前端模块单元测试

### 5.1 JavaScript测试用例

| 用例ID | 测试项 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|--------|----------|----------|----------|--------|
| UT-FE-001 | fetchLatestBrief-成功 | Mock API返回有效数据 | 1. 调用fetchLatestBrief()<br>2. 验证DOM更新 | #brief-content显示标题和内容 | P0 |
| UT-FE-002 | fetchLatestBrief-失败 | Mock API返回404 | 1. Mock 404响应<br>2. 调用fetchLatestBrief | 显示错误提示"暂无简报" | P1 |
| UT-FE-003 | fetchBriefList-成功 | Mock API返回列表 | 1. 调用fetchBriefList()<br>2. 验证DOM更新 | #list-content显示历史列表 | P0 |
| UT-FE-004 | fetchBriefList-空列表 | Mock API返回[] | 1. Mock空数组响应<br>2. 调用fetchBriefList | 显示"暂无历史简报" | P2 |
| UT-FE-005 | fetchBriefList-网络错误 | Mock网络异常 | 1. Mock fetch失败<br>2. 调用fetchBriefList | 显示错误提示 | P1 |
| UT-FE-006 | 页面初始化 | DOM加载完成 | 1. 触发DOMContentLoaded事件 | fetchLatestBrief和fetchBriefList被调用 | P0 |

---

## 6. 测试数据准备

### 6.1 Mock数据示例

```python
# RSS Feed Mock
MOCK_RSS_RESPONSE = """
<rss>
  <channel>
    <item>
      <title>Test Article</title>
      <link>https://example.com/test</link>
      <summary>Test summary content</summary>
      <pubDate>Mon, 19 May 2026 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

# arXiv Mock
MOCK_ARXIV_RESPONSE = """
<feed>
  <entry>
    <title>Test Paper Title</title>
    <link href="http://arxiv.org/abs/2401.00001"/>
    <summary>Test abstract content</summary>
    <published>2026-05-19T00:00:00Z</published>
    <author><name>Test Author</name></author>
  </entry>
</feed>
"""

# GitHub Release Mock
MOCK_GITHUB_RELEASE = {
    "name": "v1.0.0",
    "tag_name": "v1.0.0",
    "html_url": "https://github.com/test/test/releases/tag/v1.0.0",
    "body": "Release notes here",
    "published_at": "2026-05-19T00:00:00Z"
}

# Embedding Mock
MOCK_EMBEDDING = [0.1] * 2048  # 2048维向量
```

---

## 7. 自动化测试脚本示例

### 7.1 pytest配置 (pytest.ini)

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### 7.2 单元测试示例代码

```python
# tests/test_fetcher.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.fetcher import RSSFetcher, ArxivFetcher, GitHubFetcher

class TestRSSFetcher:
    @pytest.mark.asyncio
    async def test_fetch_feed_success(self, mock_httpx_success):
        """UT-RSS-001: 正常抓取RSS Feed"""
        fetcher = RSSFetcher()
        result = await fetcher.fetch_feed("test", "https://example.com/feed")

        assert isinstance(result, list)
        assert len(result) > 0
        assert "title" in result[0]
        assert "link" in result[0]

    @pytest.mark.asyncio
    async def test_fetch_feed_timeout(self, mock_httpx_timeout):
        """UT-RSS-002: RSS Feed超时处理"""
        fetcher = RSSFetcher()
        result = await fetcher.fetch_feed("test", "https://example.com/feed")

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_all_concurrent(self, mock_all_feeds):
        """UT-RSS-006: 并发抓取所有RSS源"""
        fetcher = RSSFetcher()
        result = await fetcher.fetch_all()

        # 验证合并了所有源
        sources = set(item["source"] for item in result)
        assert len(sources) > 1


class TestArxivFetcher:
    @pytest.mark.asyncio
    async def test_fetch_papers_success(self, mock_arxiv_success):
        """UT-ARX-001: 正常抓取论文列表"""
        fetcher = ArxivFetcher()
        result = await fetcher.fetch_papers("cs.AI")

        assert isinstance(result, list)
        assert all(hasattr(paper, "title") for paper in result)

    @pytest.mark.asyncio
    async def test_fetch_all_categories(self, mock_arxiv_all):
        """UT-ARX-005: 多分类并发抓取"""
        fetcher = ArxivFetcher()
        result = await fetcher.fetch_all()

        # 验证包含多个分类
        categories = set(paper.category for paper in result)
        assert len(categories) == 4  # cs.AI, cs.CL, cs.LG, cs.CV


class TestGitHubFetcher:
    @pytest.mark.asyncio
    async def test_fetch_release_success(self, mock_github_release):
        """UT-GIT-001: 正常抓取Release"""
        fetcher = GitHubFetcher()
        result = await fetcher.fetch_release("test/repo")

        assert result is not None
        assert "title" in result
        assert "link" in result

    @pytest.mark.asyncio
    async def test_fetch_release_404(self, mock_github_404):
        """UT-GIT-002: 404无Release处理"""
        fetcher = GitHubFetcher()
        result = await fetcher.fetch_release("nonexistent/repo")

        assert result is None
```

```python
# tests/test_embedding.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.embedding import EmbeddingService, deduplicate

class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_get_embedding_success(self, mock_glm_api):
        """UT-EMB-001: 正常获取向量"""
        service = EmbeddingService()
        result = await service.get_embedding("test text")

        assert result is not None
        assert len(result) == 2048

    @pytest.mark.asyncio
    async def test_get_embedding_empty_text(self):
        """UT-EMB-002: 空文本处理"""
        service = EmbeddingService()
        result = await service.get_embedding("")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit_memory(self, mock_glm_api):
        """UT-EMB-004: 缓存命中-内存缓存"""
        service = EmbeddingService()

        # 首次调用
        await service.get_embedding("test")
        call_count = mock_glm_api.call_count

        # 再次调用相同文本
        await service.get_embedding("test")

        # API不应被再次调用
        assert mock_glm_api.call_count == call_count

    def test_cosine_similarity(self):
        """UT-DEDUP-009: 余弦相似度计算"""
        service = EmbeddingService()

        # 已知向量
        v1 = [1, 0, 0]
        v2 = [1, 0, 0]
        v3 = [0, 1, 0]

        # 相同向量
        assert service._cosine_similarity(v1, v2) == 1.0

        # 正交向量
        assert service._cosine_similarity(v1, v3) == 0.0

    def test_cosine_similarity_zero_vector(self):
        """UT-DEDUP-010: 零向量处理"""
        service = EmbeddingService()

        result = service._cosine_similarity([0, 0, 0], [1, 1, 1])
        assert result == 0.0


class TestDeduplicate:
    @pytest.mark.asyncio
    async def test_deduplicate_similar(self, mock_high_similarity):
        """UT-DEDUP-001: 正常去重-相似度高"""
        items = [
            {"title": "AI Breakthrough", "source": "test"},
            {"title": "AI Breakthrough"},  # 相似
        ]
        result = await deduplicate(items, threshold=0.85)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_different(self, mock_low_similarity):
        """UT-DEDUP-002: 正常去重-相似度低"""
        items = [
            {"title": "AI News", "source": "test"},
            {"title": "Cooking Recipe"},  # 不相似
        ]
        result = await deduplicate(items, threshold=0.85)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_deduplicate_empty(self):
        """UT-DEDUP-004: 空列表处理"""
        result = await deduplicate([])
        assert result == []
```

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestBriefAPI:
    def test_get_latest_brief_success(self, mock_db_with_brief):
        """UT-API-001: GET /api/brief/latest-成功"""
        response = client.get("/api/brief/latest")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "date" in data
        assert "title" in data

    def test_get_latest_brief_not_found(self, mock_db_empty):
        """UT-API-002: GET /api/brief/latest-无数据"""
        response = client.get("/api/brief/latest")

        assert response.status_code == 404

    def test_list_briefs_default(self, mock_db_with_briefs):
        """UT-API-003: GET /api/brief/list-默认limit"""
        response = client.get("/api/brief/list")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_briefs_custom_limit(self, mock_db_with_briefs):
        """UT-API-004: GET /api/brief/list-自定义limit"""
        response = client.get("/api/brief/list?limit=5")

        assert response.status_code == 200
        assert len(response.json()) <= 5

    def test_generate_brief_new(self, mock_db_empty):
        """UT-API-007: POST /api/brief/generate-新建"""
        response = client.post("/api/brief/generate")

        assert response.status_code == 200
        assert response.json()["status"] in ["generating", "exists"]


class TestHealthAPI:
    def test_health_all_healthy(self, mock_healthy_db):
        """UT-HLT-001: GET /health-全部健康"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_initial(self):
        """UT-HLT-004: GET /metrics-初始状态"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "total_requests" in response.text

    def test_ready_success(self, mock_healthy_db):
        """UT-HLT-008: GET /ready-数据库可用"""
        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"
```

---

## 8. 测试覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|------------|------|
| 数据抓取模块 | >= 90% | 核心业务逻辑 |
| 语义去重模块 | >= 85% | 包含API调用Mock |
| 简报生成模块 | >= 85% | 整合流程测试 |
| API路由模块 | >= 95% | 接口契约测试 |
| 前端模块 | >= 70% | 使用Jest或类似框架 |

---

## 9. 执行命令

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行指定模块测试
pytest tests/test_fetcher.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 并行执行
pytest tests/ -n auto
```