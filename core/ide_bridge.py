"""
IDE Bridge - VS Code Integration

This module provides deep integration with VS Code using the code CLI:
- Open files in VS Code
- Open diff views
- Navigate to specific lines
- Compare files side-by-side
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class IDEBridge:
    """
    Bridge to integrate with VS Code (and potentially other IDEs).

    Uses the VS Code CLI (`code` command) for deep integration.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the IDE bridge.

        Args:
            workspace_root: Root directory of the workspace (optional)
        """
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else Path.cwd()
        self.vscode_available = self._check_vscode_availability()

        if self.vscode_available:
            logger.info("VS Code CLI detected and available")
        else:
            logger.warning("VS Code CLI not found. Install VS Code and add 'code' to PATH.")

    def _check_vscode_availability(self) -> bool:
        """
        Check if VS Code CLI is available.

        Returns:
            True if 'code' command is available
        """
        return shutil.which("code") is not None

    def open_file(self, file_path: str, line: Optional[int] = None) -> Tuple[bool, str]:
        """
        Open a file in VS Code.

        Args:
            file_path: Path to the file to open
            line: Optional line number to navigate to

        Returns:
            Tuple of (success, message)
        """
        if not self.vscode_available:
            return False, "VS Code CLI not available. Install VS Code and add 'code' to PATH."

        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace_root / path

            if not path.exists():
                return False, f"File not found: {path}"

            # Build command
            if line:
                cmd = ["code", "--goto", f"{path}:{line}"]
            else:
                cmd = ["code", str(path)]

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                msg = f"Opened {path.name}" + (f" at line {line}" if line else "")
                logger.info(msg)
                return True, msg
            else:
                error_msg = f"Failed to open file: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "VS Code command timed out"
        except Exception as e:
            error_msg = f"Error opening file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def open_diff_in_vscode(self, original_path: str, new_path: str) -> Tuple[bool, str]:
        """
        Open a diff view in VS Code comparing two files.

        Args:
            original_path: Path to the original file
            new_path: Path to the new/modified file

        Returns:
            Tuple of (success, message)
        """
        if not self.vscode_available:
            return False, "VS Code CLI not available. Install VS Code and add 'code' to PATH."

        try:
            # Resolve paths
            orig = Path(original_path)
            new = Path(new_path)

            if not orig.is_absolute():
                orig = self.workspace_root / orig
            if not new.is_absolute():
                new = self.workspace_root / new

            # For new files, create empty temp file as "original"
            if not orig.exists():
                logger.info(f"Original file doesn't exist: {orig}. Creating empty temp file for diff.")
                temp_orig = self.workspace_root / "sandbox" / f"empty_{orig.name}"
                temp_orig.parent.mkdir(parents=True, exist_ok=True)
                temp_orig.write_text("")
                orig = temp_orig

            if not new.exists():
                return False, f"New file not found: {new}"

            # Build VS Code diff command
            cmd = [
                "code",
                "--diff",
                str(orig),
                str(new)
            ]

            logger.info(f"Opening diff: {orig.name} <-> {new.name}")

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                msg = f"✓ Opened diff in VS Code: {orig.name} <-> {new.name}"
                logger.info(msg)
                return True, msg
            else:
                error_msg = f"Failed to open diff: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, "VS Code command timed out"
        except Exception as e:
            error_msg = f"Error opening diff: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def open_workspace(self, workspace_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Open a workspace/folder in VS Code.

        Args:
            workspace_path: Path to workspace (defaults to self.workspace_root)

        Returns:
            Tuple of (success, message)
        """
        if not self.vscode_available:
            return False, "VS Code CLI not available"

        try:
            path = Path(workspace_path) if workspace_path else self.workspace_root

            cmd = ["code", str(path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                msg = f"Opened workspace: {path.name}"
                logger.info(msg)
                return True, msg
            else:
                return False, f"Failed to open workspace: {result.stderr}"

        except Exception as e:
            return False, f"Error opening workspace: {str(e)}"

    def open_file_at_function(
        self,
        file_path: str,
        function_name: str
    ) -> Tuple[bool, str]:
        """
        Open a file and navigate to a specific function.

        Uses AST parsing to find the function line number.

        Args:
            file_path: Path to Python file
            function_name: Name of function to navigate to

        Returns:
            Tuple of (success, message)
        """
        try:
            import ast

            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace_root / path

            if not path.exists():
                return False, f"File not found: {path}"

            # Parse file to find function
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(path))

            # Find function line number
            line_number = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    line_number = node.lineno
                    break

            if line_number:
                return self.open_file(str(path), line_number)
            else:
                return False, f"Function '{function_name}' not found in {path.name}"

        except Exception as e:
            return False, f"Error finding function: {str(e)}"

    def open_file_at_class(
        self,
        file_path: str,
        class_name: str
    ) -> Tuple[bool, str]:
        """
        Open a file and navigate to a specific class.

        Args:
            file_path: Path to Python file
            class_name: Name of class to navigate to

        Returns:
            Tuple of (success, message)
        """
        try:
            import ast

            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace_root / path

            if not path.exists():
                return False, f"File not found: {path}"

            # Parse file to find class
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(path))

            # Find class line number
            line_number = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    line_number = node.lineno
                    break

            if line_number:
                return self.open_file(str(path), line_number)
            else:
                return False, f"Class '{class_name}' not found in {path.name}"

        except Exception as e:
            return False, f"Error finding class: {str(e)}"

    def compare_files(
        self,
        file1: str,
        file2: str,
        title1: Optional[str] = None,
        title2: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Compare two arbitrary files in VS Code.

        Args:
            file1: Path to first file
            file2: Path to second file
            title1: Optional title for first file
            title2: Optional title for second file

        Returns:
            Tuple of (success, message)
        """
        # VS Code diff command doesn't support custom titles via CLI
        # Just use the standard diff command
        return self.open_diff_in_vscode(file1, file2)

    def install_instructions(self) -> str:
        """
        Get instructions for installing VS Code CLI.

        Returns:
            Installation instructions as string
        """
        return """
VS Code CLI Installation Instructions:
=========================================

1. Install VS Code:
   - Download from: https://code.visualstudio.com/

2. Add 'code' command to PATH:

   macOS:
   - Open VS Code
   - Press Cmd+Shift+P
   - Type "shell command"
   - Select "Shell Command: Install 'code' command in PATH"

   Linux:
   - Usually installed automatically with VS Code
   - Or add to ~/.bashrc: export PATH="$PATH:/usr/share/code/bin"

   Windows:
   - VS Code installer should add to PATH automatically
   - Or manually add: C:\\Program Files\\Microsoft VS Code\\bin

3. Verify installation:
   - Open terminal
   - Run: code --version
   - Should show VS Code version

4. Restart your terminal/shell after installation
"""


def open_diff_in_vscode(original_path: str, new_path: str) -> Tuple[bool, str]:
    """
    Standalone function to open diff in VS Code.

    This is the main function specified in Phase 3 requirements.

    Args:
        original_path: Path to original file
        new_path: Path to new/modified file

    Returns:
        Tuple of (success, message)
    """
    bridge = IDEBridge()
    return bridge.open_diff_in_vscode(original_path, new_path)


if __name__ == "__main__":
    # Demo usage
    import sys

    print("IDEBridge Demo\n")

    bridge = IDEBridge("/home/korety/coding-agent")

    if not bridge.vscode_available:
        print("⚠️  VS Code CLI not available")
        print(bridge.install_instructions())
        sys.exit(1)

    print("✓ VS Code CLI available\n")

    # Example 1: Open a file
    print("Example 1: Open file")
    success, msg = bridge.open_file("core/ide_bridge.py")
    print(f"  {msg}\n")

    # Example 2: Open file at specific line
    print("Example 2: Open file at line 50")
    success, msg = bridge.open_file("core/ide_bridge.py", line=50)
    print(f"  {msg}\n")

    # Example 3: Open diff
    print("Example 3: Open diff between two files")
    success, msg = bridge.open_diff_in_vscode(
        "core/context_manager.py",
        "core/diff_engine.py"
    )
    print(f"  {msg}\n")

    # Example 4: Open workspace
    print("Example 4: Open workspace")
    success, msg = bridge.open_workspace()
    print(f"  {msg}\n")

    print("Demo complete!")
