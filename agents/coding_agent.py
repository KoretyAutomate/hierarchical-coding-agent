"""
Main Coding Agent that uses Qwen3-Coder-14B
"""
import json
import httpx
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))

from tools.coding_tools import CodingTools, get_tool_schemas


class CodingAgent:
    """Autonomous coding agent powered by Qwen3-Coder-14B"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config['llm']
        self.workspace_root = config['workspace']['project_root']
        self.tools = CodingTools(self.workspace_root)
        self.conversation_history = []
        self.max_iterations = 10

    def _call_llm(self, messages: List[Dict], tools: Optional[List] = None) -> Dict:
        """Call the LLM API"""
        payload = {
            "model": self.llm_config['model_name'].split('/')[-1],
            "messages": messages,
            "temperature": self.llm_config['temperature'],
            "max_tokens": self.llm_config['max_tokens'],
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            response = httpx.post(
                f"{self.llm_config['base_url']}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.llm_config['api_key']}"},
                timeout=self.llm_config['timeout']
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

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
            response = self._call_llm(messages, tools=tool_schemas)

            if "error" in response:
                return {
                    "success": False,
                    "result": f"LLM Error: {response['error']}",
                    "iterations": iterations,
                    "tool_calls": all_tool_calls
                }

            # Get assistant message
            choice = response.get("choices", [{}])[0]
            assistant_message = choice.get("message", {})
            messages.append(assistant_message)

            # Check for tool calls
            tool_calls = assistant_message.get("tool_calls", [])

            if not tool_calls:
                # No more tool calls - agent is done
                final_content = assistant_message.get("content", "Task completed")
                print(f"\n✓ Agent finished: {final_content}")

                return {
                    "success": True,
                    "result": final_content,
                    "iterations": iterations,
                    "tool_calls": all_tool_calls
                }

            # Execute tool calls
            for tool_call in tool_calls:
                func = tool_call.get("function", {})
                tool_name = func.get("name")
                try:
                    arguments = json.loads(func.get("arguments", "{}"))
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


def load_config(config_path: str = "/home/korety/coding-agent/config/agent_config.yaml") -> Dict:
    """Load configuration from YAML"""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # Test the agent
    import yaml

    config_path = Path(__file__).parent.parent / "config" / "agent_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    agent = CodingAgent(config)

    # Test task
    result = agent.run_task(
        "Read the podcast_crew.py file and summarize its main components"
    )

    print("\n" + "="*60)
    print("FINAL RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2))
