"""
@ Symbols Context Injection System for Pulser Agent Framework.

Implements Cursor-style @ symbol context injection:
- @Files - Reference specific files
- @Folders - Reference directories
- @Code - Reference code snippets
- @Docs - Access documentation
- @Web - Web search
- @Git - Git history
- @Rules - Reference rules

Example:
    >>> from pulser_agents.symbols import SymbolParser, SymbolResolver
    >>>
    >>> parser = SymbolParser()
    >>> symbols = parser.parse("Check @src/api/users.py for auth logic")
    >>>
    >>> resolver = SymbolResolver()
    >>> context = await resolver.resolve_all(symbols)
"""

from pulser_agents.symbols.parser import (
    SymbolParser,
    Symbol,
    SymbolType,
    ParseResult,
)
from pulser_agents.symbols.resolver import (
    SymbolResolver,
    ResolvedSymbol,
    ResolutionContext,
)
from pulser_agents.symbols.middleware import SymbolsMiddleware

__all__ = [
    # Parser
    "SymbolParser",
    "Symbol",
    "SymbolType",
    "ParseResult",
    # Resolver
    "SymbolResolver",
    "ResolvedSymbol",
    "ResolutionContext",
    # Middleware
    "SymbolsMiddleware",
]
