"""Tests for tools.coding_tools module."""
import os
import subprocess
from pathlib import Path

import pytest

from tools.coding_tools import CodingTools


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a workspace with some files."""
    (tmp_path / "main.py").write_text("def hello():\n    print('hello')\n")
    (tmp_path / "utils.py").write_text("def add(a, b):\n    return a + b\n")
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "app.py").write_text("# app\nclass App: pass\n")
    return tmp_path


@pytest.fixture
def tools(tmp_workspace):
    return CodingTools(
        workspace_root=str(tmp_workspace),
        use_sandbox=False,
        enable_diff_review=False,
    )


class TestReadFile:
    def test_reads_existing_file(self, tools):
        result = tools.read_file("main.py")
        assert "def hello()" in result

    def test_returns_error_for_missing(self, tools):
        result = tools.read_file("nonexistent.py")
        assert "Error" in result


class TestWriteFile:
    def test_writes_new_file(self, tools, tmp_workspace):
        result = tools.write_file("new.py", "x = 1\n")
        assert "Successfully" in result
        assert (tmp_workspace / "new.py").read_text() == "x = 1\n"

    def test_creates_parent_dirs(self, tools, tmp_workspace):
        result = tools.write_file("deep/nested/file.py", "pass\n")
        assert "Successfully" in result
        assert (tmp_workspace / "deep" / "nested" / "file.py").exists()

    def test_overwrites_existing(self, tools, tmp_workspace):
        tools.write_file("main.py", "new content\n")
        assert (tmp_workspace / "main.py").read_text() == "new content\n"


class TestEditFile:
    def test_replaces_content(self, tools, tmp_workspace):
        result = tools.edit_file("main.py", "def hello():", "def greet():")
        assert "Successfully" in result
        assert "def greet():" in (tmp_workspace / "main.py").read_text()

    def test_error_when_old_not_found(self, tools):
        result = tools.edit_file("main.py", "nonexistent content", "new")
        assert "Error" in result


class TestListFiles:
    def test_lists_files(self, tools):
        result = tools.list_files()
        assert "main.py" in result
        assert "utils.py" in result

    def test_empty_for_bad_directory(self, tools):
        result = tools.list_files("nonexistent_dir")
        # Returns empty list or error - either is acceptable
        assert "Files:" in result or "Error" in result


class TestSearchCode:
    def test_finds_pattern(self, tools):
        result = tools.search_code("def hello")
        assert "main.py" in result

    def test_no_matches(self, tools):
        result = tools.search_code("zzz_nonexistent_pattern_zzz")
        assert "No matches" in result

    def test_special_chars_safe(self, tools):
        """Verify that special characters don't cause injection."""
        # This pattern contains shell metacharacters - should not crash
        result = tools.search_code('; echo pwned; #')
        # Should either find no matches or return an error, but NOT execute the echo
        assert "pwned" not in result or "No matches" in result

    def test_timeout(self, tools):
        """Search should not hang indefinitely."""
        # A search on a small workspace should finish quickly
        result = tools.search_code("def")
        assert "Error" not in result or "timed out" in result


class TestDiffReviewMode:
    def test_diff_review_generates_diff(self, tmp_workspace):
        tools = CodingTools(
            workspace_root=str(tmp_workspace),
            use_sandbox=False,
            enable_diff_review=True,
        )
        result = tools.write_file("main.py", "# changed\n")
        assert "pending_review" in result

    def test_approve_changes(self, tmp_workspace):
        tools = CodingTools(
            workspace_root=str(tmp_workspace),
            use_sandbox=False,
            enable_diff_review=True,
        )
        tools.write_file("main.py", "# changed\n")
        result = tools.approve_changes("main.py")
        assert "approved" in result.lower() or "applied" in result.lower()

    def test_reject_changes(self, tmp_workspace):
        tools = CodingTools(
            workspace_root=str(tmp_workspace),
            use_sandbox=False,
            enable_diff_review=True,
        )
        tools.write_file("main.py", "# changed\n")
        result = tools.reject_changes("main.py")
        assert "rejected" in result.lower()
        # Original should be unchanged
        assert "def hello()" in (tmp_workspace / "main.py").read_text()


class TestExecutePython:
    def test_runs_code(self, tools):
        result = tools.execute_python("print('ok')")
        assert "ok" in result

    def test_captures_errors(self, tools):
        result = tools.execute_python("raise ValueError('boom')")
        assert "ValueError" in result or "boom" in result

    def test_timeout(self, tools):
        result = tools.execute_python("import time; time.sleep(60)", timeout=2)
        assert "timed out" in result.lower()
