"""
AI Learning Coach MCP Server

Main server implementation using FastMCP.
Provides tools and UI resources for personalized learning.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("learning-coach")

# Configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")


# ============================================================================
# MCP TOOLS
# ============================================================================


@mcp.tool()
async def generate_daily_digest(
    date: str = "today",
    max_insights: int = 7,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Generate personalized learning digest for specified date.

    Args:
        date: ISO date string or "today" (default: "today")
        max_insights: Number of insights to generate (3-10, default: 7)
        force_refresh: Skip cache and regenerate (default: False)

    Returns:
        JSON with insights array, sources, and RAGAS scores

    Example:
        >>> digest = await generate_daily_digest(date="2024-11-23", max_insights=5)
        >>> print(digest['quality_badge'])
        ✨
    """
    logger.info(f"Generating daily digest: date={date}, max_insights={max_insights}")

    try:
        # Import here to avoid circular dependencies
        from .rag.digest_generator import DigestGenerator

        generator = DigestGenerator(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY,
            anthropic_api_key=ANTHROPIC_API_KEY,
        )

        # Parse date
        if date == "today":
            digest_date = datetime.now().date()
        else:
            digest_date = datetime.fromisoformat(date).date()

        # Generate digest
        digest = await generator.generate(
            user_id=DEFAULT_USER_ID,
            date=digest_date,
            max_insights=max_insights,
            force_refresh=force_refresh,
        )

        logger.info(
            f"Digest generated successfully: {len(digest['insights'])} insights, "
            f"quality={digest['ragas_scores']['average']:.2f}"
        )

        return digest

    except Exception as e:
        logger.error(f"Error generating digest: {e}", exc_info=True)
        return {
            "error": str(e),
            "message": "Failed to generate digest. Please check logs for details.",
        }


@mcp.tool()
async def manage_sources(
    action: str,
    source_type: Optional[str] = None,
    source_identifier: Optional[str] = None,
    priority: int = 3,
) -> Dict[str, Any]:
    """
    Manage content sources (add, remove, update, list).

    Args:
        action: "add", "remove", "update", or "list"
        source_type: "rss", "twitter", "reddit", "custom_url", "youtube"
        source_identifier: URL, handle, or subreddit name
        priority: 1-5 (default: 3)

    Returns:
        Success message and updated source information

    Examples:
        >>> await manage_sources(action="add", source_type="rss",
        ...                      source_identifier="https://lilianweng.github.io/feed.xml", priority=5)
        >>> await manage_sources(action="list")
    """
    logger.info(f"Managing sources: action={action}, type={source_type}")

    try:
        from .tools.source_manager import SourceManager

        manager = SourceManager(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

        if action == "add":
            if not source_type or not source_identifier:
                return {"error": "source_type and source_identifier required for 'add' action"}

            result = await manager.add_source(
                user_id=DEFAULT_USER_ID,
                source_type=source_type,
                identifier=source_identifier,
                priority=priority,
            )
            return result

        elif action == "remove":
            if not source_identifier:
                return {"error": "source_identifier required for 'remove' action"}

            result = await manager.remove_source(
                user_id=DEFAULT_USER_ID, identifier=source_identifier
            )
            return result

        elif action == "update":
            if not source_identifier:
                return {"error": "source_identifier required for 'update' action"}

            result = await manager.update_source(
                user_id=DEFAULT_USER_ID, identifier=source_identifier, priority=priority
            )
            return result

        elif action == "list":
            result = await manager.list_sources(user_id=DEFAULT_USER_ID)
            return result

        else:
            return {"error": f"Invalid action: {action}. Use 'add', 'remove', 'update', or 'list'"}

    except Exception as e:
        logger.error(f"Error managing sources: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
async def provide_feedback(
    insight_id: str,
    feedback_type: str,
    reason: Optional[str] = None,
) -> str:
    """
    Capture user feedback on an insight.

    Args:
        insight_id: UUID of the insight
        feedback_type: "helpful", "not_relevant", "incorrect", "too_basic", "too_advanced"
        reason: Optional free text explanation (max 500 chars)

    Returns:
        Confirmation message

    Example:
        >>> await provide_feedback(
        ...     insight_id="550e8400-e29b-41d4-a716-446655440000",
        ...     feedback_type="helpful",
        ...     reason="Great explanation of transformers!"
        ... )
        '✓ Feedback recorded. Your preferences will influence future digests.'
    """
    logger.info(f"Recording feedback: insight_id={insight_id}, type={feedback_type}")

    try:
        from .tools.feedback_handler import FeedbackHandler

        handler = FeedbackHandler(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

        await handler.record_feedback(
            user_id=DEFAULT_USER_ID,
            insight_id=insight_id,
            feedback_type=feedback_type,
            reason=reason,
        )

        # Update source priorities based on feedback
        await handler.update_source_priorities(insight_id=insight_id, feedback_type=feedback_type)

        logger.info("Feedback recorded successfully")
        return "✓ Feedback recorded. Your preferences will influence future digests."

    except Exception as e:
        logger.error(f"Error recording feedback: {e}", exc_info=True)
        return f"Error recording feedback: {str(e)}"


@mcp.tool()
async def sync_bootcamp_progress() -> str:
    """
    Manually sync learning context from 100xEngineers platform.

    Returns:
        Current progress summary

    Example:
        >>> await sync_bootcamp_progress()
        '✓ Synced: Week 7, Topics: Attention Mechanisms, Transformers, Multi-Head Attention'
    """
    logger.info("Syncing bootcamp progress")

    try:
        from .integrations.bootcamp import BootcampIntegration

        integration = BootcampIntegration(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

        progress = await integration.sync_progress(user_id=DEFAULT_USER_ID)

        return (
            f"✓ Synced: Week {progress['current_week']}, "
            f"Topics: {', '.join(progress['current_topics'])}"
        )

    except Exception as e:
        logger.error(f"Error syncing bootcamp progress: {e}", exc_info=True)
        return f"Error syncing progress: {str(e)}"


@mcp.tool()
async def search_past_insights(
    query: str,
    date_range: Optional[Dict[str, str]] = None,
    min_feedback_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Search through previously delivered digests.

    Args:
        query: Semantic search query
        date_range: {"start_date": "ISO date", "end_date": "ISO date"} (optional)
        min_feedback_score: Filter by helpful feedback only (optional)

    Returns:
        Array of matching insights with context

    Example:
        >>> results = await search_past_insights(
        ...     query="transformers attention mechanism",
        ...     date_range={"start_date": "2024-11-01", "end_date": "2024-11-23"}
        ... )
    """
    logger.info(f"Searching past insights: query='{query}'")

    try:
        from .rag.insight_search import InsightSearch

        search = InsightSearch(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY,
        )

        results = await search.search(
            user_id=DEFAULT_USER_ID,
            query=query,
            date_range=date_range,
            min_feedback_score=min_feedback_score,
        )

        logger.info(f"Found {len(results)} matching insights")
        return {"results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Error searching insights: {e}", exc_info=True)
        return {"error": str(e), "results": [], "count": 0}


# ============================================================================
# MCP UI RESOURCES
# ============================================================================


@mcp.resource("ui://learning-coach/daily-digest")
async def daily_digest_ui() -> str:
    """
    Interactive daily digest UI (HTML).
    Rendered in Claude.ai via MCP Apps.
    """
    from .ui.daily_digest import render_daily_digest_ui

    # Get today's digest
    digest = await generate_daily_digest(date="today")

    return render_daily_digest_ui(digest)


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================


def main():
    """Run the MCP server."""
    logger.info("Starting AI Learning Coach MCP Server...")

    # Validate required configuration
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please set these in your Claude Desktop config or .env file.")
        return
    
    # Check optional Anthropic key
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set - Anthropic features will be unavailable")
        logger.warning("The system will use OpenAI for synthesis instead.")
    else:
        logger.info("Anthropic API key configured")

    logger.info("Configuration validated")
    logger.info("Server name: learning-coach")
    logger.info(f"Default user ID: {DEFAULT_USER_ID}")

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
