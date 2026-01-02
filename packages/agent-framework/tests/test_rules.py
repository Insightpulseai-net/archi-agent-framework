"""
Tests for the Rules System.
"""

import pytest
from pathlib import Path
import tempfile

from pulser_agents.rules import (
    Rule,
    RuleMetadata,
    RuleType,
    RuleLoader,
    RulesEngine,
    RuleEvaluationResult,
)


class TestRuleMetadata:
    """Tests for RuleMetadata."""

    def test_rule_type_always(self):
        """Test always_apply determines ALWAYS type."""
        metadata = RuleMetadata(always_apply=True)
        assert metadata.rule_type == RuleType.ALWAYS

    def test_rule_type_auto_attached(self):
        """Test globs determine AUTO_ATTACHED type."""
        metadata = RuleMetadata(globs=["*.py"])
        assert metadata.rule_type == RuleType.AUTO_ATTACHED

    def test_rule_type_agent_requested(self):
        """Test description determines AGENT_REQUESTED type."""
        metadata = RuleMetadata(description="Test rule")
        assert metadata.rule_type == RuleType.AGENT_REQUESTED

    def test_rule_type_manual(self):
        """Test empty metadata is MANUAL type."""
        metadata = RuleMetadata()
        assert metadata.rule_type == RuleType.MANUAL


class TestRule:
    """Tests for Rule model."""

    def test_rule_creation(self):
        """Test basic rule creation."""
        rule = Rule(
            name="test-rule",
            content="# Test Rule\nSome content",
        )
        assert rule.name == "test-rule"
        assert rule.content == "# Test Rule\nSome content"
        assert rule.id  # Should have auto-generated ID

    def test_matches_file_with_glob(self):
        """Test file matching with glob patterns."""
        rule = Rule(
            name="python-rules",
            content="Python rules",
            metadata=RuleMetadata(globs=["*.py", "src/**/*.py"]),
        )
        assert rule.matches_file("test.py")
        assert rule.matches_file("src/api/users.py")
        assert not rule.matches_file("test.js")

    def test_to_context_string(self):
        """Test context string generation."""
        rule = Rule(
            name="test",
            content="Use TypeScript",
            metadata=RuleMetadata(description="TypeScript rules"),
        )
        context = rule.to_context_string()
        assert "TypeScript rules" in context
        assert "Use TypeScript" in context


class TestRuleLoader:
    """Tests for RuleLoader."""

    def test_parse_rule_with_frontmatter(self):
        """Test parsing rule with YAML frontmatter."""
        content = """---
description: "API development rules"
globs:
  - "src/api/**/*.ts"
alwaysApply: false
---

# API Rules

- Use REST conventions
- Return proper status codes
"""
        loader = RuleLoader()
        rule = loader.parse_rule(content, name="api-rules")

        assert rule.name == "api-rules"
        assert rule.metadata.description == "API development rules"
        assert "src/api/**/*.ts" in rule.metadata.globs
        assert "Use REST conventions" in rule.content

    def test_parse_rule_without_frontmatter(self):
        """Test parsing plain markdown rule."""
        content = """# Simple Rule

Just some content without frontmatter.
"""
        loader = RuleLoader()
        rule = loader.parse_rule(content, name="simple")

        assert rule.name == "simple"
        assert rule.metadata.description is None
        assert "Simple Rule" in rule.content

    def test_create_rule_programmatically(self):
        """Test creating rules programmatically."""
        loader = RuleLoader()
        rule = loader.create_rule(
            name="coding-standards",
            content="Use 4 spaces for indentation",
            description="Code style rules",
            globs=["*.py"],
            tags=["style", "python"],
        )

        assert rule.name == "coding-standards"
        assert rule.metadata.description == "Code style rules"
        assert rule.metadata.globs == ["*.py"]
        assert "style" in rule.metadata.tags

    def test_load_directory(self):
        """Test loading rules from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / ".cursor" / "rules"
            rules_dir.mkdir(parents=True)

            # Create test rule files
            (rules_dir / "python.md").write_text("""---
description: "Python rules"
globs: ["*.py"]
---
Use type hints
""")
            (rules_dir / "typescript.md").write_text("""---
description: "TypeScript rules"
globs: ["*.ts"]
---
Use strict mode
""")

            loader = RuleLoader(base_path=tmpdir)
            rules = loader.load_directory(rules_dir)

            assert len(rules) == 2
            names = [r.name for r in rules]
            assert "python" in names
            assert "typescript" in names


class TestRulesEngine:
    """Tests for RulesEngine."""

    def test_add_and_get_rule(self):
        """Test adding and retrieving rules."""
        engine = RulesEngine()
        rule = Rule(name="test", content="Test content")
        engine.add_rule(rule)

        assert engine.rule_count == 1
        assert engine.get_rule(rule.id) == rule
        assert engine.get_rule_by_name("test") == rule

    def test_evaluate_always_rules(self):
        """Test evaluation includes always rules."""
        engine = RulesEngine()
        always_rule = Rule(
            name="always-rule",
            content="Always apply this",
            metadata=RuleMetadata(always_apply=True),
        )
        engine.add_rule(always_rule)

        result = engine.evaluate()
        assert len(result.applied_rules) == 1
        assert result.applied_rules[0].name == "always-rule"

    def test_evaluate_auto_attached_rules(self):
        """Test evaluation matches auto-attached rules by file."""
        engine = RulesEngine()
        python_rule = Rule(
            name="python-rule",
            content="Python specific",
            metadata=RuleMetadata(globs=["*.py", "**/*.py"]),
        )
        engine.add_rule(python_rule)

        result = engine.evaluate(file_path="src/main.py")
        assert len(result.applied_rules) == 1

        result = engine.evaluate(file_path="src/main.js")
        assert len(result.applied_rules) == 0

    def test_evaluate_requested_rules(self):
        """Test evaluation with explicitly requested rules."""
        engine = RulesEngine()
        manual_rule = Rule(
            name="manual-rule",
            content="Manual content",
        )
        engine.add_rule(manual_rule)

        # Not included by default
        result = engine.evaluate()
        assert len(result.applied_rules) == 0

        # Included when requested
        result = engine.evaluate(include_requested=["manual-rule"])
        assert len(result.applied_rules) == 1

    def test_get_context_for_file(self):
        """Test getting combined context for a file."""
        engine = RulesEngine()
        engine.add_rule(Rule(
            name="always",
            content="Always rule content",
            metadata=RuleMetadata(always_apply=True),
        ))
        engine.add_rule(Rule(
            name="python",
            content="Python rule content",
            metadata=RuleMetadata(globs=["*.py"]),
        ))

        context = engine.get_context_for_file("test.py")
        assert "Always rule content" in context
        assert "Python rule content" in context

    def test_reload_rules(self):
        """Test reloading rules."""
        engine = RulesEngine()
        engine.add_rule(Rule(name="old", content="Old rule"))
        assert engine.rule_count == 1

        engine.clear_rules()
        assert engine.rule_count == 0


class TestRuleEvaluationResult:
    """Tests for RuleEvaluationResult."""

    def test_add_rule_builds_context(self):
        """Test adding rules builds injected context."""
        result = RuleEvaluationResult()
        result.add_rule(Rule(name="r1", content="Content 1"))
        result.add_rule(Rule(name="r2", content="Content 2"))

        assert "Content 1" in result.injected_context
        assert "Content 2" in result.injected_context
        assert len(result.applied_rules) == 2
