"""
Ingestion Orchestrator

Coordinates content fetching, chunking, embedding, and storage.
Runs as a background worker with scheduled jobs.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import Client

from .rss_fetcher import RSSFetcher, fetch_multiple_feeds
from .chunker import TextChunker, chunk_document
from .embedder import Embedder
from utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Orchestrates the content ingestion pipeline."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        chunk_size: int = 750,
        overlap: int = 100,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
    ):
        """
        Initialize ingestion orchestrator.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            openai_api_key: OpenAI API key
            chunk_size: Text chunk size in tokens
            overlap: Overlap between chunks
            embedding_model: OpenAI embedding model
            embedding_dimensions: Embedding vector dimensions
        """
        self.db = get_supabase_client(supabase_url, supabase_key)
        self.rss_fetcher = RSSFetcher()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        self.embedder = Embedder(
            api_key=openai_api_key,
            model=embedding_model,
            dimensions=embedding_dimensions,
        )
        self.scheduler = AsyncIOScheduler()

    async def ingest_source(
        self,
        source_id: str,
        user_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest content from a single source.

        Args:
            source_id: Source UUID
            user_id: User UUID
            force_refresh: Fetch all content regardless of last_fetched

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting ingestion for source: {source_id}")

        try:
            # Get source details
            source_result = self.db.table("sources").select("*").eq("id", source_id).single().execute()

            if not source_result.data:
                raise ValueError(f"Source not found: {source_id}")

            source = source_result.data

            # Check if source is active
            if not source["active"]:
                logger.info(f"Source {source_id} is inactive, skipping")
                return {"status": "skipped", "reason": "inactive"}

            # Determine fetch start time
            since = None
            if not force_refresh and source.get("last_fetched"):
                since = datetime.fromisoformat(source["last_fetched"])

            # Fetch articles based on source type
            if source["type"] == "rss":
                articles = await self.rss_fetcher.fetch_feed(
                    source["identifier"],
                    since=since,
                )
            else:
                logger.warning(f"Source type {source['type']} not yet implemented")
                return {"status": "skipped", "reason": "unsupported_type"}

            if not articles:
                logger.info(f"No new articles found for source {source_id}")
                # Update last_fetched and health_score
                await self._update_source_health(source_id, success=True)
                return {"status": "success", "articles_processed": 0}

            # Process articles
            stats = await self._process_articles(articles, source_id, user_id)

            # Update source health
            await self._update_source_health(source_id, success=True)

            logger.info(
                f"Ingestion complete for source {source_id}: "
                f"{stats['articles_processed']} articles, "
                f"{stats['chunks_created']} chunks"
            )

            return stats

        except Exception as e:
            logger.error(f"Error ingesting source {source_id}: {e}", exc_info=True)
            await self._update_source_health(source_id, success=False)
            return {"status": "error", "error": str(e)}

    async def _process_articles(
        self,
        articles: List[Dict[str, Any]],
        source_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Process fetched articles: deduplicate, chunk, embed, store.

        Args:
            articles: List of article dictionaries
            source_id: Source UUID
            user_id: User UUID

        Returns:
            Processing statistics
        """
        articles_processed = 0
        chunks_created = 0
        duplicates_skipped = 0

        for article in articles:
            try:
                # Generate content hash for deduplication
                content_hash = hashlib.md5(article["content"].encode()).hexdigest()

                # Check if article already exists
                existing = (
                    self.db.table("content")
                    .select("id")
                    .eq("content_hash", content_hash)
                    .execute()
                )

                if existing.data:
                    duplicates_skipped += 1
                    logger.debug(f"Skipping duplicate article: {article['title']}")
                    continue

                # Store article in content table
                content_result = (
                    self.db.table("content")
                    .insert(
                        {
                            "source_id": source_id,
                            "title": article["title"],
                            "author": article.get("author", "Unknown"),
                            "published_at": article["published_at"].isoformat()
                            if article.get("published_at")
                            else None,
                            "url": article["url"],
                            "content_hash": content_hash,
                            "raw_text": article["content"],
                            "metadata": {
                                "tags": article.get("tags", []),
                                "word_count": len(article["content"].split()),
                            },
                        }
                    )
                    .execute()
                )

                content_id = content_result.data[0]["id"]

                # Chunk the article
                chunks = chunk_document(article)

                if not chunks:
                    logger.warning(f"No chunks created for article: {article['title']}")
                    continue

                # Generate embeddings for chunks
                chunk_texts = [chunk["chunk_text"] for chunk in chunks]
                embeddings = await self.embedder.generate_embeddings(chunk_texts)

                # Store chunks with embeddings
                for chunk, embedding in zip(chunks, embeddings):
                    self.db.table("embeddings").insert(
                        {
                            "content_id": content_id,
                            "chunk_sequence": chunk["chunk_sequence"],
                            "chunk_text": chunk["chunk_text"],
                            "embedding": embedding,
                            "metadata": chunk.get("metadata", {}),
                        }
                    ).execute()

                articles_processed += 1
                chunks_created += len(chunks)

                logger.debug(
                    f"Processed article '{article['title']}': {len(chunks)} chunks"
                )

            except Exception as e:
                logger.error(f"Error processing article '{article.get('title', 'unknown')}': {e}")
                continue

        return {
            "status": "success",
            "articles_processed": articles_processed,
            "chunks_created": chunks_created,
            "duplicates_skipped": duplicates_skipped,
        }

    async def _update_source_health(self, source_id: str, success: bool) -> None:
        """
        Update source health score and last_fetched timestamp.

        Args:
            source_id: Source UUID
            success: Whether fetch was successful
        """
        try:
            # Call Supabase function to update health
            self.db.rpc("update_source_health", {"source_id_param": source_id, "success": success}).execute()

        except Exception as e:
            logger.error(f"Error updating source health for {source_id}: {e}")

    async def ingest_all_active_sources(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest content from all active sources.

        Args:
            user_id: Optional user ID to filter sources (if None, ingests for all users)

        Returns:
            Aggregated statistics
        """
        logger.info("Starting ingestion for all active sources")

        # Get all active sources
        query = self.db.table("sources").select("id, user_id").eq("active", True)

        if user_id:
            query = query.eq("user_id", user_id)

        sources_result = query.execute()

        if not sources_result.data:
            logger.info("No active sources found")
            return {"status": "success", "sources_processed": 0}

        total_articles = 0
        total_chunks = 0
        sources_processed = 0
        sources_failed = 0

        for source in sources_result.data:
            try:
                stats = await self.ingest_source(source["id"], source["user_id"])

                if stats["status"] == "success":
                    sources_processed += 1
                    total_articles += stats.get("articles_processed", 0)
                    total_chunks += stats.get("chunks_created", 0)
                else:
                    sources_failed += 1

            except Exception as e:
                logger.error(f"Error ingesting source {source['id']}: {e}")
                sources_failed += 1

        logger.info(
            f"Ingestion complete: {sources_processed} sources, "
            f"{total_articles} articles, {total_chunks} chunks"
        )

        return {
            "status": "success",
            "sources_processed": sources_processed,
            "sources_failed": sources_failed,
            "total_articles": total_articles,
            "total_chunks": total_chunks,
        }

    def start_scheduled_ingestion(self, interval_hours: int = 6) -> None:
        """
        Start scheduled ingestion job.

        Args:
            interval_hours: Hours between ingestion runs (default: 6)
        """
        logger.info(f"Starting scheduled ingestion (every {interval_hours} hours)")

        self.scheduler.add_job(
            self.ingest_all_active_sources,
            "interval",
            hours=interval_hours,
            id="content_ingestion",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler started")

    def stop_scheduled_ingestion(self) -> None:
        """Stop scheduled ingestion job."""
        logger.info("Stopping scheduled ingestion")
        self.scheduler.shutdown()


async def run_manual_ingestion(
    supabase_url: str,
    supabase_key: str,
    openai_api_key: str,
    user_id: Optional[str] = None,
) -> None:
    """
    Run one-time manual ingestion.

    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        openai_api_key: OpenAI API key
        user_id: Optional user ID to filter sources
    """
    orchestrator = IngestionOrchestrator(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        openai_api_key=openai_api_key,
    )

    stats = await orchestrator.ingest_all_active_sources(user_id=user_id)

    logger.info(f"Manual ingestion complete: {stats}")
    print(f"\nIngestion Statistics:")
    print(f"  Sources processed: {stats['sources_processed']}")
    print(f"  Sources failed: {stats['sources_failed']}")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Total chunks: {stats['total_chunks']}")


if __name__ == "__main__":
    # For testing: run manual ingestion
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        run_manual_ingestion(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
