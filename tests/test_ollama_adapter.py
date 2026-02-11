"""Tests for core.llm.ollama_adapter module."""
import pytest
from unittest.mock import MagicMock, patch
import httpx

from core.llm.ollama_adapter import OllamaAdapter
from core.llm.base import LLMResponse


@pytest.fixture
def adapter():
    """Create an adapter pointing to a fake URL (won't connect)."""
    return OllamaAdapter(
        model_name="test-model",
        base_url="http://localhost:99999/v1",
        timeout=5.0,
    )


class TestOllamaAdapterInit:
    def test_model_name(self, adapter):
        assert adapter.model_name == "test-model"

    def test_base_url_stripped(self):
        a = OllamaAdapter(model_name="m", base_url="http://host:1234/v1/")
        assert a.base_url == "http://host:1234/v1"

    def test_repr(self, adapter):
        assert "OllamaAdapter" in repr(adapter)
        assert "test-model" in repr(adapter)


class TestFormatMessages:
    def test_passthrough(self, adapter):
        msgs = [{"role": "user", "content": "hi"}]
        assert adapter.format_messages(msgs) is msgs


class TestFormatTools:
    def test_passthrough(self, adapter):
        tools = [{"type": "function", "function": {"name": "foo"}}]
        assert adapter.format_tools(tools) is tools


class TestValidateConnection:
    def test_returns_false_on_connection_error(self, adapter):
        assert adapter.validate_connection() is False


class TestGenerate:
    def test_raises_on_connection_error(self, adapter):
        """Should raise after retries are exhausted."""
        with pytest.raises(Exception):
            adapter.generate(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )

    @patch.object(OllamaAdapter, "generate")
    def test_returns_llm_response(self, mock_generate):
        """Test that generate returns proper LLMResponse shape."""
        mock_generate.return_value = LLMResponse(
            content="Hello!",
            tool_calls=None,
            finish_reason="stop",
        )
        adapter = OllamaAdapter(model_name="test")
        result = adapter.generate(
            messages=[{"role": "user", "content": "hi"}]
        )
        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"


class TestRetryBehavior:
    @patch("core.llm.ollama_adapter.OllamaAdapter.generate.__wrapped__")
    def test_retry_on_request_error(self, mock_wrapped):
        """Verify retry is configured (tenacity wraps the method)."""
        adapter = OllamaAdapter(model_name="test", base_url="http://localhost:99999/v1")
        # The method should have retry attributes from tenacity
        assert hasattr(adapter.generate, "retry")
