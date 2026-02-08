# vLLM Migration for Coding Agent

**Date**: 2026-02-07
**Purpose**: Migrate Project Lead LLM from Qwen3 (Ollama) to DeepSeek-R1 (vLLM) for better reasoning and context handling

---

## Summary of Changes

The coding agent now uses a **hierarchical dual-backend setup**:
- **Project Lead**: DeepSeek-R1-Distill-Qwen-32B via vLLM (port 8000)
- **Project Member (Coder)**: Qwen3-coder-next via Ollama (port 11434)

This separation allows the planning/review agent to use a more powerful reasoning model while keeping the implementation agent on the efficient local Ollama setup.

---

## Files Modified

### 1. `/home/korety/coding-agent/core/config.py`

**Changes**:
- Updated `lead_model` from `"frob/qwen3-coder-next"` to `"deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"`
- Added new field `lead_base_url` = `"http://localhost:8000/v1"` to `OrchestrationConfig`
- `member_model` remains `"frob/qwen3-coder-next"` (uses Ollama on port 11434)

**Lines Changed**: 177-183

```python
# Before:
lead_model: str = Field(
    default="frob/qwen3-coder-next",
    description="Project Lead model (planning and review)"
)

# After:
lead_model: str = Field(
    default="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    description="Project Lead model (planning and review)"
)
lead_base_url: str = Field(
    default="http://localhost:8000/v1",
    description="Base URL for Lead model (vLLM server)"
)
```

### 2. `/home/korety/coding-agent/hierarchical_orchestrator.py`

**Changes**:
- Updated `_create_default_lead_llm()` method to use `config.orchestration.lead_base_url` instead of `config.llm.ollama_base_url`
- Added comment explaining the separate base URL for vLLM support

**Lines Changed**: 86-98

```python
# Before:
return OllamaAdapter(
    model_name=self.config.orchestration.lead_model,
    base_url=self.config.llm.ollama_base_url,  # port 11434
    timeout=self.config.llm.ollama_timeout
)

# After:
return OllamaAdapter(
    model_name=self.config.orchestration.lead_model,
    base_url=self.config.orchestration.lead_base_url,  # port 8000 for vLLM
    timeout=self.config.llm.ollama_timeout
)
```

### 3. `/home/korety/coding-agent/start_qwen3_lead.sh`

**Changes**:
- Completely replaced with vLLM startup script for DeepSeek-R1
- Updated port from 11434 to 8000
- Changed from `ollama serve` to `vllm.entrypoints.openai.api_server`

---

## Configuration Overview

| Component | Model | Backend | Port | Base URL |
|-----------|-------|---------|------|----------|
| Project Lead | DeepSeek-R1-Distill-Qwen-32B | vLLM | 8000 | http://localhost:8000/v1 |
| Project Member (Coder) | frob/qwen3-coder-next | Ollama | 11434 | http://localhost:11434/v1 |

---

## How It Works

1. **Configuration Loading**: `core/config.py` defines separate settings for lead and member models
2. **LLM Initialization**: `hierarchical_orchestrator.py` creates two LLM adapters:
   - Lead LLM → uses `lead_base_url` (vLLM on port 8000)
   - Member LLM → uses `ollama_base_url` (Ollama on port 11434)
3. **Workflow Execution**:
   - Stage 1 (Planning): Lead LLM via vLLM
   - Stage 2 (Implementation): Member LLM via Ollama
   - Stage 3 (Review): Lead LLM via vLLM

---

## Starting the Coding Agent

### 1. Start vLLM Server (Project Lead)

```bash
cd /home/korety/coding-agent
./start_qwen3_lead.sh
```

This starts DeepSeek-R1 on port 8000.

### 2. Start Ollama (Project Member)

```bash
ollama serve
```

This starts Ollama on port 11434 (default).

### 3. Verify Both Services

```bash
# Check vLLM (Lead)
curl http://localhost:8000/v1/models

# Check Ollama (Member)
curl http://localhost:11434/v1/models
```

### 4. Run the Orchestrator

```bash
cd /home/korety/coding-agent
python3 hierarchical_orchestrator.py "Your coding task here"
```

---

## Environment Variables (Optional)

You can override defaults using environment variables:

```bash
# Override lead model configuration
export ORCH_LEAD_MODEL="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
export ORCH_LEAD_BASE_URL="http://localhost:8000/v1"

# Override member model configuration
export ORCH_MEMBER_MODEL="frob/qwen3-coder-next"
export LLM_OLLAMA_BASE_URL="http://localhost:11434/v1"
```

---

## Troubleshooting

### vLLM Server Won't Start

**Issue**: Port 8000 already in use
**Solution**: Check if vLLM is already running
```bash
lsof -i :8000
# If running, kill it or use existing server
pkill -f "vllm.entrypoints.openai.api_server"
```

### Lead LLM Connection Error

**Issue**: `Connection refused to localhost:8000`
**Solution**: Ensure vLLM server is running
```bash
./start_qwen3_lead.sh
```

### Member LLM Connection Error

**Issue**: `Connection refused to localhost:11434`
**Solution**: Ensure Ollama is running
```bash
ollama serve
```

### Wrong Model Being Used

**Issue**: Still using old Qwen3 for planning
**Solution**:
1. Verify config changes: `cat core/config.py | grep -A5 "lead_model"`
2. Check orchestrator is using new config
3. Restart both servers and orchestrator

---

## Benefits of This Setup

✅ **Better Reasoning**: DeepSeek-R1 excels at planning and code review
✅ **Better Context Handling**: 32k context window vs Ollama limitations
✅ **Efficient Implementation**: Ollama remains fast for code generation
✅ **Independent Scaling**: Can tune each backend separately
✅ **Cost Effective**: Only use powerful model where needed (planning/review)

---

## Model Information

### DeepSeek-R1-Distill-Qwen-32B (Project Lead)
- **Type**: Reasoning model (distilled from DeepSeek-R1)
- **Size**: ~32B parameters (~60GB disk space)
- **Context**: 32,768 tokens
- **Strengths**: Multi-step reasoning, planning, code review
- **Use Case**: Planning implementation strategies, reviewing code quality

### Qwen3-Coder-Next (Project Member)
- **Type**: Code generation model
- **Size**: Quantized (GGUF format)
- **Context**: Varies by quantization
- **Strengths**: Fast code generation, efficient
- **Use Case**: Implementing plans, writing code

---

## Next Steps

1. ✅ Model downloaded (8/8 shards complete)
2. ✅ Configuration updated
3. ✅ Orchestrator updated
4. ✅ Startup script created
5. ⏭️ Start vLLM server: `./start_qwen3_lead.sh`
6. ⏭️ Start Ollama: `ollama serve`
7. ⏭️ Test hierarchical orchestrator
8. ⏭️ Monitor performance and context handling

---

## Rollback Instructions

If you need to revert to the old setup:

1. **Revert config.py**:
```python
lead_model: str = Field(
    default="frob/qwen3-coder-next",
    description="Project Lead model (planning and review)"
)
# Remove lead_base_url field
```

2. **Revert hierarchical_orchestrator.py**:
```python
base_url=self.config.llm.ollama_base_url,  # Back to port 11434
```

3. **Revert start script**: Replace with original Ollama startup

4. **Restart services**:
```bash
pkill -f vllm
ollama serve
```

---

## Support

**Issues**: Create issue in coding-agent repository
**vLLM Docs**: https://docs.vllm.ai/
**DeepSeek-R1**: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
