# Sandbox Environment for Code Execution

This directory contains the Docker configuration for secure, isolated code execution.

## Overview

The sandbox provides:
- **Isolation**: Code runs in ephemeral containers, never on the host
- **Security**: Non-root user, minimal attack surface
- **Resource Limits**: CPU, memory, and timeout controls
- **Clean State**: Each execution starts fresh

## Files

- `Dockerfile` - Container image definition
- `requirements.txt` - Python dependencies for sandbox
- `README.md` - This file

## Building the Image

```bash
cd sandbox
docker build -t coding-agent-sandbox:latest .
```

## Manual Testing

```bash
# Run interactive shell
docker run --rm -it coding-agent-sandbox:latest /bin/bash

# Execute Python code
docker run --rm coding-agent-sandbox:latest python3 -c "print('Hello from sandbox!')"

# Run with workspace mount
docker run --rm -v /path/to/workspace:/workspace coding-agent-sandbox:latest python3 script.py
```

## Security Features

1. **Non-root User**: Runs as `sandbox` user (UID 1000)
2. **Minimal Base**: Uses Python slim image
3. **No Network (optional)**: Can disable network access
4. **Read-only Filesystem (optional)**: Can mount workspace read-only
5. **Resource Limits**: CPU, memory, and time limits enforced

## Resource Limits

Default limits (configurable in config):
- **Memory**: 512MB
- **CPU**: 1 core
- **Timeout**: 300 seconds (5 minutes)
- **Storage**: Ephemeral (destroyed after execution)

## Usage from Code

The sandbox is automatically used by `CodingTools` when enabled in configuration:

```python
# In .env or config
SECURITY_ENABLE_SANDBOX=true
SECURITY_DOCKER_IMAGE=coding-agent-sandbox:latest
SECURITY_MAX_EXECUTION_TIME=300
```

## Updating Dependencies

To add new dependencies to the sandbox:

1. Edit `requirements.txt`
2. Rebuild the image: `docker build -t coding-agent-sandbox:latest .`
3. The orchestrator will use the updated image

## Troubleshooting

### Image not found
```bash
docker build -t coding-agent-sandbox:latest .
```

### Permission denied
Ensure Docker is running and your user has permissions:
```bash
sudo usermod -aG docker $USER
```

### Container cleanup
Remove all stopped containers:
```bash
docker container prune -f
```

### Image cleanup
Remove old images:
```bash
docker image prune -a -f
```
