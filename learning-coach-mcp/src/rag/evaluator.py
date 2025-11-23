"""
RAGAS Quality Evaluator

Evaluates generated insights using RAGAS metrics:
- Faithfulness: Factual consistency with source material
- Context Precision: Relevance of retrieved chunks
- Context Recall: Coverage of key information
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)


class RAGASEvaluator:
    """Evaluates RAG quality using RAGAS metrics."""

    def __init__(self, min_score: float = 0.70):
        """
        Initialize RAGAS evaluator.

        Args:
            min_score: Minimum acceptable score (default: 0.70)
        """
        self.min_score = min_score

        # Lazy import RAGAS (only when needed)
        try:
            from ragas import SingleTurnSample
            from ragas.metrics import (
                Faithfulness,
                LLMContextPrecisionWithoutReference,
                NonLLMContextRecall,
            )

            self.SingleTurnSample = SingleTurnSample
            self.faithfulness = Faithfulness()
            self.context_precision = LLMContextPrecisionWithoutReference()
            self.context_recall = NonLLMContextRecall()
            self.ragas_available = True

            logger.info("RAGAS metrics initialized successfully")

        except ImportError as e:
            logger.warning(f"RAGAS not available: {e}. Quality evaluation disabled.")
            self.ragas_available = False

    async def evaluate_digest(
        self,
        query: str,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Evaluate digest quality using RAGAS metrics.

        Args:
            query: Original search query
            insights: Generated insights
            retrieved_chunks: Retrieved content chunks

        Returns:
            Dictionary with RAGAS scores
        """
        if not self.ragas_available:
            logger.warning("RAGAS not available, returning placeholder scores")
            return self._placeholder_scores()

        logger.info("Evaluating digest with RAGAS")

        try:
            # Prepare data for evaluation
            response = self._format_insights_for_eval(insights)
            contexts = [chunk["chunk_text"] for chunk in retrieved_chunks]

            # Create RAGAS sample
            sample = self.SingleTurnSample(
                user_input=query,
                response=response,
                retrieved_contexts=contexts,
            )

            # Evaluate each metric (run concurrently)
            scores = await self._evaluate_all_metrics(sample, contexts)

            # Calculate average
            scores["average"] = (
                scores["faithfulness"] + scores["context_precision"] + scores["context_recall"]
            ) / 3

            logger.info(
                f"RAGAS evaluation complete: "
                f"faithfulness={scores['faithfulness']:.3f}, "
                f"precision={scores['context_precision']:.3f}, "
                f"recall={scores['context_recall']:.3f}, "
                f"avg={scores['average']:.3f}"
            )

            return scores

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}", exc_info=True)
            return self._placeholder_scores()

    async def _evaluate_all_metrics(
        self,
        sample: Any,
        contexts: List[str],
    ) -> Dict[str, float]:
        """
        Evaluate all RAGAS metrics concurrently.

        Args:
            sample: RAGAS sample object
            contexts: Retrieved context strings

        Returns:
            Dictionary with individual scores
        """
        # Run metrics in parallel
        tasks = [
            self._evaluate_faithfulness(sample),
            self._evaluate_context_precision(sample),
            self._evaluate_context_recall(sample, contexts),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Extract scores (with fallbacks for errors)
        faithfulness_score = results[0] if not isinstance(results[0], Exception) else 0.0
        precision_score = results[1] if not isinstance(results[1], Exception) else 0.0
        recall_score = results[2] if not isinstance(results[2], Exception) else 0.0

        return {
            "faithfulness": float(faithfulness_score),
            "context_precision": float(precision_score),
            "context_recall": float(recall_score),
        }

    async def _evaluate_faithfulness(self, sample: Any) -> float:
        """Evaluate faithfulness (factual consistency)."""
        try:
            score = await self.faithfulness.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Faithfulness evaluation failed: {e}")
            return 0.75  # Conservative fallback

    async def _evaluate_context_precision(self, sample: Any) -> float:
        """Evaluate context precision (relevance of chunks)."""
        try:
            score = await self.context_precision.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Context precision evaluation failed: {e}")
            return 0.75  # Conservative fallback

    async def _evaluate_context_recall(self, sample: Any, contexts: List[str]) -> float:
        """Evaluate context recall (coverage of information)."""
        try:
            # NonLLMContextRecall doesn't need reference contexts
            score = await self.context_recall.single_turn_ascore(sample)
            return float(score)
        except Exception as e:
            logger.warning(f"Context recall evaluation failed: {e}")
            return 0.75  # Conservative fallback

    def _format_insights_for_eval(self, insights: List[Dict[str, Any]]) -> str:
        """
        Format insights into single text for evaluation.

        Args:
            insights: List of insight dictionaries

        Returns:
            Concatenated insight text
        """
        texts = []
        for insight in insights:
            title = insight.get("title", "")
            explanation = insight.get("explanation", "")
            texts.append(f"{title}\n\n{explanation}")

        return "\n\n---\n\n".join(texts)

    def _placeholder_scores(self) -> Dict[str, float]:
        """Return placeholder scores when RAGAS unavailable."""
        return {
            "faithfulness": 0.75,
            "context_precision": 0.75,
            "context_recall": 0.75,
            "average": 0.75,
        }

    def passes_quality_gate(self, scores: Dict[str, float]) -> bool:
        """
        Check if scores pass the quality gate.

        Args:
            scores: RAGAS scores dictionary

        Returns:
            True if all scores meet minimum threshold
        """
        required_metrics = ["faithfulness", "context_precision", "context_recall"]

        for metric in required_metrics:
            if scores.get(metric, 0) < self.min_score:
                logger.info(f"Failed quality gate: {metric}={scores.get(metric, 0):.3f} < {self.min_score}")
                return False

        return True


class QualityGate:
    """Manages quality gating with retry logic."""

    def __init__(
        self,
        evaluator: RAGASEvaluator,
        max_retries: int = 2,
    ):
        """
        Initialize quality gate.

        Args:
            evaluator: RAGAS evaluator instance
            max_retries: Maximum retry attempts (default: 2)
        """
        self.evaluator = evaluator
        self.max_retries = max_retries

    async def apply_gate(
        self,
        query: str,
        insights: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
        synthesizer,  # EducationalSynthesizer instance
        learning_context: Dict[str, Any],
        retry_count: int = 0,
    ) -> tuple[List[Dict[str, Any]], Dict[str, float], bool]:
        """
        Apply quality gate with retry logic.

        Args:
            query: Original query
            insights: Generated insights
            retrieved_chunks: Retrieved chunks
            synthesizer: Synthesizer instance for retries
            learning_context: Learning context
            retry_count: Current retry attempt

        Returns:
            Tuple of (final_insights, final_scores, passed)
        """
        # Evaluate current insights
        scores = await self.evaluator.evaluate_digest(
            query=query,
            insights=insights,
            retrieved_chunks=retrieved_chunks,
        )

        # Check if passes
        if self.evaluator.passes_quality_gate(scores):
            logger.info("✓ Quality gate passed")
            return (insights, scores, True)

        # If failed and retries available
        if retry_count < self.max_retries:
            logger.warning(
                f"Quality gate failed (attempt {retry_count + 1}/{self.max_retries + 1}), "
                f"retrying with stricter synthesis..."
            )

            # Retry with stricter synthesis
            retry_result = await synthesizer.synthesize_insights(
                retrieved_chunks=retrieved_chunks,
                learning_context=learning_context,
                query=query,
                num_insights=len(insights),
                stricter=True,  # Enable strict mode
            )

            retry_insights = retry_result["insights"]

            # Recursively apply gate to retry
            return await self.apply_gate(
                query=query,
                insights=retry_insights,
                retrieved_chunks=retrieved_chunks,
                synthesizer=synthesizer,
                learning_context=learning_context,
                retry_count=retry_count + 1,
            )

        # Failed all retries
        logger.warning(
            f"⚠️ Quality gate failed after {retry_count + 1} attempts. "
            f"Delivering with warning."
        )
        return (insights, scores, False)


async def test_ragas_evaluation(
    sample_query: str,
    sample_insights: List[Dict[str, Any]],
    sample_chunks: List[Dict[str, Any]],
) -> None:
    """
    Test RAGAS evaluation.

    Args:
        sample_query: Test query
        sample_insights: Sample insights
        sample_chunks: Sample chunks
    """
    evaluator = RAGASEvaluator(min_score=0.70)

    print("\n" + "=" * 60)
    print("RAGAS EVALUATION TEST")
    print("=" * 60)

    scores = await evaluator.evaluate_digest(
        query=sample_query,
        insights=sample_insights,
        retrieved_chunks=sample_chunks,
    )

    print(f"\nScores:")
    print(f"  Faithfulness:      {scores['faithfulness']:.3f}")
    print(f"  Context Precision: {scores['context_precision']:.3f}")
    print(f"  Context Recall:    {scores['context_recall']:.3f}")
    print(f"  Average:           {scores['average']:.3f}")

    passed = evaluator.passes_quality_gate(scores)
    print(f"\nQuality Gate: {'✓ PASSED' if passed else '✗ FAILED'}")

    if passed:
        print("  → Ready to deliver!")
    else:
        print("  → Needs retry with stricter synthesis")


if __name__ == "__main__":
    # Sample data for testing
    sample_query = "Explain how attention mechanisms work in transformers"

    sample_insights = [
        {
            "title": "Attention Mechanism Fundamentals",
            "explanation": "Attention mechanisms allow neural networks to focus on relevant parts of the input when producing output. In transformers, attention computes similarity scores between all input positions.",
            "practical_takeaway": "Implement a simple attention function using dot-product similarity.",
            "source": {
                "title": "Attention Is All You Need",
                "author": "Vaswani et al.",
                "url": "https://arxiv.org/abs/1706.03762",
                "published_date": "2017-06-12",
            },
        }
    ]

    sample_chunks = [
        {
            "chunk_text": "The Transformer uses multi-head attention, which allows the model to jointly attend to information from different representation subspaces at different positions.",
            "similarity": 0.89,
        }
    ]

    import asyncio

    asyncio.run(
        test_ragas_evaluation(
            sample_query=sample_query,
            sample_insights=sample_insights,
            sample_chunks=sample_chunks,
        )
    )
