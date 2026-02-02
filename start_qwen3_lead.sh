#!/bin/bash
# Start Qwen3-Next-80B-A3B-Thinking (Project Lead) with vLLM

echo "=================================="
echo "Starting Qwen3 Project Lead"
echo "=================================="
echo "Model: Qwen3-Next-80B-A3B-Thinking-AWQ-4bit"
echo "Type: MoE (80B total, 3B active)"
echo "Quantization: AWQ 4-bit"
echo "Port: 8000"
echo "Memory: Capped at 50%"
echo ""

# Start vLLM server
python3 -m vllm.entrypoints.openai.api_server \
    --model cyankiwi/Qwen3-Next-80B-A3B-Thinking-AWQ-4bit \
    --port 8000 \
    --gpu-memory-utilization 0.5 \
    --max-model-len 8192 \
    --tensor-parallel-size 1 \
    --dtype auto \
    --quantization awq \
    --api-key NA \
    --served-model-name Qwen3-Lead

echo "Qwen3 Project Lead started on http://localhost:8000"
