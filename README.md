# Hierarchical Coding Agent

> Autonomous coding agent with 3-tier hierarchical architecture for software development automation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

An autonomous coding agent that combines human oversight (Claude Code) with AI-powered project management and implementation using local LLMs. Works with any OpenAI-compatible backend (vLLM, Ollama, llama.cpp, etc.).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    You (Project Owner)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ Requirements
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         TIER 1: Project Manager (Claude Code)               │
│  • Coordinates workflow, runs tests, creates PRs            │
└───────────────────────────┬─────────────────────────────────┘
                            │ Delegates tasks
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        TIER 2: Project Lead (Qwen2.5-32B via vLLM)         │
│  • Creates implementation plans, reviews code               │
└───────────────────────────┬─────────────────────────────────┘
                            │ Assigns work
                            ↓
┌─────────────────────────────────────────────────────────────┐
│     TIER 3: Developer (Qwen2.5-32B via vLLM)               │
│  • Implements features, writes tests                        │
└─────────────────────────────────────────────────────────────┘
```

Both Lead and Developer tiers use **Qwen/Qwen2.5-32B-Instruct-AWQ** served by vLLM on port 8000.

## Quick Start

### Prerequisites

- Python 3.8+
- [vLLM](https://github.com/vllm-project/vllm) (or any OpenAI-compatible server)
- Git

### 1. Start vLLM

```bash
# Docker (recommended):
./start_vllm_docker.sh

# Or manually:
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-32B-Instruct-AWQ \
  --port 8000
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run tasks via delegate.py

```bash
# Immediate execution with file context
python3 delegate.py --now --workspace /path/to/project \
  --files src/main.py "Fix the validation bug in main.py"

# Queue a task for later
python3 delegate.py "Implement user authentication"

# Execute queued tasks
python3 delegate.py --execute       # next one
python3 delegate.py --execute-all   # all
python3 delegate.py --parallel 3    # 3 at once

# Dry run (preview diffs)
python3 delegate.py --now --dry-run "Refactor the search module"

# Check status
python3 delegate.py --list
python3 delegate.py --summary
python3 delegate.py --status TASK_ID

# View reflections
python3 delegate.py --reflect TASK_ID
python3 delegate.py --lessons
```

### 4. Or use the hierarchical orchestrator directly

```bash
# Programmatic mode (returns at checkpoints for external approval)
python3 hierarchical_orchestrator.py "Add error handling to the API"

# Interactive mode (asks for approval via terminal)
python3 hierarchical_orchestrator.py -i "Add error handling to the API"

# Resume interrupted task
python3 hierarchical_orchestrator.py --resume TASK_ID
```

## Configuration

Configuration uses **two layers**:

1. **`core/config.py`** — Pydantic defaults (authoritative source of truth)
2. **`.env`** — Environment variable overrides

Key environment variables:

```bash
# LLM settings
LLM_PROVIDER=openai                              # or "anthropic"
LLM_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
LLM_BASE_URL=http://localhost:8000/v1
LLM_TIMEOUT=300

# Orchestration
ORCH_LEAD_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
ORCH_LEAD_BASE_URL=http://localhost:8000/v1
ORCH_MEMBER_MODEL=Qwen/Qwen2.5-32B-Instruct-AWQ
ORCH_MEMBER_BASE_URL=http://localhost:8000/v1

# Workspace
WORKSPACE_PROJECT_ROOT=/path/to/your/project
```

## Writing Effective Task Prompts

### Recommended Template

```
[ACTION] [TARGET] in [FILE/SCOPE].
Context: [relevant background]
Files: [specific paths]
Expected: [what success looks like]
Constraints: [what NOT to change]
```

### Examples

**Vague** (low quality):
> Fix the search feature

**Specific** (high quality):
> Fix the empty results bug in `search/engine.py:execute_query()`. The function returns `[]` when the query contains special characters. Expected: queries like "C++" return valid results. Constraints: don't change the search index format.

Use `--files` to inject file contents as context:

```bash
python3 delegate.py "Fix the validation logic" --files src/validators.py,src/models.py --now
```

## Documentation

- [Usage Guide](USAGE_GUIDE.md) — Detailed usage examples
- [Workflow Guide](WORKFLOW_GUIDE.md) — Visual workflow walkthrough
- [Security](SECURITY.md) — Security considerations

## License

MIT — see [LICENSE](LICENSE).
