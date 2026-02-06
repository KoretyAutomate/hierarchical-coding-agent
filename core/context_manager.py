"""
Smart Context Management - Cline-like Context Intelligence

This module provides intelligent context management for the hierarchical agent:
- Token counting to prevent context overflow
- AST parsing to extract code structure (classes, functions, docstrings)
- Project structure mapping with .gitignore support
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file in the project."""
    path: str
    size: int
    estimated_tokens: int
    classes: List[str]
    functions: List[str]
    imports: List[str]
    docstring: Optional[str]


@dataclass
class CodeStructure:
    """Extracted structure from a Python file."""
    classes: List[Dict[str, any]]
    functions: List[Dict[str, any]]
    imports: List[str]
    module_docstring: Optional[str]


class ContextManager:
    """
    Smart context manager that understands codebase structure.

    Features:
    - Token estimation to prevent context overflow
    - AST parsing for structural understanding
    - Project tree generation respecting .gitignore
    """

    # Approximate tokens per character (GPT-style tokenization)
    CHARS_PER_TOKEN = 4

    # Default ignore patterns (in addition to .gitignore)
    DEFAULT_IGNORE_PATTERNS = {
        '__pycache__',
        '.git',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        '.venv',
        'venv',
        'env',
        'node_modules',
        '.DS_Store',
        '*.pyc',
        '*.pyo',
        '*.egg-info',
        '.eggs',
        'dist',
        'build',
        '.coverage',
        'htmlcov',
        '.idea',
        '.vscode'
    }

    def __init__(self, project_root: str):
        """
        Initialize the context manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.ignore_patterns = self._load_gitignore()
        logger.info(f"ContextManager initialized for: {self.project_root}")

    def _load_gitignore(self) -> Set[str]:
        """
        Load patterns from .gitignore file.

        Returns:
            Set of ignore patterns
        """
        patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        gitignore_path = self.project_root / '.gitignore'

        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            patterns.add(line)
                logger.info(f"Loaded {len(patterns)} ignore patterns from .gitignore")
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")

        return patterns

    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored based on patterns.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        path_str = str(path)
        name = path.name

        for pattern in self.ignore_patterns:
            # Simple pattern matching
            if pattern.startswith('*'):
                # Wildcard pattern (e.g., *.pyc)
                suffix = pattern[1:]
                if name.endswith(suffix) or path_str.endswith(suffix):
                    return True
            elif pattern.endswith('/'):
                # Directory pattern
                if pattern[:-1] in path_str.split(os.sep):
                    return True
            else:
                # Exact match
                if pattern == name or pattern in path_str:
                    return True

        return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a given text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // self.CHARS_PER_TOKEN

    def estimate_file_tokens(self, file_path: str) -> int:
        """
        Estimate token count for a file.

        Args:
            file_path: Path to the file

        Returns:
            Estimated token count
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return 0

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return self.estimate_tokens(content)
        except Exception as e:
            logger.warning(f"Failed to estimate tokens for {file_path}: {e}")
            return 0

    def parse_python_file(self, file_path: str) -> Optional[CodeStructure]:
        """
        Parse a Python file and extract structure using AST.

        Args:
            file_path: Path to Python file (absolute or relative to project root)

        Returns:
            CodeStructure with extracted information, or None if parsing fails
        """
        try:
            path = Path(file_path)

            # If path is relative, resolve against project root
            if not path.is_absolute():
                path = self.project_root / path

            if not path.exists() or path.suffix != '.py':
                return None

            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(path))

            # Extract module docstring
            module_docstring = ast.get_docstring(tree)

            # Extract classes
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'lineno': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'methods': [],
                        'bases': [self._get_name(base) for base in node.bases]
                    }

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'name': item.name,
                                'lineno': item.lineno,
                                'docstring': ast.get_docstring(item),
                                'args': [arg.arg for arg in item.args.args],
                                'is_async': isinstance(item, ast.AsyncFunctionDef)
                            }
                            class_info['methods'].append(method_info)

                    classes.append(class_info)

            # Extract top-level functions
            functions = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_info = {
                        'name': node.name,
                        'lineno': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    }
                    functions.append(func_info)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)

            return CodeStructure(
                classes=classes,
                functions=functions,
                imports=imports,
                module_docstring=module_docstring
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

    def _get_name(self, node) -> str:
        """Helper to extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)

    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """
        Get comprehensive information about a file.

        Args:
            file_path: Path to the file (absolute or relative to project root)

        Returns:
            FileInfo object with file details
        """
        try:
            path = Path(file_path)

            # If path is relative, resolve against project root
            if not path.is_absolute():
                path = self.project_root / path

            if not path.exists():
                return None

            size = path.stat().st_size

            # For Python files, extract structure
            if path.suffix == '.py':
                structure = self.parse_python_file(file_path)
                if structure:
                    classes = [cls['name'] for cls in structure.classes]
                    functions = [func['name'] for func in structure.functions]
                    imports = structure.imports
                    docstring = structure.module_docstring
                else:
                    classes = []
                    functions = []
                    imports = []
                    docstring = None
            else:
                classes = []
                functions = []
                imports = []
                docstring = None

            # Estimate tokens
            estimated_tokens = self.estimate_file_tokens(file_path)

            return FileInfo(
                path=str(path.relative_to(self.project_root)),
                size=size,
                estimated_tokens=estimated_tokens,
                classes=classes,
                functions=functions,
                imports=imports,
                docstring=docstring
            )

        except Exception as e:
            logger.warning(f"Failed to get info for {file_path}: {e}")
            return None

    def get_project_structure(self, max_depth: Optional[int] = None) -> str:
        """
        Generate a tree view of the project structure.

        Args:
            max_depth: Maximum depth to traverse (None for unlimited)

        Returns:
            Tree structure as a formatted string
        """
        tree_lines = [f"📁 {self.project_root.name}/"]

        def build_tree(directory: Path, prefix: str = "", depth: int = 0):
            """Recursively build the tree structure."""
            if max_depth is not None and depth >= max_depth:
                return

            try:
                # Get all items in directory
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

                # Filter out ignored items
                items = [item for item in items if not self._should_ignore(item)]

                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = prefix + ("    " if is_last else "│   ")

                    if item.is_dir():
                        tree_lines.append(f"{prefix}{current_prefix}📁 {item.name}/")
                        build_tree(item, next_prefix, depth + 1)
                    else:
                        # Add file icon based on extension
                        icon = self._get_file_icon(item.suffix)
                        tree_lines.append(f"{prefix}{current_prefix}{icon} {item.name}")

            except PermissionError:
                tree_lines.append(f"{prefix}[Permission Denied]")
            except Exception as e:
                logger.warning(f"Error reading directory {directory}: {e}")

        build_tree(self.project_root)
        return "\n".join(tree_lines)

    def _get_file_icon(self, extension: str) -> str:
        """Get emoji icon for file type."""
        icons = {
            '.py': '🐍',
            '.md': '📝',
            '.txt': '📄',
            '.json': '📋',
            '.yaml': '⚙️',
            '.yml': '⚙️',
            '.sh': '🔧',
            '.sql': '🗄️',
            '.db': '💾',
            '.log': '📊',
        }
        return icons.get(extension.lower(), '📄')

    def get_structure_summary(self, file_path: str) -> str:
        """
        Get a human-readable summary of a Python file's structure.

        Args:
            file_path: Path to Python file

        Returns:
            Formatted summary string
        """
        structure = self.parse_python_file(file_path)
        if not structure:
            return f"Unable to parse {file_path}"

        summary_lines = [f"\n📄 File: {file_path}"]

        if structure.module_docstring:
            summary_lines.append(f"📝 Description: {structure.module_docstring[:100]}...")

        if structure.imports:
            summary_lines.append(f"\n📦 Imports: {len(structure.imports)}")
            for imp in structure.imports[:5]:  # Show first 5
                summary_lines.append(f"  - {imp}")
            if len(structure.imports) > 5:
                summary_lines.append(f"  ... and {len(structure.imports) - 5} more")

        if structure.classes:
            summary_lines.append(f"\n🏛️ Classes: {len(structure.classes)}")
            for cls in structure.classes:
                methods_count = len(cls['methods'])
                summary_lines.append(f"  - {cls['name']} ({methods_count} methods)")
                if cls['docstring']:
                    summary_lines.append(f"    {cls['docstring'][:80]}...")

        if structure.functions:
            summary_lines.append(f"\n⚡ Functions: {len(structure.functions)}")
            for func in structure.functions:
                args_str = ', '.join(func['args'])
                async_marker = '(async) ' if func['is_async'] else ''
                summary_lines.append(f"  - {async_marker}{func['name']}({args_str})")

        return "\n".join(summary_lines)

    def analyze_project(self) -> Dict[str, any]:
        """
        Analyze the entire project and return statistics.

        Returns:
            Dictionary with project statistics
        """
        stats = {
            'total_files': 0,
            'python_files': 0,
            'total_tokens': 0,
            'total_classes': 0,
            'total_functions': 0,
            'largest_files': [],
            'files_by_type': {}
        }

        file_sizes = []

        for root, dirs, files in os.walk(self.project_root):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file

                if self._should_ignore(file_path):
                    continue

                stats['total_files'] += 1

                # Track by extension
                ext = file_path.suffix
                stats['files_by_type'][ext] = stats['files_by_type'].get(ext, 0) + 1

                # Get file info
                info = self.get_file_info(str(file_path))
                if info:
                    stats['total_tokens'] += info.estimated_tokens
                    file_sizes.append((info.path, info.estimated_tokens))

                    if file_path.suffix == '.py':
                        stats['python_files'] += 1
                        stats['total_classes'] += len(info.classes)
                        stats['total_functions'] += len(info.functions)

        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = file_sizes[:10]

        return stats

    def get_context_for_task(self, task_description: str, max_tokens: int = 8000) -> str:
        """
        Generate optimized context for a task, staying within token budget.

        Args:
            task_description: Description of the task
            max_tokens: Maximum tokens to use for context

        Returns:
            Formatted context string
        """
        context_parts = []
        token_count = 0

        # Add project structure (always included, compressed if needed)
        structure = self.get_project_structure(max_depth=3)
        structure_tokens = self.estimate_tokens(structure)

        if structure_tokens < max_tokens * 0.3:  # Use max 30% for structure
            context_parts.append("## Project Structure\n" + structure)
            token_count += structure_tokens
        else:
            # Use compressed version
            structure_compressed = self.get_project_structure(max_depth=2)
            context_parts.append("## Project Structure (compressed)\n" + structure_compressed)
            token_count += self.estimate_tokens(structure_compressed)

        # Add project statistics
        stats = self.analyze_project()
        stats_text = f"""
## Project Statistics
- Total Files: {stats['total_files']}
- Python Files: {stats['python_files']}
- Total Classes: {stats['total_classes']}
- Total Functions: {stats['total_functions']}
- Estimated Total Tokens: {stats['total_tokens']:,}
"""
        context_parts.append(stats_text)
        token_count += self.estimate_tokens(stats_text)

        # Add relevant files based on task description (simple keyword matching)
        keywords = task_description.lower().split()
        relevant_files = []

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file

                if file_path.suffix != '.py' or self._should_ignore(file_path):
                    continue

                # Check if filename matches any keyword
                if any(keyword in file.lower() for keyword in keywords):
                    info = self.get_file_info(str(file_path))
                    if info:
                        relevant_files.append(info)

        if relevant_files:
            context_parts.append("\n## Potentially Relevant Files")
            for info in relevant_files[:5]:  # Max 5 files
                if token_count + info.estimated_tokens < max_tokens:
                    summary = self.get_structure_summary(str(self.project_root / info.path))
                    context_parts.append(summary)
                    token_count += self.estimate_tokens(summary)

        return "\n".join(context_parts)


if __name__ == "__main__":
    # Demo usage
    import sys

    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "/home/korety/coding-agent"

    print(f"Analyzing project: {project_root}\n")

    cm = ContextManager(project_root)

    # Show project structure
    print(cm.get_project_structure(max_depth=3))
    print("\n" + "="*80 + "\n")

    # Show statistics
    stats = cm.analyze_project()
    print("Project Statistics:")
    print(f"  Total Files: {stats['total_files']}")
    print(f"  Python Files: {stats['python_files']}")
    print(f"  Total Classes: {stats['total_classes']}")
    print(f"  Total Functions: {stats['total_functions']}")
    print(f"  Estimated Tokens: {stats['total_tokens']:,}")

    if stats['largest_files']:
        print("\n  Largest Files:")
        for path, tokens in stats['largest_files'][:5]:
            print(f"    {path}: {tokens:,} tokens")
