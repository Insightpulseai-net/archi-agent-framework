"""
Symbol parser for @ symbol syntax.

Parses @ symbols from text and extracts references.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SymbolType(str, Enum):
    """Types of @ symbols."""

    FILE = "file"  # @path/to/file.py
    FOLDER = "folder"  # @path/to/folder/
    CODE = "code"  # @symbol_name or @file:line
    DOCS = "docs"  # @docs:topic
    WEB = "web"  # @web:query
    GIT = "git"  # @git:commit or @git:branch
    RULES = "rules"  # @rules:name
    LINK = "link"  # @link:url
    RECENT = "recent"  # @recent
    RECOMMENDED = "recommended"  # @recommended
    LINT_ERRORS = "lint_errors"  # @lint
    DEFINITION = "definition"  # @def:symbol
    UNKNOWN = "unknown"


@dataclass
class Symbol:
    """
    A parsed @ symbol reference.

    Attributes:
        type: Type of symbol
        value: Symbol value (path, query, etc.)
        raw: Original raw text
        start: Start position in text
        end: End position in text
        metadata: Additional metadata
    """

    type: SymbolType
    value: str
    raw: str
    start: int
    end: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_file_reference(self) -> bool:
        """Check if this is a file reference."""
        return self.type in (SymbolType.FILE, SymbolType.FOLDER)

    @property
    def is_code_reference(self) -> bool:
        """Check if this is a code reference."""
        return self.type in (SymbolType.CODE, SymbolType.DEFINITION)


@dataclass
class ParseResult:
    """
    Result of parsing a message for symbols.

    Attributes:
        original: Original text
        symbols: Extracted symbols
        cleaned: Text with symbols removed
        symbol_count: Number of symbols found
    """

    original: str
    symbols: list[Symbol]
    cleaned: str = ""
    symbol_count: int = 0

    def __post_init__(self):
        self.symbol_count = len(self.symbols)
        if not self.cleaned:
            self.cleaned = self._remove_symbols()

    def _remove_symbols(self) -> str:
        """Remove symbols from original text."""
        if not self.symbols:
            return self.original

        # Sort by position descending to remove from end first
        sorted_symbols = sorted(self.symbols, key=lambda s: s.start, reverse=True)

        result = self.original
        for symbol in sorted_symbols:
            result = result[: symbol.start] + result[symbol.end :]

        # Clean up multiple spaces
        result = re.sub(r"\s+", " ", result).strip()
        return result

    def get_symbols_by_type(self, symbol_type: SymbolType) -> list[Symbol]:
        """Get symbols of a specific type."""
        return [s for s in self.symbols if s.type == symbol_type]

    def get_file_symbols(self) -> list[Symbol]:
        """Get all file-related symbols."""
        return [s for s in self.symbols if s.is_file_reference]

    def get_code_symbols(self) -> list[Symbol]:
        """Get all code-related symbols."""
        return [s for s in self.symbols if s.is_code_reference]


class SymbolParser:
    """
    Parser for @ symbol syntax.

    Extracts @ symbols from text and identifies their types.

    Example:
        >>> parser = SymbolParser()
        >>> result = parser.parse("Look at @src/api/users.py")
        >>> print(result.symbols[0].type)
        SymbolType.FILE
    """

    # Pattern for @ symbols
    # Matches: @path/to/file.ext, @folder/, @prefix:value
    SYMBOL_PATTERN = re.compile(
        r"@(?:"
        r"(?P<prefixed>(?P<prefix>docs|web|git|rules|link|def|lint|recent|recommended):(?P<prefixed_value>[^\s,;]+))"
        r"|"
        r"(?P<path>[\w./-]+(?:\.\w+)?/?)"
        r")",
        re.IGNORECASE,
    )

    # File extensions for path detection
    FILE_EXTENSIONS = {
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
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".sql",
        ".sh",
        ".css",
        ".scss",
        ".html",
        ".vue",
        ".svelte",
    }

    # Prefixes and their symbol types
    PREFIX_TYPES = {
        "docs": SymbolType.DOCS,
        "web": SymbolType.WEB,
        "git": SymbolType.GIT,
        "rules": SymbolType.RULES,
        "link": SymbolType.LINK,
        "def": SymbolType.DEFINITION,
        "lint": SymbolType.LINT_ERRORS,
        "recent": SymbolType.RECENT,
        "recommended": SymbolType.RECOMMENDED,
    }

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse(self, text: str) -> ParseResult:
        """
        Parse text for @ symbols.

        Args:
            text: Text to parse

        Returns:
            ParseResult with extracted symbols
        """
        symbols = []

        for match in self.SYMBOL_PATTERN.finditer(text):
            symbol = self._parse_match(match)
            if symbol:
                symbols.append(symbol)

        return ParseResult(original=text, symbols=symbols)

    def _parse_match(self, match: re.Match) -> Symbol | None:
        """Parse a regex match into a Symbol."""
        raw = match.group(0)
        start = match.start()
        end = match.end()

        # Check for prefixed pattern (e.g., @docs:topic)
        if match.group("prefixed"):
            prefix = match.group("prefix").lower()
            value = match.group("prefixed_value")
            symbol_type = self.PREFIX_TYPES.get(prefix, SymbolType.UNKNOWN)

            return Symbol(
                type=symbol_type,
                value=value,
                raw=raw,
                start=start,
                end=end,
                metadata={"prefix": prefix},
            )

        # Check for path pattern
        path = match.group("path")
        if path:
            symbol_type = self._detect_path_type(path)
            return Symbol(
                type=symbol_type,
                value=path.rstrip("/"),
                raw=raw,
                start=start,
                end=end,
            )

        return None

    def _detect_path_type(self, path: str) -> SymbolType:
        """Detect whether a path is a file or folder."""
        # Trailing slash indicates folder
        if path.endswith("/"):
            return SymbolType.FOLDER

        # Check for file extension
        for ext in self.FILE_EXTENSIONS:
            if path.endswith(ext):
                return SymbolType.FILE

        # Check if it looks like a file path
        if "/" in path or "." in path:
            # Has extension-like ending
            parts = path.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) <= 5:
                return SymbolType.FILE
            # No extension, assume folder
            return SymbolType.FOLDER

        # Single word could be a symbol reference
        return SymbolType.CODE

    def extract_file_references(self, text: str) -> list[str]:
        """
        Extract just file paths from text.

        Args:
            text: Text to parse

        Returns:
            List of file paths
        """
        result = self.parse(text)
        return [s.value for s in result.get_file_symbols()]

    def has_symbols(self, text: str) -> bool:
        """Check if text contains any @ symbols."""
        return bool(self.SYMBOL_PATTERN.search(text))

    def count_symbols(self, text: str) -> int:
        """Count @ symbols in text."""
        return len(self.SYMBOL_PATTERN.findall(text))


class SymbolFormatter:
    """
    Formatter for displaying symbols and their resolved content.
    """

    @staticmethod
    def format_file_reference(file_path: str, content: str) -> str:
        """Format a file reference for LLM context."""
        return f"# File: {file_path}\n```\n{content}\n```"

    @staticmethod
    def format_code_reference(
        symbol_name: str,
        file_path: str,
        line_start: int,
        line_end: int,
        content: str,
    ) -> str:
        """Format a code reference for LLM context."""
        return (
            f"# {symbol_name} ({file_path}:{line_start}-{line_end})\n"
            f"```\n{content}\n```"
        )

    @staticmethod
    def format_docs_reference(topic: str, content: str) -> str:
        """Format a documentation reference."""
        return f"# Documentation: {topic}\n{content}"

    @staticmethod
    def format_git_reference(ref: str, content: str) -> str:
        """Format a git reference."""
        return f"# Git: {ref}\n{content}"
