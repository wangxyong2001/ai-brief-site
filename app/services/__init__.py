"""Services module"""
from app.services.fetcher import RSSFetcher
from app.services.arxiv_fetcher import ArxivFetcher
from app.services.github_fetcher import GitHubReleaseFetcher
from app.services.embedding import get_embedding, deduplicate
from app.services.brief_generator import BriefGenerator, generate_daily_brief
from app.services.article_reader import ArticleReader, read_article, read_articles
from app.services.ai_summarizer import AISummarizer, summarize_article, summarize_articles