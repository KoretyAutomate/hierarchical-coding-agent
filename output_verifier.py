#!/usr/bin/env python3
"""
Output Verification Module for Coding Agent
Verifies that code changes produce expected outputs
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime


class OutputVerifier:
    """
    Verifies that generated code produces expected outputs.
    Configurable per-project with expected file patterns and validation rules.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.verification_config = self._load_verification_config()

    def _load_verification_config(self) -> Dict[str, Any]:
        """
        Load project-specific verification config.
        Falls back to intelligent defaults if not found.
        """
        config_path = self.project_root / ".output_verification.json"

        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

        # Default configuration for DR_2_Podcast project
        if "DR_2_Podcast" in str(self.project_root):
            return {
                "project_type": "podcast_generation",
                "output_directory": "research_outputs",
                "expected_files": [
                    {
                        "name": "podcast_final_audio.mp3",
                        "type": "audio",
                        "min_size_kb": 100,
                        "required": True
                    },
                    {
                        "name": "supporting_paper.pdf",
                        "type": "pdf",
                        "min_size_kb": 10,
                        "required": True
                    },
                    {
                        "name": "adversarial_paper.pdf",
                        "type": "pdf",
                        "min_size_kb": 10,
                        "required": True
                    },
                    {
                        "name": "final_audit_report.pdf",
                        "type": "pdf",
                        "min_size_kb": 10,
                        "required": True
                    }
                ],
                "test_command": "python3 podcast_crew.py --topic 'test topic for verification' --language en",
                "timeout_seconds": 1800
            }

        # Generic fallback
        return {
            "project_type": "generic",
            "output_directory": "output",
            "expected_files": [],
            "test_command": None,
            "timeout_seconds": 300
        }

    def verify_file_exists(self, file_path: Path) -> Dict[str, Any]:
        """Check if a file exists and is valid."""
        result = {
            "exists": file_path.exists(),
            "path": str(file_path),
            "size_kb": 0,
            "size_bytes": 0,
            "readable": False,
            "valid": False
        }

        if result["exists"]:
            try:
                result["size_bytes"] = file_path.stat().st_size
                result["size_kb"] = result["size_bytes"] / 1024
                result["readable"] = os.access(file_path, os.R_OK)
                result["valid"] = result["size_bytes"] > 0
            except Exception as e:
                result["error"] = str(e)

        return result

    def verify_outputs(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Verify all expected outputs are present and valid.

        Returns:
            Dictionary with verification results including:
            - success: bool
            - total_files_expected: int
            - total_files_found: int
            - files_verified: list of file verification results
            - missing_files: list of missing required files
            - invalid_files: list of files that exist but are invalid
        """
        if output_dir is None:
            output_dir = self.project_root / self.verification_config["output_directory"]

        results = {
            "success": False,
            "output_directory": str(output_dir),
            "directory_exists": output_dir.exists(),
            "timestamp": datetime.now().isoformat(),
            "total_files_expected": len(self.verification_config["expected_files"]),
            "total_files_found": 0,
            "files_verified": [],
            "missing_files": [],
            "invalid_files": [],
            "warnings": []
        }

        if not output_dir.exists():
            results["error"] = f"Output directory does not exist: {output_dir}"
            return results

        # Verify each expected file
        for file_spec in self.verification_config["expected_files"]:
            file_path = output_dir / file_spec["name"]
            file_result = self.verify_file_exists(file_path)

            file_verification = {
                "name": file_spec["name"],
                "type": file_spec["type"],
                "required": file_spec["required"],
                "expected_min_size_kb": file_spec["min_size_kb"],
                **file_result
            }

            # Check size requirement
            if file_result["exists"]:
                if file_result["size_kb"] >= file_spec["min_size_kb"]:
                    file_verification["size_valid"] = True
                    results["total_files_found"] += 1
                else:
                    file_verification["size_valid"] = False
                    file_verification["warning"] = f"File too small: {file_result['size_kb']:.1f} KB < {file_spec['min_size_kb']} KB"
                    results["invalid_files"].append(file_spec["name"])
            else:
                file_verification["size_valid"] = False
                if file_spec["required"]:
                    results["missing_files"].append(file_spec["name"])

            results["files_verified"].append(file_verification)

        # Determine overall success
        results["success"] = (
            len(results["missing_files"]) == 0 and
            len(results["invalid_files"]) == 0 and
            results["total_files_found"] == results["total_files_expected"]
        )

        # Add summary
        if results["success"]:
            results["summary"] = f"✓ All {results['total_files_found']} expected files verified successfully"
        else:
            issues = []
            if results["missing_files"]:
                issues.append(f"{len(results['missing_files'])} missing")
            if results["invalid_files"]:
                issues.append(f"{len(results['invalid_files'])} invalid")
            results["summary"] = f"✗ Verification failed: {', '.join(issues)}"

        return results

    def run_test_and_verify(self, test_command: Optional[str] = None,
                           working_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run test command and verify outputs.

        Returns complete test results including:
        - test_execution: Dict with command, return_code, stdout, stderr, duration
        - output_verification: Dict with file verification results
        - overall_success: bool indicating if both test and verification passed
        """
        if test_command is None:
            test_command = self.verification_config.get("test_command")

        if not test_command:
            return {
                "success": False,
                "error": "No test command configured for this project"
            }

        if working_dir is None:
            working_dir = self.project_root

        print(f"\n{'='*70}")
        print(f"OUTPUT VERIFICATION TEST")
        print(f"{'='*70}")
        print(f"Project: {self.project_root}")
        print(f"Command: {test_command}")
        print(f"Working Directory: {working_dir}")
        print(f"{'='*70}\n")

        test_result = {
            "command": test_command,
            "working_directory": str(working_dir),
            "start_time": datetime.now().isoformat(),
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "duration_seconds": 0,
            "timed_out": False
        }

        try:
            # Run test command
            start_time = datetime.now()
            print(f"Running test command... (timeout: {self.verification_config['timeout_seconds']}s)")

            process = subprocess.run(
                test_command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.verification_config["timeout_seconds"]
            )

            end_time = datetime.now()
            test_result["duration_seconds"] = (end_time - start_time).total_seconds()
            test_result["end_time"] = end_time.isoformat()
            test_result["return_code"] = process.returncode
            test_result["stdout"] = process.stdout
            test_result["stderr"] = process.stderr

            print(f"✓ Command completed (return code: {process.returncode}, duration: {test_result['duration_seconds']:.1f}s)")

        except subprocess.TimeoutExpired as e:
            test_result["timed_out"] = True
            test_result["error"] = f"Command timed out after {self.verification_config['timeout_seconds']}s"
            print(f"✗ Command timed out")

        except Exception as e:
            test_result["error"] = str(e)
            print(f"✗ Command failed: {e}")

        # Verify outputs
        print(f"\nVerifying outputs...")
        verification_result = self.verify_outputs()

        # Combine results
        final_result = {
            "overall_success": (
                test_result.get("return_code") == 0 and
                not test_result.get("timed_out", False) and
                verification_result["success"]
            ),
            "test_execution": test_result,
            "output_verification": verification_result,
            "timestamp": datetime.now().isoformat()
        }

        # Print summary
        print(f"\n{'='*70}")
        print(f"VERIFICATION SUMMARY")
        print(f"{'='*70}")
        print(f"Test Execution: {'✓ PASSED' if test_result.get('return_code') == 0 else '✗ FAILED'}")
        print(f"Output Verification: {verification_result['summary']}")
        print(f"Overall Result: {'✓ SUCCESS' if final_result['overall_success'] else '✗ FAILURE'}")
        print(f"{'='*70}\n")

        # Save detailed report
        self._save_verification_report(final_result)

        return final_result

    def _save_verification_report(self, results: Dict[str, Any]):
        """Save detailed verification report to file."""
        reports_dir = self.project_root / "verification_reports"
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Detailed report saved: {report_file}")

    def quick_check(self) -> Dict[str, Any]:
        """
        Quick check without running tests - just verify expected files exist.
        Useful for fast validation after code changes.
        """
        print(f"\n{'='*70}")
        print(f"QUICK OUTPUT CHECK (No Test Execution)")
        print(f"{'='*70}\n")

        verification_result = self.verify_outputs()

        print(f"\n{verification_result['summary']}")

        if not verification_result["success"]:
            if verification_result["missing_files"]:
                print(f"\nMissing files:")
                for fname in verification_result["missing_files"]:
                    print(f"  ✗ {fname}")

            if verification_result["invalid_files"]:
                print(f"\nInvalid files:")
                for fname in verification_result["invalid_files"]:
                    print(f"  ⚠ {fname}")

        return verification_result


def main():
    """CLI interface for output verifier."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Verify code outputs")
    parser.add_argument("project_root", help="Path to project root directory")
    parser.add_argument("--quick", action="store_true", help="Quick check without running tests")
    parser.add_argument("--command", help="Override test command")

    args = parser.parse_args()

    verifier = OutputVerifier(args.project_root)

    if args.quick:
        result = verifier.quick_check()
    else:
        result = verifier.run_test_and_verify(test_command=args.command)

    # Exit with appropriate code
    sys.exit(0 if result.get("success") or result.get("overall_success") else 1)


if __name__ == "__main__":
    main()
