"""
Post-task self-reflection system for the coding agent.

Evaluates execution quality, scores prompt clarity, and accumulates
lessons learned over time.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.llm import BaseLLM


REFLECTION_PROMPT = """\
You are a coding agent performance analyst. Analyze the following completed task \
and provide a structured reflection.

## Task
Description: {description}
Context: {context}

## Execution Summary
- Iterations used: {iterations} / {max_iterations}
- Outcome: {outcome}
- Tool calls: {tool_call_count}
- Final message: {result_message}

## Tool Call Log
{tool_call_summary}

## Instructions

Analyze this execution and return ONLY valid JSON (no markdown fences) with this structure:
{{
  "execution_analysis": {{
    "what_worked": ["list of things that went well"],
    "what_failed": ["list of things that went wrong"],
    "wasted_steps": ["tool calls that were unnecessary or on wrong targets"],
    "efficiency_score": <1-5 integer>,
    "approach_quality": "<poor|fair|good|excellent>"
  }},
  "prompt_analysis": {{
    "specificity": <1-5: were file paths and targets named?>,
    "scope_clarity": <1-5: was scope clearly bounded?>,
    "context_sufficiency": <1-5: was enough context provided?>,
    "actionability": <1-5: was it clear what to do?>,
    "overall_score": <average of above 4 scores>,
    "issues": ["list of prompt quality issues"],
    "improved_prompt": "A rewritten version of the original prompt that scores 5/5"
  }},
  "lessons_learned": ["actionable lessons for future tasks"],
  "summary": "One-line reflection summary"
}}
"""


class ReflectionEngine:
    """Analyzes completed tasks and accumulates lessons learned."""

    def __init__(self, llm: Optional[BaseLLM], storage_dir: Path):
        self.llm = llm
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def reflect(
        self,
        task_data: Dict[str, Any],
        messages: List[Dict],
        tool_calls: List[Dict],
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Run LLM-based reflection on a completed task.

        Args:
            task_data: Task dict with description, context, status, etc.
            messages: Full conversation history from the agent run.
            tool_calls: List of tool call dicts (tool, arguments, result).
            max_tokens: Max tokens for reflection LLM call.

        Returns:
            Parsed reflection dict, or error dict on failure.
        """
        if self.llm is None:
            raise RuntimeError("LLM required for reflect() — pass llm to constructor")

        # Build tool call summary (compact — no full content)
        tool_summary_lines = []
        for i, tc in enumerate(tool_calls, 1):
            tool_name = tc.get("tool", "unknown")
            args = tc.get("arguments", {})
            # Truncate arg values for token efficiency
            compact_args = {
                k: (v[:80] + "…" if isinstance(v, str) and len(v) > 80 else v)
                for k, v in args.items()
            }
            result_preview = str(tc.get("result", ""))[:100]
            success = "✗" if "Error" in result_preview else "✓"
            tool_summary_lines.append(
                f"{i}. [{success}] {tool_name}({json.dumps(compact_args)}) → {result_preview}"
            )

        tool_call_summary = "\n".join(tool_summary_lines) or "(no tool calls)"

        # Extract task metadata
        result_data = task_data.get("result", {})
        iterations = result_data.get("iterations", 0) if isinstance(result_data, dict) else 0
        result_message = (
            result_data.get("result", "")[:300]
            if isinstance(result_data, dict)
            else str(result_data)[:300]
        )
        outcome = task_data.get("status", "unknown")

        prompt = REFLECTION_PROMPT.format(
            description=task_data.get("description", "N/A"),
            context=task_data.get("context", "None"),
            iterations=iterations,
            max_iterations=task_data.get("result", {}).get("iterations", iterations),
            outcome=outcome,
            tool_call_count=len(tool_calls),
            result_message=result_message,
            tool_call_summary=tool_call_summary,
        )

        # Single LLM call
        response = self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )

        # Parse JSON from response
        raw = response.content or ""
        # Strip markdown fences if present
        if "```" in raw:
            lines = raw.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or not any(line.strip().startswith("```") for _ in [1]):
                    json_lines.append(line)
            raw = "\n".join(json_lines)

        try:
            reflection = json.loads(raw)
        except json.JSONDecodeError:
            reflection = {
                "parse_error": True,
                "raw_response": raw[:500],
                "summary": "Failed to parse reflection JSON",
            }

        # Add metadata
        task_id = task_data.get("task_id", "unknown")
        reflection["_meta"] = {
            "task_id": task_id,
            "task_description": task_data.get("description", ""),
            "status": outcome,
        }

        # Persist
        self._save_reflection(task_id, reflection)
        self._update_lessons(reflection.get("lessons_learned", []))

        return reflection

    def get_reflection(self, task_id: str) -> Optional[Dict]:
        """Load a stored reflection by task ID."""
        path = self.storage_dir / f"{task_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def get_lessons(self, limit: int = 20) -> List[str]:
        """Return accumulated lessons (most recent first)."""
        lessons_path = self.storage_dir / "lessons.json"
        if not lessons_path.exists():
            return []
        with open(lessons_path) as f:
            lessons = json.load(f)
        return lessons[-limit:]

    def aggregate_lessons(self) -> str:
        """Read all reflections, collect unique lessons, return as markdown."""
        all_lessons = set()
        for path in self.storage_dir.glob("task_*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                for lesson in data.get("lessons_learned", []):
                    all_lessons.add(lesson)
            except (json.JSONDecodeError, KeyError):
                continue

        if not all_lessons:
            return "No lessons accumulated yet."

        lines = ["# Lessons Learned", ""]
        for lesson in sorted(all_lessons):
            lines.append(f"- {lesson}")
        return "\n".join(lines)

    def _save_reflection(self, task_id: str, reflection: Dict):
        """Save reflection to per-task file."""
        path = self.storage_dir / f"{task_id}.json"
        with open(path, "w") as f:
            json.dump(reflection, f, indent=2)

    def _update_lessons(self, new_lessons: List[str]):
        """Append new lessons to the aggregated lessons file, deduped, capped at 50."""
        lessons_path = self.storage_dir / "lessons.json"
        existing = []
        if lessons_path.exists():
            try:
                with open(lessons_path) as f:
                    existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

        existing_set = set(existing)
        for lesson in new_lessons:
            if lesson not in existing_set:
                existing.append(lesson)
                existing_set.add(lesson)

        # Cap at 50 — keep most recent
        if len(existing) > 50:
            existing = existing[-50:]

        with open(lessons_path, "w") as f:
            json.dump(existing, f, indent=2)
