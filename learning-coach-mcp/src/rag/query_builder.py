"""
Query Builder

Constructs semantic search queries from user's learning context.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import Client

from ..utils.db import get_supabase_client

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Builds semantic search queries from learning context."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize query builder.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.db = get_supabase_client(supabase_url, supabase_key)

    async def build_query_from_context(
        self,
        user_id: str,
        explicit_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build search query from user's learning context.

        Args:
            user_id: User ID
            explicit_query: Optional explicit query from user

        Returns:
            Dictionary with query text and context metadata
        """
        logger.info(f"Building query for user: {user_id}")

        # Get learning context from database
        learning_context = await self._get_learning_context(user_id)

        if not learning_context:
            logger.warning(f"No learning context found for user {user_id}")
            # Fallback to generic query
            query_text = explicit_query or "Recent articles about AI and machine learning"
        else:
            # Construct query from context
            query_text = self._construct_query_text(learning_context, explicit_query)

        return {
            "query_text": query_text,
            "learning_context": learning_context,
            "has_explicit_query": explicit_query is not None,
            "generated_at": datetime.now().isoformat(),
        }

    async def _get_learning_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user's learning context from database.

        Args:
            user_id: User ID

        Returns:
            Learning context dictionary or None
        """
        try:
            result = (
                self.db.table("learning_progress")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            if not result.data:
                return None

            return {
                "current_week": result.data.get("current_week"),
                "current_topics": result.data.get("current_topics", []),
                "difficulty_level": result.data.get("difficulty_level", "intermediate"),
                "learning_goals": result.data.get("learning_goals", ""),
                "completed_weeks": result.data.get("completed_weeks", []),
                "metadata": result.data.get("metadata", {}),
            }

        except Exception as e:
            logger.error(f"Error fetching learning context: {e}")
            return None

    def _construct_query_text(
        self,
        context: Dict[str, Any],
        explicit_query: Optional[str] = None,
    ) -> str:
        """
        Construct semantic query text from learning context.

        Args:
            context: Learning context dictionary
            explicit_query: Optional explicit user query

        Returns:
            Query text string
        """
        # If user provided explicit query, enhance it with context
        if explicit_query:
            query_parts = [explicit_query]

            # Add context hints
            if context.get("current_topics"):
                topics_str = ", ".join(context["current_topics"][:3])
                query_parts.append(
                    f"Related to my current learning topics: {topics_str}."
                )

            if context.get("difficulty_level"):
                level = context["difficulty_level"]
                query_parts.append(
                    f"I'm at {level} level, so provide {level}-appropriate depth."
                )

            return " ".join(query_parts)

        # Otherwise, construct query from context
        query_parts = []

        # Week and bootcamp info
        if context.get("current_week"):
            query_parts.append(
                f"I am in Week {context['current_week']} of an AI bootcamp."
            )

        # Topics
        if context.get("current_topics"):
            topics = context["current_topics"]
            if len(topics) == 1:
                query_parts.append(f"I am learning about {topics[0]}.")
            else:
                topics_str = ", ".join(topics[:-1]) + f", and {topics[-1]}"
                query_parts.append(f"I am learning about {topics_str}.")

        # Difficulty level
        difficulty = context.get("difficulty_level", "intermediate")
        if difficulty == "beginner":
            query_parts.append(
                "I am a beginner, so I need foundational explanations with examples."
            )
        elif difficulty == "intermediate":
            query_parts.append(
                "I have intermediate knowledge, so I need practical implementation details."
            )
        elif difficulty == "advanced":
            query_parts.append(
                "I have advanced knowledge, so I need deep technical insights and edge cases."
            )

        # Learning goals
        if context.get("learning_goals"):
            query_parts.append(f"My goal is to: {context['learning_goals']}.")

        # Request type
        query_parts.append(
            "Find recent articles that explain these topics with practical examples, "
            "implementation details, and real-world applications. "
            "Prefer technical depth over high-level overviews."
        )

        query_text = " ".join(query_parts)

        logger.debug(f"Constructed query: {query_text[:200]}...")
        return query_text

    async def build_weekly_summary_query(
        self,
        user_id: str,
        week_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Build query for weekly summary generation.

        Args:
            user_id: User ID
            week_number: Specific week number (None for current week)

        Returns:
            Query dictionary for weekly summary
        """
        context = await self._get_learning_context(user_id)

        if not context:
            raise ValueError(f"No learning context found for user {user_id}")

        target_week = week_number or context.get("current_week")

        query_text = (
            f"Summarize the most important concepts and insights from Week {target_week}. "
            f"Topics covered: {', '.join(context.get('current_topics', []))}. "
            f"Provide a comprehensive overview with key takeaways and learning progress."
        )

        return {
            "query_text": query_text,
            "week_number": target_week,
            "learning_context": context,
            "query_type": "weekly_summary",
        }

    async def build_topic_deep_dive_query(
        self,
        user_id: str,
        topic: str,
    ) -> Dict[str, Any]:
        """
        Build query for deep dive into a specific topic.

        Args:
            user_id: User ID
            topic: Topic to explore

        Returns:
            Query dictionary for topic deep dive
        """
        context = await self._get_learning_context(user_id)

        difficulty = context.get("difficulty_level", "intermediate") if context else "intermediate"

        query_text = (
            f"Provide a comprehensive, {difficulty}-level explanation of {topic}. "
            f"Include: fundamental concepts, how it works, practical examples, "
            f"implementation details, common pitfalls, and real-world applications. "
            f"Focus on technical depth and actionable insights."
        )

        return {
            "query_text": query_text,
            "topic": topic,
            "learning_context": context,
            "query_type": "deep_dive",
        }

    def get_query_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate suggested queries based on learning context.

        Args:
            context: Learning context

        Returns:
            List of suggested query strings
        """
        suggestions = []

        topics = context.get("current_topics", [])

        for topic in topics[:3]:  # Top 3 topics
            suggestions.append(f"How does {topic} work?")
            suggestions.append(f"Practical examples of {topic}")
            suggestions.append(f"Common mistakes with {topic}")

        # Add goal-based suggestions
        if context.get("learning_goals"):
            goal = context["learning_goals"]
            suggestions.append(f"Resources for: {goal}")
            suggestions.append(f"Step-by-step guide to: {goal}")

        return suggestions


async def test_query_builder(
    supabase_url: str,
    supabase_key: str,
    user_id: str,
) -> None:
    """
    Test query builder functionality.

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase key
        user_id: User ID
    """
    builder = QueryBuilder(supabase_url=supabase_url, supabase_key=supabase_key)

    # Test 1: Query from context
    print("=" * 60)
    print("Test 1: Query from Learning Context")
    print("=" * 60)

    result = await builder.build_query_from_context(user_id=user_id)

    print(f"\nGenerated Query:\n{result['query_text']}\n")
    print(f"Learning Context:")
    for key, value in result["learning_context"].items():
        print(f"  {key}: {value}")

    # Test 2: Query with explicit input
    print("\n" + "=" * 60)
    print("Test 2: Query with Explicit User Input")
    print("=" * 60)

    result = await builder.build_query_from_context(
        user_id=user_id,
        explicit_query="Explain multi-head attention in detail",
    )

    print(f"\nEnhanced Query:\n{result['query_text']}\n")

    # Test 3: Topic deep dive
    print("\n" + "=" * 60)
    print("Test 3: Topic Deep Dive Query")
    print("=" * 60)

    result = await builder.build_topic_deep_dive_query(
        user_id=user_id,
        topic="Transformers",
    )

    print(f"\nDeep Dive Query:\n{result['query_text']}\n")

    # Test 4: Query suggestions
    print("\n" + "=" * 60)
    print("Test 4: Query Suggestions")
    print("=" * 60)

    context_result = await builder.build_query_from_context(user_id=user_id)
    suggestions = builder.get_query_suggestions(context_result["learning_context"])

    print("\nSuggested Queries:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")


if __name__ == "__main__":
    import os
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(
        test_query_builder(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            user_id=os.getenv("DEFAULT_USER_ID"),
        )
    )
