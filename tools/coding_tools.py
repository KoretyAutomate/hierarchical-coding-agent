"""
Coding tools for the local agent
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any


class CodingTools:
    """Tools available to the coding agent"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def read_file(self, file_path: str) -> str:
        """Read a file from the workspace"""
        full_path = self.workspace_root / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File: {file_path}\n\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file in the workspace"""
        full_path = self.workspace_root / file_path
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def edit_file(self, file_path: str, old_content: str, new_content: str) -> str:
        """Edit a file by replacing old_content with new_content"""
        full_path = self.workspace_root / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_content not in content:
                return f"Error: old_content not found in {file_path}"

            new_file_content = content.replace(old_content, new_content, 1)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)

            return f"Successfully edited {file_path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

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
        """Execute Python code in a safe environment"""
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
        """Run pytest tests"""
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
        """Search for a pattern in code files"""
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', pattern, '--include', file_pattern, '.'],
                capture_output=True,
                text=True,
                cwd=str(self.workspace_root)
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')[:20]  # Limit to 20 results
                return "Search results:\n" + "\n".join(lines)
            else:
                return f"No matches found for pattern: {pattern}"
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
