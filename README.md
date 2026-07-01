# xMoney Hype Tracker

Live Gradio dashboard that tracks xMoney rollout hype on X — sentiment, trending posts, and a 0–100 Hype Score powered by Grok.

Built live on [airomatic.ai](https://airomatic.ai/live/) with Grok Build.

## Features

- Recent X posts mentioning "xMoney" or "x money"
- Grok API analysis: summary + rollout insights
- Sentiment breakdown (positive, negative, hype, neutral)
- Plotly charts: mentions over time, sentiment pie
- Hype Score (0–100) from volume, engagement, and sentiment

## Quick start

```bash
cd ~/projects/xmoney-hype-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/sync_grok_key.py   # optional — copies Grok Build token
python app.py
```

Open **http://127.0.0.1:7860**

## Configuration

| Variable | Description |
|----------|-------------|
| `XAI_API_KEY` | xAI/Grok API key (required for AI summaries) |
| `X_BEARER_TOKEN` | X API v2 bearer token (optional — uses demo data if unset) |
| `SEARCH_HOURS` | How far back to search (default 48) |
| `MAX_POSTS` | Max posts to analyze (default 50) |

Without `X_BEARER_TOKEN`, the app uses bundled demo posts in `data/sample_posts.json` — ideal for livestreams and local dev.

## Stack

Python · Gradio · Grok API (OpenAI-compatible) · Plotly · pandas · httpx