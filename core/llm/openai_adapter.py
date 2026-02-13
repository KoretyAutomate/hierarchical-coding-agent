"""
OpenAI-compatible LLM adapter.
Works with vLLM, Ollama, llama.cpp, and any OpenAI-compatible API server.
"""
import logging
import httpx
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from .base import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLM):
    """
    Adapter for OpenAI-compatible API endpoints.
    Works with vLLM, Ollama, llama.cpp server, and similar backends.
    """

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "NA",
        timeout: float = 300.0,
        **kwargs
    ):
        """
        Initialize OpenAI-compatible adapter.

        Args:
            model_name: Model name (e.g., 'Qwen/Qwen2.5-32B-Instruct-AWQ')
            base_url: OpenAI-compatible API base URL
            api_key: API key (use 'NA' for local servers)
            timeout: Request timeout in seconds
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tool schemas for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            Exception: If API call fails
        """
        # Format messages for Ollama
        formatted_messages = self.format_messages(messages)

        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        # Add tools if provided
        if tools:
            formatted_tools = self.format_tools(tools)
            payload["tools"] = formatted_tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            result = response.json()

            # Parse response
            choice = result.get("choices", [{}])[0]
            message = choice.get("message", {})

            return LLMResponse(
                content=message.get("content", ""),
                tool_calls=message.get("tool_calls"),
                raw_response=result,
                finish_reason=choice.get("finish_reason"),
                usage=result.get("usage")
            )

        except httpx.HTTPStatusError as e:
            # Let retryable HTTP errors propagate for tenacity
            logger.warning(f"API error: {e.response.status_code} - {e.response.text[:200]}")
            raise
        except httpx.RequestError as e:
            # Let connection errors propagate for tenacity
            logger.warning(f"Connection error: {e}")
            raise
        except Exception as e:
            raise Exception(f"Generate error: {str(e)}")

    def validate_connection(self) -> bool:
        """
        Validate API service is accessible.

        Returns:
            True if the API server is running and accessible
        """
        try:
            response = self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except Exception:
            return False

    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """OpenAI-compatible format — no transformation needed."""
        return messages

    def format_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """OpenAI-compatible tool format — no transformation needed."""
        return tools

    def list_models(self) -> List[str]:
        """List available models from the API server."""
        try:
            response = self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            models_data = response.json()
            return [model["id"] for model in models_data.get("data", [])]
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
