"""
Simple API wrapper for ingestion that can be called from the dashboard.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the src directory to path
src_path = Path(__file__).parent.parent / "learning-coach-mcp" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


async def run_ingestion_for_user(user_id: str) -> Dict[str, Any]:
    """
    Run content ingestion for a specific user's active sources.

    Args:
        user_id: User UUID

    Returns:
        Dictionary with ingestion statistics and status
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")

        if not supabase_url or not supabase_key:
            return {
                "status": "error",
                "error": "Supabase configuration missing",
                "message": "Please set SUPABASE_URL and SUPABASE_KEY in your .env file."
            }

        if not openai_api_key:
            return {
                "status": "error",
                "error": "OpenAI API key missing",
                "message": "OPENAI_API_KEY not configured. Please set it in learning-coach-mcp/.env"
            }

        # Import here to avoid issues if dependencies aren't installed
        from ingestion.orchestrator import IngestionOrchestrator

        # Create orchestrator
        orchestrator = IngestionOrchestrator(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key,
        )

        # Run ingestion for this user's sources
        stats = await orchestrator.ingest_all_active_sources(user_id=user_id)

        return {
            "status": "success",
            "sources_processed": stats.get("sources_processed", 0),
            "sources_failed": stats.get("sources_failed", 0),
            "total_articles": stats.get("total_articles", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "message": f"Successfully processed {stats.get('sources_processed', 0)} sources, "
                      f"fetched {stats.get('total_articles', 0)} articles, "
                      f"created {stats.get('total_chunks', 0)} chunks"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "message": f"Error running ingestion: {e}"
        }
