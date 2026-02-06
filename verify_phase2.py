#!/usr/bin/env python3
"""
Phase 2 Verification Script: The "Diff" Experience

This script verifies that the DiffEngine and review workflow are working correctly:
1. DiffEngine generates correct diffs
2. Color-coded output works
3. Temp file management
4. CodingTools integration with review_mode
5. Approve/reject workflow
"""

import sys
import os
from pathlib import Path
from core.diff_engine import DiffEngine
from tools.coding_tools import CodingTools


def test_diff_generation(engine: DiffEngine, workspace: Path):
    """Test basic diff generation."""
    print("\n" + "="*80)
    print("TEST 1: Diff Generation")
    print("="*80)

    # Create a test file
    test_file = workspace / "test_diff_file.py"
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
"""

    new_content = """def hello():
    print("Hello, World!")
    print("Welcome!")

def goodbye():
    print("Goodbye!")
    print("See you later!")

def new_function():
    return "New function added"
"""

    # Write original file
    with open(test_file, 'w') as f:
        f.write(original_content)

    # Generate diff
    diff_result = engine.generate_diff(str(test_file), new_content)

    print(f"\nFile: {test_file.name}")
    print(f"  Has changes: {diff_result.has_changes}")
    print(f"  Additions: {diff_result.additions}")
    print(f"  Deletions: {diff_result.deletions}")
    print(f"  Temp file: {diff_result.temp_path}")

    if diff_result.has_changes:
        print("\n✓ Diff generation works!")
        return True, diff_result
    else:
        print("\n✗ Diff generation failed")
        return False, None


def test_colored_diff(engine: DiffEngine, diff_result):
    """Test color-coded diff output."""
    print("\n" + "="*80)
    print("TEST 2: Color-Coded Diff Output")
    print("="*80)

    if not diff_result:
        print("✗ No diff result to test")
        return False

    # Display colored diff
    print("\nColored diff:")
    print(diff_result.colored_diff)

    # Check if colors are present
    has_colors = (
        engine.COLOR_GREEN in diff_result.colored_diff or
        engine.COLOR_RED in diff_result.colored_diff
    )

    if has_colors:
        print("\n✓ Color-coded output works!")
        return True
    else:
        print("\n✗ Color codes not found in output")
        return False


def test_diff_summary(engine: DiffEngine, diff_result):
    """Test formatted diff summary."""
    print("\n" + "="*80)
    print("TEST 3: Diff Summary Formatting")
    print("="*80)

    if not diff_result:
        print("✗ No diff result to test")
        return False

    summary = engine.format_diff_summary(diff_result)

    print("\nFormatted summary:")
    print(summary)

    # Check for key elements
    has_statistics = "Statistics:" in summary or "additions" in summary
    has_diff_content = diff_result.diff_text[:50] in summary if diff_result.diff_text else True

    if has_statistics:
        print("\n✓ Diff summary formatting works!")
        return True
    else:
        print("\n✗ Summary formatting incomplete")
        return False


def test_temp_file_management(engine: DiffEngine, diff_result):
    """Test temp file creation and cleanup."""
    print("\n" + "="*80)
    print("TEST 4: Temp File Management")
    print("="*80)

    if not diff_result:
        print("✗ No diff result to test")
        return False

    temp_path = Path(diff_result.temp_path)

    # Check if temp file exists
    if not temp_path.exists():
        print(f"✗ Temp file not found: {temp_path}")
        return False

    print(f"✓ Temp file created: {temp_path}")

    # Test cleanup
    success = engine.cleanup_temp_file(diff_result)

    if success and not temp_path.exists():
        print("✓ Temp file cleanup works!")
        return True
    else:
        print("✗ Temp file cleanup failed")
        return False


def test_apply_changes(engine: DiffEngine, workspace: Path):
    """Test applying changes."""
    print("\n" + "="*80)
    print("TEST 5: Apply Changes")
    print("="*80)

    # Create test file
    test_file = workspace / "test_apply.py"
    original_content = "def old(): pass\n"
    new_content = "def new(): pass\n"

    with open(test_file, 'w') as f:
        f.write(original_content)

    # Generate diff
    diff_result = engine.generate_diff(str(test_file), new_content)

    # Apply changes
    success = engine.apply_changes(diff_result)

    if not success:
        print("✗ Failed to apply changes")
        return False

    # Verify changes were applied
    with open(test_file, 'r') as f:
        result_content = f.read()

    if result_content == new_content:
        print("✓ Changes applied correctly!")
        # Cleanup
        test_file.unlink()
        engine.cleanup_temp_file(diff_result)
        return True
    else:
        print("✗ Changes not applied correctly")
        print(f"  Expected: {new_content}")
        print(f"  Got: {result_content}")
        return False


def test_new_file_diff(engine: DiffEngine, workspace: Path):
    """Test diff for a new file that doesn't exist yet."""
    print("\n" + "="*80)
    print("TEST 6: New File Diff")
    print("="*80)

    # Use a file that doesn't exist
    new_file = workspace / "brand_new_file.py"
    if new_file.exists():
        new_file.unlink()

    new_content = "def brand_new(): pass\n"

    # Generate diff
    diff_result = engine.generate_diff(str(new_file), new_content)

    print(f"\nFile exists: {diff_result.file_exists}")
    print(f"Has changes: {diff_result.has_changes}")
    print(f"Additions: {diff_result.additions}")

    if not diff_result.file_exists and diff_result.has_changes:
        print("✓ New file diff works!")
        engine.cleanup_temp_file(diff_result)
        return True
    else:
        print("✗ New file diff failed")
        return False


def test_coding_tools_integration(workspace: Path):
    """Test CodingTools integration with review_mode."""
    print("\n" + "="*80)
    print("TEST 7: CodingTools Integration")
    print("="*80)

    # Initialize CodingTools with review enabled
    tools = CodingTools(str(workspace), enable_diff_review=True)

    # Create a test file
    test_file = "test_tools_integration.py"
    test_path = workspace / test_file

    original_content = "def original(): pass\n"
    with open(test_path, 'w') as f:
        f.write(original_content)

    # Try to write with review_mode=True
    new_content = "def modified(): pass\n"
    result = tools.write_file(test_file, new_content, review_mode=True)

    print("\nWrite result (review mode):")
    print(result[:200] + "..." if len(result) > 200 else result)

    # Check if result indicates pending review
    if "pending_review" in result or "APPROVE" in result.upper():
        print("\n✓ CodingTools review mode works!")
        return True, tools, test_file
    else:
        print("\n✗ CodingTools review mode failed")
        return False, None, None


def test_approve_reject_workflow(tools: CodingTools, test_file: str, workspace: Path):
    """Test approve and reject workflow."""
    print("\n" + "="*80)
    print("TEST 8: Approve/Reject Workflow")
    print("="*80)

    if not tools:
        print("✗ No tools instance to test")
        return False

    # List pending changes
    pending = tools.list_pending_changes()
    print("\nPending changes:")
    print(pending)

    if test_file not in pending:
        print("✗ Test file not in pending changes")
        return False

    # Test approve
    print(f"\nApproving changes to {test_file}...")
    approve_result = tools.approve_changes(test_file)
    print(approve_result)

    if "approved" in approve_result.lower():
        # Verify file was actually modified
        test_path = workspace / test_file
        with open(test_path, 'r') as f:
            content = f.read()

        if "modified" in content:
            print("✓ Approve workflow works!")
            test_path.unlink()  # Cleanup
            return True
        else:
            print("✗ File was not modified after approval")
            return False
    else:
        print("✗ Approve workflow failed")
        return False


def test_reject_workflow(tools: CodingTools, workspace: Path):
    """Test rejection workflow."""
    print("\n" + "="*80)
    print("TEST 9: Reject Workflow")
    print("="*80)

    # Create a new test file
    test_file = "test_reject.py"
    test_path = workspace / test_file

    original_content = "def original(): pass\n"
    with open(test_path, 'w') as f:
        f.write(original_content)

    # Create pending change
    new_content = "def rejected(): pass\n"
    tools.write_file(test_file, new_content, review_mode=True)

    # Reject changes
    print(f"\nRejecting changes to {test_file}...")
    reject_result = tools.reject_changes(test_file)
    print(reject_result)

    if "rejected" in reject_result.lower():
        # Verify file was NOT modified
        with open(test_path, 'r') as f:
            content = f.read()

        if "original" in content and "rejected" not in content:
            print("✓ Reject workflow works!")
            test_path.unlink()  # Cleanup
            return True
        else:
            print("✗ File was modified despite rejection")
            return False
    else:
        print("✗ Reject workflow failed")
        return False


def test_edit_file_with_review(workspace: Path):
    """Test edit_file with review mode."""
    print("\n" + "="*80)
    print("TEST 10: Edit File with Review Mode")
    print("="*80)

    tools = CodingTools(str(workspace), enable_diff_review=True)

    # Create test file
    test_file = "test_edit_review.py"
    test_path = workspace / test_file

    content = "def function_one(): pass\ndef function_two(): pass\n"
    with open(test_path, 'w') as f:
        f.write(content)

    # Edit with review mode
    result = tools.edit_file(
        test_file,
        "def function_one(): pass",
        "def function_one():\n    return 'modified'",
        review_mode=True
    )

    print("\nEdit result:")
    print(result[:200] + "..." if len(result) > 200 else result)

    if "pending_review" in result:
        print("\n✓ Edit file with review mode works!")

        # Approve and verify
        tools.approve_changes(test_file)
        with open(test_path, 'r') as f:
            final_content = f.read()

        test_path.unlink()  # Cleanup

        if "modified" in final_content:
            return True
        else:
            print("✗ Edit was not applied correctly")
            return False
    else:
        print("✗ Edit file review mode failed")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("PHASE 2 VERIFICATION: The 'Diff' Experience")
    print("="*80)

    # Setup workspace
    workspace = Path("/home/korety/coding-agent/sandbox")
    workspace.mkdir(parents=True, exist_ok=True)

    print(f"\nTest workspace: {workspace}")

    # Initialize DiffEngine
    print("\nInitializing DiffEngine...")
    engine = DiffEngine(str(workspace.parent), str(workspace))

    # Run tests
    tests = []
    diff_result = None

    # Test 1-6: DiffEngine tests
    success, diff_result = test_diff_generation(engine, workspace)
    tests.append(("Diff Generation", success))

    success = test_colored_diff(engine, diff_result)
    tests.append(("Color-Coded Output", success))

    success = test_diff_summary(engine, diff_result)
    tests.append(("Diff Summary", success))

    success = test_temp_file_management(engine, diff_result)
    tests.append(("Temp File Management", success))

    success = test_apply_changes(engine, workspace)
    tests.append(("Apply Changes", success))

    success = test_new_file_diff(engine, workspace)
    tests.append(("New File Diff", success))

    # Test 7-10: CodingTools integration tests
    success, tools, test_file = test_coding_tools_integration(workspace)
    tests.append(("CodingTools Integration", success))

    if success and tools and test_file:
        success = test_approve_reject_workflow(tools, test_file, workspace)
        tests.append(("Approve Workflow", success))
    else:
        tests.append(("Approve Workflow", False))

    success = test_reject_workflow(CodingTools(str(workspace), enable_diff_review=True), workspace)
    tests.append(("Reject Workflow", success))

    success = test_edit_file_with_review(workspace)
    tests.append(("Edit with Review", success))

    # Cleanup test files
    for test_file in workspace.glob("test_*.py"):
        try:
            test_file.unlink()
        except:
            pass

    # Print summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print("="*80)

    if passed == total:
        print("\n🎉 Phase 2 Implementation: COMPLETE")
        print("\nVerification Criteria Met:")
        print("✓ Agent produces color-coded diff before saving files")
        print("✓ DiffEngine generates accurate unified diffs")
        print("✓ Temp file management works correctly")
        print("✓ Approve/reject workflow functions properly")
        print("✓ CodingTools integration with review_mode successful")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
