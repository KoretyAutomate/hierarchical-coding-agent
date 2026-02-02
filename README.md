# 🤖 Hierarchical Coding Agent

> **Open-source autonomous coding agent with 3-tier hierarchical architecture for software development automation**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

An intelligent, autonomous coding agent system that combines human oversight (Claude Code) with AI-powered project management (Qwen3-32B) and implementation (Qwen3-Coder) for end-to-end software development automation.

## ✨ Features

- 🏗️ **3-Tier Hierarchical Architecture** - PM → Lead → Developer workflow
- 🔄 **Autonomous Workflows** - Plan, implement, review, test automatically
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
│        TIER 2: Project Lead (Qwen3-32B)                     │
│  • Creates implementation plans                              │
│  • Reviews code quality                                      │
│  • Makes technical decisions                                │
└───────────────────────────┬─────────────────────────────────┘
                            │ Assigns work
                            ↓
┌─────────────────────────────────────────────────────────────┐
│     TIER 3: Developer (Qwen3-Coder)                         │
│  • Implements features                                       │
│  • Writes tests                                              │
│  • Follows best practices                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Ollama (for local LLM serving)
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

3. **Start Ollama server**

```bash
./start_ollama_server.sh
```

This will:
- Start Ollama on port 11434
- Pull Qwen3:32b (Project Lead model)
- Pull Qwen3-Coder:latest (Developer model)

4. **Configure your project**

Edit `config/agent_config.yaml`:

```yaml
workspace:
  project_root: "/path/to/your/project"

orchestration:
  logs_path: "logs"

models:
  lead_model: "qwen3:32b"
  coder_model: "qwen3-coder:latest"
```

### Basic Usage

#### Hierarchical Workflow

```bash
# Start autonomous workflow
python3 hierarchical_orchestrator.py "Add error handling to the API"

# The system will:
# 1. Qwen3 Lead creates implementation plan
# 2. You review and approve the plan
# 3. Qwen3-Coder implements the code
# 4. Qwen3 Lead reviews implementation
# 5. Output verification runs automatically
# 6. You approve and create PR
```

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

models:
  lead_model: "qwen3:32b"
  coder_model: "qwen3-coder:latest"
  base_url: "http://localhost:11434/v1"

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

- Built with [Qwen3](https://github.com/QwenLM/Qwen) models
- Powered by [Ollama](https://ollama.ai/) for local LLM serving
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
