#!/bin/bash
# Start Project Lead model with vLLM
# Reads configuration from .env file (same vars as Pydantic config)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source .env if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✓ Loaded .env"
fi

# Use env vars (matching Pydantic OrchestrationConfig with ORCH_ prefix)
MODEL="${ORCH_LEAD_MODEL:-Qwen/Qwen2.5-32B-Instruct-AWQ}"
PORT="${ORCH_LEAD_PORT:-8000}"
MAX_CTX="${ORCH_LEAD_MAX_CTX:-32768}"
GPU_MEM="${ORCH_LEAD_GPU_MEM:-0.9}"

echo "=================================="
echo "Starting Project Lead (vLLM)"
echo "=================================="
echo "Model:   $MODEL"
echo "Port:    $PORT"
echo "Context: $MAX_CTX tokens"
echo "GPU Mem: $GPU_MEM"
echo ""

# Activate conda environment
source /home/korety/miniconda3/bin/activate podcast_flow

# Set CUDA library path for CUDA 13 (vLLM expects CUDA 12)
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda

# Start vLLM server
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --port "$PORT" \
    --gpu-memory-utilization "$GPU_MEM" \
    --max-model-len "$MAX_CTX" \
    --tensor-parallel-size 1 \
    --dtype auto \
    --trust-remote-code \
    --api-key EMPTY

echo ""
echo "=================================="
echo "✓ Project Lead started"
echo "=================================="
echo "API: http://localhost:${PORT}/v1"
echo "Health: http://localhost:${PORT}/health"
echo "Models: http://localhost:${PORT}/v1/models"
echo ""
