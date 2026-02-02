#!/usr/bin/env python3
"""
Quick test to verify the coding agent system works
"""
import sys
from orchestrator import TaskOrchestrator

def test_basic_functionality():
    """Test basic agent functionality"""
    print("="*60)
    print("TESTING CODING AGENT SYSTEM")
    print("="*60)

    orchestrator = TaskOrchestrator()

    # Test 1: Add a simple task
    print("\n[Test 1] Adding a simple task...")
    task_id = orchestrator.add_task(
        "Read the podcast_crew.py file and list the main agent roles",
        context="Focus on identifying the Agent definitions"
    )
    print(f"✓ Task added: {task_id}")

    # Test 2: Execute the task
    print("\n[Test 2] Executing task with local agent...")
    print("(This will use Qwen3-Coder via Ollama)")
    print("-" * 60)

    result = orchestrator.execute_next_task()

    if result:
        print("\n" + "="*60)
        print("TEST RESULT")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Task ID: {result['task_id']}")

        if result['status'] == 'completed':
            print("\n✓ SUCCESS! Agent completed the task")
            print(f"\nAgent's response:")
            print("-" * 60)
            print(result['result']['result'])
            print("-" * 60)

            print(f"\nIterations used: {result['result']['iterations']}")
            print(f"Tool calls made: {len(result['result']['tool_calls'])}")

            return True
        else:
            print("\n✗ FAILED - Agent could not complete task")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
    else:
        print("\n✗ No task was executed")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
