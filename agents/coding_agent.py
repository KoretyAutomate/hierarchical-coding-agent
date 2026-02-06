"""
Main Coding Agent that uses LLM abstraction layer.
Supports multiple LLM providers (Ollama, Anthropic, etc.)
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))

from tools.coding_tools import CodingTools, get_tool_schemas
from core.llm import BaseLLM, LLMResponse


class CodingAgent:
    """Autonomous coding agent powered by pluggable LLM backends"""

    def __init__(
        self,
        llm: BaseLLM,
        workspace_root: str,
        max_iterations: int = 10,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        use_sandbox: bool = False,
        sandbox_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize coding agent with LLM adapter and optional sandbox.

        Args:
            llm: LLM adapter instance (OllamaAdapter, AnthropicAdapter, etc.)
            workspace_root: Root directory of the project workspace
            max_iterations: Maximum iterations for task execution
            temperature: LLM sampling temperature
            max_tokens: Maximum tokens to generate
            use_sandbox: Whether to use Docker sandbox for code execution
            sandbox_config: Optional sandbox configuration
        """
        self.llm = llm
        self.workspace_root = workspace_root
        self.tools = CodingTools(
            self.workspace_root,
            use_sandbox=use_sandbox,
            sandbox_config=sandbox_config
        )
        self.conversation_history = []
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _call_llm(
        self,
        messages: List[Dict],
        tools: Optional[List] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Call the LLM using the abstraction layer.

        Args:
            messages: Conversation messages
            tools: Optional tool schemas
            **kwargs: Additional LLM-specific parameters

        Returns:
            LLMResponse object

        Raises:
            Exception: If LLM call fails
        """
        try:
            response = self.llm.generate(
                messages=messages,
                tools=tools,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool call"""
        tool_method = getattr(self.tools, tool_name, None)
        if not tool_method:
            return f"Error: Tool {tool_name} not found"

        try:
            result = tool_method(**arguments)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run_task(self, task_description: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a coding task autonomously
        Returns: {"success": bool, "result": str, "iterations": int, "tool_calls": List}
        """
        print(f"\n{'='*60}")
        print(f"CODING AGENT TASK: {task_description}")
        print(f"{'='*60}\n")

        # Initialize conversation
        system_prompt = {
            "role": "system",
            "content": (
                "You are a senior software engineer working on a Python project. "
                "You have access to tools for reading, writing, and editing files, "
                "executing code, running tests, and searching code.\n\n"
                "When given a task:\n"
                "1. First understand the current codebase by reading relevant files\n"
                "2. Plan your approach\n"
                "3. Implement the solution using available tools\n"
                "4. Test your changes\n"
                "5. Report completion\n\n"
                "Always use tools to accomplish tasks. Be thorough but efficient.\n"
                f"Workspace root: {self.workspace_root}"
            )
        }

        user_message = {"role": "user", "content": task_description}
        if context:
            user_message["content"] = f"Context:\n{context}\n\nTask:\n{task_description}"

        messages = [system_prompt, user_message]
        tool_schemas = get_tool_schemas()

        iterations = 0
        all_tool_calls = []

        while iterations < self.max_iterations:
            iterations += 1
            print(f"\n--- Iteration {iterations}/{self.max_iterations} ---")

            # Call LLM
            try:
                response = self._call_llm(messages, tools=tool_schemas)
            except Exception as e:
                return {
                    "success": False,
                    "result": f"LLM Error: {str(e)}",
                    "iterations": iterations,
                    "tool_calls": all_tool_calls
                }

            # Build assistant message from LLMResponse
            assistant_message = {
                "role": "assistant",
                "content": response.content or ""
            }

            # Add tool calls if present
            if response.tool_calls:
                assistant_message["tool_calls"] = response.tool_calls

            messages.append(assistant_message)

            # Check for tool calls
            tool_calls = response.tool_calls or []

            if not tool_calls:
                # No more tool calls - agent is done
                final_content = response.content or "Task completed"
                print(f"\n✓ Agent finished: {final_content}")

                return {
                    "success": True,
                    "result": final_content,
                    "iterations": iterations,
                    "tool_calls": all_tool_calls,
                    "usage": response.usage
                }

            # Execute tool calls
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                tool_name = func.get("name")

                # Handle arguments - may already be dict or JSON string
                arguments = func.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                print(f"  🔧 Calling: {tool_name}({arguments})")

                # Execute tool
                result = self._execute_tool(tool_name, arguments)
                print(f"  ✓ Result: {result[:200]}..." if len(result) > 200 else f"  ✓ Result: {result}")

                all_tool_calls.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result
                })

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "name": tool_name,
                    "content": result
                })

        # Max iterations reached
        return {
            "success": False,
            "result": "Max iterations reached without completion",
            "iterations": iterations,
            "tool_calls": all_tool_calls
        }


if __name__ == "__main__":
    # Test the agent with new architecture
    from core.llm import OllamaAdapter
    from core.config import get_config

    # Load configuration
    config = get_config()

    # Create LLM adapter
    if config.llm.provider == "ollama":
        llm = OllamaAdapter(
            model_name=config.llm.ollama_model,
            base_url=config.llm.ollama_base_url,
            timeout=config.llm.ollama_timeout
        )
    else:
        from core.llm import AnthropicAdapter
        llm = AnthropicAdapter(
            model_name=config.llm.anthropic_model,
            api_key=config.llm.anthropic_api_key
        )

    # Create agent
    agent = CodingAgent(
        llm=llm,
        workspace_root=str(config.workspace.project_root),
        max_iterations=config.orchestration.max_iterations,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens
    )

    # Test task
    result = agent.run_task(
        "List files in the current workspace and identify Python files"
    )

    print("\n" + "="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
