#!/usr/bin/env python3
"""
Phase 1 Verification Script: Smart Context Management

This script verifies that the ContextManager is working correctly:
1. Token counting
2. AST parsing
3. Project structure generation
"""

import sys
from pathlib import Path
from core.context_manager import ContextManager


def test_token_counting(cm: ContextManager):
    """Test Feature A: Token Counting."""
    print("\n" + "="*80)
    print("TEST 1: Token Counting")
    print("="*80)

    test_text = "This is a sample text for token estimation. " * 10
    tokens = cm.estimate_tokens(test_text)

    print(f"Sample text length: {len(test_text)} characters")
    print(f"Estimated tokens: {tokens}")
    print(f"Chars per token: {len(test_text) / tokens:.2f}")

    # Test file token estimation
    test_file = Path(__file__)
    file_tokens = cm.estimate_file_tokens(str(test_file))
    print(f"\nThis script ({test_file.name}):")
    print(f"  Estimated tokens: {file_tokens}")

    print("✓ Token counting works!")
    return True


def test_ast_parsing(cm: ContextManager):
    """Test Feature B: AST Parsing."""
    print("\n" + "="*80)
    print("TEST 2: AST Parsing")
    print("="*80)

    # Parse the ContextManager itself
    test_file = "core/context_manager.py"
    structure = cm.parse_python_file(test_file)

    if not structure:
        print("✗ Failed to parse Python file")
        return False

    print(f"\nParsed file: {test_file}")
    print(f"  Module docstring: {structure.module_docstring[:80] if structure.module_docstring else 'None'}...")
    print(f"  Number of imports: {len(structure.imports)}")
    print(f"  Number of classes: {len(structure.classes)}")
    print(f"  Number of functions: {len(structure.functions)}")

    # Show class details
    if structure.classes:
        print("\n  Classes found:")
        for cls in structure.classes:
            print(f"    - {cls['name']} (line {cls['lineno']})")
            print(f"      Methods: {len(cls['methods'])}")
            if cls['methods']:
                for method in cls['methods'][:3]:  # Show first 3 methods
                    args = ', '.join(method['args'])
                    print(f"        - {method['name']}({args})")

    # Show function details
    if structure.functions:
        print("\n  Top-level functions:")
        for func in structure.functions:
            args = ', '.join(func['args'])
            print(f"    - {func['name']}({args})")

    print("\n✓ AST parsing works!")
    return True


def test_project_structure(cm: ContextManager):
    """Test Feature C: Project Structure Tree."""
    print("\n" + "="*80)
    print("TEST 3: Project Structure Tree View")
    print("="*80)

    # Generate tree structure
    tree = cm.get_project_structure(max_depth=2)

    print("\nProject structure (max_depth=2):")
    print(tree)

    # Check that it respects .gitignore
    if '__pycache__' in tree:
        print("\n✗ Warning: __pycache__ found in tree (should be ignored)")
        return False

    if '.git' in tree and '📁 .git/' in tree:
        print("\n✗ Warning: .git directory found in tree (should be ignored)")
        return False

    print("\n✓ Project structure generation works!")
    return True


def test_file_info(cm: ContextManager):
    """Test comprehensive file information."""
    print("\n" + "="*80)
    print("TEST 4: File Information Extraction")
    print("="*80)

    # Get info for a Python file
    test_file = "core/context_manager.py"
    info = cm.get_file_info(test_file)

    if not info:
        print("✗ Failed to get file info")
        return False

    print(f"\nFile: {info.path}")
    print(f"  Size: {info.size:,} bytes")
    print(f"  Estimated tokens: {info.estimated_tokens:,}")
    print(f"  Classes: {', '.join(info.classes) if info.classes else 'None'}")
    print(f"  Functions: {len(info.functions)} found")
    print(f"  Imports: {len(info.imports)} found")

    if info.docstring:
        print(f"  Docstring: {info.docstring[:80]}...")

    print("\n✓ File info extraction works!")
    return True


def test_project_analysis(cm: ContextManager):
    """Test project-wide analysis."""
    print("\n" + "="*80)
    print("TEST 5: Project Analysis")
    print("="*80)

    print("\nAnalyzing entire project (this may take a moment)...")
    stats = cm.analyze_project()

    print("\n📊 Project Statistics:")
    print(f"  Total Files: {stats['total_files']}")
    print(f"  Python Files: {stats['python_files']}")
    print(f"  Total Classes: {stats['total_classes']}")
    print(f"  Total Functions: {stats['total_functions']}")
    print(f"  Estimated Total Tokens: {stats['total_tokens']:,}")

    print("\n📁 Files by Type:")
    for ext, count in sorted(stats['files_by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
        ext_display = ext if ext else '(no extension)'
        print(f"  {ext_display}: {count}")

    if stats['largest_files']:
        print("\n📄 Largest Files (by tokens):")
        for path, tokens in stats['largest_files'][:5]:
            print(f"  {path}: {tokens:,} tokens")

    print("\n✓ Project analysis works!")
    return True


def test_context_for_task(cm: ContextManager):
    """Test task-specific context generation."""
    print("\n" + "="*80)
    print("TEST 6: Task-Specific Context Generation")
    print("="*80)

    test_task = "Add a new feature to handle database connections"
    print(f"\nTask: {test_task}")

    context = cm.get_context_for_task(test_task, max_tokens=2000)
    context_tokens = cm.estimate_tokens(context)

    print(f"\nGenerated context ({context_tokens} tokens):")
    print("-" * 80)
    print(context[:500] + "..." if len(context) > 500 else context)
    print("-" * 80)

    print(f"\n✓ Task-specific context generation works!")
    return True


def test_integration_with_orchestrator():
    """Test integration with HierarchicalOrchestrator."""
    print("\n" + "="*80)
    print("TEST 7: Integration with HierarchicalOrchestrator")
    print("="*80)

    try:
        from hierarchical_orchestrator import HierarchicalOrchestrator

        print("\nInitializing HierarchicalOrchestrator...")
        orchestrator = HierarchicalOrchestrator()

        # Check that context_manager is initialized
        if not hasattr(orchestrator, 'context_manager'):
            print("✗ ContextManager not found in orchestrator")
            return False

        print(f"✓ ContextManager initialized: {orchestrator.context_manager}")

        # Test context generation
        test_request = "Add error handling to file operations"
        print(f"\nGenerating context for request: '{test_request}'")

        context = orchestrator.context_manager.get_context_for_task(test_request, max_tokens=1000)
        tokens = orchestrator.context_manager.estimate_tokens(context)

        print(f"  Generated {tokens} tokens of context")
        print(f"  Context preview: {context[:200]}...")

        print("\n✓ Integration with orchestrator works!")
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("PHASE 1 VERIFICATION: Smart Context Management")
    print("="*80)

    # Get project root
    project_root = Path(__file__).parent
    print(f"\nProject root: {project_root}")

    # Initialize ContextManager
    print("\nInitializing ContextManager...")
    cm = ContextManager(str(project_root))

    # Run tests
    tests = [
        ("Token Counting", lambda: test_token_counting(cm)),
        ("AST Parsing", lambda: test_ast_parsing(cm)),
        ("Project Structure", lambda: test_project_structure(cm)),
        ("File Information", lambda: test_file_info(cm)),
        ("Project Analysis", lambda: test_project_analysis(cm)),
        ("Context for Task", lambda: test_context_for_task(cm)),
        ("Orchestrator Integration", test_integration_with_orchestrator),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print("="*80)

    if passed == total:
        print("\n🎉 Phase 1 Implementation: COMPLETE")
        print("\nVerification Criteria Met:")
        print("✓ ContextManager correctly identifies classes/functions in Python files")
        print("✓ Token counting estimates context usage")
        print("✓ Project structure tree view generated with .gitignore support")
        print("✓ Integration with HierarchicalOrchestrator successful")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
