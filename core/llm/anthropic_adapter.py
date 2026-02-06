"""
Anthropic Claude LLM adapter.
Supports Claude 3 models (Opus, Sonnet, Haiku).
"""
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from .base import BaseLLM, LLMResponse


class AnthropicAdapter(BaseLLM):
    """
    Adapter for Anthropic Claude API.
    Supports Claude 3 models with tool/function calling.
    """

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize Anthropic adapter.

        Args:
            model_name: Claude model name (e.g., 'claude-3-opus-20240229')
            api_key: Anthropic API key (can also be set via ANTHROPIC_API_KEY env var)
            max_retries: Number of retry attempts for failed requests
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)
        self.client = Anthropic(api_key=api_key, max_retries=max_retries)

    def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Claude.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional tool schemas for function calling
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Claude-specific parameters (system, stop_sequences, etc.)

        Returns:
            LLMResponse with generated content

        Raises:
            Exception: If API call fails
        """
        # Separate system message from conversation messages
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content")
            else:
                conversation_messages.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })

        # Build request parameters
        request_params = {
            "model": self.model_name,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        # Add system message if present
        if system_message:
            request_params["system"] = system_message

        # Add tools if provided
        if tools:
            formatted_tools = self.format_tools(tools)
            request_params["tools"] = formatted_tools

        try:
            response = self.client.messages.create(**request_params)

            # Parse response
            content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    # Convert Anthropic tool use to OpenAI-compatible format
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": block.input
                        }
                    })

            return LLMResponse(
                content=content,
                tool_calls=tool_calls if tool_calls else None,
                raw_response=response.model_dump(),
                finish_reason=response.stop_reason,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            )

        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def validate_connection(self) -> bool:
        """
        Validate Anthropic API is accessible.

        Returns:
            True if API key is valid and service is accessible
        """
        try:
            # Try a minimal API call to validate connection
            response = self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return response is not None
        except Exception:
            return False

    def format_tools(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        Convert OpenAI-style tool schemas to Anthropic format.

        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {...}
            }
        }

        Anthropic format:
        {
            "name": "...",
            "description": "...",
            "input_schema": {...}
        }

        Args:
            tools: OpenAI-style tool schemas

        Returns:
            Anthropic-style tool schemas
        """
        if not tools:
            return None

        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                })

        return anthropic_tools

    def __repr__(self) -> str:
        return f"AnthropicAdapter(model={self.model_name})"
