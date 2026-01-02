"""
Main codebase indexer implementation.

Coordinates chunking, embedding, and storage.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from pulser_agents.indexing.chunker import Chunk, CodeChunker
from pulser_agents.indexing.embeddings import EmbeddingProvider, OpenAIEmbeddings
from pulser_agents.indexing.storage import (
    InMemoryVectorStorage,
    SearchResult,
    VectorStorage,
)


class IndexConfig(BaseModel):
    """Configuration for codebase indexing."""

    # Chunking settings
    max_chunk_size: int = 1500
    min_chunk_size: int = 100
    chunk_overlap: int = 50
    respect_boundaries: bool = True

    # File settings
    extensions: list[str] = Field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".go",
            ".rs",
            ".java",
            ".rb",
            ".php",
            ".md",
        ]
    )
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".next",
            "target",
            ".pytest_cache",
            ".mypy_cache",
        ]
    )

    # Embedding settings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    batch_size: int = 50

    # Storage settings
    storage_path: str | None = None


@dataclass
class IndexStats:
    """Statistics about an index."""

    total_files: int = 0
    total_chunks: int = 0
    total_characters: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    index_time_ms: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class CodebaseIndexer:
    """
    Main indexer for codebases.

    Handles:
    - File discovery
    - Intelligent chunking
    - Embedding generation
    - Vector storage
    - Incremental updates

    Example:
        >>> indexer = CodebaseIndexer()
        >>> await indexer.index_directory("/path/to/project")
        >>> results = await indexer.search("authentication logic")
    """

    def __init__(
        self,
        config: IndexConfig | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        storage: VectorStorage | None = None,
    ) -> None:
        """
        Initialize the indexer.

        Args:
            config: Index configuration
            embedding_provider: Embedding provider to use
            storage: Vector storage backend
        """
        self.config = config or IndexConfig()
        self.embedding_provider = embedding_provider
        self.storage = storage or InMemoryVectorStorage()
        self.chunker = CodeChunker(
            max_chunk_size=self.config.max_chunk_size,
            min_chunk_size=self.config.min_chunk_size,
            overlap=self.config.chunk_overlap,
            respect_boundaries=self.config.respect_boundaries,
        )

        self._stats = IndexStats()
        self._file_hashes: dict[str, str] = {}

    async def _ensure_embedding_provider(self) -> None:
        """Ensure we have an embedding provider."""
        if self.embedding_provider is None:
            self.embedding_provider = OpenAIEmbeddings(
                model=self.config.embedding_model,
                dimensions=self.config.embedding_dimensions,
            )

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute hash of file contents."""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]

    async def index_file(
        self,
        file_path: str | Path,
        content: str | None = None,
        force: bool = False,
    ) -> list[Chunk]:
        """
        Index a single file.

        Args:
            file_path: Path to file
            content: Optional file content
            force: Force re-indexing even if unchanged

        Returns:
            List of indexed chunks
        """
        await self._ensure_embedding_provider()

        path = Path(file_path)
        path_str = str(path)

        # Check if file has changed
        if not force and path.exists():
            current_hash = self._compute_file_hash(path)
            if self._file_hashes.get(path_str) == current_hash:
                return []
            self._file_hashes[path_str] = current_hash

        # Chunk the file
        chunks = self.chunker.chunk_file(path_str, content)

        if not chunks:
            return []

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_provider.embed_batch(texts)

        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        # Store chunks
        await self.storage.add_batch(chunks)

        # Update stats
        self._stats.total_chunks += len(chunks)
        self._stats.total_characters += sum(len(c.content) for c in chunks)
        for chunk in chunks:
            lang = chunk.metadata.language or "unknown"
            self._stats.languages[lang] = self._stats.languages.get(lang, 0) + 1

        return chunks

    async def index_directory(
        self,
        directory: str | Path,
        force: bool = False,
        progress_callback: Any | None = None,
    ) -> IndexStats:
        """
        Index all files in a directory.

        Args:
            directory: Directory to index
            force: Force re-indexing all files
            progress_callback: Optional progress callback

        Returns:
            Index statistics
        """
        await self._ensure_embedding_provider()

        start_time = time.time()
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Find all files
        files = []
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check extension
            if file_path.suffix.lower() not in self.config.extensions:
                continue

            # Check ignore patterns
            path_str = str(file_path)
            if any(pattern in path_str for pattern in self.config.ignore_patterns):
                continue

            files.append(file_path)

        self._stats.total_files = len(files)

        # Index files in batches
        batch_size = self.config.batch_size
        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]

            for file_path in batch:
                try:
                    await self.index_file(file_path, force=force)
                except Exception:
                    # Skip files that fail
                    continue

            if progress_callback:
                progress = min(i + batch_size, len(files)) / len(files)
                progress_callback(progress)

        self._stats.index_time_ms = (time.time() - start_time) * 1000
        self._stats.last_updated = datetime.utcnow()

        return self._stats

    async def search(
        self,
        query: str,
        top_k: int = 10,
        file_path: str | None = None,
        language: str | None = None,
    ) -> list[SearchResult]:
        """
        Search the indexed codebase.

        Args:
            query: Search query
            top_k: Number of results
            file_path: Filter by file path prefix
            language: Filter by language

        Returns:
            List of search results
        """
        await self._ensure_embedding_provider()

        # Generate query embedding
        query_embedding = await self.embedding_provider.embed(query)

        # Build filters
        filters = {}
        if file_path:
            filters["file_path"] = file_path
        if language:
            filters["language"] = language

        # Search
        results = await self.storage.search(
            query_embedding,
            top_k=top_k,
            filters=filters if filters else None,
        )

        return results

    async def remove_file(self, file_path: str | Path) -> int:
        """
        Remove a file from the index.

        Args:
            file_path: Path to file

        Returns:
            Number of chunks removed
        """
        path_str = str(file_path)

        # Find and delete all chunks for this file
        if hasattr(self.storage, "get_chunks_by_file"):
            chunks = await self.storage.get_chunks_by_file(path_str)
            for chunk in chunks:
                await self.storage.delete(chunk.id)
            return len(chunks)

        return 0

    async def clear(self) -> None:
        """Clear the entire index."""
        await self.storage.clear()
        self._file_hashes.clear()
        self._stats = IndexStats()

    async def get_stats(self) -> IndexStats:
        """Get index statistics."""
        self._stats.total_chunks = await self.storage.count()
        return self._stats

    async def refresh(
        self,
        directory: str | Path,
        progress_callback: Any | None = None,
    ) -> IndexStats:
        """
        Refresh the index, only updating changed files.

        Args:
            directory: Directory to refresh
            progress_callback: Optional progress callback

        Returns:
            Updated statistics
        """
        return await self.index_directory(
            directory,
            force=False,
            progress_callback=progress_callback,
        )
