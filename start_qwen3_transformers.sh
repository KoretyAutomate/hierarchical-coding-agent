#!/bin/bash
# Start Qwen3-Thinking as Project Lead using Transformers

cd ~/coding-agent

echo "Starting Qwen3 Project Lead Server..."
echo "This will take 2-3 minutes to load the model..."
echo ""

python3 qwen3_lead_server.py
