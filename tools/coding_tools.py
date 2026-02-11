"""
Coding tools for the local agent.
Now with optional Docker sandbox for safe execution and diff review.
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from core.diff_engine import DiffEngine, DiffResult


class CodingTools:
    """
    Tools available to the coding agent.

    Supports optional sandboxed execution via Docker for safety.
    """

    def __init__(
        self,
        workspace_root: str,
        use_sandbox: bool = False,
        sandbox_config: Optional[Dict[str, Any]] = None,
        enable_diff_review: bool = True
    ):
        """
        Initialize coding tools.

        Args:
            workspace_root: Root directory of the workspace
            use_sandbox: Whether to use Docker sandbox for execution
            sandbox_config: Optional sandbox configuration
            enable_diff_review: Whether to enable diff review before file changes
        """
        self.workspace_root = Path(workspace_root)
        self.use_sandbox = use_sandbox
        self.sandbox = None
        self.enable_diff_review = enable_diff_review
        self._pending_diffs: Dict[str, Any] = {}

        # Initialize DiffEngine for code review
        self.diff_engine = DiffEngine(str(self.workspace_root))

        # Initialize sandbox if requested
        if use_sandbox:
            try:
                from core.sandbox import get_sandbox
                sandbox_config = sandbox_config or {}
                self.sandbox = get_sandbox(
                    workspace_path=self.workspace_root,
                    use_docker=True,
                    **sandbox_config
                )
                print("✓ Sandbox enabled for code execution")
            except Exception as e:
                print(f"⚠ Failed to initialize sandbox: {e}")
                print("  Falling back to direct execution")
                self.use_sandbox = False

    def read_file(self, file_path: str) -> str:
        """Read a file from the workspace"""
        full_path = self.workspace_root / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File: {file_path}\n\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str, review_mode: bool = None) -> str:
        """
        Write content to a file in the workspace.

        Args:
            file_path: Path to the file relative to workspace
            content: Content to write
            review_mode: If True, generate diff and return for review instead of writing.
                        If None, uses self.enable_diff_review

        Returns:
            Success message or diff result
        """
        # Determine review mode
        should_review = review_mode if review_mode is not None else self.enable_diff_review

        if should_review:
            # Generate diff instead of writing immediately
            try:
                diff_result = self.diff_engine.generate_diff(file_path, content)

                # Format diff for display
                diff_summary = self.diff_engine.format_diff_summary(diff_result)

                # Return diff for user review
                result = {
                    "status": "pending_review",
                    "file_path": file_path,
                    "diff": diff_summary,
                    "has_changes": diff_result.has_changes,
                    "additions": diff_result.additions,
                    "deletions": diff_result.deletions,
                    "message": "Changes pending approval. Use approve_changes() to apply or reject_changes() to discard."
                }

                # Store diff_result for later approval
                self._pending_diffs[file_path] = diff_result

                return json.dumps(result, indent=2)

            except Exception as e:
                return f"Error generating diff: {str(e)}"
        else:
            # Write directly without review
            full_path = self.workspace_root / file_path
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote to {file_path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"

    def edit_file(self, file_path: str, old_content: str, new_content: str, review_mode: bool = None) -> str:
        """
        Edit a file by replacing old_content with new_content.

        Args:
            file_path: Path to the file relative to workspace
            old_content: Content to replace
            new_content: Replacement content
            review_mode: If True, generate diff and return for review instead of editing.
                        If None, uses self.enable_diff_review

        Returns:
            Success message or diff result
        """
        full_path = self.workspace_root / file_path

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_content not in content:
                return f"Error: old_content not found in {file_path}"

            new_file_content = content.replace(old_content, new_content, 1)

            # Use write_file with the new content (which handles review_mode)
            return self.write_file(file_path, new_file_content, review_mode=review_mode)

        except Exception as e:
            return f"Error editing file: {str(e)}"

    def approve_changes(self, file_path: str) -> str:
        """
        Approve and apply pending changes for a file.

        Args:
            file_path: Path to the file with pending changes

        Returns:
            Success or error message
        """
        if file_path not in self._pending_diffs:
            return f"Error: No pending changes found for {file_path}"

        diff_result = self._pending_diffs[file_path]

        try:
            # Apply the changes
            if self.diff_engine.apply_changes(diff_result):
                # Cleanup temp file
                self.diff_engine.cleanup_temp_file(diff_result)

                # Remove from pending
                del self._pending_diffs[file_path]

                return f"✓ Changes approved and applied to {file_path}"
            else:
                return f"Error: Failed to apply changes to {file_path}"

        except Exception as e:
            return f"Error approving changes: {str(e)}"

    def reject_changes(self, file_path: str) -> str:
        """
        Reject and discard pending changes for a file.

        Args:
            file_path: Path to the file with pending changes

        Returns:
            Success or error message
        """
        if file_path not in self._pending_diffs:
            return f"Error: No pending changes found for {file_path}"

        diff_result = self._pending_diffs[file_path]

        try:
            # Cleanup temp file
            self.diff_engine.cleanup_temp_file(diff_result)

            # Remove from pending
            del self._pending_diffs[file_path]

            return f"✗ Changes rejected for {file_path}"

        except Exception as e:
            return f"Error rejecting changes: {str(e)}"

    def list_pending_changes(self) -> str:
        """
        List all files with pending changes.

        Returns:
            Formatted list of pending changes
        """
        if not self._pending_diffs:
            return "No pending changes"

        lines = ["Pending changes:"]
        for file_path, diff_result in self._pending_diffs.items():
            lines.append(f"  - {file_path}: +{diff_result.additions}/-{diff_result.deletions}")

        return "\n".join(lines)

    def cleanup_pending_diffs(self) -> str:
        """Clean up all pending diffs and their temp files."""
        if not self._pending_diffs:
            return "No pending diffs to clean up"
        count = len(self._pending_diffs)
        for file_path, diff_result in list(self._pending_diffs.items()):
            try:
                self.diff_engine.cleanup_temp_file(diff_result)
            except Exception:
                pass
        self._pending_diffs.clear()
        return f"Cleaned up {count} pending diff(s)"

    def list_files(self, directory: str = ".") -> str:
        """List files in a directory"""
        full_path = self.workspace_root / directory
        try:
            files = []
            for item in full_path.rglob('*'):
                if item.is_file() and not any(part.startswith('.') for part in item.parts):
                    rel_path = item.relative_to(self.workspace_root)
                    files.append(str(rel_path))

            return "Files:\n" + "\n".join(sorted(files)[:50])  # Limit to 50 files
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def execute_python(self, code: str, timeout: int = 30) -> str:
        """
        Execute Python code in a safe environment.

        Uses Docker sandbox if enabled, otherwise runs directly on host.

        Args:
            code: Python code to execute
            timeout: Timeout in seconds

        Returns:
            Formatted output string
        """
        # Use sandbox if enabled
        if self.use_sandbox and self.sandbox:
            try:
                result = self.sandbox.execute_python(code, timeout=timeout)

                output = ""
                if result.stdout:
                    output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                if result.timed_out:
                    output += f"⚠ Execution timed out after {timeout} seconds\n"
                output += f"Return code: {result.exit_code}"
                if result.error:
                    output += f"\nError: {result.error}"

                return output
            except Exception as e:
                return f"Error executing in sandbox: {str(e)}"

        # Fallback to direct execution (legacy mode)
        try:
            result = subprocess.run(
                ['python3', '-c', code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_root)
            )

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            output += f"Return code: {result.returncode}"

            return output
        except subprocess.TimeoutExpired:
            return f"Error: Execution timed out after {timeout} seconds"
        except Exception as e:
            return f"Error executing code: {str(e)}"

    def run_tests(self, test_path: str = "tests") -> str:
        """
        Run pytest tests.

        Uses Docker sandbox if enabled, otherwise runs directly on host.

        Args:
            test_path: Path to tests directory/file

        Returns:
            Formatted test output string
        """
        # Use sandbox if enabled
        if self.use_sandbox and self.sandbox:
            try:
                result = self.sandbox.run_tests(test_path, timeout=120)

                output = f"Test Results:\n"
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    output += f"\n{result.stderr}"
                if result.timed_out:
                    output += f"\n⚠ Tests timed out after 120 seconds"
                if result.error:
                    output += f"\nError: {result.error}"

                return output
            except Exception as e:
                return f"Error running tests in sandbox: {str(e)}"

        # Fallback to direct execution (legacy mode)
        full_path = self.workspace_root / test_path
        try:
            result = subprocess.run(
                ['pytest', str(full_path), '-v'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.workspace_root)
            )

            return f"Test Results:\n{result.stdout}\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Tests timed out after 120 seconds"
        except Exception as e:
            return f"Error running tests: {str(e)}"

    def search_code(self, pattern: str, file_pattern: str = "*.py") -> str:
        """Search for a pattern in code files using fixed-string grep."""
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-F', '--', pattern, '--include', file_pattern, '.'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace_root)
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')[:20]  # Limit to 20 results
                return "Search results:\n" + "\n".join(lines)
            else:
                return f"No matches found for pattern: {pattern}"
        except subprocess.TimeoutExpired:
            return "Error: Search timed out after 30 seconds"
        except Exception as e:
            return f"Error searching code: {str(e)}"


def get_tool_schemas():
    """Return tool schemas for LLM function calling"""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to the file from workspace root"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file in the workspace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to the file from workspace root"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Edit a file by replacing old content with new content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "old_content": {"type": "string"},
                        "new_content": {"type": "string"}
                    },
                    "required": ["file_path", "old_content", "new_content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to list (default: '.')"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_python",
                "description": "Execute Python code safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python code to execute"},
                        "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"}
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_tests",
                "description": "Run pytest tests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "test_path": {
                            "type": "string",
                            "description": "Path to tests directory (default: 'tests')"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "Search for a pattern in code files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "file_pattern": {"type": "string", "description": "File pattern (default: '*.py')"}
                    },
                    "required": ["pattern"]
                }
            }
        }
    ]
