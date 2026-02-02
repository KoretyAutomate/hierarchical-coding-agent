#!/usr/bin/env python3
"""
Pull Request Helper for Coding Agent
Enhances PR descriptions with project-specific metadata
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class PRHelper:
    """
    Generates enhanced PR descriptions with project-specific metadata.
    Automatically includes references to generated files for easier testing.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config = self._load_project_config()

    def _load_project_config(self) -> Dict:
        """Load project configuration for PR metadata."""
        config_path = self.project_root / ".pr_metadata.json"

        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

        # Auto-detect project type and provide defaults
        if self._is_podcast_project():
            return {
                "project_type": "podcast_generation",
                "output_directory": "research_outputs",
                "reference_files": {
                    "audio": {
                        "pattern": "*.mp3",
                        "label": "🎵 Test Audio",
                        "description": "Generated podcast audio for testing"
                    },
                    "documents": {
                        "pattern": "*.pdf",
                        "label": "📄 Generated Documents",
                        "description": "Research papers and reports"
                    }
                }
            }

        return {
            "project_type": "generic",
            "output_directory": "output",
            "reference_files": {}
        }

    def _is_podcast_project(self) -> bool:
        """Detect if this is the DR_2_Podcast project."""
        indicators = [
            (self.project_root / "podcast_crew.py").exists(),
            "podcast" in str(self.project_root).lower(),
            (self.project_root / "research_outputs").exists()
        ]
        return any(indicators)

    def find_output_files(self, pattern: str, output_dir: Optional[Path] = None) -> List[Path]:
        """Find files matching pattern in output directory."""
        if output_dir is None:
            output_dir = self.project_root / self.config["output_directory"]

        if not output_dir.exists():
            return []

        return sorted(output_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)

    def get_file_info(self, file_path: Path) -> Dict:
        """Get metadata about a file."""
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "path": str(file_path.relative_to(self.project_root)),
            "size_kb": stat.st_size / 1024,
            "size_human": self._human_readable_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def generate_file_references_section(self) -> str:
        """
        Generate markdown section with references to generated files.

        Returns:
            Markdown formatted section with file references
        """
        if not self.config.get("reference_files"):
            return ""

        sections = []

        for ref_type, ref_config in self.config["reference_files"].items():
            pattern = ref_config["pattern"]
            label = ref_config["label"]
            description = ref_config.get("description", "")

            files = self.find_output_files(pattern)

            if files:
                # Take most recent file
                latest_file = files[0]
                file_info = self.get_file_info(latest_file)

                section = f"\n### {label}\n\n"
                if description:
                    section += f"{description}\n\n"

                section += f"**File**: `{file_info['path']}`  \n"
                section += f"**Size**: {file_info['size_human']}  \n"
                section += f"**Modified**: {file_info['modified']}\n"

                # For audio files, add note about testing
                if ref_type == "audio":
                    section += f"\n💡 **Testing**: Download and listen to verify audio quality and content accuracy.\n"

                sections.append(section)

        if sections:
            return "\n---\n\n## 🔗 Generated Files Reference\n" + "".join(sections)

        return ""

    def generate_enhanced_pr_body(self, base_description: str,
                                  changes_summary: Optional[str] = None) -> str:
        """
        Generate enhanced PR description with file references.

        Args:
            base_description: Original PR description
            changes_summary: Optional summary of what changed

        Returns:
            Enhanced PR description with file references
        """
        sections = [base_description]

        # Add file references
        file_refs = self.generate_file_references_section()
        if file_refs:
            sections.append(file_refs)

        # Add testing instructions if this is a podcast project
        if self.config["project_type"] == "podcast_generation":
            testing_section = self._generate_podcast_testing_section()
            if testing_section:
                sections.append(testing_section)

        return "\n".join(sections)

    def _generate_podcast_testing_section(self) -> str:
        """Generate testing instructions for podcast projects."""
        audio_files = self.find_output_files("*.mp3")

        if not audio_files:
            return ""

        return """

---

## 🧪 Testing Checklist

Before merging, verify:

- [ ] Audio file generated successfully
- [ ] Audio duration is reasonable (not too short/long)
- [ ] Audio quality is clear and natural
- [ ] Character voices are distinct (if multi-speaker)
- [ ] All PDF reports generated (supporting, adversarial, final audit)
- [ ] PDFs contain expected content
- [ ] No errors in logs

### Quick Test Command

```bash
# Run with test topic
python3 podcast_crew.py --topic "test topic" --language en

# Check outputs
ls -lh research_outputs/
```
"""

    def format_audio_reference_for_pr_title(self) -> str:
        """
        Get audio filename for PR title reference.

        Returns:
            Short reference like "[audio: podcast_final_audio.mp3]" or empty string
        """
        audio_files = self.find_output_files("*.mp3")

        if audio_files:
            latest_audio = audio_files[0]
            return f" [audio: {latest_audio.name}]"

        return ""

    def get_pr_metadata_json(self) -> Dict:
        """
        Get all PR metadata as JSON for programmatic use.

        Returns:
            Dictionary with all file references and metadata
        """
        metadata = {
            "project_type": self.config["project_type"],
            "timestamp": datetime.now().isoformat(),
            "reference_files": {}
        }

        for ref_type, ref_config in self.config.get("reference_files", {}).items():
            pattern = ref_config["pattern"]
            files = self.find_output_files(pattern)

            metadata["reference_files"][ref_type] = {
                "pattern": pattern,
                "files": [self.get_file_info(f) for f in files[:5]]  # Limit to 5 most recent
            }

        return metadata


def main():
    """CLI interface for PR helper."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Generate enhanced PR descriptions")
    parser.add_argument("project_root", help="Path to project root")
    parser.add_argument("--base-description", default="", help="Base PR description")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--title-ref", action="store_true", help="Output title reference only")

    args = parser.parse_args()

    helper = PRHelper(args.project_root)

    if args.json:
        metadata = helper.get_pr_metadata_json()
        print(json.dumps(metadata, indent=2))
    elif args.title_ref:
        ref = helper.format_audio_reference_for_pr_title()
        print(ref)
    else:
        enhanced = helper.generate_enhanced_pr_body(args.base_description)
        print(enhanced)


if __name__ == "__main__":
    main()
