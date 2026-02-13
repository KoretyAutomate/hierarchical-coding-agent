#!/bin/bash
# Start DeepSeek-R1-Distill-Qwen-32B (Project Lead) with vLLM
# Updated from Qwen3 to DeepSeek-R1 for better context handling

echo "=================================="
echo "Starting Project Lead (DeepSeek-R1)"
echo "=================================="
echo "Model: DeepSeek-R1-Distill-Qwen-32B"
echo "Type: Reasoning model (32B params)"
echo "Purpose: Deep research, planning, hierarchical orchestration"
echo "Port: 8000"
echo "Context: 32k tokens"
echo "Memory: 90% GPU utilization"
echo ""

# Activate conda environment
source /home/korety/miniconda3/bin/activate podcast_flow

# Set CUDA library path for CUDA 13 (vLLM expects CUDA 12)
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda

# Start vLLM server with DeepSeek-R1
python3 -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768 \
    --tensor-parallel-size 1 \
    --dtype auto \
    --trust-remote-code \
    --api-key EMPTY \
    --served-model-name DeepSeek-R1-Lead

echo ""
echo "=================================="
echo "✓ DeepSeek-R1 Project Lead started"
echo "=================================="
echo "API: http://localhost:8000/v1"
echo "Health: http://localhost:8000/health"
echo "Models: http://localhost:8000/v1/models"
echo ""
