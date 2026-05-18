"""
AI Summarization Service
Supports GLM API (primary) and Claude API (backup)
Outputs structured Chinese summaries
"""
import json
import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """Structured summary result."""
    core_points: str          # 核心观点
    technical_points: str     # 技术要点
    applications: str         # 应用场景
    industry_impact: str      # 行业影响
    chinese_summary: str      # 中文摘要
    raw_response: Optional[str] = None
    model_used: str = ""
    success: bool = True
    error: str = ""


SUMMARY_PROMPT = """你是一位专业的AI技术分析师。请分析以下文章内容，生成结构化的中文摘要。

文章内容：
{content}

请严格按照以下JSON格式输出，不要添加任何其他文字：
{{
    "core_points": "核心观点（1-3个要点，简明扼要）",
    "technical_points": "技术要点（关键技术细节、创新点、方法）",
    "applications": "应用场景（实际应用方向、潜在用途）",
    "industry_impact": "行业影响（对AI行业或相关领域的影响）",
    "chinese_summary": "中文摘要（100-200字综合概述）"
}}

注意：
1. 所有字段必须使用中文
2. 客观分析，不夸张
3. 如果内容不足，填写"暂无相关信息"
4. 确保输出是有效的JSON格式"""


class GLMSummarizer:
    """GLM API Summarizer (智谱AI)."""

    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4"):
        self.api_key = api_key or os.getenv("GLM_API_KEY", "")
        self.model = model

    async def summarize(self, content: str, max_tokens: int = 2000) -> SummaryResult:
        """
        Generate structured summary using GLM API.

        Args:
            content: Article content to summarize
            max_tokens: Maximum tokens in response

        Returns:
            SummaryResult with structured fields
        """
        if not self.api_key:
            return SummaryResult(
                core_points="", technical_points="", applications="",
                industry_impact="", chinese_summary="",
                success=False, error="GLM_API_KEY not configured"
            )

        if not content or len(content.strip()) < 50:
            return SummaryResult(
                core_points="内容过短", technical_points="无法分析",
                applications="暂无", industry_impact="暂无",
                chinese_summary="文章内容过短，无法生成有效摘要",
                success=False, error="Content too short"
            )

        prompt = SUMMARY_PROMPT.format(content=content[:8000])  # Limit input length

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3,  # Lower temperature for consistency
                    }
                )

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"GLM API error: {response.status_code} - {error_text}")
                    return SummaryResult(
                        core_points="", technical_points="", applications="",
                        industry_impact="", chinese_summary="",
                        success=False, error=f"API error: {response.status_code}"
                    )

                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]

                return self._parse_response(raw_content, "glm")

        except httpx.TimeoutException:
            logger.error("GLM API timeout")
            return SummaryResult(
                core_points="", technical_points="", applications="",
                industry_impact="", chinese_summary="",
                success=False, error="API timeout"
            )
        except Exception as e:
            logger.error(f"GLM API error: {e}")
            return SummaryResult(
                core_points="", technical_points="", applications="",
                industry_impact="", chinese_summary="",
                success=False, error=str(e)
            )

    def _parse_response(self, raw_content: str, model: str) -> SummaryResult:
        """Parse LLM response into structured result."""
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks
            content = raw_content.strip()
            if content.startswith("```"):
                # Remove code block markers
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            # Parse JSON
            parsed = json.loads(content)

            return SummaryResult(
                core_points=parsed.get("core_points", ""),
                technical_points=parsed.get("technical_points", ""),
                applications=parsed.get("applications", ""),
                industry_impact=parsed.get("industry_impact", ""),
                chinese_summary=parsed.get("chinese_summary", ""),
                raw_response=raw_content,
                model_used=model,
                success=True
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            # Try to extract fields manually
            return self._fallback_parse(raw_content, model)

    def _fallback_parse(self, content: str, model: str) -> SummaryResult:
        """Fallback parser for malformed responses."""
        import re

        def extract_field(text: str, field: str) -> str:
            patterns = [
                rf'"{field}":\s*"([^"]*)"',
                rf'{field}:\s*([^\n]+)',
                rf'【{field}】[:：]\s*([^\n]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()
            return "解析失败"

        return SummaryResult(
            core_points=extract_field(content, "core_points"),
            technical_points=extract_field(content, "technical_points"),
            applications=extract_field(content, "applications"),
            industry_impact=extract_field(content, "industry_impact"),
            chinese_summary=extract_field(content, "chinese_summary"),
            raw_response=content,
            model_used=model,
            success=True
        )


class ClaudeSummarizer:
    """Claude API Summarizer (backup)."""

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model

    async def summarize(self, content: str, max_tokens: int = 2000) -> SummaryResult:
        """Generate structured summary using Claude API."""
        if not self.api_key:
            return SummaryResult(
                core_points="", technical_points="", applications="",
                industry_impact="", chinese_summary="",
                success=False, error="ANTHROPIC_API_KEY not configured"
            )

        if not content or len(content.strip()) < 50:
            return SummaryResult(
                core_points="内容过短", technical_points="无法分析",
                applications="暂无", industry_impact="暂无",
                chinese_summary="文章内容过短，无法生成有效摘要",
                success=False, error="Content too short"
            )

        prompt = SUMMARY_PROMPT.format(content=content[:8000])

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Claude API error: {response.status_code} - {error_text}")
                    return SummaryResult(
                        core_points="", technical_points="", applications="",
                        industry_impact="", chinese_summary="",
                        success=False, error=f"API error: {response.status_code}"
                    )

                data = response.json()
                raw_content = data["content"][0]["text"]

                # Use same parsing logic as GLM
                glm_summarizer = GLMSummarizer()
                return glm_summarizer._parse_response(raw_content, "claude")

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return SummaryResult(
                core_points="", technical_points="", applications="",
                industry_impact="", chinese_summary="",
                success=False, error=str(e)
            )


class AISummarizer:
    """
    Main summarizer with fallback support.
    Tries GLM first, falls back to Claude if configured.
    """

    def __init__(self):
        self.glm = GLMSummarizer()
        self.claude = ClaudeSummarizer()
        self._fallback_enabled = bool(os.getenv("ANTHROPIC_API_KEY"))

    async def summarize(self, content: str, prefer_model: str = "glm") -> SummaryResult:
        """
        Generate summary with automatic fallback.

        Args:
            content: Article content to summarize
            prefer_model: Preferred model ("glm" or "claude")

        Returns:
            SummaryResult with structured fields
        """
        # Try preferred model first
        if prefer_model == "claude" and self.claude.api_key:
            result = await self.claude.summarize(content)
            if result.success:
                return result

        # Try GLM
        result = await self.glm.summarize(content)
        if result.success:
            return result

        # Fallback to Claude if GLM failed
        if self._fallback_enabled and self.claude.api_key and prefer_model != "claude":
            logger.info("GLM failed, trying Claude as fallback")
            result = await self.claude.summarize(content)
            if result.success:
                return result

        return result

    async def summarize_batch(
        self,
        items: list[Dict[str, Any]],
        content_field: str = "content"
    ) -> list[Dict[str, Any]]:
        """
        Summarize multiple items.

        Args:
            items: List of items with content
            content_field: Field name containing content

        Returns:
            Items with added summary fields
        """
        import asyncio

        async def process_item(item: Dict) -> Dict:
            content = item.get(content_field, "")
            if not content:
                return {**item, "summary": None}

            result = await self.summarize(content)
            return {
                **item,
                "summary": {
                    "core_points": result.core_points,
                    "technical_points": result.technical_points,
                    "applications": result.applications,
                    "industry_impact": result.industry_impact,
                    "chinese_summary": result.chinese_summary,
                    "model": result.model_used,
                    "success": result.success,
                }
            }

        tasks = [process_item(item) for item in items]
        return await asyncio.gather(*tasks)


# Convenience functions
async def summarize_article(content: str) -> SummaryResult:
    """Summarize a single article."""
    summarizer = AISummarizer()
    return await summarizer.summarize(content)


async def summarize_articles(items: list[Dict], content_field: str = "content") -> list[Dict]:
    """Summarize multiple articles."""
    summarizer = AISummarizer()
    return await summarizer.summarize_batch(items, content_field)