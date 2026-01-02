"""
Vector storage backends for codebase indexing.

Supports multiple storage backends:
- In-memory storage
- File-based persistence
- Redis/Turbopuffer (future)
"""

from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pulser_agents.indexing.chunker import Chunk


@dataclass
class SearchResult:
    """
    Result from a vector search.

    Attributes:
        chunk: The matched chunk
        score: Similarity score (0-1)
        rank: Result rank
    """

    chunk: Chunk
    score: float
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk.id,
            "file_path": self.chunk.metadata.file_path,
            "content": self.chunk.content,
            "score": self.score,
            "rank": self.rank,
            "start_line": self.chunk.metadata.start_line,
            "end_line": self.chunk.metadata.end_line,
        }


class VectorStorage(ABC):
    """
    Abstract base class for vector storage.

    Provides interface for storing and searching embeddings.
    """

    @abstractmethod
    async def add(self, chunk: Chunk) -> None:
        """Add a chunk with embedding to storage."""
        pass

    @abstractmethod
    async def add_batch(self, chunks: list[Chunk]) -> None:
        """Add multiple chunks to storage."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Optional filters (e.g., file_path)

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def delete(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all chunks."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Get total chunk count."""
        pass


class InMemoryVectorStorage(VectorStorage):
    """
    In-memory vector storage with cosine similarity search.

    Good for development and small codebases.
    """

    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._embeddings: dict[str, list[float]] = {}

    async def add(self, chunk: Chunk) -> None:
        """Add a chunk to storage."""
        if chunk.embedding is None:
            raise ValueError("Chunk must have embedding")

        self._chunks[chunk.id] = chunk
        self._embeddings[chunk.id] = chunk.embedding

    async def add_batch(self, chunks: list[Chunk]) -> None:
        """Add multiple chunks."""
        for chunk in chunks:
            await self.add(chunk)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search using cosine similarity."""
        if not self._embeddings:
            return []

        scores = []
        for chunk_id, embedding in self._embeddings.items():
            chunk = self._chunks[chunk_id]

            # Apply filters
            if filters:
                if "file_path" in filters:
                    if not chunk.metadata.file_path.startswith(filters["file_path"]):
                        continue
                if "language" in filters:
                    if chunk.metadata.language != filters["language"]:
                        continue
                if "chunk_type" in filters:
                    if chunk.metadata.chunk_type.value != filters["chunk_type"]:
                        continue

            score = self._cosine_similarity(query_embedding, embedding)
            scores.append((chunk_id, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top k results
        results = []
        for rank, (chunk_id, score) in enumerate(scores[:top_k]):
            results.append(
                SearchResult(
                    chunk=self._chunks[chunk_id],
                    score=score,
                    rank=rank,
                )
            )

        return results

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def delete(self, chunk_id: str) -> bool:
        """Delete a chunk."""
        if chunk_id in self._chunks:
            del self._chunks[chunk_id]
            del self._embeddings[chunk_id]
            return True
        return False

    async def clear(self) -> None:
        """Clear all data."""
        self._chunks.clear()
        self._embeddings.clear()

    async def count(self) -> int:
        """Get chunk count."""
        return len(self._chunks)

    async def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Get a specific chunk."""
        return self._chunks.get(chunk_id)

    async def get_chunks_by_file(self, file_path: str) -> list[Chunk]:
        """Get all chunks for a file."""
        return [
            chunk
            for chunk in self._chunks.values()
            if chunk.metadata.file_path == file_path
        ]


class FileVectorStorage(VectorStorage):
    """
    File-based vector storage with JSON persistence.

    Persists index to disk for durability.
    """

    def __init__(self, storage_path: str | Path) -> None:
        """
        Initialize file storage.

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._index_file = self.storage_path / "index.json"
        self._embeddings_file = self.storage_path / "embeddings.json"

        self._memory = InMemoryVectorStorage()
        self._load()

    def _load(self) -> None:
        """Load data from disk."""
        if self._index_file.exists() and self._embeddings_file.exists():
            try:
                with open(self._index_file) as f:
                    index_data = json.load(f)
                with open(self._embeddings_file) as f:
                    embeddings_data = json.load(f)

                for chunk_id, chunk_data in index_data.items():
                    from pulser_agents.indexing.chunker import (
                        Chunk,
                        ChunkMetadata,
                        ChunkType,
                    )

                    metadata = ChunkMetadata(
                        file_path=chunk_data["file_path"],
                        start_line=chunk_data["start_line"],
                        end_line=chunk_data["end_line"],
                        chunk_type=ChunkType(chunk_data["chunk_type"]),
                        language=chunk_data.get("language"),
                        symbol_name=chunk_data.get("symbol_name"),
                    )
                    chunk = Chunk(
                        id=chunk_id,
                        content=chunk_data["content"],
                        metadata=metadata,
                        embedding=embeddings_data.get(chunk_id),
                    )
                    self._memory._chunks[chunk_id] = chunk
                    if chunk.embedding:
                        self._memory._embeddings[chunk_id] = chunk.embedding
            except Exception:
                # If loading fails, start fresh
                pass

    def _save(self) -> None:
        """Save data to disk."""
        index_data = {}
        embeddings_data = {}

        for chunk_id, chunk in self._memory._chunks.items():
            index_data[chunk_id] = chunk.to_dict()
            if chunk_id in self._memory._embeddings:
                embeddings_data[chunk_id] = self._memory._embeddings[chunk_id]

        with open(self._index_file, "w") as f:
            json.dump(index_data, f)
        with open(self._embeddings_file, "w") as f:
            json.dump(embeddings_data, f)

    async def add(self, chunk: Chunk) -> None:
        await self._memory.add(chunk)
        self._save()

    async def add_batch(self, chunks: list[Chunk]) -> None:
        await self._memory.add_batch(chunks)
        self._save()

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        return await self._memory.search(query_embedding, top_k, filters)

    async def delete(self, chunk_id: str) -> bool:
        result = await self._memory.delete(chunk_id)
        if result:
            self._save()
        return result

    async def clear(self) -> None:
        await self._memory.clear()
        self._save()

    async def count(self) -> int:
        return await self._memory.count()
