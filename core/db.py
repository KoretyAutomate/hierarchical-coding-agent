"""
Database layer for task persistence and workflow state management.

Provides:
- Task CRUD operations
- Workflow state persistence
- Checkpoint/resume functionality
- Transaction handling
- Backup utilities
"""
import sqlite3
import json
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(Enum):
    """Workflow state for hierarchical orchestration."""
    PENDING = "pending"
    PLANNING = "planning"
    PLAN_AWAITING_APPROVAL = "plan_awaiting_approval"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    IMPLEMENTING = "implementing"
    IMPLEMENTATION_AWAITING_APPROVAL = "implementation_awaiting_approval"
    IMPLEMENTATION_APPROVED = "implementation_approved"
    IMPLEMENTATION_REJECTED = "implementation_rejected"
    REVIEWING = "reviewing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task data model."""
    id: Optional[int] = None
    request: str = ""
    status: str = TaskStatus.PENDING.value
    workflow_state: str = WorkflowState.PENDING.value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    plan: Optional[str] = None
    implementation: Optional[str] = None
    review: Optional[str] = None
    verification_result: Optional[str] = None
    workflow_log: Optional[str] = None
    workflow_checkpoint_data: Optional[str] = None
    plan_approved_at: Optional[datetime] = None
    plan_approved_by: Optional[str] = None
    plan_rejection_reason: Optional[str] = None
    implementation_approved_at: Optional[datetime] = None
    implementation_approved_by: Optional[str] = None
    implementation_rejection_reason: Optional[str] = None
    error_details: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        # Convert datetime to ISO format
        for key in ['created_at', 'updated_at', 'plan_approved_at', 'implementation_approved_at']:
            if d.get(key):
                d[key] = d[key].isoformat() if isinstance(d[key], datetime) else d[key]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary."""
        # Convert ISO datetime strings to datetime objects
        for key in ['created_at', 'updated_at', 'plan_approved_at', 'implementation_approved_at']:
            if data.get(key) and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except (ValueError, TypeError):
                    data[key] = None
        return cls(**data)


class DatabaseManager:
    """
    Manages SQLite database for task persistence.

    Supports:
    - Task CRUD operations
    - Workflow state management
    - Resume functionality
    - Atomic transactions
    - Backup/restore
    """

    def __init__(self, db_path: Path):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database schema if needed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if tasks table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='tasks'
            """)

            if not cursor.fetchone():
                # Create new schema
                self._create_schema(conn)
            else:
                # Migrate existing schema if needed
                self._migrate_schema(conn)

    def _create_schema(self, conn: sqlite3.Connection):
        """Create database schema from scratch."""
        cursor = conn.cursor()

        # Main tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                workflow_state TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- Workflow stages
                plan TEXT,
                implementation TEXT,
                review TEXT,
                verification_result TEXT,
                workflow_log TEXT,
                workflow_checkpoint_data TEXT,

                -- Approval tracking
                plan_approved_at TIMESTAMP,
                plan_approved_by TEXT,
                plan_rejection_reason TEXT,
                implementation_approved_at TIMESTAMP,
                implementation_approved_by TEXT,
                implementation_rejection_reason TEXT,

                -- Error handling
                error_details TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status
            ON tasks(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_workflow_state
            ON tasks(workflow_state)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_created_at
            ON tasks(created_at DESC)
        """)

        # Checkpoints table for granular state tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                checkpoint_name TEXT NOT NULL,
                checkpoint_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_task_id
            ON checkpoints(task_id)
        """)

        conn.commit()
        print("✓ Database schema created")

    def _migrate_schema(self, conn: sqlite3.Connection):
        """Migrate existing schema if needed."""
        cursor = conn.cursor()

        # Get existing columns
        cursor.execute("PRAGMA table_info(tasks)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Add missing columns (for backward compatibility)
        new_columns = {
            'workflow_state': 'TEXT DEFAULT "pending"',
            'workflow_checkpoint_data': 'TEXT',
            'verification_result': 'TEXT',
            'error_details': 'TEXT',
            'retry_count': 'INTEGER DEFAULT 0'
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                    print(f"  ✓ Added column: {col_name}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

        # Create checkpoints table if missing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                checkpoint_name TEXT NOT NULL,
                checkpoint_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        conn.commit()

    @contextmanager
    def get_connection(self):
        """
        Get database connection as context manager with thread-safety.

        Usage:
            with db.get_connection() as conn:
                conn.execute(...)
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def create_task(self, request: str, **kwargs) -> int:
        """
        Create a new task.

        Args:
            request: User request description
            **kwargs: Additional task fields

        Returns:
            Task ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            task = Task(request=request, **kwargs)
            task.created_at = datetime.now()
            task.updated_at = datetime.now()

            cursor.execute("""
                INSERT INTO tasks (
                    request, status, workflow_state, created_at, updated_at,
                    plan, implementation, review, workflow_log,
                    workflow_checkpoint_data, retry_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.request,
                task.status,
                task.workflow_state,
                task.created_at,
                task.updated_at,
                task.plan,
                task.implementation,
                task.review,
                task.workflow_log,
                task.workflow_checkpoint_data,
                task.retry_count
            ))

            task_id = cursor.lastrowid
            print(f"✓ Task created: ID {task_id}")
            return task_id

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                return Task(**dict(row))
            return None

    def update_task(self, task_id: int, **updates) -> bool:
        """
        Update task fields.

        Args:
            task_id: Task ID
            **updates: Fields to update

        Returns:
            True if updated, False if not found
        """
        updates['updated_at'] = datetime.now()

        # Build SET clause
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [task_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """
        Delete task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def list_tasks(
        self,
        status: Optional[str] = None,
        workflow_state: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Task]:
        """
        List tasks with optional filtering.

        Args:
            status: Filter by status
            workflow_state: Filter by workflow state
            limit: Maximum number of results

        Returns:
            List of Task objects
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if workflow_state:
            query += " AND workflow_state = ?"
            params.append(workflow_state)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [Task(**dict(row)) for row in cursor.fetchall()]

    def save_checkpoint(
        self,
        task_id: int,
        checkpoint_name: str,
        checkpoint_data: Dict[str, Any]
    ):
        """
        Save a workflow checkpoint.

        Args:
            task_id: Task ID
            checkpoint_name: Checkpoint name (e.g., "after_planning")
            checkpoint_data: Checkpoint data to save
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert into checkpoints table
            cursor.execute("""
                INSERT INTO checkpoints (task_id, checkpoint_name, checkpoint_data)
                VALUES (?, ?, ?)
            """, (task_id, checkpoint_name, json.dumps(checkpoint_data)))

            # Also update main task checkpoint field (in same transaction)
            checkpoint_json = json.dumps({
                'checkpoint': checkpoint_name,
                'data': checkpoint_data,
                'timestamp': datetime.now().isoformat()
            })

            cursor.execute("""
                UPDATE tasks
                SET workflow_checkpoint_data = ?, updated_at = ?
                WHERE id = ?
            """, (checkpoint_json, datetime.now(), task_id))

    def get_latest_checkpoint(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get latest checkpoint for a task.

        Args:
            task_id: Task ID

        Returns:
            Checkpoint data or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT checkpoint_name, checkpoint_data
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY id DESC
                LIMIT 1
            """, (task_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'checkpoint': row[0],
                    'data': json.loads(row[1]) if row[1] else {}
                }
            return None

    def get_resumable_tasks(self) -> List[Task]:
        """
        Get tasks that can be resumed (in progress states).

        Returns:
            List of Task objects that are in progress
        """
        resumable_states = [
            WorkflowState.PLANNING.value,
            WorkflowState.PLAN_AWAITING_APPROVAL.value,
            WorkflowState.IMPLEMENTING.value,
            WorkflowState.IMPLEMENTATION_AWAITING_APPROVAL.value,
            WorkflowState.REVIEWING.value,
            WorkflowState.VERIFYING.value,
        ]

        placeholders = ", ".join("?" * len(resumable_states))
        query = f"""
            SELECT * FROM tasks
            WHERE workflow_state IN ({placeholders})
            AND status = 'in_progress'
            ORDER BY updated_at DESC
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, resumable_states)
            return [Task(**dict(row)) for row in cursor.fetchall()]

    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of the database.

        Args:
            backup_path: Optional custom backup path

        Returns:
            Path to backup file
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"tasks_backup_{timestamp}.db"

        shutil.copy2(self.db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with various statistics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM tasks
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())

            # Count by workflow state
            cursor.execute("""
                SELECT workflow_state, COUNT(*)
                FROM tasks
                GROUP BY workflow_state
            """)
            workflow_counts = dict(cursor.fetchall())

            # Total tasks
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]

            return {
                'total_tasks': total_tasks,
                'by_status': status_counts,
                'by_workflow_state': workflow_counts
            }


# Singleton instance for easy access
_db_manager: Optional[DatabaseManager] = None


def get_db(db_path: Optional[Path] = None) -> DatabaseManager:
    """
    Get database manager singleton.

    Args:
        db_path: Optional database path (uses config default if not provided)

    Returns:
        DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        if db_path is None:
            from core.config import get_config
            config = get_config()
            db_path = config.database.db_path

        _db_manager = DatabaseManager(db_path)

    return _db_manager


def reset_db():
    """Reset database singleton (useful for testing)."""
    global _db_manager
    _db_manager = None
