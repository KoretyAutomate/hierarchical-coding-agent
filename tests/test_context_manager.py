"""Tests for core.context_manager module."""
import os
import tempfile
import time
from pathlib import Path

import pytest

from core.context_manager import ContextManager, CodeStructure, _CacheEntry


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project structure for testing."""
    # Create a Python file
    py_file = tmp_path / "example.py"
    py_file.write_text(
        '"""Module docstring."""\n'
        "import os\n"
        "from pathlib import Path\n\n"
        "class Foo:\n"
        '    """A test class."""\n'
        "    def bar(self, x):\n"
        "        return x\n\n"
        "def standalone(a, b):\n"
        "    return a + b\n"
    )
    # Create a subdirectory with another file
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "helper.py").write_text("def helper(): pass\n")
    # Create a non-Python file
    (tmp_path / "README.md").write_text("# Project\n")
    # Create a .gitignore
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\n")
    return tmp_path


@pytest.fixture
def cm(tmp_project):
    return ContextManager(str(tmp_project))


class TestContextManagerInit:
    def test_project_root_resolved(self, cm, tmp_project):
        assert cm.project_root == tmp_project.resolve()

    def test_gitignore_loaded(self, cm):
        assert "*.log" in cm.ignore_patterns
        assert "build/" in cm.ignore_patterns


class TestShouldIgnore:
    def test_ignores_pycache(self, cm):
        assert cm._should_ignore(Path("__pycache__"))

    def test_ignores_pyc_files(self, cm):
        assert cm._should_ignore(Path("foo.pyc"))

    def test_ignores_custom_pattern(self, cm):
        assert cm._should_ignore(Path("debug.log"))

    def test_does_not_ignore_normal_file(self, cm):
        assert not cm._should_ignore(Path("main.py"))


class TestParsePythonFile:
    def test_parses_classes(self, cm, tmp_project):
        result = cm.parse_python_file(str(tmp_project / "example.py"))
        assert result is not None
        assert len(result.classes) == 1
        assert result.classes[0]["name"] == "Foo"

    def test_parses_functions(self, cm, tmp_project):
        result = cm.parse_python_file(str(tmp_project / "example.py"))
        assert len(result.functions) == 1
        assert result.functions[0]["name"] == "standalone"

    def test_parses_imports(self, cm, tmp_project):
        result = cm.parse_python_file(str(tmp_project / "example.py"))
        assert "os" in result.imports

    def test_parses_module_docstring(self, cm, tmp_project):
        result = cm.parse_python_file(str(tmp_project / "example.py"))
        assert result.module_docstring == "Module docstring."

    def test_returns_none_for_nonexistent(self, cm):
        assert cm.parse_python_file("nonexistent.py") is None

    def test_returns_none_for_non_python(self, cm, tmp_project):
        assert cm.parse_python_file(str(tmp_project / "README.md")) is None

    def test_caching(self, cm, tmp_project):
        path = str(tmp_project / "example.py")
        result1 = cm.parse_python_file(path)
        result2 = cm.parse_python_file(path)
        # Should return the same cached object
        assert result1 is result2

    def test_cache_invalidation_on_mtime_change(self, cm, tmp_project):
        path = tmp_project / "example.py"
        result1 = cm.parse_python_file(str(path))
        # Modify the file
        time.sleep(0.05)
        path.write_text("def new_func(): pass\n")
        result2 = cm.parse_python_file(str(path))
        assert result1 is not result2
        assert result2.functions[0]["name"] == "new_func"


class TestEstimateTokens:
    def test_estimate(self, cm):
        text = "a" * 400
        assert cm.estimate_tokens(text) == 100

    def test_file_tokens_cached(self, cm, tmp_project):
        path = str(tmp_project / "example.py")
        t1 = cm.estimate_file_tokens(path)
        t2 = cm.estimate_file_tokens(path)
        assert t1 == t2
        assert t1 > 0


class TestGetProjectStructure:
    def test_returns_string(self, cm):
        structure = cm.get_project_structure(max_depth=2)
        assert isinstance(structure, str)
        assert cm.project_root.name in structure

    def test_contains_files(self, cm):
        structure = cm.get_project_structure(max_depth=3)
        assert "example.py" in structure
        assert "README.md" in structure

    def test_caching(self, cm):
        s1 = cm.get_project_structure(max_depth=2)
        s2 = cm.get_project_structure(max_depth=2)
        assert s1 == s2


class TestAnalyzeProject:
    def test_counts_files(self, cm):
        stats = cm.analyze_project()
        assert stats["total_files"] >= 3  # example.py, helper.py, README.md
        assert stats["python_files"] >= 2

    def test_counts_classes(self, cm):
        stats = cm.analyze_project()
        assert stats["total_classes"] >= 1

    def test_caching(self, cm):
        s1 = cm.analyze_project()
        s2 = cm.analyze_project()
        assert s1 is s2  # Same dict object from cache


class TestGetContextForTask:
    def test_returns_context(self, cm):
        ctx = cm.get_context_for_task("add a new function", max_tokens=4000)
        assert isinstance(ctx, str)
        assert "Project Structure" in ctx
        assert "Project Statistics" in ctx

    def test_respects_token_budget(self, cm):
        ctx = cm.get_context_for_task("test", max_tokens=100)
        # Should still return something (structure is always included)
        assert len(ctx) > 0
