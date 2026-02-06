#!/usr/bin/env python3
"""
Test script for Phase 2 implementation.
Verifies database persistence, checkpoint/resume functionality, and state management.
"""
import sys
import json
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.db import get_db, reset_db, Task, WorkflowState, TaskStatus
from core.config import get_config
from hierarchical_orchestrator import HierarchicalOrchestrator


def test_database_initialization():
    """Test database initialization and schema."""
    print("\n" + "="*70)
    print("TEST 1: Database Initialization")
    print("="*70)

    try:
        # Reset and reinitialize
        reset_db()
        db = get_db()

        print(f"✓ Database initialized at: {db.db_path}")

        # Check statistics
        stats = db.get_statistics()
        print(f"✓ Database statistics:")
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  By status: {stats['by_status']}")
        print(f"  By workflow state: {stats['by_workflow_state']}")

        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_crud_operations():
    """Test task CRUD operations."""
    print("\n" + "="*70)
    print("TEST 2: Task CRUD Operations")
    print("="*70)

    try:
        db = get_db()

        # Create task
        task_id = db.create_task(
            request="Test task for Phase 2",
            status=TaskStatus.PENDING.value,
            workflow_state=WorkflowState.PENDING.value
        )
        print(f"✓ Created task: #{task_id}")

        # Read task
        task = db.get_task(task_id)
        assert task is not None, "Task not found"
        assert task.request == "Test task for Phase 2"
        print(f"✓ Read task: {task.request}")

        # Update task
        success = db.update_task(
            task_id,
            status=TaskStatus.IN_PROGRESS.value,
            workflow_state=WorkflowState.PLANNING.value,
            plan="This is a test plan"
        )
        assert success, "Update failed"
        print(f"✓ Updated task status and workflow state")

        # Verify update
        task = db.get_task(task_id)
        assert task.status == TaskStatus.IN_PROGRESS.value
        assert task.plan == "This is a test plan"
        print(f"✓ Verified update")

        # List tasks
        tasks = db.list_tasks(status=TaskStatus.IN_PROGRESS.value)
        assert len(tasks) >= 1
        print(f"✓ Listed {len(tasks)} in-progress task(s)")

        # Delete task (cleanup)
        # db.delete_task(task_id)
        # print(f"✓ Deleted task #{task_id}")

        return True
    except Exception as e:
        print(f"✗ CRUD operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_checkpoint_functionality():
    """Test checkpoint save and restore."""
    print("\n" + "="*70)
    print("TEST 3: Checkpoint Functionality")
    print("="*70)

    try:
        db = get_db()

        # Create task
        task_id = db.create_task(
            request="Test checkpoint task",
            status=TaskStatus.IN_PROGRESS.value
        )
        print(f"✓ Created task #{task_id}")

        # Save checkpoint
        checkpoint_data = {
            "stage": "planning",
            "plan": "Test implementation plan",
            "timestamp": time.time()
        }
        db.save_checkpoint(task_id, "after_planning", checkpoint_data)
        print(f"✓ Saved checkpoint: after_planning")

        # Retrieve checkpoint
        latest = db.get_latest_checkpoint(task_id)
        assert latest is not None, "Checkpoint not found"
        assert latest['checkpoint'] == "after_planning"
        assert 'plan' in latest['data']
        print(f"✓ Retrieved checkpoint: {latest['checkpoint']}")
        print(f"  Data keys: {list(latest['data'].keys())}")

        return True
    except Exception as e:
        print(f"✗ Checkpoint functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resumable_tasks():
    """Test finding resumable tasks."""
    print("\n" + "="*70)
    print("TEST 4: Resumable Tasks Detection")
    print("="*70)

    try:
        db = get_db()

        # Create tasks in various states
        resumable_id = db.create_task(
            request="Resumable task test",
            status=TaskStatus.IN_PROGRESS.value,
            workflow_state=WorkflowState.PLAN_AWAITING_APPROVAL.value
        )
        print(f"✓ Created resumable task #{resumable_id}")

        completed_id = db.create_task(
            request="Completed task test",
            status=TaskStatus.COMPLETED.value,
            workflow_state=WorkflowState.COMPLETED.value
        )
        print(f"✓ Created completed task #{completed_id}")

        # Find resumable tasks
        resumable = db.get_resumable_tasks()
        resumable_ids = [t.id for t in resumable]

        assert resumable_id in resumable_ids, "Resumable task not found"
        assert completed_id not in resumable_ids, "Completed task incorrectly marked as resumable"

        print(f"✓ Found {len(resumable)} resumable task(s)")
        for task in resumable:
            print(f"  - Task #{task.id}: {task.workflow_state}")

        return True
    except Exception as e:
        print(f"✗ Resumable tasks detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_database_integration():
    """Test orchestrator integration with database."""
    print("\n" + "="*70)
    print("TEST 5: Orchestrator Database Integration")
    print("="*70)

    try:
        # Note: This test doesn't call LLM, just tests database integration
        config = get_config()

        # Create orchestrator
        orchestrator = HierarchicalOrchestrator(config=config)
        print("✓ Created orchestrator with database support")

        # Check database connection
        assert orchestrator.db is not None
        print(f"✓ Orchestrator has database connection")

        # Test checkpoint saving
        test_task_id = orchestrator.db.create_task(
            request="Test orchestrator integration",
            status=TaskStatus.IN_PROGRESS.value
        )
        print(f"✓ Created task via orchestrator: #{test_task_id}")

        orchestrator._save_checkpoint(
            test_task_id,
            "test_checkpoint",
            {"test": "data"}
        )
        print(f"✓ Saved checkpoint via orchestrator")

        orchestrator._update_workflow_state(
            test_task_id,
            WorkflowState.PLANNING,
            plan="Test plan"
        )
        print(f"✓ Updated workflow state via orchestrator")

        # Verify
        task = orchestrator.db.get_task(test_task_id)
        assert task.workflow_state == WorkflowState.PLANNING.value
        assert task.plan == "Test plan"
        print(f"✓ Verified orchestrator database operations")

        return True
    except Exception as e:
        print(f"✗ Orchestrator integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_functionality():
    """Test task resume functionality."""
    print("\n" + "="*70)
    print("TEST 6: Resume Functionality")
    print("="*70)

    try:
        config = get_config()
        orchestrator = HierarchicalOrchestrator(config=config)
        db = orchestrator.db

        # Create a task in an intermediate state (simulating interruption)
        task_id = db.create_task(
            request="Task to resume",
            status=TaskStatus.IN_PROGRESS.value,
            workflow_state=WorkflowState.PLAN_AWAITING_APPROVAL.value,
            plan="This is the plan that was created before interruption",
            workflow_log=json.dumps({
                "task_id": None,  # Will be set later
                "user_request": "Task to resume",
                "stages": [
                    {
                        "stage": "planning",
                        "agent": "lead",
                        "output": "Plan created"
                    }
                ]
            })
        )
        print(f"✓ Created task #{task_id} in intermediate state")

        # Save checkpoint
        db.save_checkpoint(task_id, "after_planning", {
            "plan": "This is the plan that was created before interruption"
        })
        print(f"✓ Saved checkpoint for task #{task_id}")

        # Attempt to resume
        print(f"\n  Attempting to resume task #{task_id}...")
        result = orchestrator.resume_task(task_id)

        assert result is not None, "Resume returned None"
        assert result.get("status") == "awaiting_user_approval", f"Unexpected status: {result.get('status')}"
        assert result.get("task_id") == task_id, "Task ID mismatch"
        assert result.get("plan") is not None, "Plan not restored"

        print(f"✓ Successfully resumed task #{task_id}")
        print(f"  Status: {result.get('status')}")
        print(f"  Stage: {result.get('stage')}")
        print(f"  Plan preview: {result.get('plan', '')[:60]}...")

        return True
    except Exception as e:
        print(f"✗ Resume functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backup_functionality():
    """Test database backup."""
    print("\n" + "="*70)
    print("TEST 7: Database Backup")
    print("="*70)

    try:
        db = get_db()

        # Create backup
        backup_path = db.backup_database()
        assert backup_path.exists(), "Backup file not created"
        print(f"✓ Created backup at: {backup_path}")

        # Check backup file size
        size = backup_path.stat().st_size
        print(f"✓ Backup file size: {size} bytes")

        return True
    except Exception as e:
        print(f"✗ Backup functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests."""
    print("\n" + "#"*70)
    print("# PHASE 2 IMPLEMENTATION TEST SUITE")
    print("#"*70)

    tests = [
        ("Database Initialization", test_database_initialization),
        ("Task CRUD Operations", test_task_crud_operations),
        ("Checkpoint Functionality", test_checkpoint_functionality),
        ("Resumable Tasks Detection", test_resumable_tasks),
        ("Orchestrator Database Integration", test_orchestrator_database_integration),
        ("Resume Functionality", test_resume_functionality),
        ("Database Backup", test_backup_functionality),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "#"*70)
    print("# TEST SUMMARY")
    print("#"*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 2 tests passed!")
        print("\nDefinition of Done: ✅ ACHIEVED")
        print("  - Tasks persist to database")
        print("  - Workflow state saved at checkpoints")
        print("  - Resume functionality works")
        print("  - Process can be interrupted and resumed")
        return 0
    else:
        print("\n⚠ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
