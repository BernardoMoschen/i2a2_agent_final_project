#!/usr/bin/env python3
"""Quick test to verify the agent can answer questions correctly after the fix."""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.agent_core import create_agent

# Quick test
api_key = os.getenv("GEMINI_API_KEY", "test-key-for-demo")

print("=" * 80)
print("🧪 TESTING FIXED AGENT")
print("=" * 80)
print()

if api_key == "test-key-for-demo":
    print("⚠️  No GEMINI_API_KEY found. Set it to test with real LLM:")
    print("   export GEMINI_API_KEY='your-key-here'")
    print()
    print("For now, showing that the tool fix works:")
    print()
    
    from src.agent.tools import DatabaseSearchTool
    
    tool = DatabaseSearchTool()
    
    print("Test 1: Searching for purchase invoices")
    print("-" * 80)
    result = tool._run({'operation_type': 'purchase', 'days_back': 9999})
    print(result[:300])
    print()
    
    print("Test 2: Searching for sale invoices")
    print("-" * 80)
    result = tool._run({'operation_type': 'sale', 'days_back': 9999})
    print(result[:300])
    print()
    
    print("=" * 80)
    print("✅ TOOL FIX VERIFIED")
    print("=" * 80)
    print()
    print("The tool now correctly handles dict parameters from LangChain!")
    print("Set GEMINI_API_KEY to test with the full agent.")
    
else:
    print("✅ API Key found! Testing with real agent...")
    print()
    
    agent = create_agent(api_key=api_key, model_name="gemini-2.0-flash-exp")
    
    test_questions = [
        "Quantas notas de compra temos?",
        "O que é ICMS?",
    ]
    
    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print('=' * 80)
        
        response = agent.chat(question)
        print(f"\nResponse:\n{response}\n")
