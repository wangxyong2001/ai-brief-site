# AI Daily Brief v4 升级计划 - 详细阅读 + 中文整理

## 当前问题

| 问题 | 现状 | 要求 |
|------|------|------|
| 内容深度 | RSS摘要(100-500字) | **全文阅读理解** |
| 语言 | 英文原文 | **中文整理输出** |
| 信源配置 | 简单硬编码 | **精选信源分级** |
| 输出风格 | 固定HTML | **20种风格可选** |

## 升级方案

### Phase 1: 全文抓取 + 详细阅读

```python
# 现状: 只取RSS摘要
article = {
    "title": entry.title,
    "summary": entry.summary[:100]  # ❌ 截断
}

# 升级: 全文抓取 + AI阅读理解
article = await fetch_full_article(entry.link)
summary = await ai_read_and_summarize(article.content, language="zh-CN")
```

### Phase 2: 中文整理系统

```
输入: 英文原文 (全文)
  ↓
AI阅读理解
  ↓
提取关键信息:
  - 核心观点 (3条)
  - 技术要点 (如有代码)
  - 应用场景
  - 行业影响
  ↓
生成中文摘要 (300-500字)
```

### Phase 3: 精选信源分级

```json
{
  "tier_1_core": [
    {"name": "OpenAI News", "weight": 10},
    {"name": "Anthropic News", "weight": 10},
    {"name": "Hugging Face", "weight": 9},
    {"name": "机器之心", "weight": 9},
    {"name": "arXiv cs.AI", "weight": 8}
  ],
  "tier_2_important": [
    {"name": "TechCrunch AI", "weight": 7},
    {"name": "MIT Tech Review", "weight": 7},
    {"name": "量子位", "weight": 7},
    {"name": "LangChain Blog", "weight": 6}
  ],
  "tier_3_github": [
    {"name": "vLLM", "weight": 8},
    {"name": "Ollama", "weight": 8}
  ]
}
```

### Phase 4: 20种简报风格

| 风格 | 特点 | 输出格式 |
|------|------|----------|
| lobster | TOP3 + 人话解读 | Markdown |
| news | 客观简洁 | Markdown |
| academic | 深度分析 | Markdown |
| tech | 代码+架构 | Markdown |
| flash | 一句话摘要 | Text |

## 技术实现

### 1. 全文抓取服务

```python
# app/services/article_reader.py

async def fetch_full_content(url: str) -> str:
    """抓取文章全文"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True)
        html = resp.text
        # 提取正文
        text = extract_main_content(html)
        return text

async def ai_summarize_zh(content: str, api_key: str) -> Dict:
    """AI阅读理解并生成中文摘要"""
    prompt = f"""
阅读以下英文文章，用中文整理关键信息：

{content}

输出JSON格式：
{
  "核心观点": ["...", "...", "..."],
  "技术要点": "...",
  "应用场景": "...",
  "行业影响": "...",
  "中文摘要": "... (300-500字)"
}
"""
    # 调用GLM/Claude API
    result = await call_llm(prompt, api_key)
    return json.loads(result)
```

### 2. 简报生成流程

```
┌─────────────────────────────────────────────────────┐
│                   详细阅读流程                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  RSS抓取                                             │
│  └─ 获取标题+链接                                     │
│                                                      │
│  全文抓取 (并发)                                      │
│  ├─ fetch_full_content(url[0])                      │
│  ├─ fetch_full_content(url[1])                      │
│  └─ fetch_full_content(url[N])                      │
│                                                      │
│  AI阅读理解 (并发)                                    │
│  ├─ ai_summarize_zh(content[0]) → 中文摘要           │
│  ├─ ai_summarize_zh(content[1]) → 中文摘要           │
│  └─ ai_summarize_zh(content[N]) → 中文摘要           │
│                                                      │
│  向量去重                                            │
│  └─ 基于中文摘要去重                                  │
│                                                      │
│  筀展评分                                            │
│  ├─ source_weight: 10/7/5                            │
│  ├─ freshness: 6h内+3, 24h内+2                       │
│  └─ multi_source_bonus: +5                          │
│                                                      │
│  生成简报                                            │
│  └─ 根据style参数选择格式                             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## API设计

### POST /api/brief/generate

```json
{
  "date": "2026-05-19",
  "style": "lobster",  // 可选: lobster/news/tech/academic
  "language": "zh-CN",
  "max_articles": 20,
  "include_full_content": true  // 是否全文阅读
}
```

### Response

```json
{
  "status": "success",
  "brief_id": 3,
  "articles_count": 15,
  "articles": [
    {
      "title": "Claude 3.5 Sonnet 发布",
      "original_link": "https://anthropic.com/news/...",
      "chinese_title": "Anthropic发布Claude 3.5 Sonnet模型",
      "核心观点": ["性能超越GPT-4", "成本降低50%", "API已上线"],
      "技术要点": "新架构,推理速度提升3倍",
      "中文摘要": "Anthropic今日发布Claude 3.5 Sonnet...",
      "score": 13,
      "category": "product"
    }
  ]
}
```

## 待办事项

- [ ] 复制 curated-sources.json 到 ai-brief-site
- [ ] 创建 article_reader.py 服务
- [ ] 创建 ai_summarizer.py (中文整理)
- [ ] 创建 style_generator.py (20种风格)
- [ ] 更新 brief_generator.py 流程
- [ ] 更新 API 接口
- [ ] 配置 GLM_API_KEY (中文生成)
- [ ] 测试全文抓取 + 中文输出