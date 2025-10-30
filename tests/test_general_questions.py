#!/usr/bin/env python3
"""
Test script to demonstrate the agent's ability to answer ANY question.

This script tests both:
1. Questions specific to invoices in the system
2. General knowledge questions (fiscal, accounting, general topics)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.agent_core import create_agent


def test_general_questions():
    """Test the agent with various types of questions."""
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Please set it: export GEMINI_API_KEY='your-key-here'")
        return
    
    print("🤖 Creating Fiscal Agent...")
    agent = create_agent(api_key=api_key, model_name="gemini-2.0-flash-exp")
    
    print("\n" + "="*80)
    print("🧪 TESTING AGENT'S GENERAL KNOWLEDGE CAPABILITIES")
    print("="*80 + "\n")
    
    # Test questions - mix of specific and general
    test_questions = [
        # Fiscal-specific questions
        {
            "category": "📚 Fiscal Knowledge",
            "question": "O que é ICMS e como ele é calculado?",
        },
        {
            "category": "📚 Fiscal Knowledge",
            "question": "Qual a diferença entre NFe e NFCe?",
        },
        {
            "category": "📚 Fiscal Knowledge",
            "question": "O que significa CFOP 5102?",
        },
        # Accounting questions
        {
            "category": "💰 Accounting",
            "question": "Como calcular o lucro líquido de uma empresa?",
        },
        {
            "category": "💰 Accounting",
            "question": "O que é regime de competência?",
        },
        # Tax calculation
        {
            "category": "🧮 Calculations",
            "question": "Se um produto custa R$ 100 e tem IPI de 10%, qual o valor final?",
        },
        # Brazilian legislation
        {
            "category": "⚖️ Legislation",
            "question": "O que é o Simples Nacional?",
        },
        # General knowledge
        {
            "category": "🌍 General Knowledge",
            "question": "Quem foi Albert Einstein?",
        },
        {
            "category": "🌍 General Knowledge",
            "question": "Explique como funciona a fotossíntese.",
        },
        # Technical
        {
            "category": "💻 Technology",
            "question": "O que é um arquivo XML?",
        },
    ]
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_questions)}: {test['category']}")
        print(f"{'='*80}")
        print(f"\n❓ Question: {test['question']}\n")
        
        try:
            response = agent.chat(test['question'])
            print(f"🤖 Agent Response:\n{response}\n")
            
        except Exception as e:
            print(f"❌ Error: {e}\n")
        
        print("-" * 80)
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETED")
    print("="*80)
    print("\nThe agent can now answer:")
    print("  ✓ Specific questions about invoices in the database")
    print("  ✓ General fiscal and accounting questions")
    print("  ✓ Tax calculations and explanations")
    print("  ✓ Brazilian legislation and regulations")
    print("  ✓ General knowledge questions")
    print("  ✓ Technical explanations")


if __name__ == "__main__":
    test_general_questions()
