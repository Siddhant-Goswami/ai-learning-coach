"""
Insight Search

Search through previously generated digests and insights.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI
from supabase import Client

from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class InsightSearch:
    """Search through past insights."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
    ):
        """
        Initialize insight search.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key
            embedding_model: OpenAI embedding model
            embedding_dimensions: Embedding dimensions
        """
        self.db = get_supabase_client(supabase_url, supabase_key)
        self.embeddings_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions

    async def search(
        self,
        user_id: str,
        query: str,
        date_range: Optional[Dict[str, str]] = None,
        min_feedback_score: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search past insights semantically.

        Args:
            user_id: User ID
            query: Search query
            date_range: Optional date range filter (start_date, end_date)
            min_feedback_score: Filter insights with positive feedback only
            limit: Maximum results to return

        Returns:
            List of matching insights
        """
        logger.info(f"Searching past insights: '{query}'")

        try:
            # Get all digests for user
            digests_query = self.db.table("generated_digests").select("*").eq("user_id", user_id)

            # Apply date range filter
            if date_range:
                if "start_date" in date_range:
                    digests_query = digests_query.gte("digest_date", date_range["start_date"])
                if "end_date" in date_range:
                    digests_query = digests_query.lte("digest_date", date_range["end_date"])

            digests_result = digests_query.execute()
            digests = digests_result.data if digests_result.data else []

            if not digests:
                logger.info("No digests found for user")
                return []

            # Extract all insights from digests
            all_insights = []
            for digest in digests:
                insights = digest.get("insights", [])
                for insight in insights:
                    # Add digest metadata
                    insight["digest_date"] = digest["digest_date"]
                    insight["digest_id"] = digest["id"]
                    all_insights.append(insight)

            if not all_insights:
                return []

            # Generate query embedding
            query_embedding = await self._generate_query_embedding(query)

            # Score insights by semantic similarity
            for insight in all_insights:
                # Create searchable text from insight
                searchable_text = (
                    f"{insight.get('title', '')} "
                    f"{insight.get('explanation', '')} "
                    f"{insight.get('practical_takeaway', '')}"
                )

                # Generate embedding for insight
                insight_embedding = await self._generate_query_embedding(searchable_text)

                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, insight_embedding)
                insight["search_score"] = similarity

            # Filter by feedback if requested
            if min_feedback_score is not None:
                # Get feedback for insights
                filtered_insights = []
                for insight in all_insights:
                    feedback_result = (
                        self.db.table("feedback")
                        .select("type")
                        .eq("insight_id", insight.get("id", ""))
                        .execute()
                    )

                    feedbacks = feedback_result.data if feedback_result.data else []

                    # Count helpful feedback
                    helpful_count = sum(1 for f in feedbacks if f["type"] == "helpful")

                    if helpful_count >= min_feedback_score:
                        filtered_insights.append(insight)

                all_insights = filtered_insights

            # Sort by search score
            all_insights.sort(key=lambda x: x["search_score"], reverse=True)

            # Return top results
            results = all_insights[:limit]

            logger.info(f"Found {len(results)} matching insights")
            return results

        except Exception as e:
            logger.error(f"Error searching insights: {e}", exc_info=True)
            return []

    async def _generate_query_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        response = await self.embeddings_client.embeddings.create(
            model=self.embedding_model,
            input=text,
            dimensions=self.embedding_dimensions,
        )
        return response.data[0].embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


async def test_insight_search(
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    user_id: str,
) -> None:
    """
    Test insight search.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        openai_api_key: OpenAI key
        user_id: User ID
    """
    search = InsightSearch(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        openai_api_key=openai_api_key,
    )

    print("\n" + "=" * 60)
    print("INSIGHT SEARCH TEST")
    print("=" * 60)

    query = "transformers attention mechanism"
    print(f"\nSearching for: '{query}'")

    results = await search.search(
        user_id=user_id,
        query=query,
        limit=5,
    )

    print(f"\nFound {len(results)} results:\n")

    for i, insight in enumerate(results, 1):
        print(f"{i}. {insight.get('title', 'Untitled')}")
        print(f"   Date: {insight.get('digest_date', 'N/A')}")
        print(f"   Score: {insight.get('search_score', 0):.3f}")
        print(f"   Preview: {insight.get('explanation', '')[:100]}...")
        print()


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_insight_search(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
