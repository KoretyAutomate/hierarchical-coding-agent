#!/bin/bash
# Start Web Interface for Coding Agent

cd /home/korety/coding-agent

# Set custom credentials (optional - will auto-generate if not set)
# export WEB_USERNAME=your_username
# export WEB_PASSWORD=your_password

# Start on port 8080 (or pass custom port as argument)
PORT=${1:-8080}

echo "Starting Coding Agent Web Interface..."
echo "Port: $PORT"
echo ""

python3 web_interface.py $PORT
