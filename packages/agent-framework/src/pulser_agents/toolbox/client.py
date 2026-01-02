"""
GenAI Toolbox Client
====================

Python client for Google's GenAI Toolbox server.
Provides async interface for loading toolsets and executing database tools.

Reference: https://github.com/googleapis/genai-toolbox
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel, Field

from pulser_agents.core.base_client import ToolDefinition
from pulser_agents.core.exceptions import ToolError


class ToolboxError(ToolError):
    """Error from Toolbox server."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        tool_name: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.tool_name = tool_name


class ToolboxClientConfig(BaseModel):
    """Configuration for Toolbox client."""

    base_url: str = Field(default="http://localhost:5000", description="Toolbox server URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries")
    api_key: str | None = Field(default=None, description="Optional API key for auth")
    headers: dict[str, str] = Field(default_factory=dict, description="Custom headers")


@dataclass
class ToolboxTool:
    """
    A tool loaded from Toolbox.

    Can be converted to agent framework ToolDefinition or used directly.
    """

    name: str
    description: str
    kind: str
    source: str
    parameters: list[dict[str, Any]] = field(default_factory=list)
    statement: str | None = None

    def to_tool_definition(self) -> ToolDefinition:
        """Convert to agent framework ToolDefinition."""
        properties = {}
        required = []

        for param in self.parameters:
            param_name = param.get("name", "")
            param_type = param.get("type", "string")
            param_desc = param.get("description", "")

            properties[param_name] = {
                "type": param_type,
                "description": param_desc,
            }

            if param.get("required", False):
                required.append(param_name)

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=properties,
            required=required,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "kind": self.kind,
            "source": self.source,
            "parameters": self.parameters,
            "statement": self.statement,
        }


class ToolboxClient:
    """
    Async client for GenAI Toolbox server.

    Usage:
        >>> async with ToolboxClient("http://localhost:5000") as client:
        ...     tools = await client.load_toolset("explorer")
        ...     result = await client.execute_tool("list_schemas")

    Args:
        base_url: Toolbox server URL
        config: Optional client configuration
    """

    def __init__(
        self,
        base_url: str | None = None,
        config: ToolboxClientConfig | None = None,
    ):
        if config is None:
            config = ToolboxClientConfig(base_url=base_url or "http://localhost:5000")
        elif base_url:
            config = config.model_copy(update={"base_url": base_url})

        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._tools: dict[str, ToolboxTool] = {}
        self._toolsets: dict[str, list[str]] = {}

    async def __aenter__(self) -> ToolboxClient:
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            headers = dict(self.config.headers)
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic."""
        client = await self._ensure_client()

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = ToolboxError(
                    message=f"Toolbox request failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
                if e.response.status_code < 500:
                    raise last_error from e
            except httpx.RequestError as e:
                last_error = ToolboxError(f"Toolbox connection error: {e}")

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise last_error or ToolboxError("Unknown error")

    async def health(self) -> dict[str, Any]:
        """Check Toolbox server health."""
        return await self._request("GET", "/health")

    async def list_tools(self) -> list[ToolboxTool]:
        """List all available tools."""
        data = await self._request("GET", "/api/tools")

        tools = []
        for name, tool_data in data.get("tools", {}).items():
            tool = ToolboxTool(
                name=name,
                description=tool_data.get("description", ""),
                kind=tool_data.get("kind", "unknown"),
                source=tool_data.get("source", ""),
                parameters=tool_data.get("parameters", []),
                statement=tool_data.get("statement"),
            )
            tools.append(tool)
            self._tools[name] = tool

        return tools

    async def list_toolsets(self) -> dict[str, list[str]]:
        """List all available toolsets."""
        data = await self._request("GET", "/api/toolsets")
        self._toolsets = data.get("toolsets", {})
        return self._toolsets

    async def load_toolset(self, toolset_name: str) -> list[ToolboxTool]:
        """
        Load a toolset by name.

        Returns list of ToolboxTool objects that can be converted to
        ToolDefinition for use with agents.

        Args:
            toolset_name: Name of the toolset (e.g., "explorer", "analyst")

        Returns:
            List of tools in the toolset
        """
        data = await self._request("GET", f"/api/toolsets/{toolset_name}")

        tools = []
        for tool_data in data.get("tools", []):
            tool = ToolboxTool(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                kind=tool_data.get("kind", "unknown"),
                source=tool_data.get("source", ""),
                parameters=tool_data.get("parameters", []),
                statement=tool_data.get("statement"),
            )
            tools.append(tool)
            self._tools[tool.name] = tool

        return tools

    async def get_tool(self, tool_name: str) -> ToolboxTool:
        """Get a specific tool by name."""
        if tool_name in self._tools:
            return self._tools[tool_name]

        data = await self._request("GET", f"/api/tools/{tool_name}")
        tool = ToolboxTool(
            name=tool_name,
            description=data.get("description", ""),
            kind=data.get("kind", "unknown"),
            source=data.get("source", ""),
            parameters=data.get("parameters", []),
            statement=data.get("statement"),
        )
        self._tools[tool_name] = tool
        return tool

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        payload = {"parameters": parameters or {}}

        try:
            result = await self._request(
                "POST",
                f"/api/tools/{tool_name}/execute",
                json=payload,
            )
            return result
        except ToolboxError as e:
            e.tool_name = tool_name
            raise

    async def execute_sql(
        self,
        sql: str,
        params: list[Any] | None = None,
        tool_name: str = "workbench_sql",
    ) -> dict[str, Any]:
        """
        Execute a SQL query via the SQL tool.

        Convenience method for direct SQL execution.

        Args:
            sql: SQL query to execute
            params: Query parameters
            tool_name: Name of the SQL tool (default: workbench_sql)

        Returns:
            Query results
        """
        parameters: dict[str, Any] = {"sql": sql}
        if params:
            parameters["params"] = params

        return await self.execute_tool(tool_name, parameters)

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """
        Get all loaded tools as ToolDefinition objects.

        Use this to pass tools to an agent.
        """
        return [tool.to_tool_definition() for tool in self._tools.values()]


def create_toolbox_executor(client: ToolboxClient):
    """
    Create a tool executor function for use with agents.

    Returns a callable that executes tools via the Toolbox client.

    Usage:
        >>> client = ToolboxClient("http://localhost:5000")
        >>> executor = create_toolbox_executor(client)
        >>> result = await executor("list_schemas", {})
    """

    async def executor(tool_name: str, parameters: dict[str, Any]) -> Any:
        result = await client.execute_tool(tool_name, parameters)
        return result.get("data", result)

    return executor
