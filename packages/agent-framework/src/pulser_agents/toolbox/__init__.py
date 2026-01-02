"""
GenAI Toolbox Integration
=========================

Client for Google's GenAI Toolbox - a tool-serving control plane for databases.

Toolbox exposes database operations as MCP tools with:
- Connection pooling and authentication
- OpenTelemetry observability
- Hot-reload tool definitions

Usage:
    >>> from pulser_agents.toolbox import ToolboxClient
    >>>
    >>> async with ToolboxClient("http://localhost:5000") as client:
    ...     # Load a toolset
    ...     tools = await client.load_toolset("explorer")
    ...
    ...     # Execute a tool
    ...     result = await client.execute_tool("list_schemas")
    ...     print(result)

Architecture:
    - Toolbox = DB tool plane (handles pooling, auth, observability)
    - Workbench-API = Pipeline plane (artifacts, codegen, orchestration)
    - VS Code Extension / Agents = UX shell (calls both planes)
"""

from pulser_agents.toolbox.client import (
    ToolboxClient,
    ToolboxClientConfig,
    ToolboxError,
    ToolboxTool,
)

__all__ = [
    "ToolboxClient",
    "ToolboxClientConfig",
    "ToolboxError",
    "ToolboxTool",
]
