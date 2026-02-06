"""
Base LLM abstraction interface.
All LLM adapters must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response format."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.

    All LLM adapters (Anthropic, Ollama, OpenAI, etc.) must implement this interface
    to ensure consistent behavior across the application.
    """

    def __init__(self, model_name: str, **kwargs):
        """
        Initialize the LLM adapter.

        Args:
            model_name: The model identifier (e.g., 'claude-3-opus', 'qwen3-coder')
            **kwargs: Provider-specific configuration options
        """
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            tools: Optional list of tool schemas for function calling
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object with standardized response data

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the LLM service is accessible.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Format messages for this specific provider.
        Can be overridden by subclasses if provider requires special formatting.

        Args:
            messages: Standard message format

        Returns:
            Provider-specific message format
        """
        return messages

    def format_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[Any]:
        """
        Format tools for this specific provider.
        Can be overridden by subclasses if provider requires special formatting.

        Args:
            tools: Standard tool schema format

        Returns:
            Provider-specific tool format
        """
        return tools

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"
