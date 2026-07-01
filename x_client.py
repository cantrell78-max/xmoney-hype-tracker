"""Fetch recent X posts mentioning xMoney, with demo fallback."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx

from config import settings
from models import Post

SEARCH_QUERY = '("xMoney" OR "x money") -is:retweet lang:en'


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _post_from_dict(raw: dict) -> Post:
    return Post(
        id=str(raw["id"]),
        text=raw["text"],
        author=raw.get("author", "unknown"),
        created_at=_parse_timestamp(raw["created_at"]),
        likes=int(raw.get("likes", 0)),
        retweets=int(raw.get("retweets", 0)),
        replies=int(raw.get("replies", 0)),
        url=raw.get("url", ""),
    )


def load_sample_posts() -> list[Post]:
    data = json.loads(settings.sample_data_path.read_text())
    posts = [_post_from_dict(item) for item in data]
    return sorted(posts, key=lambda p: p.created_at, reverse=True)


def fetch_live_posts() -> tuple[list[Post], str]:
    """Return posts and a source label ('live' or error message)."""
    if not settings.x_bearer_token:
        return [], "X_BEARER_TOKEN not set"

    start = datetime.now(timezone.utc) - timedelta(hours=settings.search_hours)
    params = {
        "query": SEARCH_QUERY,
        "max_results": min(settings.max_posts, 100),
        "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }
    headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return [], f"X API error: {exc}"

    users = {
        user["id"]: user.get("username", "unknown")
        for user in payload.get("includes", {}).get("users", [])
    }
    posts: list[Post] = []
    for tweet in payload.get("data", []):
        metrics = tweet.get("public_metrics", {})
        author_id = tweet.get("author_id", "")
        username = users.get(author_id, "unknown")
        tweet_id = tweet["id"]
        posts.append(
            Post(
                id=tweet_id,
                text=tweet["text"],
                author=username,
                created_at=_parse_timestamp(tweet["created_at"]),
                likes=metrics.get("like_count", 0),
                retweets=metrics.get("retweet_count", 0),
                replies=metrics.get("reply_count", 0),
                url=f"https://x.com/{username}/status/{tweet_id}",
            )
        )

    return sorted(posts, key=lambda p: p.created_at, reverse=True), "live"


def fetch_posts() -> tuple[list[Post], str]:
    """Prefer live X data; fall back to bundled demo posts."""
    posts, status = fetch_live_posts()
    if posts:
        return posts, "live"
    sample = load_sample_posts()
    if status == "X_BEARER_TOKEN not set":
        return sample, "demo"
    return sample, f"demo ({status})"