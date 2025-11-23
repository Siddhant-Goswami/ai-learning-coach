"""
Source Manager

Manages content sources (RSS feeds, Twitter, Reddit, etc.)
Provides CRUD operations for sources.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import Client
import httpx
import feedparser

from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class SourceManager:
    """Manages content sources for users."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize source manager.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.db = get_supabase_client(supabase_url, supabase_key)

    async def add_source(
        self,
        user_id: str,
        source_type: str,
        identifier: str,
        priority: int = 3,
    ) -> Dict[str, Any]:
        """
        Add a new content source.

        Args:
            user_id: User ID
            source_type: Type of source (rss, twitter, reddit, custom_url)
            identifier: Source identifier (URL, handle, subreddit)
            priority: Priority level 1-5 (default: 3)

        Returns:
            Result dictionary with success status and source info
        """
        logger.info(f"Adding source: type={source_type}, identifier={identifier}")

        # Validate source type
        valid_types = ["rss", "twitter", "reddit", "custom_url", "youtube"]
        if source_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid source type. Must be one of: {', '.join(valid_types)}",
            }

        # Validate priority
        if not 1 <= priority <= 5:
            return {"success": False, "error": "Priority must be between 1 and 5"}

        # Validate source is reachable
        is_valid = await self._validate_source(source_type, identifier)
        if not is_valid:
            return {
                "success": False,
                "error": f"Source validation failed. Could not reach: {identifier}",
            }

        # Check for duplicates
        existing = (
            self.db.table("sources")
            .select("id")
            .eq("user_id", user_id)
            .eq("identifier", identifier)
            .execute()
        )

        if existing.data:
            return {
                "success": False,
                "error": f"Source already exists: {identifier}",
                "source_id": existing.data[0]["id"],
            }

        # Insert source
        try:
            result = (
                self.db.table("sources")
                .insert(
                    {
                        "user_id": user_id,
                        "type": source_type,
                        "identifier": identifier,
                        "priority": priority,
                        "active": True,
                        "health_score": 1.0,
                        "metadata": {
                            "added_at": datetime.now().isoformat(),
                            "validation_status": "valid",
                        },
                    }
                )
                .execute()
            )

            source_id = result.data[0]["id"]

            logger.info(f"✓ Source added successfully: {source_id}")

            return {
                "success": True,
                "message": f"Added source: {identifier}",
                "source_id": source_id,
                "source": result.data[0],
            }

        except Exception as e:
            logger.error(f"Error adding source: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def remove_source(
        self,
        user_id: str,
        identifier: str,
    ) -> Dict[str, Any]:
        """
        Remove a content source.

        Args:
            user_id: User ID
            identifier: Source identifier

        Returns:
            Result dictionary
        """
        logger.info(f"Removing source: {identifier}")

        try:
            # Find source
            source_result = (
                self.db.table("sources")
                .select("id")
                .eq("user_id", user_id)
                .eq("identifier", identifier)
                .execute()
            )

            if not source_result.data:
                return {"success": False, "error": f"Source not found: {identifier}"}

            source_id = source_result.data[0]["id"]

            # Delete source (cascade will delete related content and embeddings)
            self.db.table("sources").delete().eq("id", source_id).execute()

            logger.info(f"✓ Source removed: {identifier}")

            return {
                "success": True,
                "message": f"Removed source: {identifier}",
                "source_id": source_id,
            }

        except Exception as e:
            logger.error(f"Error removing source: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def update_source(
        self,
        user_id: str,
        identifier: str,
        priority: Optional[int] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update source settings.

        Args:
            user_id: User ID
            identifier: Source identifier
            priority: New priority (optional)
            active: New active status (optional)

        Returns:
            Result dictionary
        """
        logger.info(f"Updating source: {identifier}")

        try:
            # Find source
            source_result = (
                self.db.table("sources")
                .select("*")
                .eq("user_id", user_id)
                .eq("identifier", identifier)
                .single()
                .execute()
            )

            if not source_result.data:
                return {"success": False, "error": f"Source not found: {identifier}"}

            source_id = source_result.data["id"]

            # Build update data
            update_data = {}
            if priority is not None:
                if not 1 <= priority <= 5:
                    return {"success": False, "error": "Priority must be between 1 and 5"}
                update_data["priority"] = priority

            if active is not None:
                update_data["active"] = active

            if not update_data:
                return {"success": False, "error": "No updates provided"}

            # Update source
            result = (
                self.db.table("sources")
                .update(update_data)
                .eq("id", source_id)
                .execute()
            )

            logger.info(f"✓ Source updated: {identifier}")

            return {
                "success": True,
                "message": f"Updated source: {identifier}",
                "source": result.data[0],
            }

        except Exception as e:
            logger.error(f"Error updating source: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def list_sources(self, user_id: str) -> Dict[str, Any]:
        """
        List all sources for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with sources list
        """
        try:
            result = (
                self.db.table("sources")
                .select("*")
                .eq("user_id", user_id)
                .order("priority", desc=True)
                .execute()
            )

            sources = result.data if result.data else []

            # Add statistics for each source
            for source in sources:
                # Count content from this source
                content_count = (
                    self.db.table("content")
                    .select("id", count="exact")
                    .eq("source_id", source["id"])
                    .execute()
                )

                source["content_count"] = content_count.count if content_count else 0

            logger.info(f"Listed {len(sources)} sources for user {user_id}")

            return {
                "success": True,
                "sources": sources,
                "total": len(sources),
            }

        except Exception as e:
            logger.error(f"Error listing sources: {e}", exc_info=True)
            return {"success": False, "error": str(e), "sources": []}

    async def _validate_source(self, source_type: str, identifier: str) -> bool:
        """
        Validate that a source is reachable and valid.

        Args:
            source_type: Type of source
            identifier: Source identifier

        Returns:
            True if valid, False otherwise
        """
        try:
            if source_type == "rss":
                return await self._validate_rss(identifier)
            elif source_type == "custom_url":
                return await self._validate_url(identifier)
            elif source_type in ["twitter", "reddit", "youtube"]:
                # For now, just validate format
                # TODO: Add API validation when credentials available
                return len(identifier) > 0
            else:
                return False

        except Exception as e:
            logger.warning(f"Source validation failed: {e}")
            return False

    async def _validate_rss(self, url: str) -> bool:
        """Validate RSS feed."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0, follow_redirects=True)
                response.raise_for_status()

                # Try to parse as RSS
                feed = feedparser.parse(response.text)

                # Check if valid feed
                if feed.bozo and not feed.entries:
                    logger.warning(f"Invalid RSS feed: {url}")
                    return False

                return len(feed.entries) > 0

        except Exception as e:
            logger.warning(f"RSS validation failed for {url}: {e}")
            return False

    async def _validate_url(self, url: str) -> bool:
        """Validate custom URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0, follow_redirects=True)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return False


async def test_source_manager(
    supabase_url: str,
    supabase_key: str,
    user_id: str,
) -> None:
    """
    Test source manager functionality.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        user_id: User ID
    """
    manager = SourceManager(supabase_url=supabase_url, supabase_key=supabase_key)

    print("\n" + "=" * 60)
    print("SOURCE MANAGER TEST")
    print("=" * 60)

    # Test 1: Add source
    print("\n1. Adding RSS source...")
    result = await manager.add_source(
        user_id=user_id,
        source_type="rss",
        identifier="https://lilianweng.github.io/feed.xml",
        priority=5,
    )
    print(f"   Result: {result['message'] if result['success'] else result['error']}")

    # Test 2: List sources
    print("\n2. Listing sources...")
    result = await manager.list_sources(user_id=user_id)
    if result["success"]:
        print(f"   Found {result['total']} sources:")
        for src in result["sources"]:
            print(f"   - {src['identifier']} (priority: {src['priority']}, active: {src['active']})")

    # Test 3: Update source
    print("\n3. Updating source priority...")
    result = await manager.update_source(
        user_id=user_id,
        identifier="https://lilianweng.github.io/feed.xml",
        priority=4,
    )
    print(f"   Result: {result['message'] if result['success'] else result['error']}")


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_source_manager(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
