"""Hype score and chart helpers."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go

from models import AnalysisResult, Post, SentimentBreakdown


def compute_hype_score(posts: list[Post], sentiment: SentimentBreakdown) -> int:
    """Score 0–100 from mention volume, engagement, and positive/hype sentiment."""
    if not posts:
        return 0

    volume = len(posts)
    engagement = sum(p.engagement for p in posts)
    max_engagement = max(p.engagement for p in posts)

    volume_score = min(volume / 30, 1.0) * 35
    engagement_score = min(engagement / 5000, 1.0) * 35
    peak_score = min(max_engagement / 1500, 1.0) * 15

    total = sentiment.total or 1
    bullish = sentiment.positive + sentiment.hype
    sentiment_score = (bullish / total) * 15

    return int(round(min(volume_score + engagement_score + peak_score + sentiment_score, 100)))


def score_color(score: int) -> str:
    if score >= 75:
        return "#22c55e"
    if score >= 50:
        return "#eab308"
    if score >= 25:
        return "#f97316"
    return "#ef4444"


def trending_posts(posts: list[Post], limit: int = 10) -> list[Post]:
    return sorted(posts, key=lambda p: p.engagement, reverse=True)[:limit]


def posts_to_dataframe(posts: list[Post]) -> pd.DataFrame:
    rows = [
        {
            "id": p.id,
            "text": p.text,
            "author": p.author,
            "created_at": p.created_at,
            "likes": p.likes,
            "retweets": p.retweets,
            "replies": p.replies,
            "engagement": p.engagement,
            "url": p.url,
        }
        for p in posts
    ]
    return pd.DataFrame(rows)


def mentions_over_time_chart(posts: list[Post]) -> go.Figure:
    if not posts:
        fig = go.Figure()
        fig.update_layout(title="Mentions over time", height=320)
        return fig

    df = posts_to_dataframe(posts)
    df["hour"] = df["created_at"].dt.floor("h")
    counts = df.groupby("hour").size().reset_index(name="mentions")

    fig = go.Figure(
        go.Scatter(
            x=counts["hour"],
            y=counts["mentions"],
            mode="lines+markers",
            fill="tozeroy",
            line={"color": "#8b5cf6", "width": 2},
            marker={"size": 6},
            name="Mentions",
        )
    )
    fig.update_layout(
        title="Mentions over time",
        xaxis_title="Time (UTC)",
        yaxis_title="Posts",
        height=320,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def sentiment_chart(sentiment: SentimentBreakdown) -> go.Figure:
    labels = ["Positive", "Hype", "Neutral", "Negative"]
    values = [sentiment.positive, sentiment.hype, sentiment.neutral, sentiment.negative]
    colors = ["#22c55e", "#a855f7", "#94a3b8", "#ef4444"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker={"colors": colors},
            textinfo="label+percent",
        )
    )
    fig.update_layout(
        title="Sentiment breakdown",
        height=320,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        showlegend=False,
    )
    return fig


def format_posts_table(posts: list[Post], sentiments: dict[str, str] | None = None) -> list[list]:
    sentiments = sentiments or {}
    rows: list[list] = []
    for post in trending_posts(posts):
        sentiment = sentiments.get(post.id, "—")
        rows.append(
            [
                f"@{post.author}",
                post.text[:140] + ("…" if len(post.text) > 140 else ""),
                post.engagement,
                sentiment,
                post.created_at.strftime("%b %d %H:%M"),
                post.url or "—",
            ]
        )
    return rows


def heuristic_sentiment(posts: list[Post]) -> SentimentBreakdown:
    """Fast offline sentiment when Grok is unavailable."""
    positive_words = {"smooth", "great", "bullish", "love", "polished", "works", "excited", "best"}
    negative_words = {"concerned", "failed", "skeptical", "uncomfortable", "waiting", "timed out", "bugs"}
    hype_words = {"hype", "fomo", "exploding", "wild", "insane", "moon", "shipping", "rollout"}

    counts = Counter()
    for post in posts:
        text = post.text.lower()
        if any(w in text for w in hype_words):
            counts["hype"] += 1
        elif any(w in text for w in negative_words):
            counts["negative"] += 1
        elif any(w in text for w in positive_words):
            counts["positive"] += 1
        else:
            counts["neutral"] += 1

    return SentimentBreakdown(
        positive=counts["positive"],
        negative=counts["negative"],
        hype=counts["hype"],
        neutral=counts["neutral"],
    )


def fallback_analysis(posts: list[Post]) -> AnalysisResult:
    sentiment = heuristic_sentiment(posts)
    volume = len(posts)
    engagement = sum(p.engagement for p in posts)
    return AnalysisResult(
        summary=(
            f"Tracking **{volume}** recent posts mentioning xMoney with **{engagement:,}** total "
            f"engagements. Conversation skews toward rollout excitement and early-adopter experiences."
        ),
        rollout_insights=(
            "- US-first rollout driving FOMO in other regions\n"
            "- Creators and tipping use cases dominate early buzz\n"
            "- Some friction around KYC and regional availability\n"
            "- Merchant interest is picking up organically"
        ),
        sentiment=sentiment,
        source="heuristic",
    )