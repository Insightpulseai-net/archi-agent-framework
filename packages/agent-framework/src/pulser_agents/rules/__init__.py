"""
Rules System for Pulser Agent Framework.

Implements a Cursor-style rules system with:
- YAML frontmatter metadata
- Glob-based auto-attachment
- Rule types: always, auto_attached, agent_requested, manual
- Project rules (.cursor/rules pattern)
- Team rules support

Example:
    >>> from pulser_agents.rules import RulesEngine, Rule, RuleType
    >>>
    >>> engine = RulesEngine()
    >>> await engine.load_project_rules("/path/to/project")
    >>>
    >>> # Get applicable rules for a file
    >>> rules = engine.get_rules_for_file("src/api/users.py")
"""

from pulser_agents.rules.engine import RulesEngine
from pulser_agents.rules.models import (
    Rule,
    RuleMetadata,
    RuleType,
    RulePolicy,
    RuleViolation,
    RuleEvaluationResult,
)
from pulser_agents.rules.loader import RuleLoader
from pulser_agents.rules.middleware import RulesMiddleware

__all__ = [
    "RulesEngine",
    "Rule",
    "RuleMetadata",
    "RuleType",
    "RulePolicy",
    "RuleViolation",
    "RuleEvaluationResult",
    "RuleLoader",
    "RulesMiddleware",
]
