#!/bin/bash
# Start Ollama server for Qwen3-Coder

echo "=================================="
echo "Starting Ollama Server"
echo "=================================="
echo "Port: 11434 (Ollama default)"
echo "Model: qwen3-coder (will be pulled if needed)"
echo "Memory: GGUF quantization for minimal VRAM"
echo ""

# Check if Ollama service is running
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama is already running"
else
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Pull qwen3-coder model if not already available
echo "Checking for qwen3-coder model..."
if ! ollama list | grep -q "qwen3-coder"; then
    echo "Pulling qwen3-coder model (this may take a few minutes)..."
    ollama pull qwen3-coder
else
    echo "✓ qwen3-coder model already available"
fi

echo ""
echo "=================================="
echo "Ollama server ready on port 11434"
echo "Model: qwen3-coder"
echo "API: http://localhost:11434/v1"
echo "=================================="
