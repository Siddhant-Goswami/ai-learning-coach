"""
Search Page - Past Insights

Search through previously generated digests and insights.
"""

import streamlit as st
from datetime import datetime, timedelta
import asyncio
import os


def show():
    """Render the search page."""
    st.title("🔍 Search Past Insights")

    # Search interface
    query = st.text_input(
        "Search for topics, concepts, or questions...",
        placeholder="e.g., 'transformers attention mechanism', 'explain backpropagation'"
    )

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        # Date range
        date_range_option = st.selectbox(
            "Date Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom"],
        )

        if date_range_option == "Custom":
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
            end_date = st.date_input("End Date", value=datetime.now().date())
        else:
            days_map = {
                "Last 7 days": 7,
                "Last 30 days": 30,
                "Last 90 days": 90,
                "All time": 365 * 10,  # 10 years
            }
            days = days_map[date_range_option]
            start_date = datetime.now().date() - timedelta(days=days)
            end_date = datetime.now().date()

    with col2:
        # Feedback filter
        feedback_filter = st.selectbox(
            "Filter by Feedback",
            ["All insights", "Helpful only", "Not reviewed"],
        )

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if query:
            with st.spinner("Searching past insights..."):
                results = asyncio.run(search_insights(
                    query=query,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    feedback_filter=feedback_filter,
                ))

                # Display results
                st.markdown("---")

                if results:
                    st.success(f"Found {len(results)} insights")

                    for i, result in enumerate(results, 1):
                        render_search_result(result, i)
                else:
                    st.info("No insights found matching your search. Try different keywords or expand the date range.")
        else:
            st.warning("Please enter a search query.")


def render_search_result(result: dict, idx: int):
    """Render a search result."""
    title = result.get("title", "Untitled")
    explanation = result.get("explanation", "")
    digest_date = result.get("digest_date", "Unknown date")
    score = result.get("search_score", 0.0)

    with st.expander(f"{idx}. {title} (Score: {score:.2f})"):
        st.caption(f"📅 From digest on {digest_date}")

        st.markdown("**Explanation:**")
        st.write(explanation[:500] + "..." if len(explanation) > 500 else explanation)

        if result.get("practical_takeaway"):
            st.success(f"💡 **Takeaway:** {result['practical_takeaway']}")

        if result.get("source"):
            source = result["source"]
            st.markdown(f"**Source:** [{source.get('title', 'Unknown')}]({source.get('url', '#')})")


async def search_insights(query: str, start_date: str, end_date: str, feedback_filter: str):
    """Search past insights."""
    try:
        from src.rag.insight_search import InsightSearch

        search = InsightSearch(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Determine min feedback score
        min_feedback = None
        if feedback_filter == "Helpful only":
            min_feedback = 1

        results = await search.search(
            user_id=st.session_state.user_id,
            query=query,
            date_range={"start_date": start_date, "end_date": end_date},
            min_feedback_score=min_feedback,
            limit=20,
        )

        return results

    except Exception as e:
        st.error(f"Search error: {e}")
        return []
