#!/usr/bin/env python3
"""
Quick test script for web interface
"""
import sys
import subprocess
import time

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        import asyncio
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_database_schema():
    """Test database schema migration"""
    print("\nTesting database schema...")
    try:
        import sqlite3
        conn = sqlite3.connect("/home/korety/coding-agent/tasks.db")
        c = conn.cursor()

        # Check if new columns exist
        c.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in c.fetchall()]

        required_columns = [
            'plan_approved_at', 'plan_approved_by', 'plan_rejection_reason',
            'implementation_approved_at', 'implementation_approved_by',
            'implementation_rejection_reason', 'workflow_state',
            'workflow_checkpoint_data', 'verification_result',
            'error_details', 'retry_count'
        ]

        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"✗ Missing columns: {missing}")
            conn.close()
            return False
        else:
            print(f"✓ All {len(required_columns)} new columns present")
            print(f"  Total columns: {len(columns)}")
            conn.close()
            return True

    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_syntax():
    """Test Python syntax"""
    print("\nTesting Python syntax...")
    result = subprocess.run(
        ["python3", "-m", "py_compile", "/home/korety/coding-agent/web_interface.py"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Python syntax valid")
        return True
    else:
        print(f"✗ Syntax error: {result.stderr}")
        return False

def main():
    print("="*60)
    print("Web Interface Implementation Tests")
    print("="*60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Syntax", test_syntax()))
    results.append(("Database Schema", test_database_schema()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Implementation ready to run.")
        print("\nTo start the server:")
        print("  cd /home/korety/coding-agent")
        print("  python3 web_interface.py 8080")
        return 0
    else:
        print("\n✗ Some tests failed. Please review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
