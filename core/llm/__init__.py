"""
LLM abstraction layer for hierarchical coding agent.

Provides a unified interface for different LLM providers:
- Anthropic Claude (via API)
- Ollama (local models like Qwen3-Coder)
- Extensible to other providers (OpenAI, etc.)
"""

from .base import BaseLLM, LLMResponse
from .anthropic_adapter import AnthropicAdapter
from .ollama_adapter import OllamaAdapter

__all__ = [
    "BaseLLM",
    "LLMResponse",
    "AnthropicAdapter",
    "OllamaAdapter",
]
