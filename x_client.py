"""Fetch recent X posts mentioning xMoney, with demo fallback."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx

from config import settings
from models import Post

SEARCH_QUERY = '("xMoney" OR "x money") -is:retweet lang:en'
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


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


def _api_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return response.text[:200] or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        if "errors" in payload:
            parts = [err.get("detail") or err.get("message") or str(err) for err in payload["errors"]]
            return "; ".join(parts)
        return payload.get("detail") or payload.get("title") or response.text[:200]
    return response.text[:200]


def _parse_live_page(payload: dict) -> tuple[list[Post], str | None]:
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
    return posts, payload.get("meta", {}).get("next_token")


def fetch_live_posts() -> tuple[list[Post], str]:
    """Return posts and a source label ('live' or an error message)."""
    if not settings.x_bearer_token:
        return [], "X_BEARER_TOKEN not set"

    start = datetime.now(timezone.utc) - timedelta(hours=settings.search_hours)
    headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}
    posts: list[Post] = []
    next_token: str | None = None

    try:
        with httpx.Client(timeout=30.0) as client:
            while len(posts) < settings.max_posts:
                page_size = min(max(settings.max_posts - len(posts), 10), 100)
                params: dict[str, str | int] = {
                    "query": SEARCH_QUERY,
                    "max_results": page_size,
                    "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "tweet.fields": "created_at,public_metrics,author_id",
                    "expansions": "author_id",
                    "user.fields": "username",
                    "sort_order": "recency",
                }
                if next_token:
                    params["next_token"] = next_token

                response = client.get(SEARCH_URL, params=params, headers=headers)
                if response.status_code == 429:
                    return posts, "live" if posts else "X API rate limit — try again shortly"
                if response.status_code >= 400:
                    detail = _api_error_message(response)
                    if posts:
                        return (
                            sorted(posts, key=lambda p: p.created_at, reverse=True),
                            f"live (partial — {detail})",
                        )
                    return [], f"X API {response.status_code}: {detail}"

                payload = response.json()
                page_posts, next_token = _parse_live_page(payload)
                posts.extend(page_posts)
                if not next_token or not page_posts:
                    break
    except httpx.HTTPError as exc:
        if posts:
            return sorted(posts, key=lambda p: p.created_at, reverse=True), f"live (partial — {exc})"
        return [], f"X API error: {exc}"

    return sorted(posts, key=lambda p: p.created_at, reverse=True), "live"


def fetch_posts() -> tuple[list[Post], str]:
    """Prefer live X data when a bearer token is configured."""
    if not settings.x_bearer_token:
        return load_sample_posts(), "demo"

    posts, status = fetch_live_posts()
    if status == "live":
        return posts, "live" if posts else "live (0 posts)"
    if status.startswith("live"):
        return posts, status
    return load_sample_posts(), f"demo ({status})"