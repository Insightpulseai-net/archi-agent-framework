"""
Middleware for integrating rules into the agent pipeline.

Injects rule context into agent requests and validates responses.
"""

from __future__ import annotations

from typing import Any

from pulser_agents.core.response import RunResult
from pulser_agents.middleware.base import (
    Middleware,
    MiddlewareContext,
    NextHandler,
)
from pulser_agents.rules.engine import RulesEngine
from pulser_agents.rules.models import RuleEvaluationResult


class RulesMiddleware(Middleware):
    """
    Middleware that applies rules to agent requests.

    Injects rule context into the system prompt and tracks
    which rules were applied.

    Example:
        >>> engine = RulesEngine()
        >>> engine.load_project_rules("/path/to/project")
        >>>
        >>> middleware = RulesMiddleware(engine)
        >>> agent.add_middleware(middleware)
    """

    def __init__(
        self,
        rules_engine: RulesEngine,
        inject_as_system: bool = True,
        track_applied_rules: bool = True,
    ) -> None:
        """
        Initialize the rules middleware.

        Args:
            rules_engine: The rules engine to use
            inject_as_system: Whether to inject rules into system prompt
            track_applied_rules: Whether to track which rules were applied
        """
        self.rules_engine = rules_engine
        self.inject_as_system = inject_as_system
        self.track_applied_rules = track_applied_rules

    async def __call__(
        self,
        ctx: MiddlewareContext,
        next_handler: NextHandler,
    ) -> RunResult:
        """
        Process the request through the rules engine.

        Args:
            ctx: Middleware context
            next_handler: Next handler in chain

        Returns:
            Agent response
        """
        # Get file paths from context metadata
        file_paths = self._extract_file_paths(ctx)

        # Get requested rules from metadata
        requested_rules = ctx.get_metadata("requested_rules", [])

        # Evaluate rules
        result = self.rules_engine.evaluate(
            file_paths=file_paths,
            include_requested=requested_rules,
        )

        # Store evaluation result in metadata
        if self.track_applied_rules:
            ctx.set_metadata("rules_evaluation", result)
            ctx.set_metadata(
                "applied_rules",
                [r.name for r in result.applied_rules]
            )

        # Inject context if we have rules
        if result.injected_context and self.inject_as_system:
            self._inject_context(ctx, result)

        # Continue to next handler
        response = await next_handler(ctx)

        return response

    def _extract_file_paths(self, ctx: MiddlewareContext) -> list[str]:
        """Extract file paths from the middleware context."""
        paths = []

        # Check metadata for explicit file paths
        if ctx.metadata.get("file_paths"):
            paths.extend(ctx.metadata["file_paths"])

        if ctx.metadata.get("file_path"):
            paths.append(ctx.metadata["file_path"])

        # Check context variables if available
        if ctx.context:
            if ctx.context.has("file_paths"):
                paths.extend(ctx.context.get("file_paths", []))
            if ctx.context.has("file_path"):
                paths.append(ctx.context.get("file_path"))
            if ctx.context.has("current_file"):
                paths.append(ctx.context.get("current_file"))

        return paths

    def _inject_context(
        self,
        ctx: MiddlewareContext,
        result: RuleEvaluationResult,
    ) -> None:
        """Inject rule context into the request."""
        # Store the rules context for system prompt injection
        rules_header = "# Applied Rules\n\n"
        rules_content = rules_header + result.injected_context

        # Add to metadata for agent to pick up
        ctx.set_metadata("rules_context", rules_content)

        # If we have an agent context, add to variables
        if ctx.context:
            ctx.context.set("rules_context", rules_content)
            ctx.context.set(
                "applied_rules_summary",
                f"Applied {len(result.applied_rules)} rules"
            )


class RulesContextBuilder:
    """
    Helper for building rule context for LLM prompts.

    Combines rules with other context sources.
    """

    def __init__(self, rules_engine: RulesEngine) -> None:
        """
        Initialize the context builder.

        Args:
            rules_engine: Rules engine to use
        """
        self.rules_engine = rules_engine

    def build_system_context(
        self,
        file_paths: list[str] | None = None,
        additional_context: str | None = None,
        include_rule_names: bool = True,
    ) -> str:
        """
        Build a complete system context with rules.

        Args:
            file_paths: Files to get rules for
            additional_context: Extra context to include
            include_rule_names: Whether to include rule names

        Returns:
            Combined context string
        """
        parts = []

        # Get rule evaluation
        result = self.rules_engine.evaluate(file_paths=file_paths or [])

        # Add rule names header if enabled
        if include_rule_names and result.applied_rules:
            rule_names = [r.name for r in result.applied_rules]
            parts.append(f"# Active Rules: {', '.join(rule_names)}")
            parts.append("")

        # Add rule content
        if result.injected_context:
            parts.append(result.injected_context)

        # Add additional context
        if additional_context:
            parts.append("")
            parts.append(additional_context)

        return "\n".join(parts)

    def get_available_rules_prompt(self) -> str:
        """
        Get a prompt describing available rules for agent requests.

        Returns:
            Prompt string listing available rules
        """
        rules = self.rules_engine.get_agent_requestable_rules()

        if not rules:
            return "No additional rules are available for request."

        lines = ["# Available Rules", ""]
        lines.append("You can request the following rules by name:")
        lines.append("")

        for rule in rules:
            lines.append(f"- **{rule['name']}**: {rule['description']}")

        return "\n".join(lines)
