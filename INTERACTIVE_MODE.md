# Interactive Mode Guide

## Overview

The Hierarchical Coding Agent supports two workflow modes:

1. **Programmatic Mode** (default): Returns to caller (Claude Code) at checkpoints for approval
2. **Interactive Mode** (new): Works directly with user via terminal prompts

This allows the agent to be used both as a library component in automated systems and as a standalone interactive tool.

## Modes Comparison

| Feature | Programmatic Mode | Interactive Mode |
|---------|-------------------|------------------|
| **Approval Method** | Returns to caller | Asks user via `input()` |
| **Checkpoints** | Returns at 2 checkpoints | Handles checkpoints internally |
| **Usage** | Called from code (e.g., Claude Code) | Run from terminal |
| **Complete in one call** | No - requires multiple calls | Yes - runs to completion |
| **CLI Flag** | Default (no flag) | `--interactive` or `-i` |

## Programmatic Mode (Default)

**Use Case:** Integration with Claude Code or other automation systems

**Behavior:**
1. Creates implementation plan
2. **Returns** with status `awaiting_user_approval` and plan for review
3. Caller approves/rejects
4. Call `continue_after_plan_approval()` to resume
5. Implements code, runs tests
6. **Returns** with status `awaiting_user_approval` and results
7. Caller approves/rejects for PR creation

**Example Usage from Python:**

```python
from hierarchical_orchestrator import HierarchicalOrchestrator

orchestrator = HierarchicalOrchestrator()

# Start workflow
result = orchestrator.autonomous_workflow("Add error handling to API")

# Check plan
if result['status'] == 'awaiting_user_approval' and result['stage'] == 'plan_created':
    print("Plan:", result['plan'])

    # User approves (handled by caller)
    user_approved = input("Approve? (y/n): ").lower() == 'y'

    if user_approved:
        # Continue workflow
        result = orchestrator.continue_after_plan_approval(
            result['workflow_log'],
            result['plan']
        )

        # Check implementation
        if result['status'] == 'awaiting_user_approval' and result['stage'] == 'implementation_complete':
            print("Review:", result['review'])
            # User approves for PR creation...
```

**Example Usage from CLI:**

```bash
# Start workflow (returns at plan checkpoint)
python3 hierarchical_orchestrator.py "Add error handling to API"

# Review plan, then continue manually via Python if approved
```

## Interactive Mode

**Use Case:** Direct terminal usage when running the agent standalone

**Behavior:**
1. Creates implementation plan
2. **Asks user directly**: "Do you approve this plan? (yes/no/edit)"
   - `yes`: Continues to implementation
   - `no`: Aborts workflow
   - `edit`: Ask for changes, revise plan with Qwen3-Lead
3. Implements code, runs tests
4. **Asks user directly**: "Do you approve the implementation? (yes/no/retry)"
   - `yes`: Completes workflow, saves log
   - `no`: Aborts workflow
   - `retry`: Re-runs implementation with same plan
5. Returns final status `completed` or `aborted`

**Example Usage from CLI:**

```bash
# Run in interactive mode
python3 hierarchical_orchestrator.py --interactive "Add error handling to API"

# OR shorthand:
python3 hierarchical_orchestrator.py -i "Add error handling to API"
```

**Interactive Session Example:**

```
$ python3 hierarchical_orchestrator.py -i "Add error handling to API"

======================================================================
AUTONOMOUS WORKFLOW STARTED
======================================================================
User Request: Add error handling to API

STAGE 1: Qwen3 (Project Lead) Creating Implementation Plan...
----------------------------------------------------------------------

[Plan created by Qwen3-Lead...]

----------------------------------------------------------------------

======================================================================
PLAN APPROVAL REQUIRED
======================================================================

Do you approve this plan? (yes/no/edit): edit
What changes would you like to the plan?
Changes: Add logging for errors

Revising plan based on your feedback...

[Revised plan shown...]

Do you approve this plan? (yes/no/edit): yes
✓ Plan approved! Continuing with implementation...

======================================================================
CONTINUING WORKFLOW - Plan Approved
======================================================================

STAGE 2: Qwen3-Coder (Project Member) Implementing...
----------------------------------------------------------------------
[Implementation output...]

STAGE 3: Qwen3 (Project Lead) Reviewing Implementation...
----------------------------------------------------------------------
[Review output...]

STAGE 4: Output Verification Testing...
----------------------------------------------------------------------
✓ Output verification PASSED

======================================================================
FINAL APPROVAL REQUIRED
======================================================================

Implementation Summary:
  Plan: Created and approved
  Implementation: Completed
  Review: Code quality acceptable, follows plan...
  Verification: PASSED

Do you approve the implementation? (yes/no/retry): yes
✓ Implementation approved! Workflow complete.

✓ Workflow log saved: logs/workflow_20260202_143022.json

======================================================================
WORKFLOW RESULT
======================================================================
Status: completed
Stage: approved

✓ Workflow completed successfully!
  Log file: logs/workflow_20260202_143022.json
  Next: Ready to create PR or deploy
```

## Implementation Details

### Key Methods

**`autonomous_workflow(user_request: str, interactive: bool = False)`**
- Main entry point for both modes
- `interactive=False`: Programmatic mode (default)
- `interactive=True`: Interactive mode
- Returns at CHECKPOINT 1 (plan) or CHECKPOINT 2 (implementation) in programmatic mode
- Handles both checkpoints internally in interactive mode

**`_continue_workflow(workflow_log: Dict, plan: str, interactive: bool = False)`**
- Internal method to continue after plan approval
- Called by `autonomous_workflow()` after CHECKPOINT 1
- Handles CHECKPOINT 2 similarly (return vs ask user)
- Not meant to be called directly (use `continue_after_plan_approval` instead)

**`continue_after_plan_approval(workflow_log: Dict, plan: str)`**
- Backward compatibility wrapper for programmatic mode
- Always uses `interactive=False`
- Provided for external callers (like Claude Code)

### Return Values

**Programmatic Mode Returns:**

At CHECKPOINT 1 (plan created):
```python
{
    "status": "awaiting_user_approval",
    "stage": "plan_created",
    "plan": "<implementation plan>",
    "workflow_log": {...},
    "next_action": "User must approve this plan to proceed"
}
```

At CHECKPOINT 2 (implementation complete):
```python
{
    "status": "awaiting_user_approval",
    "stage": "implementation_complete",
    "plan": "<implementation plan>",
    "implementation": {...},
    "review": "<code review>",
    "verification": {...},
    "workflow_log": {...},
    "next_action": "User must review and approve to create PR"
}
```

**Interactive Mode Returns:**

On completion:
```python
{
    "status": "completed",
    "stage": "approved",
    "plan": "<implementation plan>",
    "implementation": {...},
    "review": "<code review>",
    "verification": {...},
    "workflow_log": {...},
    "log_file": "logs/workflow_20260202_143022.json",
    "next_action": "Ready to create PR or deploy"
}
```

On abort (user rejected):
```python
{
    "status": "aborted",
    "stage": "plan_rejected" | "implementation_rejected",
    "plan": "<implementation plan>",
    "workflow_log": {...}
}
```

## Use Cases

### When to Use Programmatic Mode
- Integration with Claude Code
- Automated CI/CD pipelines
- Custom approval workflows
- Multi-agent orchestration systems
- When approval logic is complex or needs external validation

### When to Use Interactive Mode
- Running agent standalone from terminal
- Quick testing and prototyping
- Manual task execution
- Learning how the agent works
- When you want immediate feedback and control

## Configuration

No configuration changes needed. The mode is determined solely by the `--interactive` flag or `interactive` parameter.

## Backward Compatibility

All existing code calling the orchestrator continues to work:

```python
# Old code (still works - defaults to programmatic mode)
orchestrator = HierarchicalOrchestrator()
result = orchestrator.autonomous_workflow("Add feature")
# Returns at checkpoint as before

# New interactive usage
result = orchestrator.autonomous_workflow("Add feature", interactive=True)
# Completes fully with user prompts
```

## Testing

Run structure tests:
```bash
python3 test_interactive_mode.py
```

Test programmatic mode:
```bash
python3 hierarchical_orchestrator.py "Add logging to function"
# Should pause at plan checkpoint
```

Test interactive mode:
```bash
python3 hierarchical_orchestrator.py -i "Add logging to function"
# Should ask for approval interactively
```

## Limitations

**Interactive Mode:**
- Requires terminal access (can't be used in non-interactive environments)
- No timeout on user input (waits indefinitely)
- Single-user workflow (no concurrent approvals)

**Programmatic Mode:**
- Requires caller to manage state between checkpoints
- More complex integration code needed

## Future Enhancements

- [ ] Web-based approval UI for remote workflows
- [ ] Timeout support for interactive prompts
- [ ] Approval delegation to multiple reviewers
- [ ] Approval history and audit trail
- [ ] Custom checkpoint hooks
