#!/usr/bin/env python3
"""
Quick delegation interface for Claude Code to assign tasks to the coding agent.

Supports multiple input modes (positional, --file, stdin), immediate execution (--now),
workspace overrides, structured JSON output, dry-run previews, parallel execution,
task templates, and self-update capability.
"""
import sys
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all flags."""
    parser = argparse.ArgumentParser(
        description="Delegate tasks to the coding agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  delegate.py "Add error handling to foo.py"
  delegate.py "Refactor bar()" --now --workspace /path/to/project
  delegate.py --file task.md --now --json
  echo "Fix the bug" | delegate.py --now
  delegate.py --template refactor_method "file_path=foo.py method_name=bar" --now
  delegate.py --self-update --dry-run "Add a comment to delegate.py"
  delegate.py --parallel 3
  delegate.py --list
  delegate.py --status task_123456
"""
    )

    # Task input (positional — can coexist with --file/stdin logic)
    parser.add_argument('task', nargs='?', default=None,
                        help='Task description (or template variables when --template is used)')

    # Task input alternatives
    parser.add_argument('--file', '-f', metavar='FILE',
                        help='Read task description from a file')

    # Execution modifiers
    parser.add_argument('--now', action='store_true',
                        help='Queue and execute immediately')
    parser.add_argument('--workspace', '-w', metavar='DIR',
                        help='Override workspace directory')
    parser.add_argument('--context', '-c', metavar='TEXT',
                        help='Additional context string')
    parser.add_argument('--files', metavar='FILE1,FILE2,...',
                        help='Comma-separated files to auto-inject as context')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='Structured JSON output')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show diffs without applying changes')
    parser.add_argument('--parallel', type=int, metavar='N',
                        help='Execute N queued tasks in parallel')
    parser.add_argument('--template', '-t', metavar='NAME',
                        help='Use named task template')
    parser.add_argument('--self-update', action='store_true',
                        help='Target the coding agent itself (with backup)')

    # Reflection commands
    parser.add_argument('--reflect', metavar='TASK_ID',
                        help='View reflection for a completed task')
    parser.add_argument('--lessons', action='store_true',
                        help='View aggregated lessons learned')

    # Existing query commands
    parser.add_argument('--execute', action='store_true',
                        help='Execute next task in queue')
    parser.add_argument('--execute-all', action='store_true',
                        help='Execute all queued tasks')
    parser.add_argument('--status', metavar='TASK_ID',
                        help='Check status of a task')
    parser.add_argument('--list', action='store_true', dest='list_tasks',
                        help='List queued tasks')
    parser.add_argument('--summary', action='store_true',
                        help='View task summary')

    return parser


def get_task_description(args) -> str | None:
    """Resolve task description from positional arg, --file, or stdin."""
    if args.task:
        return args.task
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return path.read_text().strip()
    elif not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return None


def inject_file_context(task: str, file_list: str, workspace: str) -> str:
    """Prepend file contents as markdown context to the task description."""
    workspace_path = Path(workspace)
    parts = []
    for f in file_list.split(','):
        f = f.strip()
        fpath = workspace_path / f
        if fpath.exists():
            parts.append(f"## {f}\n```\n{fpath.read_text()}\n```")
        else:
            parts.append(f"## {f}\n*(file not found)*")
    return "\n".join(["# File Context"] + parts + [f"\n# Task\n{task}"])


def render_template(template_name: str, variables_str: str | None) -> str:
    """Load and render a task template with provided variables."""
    from core.templates import TaskTemplate
    template = TaskTemplate.load(template_name)

    # Parse variables from "key=value key2=value2" format
    variables = {}
    if variables_str:
        for part in variables_str.split():
            if '=' in part:
                k, v = part.split('=', 1)
                variables[k] = v

    return template.render(variables)


def setup_self_update(args):
    """Configure self-update mode: set workspace to coding agent dir, create backup."""
    agent_dir = Path(__file__).parent.resolve()
    args.workspace = str(agent_dir)

    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = agent_dir / "backups" / f"self_update_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Back up key source files
    for pattern in ["*.py", "core/*.py", "tools/*.py", "agents/*.py", "config/*.yaml"]:
        for src in agent_dir.glob(pattern):
            if src.is_file():
                rel = src.relative_to(agent_dir)
                dst = backup_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    print(f"Backup created: {backup_dir}")
    print(f"To rollback: cp -r {backup_dir}/* {agent_dir}/")

    return backup_dir


def format_json_result(task_result: dict) -> str:
    """Format task result as structured JSON."""
    if task_result is None:
        return json.dumps({"status": "empty_queue", "message": "No tasks in queue"})

    # Extract files_modified from tool_calls
    files_modified = []
    result_data = task_result.get('result', {})
    if isinstance(result_data, dict):
        for tc in result_data.get('tool_calls', []):
            if tc.get('tool') in ('write_file', 'edit_file'):
                fp = tc.get('arguments', {}).get('file_path')
                if fp and fp not in files_modified:
                    files_modified.append(fp)

    output = {
        "status": task_result.get('status', 'unknown'),
        "task_id": task_result.get('task_id', ''),
        "files_modified": files_modified,
        "iterations": result_data.get('iterations', 0) if isinstance(result_data, dict) else 0,
        "result_message": result_data.get('result', str(result_data)) if isinstance(result_data, dict) else str(result_data),
    }
    return json.dumps(output, indent=2)


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Import orchestrator lazily to keep --help fast
    from orchestrator import TaskOrchestrator

    # --- Reflection commands ---
    if args.reflect:
        from core.reflection import ReflectionEngine
        engine = ReflectionEngine(llm=None, storage_dir=Path("reflections"))
        r = engine.get_reflection(args.reflect)
        if r:
            print(json.dumps(r, indent=2))
        else:
            print(f"No reflection found for {args.reflect}")
        return

    if args.lessons:
        from core.reflection import ReflectionEngine
        engine = ReflectionEngine(llm=None, storage_dir=Path("reflections"))
        lessons = engine.get_lessons()
        if lessons:
            for lesson in lessons:
                print(f"  - {lesson}")
        else:
            print("No lessons accumulated yet.")
        return

    # --- Query commands (no task needed) ---
    if args.status:
        orchestrator = TaskOrchestrator()
        status = orchestrator.get_task_status(args.status)
        if status:
            print(json.dumps(status, indent=2))
        else:
            print(f"Task {args.status} not found")
        return

    if args.list_tasks:
        orchestrator = TaskOrchestrator()
        queue = orchestrator.list_queue()
        print(json.dumps(queue, indent=2))
        return

    if args.summary:
        orchestrator = TaskOrchestrator()
        summary = orchestrator.get_summary()
        print(json.dumps(summary, indent=2))
        return

    if args.execute:
        orchestrator = TaskOrchestrator()
        result = orchestrator.execute_next_task(
            workspace_override=args.workspace,
            dry_run=args.dry_run,
        )
        if args.json_output and result:
            print(format_json_result(result))
        return

    if args.execute_all:
        orchestrator = TaskOrchestrator()
        orchestrator.execute_all_tasks()
        return

    if args.parallel:
        orchestrator = TaskOrchestrator()
        results = orchestrator.execute_parallel(max_workers=args.parallel)
        if args.json_output:
            print(json.dumps([json.loads(format_json_result(r)) for r in results], indent=2))
        else:
            for r in results:
                print(f"  {r.get('task_id', '?')}: {r.get('status', '?')}")
        return

    # --- Self-update setup ---
    backup_dir = None
    if args.self_update:
        if not args.dry_run:
            confirm = input("Self-update will modify the coding agent. Continue? [y/N] ")
            if confirm.lower() != 'y':
                print("Aborted.")
                return
        backup_dir = setup_self_update(args)

    # --- Resolve task description ---
    if args.template:
        task_desc = render_template(args.template, args.task)
    else:
        task_desc = get_task_description(args)

    if not task_desc:
        parser.print_help()
        sys.exit(1)

    # --- File context injection ---
    workspace = args.workspace or str(Path(__file__).parent.resolve())
    if args.files:
        task_desc = inject_file_context(task_desc, args.files, workspace)

    # --- Context ---
    context = args.context

    # --- Queue the task ---
    orchestrator = TaskOrchestrator()
    task_id = orchestrator.add_task(
        task_desc,
        context=context,
        workspace_override=args.workspace,
    )

    # --- Immediate execution ---
    if args.now:
        result = orchestrator.execute_next_task(
            workspace_override=args.workspace,
            dry_run=args.dry_run,
            backup_dir=str(backup_dir) if backup_dir else None,
        )
        if args.json_output:
            print(format_json_result(result))
        elif result:
            status = result.get('status', 'unknown')
            print(f"\nResult: {status}")
            if backup_dir:
                print(f"\nRollback: cp -r {backup_dir}/* {Path(__file__).parent.resolve()}/")
    else:
        print(f"\n✓ Task queued: {task_id}")
        print(f"\nTo execute:")
        print(f"  python3 delegate.py --execute")


if __name__ == "__main__":
    main()
