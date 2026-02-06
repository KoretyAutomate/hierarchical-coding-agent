# Secure sandbox environment for code execution
# Based on official Python slim image for minimal attack surface
FROM python:3.11-slim

# Set labels for identification
LABEL maintainer="Hierarchical Coding Agent"
LABEL description="Secure sandbox for code execution"
LABEL version="1.0"

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash sandbox && \
    mkdir -p /workspace && \
    chown sandbox:sandbox /workspace

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Switch to non-root user
USER sandbox

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/home/sandbox

# Default command (can be overridden)
CMD ["/bin/bash"]
