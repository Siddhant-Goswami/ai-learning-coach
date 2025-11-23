"""
Text Chunking for RAG

Splits text into overlapping chunks while respecting sentence boundaries.
"""

import logging
import re
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""

    chunk_index: int
    total_chunks: int
    estimated_tokens: int
    has_code: bool = False
    section_heading: str = ""


class TextChunker:
    """Chunks text into overlapping segments for embedding."""

    def __init__(
        self,
        chunk_size: int = 750,
        overlap: int = 100,
        min_chunk_size: int = 100,
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in tokens (default: 750)
            overlap: Number of tokens to overlap between chunks (default: 100)
            min_chunk_size: Minimum chunk size to keep (default: 100)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

        # Sentence boundary regex
        self.sentence_regex = re.compile(r"[.!?]+\s+")

        # Code block detection regex
        self.code_block_regex = re.compile(r"```[\s\S]*?```|`[^`]+`")

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for chunking")
            return []

        # Detect code blocks
        code_blocks = self._extract_code_blocks(text)

        # Split into sentences
        sentences = self._split_sentences(text)

        if not sentences:
            logger.warning("No sentences found in text")
            return []

        # Create chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If this sentence alone exceeds chunk size, split it further
            if sentence_tokens > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence into smaller pieces
                sub_chunks = self._split_long_sentence(sentence)
                for sub_chunk in sub_chunks:
                    chunks.append(
                        self._create_chunk([sub_chunk], chunk_index, metadata, is_split=True)
                    )
                    chunk_index += 1

                continue

            # Check if adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk from current sentences
                chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))
                chunk_index += 1

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, self.overlap
                )
                current_chunk = overlap_sentences
                current_tokens = sum(self._estimate_tokens(s) for s in overlap_sentences)

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk if it has content
        if current_chunk and current_tokens >= self.min_chunk_size:
            chunks.append(self._create_chunk(current_chunk, chunk_index, metadata))

        # Update total chunks in metadata
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = len(chunks)

        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, preserving paragraph structure.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split by sentence boundaries
        sentences = self.sentence_regex.split(text)

        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token on average
        return len(text) // 4

    def _get_overlap_sentences(self, sentences: List[str], target_overlap: int) -> List[str]:
        """
        Get last few sentences to use as overlap for next chunk.

        Args:
            sentences: List of sentences
            target_overlap: Target overlap in tokens

        Returns:
            List of sentences for overlap
        """
        overlap_sentences = []
        overlap_tokens = 0

        # Work backwards from end
        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            if overlap_tokens + sentence_tokens > target_overlap:
                break
            overlap_sentences.insert(0, sentence)
            overlap_tokens += sentence_tokens

        return overlap_sentences

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        Split a very long sentence into smaller pieces.

        Args:
            sentence: Long sentence to split

        Returns:
            List of smaller text pieces
        """
        # Split on commas, semicolons, or conjunctions
        parts = re.split(r"[,;]|\s+(?:and|or|but)\s+", sentence)

        chunks = []
        current = ""

        for part in parts:
            if self._estimate_tokens(current + part) > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                current = part
            else:
                current += (" " if current else "") + part

        if current:
            chunks.append(current.strip())

        return chunks if chunks else [sentence]

    def _extract_code_blocks(self, text: str) -> List[str]:
        """
        Extract code blocks from text.

        Args:
            text: Text containing code blocks

        Returns:
            List of code blocks
        """
        matches = self.code_block_regex.findall(text)
        return matches

    def _create_chunk(
        self,
        sentences: List[str],
        chunk_index: int,
        base_metadata: Dict[str, Any] = None,
        is_split: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a chunk dictionary with metadata.

        Args:
            sentences: List of sentences for this chunk
            chunk_index: Index of this chunk
            base_metadata: Base metadata to include
            is_split: Whether this chunk is from a split long sentence

        Returns:
            Chunk dictionary
        """
        chunk_text = " ".join(sentences)
        estimated_tokens = self._estimate_tokens(chunk_text)

        # Check if chunk contains code
        has_code = bool(self.code_block_regex.search(chunk_text))

        metadata = {
            "chunk_index": chunk_index,
            "total_chunks": 0,  # Will be updated later
            "estimated_tokens": estimated_tokens,
            "has_code": has_code,
            "is_split": is_split,
        }

        # Merge with base metadata
        if base_metadata:
            metadata.update(base_metadata)

        return {
            "chunk_text": chunk_text,
            "chunk_sequence": chunk_index,
            "metadata": metadata,
        }


def chunk_document(
    document: Dict[str, Any],
    chunk_size: int = 750,
    overlap: int = 100,
) -> List[Dict[str, Any]]:
    """
    Convenience function to chunk a document.

    Args:
        document: Document dict with 'content' and optional metadata
        chunk_size: Target chunk size in tokens
        overlap: Overlap size in tokens

    Returns:
        List of chunks with metadata
    """
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)

    metadata = {
        "document_title": document.get("title", ""),
        "document_url": document.get("url", ""),
        "document_author": document.get("author", ""),
    }

    chunks = chunker.chunk_text(document.get("content", ""), metadata)

    return chunks
