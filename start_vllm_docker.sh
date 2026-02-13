#!/bin/bash
# vLLM Docker Server Startup Script for Coding Agent
# Model: DeepSeek-R1-Distill-Qwen-32B (Project Lead)
# Port: 8000

echo "======================================="
echo "Starting Project Lead (DeepSeek-R1 Docker)"
echo "======================================="
echo "Model: DeepSeek-R1-Distill-Qwen-32B"
echo "Type: Reasoning model (32B params)"
echo "Purpose: Deep research, planning, hierarchical orchestration"
echo "Port: 8000"
echo "Context: 32k tokens"
echo "Memory: 90% GPU utilization"
echo ""

# Kill any existing container
docker ps -a --filter "name=vllm-server" -q | xargs docker rm -f 2>/dev/null || true

# Start vLLM server in Docker
docker run --runtime nvidia --gpus all \
  --name vllm-server \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8000:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.9 \
  --dtype auto \
  --trust-remote-code

echo ""
echo "======================================="
echo "✓ DeepSeek-R1 Project Lead started"
echo "======================================="
echo "API: http://localhost:8000/v1"
echo "Health: http://localhost:8000/health"
echo "Models: http://localhost:8000/v1/models"
echo "Docker logs: docker logs vllm-server"
echo ""
