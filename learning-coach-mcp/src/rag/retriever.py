"""
Vector Retriever with Hybrid Ranking

Retrieves relevant content chunks using vector similarity search
combined with recency and source priority scoring.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from supabase import Client

from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Retrieves relevant content using hybrid ranking."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
    ):
        """
        Initialize vector retriever.

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

    async def retrieve(
        self,
        query: str,
        user_id: str,
        top_k: int = 15,
        similarity_threshold: float = 0.70,
        min_sources: int = 3,
        recency_weight: float = 0.3,
        priority_weight: float = 0.1,
        similarity_weight: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using hybrid ranking.

        Args:
            query: Search query text
            user_id: User ID for filtering sources
            top_k: Number of top results to return (default: 15)
            similarity_threshold: Minimum cosine similarity (default: 0.70)
            min_sources: Minimum number of different sources in results (default: 3)
            recency_weight: Weight for recency score (default: 0.3)
            priority_weight: Weight for source priority (default: 0.1)
            similarity_weight: Weight for vector similarity (default: 0.6)

        Returns:
            List of chunk dictionaries with metadata and scores
        """
        logger.info(f"Retrieving chunks for query: '{query[:100]}...'")

        # 1. Generate query embedding
        query_embedding = await self._generate_query_embedding(query)

        # 2. Vector similarity search
        similar_chunks = await self._vector_search(
            query_embedding=query_embedding,
            user_id=user_id,
            match_count=top_k * 2,  # Retrieve more than needed for re-ranking
            similarity_threshold=similarity_threshold,
        )

        if not similar_chunks:
            logger.warning("No chunks found above similarity threshold")
            return []

        # 3. Apply hybrid ranking
        ranked_chunks = self._apply_hybrid_ranking(
            chunks=similar_chunks,
            recency_weight=recency_weight,
            priority_weight=priority_weight,
            similarity_weight=similarity_weight,
        )

        # 4. Ensure source diversity
        diverse_chunks = self._ensure_source_diversity(
            chunks=ranked_chunks,
            min_sources=min_sources,
            top_k=top_k,
        )

        logger.info(
            f"Retrieved {len(diverse_chunks)} chunks from "
            f"{len(set(c['source_id'] for c in diverse_chunks))} different sources"
        )

        return diverse_chunks

    async def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        response = await self.embeddings_client.embeddings.create(
            model=self.embedding_model,
            input=query,
            dimensions=self.embedding_dimensions,
        )

        return response.data[0].embedding

    async def _vector_search(
        self,
        query_embedding: List[float],
        user_id: str,
        match_count: int,
        similarity_threshold: float,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using Supabase RPC.

        Args:
            query_embedding: Query embedding vector
            user_id: User ID for filtering
            match_count: Number of matches to retrieve
            similarity_threshold: Minimum similarity score

        Returns:
            List of matching chunks with metadata
        """
        try:
            # Call Supabase RPC function
            result = self.db.rpc(
                "match_embeddings",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": match_count,
                    "filter_user_id": user_id,
                },
            ).execute()

            chunks = result.data if result.data else []

            logger.debug(f"Vector search returned {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            raise

    def _apply_hybrid_ranking(
        self,
        chunks: List[Dict[str, Any]],
        recency_weight: float,
        priority_weight: float,
        similarity_weight: float,
    ) -> List[Dict[str, Any]]:
        """
        Apply hybrid ranking combining similarity, recency, and priority.

        Args:
            chunks: List of chunks from vector search
            recency_weight: Weight for recency factor
            priority_weight: Weight for source priority
            similarity_weight: Weight for similarity score

        Returns:
            Chunks sorted by hybrid score
        """
        now = datetime.now()

        for chunk in chunks:
            # Similarity score (already 0-1 from cosine similarity)
            similarity = chunk["similarity"]

            # Recency factor (0-1, higher for newer content)
            published_at = datetime.fromisoformat(chunk["published_at"])
            days_old = (now - published_at).days
            recency_factor = max(0, 1 - (days_old / 30))  # Decay over 30 days

            # Priority factor (0-1, normalized from 1-5 scale)
            priority_factor = chunk["source_priority"] / 5.0

            # Combined hybrid score
            hybrid_score = (
                similarity_weight * similarity
                + recency_weight * recency_factor
                + priority_weight * priority_factor
            )

            # Store individual scores for debugging
            chunk["scores"] = {
                "similarity": similarity,
                "recency": recency_factor,
                "priority": priority_factor,
                "hybrid": hybrid_score,
            }
            chunk["final_score"] = hybrid_score

        # Sort by hybrid score (descending)
        chunks.sort(key=lambda x: x["final_score"], reverse=True)

        return chunks

    def _ensure_source_diversity(
        self,
        chunks: List[Dict[str, Any]],
        min_sources: int,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Ensure results include chunks from multiple sources.

        Args:
            chunks: Ranked chunks
            min_sources: Minimum number of different sources
            top_k: Target number of chunks to return

        Returns:
            Diversified chunk list
        """
        if not chunks:
            return []

        # Track sources seen
        seen_sources = set()
        diverse_chunks = []
        remaining_chunks = []

        # First pass: ensure at least one chunk from each source
        for chunk in chunks:
            source_id = chunk["source_id"]

            if source_id not in seen_sources:
                diverse_chunks.append(chunk)
                seen_sources.add(source_id)

                # Stop if we have enough sources and chunks
                if len(seen_sources) >= min_sources and len(diverse_chunks) >= top_k:
                    break
            else:
                remaining_chunks.append(chunk)

        # Second pass: fill remaining slots with highest-scoring chunks
        if len(diverse_chunks) < top_k:
            needed = top_k - len(diverse_chunks)
            diverse_chunks.extend(remaining_chunks[:needed])

        return diverse_chunks[:top_k]

    async def retrieve_with_context(
        self,
        query: str,
        user_id: str,
        learning_context: Dict[str, Any],
        top_k: int = 15,
    ) -> Dict[str, Any]:
        """
        Retrieve chunks with additional learning context.

        Args:
            query: Search query
            user_id: User ID
            learning_context: User's learning context (week, topics, etc.)
            top_k: Number of chunks to retrieve

        Returns:
            Dictionary with chunks and metadata
        """
        chunks = await self.retrieve(
            query=query,
            user_id=user_id,
            top_k=top_k,
        )

        return {
            "chunks": chunks,
            "query": query,
            "learning_context": learning_context,
            "retrieved_at": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "sources": list(set(c["source_id"] for c in chunks)),
            "avg_similarity": (
                sum(c["similarity"] for c in chunks) / len(chunks) if chunks else 0
            ),
        }


async def test_retrieval(
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    user_id: str,
    query: str,
) -> None:
    """
    Test retrieval functionality.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        openai_api_key: OpenAI key
        user_id: User ID
        query: Test query
    """
    retriever = VectorRetriever(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        openai_api_key=openai_api_key,
    )

    results = await retriever.retrieve(
        query=query,
        user_id=user_id,
        top_k=5,
    )

    print(f"\nRetrieved {len(results)} chunks for query: '{query}'\n")

    for i, chunk in enumerate(results, 1):
        print(f"\n{i}. {chunk['content_title']}")
        print(f"   Similarity: {chunk['similarity']:.3f}")
        print(f"   Hybrid Score: {chunk['final_score']:.3f}")
        print(f"   Published: {chunk['published_at']}")
        print(f"   Chunk: {chunk['chunk_text'][:100]}...")


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_retrieval(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
            query="Explain how attention mechanisms work in transformers",
        )
    )
