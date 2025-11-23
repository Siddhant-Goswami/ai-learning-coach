"""
Home Page - Today's Digest

Displays the daily learning digest with insights.
"""

import streamlit as st
from datetime import datetime
import asyncio
import os


def show():
    """Render the home page."""
    st.title("📚 Today's Learning Digest")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**{datetime.now().strftime('%B %d, %Y')}**")

    with col2:
        if st.button("🔄 Refresh Digest", use_container_width=True):
            with st.spinner("Generating fresh insights..."):
                st.session_state.current_digest = asyncio.run(generate_digest(force_refresh=True))
                st.success("Digest refreshed!")

    with col3:
        week_topics = "Transformers, Attention"
        st.markdown(f"**Focus:** {week_topics}")

    st.markdown("---")

    # Load or generate digest
    if st.session_state.current_digest is None:
        with st.spinner("Loading today's digest..."):
            st.session_state.current_digest = asyncio.run(generate_digest())

    digest = st.session_state.current_digest

    if digest and "error" not in digest:
        # Quality badge
        quality_badge = digest.get("quality_badge", "✓")
        ragas_scores = digest.get("ragas_scores", {})
        avg_score = ragas_scores.get("average", 0.75)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Quality", f"{quality_badge} {avg_score:.2f}")

        with col2:
            st.metric("Faithfulness", f"{ragas_scores.get('faithfulness', 0.75):.2f}")

        with col3:
            st.metric("Precision", f"{ragas_scores.get('context_precision', 0.75):.2f}")

        with col4:
            st.metric("Recall", f"{ragas_scores.get('context_recall', 0.75):.2f}")

        st.markdown("---")

        # Render insights
        insights = digest.get("insights", [])

        if insights:
            for idx, insight in enumerate(insights):
                render_insight_card(insight, idx)
        else:
            st.info("No insights available. Try adding more content sources or adjusting your learning context.")

    else:
        st.error("Failed to load digest. Please check your configuration and try again.")


def render_insight_card(insight: dict, idx: int):
    """Render a single insight card."""
    title = insight.get("title", "Untitled")
    relevance = insight.get("relevance_reason", "")
    explanation = insight.get("explanation", "")
    takeaway = insight.get("practical_takeaway", "")
    source = insight.get("source", {})
    insight_id = insight.get("id", f"insight_{idx}")

    # Create card container
    with st.container():
        st.markdown(f"""
        <div class="insight-card">
            <h3 style="color: #3b82f6;">
                {idx + 1}. {title}
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # Relevance
        if relevance:
            st.info(f"**Why This Matters:** {relevance}")

        # Explanation (in expander)
        with st.expander("📖 Read Explanation", expanded=(idx == 0)):
            st.write(explanation)

        # Practical takeaway
        if takeaway:
            st.success(f"💡 **Takeaway:** {takeaway}")

        # Source
        if source:
            source_title = source.get("title", "Unknown Source")
            source_author = source.get("author", "Unknown Author")
            source_url = source.get("url", "#")
            source_date = source.get("published_date", "")

            st.markdown(f"""
            **Source:** [{source_title}]({source_url}) by {source_author}
            *Published: {source_date}*
            """)

        # Feedback buttons
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👍 Helpful", key=f"helpful_{insight_id}"):
                asyncio.run(submit_feedback(insight_id, "helpful"))
                st.success("✓ Feedback recorded!")

        with col2:
            if st.button("👎 Not Relevant", key=f"not_relevant_{insight_id}"):
                asyncio.run(submit_feedback(insight_id, "not_relevant"))
                st.info("✓ Feedback recorded!")

        with col3:
            if st.button("Too Basic", key=f"too_basic_{insight_id}"):
                asyncio.run(submit_feedback(insight_id, "too_basic"))
                st.info("✓ Feedback recorded!")

        with col4:
            if st.button("Too Advanced", key=f"too_advanced_{insight_id}"):
                asyncio.run(submit_feedback(insight_id, "too_advanced"))
                st.info("✓ Feedback recorded!")

        st.markdown("---")


async def generate_digest(force_refresh: bool = False):
    """Generate or retrieve daily digest."""
    try:
        from src.rag.digest_generator import DigestGenerator

        generator = DigestGenerator(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        digest = await generator.generate(
            user_id=st.session_state.user_id,
            date=datetime.now().date(),
            max_insights=7,
            force_refresh=force_refresh,
        )

        return digest

    except Exception as e:
        st.error(f"Error generating digest: {e}")
        return {"error": str(e)}


async def submit_feedback(insight_id: str, feedback_type: str):
    """Submit user feedback."""
    try:
        from src.tools.feedback_handler import FeedbackHandler

        handler = FeedbackHandler(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
        )

        await handler.record_feedback(
            user_id=st.session_state.user_id,
            insight_id=insight_id,
            feedback_type=feedback_type,
        )

    except Exception as e:
        st.error(f"Error submitting feedback: {e}")
