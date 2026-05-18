"""
AI Daily Brief Site - Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Database paths
LANCEDB_PATH = DATA_DIR / "lancedb"
SQLITE_PATH = DATA_DIR / "metadata.db"

# API Keys
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_API_URL = os.getenv("GLM_API_URL", "https://open.bigmodel.cn/api/paas/v4/embeddings")
GLM_EMBED_MODEL = "embedding-3"

# Sources configuration
RSS_FEEDS = [
    "https://www.anthropic.com/news/rss",
    "https://openai.com/blog/rss.xml",
    "https://deepmind.google/discover/blog/rss.xml",
]

ARXIV_CATEGORIES = [
    "cs.AI",
    "cs.CL",
    "cs.LG",
    "cs.CV",
]

# Server config
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# SLO thresholds
SLO_ERROR_RATE_THRESHOLD = 0.01  # 1% error rate
SLO_LATENCY_THRESHOLD_MS = 2000  # 2s max latency