#!/usr/bin/env python3
"""
Test script for Phase 1 implementation.
Verifies LLM abstraction layer, config system, and refactored agents.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm import OllamaAdapter, AnthropicAdapter, BaseLLM
from core.config import get_config
from agents.coding_agent import CodingAgent


def test_config_system():
    """Test configuration management."""
    print("\n" + "="*70)
    print("TEST 1: Configuration System")
    print("="*70)

    config = get_config()

    print(f"✓ Config loaded successfully")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Ollama Model: {config.llm.ollama_model}")
    print(f"  Ollama URL: {config.llm.ollama_base_url}")
    print(f"  Workspace: {config.workspace.project_root}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Max Tokens: {config.llm.max_tokens}")

    return config


def test_llm_adapter_creation(config):
    """Test LLM adapter instantiation."""
    print("\n" + "="*70)
    print("TEST 2: LLM Adapter Creation")
    print("="*70)

    # Test Ollama adapter
    ollama = OllamaAdapter(
        model_name=config.llm.ollama_model,
        base_url=config.llm.ollama_base_url,
        timeout=config.llm.ollama_timeout
    )
    print(f"✓ OllamaAdapter created: {ollama}")

    # Test Anthropic adapter (without API key - just instantiation)
    try:
        anthropic = AnthropicAdapter(
            model_name="claude-3-5-sonnet-20241022",
            api_key="dummy-key"  # Just for testing instantiation
        )
        print(f"✓ AnthropicAdapter created: {anthropic}")
    except Exception as e:
        print(f"⚠ AnthropicAdapter creation warning: {e}")

    return ollama


def test_llm_connection(llm: BaseLLM):
    """Test LLM connection (requires Ollama to be running)."""
    print("\n" + "="*70)
    print("TEST 3: LLM Connection")
    print("="*70)

    try:
        is_connected = llm.validate_connection()
        if is_connected:
            print(f"✓ LLM connection valid: {llm}")
        else:
            print(f"⚠ LLM connection failed (is Ollama running?)")
            return False
    except Exception as e:
        print(f"⚠ Connection test failed: {e}")
        return False

    return True


def test_llm_generation(llm: BaseLLM):
    """Test LLM generation (requires Ollama to be running)."""
    print("\n" + "="*70)
    print("TEST 4: LLM Generation")
    print("="*70)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from Phase 1!' and nothing else."}
    ]

    try:
        response = llm.generate(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        print(f"✓ LLM generated response")
        print(f"  Content: {response.content}")
        print(f"  Usage: {response.usage}")
        return True
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def test_coding_agent(llm: BaseLLM, config):
    """Test CodingAgent with new architecture."""
    print("\n" + "="*70)
    print("TEST 5: CodingAgent with LLM Abstraction")
    print("="*70)

    try:
        agent = CodingAgent(
            llm=llm,
            workspace_root=str(config.workspace.project_root),
            max_iterations=2,  # Keep it short for testing
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens
        )
        print(f"✓ CodingAgent created with {llm}")
        return agent
    except Exception as e:
        print(f"✗ CodingAgent creation failed: {e}")
        return None


def test_hierarchical_orchestrator():
    """Test HierarchicalOrchestrator with new architecture."""
    print("\n" + "="*70)
    print("TEST 6: HierarchicalOrchestrator")
    print("="*70)

    try:
        from hierarchical_orchestrator import HierarchicalOrchestrator

        orchestrator = HierarchicalOrchestrator()
        print(f"✓ HierarchicalOrchestrator created")
        print(f"  Lead LLM: {orchestrator.lead_llm}")
        print(f"  Member LLM: {orchestrator.member_llm}")
        print(f"  Workspace: {orchestrator.workspace}")
        return True
    except Exception as e:
        print(f"✗ HierarchicalOrchestrator creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 1 tests."""
    print("\n" + "#"*70)
    print("# PHASE 1 IMPLEMENTATION TEST SUITE")
    print("#"*70)

    results = {
        "config": False,
        "adapter_creation": False,
        "connection": False,
        "generation": False,
        "coding_agent": False,
        "orchestrator": False
    }

    # Test 1: Config system
    try:
        config = test_config_system()
        results["config"] = True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return

    # Test 2: Adapter creation
    try:
        llm = test_llm_adapter_creation(config)
        results["adapter_creation"] = True
    except Exception as e:
        print(f"✗ Adapter creation test failed: {e}")
        return

    # Test 3: Connection (optional - requires Ollama running)
    results["connection"] = test_llm_connection(llm)

    # Test 4: Generation (optional - requires Ollama running)
    if results["connection"]:
        results["generation"] = test_llm_generation(llm)
    else:
        print("\n⚠ Skipping generation test (no connection)")

    # Test 5: CodingAgent (always test creation, even without connection)
    results["coding_agent"] = test_coding_agent(llm, config) is not None

    # Test 6: HierarchicalOrchestrator
    results["orchestrator"] = test_hierarchical_orchestrator()

    # Summary
    print("\n" + "#"*70)
    print("# TEST SUMMARY")
    print("#"*70)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 1 implementation is complete.")
        return 0
    elif results["config"] and results["adapter_creation"] and results["coding_agent"] and results["orchestrator"]:
        print("\n✓ Core functionality works! (Connection tests failed - Ollama may not be running)")
        return 0
    else:
        print("\n⚠ Some critical tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
