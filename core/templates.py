"""
Task template system for the coding agent.

Templates are YAML files that define reusable task descriptions with variables.
"""
from pathlib import Path
from typing import Dict, List, Optional
import yaml


# Default templates directory (sibling to this file's parent)
DEFAULT_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class TemplateVariable:
    """A variable in a task template."""

    def __init__(self, name: str, required: bool = True, default: str = "", description: str = ""):
        self.name = name
        self.required = required
        self.default = default
        self.description = description


class TaskTemplate:
    """
    A reusable task template loaded from YAML.

    YAML format:
        name: refactor_method
        description: Refactor a method for readability
        variables:
          - {name: file_path, required: true, description: "File containing the method"}
          - {name: method_name, required: true, description: "Method to refactor"}
          - {name: reason, required: false, default: "improve code quality"}
        template: |
          Refactor `{method_name}` in `{file_path}`. Reason: {reason}.
          Read current implementation, refactor for readability, run tests.
    """

    def __init__(self, name: str, template: str, variables: List[TemplateVariable],
                 description: str = ""):
        self.name = name
        self.template = template
        self.variables = variables
        self.description = description

    @classmethod
    def load(cls, name: str, templates_dir: Path = None) -> "TaskTemplate":
        """
        Load a template by name from the templates directory.

        Args:
            name: Template name (without .yaml extension)
            templates_dir: Override templates directory

        Returns:
            TaskTemplate instance

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template YAML is invalid
        """
        tdir = templates_dir or DEFAULT_TEMPLATES_DIR
        path = tdir / f"{name}.yaml"

        if not path.exists():
            available = [p.stem for p in tdir.glob("*.yaml")] if tdir.exists() else []
            raise FileNotFoundError(
                f"Template '{name}' not found at {path}. "
                f"Available: {available}"
            )

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict) or 'template' not in data:
            raise ValueError(f"Template '{name}' must contain a 'template' field")

        variables = []
        for v in data.get('variables', []):
            variables.append(TemplateVariable(
                name=v['name'],
                required=v.get('required', True),
                default=v.get('default', ''),
                description=v.get('description', ''),
            ))

        return cls(
            name=data.get('name', name),
            template=data['template'],
            variables=variables,
            description=data.get('description', ''),
        )

    def render(self, variables: Dict[str, str]) -> str:
        """
        Render the template with provided variables.

        Args:
            variables: Dict of variable_name -> value

        Returns:
            Rendered task description string

        Raises:
            ValueError: If required variables are missing
        """
        # Build final values with defaults
        values = {}
        missing = []
        for v in self.variables:
            if v.name in variables:
                values[v.name] = variables[v.name]
            elif v.required:
                missing.append(v.name)
            else:
                values[v.name] = v.default

        if missing:
            raise ValueError(
                f"Template '{self.name}' missing required variables: {missing}. "
                f"Expected: {[v.name for v in self.variables]}"
            )

        return self.template.format(**values)

    @classmethod
    def list_templates(cls, templates_dir: Path = None) -> List[Dict]:
        """List all available templates with their descriptions."""
        tdir = templates_dir or DEFAULT_TEMPLATES_DIR
        if not tdir.exists():
            return []

        templates = []
        for path in sorted(tdir.glob("*.yaml")):
            try:
                t = cls.load(path.stem, tdir)
                templates.append({
                    "name": t.name,
                    "description": t.description,
                    "variables": [
                        {"name": v.name, "required": v.required, "description": v.description}
                        for v in t.variables
                    ],
                })
            except Exception:
                templates.append({"name": path.stem, "description": "(error loading)", "variables": []})

        return templates
