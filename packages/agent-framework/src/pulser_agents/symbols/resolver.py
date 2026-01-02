"""
Symbol resolver for @ symbol references.

Resolves symbols to actual content from files, code, docs, etc.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pulser_agents.symbols.parser import Symbol, SymbolType


@dataclass
class ResolvedSymbol:
    """
    A resolved @ symbol with its content.

    Attributes:
        symbol: Original symbol
        content: Resolved content
        success: Whether resolution succeeded
        error: Error message if failed
        metadata: Additional metadata
    """

    symbol: Symbol
    content: str = ""
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_context_string(self) -> str:
        """Convert to context string for LLM."""
        if not self.success:
            return f"# Error resolving {self.symbol.raw}: {self.error}"

        if self.symbol.type == SymbolType.FILE:
            lang = self._detect_language()
            return f"# {self.symbol.value}\n```{lang}\n{self.content}\n```"

        if self.symbol.type == SymbolType.FOLDER:
            return f"# Directory: {self.symbol.value}\n{self.content}"

        if self.symbol.type in (SymbolType.CODE, SymbolType.DEFINITION):
            return f"# Code: {self.symbol.value}\n```\n{self.content}\n```"

        if self.symbol.type == SymbolType.DOCS:
            return f"# Documentation: {self.symbol.value}\n{self.content}"

        if self.symbol.type == SymbolType.GIT:
            return f"# Git: {self.symbol.value}\n{self.content}"

        if self.symbol.type == SymbolType.WEB:
            return f"# Web Search: {self.symbol.value}\n{self.content}"

        return f"# {self.symbol.value}\n{self.content}"

    def _detect_language(self) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".md": "markdown",
            ".sql": "sql",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
        }
        ext = Path(self.symbol.value).suffix.lower()
        return ext_map.get(ext, "")


@dataclass
class ResolutionContext:
    """
    Context for symbol resolution.

    Attributes:
        base_path: Base path for file resolution
        max_file_lines: Maximum lines to read per file
        include_line_numbers: Include line numbers in output
        git_enabled: Enable git resolution
    """

    base_path: Path = field(default_factory=Path.cwd)
    max_file_lines: int = 500
    include_line_numbers: bool = True
    git_enabled: bool = True
    web_enabled: bool = False  # Requires additional setup
    indexer: Any = None  # Optional CodebaseIndexer for semantic search


class SymbolResolver:
    """
    Resolver for @ symbol references.

    Resolves symbols to their actual content.

    Example:
        >>> resolver = SymbolResolver(base_path="/path/to/project")
        >>> resolved = await resolver.resolve(symbol)
        >>> print(resolved.content)
    """

    def __init__(
        self,
        context: ResolutionContext | None = None,
    ) -> None:
        """
        Initialize the resolver.

        Args:
            context: Resolution context
        """
        self.context = context or ResolutionContext()

    async def resolve(self, symbol: Symbol) -> ResolvedSymbol:
        """
        Resolve a single symbol.

        Args:
            symbol: Symbol to resolve

        Returns:
            ResolvedSymbol with content
        """
        try:
            if symbol.type == SymbolType.FILE:
                return await self._resolve_file(symbol)

            if symbol.type == SymbolType.FOLDER:
                return await self._resolve_folder(symbol)

            if symbol.type == SymbolType.CODE:
                return await self._resolve_code(symbol)

            if symbol.type == SymbolType.DEFINITION:
                return await self._resolve_definition(symbol)

            if symbol.type == SymbolType.GIT:
                return await self._resolve_git(symbol)

            if symbol.type == SymbolType.DOCS:
                return await self._resolve_docs(symbol)

            if symbol.type == SymbolType.RECENT:
                return await self._resolve_recent(symbol)

            if symbol.type == SymbolType.RULES:
                return await self._resolve_rules(symbol)

            # Unsupported types
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Unsupported symbol type: {symbol.type}",
            )

        except Exception as e:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=str(e),
            )

    async def resolve_all(
        self,
        symbols: list[Symbol],
    ) -> list[ResolvedSymbol]:
        """
        Resolve multiple symbols.

        Args:
            symbols: Symbols to resolve

        Returns:
            List of resolved symbols
        """
        results = []
        for symbol in symbols:
            resolved = await self.resolve(symbol)
            results.append(resolved)
        return results

    async def _resolve_file(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a file reference."""
        file_path = self.context.base_path / symbol.value

        if not file_path.exists():
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"File not found: {symbol.value}",
            )

        if not file_path.is_file():
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Not a file: {symbol.value}",
            )

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            # Truncate if too long
            if len(lines) > self.context.max_file_lines:
                lines = lines[: self.context.max_file_lines]
                content = "\n".join(lines)
                content += f"\n\n... (truncated, {len(lines)} of {len(content.split(chr(10)))} lines shown)"

            # Add line numbers if requested
            if self.context.include_line_numbers:
                numbered_lines = [
                    f"{i + 1:4d} | {line}" for i, line in enumerate(lines)
                ]
                content = "\n".join(numbered_lines)

            return ResolvedSymbol(
                symbol=symbol,
                content=content,
                metadata={
                    "file_path": str(file_path),
                    "line_count": len(lines),
                },
            )

        except Exception as e:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Error reading file: {e}",
            )

    async def _resolve_folder(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a folder reference."""
        folder_path = self.context.base_path / symbol.value

        if not folder_path.exists():
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Folder not found: {symbol.value}",
            )

        if not folder_path.is_dir():
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Not a folder: {symbol.value}",
            )

        try:
            # List directory contents
            entries = []
            for entry in sorted(folder_path.iterdir()):
                if entry.name.startswith("."):
                    continue  # Skip hidden files

                prefix = "📁" if entry.is_dir() else "📄"
                entries.append(f"{prefix} {entry.name}")

            content = "\n".join(entries[:50])  # Limit entries
            if len(list(folder_path.iterdir())) > 50:
                content += f"\n... and {len(list(folder_path.iterdir())) - 50} more"

            return ResolvedSymbol(
                symbol=symbol,
                content=content,
                metadata={
                    "folder_path": str(folder_path),
                    "entry_count": len(entries),
                },
            )

        except Exception as e:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Error listing folder: {e}",
            )

    async def _resolve_code(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a code symbol reference."""
        # Try using indexer if available
        if self.context.indexer:
            try:
                results = await self.context.indexer.search(
                    query=symbol.value,
                    top_k=1,
                )
                if results:
                    chunk = results[0].chunk
                    return ResolvedSymbol(
                        symbol=symbol,
                        content=chunk.content,
                        metadata={
                            "file_path": chunk.metadata.file_path,
                            "start_line": chunk.metadata.start_line,
                            "end_line": chunk.metadata.end_line,
                        },
                    )
            except Exception:
                pass

        # Fallback: try grep
        try:
            result = subprocess.run(
                ["grep", "-rn", symbol.value, str(self.context.base_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.stdout:
                lines = result.stdout.strip().split("\n")[:10]
                content = "\n".join(lines)
                return ResolvedSymbol(
                    symbol=symbol,
                    content=content,
                    metadata={"method": "grep"},
                )
        except Exception:
            pass

        return ResolvedSymbol(
            symbol=symbol,
            success=False,
            error=f"Could not find code symbol: {symbol.value}",
        )

    async def _resolve_definition(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a definition reference."""
        # Similar to code but specifically looks for definitions
        patterns = [
            f"def {symbol.value}",
            f"class {symbol.value}",
            f"function {symbol.value}",
            f"const {symbol.value}",
            f"let {symbol.value}",
            f"var {symbol.value}",
        ]

        for pattern in patterns:
            try:
                result = subprocess.run(
                    ["grep", "-rn", pattern, str(self.context.base_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout:
                    lines = result.stdout.strip().split("\n")[:5]
                    content = "\n".join(lines)
                    return ResolvedSymbol(
                        symbol=symbol,
                        content=content,
                        metadata={"pattern": pattern},
                    )
            except Exception:
                continue

        return ResolvedSymbol(
            symbol=symbol,
            success=False,
            error=f"Could not find definition: {symbol.value}",
        )

    async def _resolve_git(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a git reference."""
        if not self.context.git_enabled:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error="Git resolution is disabled",
            )

        value = symbol.value
        try:
            # Check if it's a commit hash, branch, or command
            if value in ("log", "history"):
                result = subprocess.run(
                    ["git", "log", "--oneline", "-n", "10"],
                    capture_output=True,
                    text=True,
                    cwd=self.context.base_path,
                    timeout=10,
                )
            elif value in ("status", "changes"):
                result = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True,
                    text=True,
                    cwd=self.context.base_path,
                    timeout=10,
                )
            elif value in ("diff", "staged"):
                result = subprocess.run(
                    ["git", "diff", "--stat"],
                    capture_output=True,
                    text=True,
                    cwd=self.context.base_path,
                    timeout=10,
                )
            elif value.startswith("branch"):
                result = subprocess.run(
                    ["git", "branch", "-a"],
                    capture_output=True,
                    text=True,
                    cwd=self.context.base_path,
                    timeout=10,
                )
            else:
                # Assume it's a commit hash or ref
                result = subprocess.run(
                    ["git", "show", "--stat", value],
                    capture_output=True,
                    text=True,
                    cwd=self.context.base_path,
                    timeout=10,
                )

            if result.returncode == 0:
                return ResolvedSymbol(
                    symbol=symbol,
                    content=result.stdout,
                )
            else:
                return ResolvedSymbol(
                    symbol=symbol,
                    success=False,
                    error=result.stderr or "Git command failed",
                )

        except subprocess.TimeoutExpired:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error="Git command timed out",
            )
        except Exception as e:
            return ResolvedSymbol(
                symbol=symbol,
                success=False,
                error=f"Git error: {e}",
            )

    async def _resolve_docs(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a documentation reference."""
        # Look for markdown files matching the query
        docs_paths = [
            self.context.base_path / "docs",
            self.context.base_path / "documentation",
            self.context.base_path,
        ]

        for docs_path in docs_paths:
            if not docs_path.exists():
                continue

            # Search for matching markdown files
            for md_file in docs_path.rglob("*.md"):
                if symbol.value.lower() in md_file.stem.lower():
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        return ResolvedSymbol(
                            symbol=symbol,
                            content=content[:5000],  # Limit size
                            metadata={"file_path": str(md_file)},
                        )
                    except Exception:
                        continue

        return ResolvedSymbol(
            symbol=symbol,
            success=False,
            error=f"Documentation not found: {symbol.value}",
        )

    async def _resolve_recent(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve recent changes reference."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--name-only",
                    "-n",
                    "5",
                ],
                capture_output=True,
                text=True,
                cwd=self.context.base_path,
                timeout=10,
            )
            if result.returncode == 0:
                return ResolvedSymbol(
                    symbol=symbol,
                    content=result.stdout,
                )
        except Exception:
            pass

        return ResolvedSymbol(
            symbol=symbol,
            success=False,
            error="Could not get recent changes",
        )

    async def _resolve_rules(self, symbol: Symbol) -> ResolvedSymbol:
        """Resolve a rules reference."""
        # Look for rule files
        rule_paths = [
            self.context.base_path / ".cursor" / "rules",
            self.context.base_path / ".pulser" / "rules",
        ]

        for rules_path in rule_paths:
            if not rules_path.exists():
                continue

            for rule_file in rules_path.rglob("*.md"):
                if symbol.value.lower() in rule_file.stem.lower():
                    try:
                        content = rule_file.read_text(encoding="utf-8")
                        return ResolvedSymbol(
                            symbol=symbol,
                            content=content,
                            metadata={"file_path": str(rule_file)},
                        )
                    except Exception:
                        continue

        return ResolvedSymbol(
            symbol=symbol,
            success=False,
            error=f"Rule not found: {symbol.value}",
        )

    def build_context(
        self,
        resolved_symbols: list[ResolvedSymbol],
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Build a combined context string from resolved symbols.

        Args:
            resolved_symbols: List of resolved symbols
            separator: Separator between sections

        Returns:
            Combined context string
        """
        parts = []
        for resolved in resolved_symbols:
            if resolved.success:
                parts.append(resolved.to_context_string())

        return separator.join(parts)
