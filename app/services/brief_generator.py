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

    async def process_article(self, item: Dict) -> Dict:
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
                }

                # 存储到articles表
                self._save_processed_article(processed_item)
                return processed_item
            else:
                # LLM处理失败，使用原文
                return {**item, "processed": False, "error": summary.error}

        except Exception as e:
            print(f"Error processing article {url}: {e}")
            return {**item, "processed": False, "error": str(e)}

    def _save_processed_article(self, item: Dict):
        """存储处理后的文章到articles表"""
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            conn.execute("""
                INSERT OR REPLACE INTO articles (
                    original_link, original_title, chinese_title, source_name,
                    category, key_points, tech_points, use_cases,
                    industry_impact, chinese_summary, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("link", ""),
                item.get("title", ""),
                item.get("chinese_title", ""),
                item.get("source", "unknown"),
                item.get("category", "news"),
                item.get("核心观点", ""),
                item.get("技术要点", ""),
                item.get("应用场景", ""),
                item.get("行业影响", ""),
                item.get("中文摘要", ""),
                item.get("published", datetime.now().strftime("%Y-%m-%d"))
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving article: {e}")

    async def generate(self, date: str = None, use_llm: bool = True) -> Dict:
        """
        生成简报

        Args:
            date: 日期 YYYY-MM-DD
            use_llm: 是否使用LLM处理（需要API key）
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 抓取所有源
        items = await self.fetch_all_sources()
        if not items:
            return {"status": "error", "message": "无数据抓取"}

        # 2. 如果启用LLM，处理每篇文章
        if use_llm:
            print(f"Processing {len(items)} articles through LLM...")
            tasks = [self.process_article(item) for item in items[:20]]  # 限制20篇避免超时
            processed_items = await asyncio.gather(*tasks)
            items = processed_items

        # 3. 语义去重（使用中文摘要）
        text_field = "中文摘要" if use_llm else "title"
        unique_items = await deduplicate(items, threshold=0.85, text_field=text_field)

        # 4. 按来源分类统计
        categories = {}
        for item in unique_items:
            source = item.get("source", "unknown")
            categories[source] = categories.get(source, 0) + 1

        # 5. 生成简报内容
        content = self._format_content(unique_items, use_llm)

        # 6. 存储到数据库
        brief_id = self._save_brief(date, content, len(unique_items), categories)

        return {
            "status": "success",
            "date": date,
            "brief_id": brief_id,
            "items_count": len(unique_items),
            "sources": categories,
            "llm_processed": use_llm,
        }

    def _format_content(self, items: List[Dict], use_llm: bool) -> str:
        """格式化简报内容为HTML"""
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

                if use_llm and item.get("processed"):
                    # 使用LLM处理后的中文内容
                    chinese_summary = item.get("中文摘要", "")[:200]
                    key_points = item.get("核心观点", "")

                    html_parts.append(f'''
<li>
    <a href="{link}">{title}</a>
    <p><strong>摘要:</strong> {chinese_summary}</p>
    <p><strong>核心观点:</strong> {key_points}</p>
</li>''')
                else:
                    # 使用原始RSS摘要
                    summary = item.get("summary", "")[:100]
                    html_parts.append(f'<li><a href="{link}">{title}</a><p>{summary}</p></li>')

            html_parts.append("</ul>")

        return "\n".join(html_parts)

    def _save_brief(self, date: str, content: str, count: int, categories: Dict) -> int:
        """存储简报到SQLite"""
        conn = sqlite3.connect(SQLITE_PATH)

        title = f"AI Daily Brief - {date}"

        conn.execute("""
            INSERT OR REPLACE INTO briefs (date, title, content, source_count)
            VALUES (?, ?, ?, ?)
        """, (date, title, content, count))

        brief_id = conn.execute("SELECT id FROM briefs WHERE date = ?", (date,)).fetchone()[0]

        conn.commit()
        conn.close()

        return brief_id


async def generate_daily_brief(date: str = None, use_llm: bool = True) -> Dict:
    """便捷函数：生成每日简报"""
    generator = BriefGenerator()
    return await generator.generate(date, use_llm)