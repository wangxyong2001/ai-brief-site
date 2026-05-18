"""
GitHub Release抓取服务
"""
import httpx
from typing import Dict, List
import asyncio


class GitHubReleaseFetcher:
    """GitHub Release抓取器"""

    PROJECTS = [
        "anthropics/anthropic-sdk-python",
        "openai/openai-python",
        "huggingface/transformers",
        "pytorch/pytorch",
        "langchain-ai/langchain",
        "ollama/ollama",
    ]

    async def fetch_release(self, repo: str) -> Dict | None:
        """抓取单个项目的最新Release"""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return None
                if resp.status_code != 200:
                    return None
                data = resp.json()

            return {
                "title": data.get("name") or data.get("tag_name", "Unknown"),
                "link": data.get("html_url", ""),
                "summary": (data.get("body") or "")[:500],
                "published": data.get("published_at", ""),
                "category": repo.split("/")[-1],
                "repo": repo,
            }
        except Exception as e:
            print(f"GitHub抓取失败 [{repo}]: {e}")
            return None

    async def fetch_all(self) -> List[Dict]:
        """抓取所有项目Release"""
        tasks = [self.fetch_release(repo) for repo in self.PROJECTS]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]