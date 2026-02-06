#!/usr/bin/env python3
"""
Phase 3 Verification Script: VS Code "Deep" Integration

This script verifies that the IDE Bridge and VS Code integration are working correctly:
1. VS Code CLI availability
2. Open file in VS Code
3. Open diff in VS Code
4. Open file at specific line
5. Navigate to function/class
6. Integration with HierarchicalOrchestrator
"""

import sys
import os
from pathlib import Path
from core.ide_bridge import IDEBridge, open_diff_in_vscode
import time


def test_vscode_availability(bridge: IDEBridge):
    """Test if VS Code CLI is available."""
    print("\n" + "="*80)
    print("TEST 1: VS Code CLI Availability")
    print("="*80)

    if bridge.vscode_available:
        print("\n✓ VS Code CLI is available!")
        print(f"  'code' command found in PATH")
        return True
    else:
        print("\n✗ VS Code CLI is NOT available")
        print("\nInstallation instructions:")
        print(bridge.install_instructions())
        print("\n⚠️  Phase 3 features require VS Code CLI")
        print("   Install VS Code and run this test again")
        return False


def test_open_file(bridge: IDEBridge, workspace: Path):
    """Test opening a file in VS Code."""
    print("\n" + "="*80)
    print("TEST 2: Open File in VS Code")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create a test file
    test_file = workspace / "test_vscode_open.py"
    test_content = """# Test file for VS Code integration
def test_function():
    print("Hello from VS Code!")
"""
    test_file.write_text(test_content)

    print(f"\nOpening file: {test_file.name}")
    success, msg = bridge.open_file(str(test_file))

    print(f"  Result: {msg}")

    if success:
        print("\n✓ File opened in VS Code!")
        print("  Check your VS Code window to verify")
        # Cleanup
        time.sleep(1)
        test_file.unlink()
        return True
    else:
        print("\n✗ Failed to open file")
        return False


def test_open_file_at_line(bridge: IDEBridge, workspace: Path):
    """Test opening a file at a specific line."""
    print("\n" + "="*80)
    print("TEST 3: Open File at Specific Line")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create a test file with multiple lines
    test_file = workspace / "test_vscode_line.py"
    test_content = """# Line 1
# Line 2
# Line 3
# Line 4
# THIS IS LINE 5 - CURSOR SHOULD BE HERE
# Line 6
# Line 7
"""
    test_file.write_text(test_content)

    print(f"\nOpening file at line 5: {test_file.name}")
    success, msg = bridge.open_file(str(test_file), line=5)

    print(f"  Result: {msg}")

    if success:
        print("\n✓ File opened at line 5!")
        print("  Check VS Code - cursor should be on line 5")
        # Cleanup
        time.sleep(1)
        test_file.unlink()
        return True
    else:
        print("\n✗ Failed to open file at line")
        return False


def test_open_diff(bridge: IDEBridge, workspace: Path):
    """Test opening a diff in VS Code."""
    print("\n" + "="*80)
    print("TEST 4: Open Diff in VS Code")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create original and modified files
    original_file = workspace / "test_diff_original.py"
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""

    modified_file = workspace / "test_diff_modified.py"
    modified_content = """def hello():
    print("Hello, World!")
    print("Welcome!")

def goodbye():
    print("Goodbye!")
    print("See you later!")

def new_function():
    return "New function added"
"""

    original_file.write_text(original_content)
    modified_file.write_text(modified_content)

    print(f"\nOpening diff: {original_file.name} <-> {modified_file.name}")
    success, msg = bridge.open_diff_in_vscode(str(original_file), str(modified_file))

    print(f"  Result: {msg}")

    if success:
        print("\n✓ Diff opened in VS Code!")
        print("  Check VS Code for side-by-side diff view")
        # Cleanup
        time.sleep(2)
        original_file.unlink()
        modified_file.unlink()
        return True
    else:
        print("\n✗ Failed to open diff")
        return False


def test_new_file_diff(bridge: IDEBridge, workspace: Path):
    """Test diff for a new file that doesn't exist yet."""
    print("\n" + "="*80)
    print("TEST 5: New File Diff")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create only the new file (original doesn't exist)
    new_file = workspace / "test_new_file.py"
    new_content = """# This is a brand new file
def brand_new():
    return "This file didn't exist before"
"""
    new_file.write_text(new_content)

    # Original file doesn't exist
    original_file = workspace / "nonexistent_file.py"

    print(f"\nOpening diff for new file: {new_file.name}")
    success, msg = bridge.open_diff_in_vscode(str(original_file), str(new_file))

    print(f"  Result: {msg}")

    if success:
        print("\n✓ New file diff opened in VS Code!")
        print("  Check VS Code - should show all lines as additions")
        # Cleanup
        time.sleep(2)
        new_file.unlink()
        return True
    else:
        print("\n✗ Failed to open new file diff")
        return False


def test_navigate_to_function(bridge: IDEBridge, workspace: Path):
    """Test navigating to a specific function."""
    print("\n" + "="*80)
    print("TEST 6: Navigate to Function")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create a file with multiple functions
    test_file = workspace / "test_navigate.py"
    test_content = """def function_one():
    pass

def function_two():
    pass

def target_function():
    '''This is the target function'''
    print("You found me!")

def function_three():
    pass
"""
    test_file.write_text(test_content)

    print(f"\nNavigating to function 'target_function' in {test_file.name}")
    success, msg = bridge.open_file_at_function(str(test_file), "target_function")

    print(f"  Result: {msg}")

    if success:
        print("\n✓ Navigated to function!")
        print("  Check VS Code - cursor should be at target_function")
        # Cleanup
        time.sleep(1)
        test_file.unlink()
        return True
    else:
        print("\n✗ Failed to navigate to function")
        return False


def test_navigate_to_class(bridge: IDEBridge, workspace: Path):
    """Test navigating to a specific class."""
    print("\n" + "="*80)
    print("TEST 7: Navigate to Class")
    print("="*80)

    if not bridge.vscode_available:
        print("✗ Skipping test (VS Code not available)")
        return False

    # Create a file with classes
    test_file = workspace / "test_navigate_class.py"
    test_content = """class FirstClass:
    pass

class SecondClass:
    pass

class TargetClass:
    '''This is the target class'''
    def method(self):
        pass

class ThirdClass:
    pass
"""
    test_file.write_text(test_content)

    print(f"\nNavigating to class 'TargetClass' in {test_file.name}")
    success, msg = bridge.open_file_at_class(str(test_file), "TargetClass")

    print(f"  Result: {msg}")

    if success:
        print("\n✓ Navigated to class!")
        print("  Check VS Code - cursor should be at TargetClass")
        # Cleanup
        time.sleep(1)
        test_file.unlink()
        return True
    else:
        print("\n✗ Failed to navigate to class")
        return False


def test_standalone_function():
    """Test the standalone open_diff_in_vscode function."""
    print("\n" + "="*80)
    print("TEST 8: Standalone Function")
    print("="*80)

    # This is the main function specified in Phase 3 requirements
    print("\nTesting standalone open_diff_in_vscode() function...")

    workspace = Path("/home/korety/coding-agent")

    # Create test files
    file1 = workspace / "sandbox" / "test_standalone_1.py"
    file2 = workspace / "sandbox" / "test_standalone_2.py"

    file1.parent.mkdir(parents=True, exist_ok=True)

    file1.write_text("def old(): pass\n")
    file2.write_text("def new(): pass\n")

    success, msg = open_diff_in_vscode(str(file1), str(file2))

    print(f"  Result: {msg}")

    # Cleanup
    if file1.exists():
        file1.unlink()
    if file2.exists():
        file2.unlink()

    if success:
        print("\n✓ Standalone function works!")
        return True
    else:
        print("\n✗ Standalone function failed")
        return False


def test_orchestrator_integration():
    """Test integration with HierarchicalOrchestrator."""
    print("\n" + "="*80)
    print("TEST 9: Orchestrator Integration")
    print("="*80)

    try:
        from hierarchical_orchestrator import HierarchicalOrchestrator

        print("\nInitializing HierarchicalOrchestrator...")
        orchestrator = HierarchicalOrchestrator()

        # Check that ide_bridge is initialized
        if not hasattr(orchestrator, 'ide_bridge'):
            print("✗ IDEBridge not found in orchestrator")
            return False

        print(f"✓ IDEBridge initialized in orchestrator")
        print(f"  VS Code available: {orchestrator.ide_bridge.vscode_available}")

        # Check that the method exists
        if not hasattr(orchestrator, '_offer_vscode_diff_review'):
            print("✗ _offer_vscode_diff_review method not found")
            return False

        print(f"✓ _offer_vscode_diff_review method exists")

        print("\n✓ Orchestrator integration works!")
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("PHASE 3 VERIFICATION: VS Code 'Deep' Integration")
    print("="*80)

    workspace = Path("/home/korety/coding-agent/sandbox")
    workspace.mkdir(parents=True, exist_ok=True)

    print(f"\nTest workspace: {workspace}")

    # Initialize IDEBridge
    print("\nInitializing IDEBridge...")
    bridge = IDEBridge(str(workspace))

    # Run availability test first
    vscode_available = test_vscode_availability(bridge)

    # Run all tests
    tests = [
        ("VS Code Availability", lambda: vscode_available),
    ]

    # Only run VS Code-dependent tests if available
    if vscode_available:
        tests.extend([
            ("Open File", lambda: test_open_file(bridge, workspace)),
            ("Open File at Line", lambda: test_open_file_at_line(bridge, workspace)),
            ("Open Diff", lambda: test_open_diff(bridge, workspace)),
            ("New File Diff", lambda: test_new_file_diff(bridge, workspace)),
            ("Navigate to Function", lambda: test_navigate_to_function(bridge, workspace)),
            ("Navigate to Class", lambda: test_navigate_to_class(bridge, workspace)),
            ("Standalone Function", test_standalone_function),
        ])
    else:
        print("\n⚠️  Skipping VS Code-dependent tests")
        print("   Install VS Code CLI to run full test suite")

    # Always run integration test
    tests.append(("Orchestrator Integration", test_orchestrator_integration))

    # Execute tests
    results = []
    for name, test_func in tests:
        try:
            result = test_func() if callable(test_func) else test_func
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

    if vscode_available and passed == total:
        print("\n🎉 Phase 3 Implementation: COMPLETE")
        print("\nVerification Criteria Met:")
        print("✓ VS Code CLI integration works")
        print("✓ open_diff_in_vscode() function implemented")
        print("✓ Files can be opened in VS Code")
        print("✓ Diffs can be viewed in VS Code")
        print("✓ Navigation to functions/classes works")
        print("✓ Integration with HierarchicalOrchestrator successful")
        return 0
    elif not vscode_available:
        print("\n⚠️  VS Code CLI not available")
        print("   Install VS Code and run tests again for full verification")
        print(f"\n   Core functionality: {passed}/{total} tests passed")
        return 0 if passed == total else 1
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
