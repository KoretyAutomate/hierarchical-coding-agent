#!/usr/bin/env python3
"""
Hierarchical Agent Orchestrator
3-Tier System: Claude (PM) → Qwen3 (Lead) → Qwen3-Coder (Member)
"""
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import yaml
from output_verifier import OutputVerifier

class HierarchicalOrchestrator:
    """
    Manages the 3-tier agent hierarchy:
    - Project Manager (Claude Code): Coordinates workflow
    - Project Lead (Qwen3): Makes decisions, reviews plans
    - Project Member (Qwen3-Coder): Implements code
    """

    def __init__(self, config_path: str = "/home/korety/coding-agent/config/agent_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # API endpoints (both on Ollama)
        self.qwen3_lead_url = "http://localhost:11434/v1"  # Project Lead (Qwen3-32B)
        self.qwen3_coder_url = "http://localhost:11434/v1"  # Project Member (Qwen3-Coder)

        # Model names
        self.qwen3_lead_model = "qwen3:32b"
        self.qwen3_coder_model = "qwen3-coder:latest"

        # Paths
        self.workspace = Path(self.config['workspace']['project_root'])
        self.logs_dir = Path(self.config['orchestration']['logs_path'])
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        print("✓ Hierarchical Orchestrator initialized")
        print(f"  Project Lead: Qwen3 @ {self.qwen3_lead_url}")
        print(f"  Project Member: Qwen3-Coder @ {self.qwen3_coder_url}")
        print(f"  Workspace: {self.workspace}")

    def call_qwen3_lead(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call Qwen3 (Project Lead) for decision-making and planning.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = httpx.post(
                f"{self.qwen3_lead_url}/chat/completions",
                json={
                    "model": self.qwen3_lead_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Error calling Qwen3 Lead: {e}"

    def call_qwen3_coder(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call Qwen3-Coder (Project Member) for implementation.
        Uses the existing coding agent system.
        """
        from orchestrator import TaskOrchestrator

        # Use existing coding agent infrastructure
        task_orch = TaskOrchestrator()
        task_id = task_orch.add_task(prompt)
        result = task_orch.execute_next_task()

        return result

    def autonomous_workflow(self, user_request: str, interactive: bool = False) -> Dict[str, Any]:
        """
        Fully autonomous workflow with two modes:

        INTERACTIVE MODE (interactive=True):
        - Works directly with user via terminal
        - Asks for approval using input()
        - Completes full workflow in one call

        PROGRAMMATIC MODE (interactive=False):
        - Returns to caller (Claude Code) at checkpoints
        - Caller handles approval
        - Requires continue_after_plan_approval() call

        Workflow:
        1. User provides request
        2. Qwen3 (Lead) creates implementation plan
        3. User approves plan [CHECKPOINT - interactive or return]
        4. Qwen3-Coder implements
        5. Qwen3 reviews implementation
        6. Output verification
        7. User approves results [CHECKPOINT - interactive or return]
        """
        workflow_log = {
            "user_request": user_request,
            "timestamp": datetime.now().isoformat(),
            "stages": [],
            "interactive_mode": interactive
        }

        print(f"\n{'='*70}")
        print(f"AUTONOMOUS WORKFLOW STARTED")
        print(f"{'='*70}")
        print(f"User Request: {user_request}\n")

        # STAGE 1: Qwen3 creates plan
        print("STAGE 1: Qwen3 (Project Lead) Creating Implementation Plan...")
        print("-" * 70)

        planning_prompt = f"""You are the Project Lead responsible for planning software implementations.

User Request: {user_request}

Create a detailed implementation plan that includes:
1. **Requirements Analysis**: What needs to be built
2. **Technical Approach**: How to implement it
3. **File Changes**: Which files need to be modified/created
4. **Testing Strategy**: How to verify it works
5. **Success Criteria**: How to know when it's complete

Be specific and actionable. This plan will be given to a junior developer (Qwen3-Coder) to implement.

Provide your plan in a clear, structured format."""

        system_prompt = """You are an experienced Project Lead (Technical Architect) responsible for:
- Analyzing requirements
- Creating detailed implementation plans
- Reviewing code from junior developers
- Making technical decisions
- Ensuring quality standards

You work with:
- Project Manager (Claude Code): Coordinates workflow, runs tests
- Junior Developer (Qwen3-Coder): Implements your plans

Be thorough but concise. Focus on actionable guidance."""

        plan = self.call_qwen3_lead(planning_prompt, system_prompt)

        workflow_log["stages"].append({
            "stage": "planning",
            "agent": "qwen3_lead",
            "output": plan
        })

        print(f"\n{plan}\n")
        print("-" * 70)

        # CHECKPOINT 1: Plan approval
        if not interactive:
            # Programmatic mode - return to caller
            return {
                "status": "awaiting_user_approval",
                "stage": "plan_created",
                "plan": plan,
                "workflow_log": workflow_log,
                "next_action": "User must approve this plan to proceed"
            }

        # Interactive mode - ask user directly
        print(f"\n{'='*70}")
        print(f"PLAN APPROVAL REQUIRED")
        print(f"{'='*70}")

        while True:
            approval = input("\nDo you approve this plan? (yes/no/edit): ").strip().lower()

            if approval in ['yes', 'y']:
                print("✓ Plan approved! Continuing with implementation...\n")
                break
            elif approval in ['no', 'n']:
                print("✗ Plan rejected. Workflow aborted.")
                return {
                    "status": "aborted",
                    "stage": "plan_rejected",
                    "plan": plan,
                    "workflow_log": workflow_log
                }
            elif approval == 'edit':
                print("\nWhat changes would you like to the plan?")
                changes = input("Changes: ").strip()

                # Ask Qwen3 to revise plan
                revision_prompt = f"""The user reviewed your plan and requested changes:

Original Plan:
{plan}

Requested Changes:
{changes}

Please provide a revised implementation plan addressing these changes."""

                print("\nRevising plan based on your feedback...")
                plan = self.call_qwen3_lead(revision_prompt, system_prompt)

                workflow_log["stages"].append({
                    "stage": "plan_revision",
                    "agent": "qwen3_lead",
                    "user_feedback": changes,
                    "output": plan
                })

                print(f"\n{'-'*70}")
                print("REVISED PLAN:")
                print(f"{'-'*70}\n{plan}\n{'-'*70}")
            else:
                print("Please enter 'yes', 'no', or 'edit'")

        # Continue to implementation
        return self._continue_workflow(workflow_log, plan, interactive)

    def _continue_workflow(self, workflow_log: Dict, plan: str, interactive: bool = False) -> Dict[str, Any]:
        """
        Internal method to continue workflow after plan approval.
        Used by both interactive and programmatic modes.
        """
        print(f"\n{'='*70}")
        print(f"CONTINUING WORKFLOW - Plan Approved")
        print(f"{'='*70}\n")

        # STAGE 2: Qwen3-Coder implements
        print("STAGE 2: Qwen3-Coder (Project Member) Implementing...")
        print("-" * 70)

        implementation_request = f"""Implement the following plan:

{plan}

Follow the plan exactly. Report what you did when complete."""

        implementation_result = self.call_qwen3_coder(implementation_request)

        workflow_log["stages"].append({
            "stage": "implementation",
            "agent": "qwen3_coder",
            "output": implementation_result
        })

        print(f"\nImplementation Result: {json.dumps(implementation_result, indent=2)}\n")
        print("-" * 70)

        # STAGE 3: Qwen3 reviews
        print("STAGE 3: Qwen3 (Project Lead) Reviewing Implementation...")
        print("-" * 70)

        review_prompt = f"""Review this implementation by the junior developer:

Original Plan:
{plan}

Implementation Result:
{json.dumps(implementation_result, indent=2)}

As Project Lead, review:
1. Does it follow the plan?
2. Is the code quality acceptable?
3. Are there any issues or improvements needed?
4. Should we proceed to testing?

Provide your review and decision: APPROVE or REQUEST_CHANGES."""

        review = self.call_qwen3_lead(review_prompt)

        workflow_log["stages"].append({
            "stage": "review",
            "agent": "qwen3_lead",
            "output": review
        })

        print(f"\n{review}\n")
        print("-" * 70)

        # STAGE 4: Output Verification Testing
        print("STAGE 4: Output Verification Testing...")
        print("-" * 70)

        try:
            verifier = OutputVerifier(str(self.workspace))

            # First do a quick check to see if outputs exist
            print("\nRunning quick output check...")
            quick_check_result = verifier.quick_check()

            verification_result = {
                "quick_check": quick_check_result,
                "full_test": None
            }

            # If quick check passes, consider running full test (optional - can be slow)
            # For now, we'll just use quick check to verify files exist
            # User can manually run full tests before PR if needed

            workflow_log["stages"].append({
                "stage": "output_verification",
                "agent": "output_verifier",
                "output": verification_result
            })

            if quick_check_result.get("success"):
                print("\n✓ Output verification PASSED")
            else:
                print("\n⚠ Output verification issues detected")
                print("Missing files:", quick_check_result.get("missing_files", []))
                print("Invalid files:", quick_check_result.get("invalid_files", []))

        except Exception as e:
            print(f"\n⚠ Output verification could not run: {e}")
            verification_result = {"error": str(e)}
            workflow_log["stages"].append({
                "stage": "output_verification",
                "agent": "output_verifier",
                "output": verification_result
            })

        print("-" * 70)

        # CHECKPOINT 2: Final approval
        if not interactive:
            # Programmatic mode - return to caller
            return {
                "status": "awaiting_user_approval",
                "stage": "implementation_complete",
                "plan": plan,
                "implementation": implementation_result,
                "review": review,
                "verification": verification_result,
                "workflow_log": workflow_log,
                "next_action": "User must review and approve to create PR"
            }

        # Interactive mode - ask user for final approval
        print(f"\n{'='*70}")
        print(f"FINAL APPROVAL REQUIRED")
        print(f"{'='*70}")
        print("\nImplementation Summary:")
        print(f"  Plan: Created and approved")
        print(f"  Implementation: Completed")
        print(f"  Review: {review[:100]}..." if len(str(review)) > 100 else f"  Review: {review}")
        print(f"  Verification: {'PASSED' if verification_result.get('quick_check', {}).get('success') else 'ISSUES DETECTED'}")

        while True:
            approval = input("\nDo you approve the implementation? (yes/no/retry): ").strip().lower()

            if approval in ['yes', 'y']:
                print("✓ Implementation approved! Workflow complete.\n")

                # Save workflow log
                log_file = self.save_workflow_log(workflow_log)

                return {
                    "status": "completed",
                    "stage": "approved",
                    "plan": plan,
                    "implementation": implementation_result,
                    "review": review,
                    "verification": verification_result,
                    "workflow_log": workflow_log,
                    "log_file": str(log_file),
                    "next_action": "Ready to create PR or deploy"
                }
            elif approval in ['no', 'n']:
                print("✗ Implementation rejected. Workflow aborted.")
                self.save_workflow_log(workflow_log)
                return {
                    "status": "aborted",
                    "stage": "implementation_rejected",
                    "plan": plan,
                    "implementation": implementation_result,
                    "review": review,
                    "verification": verification_result,
                    "workflow_log": workflow_log
                }
            elif approval == 'retry':
                print("\nRetrying implementation with same plan...")
                # Recursive retry - go back to implementation stage
                return self._continue_workflow(workflow_log, plan, interactive)
            else:
                print("Please enter 'yes', 'no', or 'retry'")

    def continue_after_plan_approval(self, workflow_log: Dict, plan: str) -> Dict[str, Any]:
        """
        Backward compatibility wrapper for programmatic mode.
        Continue workflow after plan has been approved externally.

        This method is for programmatic callers (like Claude Code) who handle
        approval themselves. For interactive mode, use autonomous_workflow(interactive=True).
        """
        return self._continue_workflow(workflow_log, plan, interactive=False)

    def save_workflow_log(self, workflow_log: Dict):
        """Save workflow log for audit trail."""
        log_file = self.logs_dir / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(workflow_log, f, indent=2)
        print(f"\n✓ Workflow log saved: {log_file}")
        return log_file


def main():
    """Test the hierarchical orchestrator."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Hierarchical Coding Agent Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Programmatic mode (returns at checkpoints for external approval)
  python3 hierarchical_orchestrator.py "Add error handling to the search function"

  # Interactive mode (asks user directly via terminal)
  python3 hierarchical_orchestrator.py --interactive "Add error handling to the search function"
        """
    )
    parser.add_argument('request', type=str, help='User request for the coding task')
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode (ask user for approvals directly)'
    )

    args = parser.parse_args()

    orchestrator = HierarchicalOrchestrator()

    # Start autonomous workflow
    result = orchestrator.autonomous_workflow(args.request, interactive=args.interactive)

    # Display results
    print(f"\n{'='*70}")
    print(f"WORKFLOW RESULT")
    print(f"{'='*70}")
    print(f"Status: {result['status']}")
    print(f"Stage: {result['stage']}")

    if result['status'] == 'awaiting_user_approval':
        # Programmatic mode - paused at checkpoint
        print(f"\nNext: {result['next_action']}")
        orchestrator.save_workflow_log(result['workflow_log'])
        print("\n✓ Workflow paused for user approval")
        if result['stage'] == 'plan_created':
            print("  Approve the plan above to continue to implementation")
        elif result['stage'] == 'implementation_complete':
            print("  Approve the implementation to create PR")
    elif result['status'] == 'completed':
        # Interactive mode - completed
        print(f"\n✓ Workflow completed successfully!")
        print(f"  Log file: {result.get('log_file', 'N/A')}")
        print(f"  Next: {result.get('next_action', 'N/A')}")
    elif result['status'] == 'aborted':
        # User rejected at some checkpoint
        print(f"\n✗ Workflow aborted by user")
        orchestrator.save_workflow_log(result['workflow_log'])


if __name__ == "__main__":
    main()
