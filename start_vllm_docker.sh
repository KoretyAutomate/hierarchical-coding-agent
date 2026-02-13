#!/bin/bash
# Start Project Lead via vLLM in Docker
# Reads configuration from .env file

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Source .env if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    echo "✓ Loaded .env"
fi

MODEL="${ORCH_LEAD_MODEL:-Qwen/Qwen2.5-32B-Instruct-AWQ}"
PORT="${ORCH_LEAD_PORT:-8000}"
MAX_CTX="${ORCH_LEAD_MAX_CTX:-32768}"
GPU_MEM="${ORCH_LEAD_GPU_MEM:-0.9}"

echo "======================================="
echo "Starting Project Lead (vLLM Docker)"
echo "======================================="
echo "Model:   $MODEL"
echo "Port:    $PORT"
echo "Context: $MAX_CTX tokens"
echo "GPU Mem: $GPU_MEM"
echo ""

# Kill any existing container
docker ps -a --filter "name=vllm-server" -q | xargs docker rm -f 2>/dev/null || true

# Start vLLM server in Docker
docker run --runtime nvidia --gpus all \
  --name vllm-server \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p "${PORT}:${PORT}" \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model "$MODEL" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --max-model-len "$MAX_CTX" \
  --gpu-memory-utilization "$GPU_MEM" \
  --dtype auto \
  --trust-remote-code

echo ""
echo "======================================="
echo "✓ Project Lead started"
echo "======================================="
echo "API: http://localhost:${PORT}/v1"
echo "Health: http://localhost:${PORT}/health"
echo "Models: http://localhost:${PORT}/v1/models"
echo "Docker logs: docker logs vllm-server"
echo ""
