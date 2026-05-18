"""
arXiv论文抓取服务
"""
import httpx
import feedparser
import asyncio
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    link: str
    summary: str
    published: str
    category: str
    authors: List[str]

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published,
            "category": self.category,
            "authors": self.authors,
        }


class ArxivFetcher:
    CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]
    BASE_URL = "http://export.arxiv.org/api/query"
    TIMEOUT = 30.0

    async def fetch_papers(self, category: str, max_results: int = 20) -> List[Paper]:
        url = f"{self.BASE_URL}?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

            papers = []
            for entry in feed.entries:
                papers.append(Paper(
                    title=entry.get("title", "").strip().replace("\n", " "),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", "").strip().replace("\n", " ")[:500],
                    published=entry.get("published", ""),
                    category=category,
                    authors=[a.get("name", "") for a in entry.get("authors", [])],
                ))
            return papers

        except httpx.TimeoutException:
            print(f"arXiv请求超时 [{category}]")
            return []
        except httpx.HTTPStatusError as e:
            print(f"arXiv请求失败 [{category}]: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"arXiv解析失败 [{category}]: {e}")
            return []

    async def fetch_all(self, max_results_per_category: int = 20) -> List[Paper]:
        tasks = [self.fetch_papers(cat, max_results_per_category) for cat in self.CATEGORIES]
        results = await asyncio.gather(*tasks)
        return [paper for papers in results for paper in papers]

    async def fetch_all_as_dict(self, max_results_per_category: int = 20) -> List[Dict]:
        papers = await self.fetch_all(max_results_per_category)
        return [p.to_dict() for p in papers]


async def fetch_arxiv_papers(max_results: int = 20) -> List[Dict]:
    fetcher = ArxivFetcher()
    return await fetcher.fetch_all_as_dict(max_results)