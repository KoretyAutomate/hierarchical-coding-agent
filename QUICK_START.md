# Coding Agent System - Quick Start

## ✅ Setup Complete!

Your local coding agent powered by **Qwen3-Coder** via **Ollama** is ready to use.

### Memory Usage: ✅ Safe
- **Model**: Qwen3-Coder (18GB GGUF quantized)
- **VRAM**: Minimal usage with Ollama quantization
- **Status**: Well under 40% memory limit for DGX Spark stability

## How to Use

### For You (End User)

Just tell Claude Code what you want in natural language:

```
You: "Add error handling to the search_tool function"
You: "Create a feature to export research to JSON"
You: "Write tests for the PDF generator"
```

Claude Code will:
1. Break down your request
2. Delegate coding to the local agent
3. Review the agent's work
4. Test everything
5. Deliver working code

**You don't need to do anything else!** The agent runs in the background.

---

## System Status

### Check if everything is running:
```bash
# Check Ollama
ollama list

# Should show: qwen3-coder:latest

# Test API
curl http://localhost:11434/v1/models
```

### If Ollama is not running:
```bash
cd ~/coding-agent
./start_ollama_server.sh
```

---

## Example Workflow

### Simple Task:
```
You: "Add input validation to podcast_crew.py"

Claude Code:
  ├─ Analyzes request
  ├─ Delegates to agent: "Add validation for topic_name variable"
  │   └─ Agent: Reads file, adds validation, tests it
  ├─ Reviews agent's code
  ├─ Tests the changes
  └─ Shows you: "✓ Validation added!"

You: Get working code, ready to run!
```

### Complex Feature:
```
You: "Add database support to save research findings"

Claude Code:
  ├─ Asks: "Which database? SQLite, PostgreSQL?"
  │   (You answer: "SQLite")
  ├─ Breaks into tasks:
  │   1. Design schema
  │   2. Add SQLite connection
  │   3. Implement save function
  │   4. Add error handling
  │   5. Write tests
  ├─ Delegates each task to agent
  ├─ Reviews all implementations
  ├─ Integrates everything
  ├─ Tests end-to-end
  └─ Delivers: "✓ Database support added with 15 tests passing!"

You: Complete feature, working perfectly!
```

---

## What Claude Code Does Behind the Scenes

When you make a request, Claude Code uses the orchestrator:

```python
# Internal - you don't run this
from orchestrator import TaskOrchestrator
orch = TaskOrchestrator()

# Add task to queue
task_id = orch.add_task("Your request here")

# Agent works on it
orch.execute_next_task()

# Claude reviews and tests
# Then shows you the result
```

---

## Agent Capabilities

### ✅ What the agent CAN do:
- Read and write code files
- Implement new functions and features
- Refactor existing code
- Write tests
- Fix bugs
- Search and analyze code
- Execute Python code for testing
- Follow coding best practices

### ⚠️ What requires Claude Code oversight:
- Architecture decisions (Claude asks you)
- Breaking changes (Claude reviews first)
- Complex multi-file changes (Claude coordinates)
- Integration testing (Claude verifies)
- Final delivery (Claude presents to you)

### ❌ What the agent CANNOT do:
- Install system packages (you must do this)
- Access network/external APIs (except through code)
- Modify files outside the project
- Make autonomous architecture decisions

---

## Manual Testing (Optional)

If you want to test the agent directly:

```bash
cd ~/coding-agent

# Run test
python3 test_agent.py

# Or add your own task
python3 delegate.py "List all functions in podcast_crew.py"
python3 delegate.py --execute

# Check status
python3 delegate.py --summary
```

---

## Files & Logs

### Configuration:
- `~/coding-agent/config/agent_config.yaml` - Settings

### Logs:
- `~/coding-agent/tasks/queue.json` - Pending tasks
- `~/coding-agent/tasks/completed.json` - Completed tasks
- `~/coding-agent/logs/task_*.json` - Detailed task logs

### Scripts:
- `~/coding-agent/start_ollama_server.sh` - Start Ollama
- `~/coding-agent/test_agent.py` - Test the system
- `~/coding-agent/delegate.py` - Manual task delegation

---

## Memory Monitoring

```bash
# Check GPU memory
nvidia-smi

# The system is configured to stay under 40% automatically
```

---

## Troubleshooting

### "Ollama not responding"
```bash
./start_ollama_server.sh
```

### "Model not found"
```bash
ollama pull qwen3-coder
```

### "Agent taking too long"
- Claude Code will detect this and take over
- You don't need to intervene

### "Task failed"
- Claude Code reviews failures
- Either retries with better instructions
- Or completes the task itself
- You'll always get a working result

---

## What's Next?

**You're all set!** Just start making requests:

1. Tell Claude Code what feature you want
2. Watch the agent work (or don't - it's automatic)
3. Get working code delivered to you

**Example requests to try:**
- "Add logging to all the agents in podcast_crew.py"
- "Create a config file for the topic name"
- "Add a progress bar to show research status"
- "Write unit tests for the PDF generator"
- "Refactor the search tool to handle errors better"

---

## System Summary

```
✅ LLM: Qwen3-Coder via Ollama
✅ Memory: <40% (GGUF quantized)
✅ API: OpenAI-compatible endpoint
✅ Tools: File ops, code exec, testing
✅ Orchestration: Task queue + monitoring
✅ Test: Passed successfully!
✅ Status: Ready to use!
```

**Start building features touchlessly! Just tell Claude Code what you need.**
