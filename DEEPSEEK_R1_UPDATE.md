# DeepSeek-R1 Update - Coding Agent

**Date**: 2026-02-07
**Previous Setup**: Attempted vLLM with DeepSeek-R1-Distill-Qwen-32B (failed due to ARM64+CUDA13 issues)
**New Setup**: Ollama with DeepSeek-R1:32b (131k context)

---

## Changes Made

### core/config.py

**OrchestrationConfig (Lines 173-184)**:
```python
# Before (vLLM):
lead_model: str = Field(
    default="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    description="Project Lead model (planning and review)"
)
lead_base_url: str = Field(
    default="http://localhost:8000/v1",
    description="Base URL for Lead model (vLLM server)"
)

# After (Ollama):
lead_model: str = Field(
    default="deepseek-r1:32b",
    description="Project Lead model (planning and review)"
)
lead_base_url: str = Field(
    default="http://localhost:11434/v1",
    description="Base URL for Lead model (Ollama server)"
)
```

**No changes to `member_model`** - stays as `frob/qwen3-coder-next` (Ollama)

---

## Architecture

### Hierarchical Setup

| Component | Model | Backend | Port | Context |
|-----------|-------|---------|------|---------|
| **Project Lead** (Planning/Review) | DeepSeek-R1:32b | Ollama | 11434 | 131k |
| **Project Member** (Coding) | Qwen3-coder-next 79B | Ollama | 11434 | 262k |

**Both use the same Ollama server** - simpler than split vLLM+Ollama setup.

---

## Why This Setup

### Project Lead: DeepSeek-R1:32b
- ✅ **Reasoning-focused**: Better for planning and code review
- ✅ **131k context**: Handles large code contexts
- ✅ **Smaller**: 32B params, faster responses
- ✅ **Research quality**: Excellent for architectural decisions

### Project Member: Qwen3-coder-next 79B
- ✅ **Coding-focused**: Specialized for implementation
- ✅ **262k context**: Can handle massive codebases
- ✅ **Proven**: Already installed and working

---

## Running the Orchestrator

### 1. Ensure Ollama is Running

```bash
ollama serve
```

### 2. Verify Both Models

```bash
ollama list | grep -E "deepseek-r1|qwen3-coder"
# Should show both models
```

### 3. Run Orchestrator

```bash
cd /home/korety/coding-agent
python3 hierarchical_orchestrator.py "Your coding task here"
```

---

## Startup Scripts

### Old Scripts (vLLM - No Longer Used)
- `start_lead_vllm.sh` - vLLM startup (deprecated)
- `start_vllm_docker.sh` - Docker vLLM (deprecated)

### Current Setup
**No separate startup needed** - Both models use same Ollama server:
```bash
ollama serve  # Serves both lead and member models
```

---

## Expected Behavior

### Planning Phase (Project Lead)
- Uses DeepSeek-R1:32b
- Better architectural reasoning
- More thoughtful code reviews
- 131k context for large plans

### Implementation Phase (Project Member)
- Uses Qwen3-coder-next 79B
- Fast, accurate code generation
- 262k context for large files
- Specialized coding capabilities

---

## Performance Expectations

### DeepSeek-R1:32b (Lead)
- **Speed**: ~25-40 tokens/sec
- **Use case**: Planning, reviews (less frequent)
- **Quality**: Excellent reasoning

### Qwen3-coder-next 79B (Member)
- **Speed**: ~20-35 tokens/sec
- **Use case**: Implementation (frequent)
- **Quality**: Excellent coding

---

## Troubleshooting

### Lead Model Issues

**Check Ollama connection**:
```bash
curl http://localhost:11434/v1/models
```

**Verify lead model loaded**:
```bash
ollama list | grep deepseek-r1
```

**Test lead model**:
```bash
ollama run deepseek-r1:32b "Explain the benefits of test-driven development"
```

### Configuration Override

Can override via environment variables:
```bash
export ORCH_LEAD_MODEL="deepseek-r1:32b"
export ORCH_LEAD_BASE_URL="http://localhost:11434/v1"
export ORCH_MEMBER_MODEL="frob/qwen3-coder-next"
```

---

## Alternative Lead Models

If DeepSeek-R1:32b doesn't meet needs:

### Faster (14B)
```python
lead_model: str = Field(default="deepseek-r1:14b")
# Still 131k context, faster responses
```

### Best Quality (70B)
```python
lead_model: str = Field(default="deepseek-r1:70b")
# ~40GB, best reasoning, 131k context
```

### Different Model
```python
lead_model: str = Field(default="qwen2.5:32b")
# Non-reasoning model, might be faster
```

---

## Why Not vLLM?

Attempted but failed due to:
1. ❌ PyTorch 2.9.1 for ARM64 is CPU-only (no CUDA support)
2. ❌ Docker vLLM has CUDA 12 vs host CUDA 13 mismatch
3. ❌ Building PyTorch from source would take 4-6 hours

**Ollama works perfectly** on ARM64 + Grace Blackwell architecture.

---

## Benefits of Current Setup

1. ✅ **Single backend**: Both models use Ollama (simpler)
2. ✅ **No CUDA issues**: Ollama handles ARM64 natively
3. ✅ **Proven stable**: Ollama reliable on this hardware
4. ✅ **Good separation**: Lead (reasoning) vs Member (coding)
5. ✅ **Large contexts**: 131k + 262k sufficient for any project

---

## Testing Recommendations

### Test 1: Simple Task
```bash
python3 hierarchical_orchestrator.py "Add error handling to the search function"
```
- Should complete both planning and implementation

### Test 2: Complex Task
```bash
python3 hierarchical_orchestrator.py "Refactor the authentication system to use JWT tokens"
```
- Tests DeepSeek-R1's planning capabilities
- Tests Project Member's implementation skills

### Test 3: Large Context
```bash
python3 hierarchical_orchestrator.py "Review and improve all API endpoints in the project"
```
- Tests 131k context window for planning
- Tests 262k context window for implementation

---

## Support

**Issue Tracker**: https://github.com/KoretyAutomate/hierarchical-coding-agent/issues
**DeepSeek-R1**: https://ollama.com/library/deepseek-r1
**Ollama Docs**: https://github.com/ollama/ollama
