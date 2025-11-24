"""
Digest Generator

Orchestrates the full RAG pipeline to generate personalized daily digests.
Combines query building, retrieval, and synthesis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from supabase import Client

from .query_builder import QueryBuilder
from .retriever import VectorRetriever
from .synthesizer import EducationalSynthesizer
from .evaluator import RAGASEvaluator, QualityGate
from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates personalized daily learning digests."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        anthropic_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        claude_model: str = "claude-sonnet-4-5-20250929",
        ragas_min_score: float = 0.70,
        ragas_max_retries: int = 2,
    ):
        """
        Initialize digest generator.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key (optional, falls back to OpenAI if not provided)
            embedding_model: OpenAI embedding model
            claude_model: Claude model for synthesis
            ragas_min_score: Minimum RAGAS score for quality gate
            ragas_max_retries: Maximum retry attempts for quality gate
        """
        self.db = get_supabase_client(supabase_url, supabase_key)

        self.query_builder = QueryBuilder(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
        )

        self.retriever = VectorRetriever(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key,
            embedding_model=embedding_model,
        )

        # Only create Anthropic synthesizer if API key is provided
        if anthropic_api_key:
            self.synthesizer = EducationalSynthesizer(
                api_key=anthropic_api_key,
                model=claude_model,
            )
            self.use_anthropic = True
        else:
            logger.warning(
                "ANTHROPIC_API_KEY not provided. "
                "Digest generation will require Anthropic API key. "
                "Please add ANTHROPIC_API_KEY to your Claude Desktop config or .env file."
            )
            # Create a placeholder - will fail gracefully when used
            self.synthesizer = None
            self.use_anthropic = False

        # RAGAS evaluation and quality gate
        self.evaluator = RAGASEvaluator(min_score=ragas_min_score)
        self.quality_gate = QualityGate(
            evaluator=self.evaluator,
            max_retries=ragas_max_retries,
        )

    async def generate(
        self,
        user_id: str,
        date: datetime.date,
        max_insights: int = 7,
        force_refresh: bool = False,
        explicit_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate daily digest for a user.

        Args:
            user_id: User ID
            date: Date for the digest
            max_insights: Maximum number of insights to generate (default: 7)
            force_refresh: Skip cache and regenerate (default: False)
            explicit_query: Optional explicit query from user

        Returns:
            Digest dictionary with insights and metadata
        """
        logger.info(f"Generating digest for user {user_id}, date {date}")

        # 1. Check cache (if not force_refresh)
        if not force_refresh:
            cached_digest = await self._get_cached_digest(user_id, date)
            if cached_digest:
                logger.info("Returning cached digest")
                return cached_digest

        # 2. Build query from learning context
        query_result = await self.query_builder.build_query_from_context(
            user_id=user_id,
            explicit_query=explicit_query,
        )

        query_text = query_result["query_text"]
        learning_context = query_result["learning_context"]

        if not learning_context:
            logger.warning(f"No learning context for user {user_id}, using defaults")
            learning_context = {
                "current_week": 1,
                "current_topics": ["AI", "Machine Learning"],
                "difficulty_level": "intermediate",
                "learning_goals": "Learn AI fundamentals",
            }

        # 3. Retrieve relevant chunks
        chunks = await self.retriever.retrieve(
            query=query_text,
            user_id=user_id,
            top_k=15,
            similarity_threshold=0.70,
        )

        if not chunks:
            logger.warning("No chunks retrieved, returning empty digest")
            return self._create_empty_digest(date, "No relevant content found")

        # 4. Synthesize insights
        if not self.synthesizer:
            logger.error("ANTHROPIC_API_KEY is required for digest generation")
            return self._create_empty_digest(
                date, 
                "Anthropic API key not configured. Please add ANTHROPIC_API_KEY to your Claude Desktop config."
            )
        
        synthesis_result = await self.synthesizer.synthesize_insights(
            retrieved_chunks=chunks,
            learning_context=learning_context,
            query=query_text,
            num_insights=min(max_insights, 10),  # Cap at 10
        )

        insights = synthesis_result["insights"]

        if not insights:
            logger.warning("No insights generated, returning empty digest")
            return self._create_empty_digest(date, "Failed to generate insights")

        # 5. Apply RAGAS evaluation and quality gate
        final_insights, ragas_scores, passed_gate = await self.quality_gate.apply_gate(
            query=query_text,
            insights=insights,
            retrieved_chunks=chunks,
            synthesizer=self.synthesizer,
            learning_context=learning_context,
        )

        # Update quality badge based on scores
        quality_badge = self._determine_quality_badge(ragas_scores)

        # 6. Create digest object
        digest = {
            "date": date.isoformat(),
            "insights": final_insights,
            "ragas_scores": ragas_scores,
            "quality_badge": quality_badge,
            "quality_passed": passed_gate,
            "generated_at": datetime.now().isoformat(),
            "metadata": {
                "query": query_text,
                "learning_context": learning_context,
                "num_chunks_used": len(chunks),
                "num_insights": len(insights),
                "sources": list(set(c["source_id"] for c in chunks)),
                "avg_similarity": sum(c["similarity"] for c in chunks) / len(chunks),
            },
        }

        # 6. Store digest in database (with cache)
        await self._store_digest(user_id, digest)

        logger.info(f"Digest generated successfully: {len(insights)} insights")
        return digest

    async def _get_cached_digest(
        self,
        user_id: str,
        date: datetime.date,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached digest if available and not expired.

        Args:
            user_id: User ID
            date: Digest date

        Returns:
            Cached digest or None
        """
        try:
            result = (
                self.db.table("generated_digests")
                .select("*")
                .eq("user_id", user_id)
                .eq("digest_date", date.isoformat())
                .single()
                .execute()
            )

            if not result.data:
                return None

            # Check if cache expired (6 hours by default)
            cache_expires = result.data.get("cache_expires_at")
            if cache_expires:
                expires_dt = datetime.fromisoformat(cache_expires)
                if datetime.now() > expires_dt:
                    logger.debug("Cached digest expired")
                    return None

            # Reconstruct digest from database
            return {
                "date": result.data["digest_date"],
                "insights": result.data["insights"],
                "ragas_scores": result.data.get("ragas_scores", {}),
                "quality_badge": self._determine_quality_badge(
                    result.data.get("ragas_scores", {})
                ),
                "generated_at": result.data["generated_at"],
                "metadata": result.data.get("metadata", {}),
                "cached": True,
            }

        except Exception as e:
            logger.debug(f"No cached digest found: {e}")
            return None

    async def _store_digest(self, user_id: str, digest: Dict[str, Any]) -> None:
        """
        Store digest in database with cache expiration.

        Args:
            user_id: User ID
            digest: Digest dictionary
        """
        try:
            # Calculate cache expiration (6 hours from now)
            cache_expires_at = datetime.now() + timedelta(hours=6)

            # Upsert digest
            self.db.table("generated_digests").upsert(
                {
                    "user_id": user_id,
                    "digest_date": digest["date"],
                    "insights": digest["insights"],
                    "ragas_scores": digest.get("ragas_scores", {}),
                    "generated_at": digest["generated_at"],
                    "cache_expires_at": cache_expires_at.isoformat(),
                    "metadata": digest.get("metadata", {}),
                }
            ).execute()

            logger.debug("Digest stored in database")

        except Exception as e:
            logger.error(f"Error storing digest: {e}")
            # Non-critical error, continue

    def _create_empty_digest(self, date: datetime.date, reason: str) -> Dict[str, Any]:
        """
        Create an empty digest with error message.

        Args:
            date: Digest date
            reason: Reason for empty digest

        Returns:
            Empty digest dictionary
        """
        return {
            "date": date.isoformat(),
            "insights": [],
            "ragas_scores": {},
            "quality_badge": "⚠️",
            "generated_at": datetime.now().isoformat(),
            "metadata": {
                "error": reason,
                "num_insights": 0,
            },
        }

    def _determine_quality_badge(self, ragas_scores: Dict[str, Any]) -> str:
        """
        Determine quality badge based on RAGAS scores.

        Args:
            ragas_scores: RAGAS scores dictionary

        Returns:
            Quality badge emoji
        """
        avg_score = ragas_scores.get("average", 0)

        if avg_score >= 0.85:
            return "✨"  # High quality
        elif avg_score >= 0.70:
            return "✓"  # Good quality
        else:
            return "⚠️"  # Below threshold


async def test_digest_generation(
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    anthropic_api_key: str,
    user_id: str,
) -> None:
    """
    Test full digest generation pipeline.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        openai_api_key: OpenAI key
        anthropic_api_key: Anthropic key
        user_id: User ID
    """
    generator = DigestGenerator(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
    )

    print("\n" + "=" * 70)
    print("GENERATING DAILY DIGEST")
    print("=" * 70)

    digest = await generator.generate(
        user_id=user_id,
        date=datetime.now().date(),
        max_insights=5,
        force_refresh=True,
    )

    print(f"\nDate: {digest['date']}")
    print(f"Quality Badge: {digest['quality_badge']}")
    print(f"Number of Insights: {len(digest['insights'])}")
    print(f"\nQuery Used: {digest['metadata'].get('query', 'N/A')[:200]}...")
    print(f"\nLearning Context:")
    for key, value in digest['metadata'].get('learning_context', {}).items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("INSIGHTS")
    print("=" * 70)

    for i, insight in enumerate(digest["insights"], 1):
        print(f"\n{i}. {insight['title']}")
        print(f"\n   Why Relevant: {insight.get('relevance_reason', 'N/A')[:150]}...")
        print(f"\n   Explanation: {insight['explanation'][:200]}...")
        print(f"\n   Takeaway: {insight['practical_takeaway'][:150]}...")
        print(f"\n   Source: {insight['source']['title']}")
        print(f"   Confidence: {insight['metadata'].get('confidence', 'N/A')}")
        print("-" * 70)

    print(f"\n\nDigest Statistics:")
    print(f"  Chunks Used: {digest['metadata']['num_chunks_used']}")
    print(f"  Unique Sources: {len(digest['metadata']['sources'])}")
    print(f"  Avg Similarity: {digest['metadata']['avg_similarity']:.3f}")


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_digest_generation(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
