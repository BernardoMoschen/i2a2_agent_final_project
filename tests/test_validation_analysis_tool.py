#!/usr/bin/env python3
"""Test script for the new validation analysis tool."""

from src.agent.agent_core import FiscalDocumentAgent
import os


def main():
    """Test the validation analysis tool with the agent."""
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not set")
        return
    
    print("=" * 60)
    print("🧪 Testing Validation Analysis Tool with Agent")
    print("=" * 60)
    
    # Initialize agent
    agent = FiscalDocumentAgent(api_key=api_key, model_name="gemini-2.5-flash-lite")
    
    # Test queries
    test_queries = [
        "qual o problema de validação mais comum em 2024?",
        "quais são os problemas de validação mais frequentes?",
        "qual erro mais ocorre nos documentos?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        response, history = agent.run(query)
        print(f"✅ Response:\n{response}")
        print("\n")


if __name__ == "__main__":
    main()
