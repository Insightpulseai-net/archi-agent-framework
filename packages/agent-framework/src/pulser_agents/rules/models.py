"""
Data models for the rules system.

Defines Rule, RuleMetadata, RuleType, and related types.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """
    Types of rules and how they are applied.

    - ALWAYS: Always included in model context
    - AUTO_ATTACHED: Applied when files match glob patterns
    - AGENT_REQUESTED: Agent can request based on description
    - MANUAL: Only when explicitly referenced
    """

    ALWAYS = "always"
    AUTO_ATTACHED = "auto_attached"
    AGENT_REQUESTED = "agent_requested"
    MANUAL = "manual"


class RuleMetadata(BaseModel):
    """
    YAML frontmatter metadata for a rule.

    Attributes:
        description: Human-readable purpose of the rule
        globs: File patterns for auto-attached rules
        always_apply: Always include in context
        priority: Rule priority (higher = more important)
        tags: Optional tags for categorization
    """

    description: str | None = None
    globs: list[str] = Field(default_factory=list)
    always_apply: bool = False
    priority: int = 0
    tags: list[str] = Field(default_factory=list)
    version: str | None = None
    author: str | None = None

    @property
    def rule_type(self) -> RuleType:
        """Determine the rule type from metadata."""
        if self.always_apply:
            return RuleType.ALWAYS
        if self.globs:
            return RuleType.AUTO_ATTACHED
        if self.description:
            return RuleType.AGENT_REQUESTED
        return RuleType.MANUAL


class Rule(BaseModel):
    """
    A rule definition with content and metadata.

    Attributes:
        id: Unique rule identifier
        name: Rule name (derived from filename)
        path: Path to the rule file
        content: Rule content (markdown)
        metadata: YAML frontmatter metadata
        source: Where the rule came from (project, user, team)
        created_at: When the rule was created
        updated_at: When the rule was last updated
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    path: Path | None = None
    content: str
    metadata: RuleMetadata = Field(default_factory=RuleMetadata)
    source: str = "project"  # project, user, team
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    @property
    def rule_type(self) -> RuleType:
        """Get the rule type."""
        return self.metadata.rule_type

    @property
    def globs(self) -> list[str]:
        """Get glob patterns."""
        return self.metadata.globs

    @property
    def description(self) -> str | None:
        """Get rule description."""
        return self.metadata.description

    def matches_file(self, file_path: str) -> bool:
        """Check if this rule applies to a file path."""
        from fnmatch import fnmatch

        if not self.globs:
            return False

        for pattern in self.globs:
            if fnmatch(file_path, pattern):
                return True
        return False

    def to_context_string(self) -> str:
        """Convert rule to a string for LLM context."""
        parts = []
        if self.metadata.description:
            parts.append(f"# {self.metadata.description}")
        parts.append(self.content)
        return "\n\n".join(parts)


class RulePolicy(BaseModel):
    """
    Policy for how rule violations are handled.

    Attributes:
        on_violation: Action to take (allow, deny, warn, modify)
        rules: List of rules in this policy
        name: Policy name
        enabled: Whether policy is active
    """

    class ViolationAction(str, Enum):
        ALLOW = "allow"
        DENY = "deny"
        WARN = "warn"
        MODIFY = "modify"

    name: str
    rules: list[Rule] = Field(default_factory=list)
    on_violation: ViolationAction = ViolationAction.WARN
    enabled: bool = True
    priority: int = 0

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the policy."""
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                return True
        return False


class RuleViolation(BaseModel):
    """
    Record of a rule violation.

    Attributes:
        rule: The violated rule
        message: Violation message
        severity: Violation severity
        context: Additional context
    """

    class Severity(str, Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"

    rule: Rule
    message: str
    severity: Severity = Severity.WARNING
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class RuleEvaluationResult(BaseModel):
    """
    Result of evaluating rules against a request.

    Attributes:
        passed: Whether all rules passed
        applied_rules: Rules that were applied
        violations: Any rule violations
        injected_context: Context to inject into the request
    """

    passed: bool = True
    applied_rules: list[Rule] = Field(default_factory=list)
    violations: list[RuleViolation] = Field(default_factory=list)
    injected_context: str = ""
    evaluation_time_ms: float = 0.0

    class Config:
        arbitrary_types_allowed = True

    def add_violation(self, violation: RuleViolation) -> None:
        """Add a violation."""
        self.violations.append(violation)
        if violation.severity in (
            RuleViolation.Severity.ERROR,
            RuleViolation.Severity.CRITICAL,
        ):
            self.passed = False

    def add_rule(self, rule: Rule) -> None:
        """Add an applied rule."""
        self.applied_rules.append(rule)
        if self.injected_context:
            self.injected_context += "\n\n"
        self.injected_context += rule.to_context_string()
