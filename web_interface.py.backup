#!/usr/bin/env python3
"""
Secure Web Interface for Hierarchical Coding Agent
Mobile-friendly task submission and monitoring
"""
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from hierarchical_orchestrator import HierarchicalOrchestrator

# Configuration
DB_PATH = Path("/home/korety/coding-agent/tasks.db")
USERNAME = os.getenv("WEB_USERNAME", "admin")
PASSWORD = os.getenv("WEB_PASSWORD", secrets.token_urlsafe(16))  # Generate random if not set

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

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan TEXT,
            implementation TEXT,
            review TEXT,
            workflow_log TEXT
        )
    ''')
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

# Routes
@app.get("/", response_class=HTMLResponse)
def home(username: str = Depends(verify_credentials)):
    """Main page with mobile-responsive UI"""
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
            }}

            .task-item.pending {{
                border-left-color: #fbbf24;
            }}

            .task-item.in_progress {{
                border-left-color: #3b82f6;
            }}

            .task-item.completed {{
                border-left-color: #10b981;
            }}

            .task-item.failed {{
                border-left-color: #ef4444;
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

            .task-status.in_progress {{
                background: #dbeafe;
                color: #1e40af;
            }}

            .task-status.completed {{
                background: #d1fae5;
                color: #065f46;
            }}

            .task-status.failed {{
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

        <script>
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
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ request }})
                    }});

                    if (response.ok) {{
                        document.getElementById('taskRequest').value = '';
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
                    const response = await fetch('/api/tasks');
                    const tasks = await response.json();

                    const taskList = document.getElementById('taskList');

                    if (tasks.length === 0) {{
                        taskList.innerHTML = '<div class="empty-state">No tasks yet. Submit your first task above!</div>';
                        return;
                    }}

                    taskList.innerHTML = '<ul class="task-list">' + tasks.map(task => `
                        <li class="task-item ${{task.status}}">
                            <div class="task-header">
                                <span class="task-id">#${{task.id}}</span>
                                <span class="task-status ${{task.status}}">${{task.status.replace('_', ' ')}}</span>
                            </div>
                            <div class="task-request">${{task.request}}</div>
                            <div class="task-time">${{new Date(task.created_at).toLocaleString()}}</div>
                        </li>
                    `).join('') + '</ul>';
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

@app.post("/api/tasks")
async def create_task(request: Request, username: str = Depends(verify_credentials)):
    """Submit a new coding task"""
    data = await request.json()
    task_request = data.get("request", "").strip()

    if not task_request:
        raise HTTPException(status_code=400, detail="Request is required")

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (request, status) VALUES (?, ?)",
        (task_request, "pending")
    )
    task_id = c.lastrowid
    conn.commit()
    conn.close()

    # Start workflow in background
    import threading
    thread = threading.Thread(target=run_workflow, args=(task_id, task_request))
    thread.daemon = True
    thread.start()

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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": row[0],
        "request": row[1],
        "status": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "plan": row[5],
        "implementation": row[6],
        "review": row[7],
        "workflow_log": row[8]
    }

def run_workflow(task_id: int, request: str):
    """Run the hierarchical workflow for a task"""
    try:
        # Update status
        update_task(task_id, "in_progress")

        # Initialize orchestrator
        orchestrator = HierarchicalOrchestrator()

        # Run workflow
        result = orchestrator.autonomous_workflow(request)

        # Save plan
        update_task(task_id, "awaiting_approval", plan=result.get("plan"))

        # Note: In a production system, you'd want user approval here
        # For now, we just save the plan and mark as awaiting approval

    except Exception as e:
        update_task(task_id, "failed", workflow_log=str(e))

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

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    print(f"\nStarting web interface on http://0.0.0.0:{port}")
    print("Access from your mobile at http://YOUR_IP:{port}")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
