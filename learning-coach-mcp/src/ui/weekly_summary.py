"""
Weekly Summary UI

Renders weekly learning summary with analytics and progress tracking.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def render_weekly_summary_ui(summary: Dict[str, Any]) -> str:
    """
    Render weekly summary as interactive HTML.

    Args:
        summary: Weekly summary data with insights and analytics

    Returns:
        HTML string for MCP UI resource
    """
    logger.info("Rendering weekly summary UI")

    week_number = summary.get("week_number", 1)
    insights = summary.get("insights", [])
    learning_context = summary.get("learning_context", {})
    analytics = summary.get("analytics", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Summary - Week {week_number}</title>
    <style>
        :root {{
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --text-muted: #666666;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --border: #333333;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}

        .header h1 {{
            font-size: 32px;
            margin-bottom: 8px;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            font-size: 16px;
        }}

        .progress-bar {{
            background: var(--bg-secondary);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 16px;
        }}

        .progress-fill {{
            background: linear-gradient(90deg, var(--accent), var(--success));
            height: 100%;
            transition: width 0.3s ease;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 8px;
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .insights-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .insight-item {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }}

        .insight-title {{
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 8px;
        }}

        .insight-preview {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .topics-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .topic-tag {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            color: var(--text-primary);
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Week {week_number} Summary</h1>
        <p class="subtitle">{', '.join(learning_context.get('current_topics', []))}</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(week_number / 24) * 100}%"></div>
        </div>
        <p style="margin-top: 8px; color: var(--text-muted); font-size: 14px;">
            Week {week_number} of 24 • {(week_number / 24) * 100:.1f}% Complete
        </p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{analytics.get('total_insights', 0)}</div>
            <div class="stat-label">Insights This Week</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{analytics.get('helpful_rate', 85)}%</div>
            <div class="stat-label">Helpful Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{analytics.get('sources_used', 5)}</div>
            <div class="stat-label">Sources</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{analytics.get('topics_covered', 3)}</div>
            <div class="stat-label">Topics Covered</div>
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">🎯 Topics Covered</h2>
        <div class="topics-list">
            {_render_topics(learning_context.get('current_topics', []))}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">💡 Top Insights</h2>
        <div class="insights-list">
            {_render_top_insights(insights[:10])}
        </div>
    </div>

    <div class="section">
        <h2 class="section-title">🎓 Next Steps</h2>
        <div style="background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 20px;">
            <p style="color: var(--text-secondary); margin-bottom: 12px;">
                Based on your progress this week, here's what to focus on next:
            </p>
            <ul style="color: var(--text-primary); padding-left: 20px;">
                <li style="margin-bottom: 8px;">Continue practicing with the concepts you found helpful</li>
                <li style="margin-bottom: 8px;">Review topics that received "too advanced" feedback</li>
                <li style="margin-bottom: 8px;">Explore related resources from your highest-rated sources</li>
            </ul>
        </div>
    </div>
</body>
</html>"""

    return html


def _render_topics(topics: list) -> str:
    """Render topic tags."""
    if not topics:
        return '<div class="topic-tag">No topics yet</div>'

    tags = []
    for topic in topics:
        tags.append(f'<div class="topic-tag">{topic}</div>')

    return "\n".join(tags)


def _render_top_insights(insights: list) -> str:
    """Render top insights list."""
    if not insights:
        return '<div style="color: var(--text-muted); text-align: center; padding: 20px;">No insights this week</div>'

    items = []
    for i, insight in enumerate(insights, 1):
        title = insight.get("title", "Untitled")
        explanation = insight.get("explanation", "")
        preview = explanation[:150] + "..." if len(explanation) > 150 else explanation

        items.append(f"""
        <div class="insight-item">
            <div class="insight-title">{i}. {title}</div>
            <div class="insight-preview">{preview}</div>
        </div>
        """)

    return "\n".join(items)
