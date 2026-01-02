#!/usr/bin/env python3
"""
GenAI Toolbox Tool Generator
============================

Generates Toolbox tool definitions from:
- OpenAPI specifications (API endpoints → callable tools)
- Database schema (SQL migrations → schema inspection tools)

Usage:
    python generate_tools.py --openapi specs/openapi/openapi.yaml
    python generate_tools.py --schema db/schema.sql
    python generate_tools.py --all --output tools/toolbox/generated.yaml

Output is merged with tools.yaml via includes or manual copy.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def load_openapi_spec(spec_path: Path) -> dict[str, Any]:
    """Load and resolve OpenAPI specification."""
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    return spec


def load_sql_schema(schema_path: Path) -> str:
    """Load SQL schema file."""
    with open(schema_path) as f:
        return f.read()


def openapi_to_tools(spec: dict[str, Any], source_name: str = "api") -> dict[str, Any]:
    """
    Convert OpenAPI paths to Toolbox tool definitions.

    Each endpoint becomes a tool that can be called by agents.
    This is useful for exposing workbench-api endpoints as MCP tools.
    """
    tools = {}
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
            summary = operation.get("summary", "")
            description = operation.get("description", summary)
            tags = operation.get("tags", [])

            # Generate tool name from operationId
            tool_name = _sanitize_tool_name(operation_id)

            # Build parameters from path params + query params
            parameters = []
            for param in operation.get("parameters", []):
                param_def = {
                    "name": param.get("name"),
                    "type": _openapi_type_to_toolbox(param.get("schema", {}).get("type", "string")),
                    "description": param.get("description", ""),
                }
                if param.get("required", False):
                    param_def["required"] = True
                parameters.append(param_def)

            # Create tool definition
            tools[tool_name] = {
                "kind": "http",
                "source": source_name,
                "description": f"{description}\n\nEndpoint: {method.upper()} {path}",
                "method": method.upper(),
                "path": path,
            }

            if parameters:
                tools[tool_name]["parameters"] = parameters

            if tags:
                tools[tool_name]["tags"] = tags

    return tools


def schema_to_tools(schema_sql: str, source_name: str = "workbench_pg") -> dict[str, Any]:
    """
    Parse SQL schema to generate table inspection tools.

    Creates tools for each detected table:
    - list_<table>: List rows from the table
    - describe_<table>: Get column information
    """
    tools = {}

    # Extract CREATE TABLE statements
    table_pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_.]+)\s*\("
    tables = re.findall(table_pattern, schema_sql, re.IGNORECASE)

    for full_table_name in tables:
        # Parse schema.table format
        if "." in full_table_name:
            schema, table = full_table_name.rsplit(".", 1)
        else:
            schema = "public"
            table = full_table_name

        safe_name = _sanitize_tool_name(f"{schema}_{table}")

        # List tool
        tools[f"list_{safe_name}"] = {
            "kind": "postgres-sql",
            "source": source_name,
            "description": f"List rows from {schema}.{table}",
            "statement": f"SELECT * FROM {schema}.{table} ORDER BY 1 DESC LIMIT $1",
            "parameters": [
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "Maximum rows to return",
                    "default": 100,
                }
            ],
        }

        # Count tool
        tools[f"count_{safe_name}"] = {
            "kind": "postgres-sql",
            "source": source_name,
            "description": f"Count rows in {schema}.{table}",
            "statement": f"SELECT COUNT(*) as count FROM {schema}.{table}",
        }

    return tools


def _sanitize_tool_name(name: str) -> str:
    """Convert name to valid tool identifier."""
    # Replace non-alphanumeric with underscore
    name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    # Lowercase
    return name.lower()


def _openapi_type_to_toolbox(openapi_type: str) -> str:
    """Map OpenAPI types to Toolbox parameter types."""
    mapping = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "array": "array",
        "object": "object",
    }
    return mapping.get(openapi_type, "string")


def generate_toolset(tools: dict[str, Any], name: str, description: str) -> dict[str, Any]:
    """Generate a toolset from tool names."""
    return {name: list(tools.keys())}


def merge_configs(base: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    """Merge generated config into base config."""
    result = dict(base)

    # Merge tools
    if "tools" not in result:
        result["tools"] = {}
    result["tools"].update(generated.get("tools", {}))

    # Merge toolsets
    if "toolsets" not in result:
        result["toolsets"] = {}
    result["toolsets"].update(generated.get("toolsets", {}))

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate Toolbox tool definitions from specs and schemas"
    )
    parser.add_argument(
        "--openapi",
        type=Path,
        help="Path to OpenAPI specification YAML",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        help="Path to SQL schema file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate from all known sources",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("generated_tools.yaml"),
        help="Output file path",
    )
    parser.add_argument(
        "--source-name",
        default="workbench_pg",
        help="Source name to reference in tools",
    )
    parser.add_argument(
        "--merge-with",
        type=Path,
        help="Merge output with existing tools.yaml",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format",
    )

    args = parser.parse_args()

    # Find repo root
    repo_root = Path(__file__).parent.parent.parent

    generated = {"tools": {}, "toolsets": {}}

    # Process OpenAPI spec
    if args.openapi or args.all:
        openapi_path = args.openapi or repo_root / "specs" / "openapi" / "openapi.yaml"
        if openapi_path.exists():
            print(f"Processing OpenAPI spec: {openapi_path}")
            spec = load_openapi_spec(openapi_path)
            api_tools = openapi_to_tools(spec, "workbench_api")
            generated["tools"].update(api_tools)
            generated["toolsets"]["api"] = list(api_tools.keys())
            print(f"  Generated {len(api_tools)} API tools")
        else:
            print(f"Warning: OpenAPI spec not found at {openapi_path}")

    # Process SQL schema
    if args.schema or args.all:
        schema_path = args.schema or repo_root / "db" / "schema.sql"
        if schema_path.exists():
            print(f"Processing SQL schema: {schema_path}")
            schema_sql = load_sql_schema(schema_path)
            schema_tools = schema_to_tools(schema_sql, args.source_name)
            generated["tools"].update(schema_tools)
            generated["toolsets"]["schema"] = list(schema_tools.keys())
            print(f"  Generated {len(schema_tools)} schema tools")
        else:
            print(f"Warning: SQL schema not found at {schema_path}")

    # Also process migrations
    if args.all:
        migrations_dir = repo_root / "db" / "migrations"
        if migrations_dir.exists():
            for migration_file in sorted(migrations_dir.glob("*.sql")):
                print(f"Processing migration: {migration_file}")
                schema_sql = load_sql_schema(migration_file)
                migration_tools = schema_to_tools(schema_sql, args.source_name)
                generated["tools"].update(migration_tools)
                print(f"  Generated {len(migration_tools)} tools from migration")

    # Merge with existing config if requested
    if args.merge_with and args.merge_with.exists():
        print(f"Merging with existing config: {args.merge_with}")
        with open(args.merge_with) as f:
            base = yaml.safe_load(f)
        generated = merge_configs(base, generated)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "yaml":
        with open(args.output, "w") as f:
            yaml.dump(generated, f, default_flow_style=False, sort_keys=False)
    else:
        with open(args.output, "w") as f:
            json.dump(generated, f, indent=2)

    print(f"\nGenerated tools written to: {args.output}")
    print(f"Total tools: {len(generated.get('tools', {}))}")
    print(f"Toolsets: {list(generated.get('toolsets', {}).keys())}")


if __name__ == "__main__":
    main()
