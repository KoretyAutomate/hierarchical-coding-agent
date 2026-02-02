#!/bin/bash
# Start Qwen3-Coder-14B with vLLM on port 8001

echo "Starting Qwen3-Coder-14B inference server..."
echo "Port: 8001 (separate from main Qwen 3 on 8000)"
echo "GPU Memory: 85% utilization"
echo ""

# Check if model exists locally
MODEL_PATH="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3-Coder-14B-Instruct"

if [ ! -d "$MODEL_PATH" ]; then
    echo "Model not found locally. Downloading Qwen3-Coder-14B-Instruct..."
    echo "This may take some time (~30GB download)..."
fi

# Start vLLM server
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-Coder-14B-Instruct \
    --port 8001 \
    --gpu-memory-utilization 0.85 \
    --max-model-len 8192 \
    --tensor-parallel-size 1 \
    --dtype auto \
    --api-key NA \
    --served-model-name Qwen3-Coder-14B

# Note: Add --quantization awq if you need to reduce memory usage further
