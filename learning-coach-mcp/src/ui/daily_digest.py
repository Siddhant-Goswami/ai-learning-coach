"""
Daily Digest Interactive UI

Renders the daily digest as an interactive HTML interface for Claude.ai MCP Apps.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def render_daily_digest_ui(digest: Dict[str, Any]) -> str:
    """
    Render daily digest as interactive HTML.

    Args:
        digest: Digest dictionary with insights and metadata

    Returns:
        HTML string for MCP UI resource
    """
    logger.info("Rendering daily digest UI")

    insights = digest.get("insights", [])
    date = digest.get("date", datetime.now().date().isoformat())
    quality_badge = digest.get("quality_badge", "✓")
    ragas_scores = digest.get("ragas_scores", {})
    metadata = digest.get("metadata", {})

    # Build insights HTML
    insights_html = _render_insights(insights)

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learning Digest - {date}</title>
    <style>
        :root {{
            --bg-primary: #0a0a0a;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --text-muted: #666666;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Header */
        .digest-header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .digest-title {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}

        .digest-meta {{
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .quality-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 12px;
            background: var(--bg-secondary);
            font-size: 14px;
            font-weight: 500;
        }}

        .quality-badge.high {{ border: 1px solid var(--success); }}
        .quality-badge.good {{ border: 1px solid var(--accent); }}
        .quality-badge.warning {{ border: 1px solid var(--warning); }}

        .ragas-scores {{
            display: flex;
            gap: 15px;
            font-size: 13px;
        }}

        .ragas-score {{
            display: flex;
            flex-direction: column;
        }}

        .ragas-label {{
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .ragas-value {{
            color: var(--text-primary);
            font-weight: 600;
        }}

        /* Insights */
        .insights-container {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .insight-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.2s ease;
        }}

        .insight-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            border-color: var(--accent);
        }}

        .insight-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 16px;
        }}

        .insight-title {{
            font-size: 20px;
            font-weight: 600;
            color: var(--accent);
            flex: 1;
            line-height: 1.3;
        }}

        .insight-number {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: var(--bg-tertiary);
            border-radius: 50%;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            flex-shrink: 0;
            margin-right: 12px;
        }}

        .relevance-section {{
            background: var(--bg-tertiary);
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            border-left: 3px solid var(--accent);
        }}

        .relevance-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}

        .relevance-text {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .explanation {{
            color: var(--text-primary);
            margin: 16px 0;
            line-height: 1.8;
            font-size: 15px;
        }}

        .explanation.collapsed {{
            max-height: 150px;
            overflow: hidden;
            position: relative;
        }}

        .explanation.collapsed::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: linear-gradient(transparent, var(--bg-secondary));
        }}

        .read-more {{
            color: var(--accent);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            margin-top: 8px;
            display: inline-block;
            text-decoration: none;
        }}

        .read-more:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}

        .takeaway {{
            background: var(--bg-primary);
            border-left: 3px solid var(--success);
            padding: 16px;
            margin: 16px 0;
            border-radius: 4px;
        }}

        .takeaway-label {{
            font-weight: 600;
            color: var(--success);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }}

        .takeaway-text {{
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.6;
        }}

        .source {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-muted);
        }}

        .source-title {{
            color: var(--text-secondary);
            font-weight: 500;
            margin-bottom: 4px;
        }}

        .source-link {{
            color: var(--accent);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: 4px;
        }}

        .source-link:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}

        .feedback-buttons {{
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }}

        .feedback-btn {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .feedback-btn:hover {{
            background: var(--bg-secondary);
            border-color: var(--accent);
            transform: translateY(-1px);
        }}

        .feedback-btn.active {{
            background: var(--success);
            border-color: var(--success);
            color: white;
        }}

        .feedback-btn.active.negative {{
            background: var(--danger);
            border-color: var(--danger);
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }}

        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}

        .empty-state-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-primary);
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            body {{
                padding: 12px;
            }}

            .digest-title {{
                font-size: 24px;
            }}

            .insight-card {{
                padding: 16px;
            }}

            .insight-title {{
                font-size: 18px;
            }}

            .feedback-buttons {{
                flex-direction: column;
            }}

            .feedback-btn {{
                width: 100%;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="digest-header">
        <h1 class="digest-title">📚 Your Learning Digest</h1>
        <div class="digest-meta">
            <span>📅 {date}</span>
            <span class="quality-badge {_get_badge_class(quality_badge)}">
                {quality_badge} Quality Score: {ragas_scores.get('average', 0.75):.2f}
            </span>
            <div class="ragas-scores">
                <div class="ragas-score">
                    <span class="ragas-label">Faithfulness</span>
                    <span class="ragas-value">{ragas_scores.get('faithfulness', 0.75):.2f}</span>
                </div>
                <div class="ragas-score">
                    <span class="ragas-label">Precision</span>
                    <span class="ragas-value">{ragas_scores.get('context_precision', 0.75):.2f}</span>
                </div>
                <div class="ragas-score">
                    <span class="ragas-label">Recall</span>
                    <span class="ragas-value">{ragas_scores.get('context_recall', 0.75):.2f}</span>
                </div>
            </div>
        </div>
    </div>

    <div class="insights-container">
        {insights_html}
    </div>

    <script>
        // Expand/collapse functionality
        document.querySelectorAll('.read-more').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                e.preventDefault();
                const explanation = e.target.previousElementSibling;
                explanation.classList.toggle('collapsed');
                e.target.textContent = explanation.classList.contains('collapsed')
                    ? 'Read more →'
                    : '← Read less';
            }});
        }});

        // Feedback handling
        document.querySelectorAll('.feedback-btn').forEach(btn => {{
            btn.addEventListener('click', async (e) => {{
                const insightId = e.currentTarget.dataset.insightId;
                const feedbackType = e.currentTarget.dataset.feedbackType;

                // Send message to parent (Claude.ai via MCP)
                if (window.parent && window.parent.postMessage) {{
                    window.parent.postMessage({{
                        type: 'mcp-tool-call',
                        tool: 'provide_feedback',
                        params: {{
                            insight_id: insightId,
                            feedback_type: feedbackType
                        }}
                    }}, '*');
                }}

                // Visual feedback
                e.currentTarget.classList.add('active');
                if (feedbackType.includes('not_') || feedbackType === 'incorrect') {{
                    e.currentTarget.classList.add('negative');
                }}

                const icon = feedbackType === 'helpful' ? '✓' : '✗';
                e.currentTarget.textContent = icon + ' ' + e.currentTarget.textContent.replace('👍', '').replace('👎', '').trim();

                // Disable other buttons in same group
                const card = e.currentTarget.closest('.insight-card');
                card.querySelectorAll('.feedback-btn').forEach(otherBtn => {{
                    if (otherBtn !== e.currentTarget) {{
                        otherBtn.disabled = true;
                        otherBtn.style.opacity = '0.5';
                    }}
                }});
            }});
        }});

        // Log render event
        console.log('Daily digest rendered:', {{
            date: '{date}',
            insights: {len(insights)},
            quality: '{quality_badge}'
        }});
    </script>
</body>
</html>"""

    return html


def _render_insights(insights: list) -> str:
    """Render individual insight cards."""
    if not insights:
        return """
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-title">No insights available</div>
            <p>Try adding more content sources or adjusting your learning context.</p>
        </div>
        """

    cards = []
    for i, insight in enumerate(insights, 1):
        # Extract fields with defaults
        title = insight.get("title", "Untitled Insight")
        relevance = insight.get("relevance_reason", "")
        explanation = insight.get("explanation", "")
        takeaway = insight.get("practical_takeaway", "")
        source = insight.get("source", {})
        metadata = insight.get("metadata", {})
        insight_id = insight.get("id", f"insight_{i}")

        # Truncate long explanations
        should_collapse = len(explanation) > 500
        collapsed_class = "collapsed" if should_collapse else ""

        card = f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-number">{i}</span>
                <h2 class="insight-title">{_escape_html(title)}</h2>
            </div>

            {_render_relevance(relevance)}

            <div class="explanation {collapsed_class}">
                {_format_text(explanation)}
            </div>

            {f'<a href="#" class="read-more">Read more →</a>' if should_collapse else ''}

            {_render_takeaway(takeaway)}

            {_render_source(source)}

            <div class="feedback-buttons">
                <button class="feedback-btn" data-insight-id="{insight_id}" data-feedback-type="helpful">
                    👍 Helpful
                </button>
                <button class="feedback-btn" data-insight-id="{insight_id}" data-feedback-type="not_relevant">
                    👎 Not Relevant
                </button>
                <button class="feedback-btn" data-insight-id="{insight_id}" data-feedback-type="too_basic">
                    Too Basic
                </button>
                <button class="feedback-btn" data-insight-id="{insight_id}" data-feedback-type="too_advanced">
                    Too Advanced
                </button>
            </div>
        </div>
        """
        cards.append(card)

    return "\n".join(cards)


def _render_relevance(relevance: str) -> str:
    """Render relevance section."""
    if not relevance:
        return ""

    return f"""
    <div class="relevance-section">
        <div class="relevance-label">Why This Matters</div>
        <div class="relevance-text">{_escape_html(relevance)}</div>
    </div>
    """


def _render_takeaway(takeaway: str) -> str:
    """Render practical takeaway section."""
    if not takeaway:
        return ""

    return f"""
    <div class="takeaway">
        <div class="takeaway-label">💡 Practical Takeaway</div>
        <div class="takeaway-text">{_escape_html(takeaway)}</div>
    </div>
    """


def _render_source(source: dict) -> str:
    """Render source attribution."""
    if not source:
        return ""

    title = source.get("title", "Unknown Source")
    author = source.get("author", "Unknown Author")
    url = source.get("url", "#")
    date = source.get("published_date", "")

    return f"""
    <div class="source">
        <div class="source-title">📖 {_escape_html(title)}</div>
        <div>by {_escape_html(author)}{f' • {date}' if date else ''}</div>
        <a href="{url}" target="_blank" class="source-link">
            Read full article →
        </a>
    </div>
    """


def _get_badge_class(badge: str) -> str:
    """Get CSS class for quality badge."""
    if badge == "✨":
        return "high"
    elif badge == "✓":
        return "good"
    else:
        return "warning"


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _format_text(text: str) -> str:
    """Format text with paragraph breaks."""
    if not text:
        return ""

    # Split into paragraphs and wrap in <p> tags
    paragraphs = text.split("\n\n")
    formatted = []

    for para in paragraphs:
        para = para.strip()
        if para:
            # Escape HTML but preserve intentional formatting
            para = _escape_html(para)
            # Convert single newlines to <br>
            para = para.replace("\n", "<br>")
            formatted.append(f"<p>{para}</p>")

    return "\n".join(formatted)
