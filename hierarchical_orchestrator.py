#!/usr/bin/env python3
"""
Hierarchical Agent Orchestrator
3-Tier System: Claude (PM) → Qwen3 (Lead) → Qwen3-Coder (Member)

Now uses:
- LLM abstraction layer
- Centralized configuration
- Database persistence with resume capability
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from output_verifier import OutputVerifier
from core.llm import BaseLLM, OllamaAdapter, AnthropicAdapter
from core.config import get_config, AppConfig
from core.db import get_db, Task, WorkflowState, TaskStatus
from core.context_manager import ContextManager
from core.ide_bridge import IDEBridge

class HierarchicalOrchestrator:
    """
    Manages the 3-tier agent hierarchy:
    - Project Manager (Claude Code): Coordinates workflow
    - Project Lead (LLM): Makes decisions, reviews plans
    - Project Member (LLM): Implements code

    Now supports multiple LLM backends via abstraction layer.
    """

    def __init__(
        self,
        lead_llm: Optional[BaseLLM] = None,
        member_llm: Optional[BaseLLM] = None,
        config: Optional[AppConfig] = None,
        task_id: Optional[int] = None
    ):
        """
        Initialize hierarchical orchestrator with LLM adapters and database support.

        Args:
            lead_llm: LLM for Project Lead role (planning, review)
            member_llm: LLM for Project Member role (implementation)
            config: Application configuration (loads default if not provided)
            task_id: Optional task ID for resuming an existing task
        """
        # Load configuration
        self.config = config or get_config()

        # Initialize database
        self.db = get_db()
        if self.config.database.backup_on_start:
            self.db.backup_database()

        # Initialize LLMs for different roles
        self.lead_llm = lead_llm or self._create_default_lead_llm()
        self.member_llm = member_llm or self._create_default_member_llm()

        # Paths
        self.workspace = self.config.workspace.project_root
        self.logs_dir = self.config.workspace.logs_path
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Context Manager (Cline-like feature)
        self.context_manager = ContextManager(str(self.workspace))

        # Initialize IDE Bridge (Cline-like feature)
        self.ide_bridge = IDEBridge(str(self.workspace))

        # Current task tracking
        self.current_task_id = task_id

        print("✓ Hierarchical Orchestrator initialized")
        print(f"  Lead LLM: {self.lead_llm}")
        print(f"  Member LLM: {self.member_llm}")
        print(f"  Workspace: {self.workspace}")
        print(f"  Database: {self.db.db_path}")
        print(f"  Context Manager: Enabled (Smart Context)")
        print(f"  IDE Bridge: {'VS Code' if self.ide_bridge.vscode_available else 'Not Available'}")

        # Check for resumable tasks if no task_id provided
        if not task_id and self.config.orchestration.enable_resume:
            self._check_resumable_tasks()

    def _create_default_lead_llm(self) -> BaseLLM:
        """Create default LLM for Project Lead role."""
        if self.config.llm.provider == "ollama":
            return OllamaAdapter(
                model_name=self.config.orchestration.lead_model,
                base_url=self.config.llm.ollama_base_url,
                timeout=self.config.llm.ollama_timeout
            )
        else:
            return AnthropicAdapter(
                model_name=self.config.orchestration.lead_model,
                api_key=self.config.llm.anthropic_api_key
            )

    def _create_default_member_llm(self) -> BaseLLM:
        """Create default LLM for Project Member role."""
        if self.config.llm.provider == "ollama":
            return OllamaAdapter(
                model_name=self.config.orchestration.member_model,
                base_url=self.config.llm.ollama_base_url,
                timeout=self.config.llm.ollama_timeout
            )
        else:
            return AnthropicAdapter(
                model_name=self.config.orchestration.member_model,
                api_key=self.config.llm.anthropic_api_key
            )

    def _check_resumable_tasks(self):
        """Check for tasks that can be resumed."""
        resumable = self.db.get_resumable_tasks()
        if resumable:
            print(f"\n⚠ Found {len(resumable)} resumable task(s):")
            for task in resumable:
                print(f"  - Task #{task.id}: {task.request[:60]}...")
                print(f"    State: {task.workflow_state}")
                print(f"    Last updated: {task.updated_at}")

    def _save_checkpoint(
        self,
        task_id: int,
        checkpoint_name: str,
        data: Dict[str, Any]
    ):
        """
        Save a workflow checkpoint.

        Args:
            task_id: Task ID
            checkpoint_name: Checkpoint identifier
            data: Data to save
        """
        self.db.save_checkpoint(task_id, checkpoint_name, data)
        print(f"  💾 Checkpoint saved: {checkpoint_name}")

    def _update_workflow_state(
        self,
        task_id: int,
        workflow_state: WorkflowState,
        **updates
    ):
        """
        Update task workflow state and related fields.

        Args:
            task_id: Task ID
            workflow_state: New workflow state
            **updates: Additional fields to update
        """
        self.db.update_task(
            task_id,
            workflow_state=workflow_state.value,
            **updates
        )

    def call_qwen3_lead(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call Project Lead LLM for decision-making and planning.
        Now uses LLM abstraction layer.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.lead_llm.generate(
                messages=messages,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens
            )
            return response.content
        except Exception as e:
            return f"Error calling Lead LLM: {e}"

    def call_qwen3_coder(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Call Project Member LLM for implementation.
        Uses the CodingAgent with LLM abstraction and optional sandbox.
        """
        from agents.coding_agent import CodingAgent

        # Prepare sandbox config
        sandbox_config = {}
        if self.config.security.enable_sandbox:
            sandbox_config = {
                'image': self.config.security.docker_image,
                'timeout': self.config.security.max_execution_time,
                'network_disabled': False  # Can be made configurable
            }

        # Create coding agent with member LLM
        agent = CodingAgent(
            llm=self.member_llm,
            workspace_root=str(self.workspace),
            max_iterations=self.config.orchestration.max_iterations,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            use_sandbox=self.config.security.enable_sandbox,
            sandbox_config=sandbox_config
        )

        # Add system context if provided
        task_with_context = prompt
        if system_prompt:
            task_with_context = f"{system_prompt}\n\nTask: {prompt}"

        # Run the task
        result = agent.run_task(task_with_context)

        return result

    def autonomous_workflow(self, user_request: str, interactive: bool = False) -> Dict[str, Any]:
        """
        Fully autonomous workflow with database persistence and resume capability.

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

        All state is persisted to database with checkpoints for resume capability.
        """
        # Create task in database
        task_id = self.db.create_task(
            request=user_request,
            status=TaskStatus.IN_PROGRESS.value,
            workflow_state=WorkflowState.PLANNING.value
        )
        self.current_task_id = task_id

        workflow_log = {
            "task_id": task_id,
            "user_request": user_request,
            "timestamp": datetime.now().isoformat(),
            "stages": [],
            "interactive_mode": interactive
        }

        print(f"\n{'='*70}")
        print(f"AUTONOMOUS WORKFLOW STARTED (Task #{task_id})")
        print(f"{'='*70}")
        print(f"User Request: {user_request}\n")

        # Save initial checkpoint
        self._save_checkpoint(task_id, "workflow_start", {
            "user_request": user_request,
            "interactive": interactive
        })

        # STAGE 1: Qwen3 creates plan
        print("STAGE 1: Qwen3 (Project Lead) Creating Implementation Plan...")
        print("-" * 70)

        # Generate project context using ContextManager (Cline-like feature)
        print("  Analyzing project structure...")
        project_context = self.context_manager.get_context_for_task(user_request, max_tokens=4000)

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

        system_prompt = f"""You are an experienced Project Lead (Technical Architect) responsible for:
- Analyzing requirements
- Creating detailed implementation plans
- Reviewing code from junior developers
- Making technical decisions
- Ensuring quality standards

You work with:
- Project Manager (Claude Code): Coordinates workflow, runs tests
- Junior Developer (Qwen3-Coder): Implements your plans

Be thorough but concise. Focus on actionable guidance.

{project_context}"""

        plan = self.call_qwen3_lead(planning_prompt, system_prompt)

        workflow_log["stages"].append({
            "stage": "planning",
            "agent": "qwen3_lead",
            "output": plan
        })

        # Save plan to database
        self._update_workflow_state(
            task_id,
            WorkflowState.PLAN_AWAITING_APPROVAL,
            plan=plan,
            workflow_log=json.dumps(workflow_log)
        )
        self._save_checkpoint(task_id, "after_planning", {
            "plan": plan,
            "workflow_log": workflow_log
        })

        print(f"\n{plan}\n")
        print("-" * 70)

        # CHECKPOINT 1: Plan approval
        if not interactive:
            # Programmatic mode - return to caller
            return {
                "status": "awaiting_user_approval",
                "stage": "plan_created",
                "task_id": task_id,
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
                # Record approval in database
                self._update_workflow_state(
                    task_id,
                    WorkflowState.PLAN_APPROVED,
                    plan_approved_at=datetime.now(),
                    plan_approved_by="user_interactive"
                )
                break
            elif approval in ['no', 'n']:
                print("✗ Plan rejected. Workflow aborted.")
                # Record rejection in database
                self._update_workflow_state(
                    task_id,
                    WorkflowState.PLAN_REJECTED,
                    status=TaskStatus.CANCELLED.value,
                    plan_rejection_reason="User rejected plan in interactive mode"
                )
                return {
                    "status": "aborted",
                    "stage": "plan_rejected",
                    "task_id": task_id,
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
        task_id = workflow_log.get("task_id", self.current_task_id)

        print(f"\n{'='*70}")
        print(f"CONTINUING WORKFLOW - Plan Approved (Task #{task_id})")
        print(f"{'='*70}\n")

        # Update workflow state
        self._update_workflow_state(
            task_id,
            WorkflowState.IMPLEMENTING
        )
        self._save_checkpoint(task_id, "start_implementation", {
            "plan": plan
        })

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

        # Save implementation to database
        self._update_workflow_state(
            task_id,
            WorkflowState.REVIEWING,
            implementation=json.dumps(implementation_result),
            workflow_log=json.dumps(workflow_log)
        )
        self._save_checkpoint(task_id, "after_implementation", {
            "implementation": implementation_result,
            "workflow_log": workflow_log
        })

        print(f"\nImplementation Result: {json.dumps(implementation_result, indent=2, default=str)}\n")
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

        # Save review to database
        self._update_workflow_state(
            task_id,
            WorkflowState.VERIFYING,
            review=review,
            workflow_log=json.dumps(workflow_log)
        )
        self._save_checkpoint(task_id, "after_review", {
            "review": review,
            "workflow_log": workflow_log
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

            # Save verification results to database
            self._update_workflow_state(
                task_id,
                WorkflowState.IMPLEMENTATION_AWAITING_APPROVAL,
                verification_result=json.dumps(verification_result),
                workflow_log=json.dumps(workflow_log)
            )

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

            # Save error to database
            self._update_workflow_state(
                task_id,
                WorkflowState.IMPLEMENTATION_AWAITING_APPROVAL,
                verification_result=json.dumps(verification_result),
                workflow_log=json.dumps(workflow_log),
                error_details=str(e)
            )

        # Save checkpoint before final approval
        self._save_checkpoint(task_id, "after_verification", {
            "verification": verification_result,
            "workflow_log": workflow_log
        })

        print("-" * 70)

        # VS Code Integration: Offer to view diffs (Phase 3 feature)
        if interactive and self.ide_bridge.vscode_available:
            self._offer_vscode_diff_review(implementation_result)

        # CHECKPOINT 2: Final approval
        if not interactive:
            # Programmatic mode - return to caller
            return {
                "status": "awaiting_user_approval",
                "stage": "implementation_complete",
                "task_id": task_id,
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

                # Update database - mark as completed
                self._update_workflow_state(
                    task_id,
                    WorkflowState.COMPLETED,
                    status=TaskStatus.COMPLETED.value,
                    implementation_approved_at=datetime.now(),
                    implementation_approved_by="user_interactive",
                    workflow_log=json.dumps(workflow_log)
                )

                # Save workflow log
                log_file = self.save_workflow_log(workflow_log)

                return {
                    "status": "completed",
                    "stage": "approved",
                    "task_id": task_id,
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

                # Update database - mark as rejected
                self._update_workflow_state(
                    task_id,
                    WorkflowState.IMPLEMENTATION_REJECTED,
                    status=TaskStatus.CANCELLED.value,
                    implementation_rejection_reason="User rejected implementation in interactive mode",
                    workflow_log=json.dumps(workflow_log)
                )

                self.save_workflow_log(workflow_log)
                return {
                    "status": "aborted",
                    "stage": "implementation_rejected",
                    "task_id": task_id,
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

    def continue_after_plan_approval(
        self,
        workflow_log: Dict,
        plan: str,
        approved_by: str = "user_programmatic"
    ) -> Dict[str, Any]:
        """
        Continue workflow after plan has been approved externally.

        This method is for programmatic callers (like Claude Code) who handle
        approval themselves. For interactive mode, use autonomous_workflow(interactive=True).

        Args:
            workflow_log: Workflow log from previous stage
            plan: Approved plan
            approved_by: Identifier of who approved the plan

        Returns:
            Workflow result
        """
        task_id = workflow_log.get("task_id", self.current_task_id)

        # Record plan approval in database
        if task_id:
            self._update_workflow_state(
                task_id,
                WorkflowState.PLAN_APPROVED,
                plan_approved_at=datetime.now(),
                plan_approved_by=approved_by
            )

        return self._continue_workflow(workflow_log, plan, interactive=False)

    def resume_task(self, task_id: int) -> Dict[str, Any]:
        """
        Resume an interrupted task from its last checkpoint.

        Args:
            task_id: Task ID to resume

        Returns:
            Workflow result
        """
        print(f"\n{'='*70}")
        print(f"RESUMING TASK #{task_id}")
        print(f"{'='*70}\n")

        # Load task from database
        task = self.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task #{task_id} not found")

        # Check if task is resumable
        if task.workflow_state == WorkflowState.COMPLETED.value:
            print(f"⚠ Task #{task_id} is already completed")
            return {
                "status": "already_completed",
                "task_id": task_id,
                "workflow_state": task.workflow_state
            }

        if task.workflow_state == WorkflowState.FAILED.value:
            print(f"⚠ Task #{task_id} has failed")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": task.error_details
            }

        # Load latest checkpoint
        checkpoint = self.db.get_latest_checkpoint(task_id)
        if not checkpoint:
            print(f"⚠ No checkpoint found for task #{task_id}, starting from beginning")
            return self.autonomous_workflow(task.request, interactive=False)

        print(f"  Last checkpoint: {checkpoint['checkpoint']}")
        print(f"  Workflow state: {task.workflow_state}\n")

        # Parse workflow log
        try:
            workflow_log = json.loads(task.workflow_log) if task.workflow_log else {}
        except json.JSONDecodeError:
            workflow_log = {}

        workflow_log["task_id"] = task_id
        workflow_log["resumed_at"] = datetime.now().isoformat()
        workflow_log["resumed_from"] = checkpoint['checkpoint']

        self.current_task_id = task_id

        # Resume based on workflow state
        if task.workflow_state == WorkflowState.PLAN_AWAITING_APPROVAL.value:
            print("  Resuming at: Plan awaiting approval")
            return {
                "status": "awaiting_user_approval",
                "stage": "plan_created",
                "task_id": task_id,
                "plan": task.plan,
                "workflow_log": workflow_log,
                "next_action": "User must approve this plan to proceed"
            }

        elif task.workflow_state == WorkflowState.PLAN_APPROVED.value:
            print("  Resuming at: Plan approved, starting implementation")
            return self._continue_workflow(workflow_log, task.plan, interactive=False)

        elif task.workflow_state == WorkflowState.IMPLEMENTATION_AWAITING_APPROVAL.value:
            print("  Resuming at: Implementation awaiting approval")
            try:
                implementation = json.loads(task.implementation) if task.implementation else {}
                verification = json.loads(task.verification_result) if task.verification_result else {}
            except json.JSONDecodeError:
                implementation = task.implementation
                verification = task.verification_result

            return {
                "status": "awaiting_user_approval",
                "stage": "implementation_complete",
                "task_id": task_id,
                "plan": task.plan,
                "implementation": implementation,
                "review": task.review,
                "verification": verification,
                "workflow_log": workflow_log,
                "next_action": "User must review and approve to create PR"
            }

        else:
            print(f"  ⚠ Unknown workflow state: {task.workflow_state}")
            print("  Starting from scratch")
            return self.autonomous_workflow(task.request, interactive=False)

    def _offer_vscode_diff_review(self, implementation_result: Dict):
        """
        Offer to view diffs in VS Code (Phase 3 feature).

        Args:
            implementation_result: Result from the implementation stage
        """
        print("\n" + "="*70)
        print("VS CODE DIFF REVIEW AVAILABLE")
        print("="*70)
        print("\n💡 You can view the code changes in VS Code before final approval.")

        while True:
            response = input("\nOpen diffs in VS Code? (y/n): ").strip().lower()

            if response in ['y', 'yes']:
                # Try to find changed files from implementation_result
                # This depends on what the implementation agent returns
                # For now, we'll check the sandbox directory for temp files
                from core.diff_engine import DiffEngine

                diff_engine = DiffEngine(str(self.workspace))

                # Look for temp files in sandbox
                temp_files = list(Path(self.workspace / "sandbox").glob("temp_*.py"))

                if not temp_files:
                    print("\n⚠️  No pending changes found to review.")
                    break

                print(f"\nFound {len(temp_files)} file(s) with changes:")

                # Open each diff in VS Code
                opened_count = 0
                for temp_file in temp_files:
                    # Extract original filename from temp filename
                    # temp_YYYYMMDD_HHMMSS_originalname.py -> originalname.py
                    parts = temp_file.name.split('_')
                    if len(parts) >= 4:
                        original_name = '_'.join(parts[3:])  # Reconstruct original name
                        original_path = self.workspace / original_name

                        # Check if original exists, if not, use temp as "new file"
                        if original_path.exists():
                            success, msg = self.ide_bridge.open_diff_in_vscode(
                                str(original_path),
                                str(temp_file)
                            )
                        else:
                            # New file - compare with empty
                            success, msg = self.ide_bridge.open_diff_in_vscode(
                                str(temp_file),  # Show as new
                                str(temp_file)
                            )

                        print(f"  {msg}")
                        if success:
                            opened_count += 1

                if opened_count > 0:
                    print(f"\n✓ Opened {opened_count} diff(s) in VS Code")
                else:
                    print("\n⚠️  No diffs could be opened")

                break

            elif response in ['n', 'no']:
                print("\n Skipping VS Code diff review.")
                break
            else:
                print("Please enter 'y' or 'n'")

    def save_workflow_log(self, workflow_log: Dict):
        """Save workflow log for audit trail."""
        log_file = self.logs_dir / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump(workflow_log, f, indent=2)
        print(f"\n✓ Workflow log saved: {log_file}")
        return log_file


def main():
    """Test the hierarchical orchestrator with new architecture."""
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

  # Use custom config file
  python3 hierarchical_orchestrator.py --config config/custom.yaml "Your task here"
        """
    )
    parser.add_argument(
        'request',
        type=str,
        nargs='?',  # Make optional
        help='User request for the coding task'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode (ask user for approvals directly)'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (YAML)'
    )
    parser.add_argument(
        '--provider',
        choices=['ollama', 'anthropic'],
        help='Override LLM provider from config'
    )
    parser.add_argument(
        '--resume',
        type=int,
        metavar='TASK_ID',
        help='Resume an interrupted task by ID'
    )
    parser.add_argument(
        '--list-resumable',
        action='store_true',
        help='List all resumable tasks and exit'
    )

    args = parser.parse_args()

    # Load configuration
    config = None
    if args.config:
        from pathlib import Path
        config = get_config(config_path=Path(args.config))
    else:
        config = get_config()

    # Override provider if specified
    if args.provider:
        config.llm.provider = args.provider

    # Create orchestrator with config
    orchestrator = HierarchicalOrchestrator(config=config)

    # Handle --list-resumable
    if args.list_resumable:
        db = get_db()
        resumable = db.get_resumable_tasks()
        if not resumable:
            print("No resumable tasks found.")
            return
        print(f"\nFound {len(resumable)} resumable task(s):\n")
        for task in resumable:
            print(f"Task #{task.id}:")
            print(f"  Request: {task.request[:80]}...")
            print(f"  State: {task.workflow_state}")
            print(f"  Status: {task.status}")
            print(f"  Last updated: {task.updated_at}")
            print()
        print("Use --resume TASK_ID to continue a task\n")
        return

    # Handle --resume
    if args.resume:
        try:
            result = orchestrator.resume_task(args.resume)
        except Exception as e:
            print(f"\n✗ Error resuming task: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        # Start new workflow
        if not args.request:
            parser.error("request is required when not using --resume or --list-resumable")
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
