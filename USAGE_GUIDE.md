# Coding Agent System - Usage Guide

## Overview

This system allows Claude Code to delegate coding tasks to a local AI agent powered by **Qwen2.5-Coder-7B** (memory-optimized for your DGX Spark).

## Memory Safety ⚠️

- **CRITICAL**: Memory usage capped at <40% to prevent DGX crashes
- Model: Qwen2.5-Coder-7B (not 14B) for safety
- Max memory: 10GB allocation
- Monitor with: `./check_memory.sh`

## System Status

### Check if LLM server is running:
```bash
curl http://localhost:8001/v1/models
```

If not running, start it:
```bash
cd ~/coding-agent
./start_simple_server.sh
```

## How It Works

### Architecture
```
You (User)
    ↓ "Build feature X"
Claude Code (Orchestrator)
    ↓ Breaks down task, delegates
Task Queue
    ↓
Local Coding Agent (Qwen2.5-Coder-7B)
    ↓ Uses tools to implement
Your Project Files
    ↓
Claude Code Reviews & Tests
    ↓
You Get Working Feature!
```

### What Claude Code Does
1. Receives your high-level request
2. Breaks it into concrete tasks
3. Delegates coding work to the local agent
4. Monitors agent progress
5. Reviews outputs for quality
6. Tests the code
7. Steps in if agent gets stuck
8. Delivers working solution to you

### What the Agent Does
- Reads and writes files
- Implements code changes
- Runs tests
- Searches code
- Executes Python for testing
- Reports back to Claude Code

## Usage Examples

### Example 1: Claude Code Delegates a Task

When you tell Claude Code: *"Add input validation to the podcast_crew.py"*

Claude Code will:
```python
# Claude Code runs internally:
from orchestrator import TaskOrchestrator
orch = TaskOrchestrator()

task_id = orch.add_task(
    "Add input validation to podcast_crew.py",
    context="Validate topic_name is not empty and has reasonable length"
)

# Then executes the task
orch.execute_next_task()
```

The agent will:
1. Read `podcast_crew.py`
2. Understand the current structure
3. Add validation code
4. Test it works
5. Report completion

Claude Code will then:
1. Review the changes
2. Test the code
3. Show you the results

### Example 2: Building a New Feature

You: *"Add a feature to save research findings to a database"*

Claude Code will:
1. Ask clarifying questions (which database? schema?)
2. Break down into tasks:
   - Design database schema
   - Add database connection
   - Implement save function
   - Add error handling
   - Write tests
3. Delegate implementation tasks to agent
4. Review each completed task
5. Ensure everything works together
6. Deliver working feature

## Direct CLI Usage (Advanced)

### Manually add tasks to queue:
```bash
cd ~/coding-agent
python3 delegate.py "Add logging to all functions in podcast_crew.py"
```

### Execute tasks:
```bash
# Execute next task in queue
python3 delegate.py --execute

# Execute all queued tasks
python3 delegate.py --execute-all
```

### Monitor tasks:
```bash
# View summary
python3 delegate.py --summary

# List queue
python3 delegate.py --list

# Check specific task
python3 delegate.py --status task_1738344123000
```

### View logs:
```bash
# Server logs
tail -f ~/coding-agent/logs/server.log

# Task logs
ls ~/coding-agent/logs/task_*.json
cat ~/coding-agent/logs/task_1738344123000.json
```

## Agent Capabilities

### File Operations
- Read any file in the project
- Write new files
- Edit existing files (find & replace)
- List directory contents
- Search code with patterns

### Code Execution
- Run Python code safely
- Execute tests with pytest
- Check syntax and imports

### Limitations
- Works within `/home/korety/Project/DR_2_Podcast` by default
- Cannot modify system files
- Cannot install packages (you must do this)
- Cannot make network requests (except through your code)
- 10-iteration limit per task (prevents infinite loops)

## Configuration

Edit `/home/korety/coding-agent/config/agent_config.yaml`:

```yaml
agent:
  model: "Qwen2.5-Coder-7B"
  memory_limit: "40%"  # Don't change this!

llm:
  base_url: "http://localhost:8001/v1"
  temperature: 0.2  # Lower = more deterministic
  max_tokens: 4096

workspace:
  project_root: "/home/korety/Project/DR_2_Podcast"
```

## Troubleshooting

### Server won't start
```bash
# Check if port 8001 is in use
lsof -i :8001

# Kill existing process
pkill -f simple_llm_server

# Restart
./start_simple_server.sh
```

### Agent gets stuck
Claude Code will:
- Detect when agent isn't making progress
- Take over the task
- Complete it directly
- You don't need to do anything

### Memory issues
```bash
# Check memory
nvidia-smi

# If over 40%, restart with smaller model already configured
# The system is already using 7B (smallest practical coding model)
```

### Task failed
```bash
# Check logs
cat ~/coding-agent/logs/task_<id>.json

# Claude Code will review failures and either:
# - Fix the issue and retry
# - Complete the task itself
# - Ask you for clarification
```

## Best Practices

### For You (User):
1. Tell Claude Code what you want in natural language
2. Let Claude Code handle the details
3. Answer questions if Claude Code needs clarification
4. Review the final result

### For Claude Code:
1. Break complex requests into small tasks
2. Provide clear task descriptions to the agent
3. Always review agent outputs
4. Test changes before showing to user
5. Step in if agent struggles
6. Keep task descriptions focused and specific

## What's Next?

1. **Wait for model to load** (~5-10 minutes for first time)
2. **Test the system** with a simple task
3. **Integrate with your workflow**
4. **Start building features touchlessly!**

## Example Workflow

```
User: "Add a summary function to generate 2-sentence paper abstracts"

Claude Code:
  ├─ Analyzes current code structure
  ├─ Delegates: "Implement summarize_paper() function in podcast_crew.py"
  │   └─ Agent: Reads code, implements function, tests it
  ├─ Reviews agent's implementation
  ├─ Tests with sample data
  ├─ Fixes any issues
  └─ Reports: "✓ Summary function added and tested!"

User: Sees working feature, ready to use!
```

## Files Structure

```
~/coding-agent/
├── config/
│   └── agent_config.yaml          # Configuration
├── agents/
│   └── coding_agent.py            # Main agent logic
├── tools/
│   └── coding_tools.py            # Available tools
├── tasks/
│   ├── queue.json                 # Pending tasks
│   └── completed.json             # Task history
├── logs/
│   ├── server.log                 # LLM server logs
│   └── task_*.json                # Individual task logs
├── orchestrator.py                # Task management
├── delegate.py                    # Quick delegation interface
├── simple_llm_server.py           # LLM inference server
└── start_simple_server.sh         # Server startup script
```

---

**Ready to build!** Just tell Claude Code what you want, and the agent system will help make it happen.
