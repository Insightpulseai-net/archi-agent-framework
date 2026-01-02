"""
Rule loader for parsing rule files with YAML frontmatter.

Handles loading rules from:
- Project rules (.cursor/rules/, .pulser/rules/)
- AGENTS.md files
- User rules
- Team rules
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from pulser_agents.rules.models import Rule, RuleMetadata


class RuleLoader:
    """
    Loads rules from various sources.

    Supports:
    - Markdown files with YAML frontmatter
    - AGENTS.md simple markdown
    - Directory-based rule organization
    """

    # Pattern for YAML frontmatter
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n(.*)$",
        re.DOTALL,
    )

    # Default rule directories to search
    DEFAULT_RULE_DIRS = [
        ".cursor/rules",
        ".pulser/rules",
        ".agent/rules",
    ]

    # Default AGENTS.md locations
    AGENTS_MD_FILES = [
        "AGENTS.md",
        ".cursor/AGENTS.md",
        ".pulser/AGENTS.md",
    ]

    def __init__(self, base_path: Path | str | None = None) -> None:
        """
        Initialize the rule loader.

        Args:
            base_path: Base path for relative rule lookups
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def load_file(self, file_path: Path | str) -> Rule:
        """
        Load a single rule from a file.

        Args:
            file_path: Path to the rule file

        Returns:
            Parsed Rule object
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_rule(content, name=path.stem, path=path)

    def parse_rule(
        self,
        content: str,
        name: str = "unnamed",
        path: Path | None = None,
        source: str = "project",
    ) -> Rule:
        """
        Parse rule content with optional YAML frontmatter.

        Args:
            content: Raw rule content
            name: Rule name
            path: Optional file path
            source: Rule source (project, user, team)

        Returns:
            Parsed Rule object
        """
        metadata = RuleMetadata()
        body = content

        # Try to extract YAML frontmatter
        match = self.FRONTMATTER_PATTERN.match(content)
        if match:
            frontmatter_str, body = match.groups()
            try:
                frontmatter_data = yaml.safe_load(frontmatter_str) or {}
                metadata = self._parse_metadata(frontmatter_data)
            except yaml.YAMLError:
                # If YAML parsing fails, treat entire content as body
                body = content

        return Rule(
            name=name,
            path=path,
            content=body.strip(),
            metadata=metadata,
            source=source,
        )

    def _parse_metadata(self, data: dict[str, Any]) -> RuleMetadata:
        """Parse frontmatter data into RuleMetadata."""
        # Handle various key formats
        globs = data.get("globs", data.get("glob", []))
        if isinstance(globs, str):
            globs = [globs]

        always_apply = data.get("alwaysApply", data.get("always_apply", False))

        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        return RuleMetadata(
            description=data.get("description"),
            globs=globs,
            always_apply=always_apply,
            priority=data.get("priority", 0),
            tags=tags,
            version=data.get("version"),
            author=data.get("author"),
        )

    def load_directory(self, dir_path: Path | str) -> list[Rule]:
        """
        Load all rules from a directory.

        Args:
            dir_path: Path to rules directory

        Returns:
            List of parsed rules
        """
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists() or not path.is_dir():
            return []

        rules = []
        for file_path in path.rglob("*.md"):
            try:
                rule = self.load_file(file_path)
                rules.append(rule)
            except Exception:
                # Skip files that fail to parse
                continue

        # Sort by priority (higher first)
        rules.sort(key=lambda r: r.metadata.priority, reverse=True)
        return rules

    def load_project_rules(self, project_path: Path | str | None = None) -> list[Rule]:
        """
        Load all project rules from standard locations.

        Searches:
        - .cursor/rules/
        - .pulser/rules/
        - AGENTS.md

        Args:
            project_path: Path to project root

        Returns:
            List of all project rules
        """
        base = Path(project_path) if project_path else self.base_path
        all_rules = []

        # Load from rule directories
        for rule_dir in self.DEFAULT_RULE_DIRS:
            dir_path = base / rule_dir
            if dir_path.exists():
                rules = self.load_directory(dir_path)
                all_rules.extend(rules)

        # Load AGENTS.md files
        for agents_file in self.AGENTS_MD_FILES:
            file_path = base / agents_file
            if file_path.exists():
                try:
                    rule = self.load_file(file_path)
                    rule.metadata.always_apply = True  # AGENTS.md is always applied
                    all_rules.append(rule)
                except Exception:
                    continue

        return all_rules

    def load_from_string(
        self,
        content: str,
        name: str = "inline",
        source: str = "inline",
    ) -> Rule:
        """
        Load a rule from a string.

        Args:
            content: Rule content
            name: Rule name
            source: Rule source

        Returns:
            Parsed Rule object
        """
        return self.parse_rule(content, name=name, source=source)

    def create_rule(
        self,
        name: str,
        content: str,
        description: str | None = None,
        globs: list[str] | None = None,
        always_apply: bool = False,
        tags: list[str] | None = None,
    ) -> Rule:
        """
        Create a new rule programmatically.

        Args:
            name: Rule name
            content: Rule content
            description: Rule description
            globs: File patterns for auto-attachment
            always_apply: Whether to always apply
            tags: Optional tags

        Returns:
            New Rule object
        """
        metadata = RuleMetadata(
            description=description,
            globs=globs or [],
            always_apply=always_apply,
            tags=tags or [],
        )
        return Rule(
            name=name,
            content=content,
            metadata=metadata,
            source="programmatic",
        )
