"""
Educational Synthesizer

Synthesizes personalized learning insights from retrieved content
using Claude with first-principles thinking and Feynman technique.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class EducationalSynthesizer:
    """Synthesizes educational insights using Claude."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
    ):
        """
        Initialize synthesizer.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def synthesize_insights(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int = 7,
        stricter: bool = False,
    ) -> Dict[str, Any]:
        """
        Synthesize personalized learning insights from retrieved content.

        Args:
            retrieved_chunks: Chunks retrieved from vector search
            learning_context: User's learning context (week, topics, level, goals)
            query: Original search query
            num_insights: Number of insights to generate (default: 7)
            stricter: Use stricter prompt for higher quality (default: False)

        Returns:
            Dictionary with insights array and metadata
        """
        logger.info(f"Synthesizing {num_insights} insights from {len(retrieved_chunks)} chunks")

        if not retrieved_chunks:
            logger.warning("No chunks provided for synthesis")
            return {"insights": [], "metadata": {"error": "No content to synthesize"}}

        # Build context from chunks
        context_text = self._build_context_text(retrieved_chunks)

        # Construct prompts
        system_prompt = self._build_system_prompt(stricter=stricter)
        user_prompt = self._build_user_prompt(
            context_text=context_text,
            learning_context=learning_context,
            query=query,
            num_insights=num_insights,
        )

        # Call Claude
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.3,  # Lower temperature for consistency
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Parse JSON response
            response_text = response.content[0].text

            # Extract JSON from response (may be wrapped in markdown code block)
            insights_data = self._extract_json(response_text)

            # Validate and enrich insights
            insights = self._validate_and_enrich_insights(
                insights_data=insights_data,
                retrieved_chunks=retrieved_chunks,
            )

            logger.info(f"Successfully synthesized {len(insights)} insights")

            return {
                "insights": insights,
                "metadata": {
                    "num_chunks_used": len(retrieved_chunks),
                    "model": self.model,
                    "temperature": 0.3,
                    "generated_at": datetime.now().isoformat(),
                    "query": query,
                },
            }

        except Exception as e:
            logger.error(f"Error synthesizing insights: {e}", exc_info=True)
            return {
                "insights": [],
                "metadata": {
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                },
            }

    def _build_system_prompt(self, stricter: bool = False) -> str:
        """
        Build system prompt for Claude.

        Args:
            stricter: Use stricter guidelines for accuracy

        Returns:
            System prompt string
        """
        base_prompt = """You are an expert AI learning coach with deep expertise in educational theory and first-principles thinking. Your role is to help learners understand complex AI/ML concepts by:

1. **First-Principles Thinking**: Break down concepts to their fundamentals before building up
2. **Feynman Technique**: Explain as if teaching someone without prior knowledge, then add depth
3. **Practical Application**: Always connect theory to real-world implementation
4. **Active Learning**: Provide actionable takeaways, not just passive information
5. **Source Fidelity**: Maintain accuracy to source material while synthesizing

Educational Principles:
- Start with "WHY" before "HOW" - motivation drives understanding
- Use analogies only when they clarify, never when they obscure
- Prefer concrete examples over abstract descriptions
- Connect new concepts to prior knowledge explicitly
- Highlight common misconceptions and pitfalls
- Provide progressive disclosure: overview → details → nuances

Quality Standards:
- Every insight must be grounded in the provided source material
- Citations must be accurate and specific
- Explanations must be self-contained (understandable without external references)
- Practical takeaways must be immediately actionable
- Tone should match the learner's level (avoid condescension or overwhelming jargon)"""

        if stricter:
            base_prompt += """

STRICT MODE ACTIVATED:
- Be extremely precise and accurate - no speculation beyond source material
- Reduce creativity in explanations - stick closely to source content
- Emphasize source fidelity above all else
- If uncertain about any detail, omit rather than infer
- Double-check all technical claims against source material"""

        return base_prompt

    def _build_user_prompt(
        self,
        context_text: str,
        learning_context: Dict[str, Any],
        query: str,
        num_insights: int,
    ) -> str:
        """
        Build user prompt with context and request.

        Args:
            context_text: Formatted context from retrieved chunks
            learning_context: Learning context metadata
            query: Search query
            num_insights: Number of insights to generate

        Returns:
            User prompt string
        """
        # Extract learning context details
        current_week = learning_context.get("current_week", "N/A")
        topics = learning_context.get("current_topics", [])
        difficulty = learning_context.get("difficulty_level", "intermediate")
        goal = learning_context.get("learning_goals", "General AI/ML learning")

        topics_str = ", ".join(topics) if topics else "AI and Machine Learning"

        prompt = f"""# Learning Context

**Current Week**: {current_week}
**Topics**: {topics_str}
**Level**: {difficulty}
**Goal**: {goal}

# Search Query
{query}

# Retrieved Content

{context_text}

# Task

Generate **{num_insights}** personalized learning insights based on the content above and tailored to my learning context.

For each insight, provide:

1. **Title**: Concise, specific title (max 100 characters)
2. **Relevance Reason**: Brief explanation of why this insight matters for my current learning (50-100 words)
3. **Explanation**: Main educational content using first-principles approach (300-500 words)
   - Start with fundamentals (the "why")
   - Build up to implementation (the "how")
   - Include concrete examples
   - Connect to my learning goals
   - Highlight key takeaways
4. **Practical Takeaway**: One actionable item I can do immediately (50-100 words)
   - Should be specific and concrete
   - Should align with my skill level
   - Should advance toward my learning goal
5. **Source Attribution**: Full source details (title, author, URL, date)

# Output Format

Return a JSON object matching this exact schema:

```json
{{
  "insights": [
    {{
      "title": "string (max 100 chars)",
      "relevance_reason": "string (50-100 words)",
      "explanation": "string (300-500 words, first-principles approach)",
      "practical_takeaway": "string (50-100 words, actionable)",
      "source": {{
        "title": "string (exact source title)",
        "author": "string",
        "url": "string (full URL)",
        "published_date": "YYYY-MM-DD"
      }},
      "metadata": {{
        "confidence": 0.0-1.0,
        "estimated_read_time": integer (minutes),
        "difficulty_level": "beginner|intermediate|advanced",
        "tags": ["array", "of", "relevant", "tags"]
      }}
    }}
  ]
}}
```

IMPORTANT:
- Return ONLY valid JSON, no additional text
- Ensure all {num_insights} insights are unique and cover different aspects
- Base all content strictly on the provided sources
- Match explanation depth to my {difficulty} level
- Make practical takeaways specific to my goal: "{goal}"
"""

        return prompt

    def _build_context_text(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context text.

        Args:
            chunks: Retrieved chunks with metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Format chunk as numbered source
            source_block = f"""## Source {i}: {chunk.get('content_title', 'Untitled')}

**Author**: {chunk.get('content_author', 'Unknown')}
**URL**: {chunk.get('content_url', 'N/A')}
**Published**: {chunk.get('published_at', 'N/A')}
**Relevance Score**: {chunk.get('similarity', 0):.3f}

### Content:
{chunk.get('chunk_text', '')}

---
"""
            context_parts.append(source_block)

        return "\n".join(context_parts)

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from Claude's response.

        Args:
            response_text: Raw response text

        Returns:
            Parsed JSON dictionary
        """
        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        import re

        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding raw JSON object
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error(f"Could not extract JSON from response: {response_text[:500]}")
        raise ValueError("Failed to parse JSON from Claude response")

    def _validate_and_enrich_insights(
        self,
        insights_data: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate and enrich insights with additional metadata.

        Args:
            insights_data: Parsed insights from Claude
            retrieved_chunks: Original chunks for reference

        Returns:
            Validated and enriched insights list
        """
        insights = insights_data.get("insights", [])

        enriched = []

        for i, insight in enumerate(insights):
            # Generate unique ID
            insight["id"] = f"insight_{datetime.now().timestamp()}_{i}"

            # Ensure all required fields exist
            if not all(
                key in insight
                for key in ["title", "explanation", "practical_takeaway", "source"]
            ):
                logger.warning(f"Insight {i} missing required fields, skipping")
                continue

            # Add generation timestamp
            insight["generated_at"] = datetime.now().isoformat()

            # Ensure metadata exists
            if "metadata" not in insight:
                insight["metadata"] = {}

            # Add chunk references
            insight["metadata"]["source_chunks"] = [
                chunk["id"] for chunk in retrieved_chunks[:3]
            ]  # Top 3 chunks

            enriched.append(insight)

        return enriched


async def test_synthesizer(
    anthropic_api_key: str,
    sample_chunks: List[Dict[str, Any]],
) -> None:
    """
    Test synthesizer functionality.

    Args:
        anthropic_api_key: Anthropic API key
        sample_chunks: Sample chunks for testing
    """
    synthesizer = EducationalSynthesizer(api_key=anthropic_api_key)

    learning_context = {
        "current_week": 7,
        "current_topics": ["Attention Mechanisms", "Transformers", "Multi-Head Attention"],
        "difficulty_level": "intermediate",
        "learning_goals": "Build chatbot with RAG",
    }

    query = "Explain how attention mechanisms work in transformers"

    result = await synthesizer.synthesize_insights(
        retrieved_chunks=sample_chunks,
        learning_context=learning_context,
        query=query,
        num_insights=3,
    )

    print("\n" + "=" * 60)
    print("SYNTHESIZED INSIGHTS")
    print("=" * 60)

    for i, insight in enumerate(result["insights"], 1):
        print(f"\n{i}. {insight['title']}")
        print(f"\nRelevance: {insight.get('relevance_reason', 'N/A')}")
        print(f"\nExplanation:\n{insight['explanation'][:300]}...")
        print(f"\nTakeaway: {insight['practical_takeaway']}")
        print(f"\nSource: {insight['source']['title']}")
        print("-" * 60)


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Sample chunks for testing
    sample = [
        {
            "id": "test1",
            "content_title": "Attention Is All You Need",
            "content_author": "Vaswani et al.",
            "content_url": "https://arxiv.org/abs/1706.03762",
            "published_at": "2017-06-12",
            "similarity": 0.92,
            "chunk_text": "The Transformer model architecture eschews recurrence and instead relies entirely on an attention mechanism to draw global dependencies between input and output. The attention mechanism allows the model to focus on different parts of the input sequence when producing each element of the output sequence.",
        }
    ]

    import asyncio

    asyncio.run(
        test_synthesizer(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            sample_chunks=sample,
        )
    )
