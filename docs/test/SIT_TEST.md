# AI Daily Brief v4 - 系统集成测试 (SIT)

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | AI Daily Brief v4 |
| 文档版本 | v1.0 |
| 创建日期 | 2026-05-19 |
| 测试类型 | 系统集成测试 (SIT) |
| 测试环境 | Staging环境 |

---

## 1. 集成测试概述

### 1.1 测试范围

| 集成点 | 描述 | 优先级 |
|--------|------|--------|
| 数据抓取集成 | RSS/arXiv/GitHub数据源与系统整合 | P0 |
| 语义去重集成 | GLM API + LanceDB去重流程 | P0 |
| 简报生成集成 | 数据获取 -> 去重 -> 存储 完整流程 | P0 |
| API与数据库集成 | FastAPI与SQLite/LanceDB交互 | P0 |
| 前后端集成 | 前端页面与API接口联调 | P1 |

### 1.2 测试环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| 数据库 | SQLite + LanceDB |
| 外部API | GLM Embedding API (或Mock) |
| 网络 | 可访问arXiv/GitHub/RSS源 |

---

## 2. 数据抓取集成测试

### 2.1 RSS数据源集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-RSS-001 | Anthropic RSS集成 | 1. 调用 `RSSFetcher.fetch_feed("anthropic", "https://www.anthropic.com/news/rss")`<br>2. 验证返回数据结构 | 返回非空列表，每条包含title/link/summary字段 | 网络连通 | P0 |
| SIT-RSS-002 | OpenAI RSS集成 | 1. 调用fetch_feed获取OpenAI博客<br>2. 验证数据格式 | 返回有效数据，category="news" | 网络连通 | P0 |
| SIT-RSS-003 | DeepMind RSS集成 | 1. 调用fetch_feed获取DeepMind博客<br>2. 验证数据格式 | 返回有效数据 | 网络连通 | P0 |
| SIT-RSS-004 | HuggingFace RSS集成 | 1. 调用fetch_feed获取HF博客<br>2. 验证数据格式 | 返回有效数据 | 网络连通 | P1 |
| SIT-RSS-005 | 全部RSS源并发抓取 | 1. 调用 `RSSFetcher.fetch_all()`<br>2. 统计各源返回数量 | 所有配置源都有返回，总条数>0 | 网络连通 | P0 |
| SIT-RSS-006 | RSS源不可达处理 | 1. Mock一个无效URL<br>2. 调用fetch_all | 有效源正常返回，无效源返回空列表不影响整体 | - | P1 |
| SIT-RSS-007 | RSS格式兼容性测试 | 1. 测试不同RSS版本(2.0, 1.0, Atom)<br>2. 验证解析正确性 | 都能正确解析并提取关键字段 | - | P2 |

### 2.2 arXiv数据源集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-ARX-001 | cs.AI分类集成 | 1. 调用 `ArxivFetcher.fetch_papers("cs.AI", 10)`<br>2. 验证返回论文结构 | 返回最多10篇论文，包含authors列表 | arXiv API可用 | P0 |
| SIT-ARX-002 | cs.CL分类集成 | 1. 调用fetch_papers("cs.CL")<br>2. 验证数据 | 返回NLP相关论文 | arXiv API可用 | P0 |
| SIT-ARX-003 | cs.LG分类集成 | 1. 调用fetch_papers("cs.LG")<br>2. 验证数据 | 返回机器学习相关论文 | arXiv API可用 | P0 |
| SIT-ARX-004 | cs.CV分类集成 | 1. 调用fetch_papers("cs.CV")<br>2. 验证数据 | 返回计算机视觉相关论文 | arXiv API可用 | P0 |
| SIT-ARX-005 | 全部分类并发抓取 | 1. 调用 `ArxivFetcher.fetch_all()`<br>2. 统计各分类数量 | 4个分类都有返回，总数>0 | arXiv API可用 | P0 |
| SIT-ARX-006 | arXiv API限流处理 | 1. 短时间发送多次请求<br>2. 验证错误处理 | 超时后返回空列表，不抛出异常 | - | P1 |
| SIT-ARX-007 | Paper对象转换 | 1. 获取Paper对象<br>2. 调用to_dict()<br>3. 验证字典结构 | 包含所有字段，格式正确 | - | P2 |

### 2.3 GitHub数据源集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-GIT-001 | anthropic-sdk-python集成 | 1. 调用 `GitHubReleaseFetcher.fetch_release("anthropics/anthropic-sdk-python")`<br>2. 验证返回结构 | 返回最新Release信息 | GitHub API可用 | P0 |
| SIT-GIT-002 | openai-python集成 | 1. 调用fetch_release获取OpenAI SDK<br>2. 验证数据 | 返回有效Release | GitHub API可用 | P0 |
| SIT-GIT-003 | transformers集成 | 1. 调用fetch_release获取HF transformers<br>2. 验证数据 | 返回有效Release | GitHub API可用 | P1 |
| SIT-GIT-004 | pytorch集成 | 1. 调用fetch_release获取PyTorch<br>2. 验证数据 | 返回有效Release | GitHub API可用 | P1 |
| SIT-GIT-005 | langchain集成 | 1. 调用fetch_release获取LangChain<br>2. 验证数据 | 返回有效Release | GitHub API可用 | P1 |
| SIT-GIT-006 | ollama集成 | 1. 调用fetch_release获取Ollama<br>2. 验证数据 | 返回有效Release | GitHub API可用 | P1 |
| SIT-GIT-007 | 全部项目并发抓取 | 1. 调用 `fetch_all()`<br>2. 统计返回数量 | 至少返回部分项目Release | GitHub API可用 | P0 |
| SIT-GIT-008 | GitHub API限流处理 | 1. 触发Rate Limit<br>2. 验证处理 | 返回None，不影响其他项目 | - | P2 |

---

## 3. 语义去重集成测试

### 3.1 GLM API集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-GLM-001 | GLM API连通性 | 1. 配置有效GLM_API_KEY<br>2. 调用 `get_embedding("测试文本")` | 返回2048维向量 | GLM API密钥 | P0 |
| SIT-GLM-002 | 中文文本Embedding | 1. 传入中文文本<br>2. 验证向量 | 返回有效向量，维度正确 | GLM API密钥 | P0 |
| SIT-GLM-003 | 英文文本Embedding | 1. 传入英文文本<br>2. 验证向量 | 返回有效向量 | GLM API密钥 | P0 |
| SIT-GLM-004 | 长文本处理 | 1. 传入>1000字文本<br>2. 验证处理 | 正常返回向量或截断处理 | GLM API密钥 | P1 |
| SIT-GLM-005 | API密钥无效 | 1. 配置无效API密钥<br>2. 调用get_embedding | 返回None，打印错误日志 | - | P1 |
| SIT-GLM-006 | API密钥缺失 | 1. 不配置API密钥<br>2. 调用get_embedding | 返回None，打印警告 | - | P1 |
| SIT-GLM-007 | API超时处理 | 1. 设置短超时<br>2. 调用API | 返回None，不崩溃 | - | P2 |

### 3.2 LanceDB集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-LDB-001 | LanceDB初始化 | 1. 首次启动服务<br>2. 验证data/lancedb目录 | 目录创建成功，包含表结构 | - | P0 |
| SIT-LDB-002 | 向量存储 | 1. 获取embedding<br>2. 查询LanceDB验证存储 | 记录包含id/text/vector字段 | GLM API | P0 |
| SIT-LDB-003 | 向量检索 | 1. 存入向量后<br>2. 使用id查询 | 返回正确的向量记录 | - | P0 |
| SIT-LDB-004 | 重复ID处理 | 1. 存入相同文本两次<br>2. 验证存储结果 | 只存储一条记录(相同ID覆盖) | - | P1 |
| SIT-LDB-005 | 批量存储 | 1. 连续存储多条向量<br>2. 验证存储数量 | 全部正确存储 | GLM API | P1 |
| SIT-LDB-006 | 服务重启后数据持久化 | 1. 存入向量<br>2. 重启服务<br>3. 查询验证 | 数据仍然存在 | - | P0 |

### 3.3 去重流程集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-DUP-001 | 完整去重流程 | 1. 准备10条相似新闻标题<br>2. 调用 `deduplicate(items, 0.85)`<br>3. 验证结果 | 返回去重后列表，相似标题只保留一条 | GLM API + LanceDB | P0 |
| SIT-DUP-002 | 缓存命中流程 | 1. 首次调用deduplicate<br>2. 再次调用相同数据<br>3. 监控API调用次数 | 第二次调用使用缓存，API调用次数不增加 | GLM API + LanceDB | P0 |
| SIT-DUP-003 | 多源数据去重 | 1. 准备RSS/arXiv/GitHub数据<br>2. 其中包含相似内容<br>3. 调用deduplicate | 跨源相似内容被去重 | GLM API + LanceDB | P0 |
| SIT-DUP-004 | 阈值调优测试 | 1. 测试threshold=0.7<br>2. 测试threshold=0.9<br>3. 比较去重数量 | 阈值越高保留越多 | GLM API + LanceDB | P1 |
| SIT-DUP-005 | 不同文本字段去重 | 1. 使用summary字段比较<br>2. 调用deduplicate(items, text_field="summary") | 使用summary进行相似度比较 | GLM API + LanceDB | P1 |

---

## 4. 简报生成集成测试

### 4.1 数据获取到存储完整流程

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-GEN-001 | 完整生成流程 | 1. 调用 `BriefGenerator.generate("2026-05-19")`<br>2. 验证各步骤执行<br>3. 检查数据库存储 | 数据正确存入SQLite，返回success | 所有数据源 + GLM API + 数据库 | P0 |
| SIT-GEN-002 | 多数据源聚合 | 1. 执行generate<br>2. 检查content字段 | HTML包含所有来源分类(h3标题) | 所有数据源 | P0 |
| SIT-GEN-003 | 去重效果验证 | 1. 抓取数据中故意包含相似标题<br>2. 生成简报<br>3. 验证content不含重复 | 相似内容只出现一次 | 所有数据源 + GLM API | P0 |
| SIT-GEN-004 | 分类统计准确性 | 1. 执行generate<br>2. 验证source_count<br>3. 验证categories统计 | count与实际入库条数一致 | 所有数据源 | P1 |
| SIT-GEN-005 | HTML格式验证 | 1. 执行generate<br>2. 检查content HTML结构 | 包含正确的h3/ul/li/a标签 | 所有数据源 | P1 |
| SIT-GEN-006 | 每类最多5条限制 | 1. 某分类数据>5条<br>2. 生成简报<br>3. 验证HTML输出 | 每分类最多显示5条链接 | 所有数据源 | P2 |
| SIT-GEN-007 | 当日重复生成 | 1. 首次生成当天简报<br>2. 再次生成同一天<br>3. 检查数据库 | 更新原有记录(INSERT OR REPLACE) | 数据库 | P1 |
| SIT-GEN-008 | 无数据情况处理 | 1. Mock所有fetcher返回空<br>2. 执行generate | 返回error状态，不写入数据库 | - | P1 |

### 4.2 后台任务集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-BG-001 | 后台生成任务触发 | 1. POST /api/brief/generate<br>2. 验证后台任务执行 | 立即返回generating，后台完成生成 | API服务 | P0 |
| SIT-BG-002 | 后台任务完成验证 | 1. 触发生成<br>2. 等待任务完成<br>3. GET /api/brief/latest | 返回新生成的简报 | API服务 | P0 |
| SIT-BG-003 | 并发生成请求 | 1. 同时发送多个generate请求<br>2. 验证处理 | 正确处理，只有一个生成任务执行 | API服务 | P2 |

---

## 5. API与数据库集成测试

### 5.1 SQLite集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-SQL-001 | 数据库初始化 | 1. 删除现有数据库<br>2. 启动服务<br>3. 验证表结构创建 | briefs和sources表正确创建 | - | P0 |
| SIT-SQL-002 | 简报写入 | 1. 执行generate<br>2. 直接查询SQLite | 数据正确写入briefs表 | - | P0 |
| SIT-SQL-003 | 简报读取 | 1. 写入测试数据<br>2. GET /api/brief/latest | 返回正确数据 | API服务 | P0 |
| SIT-SQL-004 | 日期查询 | 1. 写入多日数据<br>2. GET /api/brief/{date} | 返回指定日期数据 | API服务 | P0 |
| SIT-SQL-005 | 列表查询 | 1. 写入>30条数据<br>2. GET /api/brief/list | 默认返回30条，按日期倒序 | API服务 | P0 |
| SIT-SQL-006 | 分页参数 | 1. GET /api/brief/list?limit=5 | 返回5条数据 | API服务 | P1 |
| SIT-SQL-007 | 数据库锁定处理 | 1. 模拟并发读写<br>2. 验证不出现锁错误 | 正确处理，无数据丢失 | - | P2 |

### 5.2 健康检查与数据库

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-HEALTH-001 | SQLite健康检查 | 1. GET /health<br>2. 验证响应 | sqlite状态为healthy | API服务 | P0 |
| SIT-HEALTH-002 | LanceDB健康检查 | 1. GET /health<br>2. 验证响应 | lancedb状态为healthy | API服务 | P0 |
| SIT-HEALTH-003 | SQLite异常检测 | 1. 删除数据库文件<br>2. GET /health | 返回503，sqlite状态异常 | API服务 | P1 |
| SIT-HEALTH-004 | Ready检查 | 1. GET /ready<br>2. 验证响应 | 200，status=ready | API服务 | P0 |
| SIT-HEALTH-005 | Metrics统计准确性 | 1. 发送多个API请求<br>2. GET /metrics<br>3. 验证统计 | total_requests、error_requests正确 | API服务 | P0 |

---

## 6. 前后端集成测试

### 6.1 页面渲染集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-FE-001 | 首页加载 | 1. GET /<br>2. 验证HTML响应 | 返回index.html，包含静态资源引用 | API服务 | P0 |
| SIT-FE-002 | 静态资源加载 | 1. GET /static/css/style.css<br>2. GET /static/js/app.js | 返回对应静态文件 | API服务 | P0 |
| SIT-FE-003 | API调用加载最新简报 | 1. 打开首页<br>2. 观察网络请求<br>3. 验证数据加载 | 调用/api/brief/latest，数据正确显示 | API服务 + 数据 | P0 |
| SIT-FE-004 | 历史列表加载 | 1. 打开首页<br>2. 观察历史简报区域 | 调用/api/brief/list，列表正确显示 | API服务 + 数据 | P0 |
| SIT-FE-005 | 简报详情页 | 1. GET /api/brief/page/2026-05-19<br>2. 验证HTML结构 | 返回完整HTML页面，包含简报内容 | API服务 + 数据 | P1 |
| SIT-FE-006 | 简报不存在页面 | 1. GET /api/brief/page/2099-01-01 | 返回默认index.html | API服务 | P2 |
| SIT-FE-007 | 错误状态显示 | 1. Mock API返回错误<br>2. 打开首页 | 显示错误提示信息 | API服务 | P1 |

### 6.2 JavaScript与API集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-JS-001 | fetchLatestBrief成功 | 1. 数据库有简报<br>2. 加载首页 | brief-content区域显示简报 | API服务 + 数据 | P0 |
| SIT-JS-002 | fetchLatestBrief失败 | 1. 数据库为空<br>2. 加载首页 | 显示"暂无简报"错误提示 | API服务 | P1 |
| SIT-JS-003 | fetchBriefList成功 | 1. 数据库有多条简报<br>2. 加载首页 | list-content显示历史列表 | API服务 + 数据 | P0 |
| SIT-JS-004 | fetchBriefList空 | 1. 数据库为空<br>2. 加载首页 | 显示"暂无历史简报" | API服务 | P2 |
| SIT-JS-005 | 网络错误处理 | 1. 断开网络<br>2. 加载首页 | 显示网络错误提示 | API服务 | P1 |

---

## 7. 端到端集成场景

### 7.1 完整业务流程

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-E2E-001 | 每日简报生成完整流程 | 1. 清空数据库<br>2. POST /api/brief/generate<br>3. 等待生成完成<br>4. GET /api/brief/latest<br>5. 打开首页验证显示 | 全流程成功，页面正确显示简报 | 完整环境 | P0 |
| SIT-E2E-002 | 历史简报查看流程 | 1. 生成多日简报<br>2. GET /api/brief/list<br>3. 点击历史链接<br>4. GET /api/brief/page/{date} | 历史简报正确显示 | 完整环境 | P0 |
| SIT-E2E-003 | 重复生成处理流程 | 1. 生成当日简报<br>2. 再次生成当日简报<br>3. 验证数据库记录数 | 只有一条当日记录 | 完整环境 | P1 |
| SIT-E2E-004 | 服务重启后数据保留 | 1. 生成简报<br>2. 重启服务<br>3. 查询简报 | 数据完整保留 | 完整环境 | P0 |
| SIT-E2E-005 | 缓存生效验证 | 1. 首次生成简报(记录API调用次数)<br>2. 再次生成相同内容<br>3. 对比API调用次数 | 第二次生成时API调用减少(缓存命中) | 完整环境 + GLM API | P1 |

### 7.2 异常流程集成

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-ERR-001 | 外部API全部不可用 | 1. Mock所有外部API失败<br>2. 执行生成 | 返回error状态，不崩溃 | - | P1 |
| SIT-ERR-002 | 部分数据源不可用 | 1. Mock部分RSS源失败<br>2. 执行生成 | 使用可用数据继续生成 | - | P1 |
| SIT-ERR-003 | 数据库写入失败 | 1. Mock数据库异常<br>2. 执行生成 | 返回error状态，异常被捕获 | - | P1 |
| SIT-ERR-004 | GLM API限流 | 1. 触发GLM API限流<br>2. 执行生成 | 降级处理(不去重或使用缓存) | GLM API | P2 |
| SIT-ERR-005 | 磁盘空间不足 | 1. 模拟磁盘满<br>2. 尝试写入数据库 | 正确处理异常，服务不崩溃 | - | P2 |

---

## 8. 性能集成测试

| 用例ID | 测试场景 | 测试步骤 | 预期结果 | 依赖 | 优先级 |
|--------|----------|----------|----------|------|--------|
| SIT-PERF-001 | 简报生成性能 | 1. 执行generate<br>2. 记录耗时 | 总耗时<60秒 | 完整环境 | P1 |
| SIT-PERF-002 | API响应时间 | 1. GET /api/brief/latest<br>2. 测量响应时间 | <200ms | API服务 | P0 |
| SIT-PERF-003 | 并发API请求 | 1. 10并发请求/api/brief/latest<br>2. 验证响应 | 全部成功，无数据竞争 | API服务 | P1 |
| SIT-PERF-004 | 大量数据去重性能 | 1. 准备100条数据<br>2. 执行deduplicate | 耗时<30秒 | GLM API | P2 |
| SIT-PERF-005 | 数据库查询性能 | 1. 写入1000条简报<br>2. GET /api/brief/list | 响应时间<500ms | 数据库 | P2 |

---

## 9. 测试数据准备

### 9.1 测试数据脚本

```python
# tests/fixtures/integration_data.py
import asyncio
from datetime import datetime, timedelta

# 测试用RSS数据
TEST_RSS_ITEMS = [
    {
        "source": "anthropic",
        "title": "Claude 3.5 Released",
        "link": "https://www.anthropic.com/news/claude-3.5",
        "summary": "Announcing Claude 3.5 with improved capabilities...",
        "published": "2026-05-19",
        "category": "news"
    },
    # ... 更多测试数据
]

# 测试用arXiv数据
TEST_ARXIV_PAPERS = [
    {
        "source": "arxiv",
        "title": "Attention Is All You Need - Revisited",
        "link": "http://arxiv.org/abs/2401.00001",
        "summary": "We revisit the transformer architecture...",
        "published": "2026-05-18",
        "category": "cs.AI",
        "authors": ["Author One", "Author Two"]
    },
    # ... 更多测试数据
]

# 测试用GitHub数据
TEST_GITHUB_RELEASES = [
    {
        "source": "github",
        "title": "anthropic-sdk-python: v0.18.0",
        "link": "https://github.com/anthropics/anthropic-sdk-python/releases/tag/v0.18.0",
        "summary": "New features and bug fixes...",
        "published": "2026-05-17",
        "category": "anthropic-sdk-python"
    },
    # ... 更多测试数据
]

# 生成数据库测试数据
async def seed_test_database():
    """为集成测试准备数据库数据"""
    import sqlite3
    from config import SQLITE_PATH

    conn = sqlite3.connect(SQLITE_PATH)

    # 插入测试简报
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        conn.execute("""
            INSERT OR REPLACE INTO briefs (date, title, content, source_count)
            VALUES (?, ?, ?, ?)
        """, (date, f"Test Brief {date}", f"<p>Content for {date}</p>", 10))

    conn.commit()
    conn.close()
```

### 9.2 Mock服务配置

```python
# tests/fixtures/mock_services.py
import pytest
from unittest.mock import AsyncMock, patch
import httpx

@pytest.fixture
async def mock_external_apis():
    """Mock外部API服务"""
    with patch("httpx.AsyncClient") as mock_client:
        # 配置RSS响应
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, text=MOCK_RSS_XML)
        )
        yield mock_client

@pytest.fixture
async def mock_glm_api():
    """Mock GLM Embedding API"""
    with patch("app.services.embedding.EmbeddingService._call_api") as mock:
        mock.return_value = [0.1] * 2048  # 返回模拟向量
        yield mock
```

---

## 10. 测试执行命令

```bash
# 运行所有集成测试
pytest tests/integration/ -v --asyncio-mode=auto

# 运行指定模块集成测试
pytest tests/integration/test_fetcher_integration.py -v
pytest tests/integration/test_embedding_integration.py -v
pytest tests/integration/test_brief_integration.py -v

# 运行端到端测试
pytest tests/integration/test_e2e.py -v

# 生成覆盖率报告
pytest tests/integration/ --cov=app --cov-report=html

# 使用测试标记运行
pytest tests/integration/ -m "not slow"  # 跳过慢测试
pytest tests/integration/ -m "external"   # 只运行需要外部API的测试
```

---

## 11. 集成测试通过标准

| 指标 | 标准 |
|------|------|
| 测试通过率 | 100% P0用例通过，>=95% P1用例通过 |
| 数据源集成 | 至少80%外部源成功获取数据 |
| 性能指标 | 简报生成<60s，API响应<200ms |
| 数据完整性 | 无数据丢失或损坏 |
| 错误处理 | 所有异常被正确捕获，服务不崩溃 |