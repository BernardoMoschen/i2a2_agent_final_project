#!/usr/bin/env python3
"""Quick test of agent with question about validation issues in 2024"""
import sys
import os

# Set API key
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

from src.agent.agent_core import LLMFiscalAgent

# Create agent
agent = LLMFiscalAgent(api_key="your-api-key-here")

# Ask a question  
question = "quais os erros mais comuns em 2024 nas nossas notas?"
print(f"User: {question}")
print("\nAgent response:")
print("-" * 80)

try:
    response = agent.chat(question)
    print(response)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
