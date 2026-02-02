#!/usr/bin/env python3
"""
Quick delegation interface for Claude Code to assign tasks to the coding agent
"""
import sys
import json
from pathlib import Path
from orchestrator import TaskOrchestrator


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 delegate.py \"<task_description>\" [--context \"<context>\"]")
        print("")
        print("Examples:")
        print('  python3 delegate.py "Add error handling to podcast_crew.py"')
        print('  python3 delegate.py "Write tests for the search_tool function" --context "Focus on edge cases"')
        print("")
        print("Quick commands:")
        print("  python3 delegate.py --status <task_id>    # Check task status")
        print("  python3 delegate.py --execute              # Execute next task in queue")
        print("  python3 delegate.py --execute-all          # Execute all queued tasks")
        print("  python3 delegate.py --summary              # View summary")
        print("  python3 delegate.py --list                 # List queued tasks")
        sys.exit(1)

    orchestrator = TaskOrchestrator()

    # Handle commands
    if sys.argv[1] == "--status" and len(sys.argv) > 2:
        status = orchestrator.get_task_status(sys.argv[2])
        if status:
            print(json.dumps(status, indent=2))
        else:
            print(f"Task {sys.argv[2]} not found")
        return

    if sys.argv[1] == "--execute":
        orchestrator.execute_next_task()
        return

    if sys.argv[1] == "--execute-all":
        orchestrator.execute_all_tasks()
        return

    if sys.argv[1] == "--summary":
        summary = orchestrator.get_summary()
        print(json.dumps(summary, indent=2))
        return

    if sys.argv[1] == "--list":
        queue = orchestrator.list_queue()
        print(json.dumps(queue, indent=2))
        return

    # Add task
    task_desc = sys.argv[1]
    context = None

    if "--context" in sys.argv:
        context_idx = sys.argv.index("--context")
        if len(sys.argv) > context_idx + 1:
            context = sys.argv[context_idx + 1]

    task_id = orchestrator.add_task(task_desc, context=context)
    print(f"\n✓ Task queued: {task_id}")
    print(f"\nTo execute:")
    print(f"  python3 delegate.py --execute")


if __name__ == "__main__":
    main()
