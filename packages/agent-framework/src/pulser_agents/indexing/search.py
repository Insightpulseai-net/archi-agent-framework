"""
Semantic search interface for codebase queries.

Provides high-level search functionality with ranking and filtering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pulser_agents.indexing.indexer import CodebaseIndexer
from pulser_agents.indexing.storage import SearchResult


@dataclass
class CodeLocation:
    """A location in the codebase."""

    file_path: str
    start_line: int
    end_line: int
    content: str
    language: str | None = None
    symbol_name: str | None = None


class SemanticSearch:
    """
    High-level semantic search interface.

    Provides natural language search over indexed codebases
    with result formatting and context extraction.

    Example:
        >>> indexer = CodebaseIndexer()
        >>> await indexer.index_directory("/path/to/project")
        >>>
        >>> search = SemanticSearch(indexer)
        >>> results = await search.find("user authentication")
        >>> for loc in results:
        ...     print(f"{loc.file_path}:{loc.start_line}")
    """

    def __init__(self, indexer: CodebaseIndexer) -> None:
        """
        Initialize semantic search.

        Args:
            indexer: Codebase indexer to use
        """
        self.indexer = indexer

    async def find(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
        file_pattern: str | None = None,
        language: str | None = None,
    ) -> list[CodeLocation]:
        """
        Find code matching a natural language query.

        Args:
            query: Natural language query
            top_k: Maximum results
            min_score: Minimum similarity score
            file_pattern: File path filter
            language: Language filter

        Returns:
            List of code locations
        """
        results = await self.indexer.search(
            query=query,
            top_k=top_k,
            file_path=file_pattern,
            language=language,
        )

        locations = []
        for result in results:
            if result.score < min_score:
                continue

            locations.append(
                CodeLocation(
                    file_path=result.chunk.metadata.file_path,
                    start_line=result.chunk.metadata.start_line,
                    end_line=result.chunk.metadata.end_line,
                    content=result.chunk.content,
                    language=result.chunk.metadata.language,
                    symbol_name=result.chunk.metadata.symbol_name,
                )
            )

        return locations

    async def find_similar(
        self,
        file_path: str,
        line_number: int,
        top_k: int = 5,
    ) -> list[CodeLocation]:
        """
        Find code similar to a given location.

        Args:
            file_path: File path
            line_number: Line number to find similar code for
            top_k: Maximum results

        Returns:
            List of similar code locations
        """
        # Get the chunk at this location
        if hasattr(self.indexer.storage, "get_chunks_by_file"):
            chunks = await self.indexer.storage.get_chunks_by_file(file_path)
            target_chunk = None

            for chunk in chunks:
                if (
                    chunk.metadata.start_line <= line_number
                    <= chunk.metadata.end_line
                ):
                    target_chunk = chunk
                    break

            if target_chunk and target_chunk.embedding:
                results = await self.indexer.storage.search(
                    target_chunk.embedding,
                    top_k=top_k + 1,  # +1 because we'll exclude the source
                )

                locations = []
                for result in results:
                    # Skip the source chunk
                    if result.chunk.id == target_chunk.id:
                        continue

                    locations.append(
                        CodeLocation(
                            file_path=result.chunk.metadata.file_path,
                            start_line=result.chunk.metadata.start_line,
                            end_line=result.chunk.metadata.end_line,
                            content=result.chunk.content,
                            language=result.chunk.metadata.language,
                            symbol_name=result.chunk.metadata.symbol_name,
                        )
                    )

                return locations[:top_k]

        return []

    async def get_context(
        self,
        query: str,
        max_tokens: int = 4000,
        min_score: float = 0.5,
    ) -> str:
        """
        Get relevant code context for a query.

        Formats search results into a context string suitable
        for LLM prompts.

        Args:
            query: Query to get context for
            max_tokens: Maximum approximate tokens
            min_score: Minimum similarity score

        Returns:
            Formatted context string
        """
        # Estimate ~4 chars per token
        max_chars = max_tokens * 4

        results = await self.indexer.search(query=query, top_k=20)

        context_parts = []
        total_chars = 0

        for result in results:
            if result.score < min_score:
                continue

            chunk = result.chunk
            chunk_header = (
                f"# {chunk.metadata.file_path}:"
                f"{chunk.metadata.start_line}-{chunk.metadata.end_line}"
            )
            chunk_content = f"{chunk_header}\n```{chunk.metadata.language or ''}\n{chunk.content}\n```"

            if total_chars + len(chunk_content) > max_chars:
                break

            context_parts.append(chunk_content)
            total_chars += len(chunk_content)

        return "\n\n".join(context_parts)

    async def explain_codebase(self, max_files: int = 20) -> str:
        """
        Generate a high-level explanation of the codebase.

        Args:
            max_files: Maximum files to include

        Returns:
            Codebase summary string
        """
        stats = await self.indexer.get_stats()

        lines = [
            "# Codebase Summary",
            "",
            f"- **Total Files**: {stats.total_files}",
            f"- **Total Chunks**: {stats.total_chunks}",
            f"- **Total Characters**: {stats.total_characters:,}",
            "",
            "## Languages",
            "",
        ]

        for lang, count in sorted(
            stats.languages.items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"- {lang}: {count} chunks")

        return "\n".join(lines)


class CodebaseQueryTool:
    """
    Tool wrapper for agent function calling.

    Provides a tool interface for agents to search codebases.
    """

    def __init__(self, search: SemanticSearch) -> None:
        """
        Initialize the tool.

        Args:
            search: Semantic search instance
        """
        self.search = search

    @property
    def name(self) -> str:
        return "search_codebase"

    @property
    def description(self) -> str:
        return (
            "Search the codebase using natural language. "
            "Returns relevant code snippets with file locations."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query describing what to find",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5,
                },
                "language": {
                    "type": "string",
                    "description": "Filter by programming language",
                },
            },
            "required": ["query"],
        }

    async def __call__(
        self,
        query: str,
        max_results: int = 5,
        language: str | None = None,
    ) -> str:
        """
        Execute the search.

        Args:
            query: Search query
            max_results: Maximum results
            language: Language filter

        Returns:
            Formatted search results
        """
        locations = await self.search.find(
            query=query,
            top_k=max_results,
            language=language,
        )

        if not locations:
            return "No results found."

        parts = [f"Found {len(locations)} results:\n"]
        for i, loc in enumerate(locations, 1):
            parts.append(
                f"\n## Result {i}: {loc.file_path}:{loc.start_line}-{loc.end_line}"
            )
            parts.append(f"```{loc.language or ''}\n{loc.content}\n```")

        return "\n".join(parts)
