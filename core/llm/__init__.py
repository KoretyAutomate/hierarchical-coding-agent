"""
LLM abstraction layer for hierarchical coding agent.

Provides a unified interface for different LLM providers:
- OpenAI-compatible APIs (vLLM, Ollama, llama.cpp, etc.)
- Anthropic Claude (via API)
"""

from .base import BaseLLM, LLMResponse
from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter

# Backwards compatibility alias
OllamaAdapter = OpenAIAdapter

__all__ = [
    "BaseLLM",
    "LLMResponse",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "OllamaAdapter",
]
