"""
Feedback Handler

Processes user feedback on insights and updates source priorities.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from supabase import Client

from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """Handles user feedback processing."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize feedback handler.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.db = get_supabase_client(supabase_url, supabase_key)

    async def record_feedback(
        self,
        user_id: str,
        insight_id: str,
        feedback_type: str,
        reason: Optional[str] = None,
        content_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record user feedback on an insight.

        Args:
            user_id: User ID
            insight_id: Insight ID
            feedback_type: Type of feedback (helpful, not_relevant, incorrect, too_basic, too_advanced)
            reason: Optional explanation
            content_id: Optional content ID that insight was based on

        Returns:
            Result dictionary
        """
        logger.info(f"Recording feedback: type={feedback_type}, insight={insight_id}")

        # Validate feedback type
        valid_types = ["helpful", "not_relevant", "incorrect", "too_basic", "too_advanced"]
        if feedback_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid feedback type. Must be one of: {', '.join(valid_types)}",
            }

        # Truncate reason if too long
        if reason and len(reason) > 500:
            reason = reason[:500]

        try:
            # Insert feedback
            result = (
                self.db.table("feedback")
                .insert(
                    {
                        "user_id": user_id,
                        "insight_id": insight_id,
                        "content_id": content_id,
                        "type": feedback_type,
                        "reason": reason,
                        "created_at": datetime.now().isoformat(),
                    }
                )
                .execute()
            )

            logger.info(f"✓ Feedback recorded: {feedback_type}")

            return {
                "success": True,
                "message": "Feedback recorded",
                "feedback_id": result.data[0]["id"],
            }

        except Exception as e:
            logger.error(f"Error recording feedback: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def update_source_priorities(
        self,
        insight_id: str,
        feedback_type: str,
    ) -> None:
        """
        Update source priorities based on feedback.

        Args:
            insight_id: Insight ID
            feedback_type: Type of feedback
        """
        logger.info(f"Updating source priorities based on feedback: {feedback_type}")

        try:
            # Determine priority adjustment
            if feedback_type == "helpful":
                adjustment = 0.2  # Increase priority
            elif feedback_type in ["not_relevant", "incorrect"]:
                adjustment = -0.2  # Decrease priority
            elif feedback_type in ["too_basic", "too_advanced"]:
                adjustment = -0.1  # Slight decrease
            else:
                return  # No adjustment for other types

            # Find content IDs associated with this insight
            # Note: In real implementation, we'd store insight-to-content mapping
            # For now, we'll update based on recent content
            # This is a simplified version - in production, store the mapping

            logger.debug(f"Priority adjustment: {adjustment:+.2f}")

            # TODO: Implement actual source priority updates
            # This requires storing insight → content_ids mapping
            # For MVP, we'll skip this and rely on future implementations

        except Exception as e:
            logger.error(f"Error updating source priorities: {e}", exc_info=True)

    async def get_feedback_stats(
        self,
        user_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get feedback statistics for a user.

        Args:
            user_id: User ID
            days: Number of days to analyze (default: 7)

        Returns:
            Statistics dictionary
        """
        try:
            # Get feedback from last N days
            from datetime import timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = (
                self.db.table("feedback")
                .select("*")
                .eq("user_id", user_id)
                .gte("created_at", cutoff_date)
                .execute()
            )

            feedbacks = result.data if result.data else []

            # Calculate statistics
            total = len(feedbacks)
            if total == 0:
                return {
                    "total": 0,
                    "helpful_rate": 0.0,
                    "breakdown": {},
                }

            # Count by type
            breakdown = {}
            for feedback in feedbacks:
                ftype = feedback["type"]
                breakdown[ftype] = breakdown.get(ftype, 0) + 1

            # Calculate helpful rate
            helpful_count = breakdown.get("helpful", 0)
            helpful_rate = helpful_count / total if total > 0 else 0

            return {
                "total": total,
                "helpful_rate": helpful_rate,
                "helpful_percentage": helpful_rate * 100,
                "breakdown": breakdown,
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_source_feedback_scores(self, user_id: str) -> Dict[str, float]:
        """
        Get feedback-based scores for each source.

        Args:
            user_id: User ID

        Returns:
            Dictionary mapping source_id to feedback score
        """
        try:
            # Get all feedback with content associations
            result = (
                self.db.table("feedback")
                .select("type, content_id")
                .eq("user_id", user_id)
                .not_.is_("content_id", "null")
                .execute()
            )

            feedbacks = result.data if result.data else []

            # Map content_id to source_id and calculate scores
            source_scores = {}

            for feedback in feedbacks:
                content_id = feedback["content_id"]
                ftype = feedback["type"]

                # Get source_id for this content
                content_result = (
                    self.db.table("content")
                    .select("source_id")
                    .eq("id", content_id)
                    .single()
                    .execute()
                )

                if not content_result.data:
                    continue

                source_id = content_result.data["source_id"]

                # Update score
                if source_id not in source_scores:
                    source_scores[source_id] = {"helpful": 0, "negative": 0}

                if ftype == "helpful":
                    source_scores[source_id]["helpful"] += 1
                elif ftype in ["not_relevant", "incorrect"]:
                    source_scores[source_id]["negative"] += 1

            # Calculate final scores (0-1 scale)
            final_scores = {}
            for source_id, counts in source_scores.items():
                total = counts["helpful"] + counts["negative"]
                if total > 0:
                    final_scores[source_id] = counts["helpful"] / total
                else:
                    final_scores[source_id] = 0.5  # Neutral

            return final_scores

        except Exception as e:
            logger.error(f"Error calculating source feedback scores: {e}", exc_info=True)
            return {}


async def test_feedback_handler(
    supabase_url: str,
    supabase_key: str,
    user_id: str,
) -> None:
    """
    Test feedback handler functionality.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        user_id: User ID
    """
    handler = FeedbackHandler(supabase_url=supabase_url, supabase_key=supabase_key)

    print("\n" + "=" * 60)
    print("FEEDBACK HANDLER TEST")
    print("=" * 60)

    # Test 1: Record feedback
    print("\n1. Recording feedback...")
    result = await handler.record_feedback(
        user_id=user_id,
        insight_id="test_insight_123",
        feedback_type="helpful",
        reason="Great explanation of transformers!",
    )
    print(f"   Result: {result['message'] if result['success'] else result['error']}")

    # Test 2: Get feedback stats
    print("\n2. Getting feedback statistics...")
    stats = await handler.get_feedback_stats(user_id=user_id, days=30)
    if "error" not in stats:
        print(f"   Total feedback: {stats['total']}")
        print(f"   Helpful rate: {stats['helpful_percentage']:.1f}%")
        print(f"   Breakdown: {stats['breakdown']}")


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_feedback_handler(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
