"""
Orchestration layer for Claude Code to delegate tasks to the coding agent
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml
import sys

from agents.coding_agent import CodingAgent


class TaskOrchestrator:
    """
    Interface for Claude Code to delegate tasks to the local coding agent
    """

    def __init__(self, config_path: str = "/home/korety/Project/coding-agent/config/agent_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.task_queue_path = Path(self.config['orchestration']['task_queue_path'])
        self.completed_path = Path(self.config['orchestration']['completed_tasks_path'])
        self.logs_path = Path(self.config['orchestration']['logs_path'])

        # Initialize paths
        self.task_queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Initialize queue if not exists
        if not self.task_queue_path.exists():
            self._save_queue([])

        if not self.completed_path.exists():
            self._save_completed([])

        self.agent = None

    def _load_queue(self) -> List[Dict]:
        """Load task queue"""
        with open(self.task_queue_path, 'r') as f:
            return json.load(f)

    def _save_queue(self, queue: List[Dict]):
        """Save task queue"""
        with open(self.task_queue_path, 'w') as f:
            json.dump(queue, f, indent=2)

    def _load_completed(self) -> List[Dict]:
        """Load completed tasks"""
        with open(self.completed_path, 'r') as f:
            return json.load(f)

    def _save_completed(self, completed: List[Dict]):
        """Save completed tasks"""
        with open(self.completed_path, 'w') as f:
            json.dump(completed, f, indent=2)

    def add_task(self, description: str, context: Optional[str] = None, priority: str = "normal") -> str:
        """
        Add a task to the queue
        Returns: task_id
        """
        task_id = f"task_{int(time.time() * 1000)}"

        task = {
            "task_id": task_id,
            "description": description,
            "context": context,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "assigned_to": "coding_agent"
        }

        queue = self._load_queue()
        queue.append(task)
        self._save_queue(queue)

        print(f"✓ Task added: {task_id}")
        print(f"  Description: {description}")

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a task"""
        # Check queue
        queue = self._load_queue()
        for task in queue:
            if task['task_id'] == task_id:
                return task

        # Check completed
        completed = self._load_completed()
        for task in completed:
            if task['task_id'] == task_id:
                return task

        return None

    def execute_next_task(self) -> Optional[Dict]:
        """
        Execute the next task in the queue
        Returns: task result or None if queue is empty
        """
        queue = self._load_queue()

        if not queue:
            print("Queue is empty")
            return None

        # Get next task
        task = queue.pop(0)
        self._save_queue(queue)

        print(f"\n{'='*70}")
        print(f"EXECUTING TASK: {task['task_id']}")
        print(f"{'='*70}")

        # Initialize agent if needed
        if not self.agent:
            self.agent = CodingAgent(self.config)

        # Execute task
        task['status'] = 'running'
        task['started_at'] = datetime.now().isoformat()

        try:
            result = self.agent.run_task(
                task_description=task['description'],
                context=task.get('context')
            )

            task['status'] = 'completed' if result['success'] else 'failed'
            task['completed_at'] = datetime.now().isoformat()
            task['result'] = result

            # Save to completed
            completed = self._load_completed()
            completed.append(task)
            self._save_completed(completed)

            # Save detailed log
            log_file = self.logs_path / f"{task['task_id']}.json"
            with open(log_file, 'w') as f:
                json.dump(task, f, indent=2)

            print(f"\n{'='*70}")
            print(f"TASK {'COMPLETED' if result['success'] else 'FAILED'}: {task['task_id']}")
            print(f"{'='*70}\n")

            return task

        except Exception as e:
            task['status'] = 'error'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()

            completed = self._load_completed()
            completed.append(task)
            self._save_completed(completed)

            print(f"\n✗ Task error: {str(e)}\n")
            return task

    def execute_all_tasks(self):
        """Execute all tasks in the queue"""
        while True:
            result = self.execute_next_task()
            if result is None:
                break
            time.sleep(1)  # Brief pause between tasks

    def list_queue(self) -> List[Dict]:
        """List all queued tasks"""
        return self._load_queue()

    def list_completed(self, limit: int = 10) -> List[Dict]:
        """List completed tasks"""
        completed = self._load_completed()
        return completed[-limit:]

    def clear_queue(self):
        """Clear the task queue"""
        self._save_queue([])
        print("✓ Queue cleared")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of task status"""
        queue = self._load_queue()
        completed = self._load_completed()

        successful = sum(1 for t in completed if t.get('status') == 'completed')
        failed = sum(1 for t in completed if t.get('status') in ['failed', 'error'])

        return {
            "queued": len(queue),
            "completed": len(completed),
            "successful": successful,
            "failed": failed
        }


# CLI Interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Coding Agent Orchestrator")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add task
    add_parser = subparsers.add_parser('add', help='Add a task to the queue')
    add_parser.add_argument('description', help='Task description')
    add_parser.add_argument('--context', help='Additional context')

    # Execute
    subparsers.add_parser('execute', help='Execute next task in queue')
    subparsers.add_parser('execute-all', help='Execute all tasks in queue')

    # Status
    status_parser = subparsers.add_parser('status', help='Get task status')
    status_parser.add_argument('task_id', help='Task ID')

    # List
    subparsers.add_parser('list', help='List queued tasks')
    subparsers.add_parser('completed', help='List completed tasks')
    subparsers.add_parser('summary', help='Get summary')

    # Clear
    subparsers.add_parser('clear', help='Clear queue')

    args = parser.parse_args()

    orchestrator = TaskOrchestrator()

    if args.command == 'add':
        task_id = orchestrator.add_task(args.description, context=args.context)
        print(f"Task ID: {task_id}")

    elif args.command == 'execute':
        orchestrator.execute_next_task()

    elif args.command == 'execute-all':
        orchestrator.execute_all_tasks()

    elif args.command == 'status':
        status = orchestrator.get_task_status(args.task_id)
        print(json.dumps(status, indent=2))

    elif args.command == 'list':
        queue = orchestrator.list_queue()
        print(json.dumps(queue, indent=2))

    elif args.command == 'completed':
        completed = orchestrator.list_completed()
        print(json.dumps(completed, indent=2))

    elif args.command == 'summary':
        summary = orchestrator.get_summary()
        print(json.dumps(summary, indent=2))

    elif args.command == 'clear':
        orchestrator.clear_queue()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
