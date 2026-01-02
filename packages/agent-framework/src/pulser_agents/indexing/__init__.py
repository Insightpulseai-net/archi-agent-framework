"""
Codebase Indexing System for Pulser Agent Framework.

Implements semantic codebase indexing with:
- Intelligent chunking (function/class-aware)
- Embedding generation
- Vector storage with multiple backends
- Semantic search
- Merkle tree sync for incremental updates

Example:
    >>> from pulser_agents.indexing import CodebaseIndexer, VectorIndex
    >>>
    >>> indexer = CodebaseIndexer()
    >>> index = await indexer.index_directory("/path/to/project")
    >>>
    >>> # Search the codebase
    >>> results = await index.search("user authentication logic")
"""

from pulser_agents.indexing.chunker import (
    CodeChunker,
    Chunk,
    ChunkType,
    ChunkMetadata,
)
from pulser_agents.indexing.embeddings import (
    EmbeddingProvider,
    OpenAIEmbeddings,
    LocalEmbeddings,
)
from pulser_agents.indexing.indexer import CodebaseIndexer, IndexConfig
from pulser_agents.indexing.storage import (
    VectorStorage,
    InMemoryVectorStorage,
    SearchResult,
)
from pulser_agents.indexing.search import SemanticSearch

__all__ = [
    # Chunking
    "CodeChunker",
    "Chunk",
    "ChunkType",
    "ChunkMetadata",
    # Embeddings
    "EmbeddingProvider",
    "OpenAIEmbeddings",
    "LocalEmbeddings",
    # Indexing
    "CodebaseIndexer",
    "IndexConfig",
    # Storage
    "VectorStorage",
    "InMemoryVectorStorage",
    "SearchResult",
    # Search
    "SemanticSearch",
]
