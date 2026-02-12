"""
Orchestration layer for Claude Code to delegate tasks to the coding agent.

Supports workspace overrides, dry-run mode, parallel execution, and backup callbacks.
"""
import json
import time
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import sys

from agents.coding_agent import CodingAgent
from tools.coding_tools import CodingTools
from core.llm import BaseLLM


class TaskOrchestrator:
    """
    Interface for Claude Code to delegate tasks to the local coding agent.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = str(Path(__file__).parent / "config" / "agent_config.yaml")

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

        # Thread-safe lock for file writes in parallel mode
        self._file_lock = threading.Lock()

    def _create_llm(self) -> BaseLLM:
        """Create an LLM instance from config."""
        llm_config = self.config.get('llm', {})
        provider = llm_config.get('provider', 'ollama')

        if provider == 'ollama':
            from core.llm import OllamaAdapter
            return OllamaAdapter(
                model_name=llm_config.get('model', 'frob/qwen3-coder-next'),
                base_url=llm_config.get('base_url', 'http://localhost:11434/v1'),
                timeout=llm_config.get('timeout', 300.0),
            )
        elif provider == 'anthropic':
            from core.llm import AnthropicAdapter
            return AnthropicAdapter(
                model_name=llm_config.get('model', 'claude-3-5-sonnet-20241022'),
                api_key=llm_config.get('api_key'),
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    def _create_agent(
        self,
        workspace_root: str = None,
        dry_run: bool = False,
        backup_dir: str = None,
    ) -> CodingAgent:
        """Create a CodingAgent with proper LLM and tools configuration."""
        llm = self._create_llm()
        ws = workspace_root or self.config.get('workspace', {}).get(
            'project_root', str(Path(__file__).parent)
        )

        # Build backup callback if backup_dir is set
        backup_callback = None
        if backup_dir:
            backup_path = Path(backup_dir)

            def _backup_file(file_path_str: str):
                src = Path(file_path_str)
                if src.exists():
                    ws_path = Path(ws)
                    try:
                        rel = src.relative_to(ws_path)
                    except ValueError:
                        rel = src.name
                    dst = backup_path / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

            backup_callback = _backup_file

        llm_config = self.config.get('llm', {})
        agent = CodingAgent(
            llm=llm,
            workspace_root=ws,
            max_iterations=self.config.get('orchestration', {}).get('max_iterations', 10),
            temperature=llm_config.get('temperature', 0.2),
            max_tokens=llm_config.get('max_tokens', 4096),
        )

        # Configure tools
        if dry_run:
            agent.tools.enable_diff_review = True
        if backup_callback:
            agent.tools.set_backup_callback(backup_callback)

        return agent

    def _load_queue(self) -> List[Dict]:
        """Load task queue"""
        with self._file_lock:
            with open(self.task_queue_path, 'r') as f:
                return json.load(f)

    def _save_queue(self, queue: List[Dict]):
        """Save task queue"""
        with self._file_lock:
            with open(self.task_queue_path, 'w') as f:
                json.dump(queue, f, indent=2)

    def _load_completed(self) -> List[Dict]:
        """Load completed tasks"""
        with self._file_lock:
            with open(self.completed_path, 'r') as f:
                return json.load(f)

    def _save_completed(self, completed: List[Dict]):
        """Save completed tasks"""
        with self._file_lock:
            with open(self.completed_path, 'w') as f:
                json.dump(completed, f, indent=2)

    def _append_completed(self, task: Dict):
        """Thread-safe append a single task to completed list."""
        with self._file_lock:
            with open(self.completed_path, 'r') as f:
                completed = json.load(f)
            completed.append(task)
            with open(self.completed_path, 'w') as f:
                json.dump(completed, f, indent=2)

    def add_task(
        self,
        description: str,
        context: Optional[str] = None,
        priority: str = "normal",
        workspace_override: Optional[str] = None,
    ) -> str:
        """
        Add a task to the queue.
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
            "assigned_to": "coding_agent",
        }
        if workspace_override:
            task["workspace_override"] = workspace_override

        queue = self._load_queue()
        queue.append(task)
        self._save_queue(queue)

        print(f"✓ Task added: {task_id}")
        print(f"  Description: {description[:120]}")

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

    def execute_next_task(
        self,
        workspace_override: Optional[str] = None,
        dry_run: bool = False,
        backup_dir: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Execute the next task in the queue.
        Returns: task result or None if queue is empty.
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

        # Determine workspace
        ws = workspace_override or task.get('workspace_override')

        # Create agent for this task
        agent = self._create_agent(
            workspace_root=ws,
            dry_run=dry_run,
            backup_dir=backup_dir,
        )

        # Execute task
        task['status'] = 'running'
        task['started_at'] = datetime.now().isoformat()

        try:
            result = agent.run_task(
                task_description=task['description'],
                context=task.get('context')
            )

            task['status'] = 'completed' if result['success'] else 'failed'
            task['completed_at'] = datetime.now().isoformat()
            task['result'] = result

            # If dry_run, collect pending diffs and reject them
            if dry_run:
                pending = agent.tools.list_pending_changes()
                task['dry_run_diffs'] = pending
                agent.tools.cleanup_pending_diffs()

            # Save to completed
            self._append_completed(task)

            # Save detailed log
            log_file = self.logs_path / f"{task['task_id']}.json"
            with open(log_file, 'w') as f:
                json.dump(task, f, indent=2)

            print(f"\n{'='*70}")
            print(f"TASK {'COMPLETED' if result['success'] else 'FAILED'}: {task['task_id']}")
            if dry_run:
                print(f"(DRY RUN — no changes applied)")
            print(f"{'='*70}\n")

            return task

        except Exception as e:
            task['status'] = 'error'
            task['error'] = str(e)
            task['completed_at'] = datetime.now().isoformat()

            self._append_completed(task)

            print(f"\n✗ Task error: {str(e)}\n")
            return task

    def execute_all_tasks(self):
        """Execute all tasks in the queue sequentially."""
        while True:
            result = self.execute_next_task()
            if result is None:
                break
            time.sleep(1)  # Brief pause between tasks

    def execute_parallel(self, max_workers: int = 2) -> List[Dict]:
        """
        Execute all queued tasks in parallel using a thread pool.
        Each task gets its own CodingAgent instance.

        Args:
            max_workers: Maximum concurrent tasks

        Returns:
            List of task result dicts
        """
        queue = self._load_queue()
        if not queue:
            print("Queue is empty")
            return []

        # Take all tasks from queue
        tasks = list(queue)
        self._save_queue([])

        print(f"\nExecuting {len(tasks)} tasks with {max_workers} workers\n")

        results = []

        def _run_task(task: Dict) -> Dict:
            ws = task.get('workspace_override')
            agent = self._create_agent(workspace_root=ws)

            task['status'] = 'running'
            task['started_at'] = datetime.now().isoformat()

            try:
                result = agent.run_task(
                    task_description=task['description'],
                    context=task.get('context'),
                )
                task['status'] = 'completed' if result['success'] else 'failed'
                task['completed_at'] = datetime.now().isoformat()
                task['result'] = result
            except Exception as e:
                task['status'] = 'error'
                task['error'] = str(e)
                task['completed_at'] = datetime.now().isoformat()

            # Thread-safe save
            self._append_completed(task)

            # Save log
            log_file = self.logs_path / f"{task['task_id']}.json"
            with open(log_file, 'w') as f:
                json.dump(task, f, indent=2)

            return task

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_run_task, t): t for t in tasks}
            for future in as_completed(futures):
                task_result = future.result()
                results.append(task_result)
                print(f"  {task_result['task_id']}: {task_result['status']}")

        print(f"\nAll {len(results)} tasks finished.\n")
        return results

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

    # Parallel
    parallel_parser = subparsers.add_parser('parallel', help='Execute tasks in parallel')
    parallel_parser.add_argument('--workers', type=int, default=2, help='Number of workers')

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

    elif args.command == 'parallel':
        orchestrator.execute_parallel(max_workers=args.workers)

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
