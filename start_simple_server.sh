#!/bin/bash
# Start Qwen Coder with Simple FastAPI Server

cd ~/coding-agent

echo "=================================="
echo "Starting Qwen Coder LLM Server"
echo "=================================="
echo "Port: 8001"
echo "Model: Qwen3-Coder-30B-A3B-Instruct"
echo "Type: MoE (3B active params)"
echo "Memory: Optimized for <40% usage"
echo ""
echo "This will download the model if not cached (~18GB)"
echo ""

python3 simple_llm_server.py
