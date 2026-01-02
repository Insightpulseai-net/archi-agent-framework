"""
Pulser Agent Framework
======================

A comprehensive framework for building, orchestrating, and deploying AI agents.

Features:
- Multi-provider LLM support (OpenAI, Azure, Anthropic, Ollama)
- Flexible orchestration patterns (sequential, concurrent, group chat)
- Tool/function calling with type validation
- Memory and context management
- Middleware architecture for extensibility
- Streaming and async-first design
- Rules system (.cursor/rules pattern)
- Codebase indexing with semantic search
- @ symbol context injection

Example:
    >>> from pulser_agents import Agent, OpenAIChatClient
    >>>
    >>> client = OpenAIChatClient(api_key="sk-...")
    >>> agent = Agent(
    ...     chat_client=client,
    ...     instructions="You are a helpful assistant."
    ... )
    >>> response = await agent.run("Hello!")
"""

from pulser_agents.core.agent import Agent, AgentConfig
from pulser_agents.core.context import AgentContext, ConversationHistory
from pulser_agents.core.exceptions import (
    AgentError,
    OrchestrationError,
    ProviderError,
    ToolError,
)
from pulser_agents.core.message import Message, MessageRole
from pulser_agents.core.response import AgentResponse, StreamingResponse

# New P0 features
from pulser_agents.rules import Rule, RulesEngine, RulesMiddleware, RuleType
from pulser_agents.indexing import (
    CodebaseIndexer,
    CodeChunker,
    SemanticSearch,
    IndexConfig,
)
from pulser_agents.symbols import SymbolParser, SymbolResolver, SymbolsMiddleware

# Version
__version__ = "0.2.0"

__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    "Message",
    "MessageRole",
    "AgentResponse",
    "StreamingResponse",
    "AgentContext",
    "ConversationHistory",
    # Rules System
    "Rule",
    "RulesEngine",
    "RulesMiddleware",
    "RuleType",
    # Codebase Indexing
    "CodebaseIndexer",
    "CodeChunker",
    "SemanticSearch",
    "IndexConfig",
    # @ Symbols
    "SymbolParser",
    "SymbolResolver",
    "SymbolsMiddleware",
    # Exceptions
    "AgentError",
    "ProviderError",
    "ToolError",
    "OrchestrationError",
    # Version
    "__version__",
]
