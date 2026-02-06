#!/usr/bin/env python3
"""
Enhanced Web Interface for Hierarchical Coding Agent
Mobile-friendly task submission, approval workflows, and real-time progress tracking
"""
import os
import base64
import secrets
import sqlite3
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from hierarchical_orchestrator import HierarchicalOrchestrator

# Configuration
DB_PATH = Path("/home/korety/coding-agent/tasks.db")
USERNAME = os.getenv("WEB_USERNAME", "admin")
PASSWORD = os.getenv("WEB_PASSWORD", secrets.token_urlsafe(16))

# Print credentials on startup
print("="*60)
print("WEB INTERFACE CREDENTIALS")
print("="*60)
print(f"Username: {USERNAME}")
print(f"Password: {PASSWORD}")
print("\nSet custom credentials with:")
print("export WEB_USERNAME=your_username")
print("export WEB_PASSWORD=your_password")
print("="*60)

app = FastAPI(title="Coding Agent Interface")
security = HTTPBasic()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://your-domain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workflow State Management
@dataclass
class WorkflowCheckpoint:
    """Represents a workflow checkpoint awaiting approval."""
    task_id: int
    checkpoint_type: str  # 'plan' or 'implementation'
    workflow_log: Dict[str, Any]
    plan: Optional[str] = None
    implementation: Optional[Dict] = None
    review: Optional[str] = None
    verification: Optional[Dict] = None

class WorkflowManager:
    """Manages workflow state and resumption."""

    def __init__(self):
        self.active_workflows: Dict[int, asyncio.Task] = {}
        self.approval_queue: Dict[int, WorkflowCheckpoint] = {}
        self.progress_subscribers: Dict[int, list] = {}  # task_id -> [websockets]

    async def start_workflow(self, task_id: int, request: str, orchestrator: HierarchicalOrchestrator):
        """Start a new workflow in background."""
        task = asyncio.create_task(self._run_workflow(task_id, request, orchestrator))
        self.active_workflows[task_id] = task
        return task

    async def _run_workflow(self, task_id: int, request: str, orchestrator: HierarchicalOrchestrator):
        """Execute workflow with checkpoint handling."""
        try:
            await self._broadcast_progress(task_id, "task_started", {"request": request})

            # Update status
            update_task(task_id, "planning")
            await self._broadcast_progress(task_id, "stage_started", {"stage": "planning"})

            # STAGE 1: Create plan (synchronous call in thread pool)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.autonomous_workflow(request, interactive=False)
            )

            if result.get('status') == 'awaiting_user_approval' and result.get('stage') == 'plan_created':
                # Save checkpoint
                checkpoint = WorkflowCheckpoint(
                    task_id=task_id,
                    checkpoint_type='plan',
                    workflow_log=result.get('workflow_log', {}),
                    plan=result.get('plan', '')
                )
                self.approval_queue[task_id] = checkpoint

                # Update database
                update_task(
                    task_id,
                    "plan_awaiting_approval",
                    plan=result.get('plan', ''),
                    workflow_checkpoint_data=json.dumps({
                        'workflow_log': result.get('workflow_log', {}),
                        'stage': 'plan_created'
                    })
                )

                await self._broadcast_progress(task_id, "awaiting_approval", {
                    "checkpoint": "plan",
                    "plan": result.get('plan', '')
                })

        except Exception as e:
            update_task(task_id, "failed", error_details=str(e))
            await self._broadcast_progress(task_id, "task_error", {"error": str(e)})

    async def resume_after_plan_approval(self, task_id: int, orchestrator: HierarchicalOrchestrator):
        """Resume workflow after plan approval."""
        checkpoint = self.approval_queue.get(task_id)
        if not checkpoint:
            raise ValueError(f"No checkpoint found for task {task_id}")

        try:
            update_task(task_id, "implementing")
            await self._broadcast_progress(task_id, "stage_started", {"stage": "implementing"})

            # Continue workflow (synchronous call in thread pool)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.continue_after_plan_approval(
                    checkpoint.workflow_log,
                    checkpoint.plan
                )
            )

            if result.get('status') == 'awaiting_user_approval' and result.get('stage') == 'implementation_complete':
                # Implementation checkpoint
                new_checkpoint = WorkflowCheckpoint(
                    task_id=task_id,
                    checkpoint_type='implementation',
                    workflow_log=result.get('workflow_log', {}),
                    plan=checkpoint.plan,
                    implementation=result.get('implementation', {}),
                    review=result.get('review', ''),
                    verification=result.get('verification', {})
                )
                self.approval_queue[task_id] = new_checkpoint

                update_task(
                    task_id,
                    "implementation_awaiting_approval",
                    implementation=json.dumps(result.get('implementation', {})),
                    review=result.get('review', ''),
                    verification_result=json.dumps(result.get('verification', {})),
                    workflow_checkpoint_data=json.dumps({
                        'workflow_log': result.get('workflow_log', {}),
                        'stage': 'implementation_complete'
                    })
                )

                await self._broadcast_progress(task_id, "awaiting_approval", {
                    "checkpoint": "implementation",
                    "implementation": result.get('implementation', {}),
                    "review": result.get('review', ''),
                    "verification": result.get('verification', {})
                })
            elif result.get('status') == 'completed':
                # Workflow completed directly
                await self.complete_workflow(task_id)

        except Exception as e:
            update_task(task_id, "failed", error_details=str(e))
            await self._broadcast_progress(task_id, "task_error", {"error": str(e)})

    async def complete_workflow(self, task_id: int):
        """Mark workflow as completed."""
        self.approval_queue.pop(task_id, None)
        self.active_workflows.pop(task_id, None)
        update_task(task_id, "completed")
        await self._broadcast_progress(task_id, "task_complete", {"status": "completed"})

    async def _broadcast_progress(self, task_id: int, event_type: str, data: Dict):
        """Broadcast progress to all WebSocket subscribers."""
        if task_id in self.progress_subscribers:
            message = json.dumps({
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            })

            # Send to all connected websockets for this task
            for websocket in self.progress_subscribers[task_id][:]:
                try:
                    await websocket.send_text(message)
                except:
                    # Remove disconnected websockets
                    self.progress_subscribers[task_id].remove(websocket)

    def subscribe(self, task_id: int, websocket):
        """Subscribe a websocket to task progress."""
        if task_id not in self.progress_subscribers:
            self.progress_subscribers[task_id] = []
        self.progress_subscribers[task_id].append(websocket)

    def unsubscribe(self, task_id: int, websocket):
        """Unsubscribe a websocket from task progress."""
        if task_id in self.progress_subscribers:
            try:
                self.progress_subscribers[task_id].remove(websocket)
            except ValueError:
                pass

    def restore_checkpoint(self, task_id: int) -> Optional[WorkflowCheckpoint]:
        """Restore checkpoint from DB if not in memory (e.g. after server restart)."""
        if task_id in self.approval_queue:
            return self.approval_queue[task_id]

        task = get_task_from_db(task_id)
        if not task or not task.get('workflow_checkpoint_data'):
            return None

        try:
            checkpoint_data = json.loads(task['workflow_checkpoint_data'])
            is_implementation = task['status'] == 'implementation_awaiting_approval'

            checkpoint = WorkflowCheckpoint(
                task_id=task_id,
                checkpoint_type='implementation' if is_implementation else 'plan',
                workflow_log=checkpoint_data.get('workflow_log', {}),
                plan=task.get('plan', ''),
                implementation=json.loads(task.get('implementation') or '{}') if is_implementation else None,
                review=task.get('review') if is_implementation else None,
                verification=json.loads(task.get('verification_result') or '{}') if is_implementation else None
            )

            self.approval_queue[task_id] = checkpoint
            return checkpoint
        except Exception:
            return None

# Global workflow manager
workflow_manager = WorkflowManager()

# Database initialization with enhanced schema
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Enhanced schema with approval tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Workflow data (existing)
            plan TEXT,
            implementation TEXT,
            review TEXT,
            workflow_log TEXT,

            -- NEW: Approval tracking
            plan_approved_at TIMESTAMP,
            plan_approved_by TEXT,
            plan_rejection_reason TEXT,
            implementation_approved_at TIMESTAMP,
            implementation_approved_by TEXT,
            implementation_rejection_reason TEXT,

            -- NEW: Workflow state management
            workflow_state TEXT DEFAULT 'pending',
            workflow_checkpoint_data TEXT,

            -- NEW: Enhanced metadata
            verification_result TEXT,
            error_details TEXT,
            retry_count INTEGER DEFAULT 0
        )
    ''')

    # Migrate existing tables
    c.execute("PRAGMA table_info(tasks)")
    existing_columns = [row[1] for row in c.fetchall()]

    new_columns = [
        ("plan_approved_at", "TIMESTAMP"),
        ("plan_approved_by", "TEXT"),
        ("plan_rejection_reason", "TEXT"),
        ("implementation_approved_at", "TIMESTAMP"),
        ("implementation_approved_by", "TEXT"),
        ("implementation_rejection_reason", "TEXT"),
        ("workflow_state", "TEXT DEFAULT 'pending'"),
        ("workflow_checkpoint_data", "TEXT"),
        ("verification_result", "TEXT"),
        ("error_details", "TEXT"),
        ("retry_count", "INTEGER DEFAULT 0")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            c.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

init_db()

# Authentication
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Helper functions
def get_task_from_db(task_id: int) -> Optional[Dict]:
    """Helper to fetch task from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    columns = ['id', 'request', 'status', 'created_at', 'updated_at', 'plan',
               'implementation', 'review', 'workflow_log', 'plan_approved_at',
               'plan_approved_by', 'plan_rejection_reason', 'implementation_approved_at',
               'implementation_approved_by', 'implementation_rejection_reason',
               'workflow_state', 'workflow_checkpoint_data', 'verification_result',
               'error_details', 'retry_count']

    return dict(zip(columns[:len(row)], row))

def update_task(task_id: int, status: str, **kwargs):
    """Update task in database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    updates = {"status": status, "updated_at": datetime.now().isoformat()}
    updates.update(kwargs)

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [task_id]

    c.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

# Pydantic models for API
class TaskRequest(BaseModel):
    request: str

class PlanApprovalRequest(BaseModel):
    approved_by: str

class PlanRejectionRequest(BaseModel):
    approved_by: str
    reason: str

class PlanEditRequest(BaseModel):
    approved_by: str
    feedback: str

class ImplementationApprovalRequest(BaseModel):
    approved_by: str

class ImplementationRejectionRequest(BaseModel):
    approved_by: str
    reason: str

# Main Routes
@app.get("/", response_class=HTMLResponse)
def home(username: str = Depends(verify_credentials)):
    """Main page with mobile-responsive UI and modals"""
    auth_token = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Coding Agent Interface</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}

            .header {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #667eea;
                font-size: 24px;
                margin-bottom: 8px;
            }}

            .user-info {{
                color: #666;
                font-size: 14px;
            }}

            .card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}

            h2 {{
                color: #333;
                font-size: 18px;
                margin-bottom: 16px;
            }}

            textarea {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                font-family: inherit;
                resize: vertical;
                min-height: 100px;
                margin-bottom: 12px;
            }}

            textarea:focus {{
                outline: none;
                border-color: #667eea;
            }}

            button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 14px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                transition: background 0.3s;
            }}

            button:hover {{
                background: #5568d3;
            }}

            button:active {{
                transform: scale(0.98);
            }}

            .task-list {{
                list-style: none;
            }}

            .task-item {{
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 12px;
                border-left: 4px solid #667eea;
                cursor: pointer;
                transition: transform 0.2s;
            }}

            .task-item:hover {{
                transform: translateX(4px);
            }}

            .task-item.pending {{
                border-left-color: #fbbf24;
            }}

            .task-item.planning {{
                border-left-color: #3b82f6;
            }}

            .task-item.plan_awaiting_approval {{
                border-left-color: #f59e0b;
                animation: pulse 2s infinite;
            }}

            .task-item.implementing {{
                border-left-color: #3b82f6;
            }}

            .task-item.implementation_awaiting_approval {{
                border-left-color: #f59e0b;
                animation: pulse 2s infinite;
            }}

            .task-item.completed {{
                border-left-color: #10b981;
            }}

            .task-item.failed {{
                border-left-color: #ef4444;
            }}

            .task-item.plan_rejected {{
                border-left-color: #ef4444;
            }}

            .task-item.implementation_rejected {{
                border-left-color: #ef4444;
            }}

            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}

            .task-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }}

            .task-id {{
                font-size: 12px;
                color: #666;
            }}

            .task-status {{
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
                border-radius: 12px;
                text-transform: uppercase;
            }}

            .task-status.pending {{
                background: #fef3c7;
                color: #92400e;
            }}

            .task-status.planning {{
                background: #dbeafe;
                color: #1e40af;
            }}

            .task-status.plan_awaiting_approval {{
                background: #fed7aa;
                color: #92400e;
            }}

            .task-status.implementing {{
                background: #dbeafe;
                color: #1e40af;
            }}

            .task-status.implementation_awaiting_approval {{
                background: #fed7aa;
                color: #92400e;
            }}

            .task-status.completed {{
                background: #d1fae5;
                color: #065f46;
            }}

            .task-status.failed {{
                background: #fee2e2;
                color: #991b1b;
            }}

            .task-status.plan_rejected {{
                background: #fee2e2;
                color: #991b1b;
            }}

            .task-status.implementation_rejected {{
                background: #fee2e2;
                color: #991b1b;
            }}

            .task-request {{
                color: #333;
                font-size: 14px;
                margin-bottom: 4px;
            }}

            .task-time {{
                color: #999;
                font-size: 12px;
            }}

            .loading {{
                text-align: center;
                color: #666;
                padding: 20px;
            }}

            .empty-state {{
                text-align: center;
                color: #999;
                padding: 40px 20px;
            }}

            /* Modal styles */
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                backdrop-filter: blur(4px);
            }}

            .modal.active {{
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s;
            }}

            .modal-content {{
                background: white;
                border-radius: 16px;
                padding: 24px;
                max-width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                animation: slideUp 0.3s;
            }}

            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 12px;
            }}

            .modal-title {{
                font-size: 20px;
                font-weight: 600;
                color: #333;
            }}

            .close-button {{
                background: none;
                border: none;
                font-size: 28px;
                color: #999;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                line-height: 1;
            }}

            .close-button:hover {{
                color: #333;
            }}

            .modal-body {{
                margin-bottom: 20px;
            }}

            .modal-body h4 {{
                color: #333;
                font-size: 16px;
                margin-top: 16px;
                margin-bottom: 8px;
            }}

            .plan-content {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                max-height: 400px;
                overflow-y: auto;
            }}

            .modal-actions {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }}

            .btn {{
                flex: 1;
                min-width: 120px;
                padding: 14px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }}

            .btn-primary {{
                background: #10b981;
                color: white;
            }}

            .btn-primary:hover {{
                background: #059669;
            }}

            .btn-danger {{
                background: #ef4444;
                color: white;
            }}

            .btn-danger:hover {{
                background: #dc2626;
            }}

            .btn-secondary {{
                background: #6b7280;
                color: white;
            }}

            .btn-secondary:hover {{
                background: #4b5563;
            }}

            .edit-feedback {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                resize: vertical;
                min-height: 80px;
                margin-bottom: 12px;
            }}

            /* Progress indicator */
            .progress-container {{
                margin-top: 12px;
                padding: 12px;
                background: #f0f9ff;
                border-radius: 8px;
                border-left: 4px solid #3b82f6;
            }}

            .progress-status {{
                font-size: 14px;
                color: #1e40af;
                font-weight: 600;
                margin-bottom: 4px;
            }}

            .progress-message {{
                font-size: 12px;
                color: #64748b;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}

            @keyframes slideUp {{
                from {{
                    opacity: 0;
                    transform: translateY(20px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}

            @media (max-width: 600px) {{
                body {{
                    padding: 12px;
                }}

                .header, .card {{
                    padding: 16px;
                }}

                h1 {{
                    font-size: 20px;
                }}

                h2 {{
                    font-size: 16px;
                }}

                .btn {{
                    min-width: 100%;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Coding Agent</h1>
                <div class="user-info">Logged in as: {username}</div>
            </div>

            <div class="card">
                <h2>Submit New Task</h2>
                <form id="taskForm">
                    <textarea
                        id="taskRequest"
                        placeholder="Describe your coding task...&#10;&#10;Example: Add error handling to the search function"
                        required
                    ></textarea>
                    <button type="submit">Submit Task</button>
                </form>
            </div>

            <div class="card">
                <h2>Recent Tasks</h2>
                <div id="taskList" class="loading">Loading tasks...</div>
            </div>
        </div>

        <!-- Plan Approval Modal -->
        <div id="planModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">📋 Review Plan</h3>
                    <button class="close-button" onclick="closePlanModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="plan-content" id="planContent"></div>
                    <div id="editSection" style="display: none;">
                        <textarea id="editFeedback" class="edit-feedback"
                                  placeholder="Describe what changes you'd like to the plan..."></textarea>
                    </div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="approvePlan()" id="approveBtn">
                        ✓ Approve
                    </button>
                    <button class="btn btn-secondary" onclick="toggleEditSection()" id="editBtn">
                        ✎ Request Changes
                    </button>
                    <button class="btn btn-danger" onclick="rejectPlan()">
                        ✗ Reject
                    </button>
                </div>
            </div>
        </div>

        <!-- Implementation Approval Modal -->
        <div id="implementationModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">🔍 Review Implementation</h3>
                    <button class="close-button" onclick="closeImplementationModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <h4>📝 Original Plan:</h4>
                    <div class="plan-content" id="implPlanContent"></div>

                    <h4>💻 Implementation Result:</h4>
                    <div class="plan-content" id="implResultContent"></div>

                    <h4>👀 Lead Review:</h4>
                    <div class="plan-content" id="reviewContent"></div>

                    <h4>✅ Verification:</h4>
                    <div class="plan-content" id="verificationContent"></div>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="approveImplementation()">
                        ✓ Approve & Complete
                    </button>
                    <button class="btn btn-secondary" onclick="retryImplementation()">
                        🔄 Retry
                    </button>
                    <button class="btn btn-danger" onclick="rejectImplementation()">
                        ✗ Reject
                    </button>
                </div>
            </div>
        </div>

        <!-- Progress Modal -->
        <div id="progressModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">⚙️ Workflow Progress</h3>
                    <button class="close-button" onclick="closeProgressModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="progress-container">
                        <div class="progress-status" id="progressStatus">Starting...</div>
                        <div class="progress-message" id="progressMessage"></div>
                    </div>
                    <div id="progressLog" style="margin-top: 16px; max-height: 300px; overflow-y: auto;"></div>
                </div>
            </div>
        </div>

        <script>
            const AUTH_TOKEN = "{auth_token}";
            function authHeaders(withBody = true) {{
                const h = {{'Authorization': 'Basic ' + AUTH_TOKEN}};
                if (withBody) h['Content-Type'] = 'application/json';
                return h;
            }}

            let currentTaskId = null;
            let currentWebSocket = null;

            // WebSocket connection
            function connectWebSocket(taskId) {{
                if (currentWebSocket) {{
                    currentWebSocket.close();
                }}

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${{protocol}}//${{window.location.host}}/ws/tasks/${{taskId}}`;

                currentWebSocket = new WebSocket(wsUrl);

                currentWebSocket.onopen = () => {{
                    console.log('WebSocket connected for task', taskId);
                }};

                currentWebSocket.onmessage = (event) => {{
                    const message = JSON.parse(event.data);
                    handleProgressUpdate(taskId, message);
                }};

                currentWebSocket.onerror = (error) => {{
                    console.error('WebSocket error:', error);
                }};

                currentWebSocket.onclose = () => {{
                    console.log('WebSocket closed for task', taskId);
                }};
            }}

            function handleProgressUpdate(taskId, message) {{
                const {{ event, data }} = message;

                switch (event) {{
                    case 'task_started':
                        showProgressModal(taskId);
                        updateProgress('Starting workflow...', data.request);
                        break;

                    case 'stage_started':
                        updateProgress(`Stage: ${{data.stage}}`, `Starting ${{data.stage}}...`);
                        break;

                    case 'awaiting_approval':
                        if (data.checkpoint === 'plan') {{
                            showPlanModal(taskId, data.plan);
                            closeProgressModal();
                        }} else if (data.checkpoint === 'implementation') {{
                            showImplementationModal(taskId, data);
                            closeProgressModal();
                        }}
                        break;

                    case 'plan_revised':
                        updatePlanModal(data.plan);
                        break;

                    case 'task_complete':
                        updateProgress('Completed!', 'Workflow finished successfully');
                        setTimeout(() => {{
                            closeProgressModal();
                            loadTasks();
                        }}, 2000);
                        break;

                    case 'task_error':
                        updateProgress('Error', data.error);
                        break;
                }}
            }}

            // Plan Modal Functions
            function showPlanModal(taskId, plan) {{
                currentTaskId = taskId;
                document.getElementById('planContent').textContent = plan;
                document.getElementById('planModal').classList.add('active');
                document.getElementById('editSection').style.display = 'none';
            }}

            function closePlanModal() {{
                document.getElementById('planModal').classList.remove('active');
                document.getElementById('editFeedback').value = '';
            }}

            function toggleEditSection() {{
                const editSection = document.getElementById('editSection');
                const editBtn = document.getElementById('editBtn');
                const approveBtn = document.getElementById('approveBtn');

                if (editSection.style.display === 'none') {{
                    editSection.style.display = 'block';
                    editBtn.textContent = '📤 Submit Changes';
                    approveBtn.style.display = 'none';
                }} else {{
                    const feedback = document.getElementById('editFeedback').value.trim();
                    if (feedback) {{
                        requestPlanEdit(feedback);
                    }} else {{
                        alert('Please enter feedback for changes');
                    }}
                }}
            }}

            async function approvePlan() {{
                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/plan/approve`, {{
                        method: 'PUT',
                        headers: authHeaders(),
                        body: JSON.stringify({{ approved_by: 'web_user' }})
                    }});

                    if (response.ok) {{
                        closePlanModal();
                        showProgressModal(currentTaskId);
                        updateProgress('Plan approved', 'Continuing to implementation...');
                    }} else {{
                        alert('Failed to approve plan');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            async function rejectPlan() {{
                const reason = prompt('Reason for rejection (optional):');

                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/plan/reject`, {{
                        method: 'PUT',
                        headers: authHeaders(),
                        body: JSON.stringify({{
                            approved_by: 'web_user',
                            reason: reason || 'No reason provided'
                        }})
                    }});

                    if (response.ok) {{
                        closePlanModal();
                        loadTasks();
                    }} else {{
                        alert('Failed to reject plan');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            async function requestPlanEdit(feedback) {{
                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/plan/edit`, {{
                        method: 'PUT',
                        headers: authHeaders(),
                        body: JSON.stringify({{
                            approved_by: 'web_user',
                            feedback: feedback
                        }})
                    }});

                    if (response.ok) {{
                        const result = await response.json();
                        updatePlanModal(result.plan);
                        document.getElementById('editSection').style.display = 'none';
                        document.getElementById('editBtn').textContent = '✎ Request Changes';
                        document.getElementById('approveBtn').style.display = 'block';
                        document.getElementById('editFeedback').value = '';
                    }} else {{
                        alert('Failed to revise plan');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            function updatePlanModal(plan) {{
                document.getElementById('planContent').textContent = plan;
            }}

            // Implementation Modal Functions
            function showImplementationModal(taskId, data) {{
                currentTaskId = taskId;
                document.getElementById('implPlanContent').textContent = data.plan || 'N/A';
                document.getElementById('implResultContent').textContent =
                    JSON.stringify(data.implementation, null, 2);
                document.getElementById('reviewContent').textContent = data.review || 'N/A';
                document.getElementById('verificationContent').textContent =
                    JSON.stringify(data.verification, null, 2);
                document.getElementById('implementationModal').classList.add('active');
            }}

            function closeImplementationModal() {{
                document.getElementById('implementationModal').classList.remove('active');
            }}

            async function approveImplementation() {{
                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/implementation/approve`, {{
                        method: 'PUT',
                        headers: authHeaders(),
                        body: JSON.stringify({{ approved_by: 'web_user' }})
                    }});

                    if (response.ok) {{
                        closeImplementationModal();
                        alert('✓ Implementation approved! Workflow completed.');
                        loadTasks();
                    }} else {{
                        alert('Failed to approve implementation');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            async function rejectImplementation() {{
                const reason = prompt('Reason for rejection (optional):');

                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/implementation/reject`, {{
                        method: 'PUT',
                        headers: authHeaders(),
                        body: JSON.stringify({{
                            approved_by: 'web_user',
                            reason: reason || 'No reason provided'
                        }})
                    }});

                    if (response.ok) {{
                        closeImplementationModal();
                        loadTasks();
                    }} else {{
                        alert('Failed to reject implementation');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            async function retryImplementation() {{
                try {{
                    const response = await fetch(`/api/tasks/${{currentTaskId}}/implementation/retry`, {{
                        method: 'PUT',
                        headers: authHeaders()
                    }});

                    if (response.ok) {{
                        closeImplementationModal();
                        showProgressModal(currentTaskId);
                        updateProgress('Retrying...', 'Retrying implementation with same plan');
                    }} else {{
                        alert('Failed to retry implementation');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}

            // Progress Modal Functions
            function showProgressModal(taskId) {{
                document.getElementById('progressModal').classList.add('active');
                document.getElementById('progressLog').innerHTML = '';
                connectWebSocket(taskId);
            }}

            function closeProgressModal() {{
                document.getElementById('progressModal').classList.remove('active');
                if (currentWebSocket) {{
                    currentWebSocket.close();
                    currentWebSocket = null;
                }}
            }}

            function updateProgress(status, message) {{
                document.getElementById('progressStatus').textContent = status;
                document.getElementById('progressMessage').textContent = message;

                // Add to log
                const log = document.getElementById('progressLog');
                const timestamp = new Date().toLocaleTimeString();
                log.innerHTML += `<div style="font-size: 12px; color: #666; margin-bottom: 4px;">
                    [${{timestamp}}] ${{status}}: ${{message}}
                </div>`;
                log.scrollTop = log.scrollHeight;
            }}

            // Task item click handlers
            function makeTaskClickable(taskId, status) {{
                if (status === 'plan_awaiting_approval') {{
                    return `onclick="loadTaskPlanForApproval(${{taskId}})"`;
                }} else if (status === 'implementation_awaiting_approval') {{
                    return `onclick="loadTaskImplementationForApproval(${{taskId}})"`;
                }} else if (['planning', 'implementing', 'reviewing', 'verifying'].includes(status)) {{
                    return `onclick="showProgressModal(${{taskId}})"`;
                }}
                return '';
            }}

            async function loadTaskPlanForApproval(taskId) {{
                try {{
                    const response = await fetch(`/api/tasks/${{taskId}}`, {{ headers: authHeaders(false) }});
                    const task = await response.json();
                    showPlanModal(taskId, task.plan);
                }} catch (error) {{
                    alert('Error loading task: ' + error.message);
                }}
            }}

            async function loadTaskImplementationForApproval(taskId) {{
                try {{
                    const response = await fetch(`/api/tasks/${{taskId}}`, {{ headers: authHeaders(false) }});
                    const task = await response.json();
                    showImplementationModal(taskId, {{
                        plan: task.plan,
                        implementation: JSON.parse(task.implementation || '{{}}'),
                        review: task.review,
                        verification: JSON.parse(task.verification_result || '{{}}')
                    }});
                }} catch (error) {{
                    alert('Error loading task: ' + error.message);
                }}
            }}

            // Submit task
            document.getElementById('taskForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const request = document.getElementById('taskRequest').value;
                const button = e.target.querySelector('button');

                button.textContent = 'Submitting...';
                button.disabled = true;

                try {{
                    const response = await fetch('/api/tasks', {{
                        method: 'POST',
                        headers: authHeaders(),
                        body: JSON.stringify({{ request }})
                    }});

                    if (response.ok) {{
                        const result = await response.json();
                        document.getElementById('taskRequest').value = '';

                        // Show progress modal and connect WebSocket
                        showProgressModal(result.id);
                        loadTasks();
                    }} else {{
                        alert('Failed to submit task');
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }} finally {{
                    button.textContent = 'Submit Task';
                    button.disabled = false;
                }}
            }});

            // Load tasks
            async function loadTasks() {{
                try {{
                    const response = await fetch('/api/tasks', {{ headers: authHeaders(false) }});
                    const tasks = await response.json();

                    const taskList = document.getElementById('taskList');

                    if (tasks.length === 0) {{
                        taskList.innerHTML = '<div class="empty-state">No tasks yet. Submit your first task above!</div>';
                        return;
                    }}

                    taskList.innerHTML = '<ul class="task-list">' + tasks.map(task => {{
                        const clickable = makeTaskClickable(task.id, task.status);
                        return `
                        <li class="task-item ${{task.status}}" ${{clickable}}>
                            <div class="task-header">
                                <span class="task-id">#${{task.id}}</span>
                                <span class="task-status ${{task.status}}">${{task.status.replace(/_/g, ' ')}}</span>
                            </div>
                            <div class="task-request">${{task.request}}</div>
                            <div class="task-time">${{new Date(task.created_at).toLocaleString()}}</div>
                        </li>
                    `;
                    }}).join('') + '</ul>';
                }} catch (error) {{
                    document.getElementById('taskList').innerHTML =
                        '<div class="empty-state">Error loading tasks</div>';
                }}
            }}

            // Auto-refresh tasks every 5 seconds
            loadTasks();
            setInterval(loadTasks, 5000);
        </script>
    </body>
    </html>
    """
    return html

# WebSocket endpoint
@app.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    """WebSocket for real-time task progress updates."""
    await websocket.accept()

    try:
        # Subscribe to task progress
        workflow_manager.subscribe(task_id, websocket)

        # Send current status immediately
        task = get_task_from_db(task_id)
        if task:
            await websocket.send_text(json.dumps({
                "event": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "task_id": task_id,
                    "status": task['status'],
                    "request": task['request']
                }
            }))

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle client messages (e.g., ping/pong)
            if data == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))

    except WebSocketDisconnect:
        workflow_manager.unsubscribe(task_id, websocket)
    except Exception as e:
        print(f"WebSocket error for task {task_id}: {e}")
        workflow_manager.unsubscribe(task_id, websocket)

# API Endpoints
@app.post("/api/tasks")
async def create_task(request: TaskRequest, username: str = Depends(verify_credentials)):
    """Submit a new coding task"""
    task_request = request.request.strip()

    if not task_request:
        raise HTTPException(status_code=400, detail="Request is required")

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (request, status, workflow_state) VALUES (?, ?, ?)",
        (task_request, "pending", "pending")
    )
    task_id = c.lastrowid
    conn.commit()
    conn.close()

    # Start workflow using WorkflowManager
    orchestrator = HierarchicalOrchestrator()
    await workflow_manager.start_workflow(task_id, task_request, orchestrator)

    return {"id": task_id, "status": "pending"}

@app.get("/api/tasks")
def get_tasks(username: str = Depends(verify_credentials)):
    """Get all tasks"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, request, status, created_at FROM tasks ORDER BY id DESC LIMIT 20")
    tasks = [
        {
            "id": row[0],
            "request": row[1],
            "status": row[2],
            "created_at": row[3]
        }
        for row in c.fetchall()
    ]
    conn.close()
    return tasks

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int, username: str = Depends(verify_credentials)):
    """Get specific task details"""
    task = get_task_from_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Plan approval endpoints
@app.put("/api/tasks/{task_id}/plan/approve")
async def approve_plan(
    task_id: int,
    request: PlanApprovalRequest,
    username: str = Depends(verify_credentials)
):
    """Approve plan and continue to implementation."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'plan_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting plan approval (status: {task['status']})")

    # Update approval metadata
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tasks
        SET plan_approved_at = ?,
            plan_approved_by = ?,
            updated_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), request.approved_by, datetime.now().isoformat(), task_id))
    conn.commit()
    conn.close()

    # Restore checkpoint from DB if not in memory (survives server restarts)
    if not workflow_manager.restore_checkpoint(task_id):
        raise HTTPException(status_code=500, detail="Checkpoint data missing from DB")

    # Resume workflow
    orchestrator = HierarchicalOrchestrator()
    await workflow_manager.resume_after_plan_approval(task_id, orchestrator)

    return {"status": "approved", "message": "Plan approved, continuing to implementation"}

@app.put("/api/tasks/{task_id}/plan/reject")
async def reject_plan(
    task_id: int,
    request: PlanRejectionRequest,
    username: str = Depends(verify_credentials)
):
    """Reject plan and abort workflow."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'plan_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting plan approval (status: {task['status']})")

    # Update database
    update_task(
        task_id,
        "plan_rejected",
        plan_rejection_reason=request.reason,
        plan_approved_by=request.approved_by
    )

    # Remove from approval queue
    workflow_manager.approval_queue.pop(task_id, None)

    await workflow_manager._broadcast_progress(task_id, "plan_rejected", {"reason": request.reason})

    return {"status": "rejected", "message": "Plan rejected, workflow aborted"}

@app.put("/api/tasks/{task_id}/plan/edit")
async def edit_plan(
    task_id: int,
    request: PlanEditRequest,
    username: str = Depends(verify_credentials)
):
    """Request revised plan based on user feedback."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'plan_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting plan approval")

    # Get checkpoint data (restore from DB if needed)
    checkpoint = workflow_manager.restore_checkpoint(task_id)
    if not checkpoint:
        raise HTTPException(status_code=400, detail="No checkpoint data found")

    try:
        # Ask Qwen3 to revise plan
        orchestrator = HierarchicalOrchestrator()

        revision_prompt = f"""The user reviewed your plan and requested changes:

Original Plan:
{checkpoint.plan}

Requested Changes:
{request.feedback}

Please provide a revised implementation plan addressing these changes."""

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

        # Run in executor since call_qwen3_lead is synchronous
        loop = asyncio.get_event_loop()
        revised_plan = await loop.run_in_executor(
            None,
            lambda: orchestrator.call_qwen3_lead(revision_prompt, system_prompt)
        )

        # Update task with revised plan
        update_task(task_id, "plan_awaiting_approval", plan=revised_plan)
        checkpoint.plan = revised_plan

        await workflow_manager._broadcast_progress(task_id, "plan_revised", {"plan": revised_plan})

        return {"status": "revised", "plan": revised_plan}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revise plan: {str(e)}")

# Implementation approval endpoints
@app.put("/api/tasks/{task_id}/implementation/approve")
async def approve_implementation(
    task_id: int,
    request: ImplementationApprovalRequest,
    username: str = Depends(verify_credentials)
):
    """Approve implementation and complete workflow."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'implementation_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting implementation approval")

    # Update approval metadata
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE tasks
        SET implementation_approved_at = ?,
            implementation_approved_by = ?,
            updated_at = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), request.approved_by, datetime.now().isoformat(), task_id))
    conn.commit()
    conn.close()

    # Complete workflow
    await workflow_manager.complete_workflow(task_id)

    return {"status": "approved", "message": "Implementation approved, workflow completed"}

@app.put("/api/tasks/{task_id}/implementation/reject")
async def reject_implementation(
    task_id: int,
    request: ImplementationRejectionRequest,
    username: str = Depends(verify_credentials)
):
    """Reject implementation and abort workflow."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'implementation_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting implementation approval")

    # Update database
    update_task(
        task_id,
        "implementation_rejected",
        implementation_rejection_reason=request.reason,
        implementation_approved_by=request.approved_by
    )

    # Remove from workflow
    workflow_manager.approval_queue.pop(task_id, None)

    await workflow_manager._broadcast_progress(task_id, "implementation_rejected", {"reason": request.reason})

    return {"status": "rejected", "message": "Implementation rejected, workflow aborted"}

@app.put("/api/tasks/{task_id}/implementation/retry")
async def retry_implementation(
    task_id: int,
    username: str = Depends(verify_credentials)
):
    """Retry implementation with same plan."""
    task = get_task_from_db(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] != 'implementation_awaiting_approval':
        raise HTTPException(status_code=400, detail=f"Task not awaiting implementation approval")

    # Get checkpoint (restore from DB if needed)
    if not workflow_manager.restore_checkpoint(task_id):
        raise HTTPException(status_code=400, detail="No checkpoint data found")

    # Increment retry count
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET retry_count = retry_count + 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    # Retry implementation
    orchestrator = HierarchicalOrchestrator()
    await workflow_manager.resume_after_plan_approval(task_id, orchestrator)

    return {"status": "retrying", "message": "Retrying implementation with same plan"}

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    print(f"\nStarting web interface on http://0.0.0.0:{port}")
    print("Access from your mobile at http://YOUR_IP:{port}")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
