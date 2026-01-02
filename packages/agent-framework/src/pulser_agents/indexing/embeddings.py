"""
Embedding providers for code indexing.

Supports multiple embedding backends:
- OpenAI embeddings
- Local embeddings (sentence-transformers)
- Custom providers
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configuration for embedding providers."""

    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    batch_size: int = 100
    cache_embeddings: bool = True
    api_key: str | None = None
    base_url: str | None = None


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    Provides interface for generating embeddings from text.
    """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        pass


class OpenAIEmbeddings(EmbeddingProvider):
    """
    OpenAI embedding provider.

    Uses OpenAI's text-embedding models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        base_url: str | None = None,
    ) -> None:
        """
        Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key
            model: Model name
            dimensions: Embedding dimensions
            base_url: Optional custom base URL
        """
        import os

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._dimensions = dimensions
        self.base_url = base_url or "https://api.openai.com/v1"
        self._cache: dict[str, list[float]] = {}

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        embeddings = await self.embed_batch([text])
        self._cache[cache_key] = embeddings[0]
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts."""
        if not texts:
            return []

        # Check cache for already embedded texts
        results = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        if not texts_to_embed:
            return results

        # Call OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": texts_to_embed,
                    "dimensions": self._dimensions,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        # Extract embeddings and cache
        for i, embedding_data in enumerate(data["data"]):
            embedding = embedding_data["embedding"]
            original_index = indices_to_embed[i]
            results[original_index] = embedding
            cache_key = self._cache_key(texts_to_embed[i])
            self._cache[cache_key] = embedding

        return results


class LocalEmbeddings(EmbeddingProvider):
    """
    Local embedding provider using sentence-transformers.

    Runs embeddings locally without API calls.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
    ) -> None:
        """
        Initialize local embeddings.

        Args:
            model_name: Sentence transformer model name
            device: Device to run on (cpu, cuda, mps)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dimensions = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._dimensions = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install with: pip install sentence-transformers"
                )

    @property
    def dimensions(self) -> int:
        self._load_model()
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts."""
        if not texts:
            return []

        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]


class CachedEmbeddings(EmbeddingProvider):
    """
    Wrapper that adds persistent caching to any embedding provider.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
        cache_path: str | None = None,
    ) -> None:
        """
        Initialize cached embeddings.

        Args:
            provider: Underlying embedding provider
            cache_path: Path to cache file
        """
        self.provider = provider
        self.cache_path = cache_path
        self._cache: dict[str, list[float]] = {}

        if cache_path:
            self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        import json
        from pathlib import Path

        path = Path(self.cache_path)
        if path.exists():
            try:
                with open(path) as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        import json
        from pathlib import Path

        if not self.cache_path:
            return

        path = Path(self.cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self._cache, f)

    def _cache_key(self, text: str) -> str:
        """Generate cache key."""
        return hashlib.md5(text.encode()).hexdigest()

    @property
    def dimensions(self) -> int:
        return self.provider.dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with caching."""
        key = self._cache_key(text)
        if key in self._cache:
            return self._cache[key]

        embedding = await self.provider.embed(text)
        self._cache[key] = embedding
        self._save_cache()
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with caching."""
        results = [None] * len(texts)
        texts_to_embed = []
        indices = []

        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self._cache:
                results[i] = self._cache[key]
            else:
                texts_to_embed.append(text)
                indices.append(i)

        if texts_to_embed:
            new_embeddings = await self.provider.embed_batch(texts_to_embed)
            for i, embedding in enumerate(new_embeddings):
                original_idx = indices[i]
                results[original_idx] = embedding
                key = self._cache_key(texts_to_embed[i])
                self._cache[key] = embedding

            self._save_cache()

        return results
