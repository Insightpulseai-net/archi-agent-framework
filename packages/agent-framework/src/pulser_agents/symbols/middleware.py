"""
Middleware for @ symbol context injection.

Automatically resolves @ symbols in messages and injects context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import (
    Middleware,
    MiddlewareContext,
    NextHandler,
)
from pulser_agents.symbols.parser import ParseResult, SymbolParser
from pulser_agents.symbols.resolver import ResolutionContext, ResolvedSymbol, SymbolResolver


class SymbolsMiddleware(Middleware):
    """
    Middleware that resolves @ symbols in messages.

    Automatically parses @ symbols from input messages,
    resolves them to content, and injects the context.

    Example:
        >>> from pulser_agents.symbols import SymbolsMiddleware
        >>>
        >>> middleware = SymbolsMiddleware(base_path="/path/to/project")
        >>> agent.add_middleware(middleware)
        >>>
        >>> # Now messages like "Check @src/api/users.py" will
        >>> # automatically include the file content
    """

    def __init__(
        self,
        base_path: str | Path | None = None,
        max_file_lines: int = 500,
        include_line_numbers: bool = True,
        git_enabled: bool = True,
        inject_as_context: bool = True,
        indexer: Any = None,
    ) -> None:
        """
        Initialize the symbols middleware.

        Args:
            base_path: Base path for file resolution
            max_file_lines: Maximum lines per file
            include_line_numbers: Add line numbers to files
            git_enabled: Enable git references
            inject_as_context: Inject resolved content into context
            indexer: Optional codebase indexer for semantic search
        """
        self.parser = SymbolParser()
        self.resolver = SymbolResolver(
            context=ResolutionContext(
                base_path=Path(base_path) if base_path else Path.cwd(),
                max_file_lines=max_file_lines,
                include_line_numbers=include_line_numbers,
                git_enabled=git_enabled,
                indexer=indexer,
            )
        )
        self.inject_as_context = inject_as_context

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """
        Process the request, resolving @ symbols.

        Args:
            ctx: Middleware context
            next_handler: Next handler in chain

        Returns:
            Agent response
        """
        # Get input message
        input_text = self._get_input_text(ctx)

        if input_text and self.parser.has_symbols(input_text):
            # Parse symbols
            parse_result = self.parser.parse(input_text)

            # Resolve symbols
            resolved = await self.resolver.resolve_all(parse_result.symbols)

            # Store in metadata
            ctx.set_metadata("parsed_symbols", parse_result)
            ctx.set_metadata("resolved_symbols", resolved)

            # Build and inject context
            if self.inject_as_context and resolved:
                symbol_context = self.resolver.build_context(resolved)
                ctx.set_metadata("symbol_context", symbol_context)

                # Also store in agent context if available
                if ctx.context:
                    ctx.context.set("symbol_context", symbol_context)
                    ctx.context.set(
                        "symbol_summary",
                        self._build_summary(parse_result, resolved)
                    )

        # Continue to next handler
        return await next_handler(ctx)

    def _get_input_text(self, ctx: MiddlewareContext) -> str | None:
        """Extract input text from context."""
        if ctx.input_message:
            if isinstance(ctx.input_message, str):
                return ctx.input_message
            # Handle Message objects
            if hasattr(ctx.input_message, "content"):
                return ctx.input_message.content
        return None

    def _build_summary(
        self,
        parse_result: ParseResult,
        resolved: list[ResolvedSymbol],
    ) -> str:
        """Build a summary of resolved symbols."""
        total = len(parse_result.symbols)
        success = sum(1 for r in resolved if r.success)
        failed = total - success

        lines = [f"Resolved {success}/{total} symbols"]

        if failed > 0:
            failed_symbols = [r.symbol.raw for r in resolved if not r.success]
            lines.append(f"Failed: {', '.join(failed_symbols)}")

        return "; ".join(lines)


class SymbolsContextBuilder:
    """
    Builder for combining symbols with other context sources.
    """

    def __init__(
        self,
        resolver: SymbolResolver,
        parser: SymbolParser | None = None,
    ) -> None:
        """
        Initialize the context builder.

        Args:
            resolver: Symbol resolver
            parser: Optional parser (creates new if not provided)
        """
        self.resolver = resolver
        self.parser = parser or SymbolParser()

    async def build_from_message(
        self,
        message: str,
        additional_context: str | None = None,
    ) -> str:
        """
        Build context from a message containing @ symbols.

        Args:
            message: Message with @ symbols
            additional_context: Extra context to include

        Returns:
            Combined context string
        """
        parts = []

        # Parse and resolve symbols
        if self.parser.has_symbols(message):
            parse_result = self.parser.parse(message)
            resolved = await self.resolver.resolve_all(parse_result.symbols)
            symbol_context = self.resolver.build_context(resolved)

            if symbol_context:
                parts.append("# Referenced Context")
                parts.append(symbol_context)

        # Add additional context
        if additional_context:
            parts.append("")
            parts.append(additional_context)

        return "\n".join(parts)

    async def build_system_prompt(
        self,
        base_prompt: str,
        message: str,
    ) -> str:
        """
        Build a system prompt with symbol context injected.

        Args:
            base_prompt: Base system prompt
            message: User message with potential @ symbols

        Returns:
            Enhanced system prompt
        """
        if not self.parser.has_symbols(message):
            return base_prompt

        parse_result = self.parser.parse(message)
        resolved = await self.resolver.resolve_all(parse_result.symbols)

        successful = [r for r in resolved if r.success]
        if not successful:
            return base_prompt

        context_section = self.resolver.build_context(successful)

        return f"""{base_prompt}

# Additional Context from @ References

{context_section}
"""


def create_symbols_tool(resolver: SymbolResolver) -> dict[str, Any]:
    """
    Create a tool definition for @ symbol resolution.

    This allows agents to explicitly resolve @ symbols.

    Args:
        resolver: Symbol resolver instance

    Returns:
        Tool definition dict
    """
    async def resolve_symbols(symbols: list[str]) -> str:
        """Resolve @ symbols to their content."""
        from pulser_agents.symbols.parser import SymbolParser

        parser = SymbolParser()
        all_results = []

        for symbol_str in symbols:
            # Add @ prefix if missing
            if not symbol_str.startswith("@"):
                symbol_str = f"@{symbol_str}"

            result = parser.parse(symbol_str)
            if result.symbols:
                resolved = await resolver.resolve_all(result.symbols)
                all_results.extend(resolved)

        return resolver.build_context(all_results)

    return {
        "name": "resolve_symbols",
        "description": (
            "Resolve @ symbol references to their content. "
            "Use this to get file contents, code definitions, "
            "git history, or documentation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of @ symbols to resolve "
                        "(e.g., ['src/api/users.py', 'git:log'])"
                    ),
                },
            },
            "required": ["symbols"],
        },
        "function": resolve_symbols,
    }
