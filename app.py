"""xMoney Hype Tracker — live dashboard for X rollout buzz."""

from __future__ import annotations

import os

import gradio as gr

from analyzer import analyze_posts
from config import settings
from hype import (
    compute_hype_score,
    format_posts_table,
    mentions_over_time_chart,
    score_color,
    sentiment_chart,
)
from x_client import fetch_posts

CUSTOM_CSS = """
.gradio-container { max-width: 1200px !important; margin: auto; }
.hype-score {
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
    text-align: center;
}
.hype-label { text-align: center; color: #64748b; font-size: 0.9rem; }
"""


def _hype_score_html(score: int) -> str:
    color = score_color(score)
    return f"""
    <div class="hype-score" style="color: {color}">{score}</div>
    <div class="hype-label">Hype Score (0–100)</div>
    """


def _status_line(source: str) -> str:
    api = "✓ Grok connected" if settings.xai_api_key else "⚠ Set XAI_API_KEY for AI summaries"
    if source == "live" or source.startswith("live "):
        x_api = f"✓ X API · {source}"
    elif source == "demo":
        x_api = "📦 Demo data (set X_BEARER_TOKEN for live posts)"
    else:
        x_api = f"📦 Demo data ({source})"
    return f"**xMoney Hype Tracker** · {x_api} · {api}"


def refresh_dashboard() -> tuple:
    posts, source = fetch_posts()
    analysis = analyze_posts(posts)
    score = compute_hype_score(posts, analysis.sentiment)

    mentions_fig = mentions_over_time_chart(posts)
    sentiment_fig = sentiment_chart(analysis.sentiment)
    table = format_posts_table(posts, analysis.post_sentiments)

    return (
        _status_line(source),
        _hype_score_html(score),
        analysis.summary or "_No summary available._",
        analysis.rollout_insights or "_No rollout insights yet._",
        mentions_fig,
        sentiment_fig,
        table,
        f"Last refresh: {posts[0].created_at.strftime('%Y-%m-%d %H:%M UTC') if posts else '—'} · "
        f"{len(posts)} posts · analysis via **{analysis.source}**",
    )


def build_ui() -> tuple[gr.Blocks, gr.themes.Theme]:
    theme = gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="slate",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    )

    with gr.Blocks(title="xMoney Hype Tracker") as demo:
        gr.Markdown(
            """
            # xMoney Hype Tracker
            ### Live dashboard for xMoney rollout buzz on X · powered by Grok
            """
        )

        status = gr.Markdown(_status_line("demo"))
        meta = gr.Markdown("Click **Refresh** to load posts and run analysis.")

        with gr.Row():
            with gr.Column(scale=1):
                hype_score = gr.HTML(_hype_score_html(0))
            with gr.Column(scale=3):
                summary = gr.Markdown("_AI summary will appear here._")
                insights = gr.Markdown("_Rollout insights will appear here._")

        with gr.Row():
            mentions_chart = gr.Plot(label="Mentions over time")
            sentiment_pie = gr.Plot(label="Sentiment")

        gr.Markdown("### Trending posts")
        posts_table = gr.Dataframe(
            headers=["Author", "Post", "Engagement", "Sentiment", "Time", "Link"],
            datatype=["str", "str", "number", "str", "str", "markdown"],
            interactive=False,
            wrap=True,
        )

        refresh_btn = gr.Button("Refresh", variant="primary")

        outputs = [
            status,
            hype_score,
            summary,
            insights,
            mentions_chart,
            sentiment_pie,
            posts_table,
            meta,
        ]
        refresh_btn.click(refresh_dashboard, outputs=outputs)
        demo.load(refresh_dashboard, outputs=outputs)

    return demo, theme


def main() -> None:
    demo, theme = build_ui()
    demo.queue(default_concurrency_limit=2)
    demo.launch(
        theme=theme,
        css=CUSTOM_CSS,
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.environ.get("PORT", "7860")),
    )


if __name__ == "__main__":
    main()