"""
Home Page - Today's Learning Digest

Displays the daily learning digest with insights from Supabase.
"""

import streamlit as st
from datetime import datetime, date
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)


def show():
    """Render the home page."""
    st.title("📚 Today's Learning Digest")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"**{datetime.now().strftime('%B %d, %Y')}**")

    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.current_digest = None
            st.rerun()

    st.markdown("---")

    # Load digest from database
    digest = load_digest_from_db()

    if digest and digest.get("insights"):
        # Display quality metrics
        ragas_scores = digest.get("ragas_scores", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg = ragas_scores.get('average', 0.0)
            quality_badge = "✓" if avg >= 0.70 else "⚠"
            st.metric("Quality", f"{quality_badge} {avg:.2f}")

        with col2:
            st.metric("Faithfulness", f"{ragas_scores.get('faithfulness', 0.0):.2f}")

        with col3:
            st.metric("Precision", f"{ragas_scores.get('context_precision', 0.0):.2f}")

        with col4:
            st.metric("Recall", f"{ragas_scores.get('context_recall', 0.0):.2f}")

        st.markdown("---")

        # Display insights
        insights = digest.get("insights", [])

        for idx, insight in enumerate(insights):
            render_insight_card(insight, idx)
    else:
        st.info("📝 No digest available for today.")

        if st.button("Generate Today's Digest", type="primary"):
            with st.spinner("Generating insights... This may take 10-15 seconds..."):
                asyncio.run(generate_and_save_digest())
                st.rerun()


def load_digest_from_db():
    """Load today's digest from database."""
    try:
        from supabase import create_client

        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        today = date.today().isoformat()

        result = client.table('generated_digests').select('*').eq(
            'user_id', st.session_state.user_id
        ).eq('digest_date', today).execute()

        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Error loading digest: {e}")
        return None


async def generate_and_save_digest():
    """Generate a new digest."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from digest_api import generate_digest_simple

        await generate_digest_simple(
            user_id=st.session_state.user_id,
            date_obj=date.today(),
            max_insights=7,
            force_refresh=True
        )
    except Exception as e:
        st.error(f"Error: {e}")


def render_insight_card(insight: dict, idx: int):
    """Render a single insight card."""
    title = insight.get("title", "Untitled")
    relevance = insight.get("relevance_reason", "")
    explanation = insight.get("explanation", "")
    takeaway = insight.get("practical_takeaway", "")
    source = insight.get("source", {})
    insight_id = insight.get("id", f"insight_{idx}")

    with st.container():
        st.markdown(f"""
        <div class="insight-card">
            <h3 style="color: #3b82f6;">
                {idx + 1}. {title}
            </h3>
        </div>
        """, unsafe_allow_html=True)

        if relevance:
            st.info(f"**Why This Matters:** {relevance}")

        with st.expander("📖 Read Explanation", expanded=(idx == 0)):
            st.write(explanation)

        if takeaway:
            st.success(f"💡 **Takeaway:** {takeaway}")

        if source:
            title = source.get("title", "Unknown")
            author = source.get("author", "Unknown")
            url = source.get("url", "#")
            st.markdown(f"**Source:** [{title}]({url}) by {author}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("👍 Helpful", key=f"h_{idx}"):
                submit_feedback(insight_id, "helpful")
                st.success("✓ Thanks!")

        with col2:
            if st.button("👎 Not Relevant", key=f"n_{idx}"):
                submit_feedback(insight_id, "not_relevant")
                st.info("✓ Noted!")

        with col3:
            if st.button("📉 Too Basic", key=f"b_{idx}"):
                submit_feedback(insight_id, "too_basic")
                st.info("✓ Noted!")

        with col4:
            if st.button("📈 Too Advanced", key=f"a_{idx}"):
                submit_feedback(insight_id, "too_advanced")
                st.info("✓ Noted!")

        st.markdown("---")


def submit_feedback(insight_id: str, feedback_type: str):
    """Submit feedback."""
    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        client.table("feedback").insert({
            "user_id": st.session_state.user_id,
            "insight_id": insight_id,
            "type": feedback_type,
        }).execute()
    except Exception as e:
        st.error(f"Error: {e}")
