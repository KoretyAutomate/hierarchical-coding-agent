"""
Diff Engine - Cline-like Interactive Code Review

This module provides interactive diff viewing and approval workflow:
- Prevents blind file overwrites
- Generates unified diffs before saving
- Color-coded output (green for additions, red for deletions)
- Temp file management for comparison
- Approval/rejection workflow
"""

import os
import difflib
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of a diff comparison."""
    original_path: str
    temp_path: str
    has_changes: bool
    diff_text: str
    colored_diff: str
    additions: int
    deletions: int
    file_exists: bool


class DiffEngine:
    """
    Manages code diffs and interactive review workflow.

    Features:
    - Generate unified diffs between original and proposed code
    - Color-coded output for terminal display
    - Temp file management
    - Change statistics
    """

    # ANSI color codes for terminal output
    COLOR_RESET = "\033[0m"
    COLOR_GREEN = "\033[32m"
    COLOR_RED = "\033[31m"
    COLOR_CYAN = "\033[36m"
    COLOR_YELLOW = "\033[33m"
    COLOR_BOLD = "\033[1m"

    def __init__(self, workspace_root: str, temp_dir: Optional[str] = None):
        """
        Initialize the diff engine.

        Args:
            workspace_root: Root directory of the workspace
            temp_dir: Directory for temporary files (default: workspace_root/sandbox)
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.temp_dir = Path(temp_dir) if temp_dir else self.workspace_root / "sandbox"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DiffEngine initialized: workspace={self.workspace_root}, temp_dir={self.temp_dir}")

    def _get_temp_path(self, original_path: str) -> Path:
        """
        Get temporary file path for a given original path.

        Args:
            original_path: Path to the original file

        Returns:
            Path to temporary file
        """
        # Create unique temp filename
        original = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_name = f"temp_{timestamp}_{original.name}"

        return self.temp_dir / temp_name

    def create_temp_file(self, original_path: str, new_content: str) -> str:
        """
        Create a temporary file with new content.

        Args:
            original_path: Path to the original file
            new_content: New content to write to temp file

        Returns:
            Path to the temporary file
        """
        temp_path = self._get_temp_path(original_path)

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"Created temp file: {temp_path}")
            return str(temp_path)

        except Exception as e:
            logger.error(f"Failed to create temp file {temp_path}: {e}")
            raise

    def generate_diff(
        self,
        original_path: str,
        new_content: str,
        context_lines: int = 3
    ) -> DiffResult:
        """
        Generate a unified diff between original file and new content.

        Args:
            original_path: Path to the original file
            new_content: New content to compare
            context_lines: Number of context lines in diff (default: 3)

        Returns:
            DiffResult with diff information
        """
        original_path_obj = Path(original_path)

        # Handle absolute vs relative paths
        if not original_path_obj.is_absolute():
            original_path_obj = self.workspace_root / original_path_obj

        file_exists = original_path_obj.exists()

        # Get original content
        if file_exists:
            try:
                with open(original_path_obj, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read original file {original_path_obj}: {e}")
                original_content = ""
        else:
            original_content = ""

        # Create temp file with new content
        temp_path = self.create_temp_file(str(original_path_obj), new_content)

        # Split into lines for difflib
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        # Generate unified diff
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{original_path_obj.name}",
            tofile=f"b/{original_path_obj.name}",
            lineterm='',
            n=context_lines
        )

        diff_lines = list(diff)
        has_changes = len(diff_lines) > 0

        # Generate plain text diff
        diff_text = '\n'.join(diff_lines)

        # Generate colored diff
        colored_diff = self._colorize_diff(diff_lines)

        # Count additions and deletions
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        return DiffResult(
            original_path=str(original_path_obj),
            temp_path=temp_path,
            has_changes=has_changes,
            diff_text=diff_text,
            colored_diff=colored_diff,
            additions=additions,
            deletions=deletions,
            file_exists=file_exists
        )

    def _colorize_diff(self, diff_lines: List[str]) -> str:
        """
        Add ANSI color codes to diff output.

        Args:
            diff_lines: List of diff lines

        Returns:
            Colored diff string
        """
        colored_lines = []

        for line in diff_lines:
            if line.startswith('+++') or line.startswith('---'):
                # File headers - bold cyan
                colored_lines.append(f"{self.COLOR_BOLD}{self.COLOR_CYAN}{line}{self.COLOR_RESET}")
            elif line.startswith('@@'):
                # Line numbers - yellow
                colored_lines.append(f"{self.COLOR_YELLOW}{line}{self.COLOR_RESET}")
            elif line.startswith('+'):
                # Additions - green
                colored_lines.append(f"{self.COLOR_GREEN}{line}{self.COLOR_RESET}")
            elif line.startswith('-'):
                # Deletions - red
                colored_lines.append(f"{self.COLOR_RED}{line}{self.COLOR_RESET}")
            else:
                # Context - no color
                colored_lines.append(line)

        return '\n'.join(colored_lines)

    def format_diff_summary(self, diff_result: DiffResult) -> str:
        """
        Format a human-readable diff summary.

        Args:
            diff_result: DiffResult to format

        Returns:
            Formatted summary string
        """
        lines = []

        # Header
        lines.append("=" * 80)
        if diff_result.file_exists:
            lines.append(f"📝 CHANGES TO: {diff_result.original_path}")
        else:
            lines.append(f"✨ NEW FILE: {diff_result.original_path}")
        lines.append("=" * 80)

        # Statistics
        if diff_result.has_changes:
            lines.append(f"\n📊 Statistics:")
            lines.append(f"  {self.COLOR_GREEN}+{diff_result.additions} additions{self.COLOR_RESET}")
            lines.append(f"  {self.COLOR_RED}-{diff_result.deletions} deletions{self.COLOR_RESET}")
            lines.append("")

            # Diff content
            lines.append("📋 Diff:")
            lines.append("-" * 80)
            lines.append(diff_result.colored_diff)
            lines.append("-" * 80)
        else:
            lines.append("\n✅ No changes detected (content is identical)")

        lines.append("")
        lines.append(f"Temp file: {diff_result.temp_path}")

        return '\n'.join(lines)

    def apply_changes(self, diff_result: DiffResult) -> bool:
        """
        Apply changes from temp file to original file.

        Args:
            diff_result: DiffResult containing temp file path

        Returns:
            True if successful, False otherwise
        """
        try:
            temp_path = Path(diff_result.temp_path)
            original_path = Path(diff_result.original_path)

            # Ensure parent directory exists
            original_path.parent.mkdir(parents=True, exist_ok=True)

            # Read temp file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Write to original location
            with open(original_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Applied changes to {original_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply changes: {e}")
            return False

    def cleanup_temp_file(self, diff_result: DiffResult) -> bool:
        """
        Remove temporary file.

        Args:
            diff_result: DiffResult containing temp file path

        Returns:
            True if successful, False otherwise
        """
        try:
            temp_path = Path(diff_result.temp_path)
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Cleaned up temp file: {temp_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup temp file: {e}")
            return False

    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.

        Args:
            max_age_hours: Maximum age of temp files in hours

        Returns:
            Number of files cleaned up
        """
        cleaned = 0
        now = datetime.now()

        try:
            for temp_file in self.temp_dir.glob("temp_*"):
                if temp_file.is_file():
                    # Check file age
                    mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    age_hours = (now - mtime).total_seconds() / 3600

                    if age_hours > max_age_hours:
                        temp_file.unlink()
                        cleaned += 1
                        logger.debug(f"Cleaned up old temp file: {temp_file}")

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old temp file(s)")

        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

        return cleaned

    def interactive_review(self, diff_result: DiffResult) -> bool:
        """
        Interactive review workflow for diff approval.

        Args:
            diff_result: DiffResult to review

        Returns:
            True if approved, False if rejected
        """
        # Display diff summary
        print(self.format_diff_summary(diff_result))

        # If no changes, auto-approve
        if not diff_result.has_changes:
            print("✅ No changes to apply.")
            return True

        # Prompt for approval
        print("\n" + "=" * 80)
        print("🔍 Review the changes above.")
        print("=" * 80)

        while True:
            response = input("\nApply these changes? [APPROVE/REJECT/VIEW]: ").strip().upper()

            if response in ['APPROVE', 'A', 'YES', 'Y']:
                print(f"{self.COLOR_GREEN}✓ Changes approved{self.COLOR_RESET}")
                return True
            elif response in ['REJECT', 'R', 'NO', 'N']:
                print(f"{self.COLOR_RED}✗ Changes rejected{self.COLOR_RESET}")
                return False
            elif response in ['VIEW', 'V', 'DIFF', 'D']:
                # Show diff again
                print("\n" + diff_result.colored_diff)
            else:
                print(f"{self.COLOR_YELLOW}Invalid input. Please enter APPROVE, REJECT, or VIEW.{self.COLOR_RESET}")


if __name__ == "__main__":
    # Demo usage
    import sys

    if len(sys.argv) > 1:
        workspace = sys.argv[1]
    else:
        workspace = "/home/korety/coding-agent"

    print(f"DiffEngine Demo - Workspace: {workspace}\n")

    engine = DiffEngine(workspace)

    # Example: Create a diff for a test file
    test_file = "test_example.py"
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""

    new_content = """def hello():
    print("Hello, World!")
    print("Welcome to the diff engine!")

def goodbye():
    print("Goodbye!")
    print("See you later!")

def new_function():
    print("This is a new function!")
"""

    # Create test file if it doesn't exist
    test_path = Path(workspace) / test_file
    if not test_path.exists():
        with open(test_path, 'w') as f:
            f.write(original_content)
        print(f"Created test file: {test_path}\n")

    # Generate diff
    diff_result = engine.generate_diff(test_file, new_content)

    # Display diff
    print(engine.format_diff_summary(diff_result))

    # Interactive review
    if engine.interactive_review(diff_result):
        if engine.apply_changes(diff_result):
            print(f"\n{engine.COLOR_GREEN}✓ Changes applied successfully!{engine.COLOR_RESET}")
        else:
            print(f"\n{engine.COLOR_RED}✗ Failed to apply changes{engine.COLOR_RESET}")
    else:
        print(f"\n{engine.COLOR_YELLOW}Changes not applied{engine.COLOR_RESET}")

    # Cleanup
    engine.cleanup_temp_file(diff_result)
