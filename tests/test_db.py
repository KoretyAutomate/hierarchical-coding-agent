"""Tests for core.db module."""
import threading
import tempfile
from pathlib import Path

import pytest

from core.db import DatabaseManager, Task, TaskStatus, WorkflowState, reset_db


@pytest.fixture
def db(tmp_path):
    """Create a fresh database for each test."""
    reset_db()
    db_path = tmp_path / "test.db"
    return DatabaseManager(db_path)


class TestCreateTask:
    def test_creates_task(self, db):
        task_id = db.create_task(request="test task")
        assert task_id == 1

    def test_increments_ids(self, db):
        id1 = db.create_task(request="task 1")
        id2 = db.create_task(request="task 2")
        assert id2 == id1 + 1

    def test_stores_request(self, db):
        task_id = db.create_task(request="do something")
        task = db.get_task(task_id)
        assert task.request == "do something"


class TestGetTask:
    def test_returns_task(self, db):
        task_id = db.create_task(request="test")
        task = db.get_task(task_id)
        assert task is not None
        assert task.request == "test"

    def test_returns_none_for_missing(self, db):
        assert db.get_task(9999) is None


class TestUpdateTask:
    def test_updates_fields(self, db):
        task_id = db.create_task(request="test")
        db.update_task(task_id, status=TaskStatus.COMPLETED.value, plan="my plan")
        task = db.get_task(task_id)
        assert task.status == "completed"
        assert task.plan == "my plan"

    def test_returns_false_for_missing(self, db):
        assert db.update_task(9999, status="completed") is False


class TestDeleteTask:
    def test_deletes_task(self, db):
        task_id = db.create_task(request="test")
        assert db.delete_task(task_id) is True
        assert db.get_task(task_id) is None

    def test_returns_false_for_missing(self, db):
        assert db.delete_task(9999) is False


class TestListTasks:
    def test_lists_all(self, db):
        db.create_task(request="t1")
        db.create_task(request="t2")
        tasks = db.list_tasks()
        assert len(tasks) == 2

    def test_filters_by_status(self, db):
        id1 = db.create_task(request="t1", status=TaskStatus.COMPLETED.value)
        db.create_task(request="t2", status=TaskStatus.PENDING.value)
        tasks = db.list_tasks(status="completed")
        assert len(tasks) == 1


class TestCheckpoints:
    def test_save_and_retrieve(self, db):
        task_id = db.create_task(request="test")
        db.save_checkpoint(task_id, "after_plan", {"plan": "my plan"})
        cp = db.get_latest_checkpoint(task_id)
        assert cp is not None
        assert cp["checkpoint"] == "after_plan"
        assert cp["data"]["plan"] == "my plan"

    def test_latest_checkpoint(self, db):
        task_id = db.create_task(request="test")
        db.save_checkpoint(task_id, "step1", {"step": 1})
        db.save_checkpoint(task_id, "step2", {"step": 2})
        cp = db.get_latest_checkpoint(task_id)
        assert cp["checkpoint"] == "step2"


class TestConcurrency:
    def test_thread_safety(self, db):
        """Multiple threads creating tasks should not crash."""
        errors = []

        def create_tasks(n):
            try:
                for i in range(n):
                    db.create_task(request=f"task from thread {threading.current_thread().name} #{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_tasks, args=(5,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        tasks = db.list_tasks()
        assert len(tasks) == 20  # 4 threads * 5 tasks


class TestBackup:
    def test_creates_backup(self, db, tmp_path):
        db.create_task(request="test")
        backup_path = tmp_path / "backup.db"
        result = db.backup_database(backup_path)
        assert result == backup_path
        assert backup_path.exists()


class TestStatistics:
    def test_returns_stats(self, db):
        db.create_task(request="t1", status=TaskStatus.COMPLETED.value)
        db.create_task(request="t2", status=TaskStatus.PENDING.value)
        stats = db.get_statistics()
        assert stats["total_tasks"] == 2
        assert "completed" in stats["by_status"]
