# Visual Workflow Guide

## Complete User Journey: From Task to Completion

### Step 1: Submit Task
```
┌─────────────────────────────────────┐
│  🤖 Coding Agent                    │
│  Logged in as: admin                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Submit New Task                    │
│  ┌─────────────────────────────┐   │
│  │ Add error handling to the   │   │
│  │ search function             │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│  [    Submit Task    ]              │
└─────────────────────────────────────┘
```

### Step 2: Real-Time Progress (WebSocket)
```
┌─────────────────────────────────────┐
│  ⚙️ Workflow Progress               │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐   │
│  │ Status: Planning            │   │
│  │ Creating implementation     │   │
│  │ plan...                     │   │
│  └─────────────────────────────┘   │
│                                     │
│  [12:34:56] task_started: Add...   │
│  [12:34:57] Stage: planning        │
│  [12:35:12] Analyzing codebase...  │
│  [12:35:45] Generating plan...     │
│                                     │
│  [×]                                │
└─────────────────────────────────────┘
```

### Step 3: Plan Approval Modal
```
┌─────────────────────────────────────┐
│  📋 Review Plan              [×]    │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐   │
│  │ Implementation Plan:        │   │
│  │                             │   │
│  │ 1. Read search function     │   │
│  │ 2. Identify error points    │   │
│  │ 3. Add try/catch blocks     │   │
│  │ 4. Add input validation     │   │
│  │ 5. Add error logging        │   │
│  │ 6. Write tests              │   │
│  └─────────────────────────────┘   │
│                                     │
│  [  ✓ Approve  ] [✎ Request Changes] [✗ Reject]
└─────────────────────────────────────┘
```

### Step 3a: Request Changes (Optional)
```
┌─────────────────────────────────────┐
│  📋 Review Plan              [×]    │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐   │
│  │ Implementation Plan:        │   │
│  │ ...                         │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Also add unit tests for     │   │
│  │ edge cases                  │   │
│  └─────────────────────────────┘   │
│                                     │
│  [  ✓ Approve  ] [📤 Submit Changes]
└─────────────────────────────────────┘

    ↓ (Qwen3 Lead revises plan)

┌─────────────────────────────────────┐
│  📋 Review Plan (Revised)    [×]    │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐   │
│  │ Implementation Plan:        │   │
│  │                             │   │
│  │ 1. Read search function     │   │
│  │ 2. Identify error points    │   │
│  │ 3. Add try/catch blocks     │   │
│  │ 4. Add input validation     │   │
│  │ 5. Add error logging        │   │
│  │ 6. Write comprehensive tests│   │
│  │    - Happy path             │   │
│  │    - Edge cases             │   │
│  │    - Error conditions       │   │
│  └─────────────────────────────┘   │
│                                     │
│  [  ✓ Approve  ] [✎ Request Changes] [✗ Reject]
└─────────────────────────────────────┘
```

### Step 4: Implementation Progress
```
┌─────────────────────────────────────┐
│  ⚙️ Workflow Progress               │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────┐   │
│  │ Status: Implementing        │   │
│  │ Qwen3-Coder writing code... │   │
│  └─────────────────────────────┘   │
│                                     │
│  [12:36:01] Plan approved          │
│  [12:36:02] Stage: implementing    │
│  [12:36:15] Reading files...       │
│  [12:36:30] Writing code...        │
│  [12:37:45] Running tests...       │
│                                     │
│  [×]                                │
└─────────────────────────────────────┘
```

### Step 5: Implementation Approval Modal
```
┌─────────────────────────────────────┐
│  🔍 Review Implementation    [×]    │
│  ─────────────────────────────────  │
│  📝 Original Plan:                  │
│  ┌─────────────────────────────┐   │
│  │ 1. Read search function     │   │
│  │ 2. Add try/catch blocks...  │   │
│  └─────────────────────────────┘   │
│                                     │
│  💻 Implementation Result:          │
│  ┌─────────────────────────────┐   │
│  │ {                           │   │
│  │   "files_modified": [       │   │
│  │     "search.js"             │   │
│  │   ],                        │   │
│  │   "changes": "Added error   │   │
│  │   handling..."              │   │
│  │ }                           │   │
│  └─────────────────────────────┘   │
│                                     │
│  👀 Lead Review:                    │
│  ┌─────────────────────────────┐   │
│  │ Code looks good. Error      │   │
│  │ handling is comprehensive.  │   │
│  │ Tests pass.                 │   │
│  └─────────────────────────────┘   │
│                                     │
│  ✅ Verification:                   │
│  ┌─────────────────────────────┐   │
│  │ {                           │   │
│  │   "tests_passed": true,     │   │
│  │   "coverage": 95%           │   │
│  │ }                           │   │
│  └─────────────────────────────┘   │
│                                     │
│  [✓ Approve & Complete] [🔄 Retry] [✗ Reject]
└─────────────────────────────────────┘
```

### Step 6: Completion
```
┌─────────────────────────────────────┐
│  🤖 Coding Agent                    │
│  Logged in as: admin                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Recent Tasks                       │
│  ┌─────────────────────────────┐   │
│  │ #1              [COMPLETED] │   │
│  │ Add error handling to the   │   │
│  │ search function             │   │
│  │ 2026-02-02 12:35:00         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

✓ Implementation approved! Workflow completed.
```

---

## Alternative Paths

### Path A: Plan Rejection
```
Step 3: Plan Approval
  ↓
[✗ Reject] clicked
  ↓
Prompt: "Reason for rejection?"
User: "Too complex, simplify"
  ↓
Status: plan_rejected
Workflow: ABORTED
```

### Path B: Implementation Rejection
```
Step 5: Implementation Approval
  ↓
[✗ Reject] clicked
  ↓
Prompt: "Reason for rejection?"
User: "Tests don't cover edge cases"
  ↓
Status: implementation_rejected
Workflow: ABORTED
```

### Path C: Implementation Retry
```
Step 5: Implementation Approval
  ↓
[🔄 Retry] clicked
  ↓
Status: implementing
Retry count: +1
  ↓
Qwen3-Coder runs again with same plan
  ↓
Back to Step 5 with new implementation
```

### Path D: Error Handling
```
Any Step
  ↓
Error occurs (network, timeout, etc.)
  ↓
WebSocket event: "task_error"
  ↓
Progress modal shows error
Status: failed
Error details saved to database
```

---

## Task List View

### Status Colors
```
┌─────────────────────────────────────┐
│  Recent Tasks                       │
│                                     │
│  🟡 #4              [PENDING]       │
│  Just submitted, not started        │
│                                     │
│  🔵 #3              [PLANNING]      │
│  Qwen3 Lead creating plan           │
│                                     │
│  🟠 #2  [PLAN AWAITING APPROVAL] ← Click me!
│  ↑ Pulsing animation                │
│                                     │
│  🟢 #1              [COMPLETED]     │
│  All done, approved                 │
│                                     │
│  🔴 #0              [FAILED]        │
│  Error occurred                     │
└─────────────────────────────────────┘
```

### Click Behaviors
- **PENDING**: No action
- **PLANNING**: Opens progress modal (WebSocket)
- **PLAN_AWAITING_APPROVAL**: Opens plan modal ← ⭐ ACTION NEEDED
- **IMPLEMENTING**: Opens progress modal (WebSocket)
- **IMPLEMENTATION_AWAITING_APPROVAL**: Opens implementation modal ← ⭐ ACTION NEEDED
- **COMPLETED**: No action
- **FAILED**: No action (shows error details)

---

## Mobile Phone View

### Portrait Mode
```
┌───────────────────┐
│  🤖 Coding Agent  │
│  admin            │
├───────────────────┤
│ Submit New Task   │
│ ┌───────────────┐ │
│ │ Add error...  │ │
│ │               │ │
│ └───────────────┘ │
│ [  Submit Task  ] │
├───────────────────┤
│ Recent Tasks      │
│ ┌───────────────┐ │
│ │ #1 [COMPLETE] │ │
│ │ Add error...  │ │
│ │ 12:35:00      │ │
│ └───────────────┘ │
└───────────────────┘
```

### Modal View (Full Screen)
```
┌───────────────────┐
│ 📋 Review Plan [×]│
├───────────────────┤
│ ┌───────────────┐ │
│ │ Plan:         │ │
│ │ 1. Read...    │ │
│ │ 2. Add...     │ │
│ │ 3. Test...    │ │
│ │               │ │
│ │ ↓ scroll      │ │
│ └───────────────┘ │
│                   │
│ [   ✓ Approve  ]  │
│ [✎ Req Changes]   │
│ [   ✗ Reject   ]  │
└───────────────────┘
```

---

## WebSocket Event Timeline

```
Time        Event                    Data
───────     ──────────────────────   ─────────────────────
12:34:56    connection_established   task_id: 1
12:34:57    task_started             request: "Add error..."
12:34:58    stage_started            stage: "planning"
12:35:45    awaiting_approval        checkpoint: "plan"
            ↓ User approves plan
12:36:01    plan_approved            (internal)
12:36:02    stage_started            stage: "implementing"
12:37:50    awaiting_approval        checkpoint: "implementation"
            ↓ User approves implementation
12:38:00    task_complete            status: "completed"
```

---

## API Call Sequence

```
1. User submits task
   POST /api/tasks
   ← 201 Created { id: 1, status: "pending" }

2. Browser connects WebSocket
   WS /ws/tasks/1
   → "connection_established"

3. Workflow reaches plan checkpoint
   → "awaiting_approval" (via WebSocket)

4. User approves plan
   PUT /api/tasks/1/plan/approve
   ← 200 OK { status: "approved" }

5. Workflow reaches implementation checkpoint
   → "awaiting_approval" (via WebSocket)

6. User approves implementation
   PUT /api/tasks/1/implementation/approve
   ← 200 OK { status: "approved" }

7. Workflow completes
   → "task_complete" (via WebSocket)
```

---

## Database State Transitions

```
Task #1 State History:

INSERT INTO tasks (request, status, workflow_state)
VALUES ("Add error handling", "pending", "pending")

UPDATE tasks SET status = "planning"
WHERE id = 1

UPDATE tasks SET status = "plan_awaiting_approval",
                 plan = "1. Read...",
                 workflow_checkpoint_data = '{"stage": "plan_created"}'
WHERE id = 1

UPDATE tasks SET plan_approved_at = NOW(),
                 plan_approved_by = "web_user"
WHERE id = 1

UPDATE tasks SET status = "implementing"
WHERE id = 1

UPDATE tasks SET status = "implementation_awaiting_approval",
                 implementation = '{"files_modified": [...]}',
                 review = "Code looks good...",
                 verification_result = '{"tests_passed": true}'
WHERE id = 1

UPDATE tasks SET implementation_approved_at = NOW(),
                 implementation_approved_by = "web_user",
                 status = "completed"
WHERE id = 1
```

---

## Keyboard Shortcuts (Future Enhancement)

```
In Plan Modal:
- Enter: Approve
- Esc: Close
- E: Edit/Request Changes
- R: Reject

In Implementation Modal:
- Enter: Approve & Complete
- Esc: Close
- R: Retry
- X: Reject

In Task List:
- ↓/↑: Navigate tasks
- Enter: Open modal for selected task
- F5: Refresh
```

---

## Error Scenarios

### Scenario 1: Network Timeout
```
Step: Planning
↓
Network timeout (30s)
↓
WebSocket: { event: "task_error", data: { error: "Timeout" } }
↓
Status: failed
Error details: "Network timeout after 30s"
```

### Scenario 2: Invalid Plan
```
Step: Plan approval
↓
User clicks [✗ Reject]
↓
Reason: "Plan incomplete"
↓
Status: plan_rejected
Plan rejection reason: "Plan incomplete"
```

### Scenario 3: Implementation Failure
```
Step: Implementing
↓
Qwen3-Coder error
↓
WebSocket: { event: "task_error", data: { error: "Syntax error" } }
↓
Status: failed
Error details: "Syntax error in generated code"
```

---

## Performance Expectations

### Timing Estimates
```
Task submission:        <1s
WebSocket connection:   <1s
Plan generation:        30s - 2min (depends on complexity)
Implementation:         1min - 5min (depends on changes)
Verification:           10s - 1min (runs tests)
Total workflow:         2min - 10min
```

### User Wait Times
```
Wait 1: Plan approval needed
  → User reviews plan (1-5 minutes)
  → Approves/rejects/edits

Wait 2: Implementation approval needed
  → User reviews implementation (2-10 minutes)
  → Approves/rejects/retries

Total active user time: 3-15 minutes
Total workflow time: 2-10 minutes
```

---

## Best Practices

### For Users
1. **Review plans carefully** before approving
2. **Request changes** if plan unclear
3. **Check verification results** before final approval
4. **Use retry** if implementation has minor issues
5. **Keep browser open** during workflow (WebSocket)

### For Administrators
1. **Setup HTTPS** for production
2. **Use strong credentials** (16+ chars)
3. **Enable firewall** rules
4. **Regular backups** of tasks.db
5. **Monitor logs** for errors

---

**End of Visual Workflow Guide**
