"""
Article content fetcher - extracts full article content from URLs
Handles various sources including arXiv, blogs, and GitHub
"""
import re
import logging
from typing import Optional, Dict
from urllib.parse import urlparse
import httpx
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ArticleReader:
    """
    Fetches and extracts main content from article URLs.
    Uses trafilatura for robust content extraction.
    """

    def __init__(self, timeout: int = 30, max_redirects: int = 10):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AI-Brief-Bot/1.0; +https://github.com/ai-brief)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def fetch_article(self, url: str) -> Optional[Dict]:
        """
        Fetch and extract article content from URL.

        Args:
            url: Article URL to fetch

        Returns:
            Dict with title, content, text, url, source_type or None on failure
        """
        try:
            # Handle special sources
            if "arxiv.org" in url:
                return await self._fetch_arxiv(url)

            if "github.com" in url:
                return await self._fetch_github(url)

            # Generic web page extraction
            return await self._fetch_generic(url)

        except Exception as e:
            logger.error(f"Failed to fetch article from {url}: {e}")
            return None

    async def _fetch_arxiv(self, url: str) -> Optional[Dict]:
        """
        Fetch content from arXiv.
        Handles arXiv's redirect patterns and extracts abstract.
        """
        # Normalize URL to abstract page
        arxiv_id = self._extract_arxiv_id(url)
        if not arxiv_id:
            return await self._fetch_generic(url)

        abstract_url = f"https://arxiv.org/abs/{arxiv_id}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects
            ) as client:
                resp = await client.get(abstract_url, headers=self.headers)

                if resp.status_code != 200:
                    logger.warning(f"arXiv returned {resp.status_code} for {abstract_url}")
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")

                # Extract title
                title_elem = soup.find("h1", class_="title mathjax")
                title = title_elem.get_text(strip=True).replace("Title:", "").strip() if title_elem else ""

                # Extract authors
                authors = []
                author_elem = soup.find("div", class_="authors")
                if author_elem:
                    authors = [a.get_text(strip=True) for a in author_elem.find_all("a")]

                # Extract abstract
                abstract_elem = soup.find("blockquote", class_="abstract mathjax")
                abstract = abstract_elem.get_text(strip=True).replace("Abstract:", "").strip() if abstract_elem else ""

                # Extract categories
                categories = []
                cat_elem = soup.find("div", class_="subjects")
                if cat_elem:
                    categories = [c.strip() for c in cat_elem.get_text().split(",")]

                # Build content
                content = f"Title: {title}\n\nAuthors: {', '.join(authors)}\n\nAbstract: {abstract}"

                return {
                    "title": title,
                    "content": content,
                    "text": abstract,
                    "url": abstract_url,
                    "source_type": "arxiv",
                    "authors": authors,
                    "categories": categories,
                    "abstract": abstract,
                }

        except Exception as e:
            logger.error(f"arXiv fetch error for {url}: {e}")
            return None

    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from various URL formats."""
        patterns = [
            r"arxiv\.org/abs/(\d+\.\d+)",
            r"arxiv\.org/pdf/(\d+\.\d+)",
            r"arxiv\.org/abs/([a-z-]+/\d+)",
            r"arxiv\.org/pdf/([a-z-]+/\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def _fetch_github(self, url: str) -> Optional[Dict]:
        """
        Fetch content from GitHub.
        Extracts release notes or README content.
        """
        try:
            # Check if it's a release URL
            if "/releases/" in url:
                return await self._fetch_github_release(url)

            # Try to fetch README for repo URLs
            return await self._fetch_generic(url)

        except Exception as e:
            logger.error(f"GitHub fetch error for {url}: {e}")
            return await self._fetch_generic(url)

    async def _fetch_github_release(self, url: str) -> Optional[Dict]:
        """Fetch GitHub release notes."""
        # Convert release URL to API URL
        # https://github.com/owner/repo/releases/tag/v1.0 -> /repos/owner/repo/releases/tags/v1.0
        match = re.search(r"github\.com/([^/]+)/([^/]+)/releases/(?:tag/)?(.+)", url)
        if not match:
            return await self._fetch_generic(url)

        owner, repo, tag = match.groups()
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(api_url, headers=self.headers)

                if resp.status_code != 200:
                    return await self._fetch_generic(url)

                data = resp.json()

                title = data.get("name", data.get("tag_name", ""))
                body = data.get("body", "")

                return {
                    "title": title,
                    "content": body,
                    "text": body,
                    "url": url,
                    "source_type": "github_release",
                    "tag": data.get("tag_name", ""),
                    "published_at": data.get("published_at", ""),
                }

        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return await self._fetch_generic(url)

    async def _fetch_generic(self, url: str) -> Optional[Dict]:
        """
        Generic content extraction using trafilatura.
        Works for most web pages.
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects
            ) as client:
                resp = await client.get(url, headers=self.headers)

                if resp.status_code != 200:
                    logger.warning(f"HTTP {resp.status_code} for {url}")
                    return None

                html = resp.text

                # Use trafilatura for extraction
                # Config: favor precision over recall
                config = trafilatura.settings.use_config()
                config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

                extracted = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                    favor_precision=True,
                    output_format="python",
                )

                if not extracted:
                    # Fallback to basic BeautifulSoup extraction
                    extracted = self._fallback_extract(html)

                if not extracted:
                    return None

                # Get title
                title = trafilatura.extract_metadata(html)
                title = title.title if title else ""

                return {
                    "title": title,
                    "content": extracted,
                    "text": extracted,
                    "url": str(resp.url),  # Final URL after redirects
                    "source_type": "web",
                }

        except Exception as e:
            logger.error(f"Generic fetch error for {url}: {e}")
            return None

    def _fallback_extract(self, html: str) -> Optional[str]:
        """Fallback content extraction using BeautifulSoup."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script, style, nav, footer, header
            for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Try to find main content area
            main = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|article|post|entry"))
            if main:
                text = main.get_text(separator="\n", strip=True)
                # Clean up whitespace
                text = re.sub(r"\n{3,}", "\n\n", text)
                return text[:10000]  # Limit length

            # Last resort: get all paragraph text
            paragraphs = soup.find_all("p")
            if paragraphs:
                text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)
                return text[:10000]

            return None

        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return None

    async def fetch_multiple(self, urls: list[str]) -> list[Dict]:
        """
        Fetch multiple articles concurrently.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of article dicts (None entries for failures)
        """
        import asyncio

        tasks = [self.fetch_article(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None
        articles = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching article: {result}")
                articles.append(None)
            else:
                articles.append(result)

        return articles


# Convenience function
async def read_article(url: str) -> Optional[Dict]:
    """Fetch and extract article content from URL."""
    reader = ArticleReader()
    return await reader.fetch_article(url)


async def read_articles(urls: list[str]) -> list[Dict]:
    """Fetch multiple articles concurrently."""
    reader = ArticleReader()
    return await reader.fetch_multiple(urls)