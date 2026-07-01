from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Post:
    id: str
    text: str
    author: str
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str = ""

    @property
    def engagement(self) -> int:
        return self.likes + self.retweets + self.replies


@dataclass
class SentimentBreakdown:
    positive: int = 0
    negative: int = 0
    hype: int = 0
    neutral: int = 0

    @property
    def total(self) -> int:
        return self.positive + self.negative + self.hype + self.neutral


@dataclass
class AnalysisResult:
    summary: str = ""
    rollout_insights: str = ""
    sentiment: SentimentBreakdown = field(default_factory=SentimentBreakdown)
    post_sentiments: dict[str, str] = field(default_factory=dict)
    source: str = "demo"