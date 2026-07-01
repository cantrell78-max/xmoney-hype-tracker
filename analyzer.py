"""Grok-powered analysis of xMoney rollout chatter."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config import settings
from hype import fallback_analysis, heuristic_sentiment
from models import AnalysisResult, Post, SentimentBreakdown

SYSTEM_PROMPT = """You analyze X (Twitter) posts about the xMoney payments rollout.
Return ONLY valid JSON with this schema:
{
  "summary": "2-3 sentence markdown summary of overall buzz",
  "rollout_insights": "bullet list (markdown) of rollout status observations",
  "sentiment": {"positive": int, "negative": int, "hype": int, "neutral": int},
  "post_sentiments": {"<post_id>": "positive|negative|hype|neutral", ...}
}
Count each post exactly once in sentiment totals. Be concise and factual."""


class AnalyzerError(Exception):
    pass


def _client() -> OpenAI | None:
    if not settings.xai_api_key:
        return None
    return OpenAI(api_key=settings.xai_api_key, base_url=settings.xai_base_url)


def _format_posts_for_prompt(posts: list[Post]) -> str:
    lines = []
    for post in posts[: settings.max_posts]:
        lines.append(
            f"- id={post.id} @{post.author} engagement={post.engagement} "
            f"time={post.created_at.isoformat()}\n  {post.text}"
        )
    return "\n".join(lines)


def _parse_sentiment(raw: dict[str, Any]) -> SentimentBreakdown:
    return SentimentBreakdown(
        positive=int(raw.get("positive", 0)),
        negative=int(raw.get("negative", 0)),
        hype=int(raw.get("hype", 0)),
        neutral=int(raw.get("neutral", 0)),
    )


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    return json.loads(text)


def analyze_posts(posts: list[Post]) -> AnalysisResult:
    if not posts:
        return AnalysisResult(
            summary="No posts found for the current search window.",
            rollout_insights="Try refreshing or check X API credentials.",
            source="empty",
        )

    client = _client()
    if client is None:
        result = fallback_analysis(posts)
        result.source = "heuristic (no API key)"
        return result

    user_content = (
        f"Analyze these {len(posts)} posts about xMoney / x money rollout:\n\n"
        f"{_format_posts_for_prompt(posts)}"
    )

    try:
        response = client.chat.completions.create(
            model=settings.xai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        content = (response.choices[0].message.content or "").strip()
        data = _extract_json(content)
        return AnalysisResult(
            summary=data.get("summary", ""),
            rollout_insights=data.get("rollout_insights", ""),
            sentiment=_parse_sentiment(data.get("sentiment", {})),
            post_sentiments={
                str(k): str(v) for k, v in (data.get("post_sentiments") or {}).items()
            },
            source="grok",
        )
    except Exception:
        result = fallback_analysis(posts)
        result.sentiment = heuristic_sentiment(posts)
        result.source = "heuristic (Grok error)"
        return result