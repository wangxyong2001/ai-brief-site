"""
数据抓取服务
"""
import feedparser
import httpx
from datetime import datetime
from typing import List, Dict
import asyncio

class RSSFetcher:
    """RSS Feed抓取器"""

    FEEDS = {
        "anthropic": "https://www.anthropic.com/news/rss",
        "openai": "https://openai.com/blog/rss.xml",
        "deepmind": "https://deepmind.google/discover/blog/rss.xml",
        "huggingface": "https://huggingface.co/blog/feed.xml",
    }

    async def fetch_feed(self, source: str, url: str) -> List[Dict]:
        """抓取单个RSS feed"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                feed = feedparser.parse(resp.text)

            items = []
            for entry in feed.entries[:10]:  # 取最新10条
                items.append({
                    "source": source,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],
                    "published": entry.get("published", entry.get("updated", "")),
                    "category": "news",
                })
            return items
        except Exception as e:
            print(f"RSS抓取失败 [{source}]: {e}")
            return []

    async def fetch_all(self) -> List[Dict]:
        """抓取所有RSS源"""
        tasks = [
            self.fetch_feed(source, url)
            for source, url in self.FEEDS.items()
        ]
        results = await asyncio.gather(*tasks)
        return [item for items in results for item in items]


class ArxivFetcher:
    """arXiv论文抓取器"""

    CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]

    async def fetch_papers(self, category: str, max_results: int = 20) -> List[Dict]:
        """抓取arXiv最新论文"""
        url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                feed = feedparser.parse(resp.text)

            papers = []
            for entry in feed.entries:
                papers.append({
                    "source": "arxiv",
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "").strip()[:300],
                    "published": entry.get("published", ""),
                    "category": category,
                    "authors": [a.get("name", "") for a in entry.get("authors", [])],
                })
            return papers
        except Exception as e:
            print(f"arXiv抓取失败 [{category}]: {e}")
            return []

    async def fetch_all(self) -> List[Dict]:
        """抓取所有分类论文"""
        tasks = [self.fetch_papers(cat) for cat in self.CATEGORIES]
        results = await asyncio.gather(*tasks)
        return [paper for papers in results for paper in papers]


class GitHubFetcher:
    """GitHub Release抓取器"""

    # 热门AI项目
    PROJECTS = [
        "anthropics/anthropic-sdk-python",
        "openai/openai-python",
        "huggingface/transformers",
        "pytorch/pytorch",
        "tensorflow/tensorflow",
        "langchain-ai/langchain",
        "microsoft/semantic-kernel",
        "ollama/ollama",
    ]

    async def fetch_release(self, repo: str) -> Dict | None:
        """抓取单个项目的最新Release"""
        url = f"https://api.github.com/repos/{repo}/releases/latest"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()

            return {
                "source": "github",
                "title": f"{repo}: {data.get('name', data.get('tag_name', 'Unknown'))}",
                "link": data.get("html_url", ""),
                "summary": data.get("body", "")[:300] if data.get("body") else "",
                "published": data.get("published_at", ""),
                "category": repo.split("/")[-1],
            }
        except Exception as e:
            print(f"GitHub抓取失败 [{repo}]: {e}")
            return None

    async def fetch_all(self) -> List[Dict]:
        """抓取所有项目Release"""
        tasks = [self.fetch_release(repo) for repo in self.PROJECTS]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]


async def fetch_all_sources() -> List[Dict]:
    """抓取所有数据源"""
    rss = RSSFetcher()
    arxiv = ArxivFetcher()
    github = GitHubFetcher()

    results = await asyncio.gather(
        rss.fetch_all(),
        arxiv.fetch_all(),
        github.fetch_all(),
    )

    return [item for items in results for item in items]