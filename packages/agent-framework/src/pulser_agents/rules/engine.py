"""
Rules engine for evaluating and applying rules.

The engine manages rule loading, matching, and context injection.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from pulser_agents.rules.loader import RuleLoader
from pulser_agents.rules.models import (
    Rule,
    RuleEvaluationResult,
    RulePolicy,
    RuleType,
)


class RulesEngine:
    """
    Engine for managing and evaluating rules.

    Handles:
    - Rule loading from multiple sources
    - Rule matching against files/contexts
    - Context injection for LLM prompts
    - Rule caching and updates

    Example:
        >>> engine = RulesEngine()
        >>> await engine.load_project_rules("/path/to/project")
        >>>
        >>> # Get rules for a specific file
        >>> result = engine.evaluate(file_path="src/api/users.py")
        >>> print(result.injected_context)
    """

    def __init__(self, base_path: Path | str | None = None) -> None:
        """
        Initialize the rules engine.

        Args:
            base_path: Base path for rule lookups
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.loader = RuleLoader(self.base_path)

        # Rule storage by type
        self._always_rules: list[Rule] = []
        self._auto_attached_rules: list[Rule] = []
        self._agent_requested_rules: list[Rule] = []
        self._manual_rules: list[Rule] = []

        # All rules indexed by ID
        self._rules_by_id: dict[str, Rule] = {}

        # Policies
        self._policies: list[RulePolicy] = []

    @property
    def all_rules(self) -> list[Rule]:
        """Get all loaded rules."""
        return list(self._rules_by_id.values())

    @property
    def rule_count(self) -> int:
        """Get total number of rules."""
        return len(self._rules_by_id)

    def load_project_rules(self, project_path: Path | str | None = None) -> int:
        """
        Load all project rules from standard locations.

        Args:
            project_path: Path to project root

        Returns:
            Number of rules loaded
        """
        path = Path(project_path) if project_path else self.base_path
        rules = self.loader.load_project_rules(path)

        for rule in rules:
            self.add_rule(rule)

        return len(rules)

    def add_rule(self, rule: Rule) -> None:
        """
        Add a rule to the engine.

        Args:
            rule: Rule to add
        """
        self._rules_by_id[rule.id] = rule

        # Categorize by type
        rule_type = rule.rule_type
        if rule_type == RuleType.ALWAYS:
            self._always_rules.append(rule)
        elif rule_type == RuleType.AUTO_ATTACHED:
            self._auto_attached_rules.append(rule)
        elif rule_type == RuleType.AGENT_REQUESTED:
            self._agent_requested_rules.append(rule)
        else:
            self._manual_rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule by ID.

        Args:
            rule_id: Rule ID to remove

        Returns:
            True if removed, False if not found
        """
        if rule_id not in self._rules_by_id:
            return False

        rule = self._rules_by_id.pop(rule_id)

        # Remove from categorized lists
        for rule_list in [
            self._always_rules,
            self._auto_attached_rules,
            self._agent_requested_rules,
            self._manual_rules,
        ]:
            for i, r in enumerate(rule_list):
                if r.id == rule_id:
                    rule_list.pop(i)
                    break

        return True

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID."""
        return self._rules_by_id.get(rule_id)

    def get_rule_by_name(self, name: str) -> Rule | None:
        """Get a rule by name."""
        for rule in self._rules_by_id.values():
            if rule.name == name:
                return rule
        return None

    def clear_rules(self) -> None:
        """Remove all rules."""
        self._always_rules.clear()
        self._auto_attached_rules.clear()
        self._agent_requested_rules.clear()
        self._manual_rules.clear()
        self._rules_by_id.clear()

    def evaluate(
        self,
        file_path: str | None = None,
        file_paths: list[str] | None = None,
        include_always: bool = True,
        include_requested: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RuleEvaluationResult:
        """
        Evaluate rules for a given context.

        Args:
            file_path: Single file path to match
            file_paths: Multiple file paths to match
            include_always: Include always-applied rules
            include_requested: Rule names/IDs to explicitly include
            context: Additional context for evaluation

        Returns:
            RuleEvaluationResult with matched rules and context
        """
        start_time = time.time()
        result = RuleEvaluationResult()

        # Collect all file paths
        paths = []
        if file_path:
            paths.append(file_path)
        if file_paths:
            paths.extend(file_paths)

        # Add always rules
        if include_always:
            for rule in self._always_rules:
                result.add_rule(rule)

        # Add auto-attached rules based on file paths
        for path in paths:
            for rule in self._auto_attached_rules:
                if rule.matches_file(path) and rule not in result.applied_rules:
                    result.add_rule(rule)

        # Add explicitly requested rules
        if include_requested:
            for identifier in include_requested:
                rule = self.get_rule(identifier) or self.get_rule_by_name(identifier)
                if rule and rule not in result.applied_rules:
                    result.add_rule(rule)

        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result

    def get_rules_for_file(self, file_path: str) -> list[Rule]:
        """
        Get all rules that apply to a file.

        Args:
            file_path: File path to match

        Returns:
            List of matching rules
        """
        result = self.evaluate(file_path=file_path)
        return result.applied_rules

    def get_context_for_file(self, file_path: str) -> str:
        """
        Get the combined context string for a file.

        Args:
            file_path: File path to get context for

        Returns:
            Combined rule content as a string
        """
        result = self.evaluate(file_path=file_path)
        return result.injected_context

    def get_agent_requestable_rules(self) -> list[dict[str, str]]:
        """
        Get rules that agents can request.

        Returns a list of rule summaries with name and description
        for agents to choose from.

        Returns:
            List of rule summaries
        """
        summaries = []
        for rule in self._agent_requested_rules:
            summaries.append({
                "id": rule.id,
                "name": rule.name,
                "description": rule.description or f"Rule: {rule.name}",
            })
        return summaries

    def add_policy(self, policy: RulePolicy) -> None:
        """Add a rule policy."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a policy by name."""
        for i, policy in enumerate(self._policies):
            if policy.name == policy_name:
                self._policies.pop(i)
                return True
        return False

    def reload(self, project_path: Path | str | None = None) -> int:
        """
        Reload all rules from the project.

        Args:
            project_path: Project path to reload from

        Returns:
            Number of rules loaded
        """
        self.clear_rules()
        return self.load_project_rules(project_path)

    def to_dict(self) -> dict[str, Any]:
        """Export engine state as dictionary."""
        return {
            "base_path": str(self.base_path),
            "rule_count": self.rule_count,
            "always_rules": len(self._always_rules),
            "auto_attached_rules": len(self._auto_attached_rules),
            "agent_requested_rules": len(self._agent_requested_rules),
            "manual_rules": len(self._manual_rules),
            "policies": len(self._policies),
        }
