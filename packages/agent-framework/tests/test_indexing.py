"""
Tests for the Codebase Indexing System.
"""

import pytest
from pathlib import Path
import tempfile

from pulser_agents.indexing import (
    CodeChunker,
    Chunk,
    ChunkType,
    ChunkMetadata,
    InMemoryVectorStorage,
    SearchResult,
    IndexConfig,
)


class TestChunkMetadata:
    """Tests for ChunkMetadata."""

    def test_metadata_creation(self):
        """Test basic metadata creation."""
        metadata = ChunkMetadata(
            file_path="src/main.py",
            start_line=1,
            end_line=10,
            chunk_type=ChunkType.FUNCTION,
            language="python",
        )
        assert metadata.file_path == "src/main.py"
        assert metadata.start_line == 1
        assert metadata.end_line == 10
        assert metadata.chunk_type == ChunkType.FUNCTION
        assert metadata.language == "python"


class TestChunk:
    """Tests for Chunk."""

    def test_chunk_creation(self):
        """Test chunk creation with auto ID."""
        metadata = ChunkMetadata(
            file_path="test.py",
            start_line=1,
            end_line=5,
            chunk_type=ChunkType.BLOCK,
        )
        chunk = Chunk(content="def hello(): pass", metadata=metadata)

        assert chunk.content == "def hello(): pass"
        assert chunk.id  # Auto-generated
        assert chunk.line_count == 5
        assert chunk.char_count == 17

    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        metadata = ChunkMetadata(
            file_path="test.py",
            start_line=1,
            end_line=1,
            chunk_type=ChunkType.FUNCTION,
            language="python",
        )
        chunk = Chunk(content="pass", metadata=metadata)
        data = chunk.to_dict()

        assert data["file_path"] == "test.py"
        assert data["content"] == "pass"
        assert data["chunk_type"] == "function"


class TestCodeChunker:
    """Tests for CodeChunker."""

    def test_detect_language(self):
        """Test language detection from extensions."""
        chunker = CodeChunker()

        assert chunker.detect_language("test.py") == "python"
        assert chunker.detect_language("test.js") == "javascript"
        assert chunker.detect_language("test.ts") == "typescript"
        assert chunker.detect_language("test.go") == "go"
        assert chunker.detect_language("test.rs") == "rust"
        assert chunker.detect_language("test.unknown") is None

    def test_chunk_simple_file(self):
        """Test chunking a simple file."""
        chunker = CodeChunker(max_chunk_size=100, min_chunk_size=10)

        content = """def hello():
    print("Hello")

def world():
    print("World")
"""
        chunks = chunker.chunk_file("test.py", content)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.file_path == "test.py"
            assert chunk.metadata.language == "python"

    def test_chunk_respects_boundaries(self):
        """Test chunking respects function boundaries."""
        chunker = CodeChunker(
            max_chunk_size=500,
            min_chunk_size=10,
            respect_boundaries=True,
        )

        content = """class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass

def standalone():
    pass
"""
        chunks = chunker.chunk_file("test.py", content)
        assert len(chunks) >= 1

    def test_chunk_large_file_splits(self):
        """Test large files are split into multiple chunks."""
        chunker = CodeChunker(max_chunk_size=50, min_chunk_size=10)

        # Create content larger than max_chunk_size
        content = "\n".join([f"line {i}" for i in range(100)])
        chunks = chunker.chunk_file("test.txt", content)

        assert len(chunks) > 1

    def test_chunk_directory(self):
        """Test chunking entire directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "main.py").write_text("def main(): pass")
            (Path(tmpdir) / "utils.py").write_text("def util(): pass")
            (Path(tmpdir) / "readme.txt").write_text("Just a readme")

            chunker = CodeChunker()
            chunks = chunker.chunk_directory(
                tmpdir,
                extensions=[".py"],
            )

            # Should only include .py files
            assert len(chunks) == 2
            files = {c.metadata.file_path for c in chunks}
            assert any("main.py" in f for f in files)
            assert any("utils.py" in f for f in files)


class TestInMemoryVectorStorage:
    """Tests for InMemoryVectorStorage."""

    @pytest.fixture
    def storage(self):
        return InMemoryVectorStorage()

    @pytest.fixture
    def sample_chunk(self):
        metadata = ChunkMetadata(
            file_path="test.py",
            start_line=1,
            end_line=5,
            chunk_type=ChunkType.FUNCTION,
            language="python",
        )
        return Chunk(
            content="def hello(): pass",
            metadata=metadata,
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        )

    @pytest.mark.asyncio
    async def test_add_and_count(self, storage, sample_chunk):
        """Test adding chunks and counting."""
        await storage.add(sample_chunk)
        count = await storage.count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_add_batch(self, storage):
        """Test adding multiple chunks."""
        chunks = []
        for i in range(5):
            metadata = ChunkMetadata(
                file_path=f"file{i}.py",
                start_line=1,
                end_line=1,
                chunk_type=ChunkType.BLOCK,
            )
            chunks.append(Chunk(
                content=f"content {i}",
                metadata=metadata,
                embedding=[float(i)] * 5,
            ))

        await storage.add_batch(chunks)
        count = await storage.count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_search(self, storage, sample_chunk):
        """Test vector search."""
        await storage.add(sample_chunk)

        # Search with similar vector
        results = await storage.search(
            query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            top_k=5,
        )

        assert len(results) == 1
        assert results[0].chunk.id == sample_chunk.id
        assert results[0].score > 0.99  # Should be very similar

    @pytest.mark.asyncio
    async def test_search_with_filter(self, storage):
        """Test search with filters."""
        # Add chunks with different languages
        for lang in ["python", "javascript", "python"]:
            metadata = ChunkMetadata(
                file_path=f"test.{lang[:2]}",
                start_line=1,
                end_line=1,
                chunk_type=ChunkType.BLOCK,
                language=lang,
            )
            await storage.add(Chunk(
                content="test",
                metadata=metadata,
                embedding=[0.1] * 5,
            ))

        results = await storage.search(
            query_embedding=[0.1] * 5,
            top_k=10,
            filters={"language": "python"},
        )

        assert len(results) == 2
        assert all(r.chunk.metadata.language == "python" for r in results)

    @pytest.mark.asyncio
    async def test_delete(self, storage, sample_chunk):
        """Test deleting chunks."""
        await storage.add(sample_chunk)
        assert await storage.count() == 1

        result = await storage.delete(sample_chunk.id)
        assert result is True
        assert await storage.count() == 0

    @pytest.mark.asyncio
    async def test_clear(self, storage, sample_chunk):
        """Test clearing all chunks."""
        await storage.add(sample_chunk)
        await storage.clear()
        assert await storage.count() == 0


class TestIndexConfig:
    """Tests for IndexConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = IndexConfig()

        assert config.max_chunk_size == 1500
        assert config.min_chunk_size == 100
        assert ".py" in config.extensions
        assert "node_modules" in config.ignore_patterns

    def test_custom_config(self):
        """Test custom configuration."""
        config = IndexConfig(
            max_chunk_size=2000,
            extensions=[".py", ".go"],
            ignore_patterns=["vendor"],
        )

        assert config.max_chunk_size == 2000
        assert config.extensions == [".py", ".go"]
        assert config.ignore_patterns == ["vendor"]
