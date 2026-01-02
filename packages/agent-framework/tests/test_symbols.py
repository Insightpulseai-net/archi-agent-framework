"""
Tests for the @ Symbols Context Injection System.
"""

import pytest
from pathlib import Path
import tempfile

from pulser_agents.symbols import (
    SymbolParser,
    Symbol,
    SymbolType,
    ParseResult,
    SymbolResolver,
    ResolutionContext,
    ResolvedSymbol,
)


class TestSymbolType:
    """Tests for SymbolType enum."""

    def test_symbol_types(self):
        """Test all symbol types exist."""
        assert SymbolType.FILE == "file"
        assert SymbolType.FOLDER == "folder"
        assert SymbolType.CODE == "code"
        assert SymbolType.DOCS == "docs"
        assert SymbolType.WEB == "web"
        assert SymbolType.GIT == "git"
        assert SymbolType.RULES == "rules"


class TestSymbol:
    """Tests for Symbol dataclass."""

    def test_symbol_creation(self):
        """Test symbol creation."""
        symbol = Symbol(
            type=SymbolType.FILE,
            value="src/main.py",
            raw="@src/main.py",
            start=0,
            end=12,
        )
        assert symbol.type == SymbolType.FILE
        assert symbol.value == "src/main.py"
        assert symbol.is_file_reference

    def test_is_file_reference(self):
        """Test file reference detection."""
        file_symbol = Symbol(
            type=SymbolType.FILE,
            value="test.py",
            raw="@test.py",
            start=0,
            end=8,
        )
        folder_symbol = Symbol(
            type=SymbolType.FOLDER,
            value="src/",
            raw="@src/",
            start=0,
            end=5,
        )
        code_symbol = Symbol(
            type=SymbolType.CODE,
            value="MyClass",
            raw="@MyClass",
            start=0,
            end=8,
        )

        assert file_symbol.is_file_reference
        assert folder_symbol.is_file_reference
        assert not code_symbol.is_file_reference


class TestSymbolParser:
    """Tests for SymbolParser."""

    @pytest.fixture
    def parser(self):
        return SymbolParser()

    def test_parse_file_reference(self, parser):
        """Test parsing file references."""
        result = parser.parse("Look at @src/api/users.py for auth")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.FILE
        assert result.symbols[0].value == "src/api/users.py"

    def test_parse_folder_reference(self, parser):
        """Test parsing folder references."""
        result = parser.parse("Check @src/components/ folder")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.FOLDER
        assert result.symbols[0].value == "src/components"

    def test_parse_docs_reference(self, parser):
        """Test parsing docs references."""
        result = parser.parse("See @docs:authentication for details")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.DOCS
        assert result.symbols[0].value == "authentication"

    def test_parse_git_reference(self, parser):
        """Test parsing git references."""
        result = parser.parse("Check @git:log for history")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.GIT
        assert result.symbols[0].value == "log"

    def test_parse_web_reference(self, parser):
        """Test parsing web search references."""
        result = parser.parse("Search @web:python-async-patterns")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.WEB
        assert result.symbols[0].value == "python-async-patterns"

    def test_parse_rules_reference(self, parser):
        """Test parsing rules references."""
        result = parser.parse("Apply @rules:python-style")

        assert len(result.symbols) == 1
        assert result.symbols[0].type == SymbolType.RULES
        assert result.symbols[0].value == "python-style"

    def test_parse_multiple_symbols(self, parser):
        """Test parsing multiple symbols."""
        result = parser.parse("Compare @src/old.py with @src/new.py")

        assert len(result.symbols) == 2
        assert result.symbols[0].value == "src/old.py"
        assert result.symbols[1].value == "src/new.py"

    def test_parse_no_symbols(self, parser):
        """Test parsing text without symbols."""
        result = parser.parse("Just regular text without symbols")

        assert len(result.symbols) == 0
        assert result.cleaned == "Just regular text without symbols"

    def test_cleaned_text(self, parser):
        """Test symbol removal from text."""
        result = parser.parse("Check @src/main.py for the bug")

        assert "@src/main.py" not in result.cleaned
        assert "Check" in result.cleaned
        assert "for the bug" in result.cleaned

    def test_has_symbols(self, parser):
        """Test checking for symbols."""
        assert parser.has_symbols("Look at @file.py")
        assert not parser.has_symbols("No symbols here")

    def test_count_symbols(self, parser):
        """Test counting symbols."""
        assert parser.count_symbols("@a @b @c") == 3
        assert parser.count_symbols("no symbols") == 0

    def test_extract_file_references(self, parser):
        """Test extracting just file paths."""
        files = parser.extract_file_references("@a.py @b.js @docs:api")

        assert len(files) == 2
        assert "a.py" in files
        assert "b.js" in files


class TestParseResult:
    """Tests for ParseResult."""

    def test_get_symbols_by_type(self):
        """Test filtering symbols by type."""
        symbols = [
            Symbol(SymbolType.FILE, "a.py", "@a.py", 0, 5),
            Symbol(SymbolType.FILE, "b.py", "@b.py", 6, 11),
            Symbol(SymbolType.DOCS, "api", "@docs:api", 12, 21),
        ]
        result = ParseResult(original="test", symbols=symbols)

        file_symbols = result.get_symbols_by_type(SymbolType.FILE)
        assert len(file_symbols) == 2

        docs_symbols = result.get_symbols_by_type(SymbolType.DOCS)
        assert len(docs_symbols) == 1


class TestSymbolResolver:
    """Tests for SymbolResolver."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create files
            (path / "main.py").write_text("def main():\n    pass\n")
            (path / "utils.py").write_text("def helper():\n    pass\n")

            # Create subdirectory
            (path / "src").mkdir()
            (path / "src" / "api.py").write_text("# API module\n")

            # Create docs
            (path / "docs").mkdir()
            (path / "docs" / "api.md").write_text("# API Documentation\n")

            yield path

    @pytest.fixture
    def resolver(self, temp_project):
        return SymbolResolver(
            context=ResolutionContext(base_path=temp_project)
        )

    @pytest.mark.asyncio
    async def test_resolve_file(self, resolver):
        """Test resolving file references."""
        symbol = Symbol(
            type=SymbolType.FILE,
            value="main.py",
            raw="@main.py",
            start=0,
            end=8,
        )
        resolved = await resolver.resolve(symbol)

        assert resolved.success
        assert "def main():" in resolved.content

    @pytest.mark.asyncio
    async def test_resolve_file_not_found(self, resolver):
        """Test resolving non-existent file."""
        symbol = Symbol(
            type=SymbolType.FILE,
            value="nonexistent.py",
            raw="@nonexistent.py",
            start=0,
            end=15,
        )
        resolved = await resolver.resolve(symbol)

        assert not resolved.success
        assert "not found" in resolved.error.lower()

    @pytest.mark.asyncio
    async def test_resolve_folder(self, resolver):
        """Test resolving folder references."""
        symbol = Symbol(
            type=SymbolType.FOLDER,
            value="src",
            raw="@src/",
            start=0,
            end=5,
        )
        resolved = await resolver.resolve(symbol)

        assert resolved.success
        assert "api.py" in resolved.content

    @pytest.mark.asyncio
    async def test_resolve_docs(self, resolver):
        """Test resolving documentation references."""
        symbol = Symbol(
            type=SymbolType.DOCS,
            value="api",
            raw="@docs:api",
            start=0,
            end=9,
        )
        resolved = await resolver.resolve(symbol)

        assert resolved.success
        assert "API Documentation" in resolved.content

    @pytest.mark.asyncio
    async def test_resolve_all(self, resolver):
        """Test resolving multiple symbols."""
        symbols = [
            Symbol(SymbolType.FILE, "main.py", "@main.py", 0, 8),
            Symbol(SymbolType.FILE, "utils.py", "@utils.py", 9, 18),
        ]
        resolved = await resolver.resolve_all(symbols)

        assert len(resolved) == 2
        assert all(r.success for r in resolved)

    @pytest.mark.asyncio
    async def test_build_context(self, resolver):
        """Test building combined context string."""
        symbols = [
            Symbol(SymbolType.FILE, "main.py", "@main.py", 0, 8),
        ]
        resolved = await resolver.resolve_all(symbols)
        context = resolver.build_context(resolved)

        assert "main.py" in context
        assert "def main():" in context


class TestResolvedSymbol:
    """Tests for ResolvedSymbol."""

    def test_to_context_string_file(self):
        """Test context string for file symbol."""
        symbol = Symbol(SymbolType.FILE, "test.py", "@test.py", 0, 8)
        resolved = ResolvedSymbol(
            symbol=symbol,
            content="print('hello')",
        )

        context = resolved.to_context_string()
        assert "test.py" in context
        assert "python" in context  # Language detection
        assert "print('hello')" in context

    def test_to_context_string_error(self):
        """Test context string for failed resolution."""
        symbol = Symbol(SymbolType.FILE, "missing.py", "@missing.py", 0, 11)
        resolved = ResolvedSymbol(
            symbol=symbol,
            success=False,
            error="File not found",
        )

        context = resolved.to_context_string()
        assert "Error" in context
        assert "File not found" in context
