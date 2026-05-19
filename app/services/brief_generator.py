"""
AI Daily Brief 生成服务 v4
整合RSS/arXiv/GitHub数据源，全文阅读+LLM中文整理，生成每日简报
"""
import asyncio
import sqlite3
import json
from datetime import datetime
from typing import List, Dict

from config import SQLITE_PATH
from app.services.fetcher import RSSFetcher
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.github_fetcher import GitHubReleaseFetcher
from app.services.article_reader import ArticleReader
from app.services.ai_summarizer import AISummarizer
from app.services.embedding import deduplicate

class BriefGenerator:
    """简报生成器 v4 - 支持全文阅读+LLM中文整理"""

    def __init__(self):
        self.article_reader = ArticleReader()
        self.summarizer = AISummarizer()

    async def fetch_all_sources(self) -> List[Dict]:
        """抓取所有数据源"""
        rss = RSSFetcher()
        arxiv = ArxivFetcher()
        github = GitHubReleaseFetcher()

        results = await asyncio.gather(
            rss.fetch_all(),
            arxiv.fetch_all_as_dict(),
            github.fetch_all(),
        )

        all_items = []
        for items in results:
            all_items.extend(items)

        return all_items

    async def process_article(self, item: Dict, brief_id: int = None) -> Dict:
        """
        处理单篇文章: 全文抓取 + LLM中文整理
        """
        url = item.get("link", "")
        if not url:
            return item

        try:
            # 1. 抓取全文
            article = await self.article_reader.fetch_article(url)
            if not article:
                # 使用RSS摘要作为fallback
                return {**item, "processed": False}

            content = article.get("content", article.get("text", item.get("summary", "")))

            # 2. LLM中文整理
            summary = await self.summarizer.summarize(content)

            if summary.success:
                # 成功生成中文摘要
                processed_item = {
                    **item,
                    "processed": True,
                    "chinese_title": summary.chinese_summary[:50] if summary.chinese_summary else item.get("title", ""),
                    "核心观点": summary.core_points,
                    "技术要点": summary.technical_points,
                    "应用场景": summary.applications,
                    "行业影响": summary.industry_impact,
                    "中文摘要": summary.chinese_summary,
                    "model_used": summary.model_used,
                    "brief_id": brief_id,
                }

                return processed_item
            else:
                # LLM处理失败，使用原文
                return {**item, "processed": False, "error": summary.error, "brief_id": brief_id}

        except Exception as e:
            print(f"Error processing article {url}: {e}")
            return {**item, "processed": False, "error": str(e), "brief_id": brief_id}

    async def generate(self, date: str = None, use_llm: bool = True) -> Dict:
        """
        生成简报

        Args:
            date: 日期 YYYY-MM-DD
            use_llm: 是否使用LLM处理（需要API key）
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 先创建简报记录，获取brief_id
        brief_id = self._create_brief_record(date)

        # 2. 抓取所有源
        items = await self.fetch_all_sources()
        if not items:
            return {"status": "error", "message": "无数据抓取"}

        # 3. 如果启用LLM，处理每篇文章并设置brief_id
        if use_llm:
            print(f"Processing {len(items)} articles through LLM...")
            tasks = [self.process_article(item, brief_id) for item in items[:20]]
            processed_items = await asyncio.gather(*tasks)
            items = processed_items

        # 4. 存储文章（带brief_id）
        saved_articles = self._save_articles(items, brief_id)

        # 5. 语义去重
        text_field = "中文摘要" if use_llm else "title"
        unique_items = await deduplicate(saved_articles, threshold=0.85, text_field=text_field)

        # 6. 按来源分类统计
        categories = {}
        for item in unique_items:
            source = item.get("source", "unknown")
            categories[source] = categories.get(source, 0) + 1

        # 7. 生成简报内容（包含文章ID）
        content = self._format_content(unique_items)

        # 8. 更新简报内容
        self._update_brief_content(brief_id, content, len(unique_items))

        return {
            "status": "success",
            "date": date,
            "brief_id": brief_id,
            "items_count": len(unique_items),
            "sources": categories,
            "articles": unique_items,
            "llm_processed": use_llm,
        }

    def _create_brief_record(self, date: str) -> int:
        """创建简报记录并返回ID"""
        conn = sqlite3.connect(SQLITE_PATH)
        title = f"AI Daily Brief - {date}"

        # 先检查是否已存在
        existing = conn.execute("SELECT id FROM briefs WHERE date = ?", (date,)).fetchone()
        if existing:
            conn.close()
            return existing[0]

        conn.execute("""
            INSERT INTO briefs (date, title, content, source_count)
            VALUES (?, ?, '', 0)
        """, (date, title))

        brief_id = conn.execute("SELECT id FROM briefs WHERE date = ?", (date,)).fetchone()[0]
        conn.commit()
        conn.close()
        return brief_id

    def _update_brief_content(self, brief_id: int, content: str, count: int):
        """更新简报内容"""
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("""
            UPDATE briefs SET content = ?, source_count = ? WHERE id = ?
        """, (content, count, brief_id))
        conn.commit()
        conn.close()

    def _save_articles(self, items: List[Dict], brief_id: int) -> List[Dict]:
        """批量存储文章并返回带ID的列表"""
        conn = sqlite3.connect(SQLITE_PATH)
        saved = []

        for item in items:
            # 检查是否已存在
            existing = conn.execute(
                "SELECT id FROM articles WHERE original_link = ?",
                (item.get("link", ""),)
            ).fetchone()

            if existing:
                # 更新brief_id
                conn.execute(
                    "UPDATE articles SET brief_id = ? WHERE id = ?",
                    (brief_id, existing[0])
                )
                item["id"] = existing[0]
            else:
                # 插入新文章
                conn.execute("""
                    INSERT INTO articles (
                        original_link, original_title, chinese_title, source_name,
                        category, key_points, tech_points, use_cases,
                        industry_impact, chinese_summary, published_at, brief_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get("link", ""),
                    item.get("title", ""),
                    item.get("chinese_title", ""),
                    item.get("source", "unknown"),
                    item.get("category", "news"),
                    json.dumps(item.get("核心观点", [])) if isinstance(item.get("核心观点"), list) else item.get("核心观点", ""),
                    item.get("技术要点", ""),
                    item.get("应用场景", ""),
                    item.get("行业影响", ""),
                    item.get("中文摘要", ""),
                    item.get("published", datetime.now().strftime("%Y-%m-%d")),
                    brief_id
                ))
                item["id"] = conn.execute(
                    "SELECT id FROM articles WHERE original_link = ?",
                    (item.get("link", ""),)
                ).fetchone()[0]

            saved.append(item)

        conn.commit()
        conn.close()
        return saved

    def _format_content(self, items: List[Dict]) -> str:
        """格式化简报内容为HTML，包含文章ID"""
        sections = {}

        for item in items:
            source = item.get("source", "other")
            if source not in sections:
                sections[source] = []
            sections[source].append(item)

        html_parts = []

        for source, source_items in sections.items():
            source_name = {
                "anthropic": "Anthropic",
                "openai": "OpenAI",
                "deepmind": "DeepMind",
                "huggingface": "Hugging Face",
                "arxiv": "arXiv论文",
                "github": "GitHub Release",
            }.get(source, source)

            html_parts.append(f"<h3>{source_name}</h3><ul>")

            for item in source_items[:5]:
                title = item.get("title", "")
                link = item.get("link", "")
                article_id = item.get("id", 0)

                if item.get("processed") or item.get("中文摘要"):
                    chinese_summary = item.get("中文摘要", "")[:200]
                    key_points = item.get("核心观点", "")

                    html_parts.append(f'''
<li data-id="{article_id}" data-link="{link}">
    <a href="{link}">{title}</a>
    <p><strong>摘要:</strong> {chinese_summary}</p>
    <p><strong>核心观点:</strong> {key_points}</p>
</li>''')
                else:
                    summary = item.get("summary", "")[:100]
                    html_parts.append(f'<li data-id="{article_id}" data-link="{link}"><a href="{link}">{title}</a><p>{summary}</p></li>')

            html_parts.append("</ul>")

        return "\n".join(html_parts)


async def generate_daily_brief(date: str = None, use_llm: bool = True) -> Dict:
    """便捷函数：生成每日简报"""
    generator = BriefGenerator()
    return await generator.generate(date, use_llm)