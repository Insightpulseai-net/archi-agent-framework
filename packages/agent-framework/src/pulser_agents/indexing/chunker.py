"""
Code chunking for codebase indexing.

Implements intelligent code splitting at semantic boundaries
(functions, classes, modules) for optimal embedding.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ChunkType(str, Enum):
    """Types of code chunks."""

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    DOCSTRING = "docstring"
    COMMENT = "comment"
    IMPORT = "import"
    BLOCK = "block"


@dataclass
class ChunkMetadata:
    """Metadata for a code chunk."""

    file_path: str
    start_line: int
    end_line: int
    chunk_type: ChunkType
    language: str | None = None
    parent_name: str | None = None
    symbol_name: str | None = None
    signature: str | None = None
    docstring: str | None = None
    imports: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class Chunk:
    """
    A chunk of code with metadata.

    Attributes:
        id: Unique chunk identifier (content hash)
        content: The code content
        metadata: Chunk metadata
        embedding: Optional embedding vector
        created_at: Creation timestamp
    """

    content: str
    metadata: ChunkMetadata
    id: str = ""
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.id:
            self.id = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute content hash for chunk ID."""
        content = f"{self.metadata.file_path}:{self.content}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @property
    def line_count(self) -> int:
        """Get number of lines in chunk."""
        return self.metadata.end_line - self.metadata.start_line + 1

    @property
    def char_count(self) -> int:
        """Get character count."""
        return len(self.content)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "file_path": self.metadata.file_path,
            "start_line": self.metadata.start_line,
            "end_line": self.metadata.end_line,
            "chunk_type": self.metadata.chunk_type.value,
            "language": self.metadata.language,
            "symbol_name": self.metadata.symbol_name,
        }


class CodeChunker:
    """
    Intelligent code chunker that splits at semantic boundaries.

    Supports multiple languages and adapts chunk sizes based on
    code structure.
    """

    # Language detection by extension
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".md": "markdown",
        ".sql": "sql",
        ".sh": "shell",
        ".bash": "shell",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".toml": "toml",
    }

    # Patterns for splitting by language
    SPLIT_PATTERNS = {
        "python": {
            "class": re.compile(r"^class\s+(\w+)", re.MULTILINE),
            "function": re.compile(r"^(?:async\s+)?def\s+(\w+)", re.MULTILINE),
            "decorator": re.compile(r"^@\w+", re.MULTILINE),
        },
        "javascript": {
            "class": re.compile(r"^(?:export\s+)?class\s+(\w+)", re.MULTILINE),
            "function": re.compile(
                r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", re.MULTILINE
            ),
            "arrow": re.compile(
                r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>",
                re.MULTILINE,
            ),
        },
        "typescript": {
            "class": re.compile(r"^(?:export\s+)?class\s+(\w+)", re.MULTILINE),
            "interface": re.compile(r"^(?:export\s+)?interface\s+(\w+)", re.MULTILINE),
            "type": re.compile(r"^(?:export\s+)?type\s+(\w+)", re.MULTILINE),
            "function": re.compile(
                r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", re.MULTILINE
            ),
        },
        "go": {
            "function": re.compile(r"^func\s+(?:\([^)]+\)\s+)?(\w+)", re.MULTILINE),
            "type": re.compile(r"^type\s+(\w+)", re.MULTILINE),
        },
        "rust": {
            "function": re.compile(r"^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)", re.MULTILINE),
            "struct": re.compile(r"^(?:pub\s+)?struct\s+(\w+)", re.MULTILINE),
            "enum": re.compile(r"^(?:pub\s+)?enum\s+(\w+)", re.MULTILINE),
            "impl": re.compile(r"^impl(?:<[^>]+>)?\s+(\w+)", re.MULTILINE),
        },
    }

    def __init__(
        self,
        max_chunk_size: int = 1500,
        min_chunk_size: int = 100,
        overlap: int = 50,
        respect_boundaries: bool = True,
    ) -> None:
        """
        Initialize the chunker.

        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
            overlap: Character overlap between chunks
            respect_boundaries: Respect function/class boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        self.respect_boundaries = respect_boundaries

    def detect_language(self, file_path: str) -> str | None:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAP.get(ext)

    def chunk_file(self, file_path: str, content: str | None = None) -> list[Chunk]:
        """
        Chunk a file into semantic pieces.

        Args:
            file_path: Path to the file
            content: Optional content (reads file if not provided)

        Returns:
            List of chunks
        """
        path = Path(file_path)

        if content is None:
            if not path.exists():
                return []
            content = path.read_text(encoding="utf-8", errors="ignore")

        if not content.strip():
            return []

        language = self.detect_language(file_path)

        if self.respect_boundaries and language in self.SPLIT_PATTERNS:
            return self._chunk_with_boundaries(file_path, content, language)
        else:
            return self._chunk_simple(file_path, content, language)

    def _chunk_with_boundaries(
        self,
        file_path: str,
        content: str,
        language: str,
    ) -> list[Chunk]:
        """Chunk respecting language semantic boundaries."""
        chunks = []
        lines = content.split("\n")
        patterns = self.SPLIT_PATTERNS.get(language, {})

        # Find all boundary positions
        boundaries = self._find_boundaries(content, patterns)

        if not boundaries:
            return self._chunk_simple(file_path, content, language)

        # Sort boundaries by position
        boundaries.sort(key=lambda x: x[0])

        # Create chunks from boundaries
        prev_pos = 0
        for pos, chunk_type, name in boundaries:
            # Get content before this boundary
            if pos > prev_pos:
                chunk_content = content[prev_pos:pos].strip()
                if len(chunk_content) >= self.min_chunk_size:
                    start_line = content[:prev_pos].count("\n") + 1
                    end_line = content[:pos].count("\n")
                    chunks.append(
                        self._create_chunk(
                            file_path,
                            chunk_content,
                            start_line,
                            end_line,
                            ChunkType.BLOCK,
                            language,
                        )
                    )
            prev_pos = pos

        # Handle remaining content
        if prev_pos < len(content):
            chunk_content = content[prev_pos:].strip()
            if len(chunk_content) >= self.min_chunk_size:
                start_line = content[:prev_pos].count("\n") + 1
                end_line = len(lines)
                chunks.append(
                    self._create_chunk(
                        file_path,
                        chunk_content,
                        start_line,
                        end_line,
                        ChunkType.BLOCK,
                        language,
                    )
                )

        # Split any oversized chunks
        final_chunks = []
        for chunk in chunks:
            if len(chunk.content) > self.max_chunk_size:
                final_chunks.extend(
                    self._split_large_chunk(chunk, language)
                )
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _find_boundaries(
        self,
        content: str,
        patterns: dict[str, re.Pattern],
    ) -> list[tuple[int, ChunkType, str]]:
        """Find semantic boundaries in content."""
        boundaries = []

        type_map = {
            "class": ChunkType.CLASS,
            "function": ChunkType.FUNCTION,
            "interface": ChunkType.CLASS,
            "type": ChunkType.CLASS,
            "struct": ChunkType.CLASS,
            "enum": ChunkType.CLASS,
            "impl": ChunkType.CLASS,
            "arrow": ChunkType.FUNCTION,
            "decorator": ChunkType.FUNCTION,
        }

        for pattern_name, pattern in patterns.items():
            for match in pattern.finditer(content):
                chunk_type = type_map.get(pattern_name, ChunkType.BLOCK)
                name = match.group(1) if match.lastindex else pattern_name
                boundaries.append((match.start(), chunk_type, name))

        return boundaries

    def _chunk_simple(
        self,
        file_path: str,
        content: str,
        language: str | None,
    ) -> list[Chunk]:
        """Simple chunking by size with line-boundary respect."""
        chunks = []
        lines = content.split("\n")
        current_chunk = []
        current_size = 0
        start_line = 1

        for i, line in enumerate(lines, 1):
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.max_chunk_size and current_chunk:
                # Create chunk
                chunk_content = "\n".join(current_chunk)
                chunks.append(
                    self._create_chunk(
                        file_path,
                        chunk_content,
                        start_line,
                        i - 1,
                        ChunkType.BLOCK,
                        language,
                    )
                )
                # Start new chunk with overlap
                overlap_lines = max(1, self.overlap // 50)
                current_chunk = current_chunk[-overlap_lines:]
                current_size = sum(len(l) + 1 for l in current_chunk)
                start_line = i - len(current_chunk)

            current_chunk.append(line)
            current_size += line_size

        # Handle remaining content
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            if len(chunk_content) >= self.min_chunk_size:
                chunks.append(
                    self._create_chunk(
                        file_path,
                        chunk_content,
                        start_line,
                        len(lines),
                        ChunkType.BLOCK,
                        language,
                    )
                )

        return chunks

    def _create_chunk(
        self,
        file_path: str,
        content: str,
        start_line: int,
        end_line: int,
        chunk_type: ChunkType,
        language: str | None,
        symbol_name: str | None = None,
    ) -> Chunk:
        """Create a chunk with metadata."""
        metadata = ChunkMetadata(
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            language=language,
            symbol_name=symbol_name,
        )
        return Chunk(content=content, metadata=metadata)

    def _split_large_chunk(self, chunk: Chunk, language: str | None) -> list[Chunk]:
        """Split an oversized chunk into smaller pieces."""
        return self._chunk_simple(
            chunk.metadata.file_path,
            chunk.content,
            language,
        )

    def chunk_directory(
        self,
        directory: str | Path,
        extensions: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
    ) -> list[Chunk]:
        """
        Chunk all files in a directory.

        Args:
            directory: Directory to chunk
            extensions: File extensions to include
            ignore_patterns: Patterns to ignore

        Returns:
            List of all chunks
        """
        path = Path(directory)
        if not path.exists():
            return []

        # Default extensions
        if extensions is None:
            extensions = list(self.LANGUAGE_MAP.keys())

        # Default ignore patterns
        if ignore_patterns is None:
            ignore_patterns = [
                "node_modules",
                ".git",
                "__pycache__",
                ".venv",
                "venv",
                "dist",
                "build",
                ".next",
                "target",
            ]

        all_chunks = []

        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check extension
            if file_path.suffix.lower() not in extensions:
                continue

            # Check ignore patterns
            path_str = str(file_path)
            if any(pattern in path_str for pattern in ignore_patterns):
                continue

            try:
                chunks = self.chunk_file(str(file_path))
                all_chunks.extend(chunks)
            except Exception:
                # Skip files that fail to chunk
                continue

        return all_chunks
