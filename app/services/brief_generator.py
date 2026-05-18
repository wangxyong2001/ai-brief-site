"""
AI Daily Brief 生成服务
整合RSS/arXiv/GitHub数据源，使用LanceDB去重，生成每日简报
"""
import asyncio
import sqlite3
from datetime import datetime
from typing import List, Dict

from config import SQLITE_PATH
from app.services.fetcher import RSSFetcher
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.github_fetcher import GitHubReleaseFetcher
from app.services.embedding import deduplicate

class BriefGenerator:
    """简报生成器"""

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

    async def generate(self, date: str = None) -> Dict:
        """生成简报"""
        date = date or datetime.now().strftime("%Y-%m-%d")

        # 1. 抓取所有源
        items = await self.fetch_all_sources()
        if not items:
            return {"status": "error", "message": "无数据抓取"}

        # 2. 语义去重
        unique_items = await deduplicate(items, threshold=0.85, text_field="title")

        # 3. 按来源分类统计
        categories = {}
        for item in unique_items:
            source = item.get("source", "unknown")
            categories[source] = categories.get(source, 0) + 1

        # 4. 生成简报内容
        content = self._format_content(unique_items)

        # 5. 存储到数据库
        brief_id = self._save_brief(date, content, len(unique_items), categories)

        return {
            "status": "success",
            "date": date,
            "brief_id": brief_id,
            "items_count": len(unique_items),
            "sources": categories,
        }

    def _format_content(self, items: List[Dict]) -> str:
        """格式化简报内容为HTML"""
        sections = {}

        for item in items:
            source = item.get("source", "other")
            if source not in sections:
                sections[source] = []
            sections[source].append(item)

        html_parts = []
        for source, items in sections.items():
            source_name = {
                "anthropic": "Anthropic",
                "openai": "OpenAI",
                "deepmind": "DeepMind",
                "huggingface": "Hugging Face",
                "arxiv": "arXiv论文",
                "github": "GitHub Release",
            }.get(source, source)

            html_parts.append(f"<h3>{source_name}</h3><ul>")
            for item in items[:5]:
                title = item.get("title", "")
                link = item.get("link", "")
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


async def generate_daily_brief(date: str = None) -> Dict:
    """便捷函数：生成每日简报"""
    generator = BriefGenerator()
    return await generator.generate(date)