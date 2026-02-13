# Output Verifier - Automated Testing for Coding Agent

## Overview

The Output Verifier automatically validates that code changes produce expected outputs. This ensures the coding agent doesn't create PRs for broken code.

## Features

- ✅ **File Existence Verification** - Checks all expected output files exist
- ✅ **File Size Validation** - Ensures files meet minimum size requirements
- ✅ **File Type Checking** - Validates audio, PDF, and other file types
- ✅ **Test Execution** - Can run full test commands with timeouts
- ✅ **Detailed Reporting** - JSON reports saved for audit trail
- ✅ **Project-Specific Config** - Customizable per project
- ✅ **Quick Mode** - Fast checks without running tests

## Integration

The Output Verifier is integrated into the Hierarchical Orchestrator as **Stage 4**:

1. **Planning** (Project Lead)
2. **Implementation** (Project Member)
3. **Review** (Project Lead)
4. **Output Verification** (NEW - Output Verifier)
5. **User Approval**
6. **PR Creation**

## Configuration

Each project can have a `.output_verification.json` file:

```json
{
  "project_type": "podcast_generation",
  "output_directory": "research_outputs",
  "expected_files": [
    {
      "name": "podcast_final_audio.mp3",
      "type": "audio",
      "min_size_kb": 100,
      "required": true,
      "description": "Generated podcast audio"
    },
    {
      "name": "supporting_paper.pdf",
      "type": "pdf",
      "min_size_kb": 10,
      "required": true,
      "description": "Supporting research paper"
    }
  ],
  "test_command": "python3 main.py",
  "timeout_seconds": 1800
}
```

### Configuration Fields

- **project_type**: Project category (e.g., "podcast_generation", "web_app", "api")
- **output_directory**: Where to find generated files (relative to project root)
- **expected_files**: Array of expected output files
  - **name**: Filename to check
  - **type**: File type (audio, pdf, image, etc.)
  - **min_size_kb**: Minimum file size in KB
  - **required**: Whether file is mandatory
  - **description**: Human-readable description
- **test_command**: Shell command to run for full testing
- **timeout_seconds**: Maximum time for test execution

## Usage

### Command Line

```bash
# Quick check (fast - just verify files exist)
python3 output_verifier.py /path/to/project --quick

# Full test (run command and verify outputs)
python3 output_verifier.py /path/to/project

# Custom test command
python3 output_verifier.py /path/to/project --command "npm test"
```

### Programmatic

```python
from output_verifier import OutputVerifier

# Initialize verifier for project
verifier = OutputVerifier("/path/to/project")

# Quick check (no test execution)
result = verifier.quick_check()
print(result["summary"])

# Full test and verification
result = verifier.run_test_and_verify()
if result["overall_success"]:
    print("✓ All tests passed")
else:
    print("✗ Tests failed")
```

### In Hierarchical Orchestrator

The orchestrator automatically runs verification after code review:

```python
orchestrator = HierarchicalOrchestrator()
result = orchestrator.autonomous_workflow("Add error handling")

# After implementation and review, verification runs automatically
# Result includes: plan, implementation, review, verification
```

## Verification Results

The verifier returns detailed results:

```json
{
  "overall_success": true,
  "test_execution": {
    "command": "python3 podcast_crew.py",
    "return_code": 0,
    "duration_seconds": 156.3,
    "timed_out": false
  },
  "output_verification": {
    "success": true,
    "total_files_expected": 4,
    "total_files_found": 4,
    "files_verified": [
      {
        "name": "podcast_final_audio.mp3",
        "exists": true,
        "size_kb": 2456.7,
        "size_valid": true,
        "readable": true
      }
    ],
    "missing_files": [],
    "invalid_files": []
  }
}
```

## Reports

Detailed JSON reports are saved to `<project>/verification_reports/`:

```
verification_20260201_143022.json
```

Each report includes:
- Test execution details (command, return code, output, duration)
- File verification results (existence, size, validity)
- Timestamp and project info
- Overall success/failure status

## DR_2_Podcast Example

For the podcast project, verification checks:

1. **podcast_final_audio.mp3** - Main audio output (min 100KB)
2. **supporting_paper.pdf** - Pro-argument paper (min 10KB)
3. **adversarial_paper.pdf** - Counter-argument paper (min 10KB)
4. **final_audit_report.pdf** - Meta-analysis report (min 10KB)

Example run:

```bash
$ python3 output_verifier.py /home/korety/Project/DR_2_Podcast --quick

======================================================================
QUICK OUTPUT CHECK (No Test Execution)
======================================================================

✓ All 4 expected files verified successfully
```

## Default Configurations

If no `.output_verification.json` exists, the verifier provides intelligent defaults:

- **DR_2_Podcast projects**: Expects audio + 3 PDFs
- **Generic projects**: Empty expectations (manual configuration needed)

## Benefits for Coding Agent

1. **Prevents Broken PRs** - Catches issues before code review
2. **Faster Feedback** - Quick checks in seconds
3. **Audit Trail** - Detailed reports for debugging
4. **Quality Assurance** - Ensures output standards met
5. **Configurable** - Adapts to any project type

## Future Enhancements

- [ ] Content validation (check inside files)
- [ ] Performance benchmarking
- [ ] Screenshot comparison for UI projects
- [ ] Audio quality analysis
- [ ] API response validation
- [ ] Integration test support

## Troubleshooting

### "Output directory does not exist"
- Ensure `output_directory` in config matches your project structure
- Run the code once manually to create outputs

### "File too small" warnings
- Adjust `min_size_kb` in configuration
- Check if generation completed successfully

### Test command timeout
- Increase `timeout_seconds` in configuration
- Optimize test execution

### Missing configuration
- Create `.output_verification.json` in project root
- Or rely on intelligent defaults for known project types

## Support

For issues or questions about the Output Verifier:
1. Check verification report JSON for details
2. Run with `--quick` to isolate file issues from test execution
3. Verify `.output_verification.json` is valid JSON
4. Test the test command manually first

---

**File**: `/home/korety/coding-agent/output_verifier.py`
**Integration**: `/home/korety/coding-agent/hierarchical_orchestrator.py` (Stage 4)
**Documentation**: This file
