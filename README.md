# 🤖 Hierarchical Coding Agent

> **Open-source autonomous coding agent with 3-tier hierarchical architecture for software development automation**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

An intelligent, autonomous coding agent system that combines human oversight (Claude Code) with AI-powered project management and implementation using local LLMs for end-to-end software development automation. Works with any OpenAI-compatible LLM backend (Ollama, vLLM, llama.cpp, etc.) — we recommend models with strong code generation and instruction-following capabilities (20B+ parameters or equivalent quality).

## ✨ Features

- 🏗️ **3-Tier Hierarchical Architecture** - PM → Lead → Developer workflow
- 🔄 **Autonomous Workflows** - Plan, implement, review, test automatically
- 🎛️ **Dual Operation Modes** - Programmatic (for Claude Code integration) & Interactive (standalone terminal)
- ✅ **Output Verification** - Automated testing and file validation
- 🎨 **Enhanced PR Descriptions** - Auto-generate file references and testing guides
- 🌐 **Web Interface** - Mobile-friendly task submission and monitoring
- 🔧 **Tool Integration** - File operations, code execution, testing, search
- 📊 **Detailed Logging** - Complete audit trail of all operations
- 🎯 **Task Queue System** - Manage multiple tasks with priorities

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    You (Project Owner)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ Requirements
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         TIER 1: Project Manager (Claude Code)               │
│  • Coordinates workflow                                      │
│  • Runs tests and validation                                │
│  • Creates PRs with enhanced descriptions                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ Delegates tasks
                            ↓
┌─────────────────────────────────────────────────────────────┐
│        TIER 2: Project Lead (Local LLM — 20B+)               │
│  • Creates implementation plans                              │
│  • Reviews code quality                                      │
│  • Makes technical decisions                                │
└───────────────────────────┬─────────────────────────────────┘
                            │ Assigns work
                            ↓
┌─────────────────────────────────────────────────────────────┐
│     TIER 3: Developer (Local LLM — code-specialized)         │
│  • Implements features                                       │
│  • Writes tests                                              │
│  • Follows best practices                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- An OpenAI-compatible LLM backend (Ollama, vLLM, llama.cpp server, etc.)
- Git
- Basic understanding of software development

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/hierarchical-coding-agent.git
cd hierarchical-coding-agent
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Start your LLM backend**

```bash
# Example with Ollama:
ollama serve
ollama pull your-lead-model      # e.g. qwen3:32b, deepseek-coder-v2, codestral
ollama pull your-coder-model     # e.g. qwen3-coder, deepseek-coder, starcoder2

# Example with vLLM:
python -m vllm.entrypoints.openai.api_server --model your-model --port 8000
```

Any model served on an OpenAI-compatible endpoint works. For best results, use:
- **Lead model**: A strong reasoning model (20B+ params) for planning and review
- **Coder model**: A code-specialized model for implementation

4. **Configure your project**

Edit `config/agent_config.yaml`:

```yaml
workspace:
  project_root: "/path/to/your/project"

orchestration:
  logs_path: "logs"

llm:
  model_name: "your-model-name"          # Model served by your backend
  base_url: "http://localhost:11434/v1"   # OpenAI-compatible endpoint
  temperature: 0.2
  max_tokens: 4096
```

### Basic Usage

#### Hierarchical Workflow

**Programmatic Mode** (default - for integration with Claude Code):

```bash
# Start autonomous workflow (pauses at checkpoints for external approval)
python3 hierarchical_orchestrator.py "Add error handling to the API"

# The system will:
# 1. Lead model creates implementation plan
# 2. Returns plan for approval (caller handles approval)
# 3. After approval, continue_after_plan_approval() resumes
# 4. Coder model implements the code
# 5. Lead model reviews implementation
# 6. Output verification runs automatically
# 7. Returns results for approval (caller creates PR)
```

**Interactive Mode** (standalone - asks user directly):

```bash
# Run in interactive mode (asks for approval via terminal prompts)
python3 hierarchical_orchestrator.py --interactive "Add error handling to the API"

# OR shorthand:
python3 hierarchical_orchestrator.py -i "Add error handling to the API"

# The system will:
# 1. Lead model creates implementation plan
# 2. Asks YOU: "Do you approve this plan? (yes/no/edit)"
# 3. Coder model implements the code
# 4. Lead model reviews implementation
# 5. Output verification runs automatically
# 6. Asks YOU: "Do you approve the implementation? (yes/no/retry)"
# 7. Completes workflow and saves log
```

See [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) for detailed guide.

#### Task Queue System

```bash
# Add a task
python3 orchestrator.py add "Implement user authentication"

# Execute next task
python3 orchestrator.py execute

# Execute all tasks
python3 orchestrator.py execute-all

# Check status
python3 orchestrator.py status <task_id>

# View summary
python3 orchestrator.py summary
```

#### Web Interface

```bash
# Start web interface
./start_web_interface.sh

# Access from browser
http://localhost:8080

# Login with credentials shown in terminal
```

## Writing Effective Task Prompts

The coding agent includes a **self-reflection system** that scores prompt quality after each task. Understanding these scoring dimensions helps you write prompts that lead to efficient execution.

### Scoring Dimensions (1-5 scale)

| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Excellent) |
|-----------|----------|--------------|---------------|
| **Specificity** | "Fix the bug" | "Fix the auth bug" | "Fix the 401 error in `api/auth.py:login()`" |
| **Scope Clarity** | "Improve the code" | "Refactor the API module" | "Extract `validate_token()` from `api/auth.py` into `api/validators.py`" |
| **Context Sufficiency** | No background given | Some context provided | Relevant files, error messages, and constraints included |
| **Actionability** | Vague desired outcome | General direction clear | Success criteria explicitly stated |

### Recommended Prompt Template

```
[ACTION] [TARGET] in [FILE/SCOPE].
Context: [relevant background]
Files: [specific paths]
Expected: [what success looks like]
Constraints: [what NOT to change]
```

### Before/After Examples

**Vague** (score ~1.5):
> Fix the search feature

**Improved** (score ~4.5):
> Fix the empty results bug in `search/engine.py:execute_query()`. The function returns `[]` when the query contains special characters. Expected: queries like "C++" return valid results. Constraints: don't change the search index format.

---

**Vague** (score ~2.0):
> Add tests

**Improved** (score ~4.5):
> Add unit tests for `core/config.py:load_config()` covering: missing file (should raise FileNotFoundError), invalid YAML (should raise ValueError), and valid config (should return Config object). Place tests in `tests/test_config.py`.

---

**Vague** (score ~1.0):
> Make it faster

**Improved** (score ~4.0):
> Optimize `data/loader.py:load_dataset()` — it currently reads the entire CSV into memory. Use chunked reading with pandas `chunksize=10000`. Expected: memory usage under 500MB for the 2GB dataset. Files: `data/loader.py`.

### Anti-patterns

- **No file paths** — Forces the agent to search, wasting iterations
- **Ambiguous scope** — "Improve error handling" could touch every file
- **Missing success criteria** — Agent can't tell when it's done
- **Implicit context** — Don't assume the agent knows what changed recently

### Using `--files` for Context

Automatically inject file contents as context:

```bash
python3 delegate.py "Fix the validation logic" --files src/validators.py,src/models.py --now
```

### Using `--reflect` and `--lessons`

After tasks complete, review reflection data:

```bash
# View reflection for a specific task
python3 delegate.py --reflect task_1234567890

# View accumulated lessons learned
python3 delegate.py --lessons
```

### Using `--template`

Templates enforce good prompt structure:

```bash
python3 delegate.py --template refactor_method "file_path=foo.py method_name=bar" --now
```

## 📦 Core Components

### 1. Hierarchical Orchestrator

3-tier system with human oversight:

```python
from hierarchical_orchestrator import HierarchicalOrchestrator

orchestrator = HierarchicalOrchestrator()
result = orchestrator.autonomous_workflow("Your task here")

# Returns plan for approval
# After approval, continues with implementation
```

See [HIERARCHICAL_SYSTEM.md](HIERARCHICAL_SYSTEM.md) for details.

### 2. Output Verifier

Automated output validation:

```python
from output_verifier import OutputVerifier

verifier = OutputVerifier("/path/to/project")

# Quick check
result = verifier.quick_check()

# Full test and verification
result = verifier.run_test_and_verify()
```

Configure via `.output_verification.json` in your project:

```json
{
  "project_type": "web_app",
  "output_directory": "dist",
  "expected_files": [
    {
      "name": "bundle.js",
      "type": "javascript",
      "min_size_kb": 10,
      "required": true
    }
  ]
}
```

See [OUTPUT_VERIFIER_README.md](OUTPUT_VERIFIER_README.md) for details.

### 3. PR Helper

Enhanced pull request descriptions:

```python
from pr_helper import PRHelper

helper = PRHelper("/path/to/project")

# Generate enhanced PR body
enhanced_body = helper.generate_enhanced_pr_body(base_description)

# Get audio/file reference for title
file_ref = helper.format_audio_reference_for_pr_title()
pr_title = f"feat: New feature{file_ref}"
```

Configure via `.pr_metadata.json`:

```json
{
  "project_type": "podcast_generation",
  "output_directory": "research_outputs",
  "reference_files": {
    "audio": {
      "pattern": "*.mp3",
      "label": "🎵 Test Audio"
    }
  }
}
```

See [PR_HELPER_README.md](PR_HELPER_README.md) for details.

### 4. Web Interface

Mobile-friendly task management:

- Submit tasks from any device
- Real-time status monitoring
- Secure authentication
- Task history tracking

See [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) for details.

## 🎯 Use Cases

### Software Development

- Feature implementation
- Bug fixes
- Code refactoring
- Test writing
- Documentation generation

### Content Generation

- Podcast generation (see DR_2_Podcast integration)
- Report generation
- Data analysis scripts
- Automation tools

### DevOps

- CI/CD pipeline creation
- Deployment scripts
- Infrastructure as code
- Monitoring setup

## 📚 Documentation

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Hierarchical System](HIERARCHICAL_SYSTEM.md) - Architecture deep dive
- [Interactive Mode Guide](INTERACTIVE_MODE.md) - Programmatic vs Interactive workflows
- [Usage Guide](USAGE_GUIDE.md) - Detailed usage examples
- [Output Verifier](OUTPUT_VERIFIER_README.md) - Automated testing
- [PR Helper](PR_HELPER_README.md) - Enhanced PR descriptions
- [Web Interface](WEB_INTERFACE_GUIDE.md) - Remote task management

## 🛠️ Configuration

### Agent Configuration

`config/agent_config.yaml`:

```yaml
workspace:
  project_root: "/home/user/projects/myproject"
  output_directory: "output"

orchestration:
  logs_path: "logs"
  max_retries: 3
  timeout: 300

llm:
  model_name: "your-model-name"           # Any OpenAI-compatible model
  base_url: "http://localhost:11434/v1"    # Ollama, vLLM, llama.cpp, etc.
  temperature: 0.2
  max_tokens: 4096
  timeout: 300

tools:
  enabled:
    - file_operations
    - code_execution
    - testing
    - search
```

### Project Configuration

#### Output Verification

`.output_verification.json`:

```json
{
  "project_type": "web_app",
  "output_directory": "build",
  "expected_files": [
    {"name": "index.html", "min_size_kb": 1, "required": true},
    {"name": "bundle.js", "min_size_kb": 10, "required": true}
  ],
  "test_command": "npm test",
  "timeout_seconds": 300
}
```

#### PR Metadata

`.pr_metadata.json`:

```json
{
  "project_type": "web_app",
  "output_directory": "build",
  "reference_files": {
    "bundle": {
      "pattern": "*.js",
      "label": "📦 JavaScript Bundle"
    }
  }
}
```

## 🔧 Advanced Features

### Custom Tools

Add your own tools to `tools/`:

```python
@tool
def custom_tool(param: str) -> str:
    """Your custom tool description."""
    # Implementation
    return result
```

### Workflow Hooks

Customize behavior at key points:

```python
def on_plan_created(plan):
    # Custom validation
    pass

def on_implementation_complete(result):
    # Custom checks
    pass
```

### Multi-Project Support

Manage multiple projects:

```bash
# Switch projects
python3 orchestrator.py --project /path/to/project1

# Or set in config
export CODING_AGENT_PROJECT=/path/to/project2
```

## 📊 Monitoring & Logging

All operations are logged to `logs/`:

- `workflow_YYYYMMDD_HHMMSS.json` - Workflow execution logs
- `verification_YYYYMMDD_HHMMSS.json` - Output verification reports
- Task-specific logs with full context

View logs:

```bash
# Latest workflow
cat logs/workflow_*.json | tail -1 | python3 -m json.tool

# Latest verification
cat logs/verification_*.json | tail -1 | python3 -m json.tool
```

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
python3 -m pytest tests/

# Integration tests
python3 -m pytest tests/integration/

# Specific test
python3 test_agent.py
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Works with any OpenAI-compatible LLM backend ([Ollama](https://ollama.ai/), [vLLM](https://github.com/vllm-project/vllm), [llama.cpp](https://github.com/ggerganov/llama.cpp), etc.)
- Tested with Qwen, DeepSeek, CodeStral, and other open-weight models
- Inspired by AutoGPT and similar autonomous agent systems

## 📧 Support

- 🐛 [Report bugs](https://github.com/yourusername/hierarchical-coding-agent/issues)
- 💡 [Request features](https://github.com/yourusername/hierarchical-coding-agent/issues)
- 📖 [Read the docs](https://github.com/yourusername/hierarchical-coding-agent/wiki)

## 🗺️ Roadmap

- [ ] Multi-language support (beyond English)
- [ ] Cloud deployment options
- [ ] VS Code extension
- [ ] GitHub Actions integration
- [ ] Advanced code analysis tools
- [ ] Team collaboration features

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ by the Hierarchical Coding Agent community**
