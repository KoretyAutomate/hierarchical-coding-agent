# PR Helper - Enhanced Pull Request Descriptions

## Overview

The PR Helper automatically enhances pull request descriptions with project-specific metadata, including references to generated files (audio, PDFs, etc.) for easier testing and review.

## Features

- ✅ **Auto-detect project type** - Recognizes podcast, web, API projects
- ✅ **File references** - Links to generated audio, PDFs, images
- ✅ **Testing instructions** - Project-specific testing checklists
- ✅ **File metadata** - Size, modification time, path info
- ✅ **Configurable** - Customize via `.pr_metadata.json`
- ✅ **CLI and API** - Use standalone or integrate in workflows

## Why Use PR Helper?

### Problem
When creating PRs for projects that generate files (audio, PDFs, images), reviewers need to:
- Find the generated files manually
- Remember which files to check
- Know where files are located
- Understand testing procedures

### Solution
PR Helper automatically:
- Finds latest generated files
- Includes file references in PR description
- Adds testing instructions
- Provides file metadata (size, modification time)
- Makes testing easier for reviewers

## Configuration

Create `.pr_metadata.json` in your project root:

```json
{
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
```

### Configuration Fields

- **project_type**: Type of project (podcast_generation, web_app, api, etc.)
- **output_directory**: Where generated files are located
- **reference_files**: Dictionary of file types to reference
  - **pattern**: Glob pattern to match files (*.mp3, *.pdf, *.png)
  - **label**: Display label with emoji
  - **description**: Brief description of the files

## Usage

### Command Line

```bash
# Generate enhanced PR description
python3 pr_helper.py /path/to/project --base-description "Fix audio generation"

# Get audio reference for PR title
python3 pr_helper.py /path/to/project --title-ref

# Get metadata as JSON
python3 pr_helper.py /path/to/project --json
```

### Programmatic

```python
from pr_helper import PRHelper

# Initialize for project
helper = PRHelper("/path/to/project")

# Generate enhanced PR body
base_description = """
## Summary
Fixed audio generation issues

## Changes
- Updated audio encoding
- Fixed file path handling
"""

enhanced_pr_body = helper.generate_enhanced_pr_body(base_description)
print(enhanced_pr_body)

# Get audio filename for PR title
audio_ref = helper.format_audio_reference_for_pr_title()
pr_title = f"fix: Audio generation issues{audio_ref}"
# Result: "fix: Audio generation issues [audio: podcast_final_audio.mp3]"
```

## Enhanced PR Description Example

**Before** (manual):
```markdown
## Summary
Fixed audio generation issues

## Changes
- Updated ChatTTS integration
- Added error handling
```

**After** (with PR Helper):
```markdown
## Summary
Fixed audio generation issues

## Changes
- Updated ChatTTS integration
- Added error handling

---

## 🔗 Generated Files Reference

### 🎵 Test Audio

Generated podcast audio file for testing and review

**File**: `research_outputs/podcast_final_audio.mp3`
**Size**: 2.4 MB
**Modified**: 2026-02-01T14:30:22

💡 **Testing**: Download and listen to verify audio quality and content accuracy.

### 📄 Generated Documents

Research papers and audit reports (supporting, adversarial, final audit)

**Files**:
- `research_outputs/supporting_paper.pdf` (45.2 KB)
- `research_outputs/adversarial_paper.pdf` (38.7 KB)
- `research_outputs/final_audit_report.pdf` (52.3 KB)

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

\```bash
# Run with test topic
python3 podcast_crew.py --topic "test topic" --language en

# Check outputs
ls -lh research_outputs/
\```
```

## Integration with gh CLI

Enhance PR creation with file references:

```bash
#!/bin/bash
# Enhanced PR creation script

PROJECT_ROOT="/path/to/project"

# Base PR description
BASE_DESC="## Summary
Fix audio generation

## Changes
- Updated TTS engine
- Added error handling"

# Generate enhanced description with file references
ENHANCED_DESC=$(python3 pr_helper.py "$PROJECT_ROOT" --base-description "$BASE_DESC")

# Get audio reference for title
AUDIO_REF=$(python3 pr_helper.py "$PROJECT_ROOT" --title-ref)

# Create PR with enhanced description
gh pr create \
  --title "fix: Audio generation issues$AUDIO_REF" \
  --body "$ENHANCED_DESC"
```

Result: PR with title "fix: Audio generation issues [audio: podcast_final_audio.mp3]"

## DR_2_Podcast Example

For the podcast project, PR Helper automatically:

1. **Finds Latest Audio**: Most recent MP3 in research_outputs/
2. **Lists PDFs**: All generated research papers
3. **Includes Testing Checklist**: Podcast-specific validation steps
4. **Adds File Metadata**: Size, modification time, paths

Example metadata output:

```json
{
  "project_type": "podcast_generation",
  "timestamp": "2026-02-01T14:30:22",
  "reference_files": {
    "audio": {
      "pattern": "*.mp3",
      "files": [
        {
          "name": "podcast_final_audio.mp3",
          "path": "research_outputs/podcast_final_audio.mp3",
          "size_kb": 2456.7,
          "size_human": "2.4 MB",
          "modified": "2026-02-01T14:28:15"
        }
      ]
    },
    "documents": {
      "pattern": "*.pdf",
      "files": [
        {
          "name": "supporting_paper.pdf",
          "path": "research_outputs/supporting_paper.pdf",
          "size_kb": 45.2,
          "size_human": "45.2 KB",
          "modified": "2026-02-01T14:25:10"
        }
      ]
    }
  }
}
```

## Auto-Detection

If no `.pr_metadata.json` exists, PR Helper auto-detects project type:

### Podcast Project Detection
Looks for:
- `podcast_crew.py` file
- "podcast" in directory name
- `research_outputs/` directory

If detected, automatically expects:
- Audio files (*.mp3)
- PDF documents (*.pdf)

### Generic Projects
For unknown projects:
- No file references added
- Passes through base description unchanged
- Manual configuration recommended

## Benefits

1. **Saves Time** - No manual file hunting
2. **Consistent PRs** - Standard format across team
3. **Better Reviews** - Reviewers know what to test
4. **Testing Guidance** - Built-in checklists
5. **Metadata Tracking** - File sizes and timestamps

## Integration with Hierarchical Orchestrator

Add to workflow after implementation:

```python
from pr_helper import PRHelper

# After code implementation and review
pr_helper = PRHelper(project_root)

# Generate enhanced PR body
enhanced_body = pr_helper.generate_enhanced_pr_body(base_pr_description)

# Get audio reference for title
audio_ref = pr_helper.format_audio_reference_for_pr_title()
pr_title = f"feat: {feature_name}{audio_ref}"

# Create PR with gh CLI
subprocess.run([
    "gh", "pr", "create",
    "--title", pr_title,
    "--body", enhanced_body
])
```

## File Reference Format

For each file type:

```markdown
### 🎵 Test Audio

Generated podcast audio for testing and review

**File**: `research_outputs/podcast_final_audio.mp3`
**Size**: 2.4 MB
**Modified**: 2026-02-01T14:30:22

💡 **Testing**: Download and listen to verify audio quality and content accuracy.
```

## Advanced Usage

### Custom File Patterns

```json
{
  "reference_files": {
    "screenshots": {
      "pattern": "screenshots/*.png",
      "label": "📸 Screenshots",
      "description": "Visual regression test screenshots"
    },
    "logs": {
      "pattern": "logs/test_*.log",
      "label": "📋 Test Logs",
      "description": "Execution logs for debugging"
    }
  }
}
```

### Multiple Output Directories

```json
{
  "output_directory": "build",
  "reference_files": {
    "builds": {
      "pattern": "../dist/*.js",
      "label": "📦 Build Artifacts",
      "description": "Compiled JavaScript bundles"
    }
  }
}
```

## Future Enhancements

- [ ] Screenshot comparisons
- [ ] Audio waveform previews
- [ ] PDF thumbnail generation
- [ ] File diff summaries
- [ ] Integration with GitHub API for inline comments

## Troubleshooting

### "No files found"
- Check `output_directory` path is correct
- Verify glob `pattern` matches your files
- Run code to generate files first

### "Pattern not matching"
- Use forward slashes even on Windows
- Test pattern with `ls <pattern>` first
- Check file extensions match exactly

### "Wrong files referenced"
- Files are sorted by modification time (newest first)
- Clean old files from output directory
- Adjust pattern to be more specific

## Examples

### Web App Project

```json
{
  "project_type": "web_app",
  "output_directory": "build",
  "reference_files": {
    "bundle": {
      "pattern": "*.js",
      "label": "📦 JavaScript Bundle",
      "description": "Compiled application bundle"
    },
    "styles": {
      "pattern": "*.css",
      "label": "🎨 Stylesheets",
      "description": "Compiled CSS files"
    }
  }
}
```

### API Project

```json
{
  "project_type": "api",
  "output_directory": "test_results",
  "reference_files": {
    "coverage": {
      "pattern": "coverage/lcov-report/index.html",
      "label": "📊 Coverage Report",
      "description": "Test coverage analysis"
    }
  }
}
```

---

**File**: `/home/korety/coding-agent/pr_helper.py`
**Configuration**: `.pr_metadata.json` in project root
**Documentation**: This file
