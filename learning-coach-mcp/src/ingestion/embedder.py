"""
Embedding Generation

Generates vector embeddings for text chunks using OpenAI API.
"""

import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
import asyncio

logger = logging.getLogger(__name__)


class Embedder:
    """Generates vector embeddings for text."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        batch_size: int = 100,
    ):
        """
        Initialize embedder.

        Args:
            api_key: OpenAI API key
            model: Embedding model name (default: text-embedding-3-small)
            dimensions: Embedding dimensions (default: 1536)
            batch_size: Number of texts to embed in one API call (default: 100)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If API call fails
        """
        if not texts:
            return []

        logger.info(f"Generating embeddings for {len(texts)} texts")

        try:
            # Process in batches to avoid API limits
            all_embeddings = []

            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                batch_embeddings = await self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

                logger.debug(
                    f"Processed batch {i // self.batch_size + 1}/{(len(texts) - 1) // self.batch_size + 1}"
                )

            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            raise

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a single batch of texts.

        Args:
            texts: List of texts (max batch_size)

        Returns:
            List of embedding vectors
        """
        # Clean texts (remove excessive whitespace, ensure not empty)
        cleaned_texts = [self._clean_text(text) for text in texts]

        # Call OpenAI API
        response = await self.client.embeddings.create(
            model=self.model,
            input=cleaned_texts,
            dimensions=self.dimensions,
        )

        # Extract embeddings in order
        embeddings = [item.embedding for item in response.data]

        return embeddings

    def _clean_text(self, text: str) -> str:
        """
        Clean text before embedding.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return " "  # OpenAI API requires non-empty string

        # Remove excessive whitespace
        cleaned = " ".join(text.split())

        # Truncate if too long (8191 tokens max for text-embedding-3-small)
        max_chars = 32000  # Conservative estimate (4 chars/token)
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
            logger.warning(f"Truncated text from {len(text)} to {max_chars} chars")

        return cleaned

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of chunk dictionaries.

        Args:
            chunks: List of chunk dicts with 'chunk_text' field

        Returns:
            List of chunks with 'embedding' field added
        """
        # Extract texts
        texts = [chunk["chunk_text"] for chunk in chunks]

        # Generate embeddings
        embeddings = await self.generate_embeddings(texts)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        return chunks


async def embed_documents(
    documents: List[Dict[str, Any]],
    api_key: str,
    model: str = "text-embedding-3-small",
    dimensions: int = 1536,
) -> List[Dict[str, Any]]:
    """
    Convenience function to embed multiple documents.

    Args:
        documents: List of document dicts with 'content' field
        api_key: OpenAI API key
        model: Embedding model
        dimensions: Embedding dimensions

    Returns:
        List of documents with 'embedding' field added
    """
    embedder = Embedder(api_key=api_key, model=model, dimensions=dimensions)

    # Extract content texts
    texts = [doc.get("content", "") for doc in documents]

    # Generate embeddings
    embeddings = await embedder.generate_embeddings(texts)

    # Add embeddings to documents
    for doc, embedding in zip(documents, embeddings):
        doc["embedding"] = embedding

    return documents
