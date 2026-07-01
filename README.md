---
title: xMoney Hype Tracker
emoji: 💸
colorFrom: purple
colorTo: gray
sdk: gradio
sdk_version: 5.29.0
app_file: app.py
pinned: false
license: mit
---

# xMoney Hype Tracker

Live Gradio dashboard that tracks xMoney rollout hype on X — sentiment, trending posts, and a 0–100 Hype Score powered by Grok.

Built live on [airomatic.ai](https://airomatic.ai/live/) with Grok Build.

## Features

- Recent X posts mentioning "xMoney" or "x money" (X API v2 recent search)
- Grok API analysis: summary + rollout insights
- Sentiment breakdown (positive, negative, hype, neutral)
- Plotly charts: mentions over time, sentiment pie
- Hype Score (0–100) from volume, engagement, and sentiment

## Deploy to Hugging Face (auto-sync from GitHub)

This repo syncs to the Space on every push to `main` via GitHub Actions.

### 1. GitHub secret (one-time)

In **GitHub → cantrell78-max/xmoney-hype-tracker → Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `HF_TOKEN` | Hugging Face [write token](https://huggingface.co/settings/tokens) scoped to your Space |

### 2. Hugging Face Space

The workflow syncs to **[airomatic/xmoney](https://huggingface.co/spaces/airomatic/xmoney)** on Hugging Face.

After adding `HF_TOKEN`, push to `main` or run the **Sync to Hugging Face Hub** workflow manually under **Actions**.

## Hugging Face Space secrets

In your Space **Settings → Repository secrets**, add:

| Secret | Description |
|--------|-------------|
| `XAI_API_KEY` | xAI/Grok API key ([console.x.ai](https://console.x.ai/)) |
| `X_BEARER_TOKEN` | X API v2 **Bearer Token** (App-only auth) |

Optional secrets: `XAI_MODEL`, `SEARCH_HOURS` (default 48), `MAX_POSTS` (default 50).

Without `X_BEARER_TOKEN`, the Space uses bundled demo posts in `data/sample_posts.json`.

### X API setup

1. Create a project at [developer.x.com](https://developer.x.com/)
2. Enable **Read** access for the app
3. Generate a **Bearer Token** (OAuth 2.0 App-only)
4. Add it as the `X_BEARER_TOKEN` Space secret

The app queries: `("xMoney" OR "x money") -is:retweet lang:en` over the last 48 hours.

## Local development

```bash
cd ~/projects/xmoney-hype-tracker
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
python scripts/sync_grok_key.py   # optional — copies Grok Build token
# Add X_BEARER_TOKEN=... to .env for live posts
python app.py
```

Open **http://127.0.0.1:7860**

## Stack

Python · Gradio · Grok API (OpenAI-compatible) · Plotly · pandas · httpx