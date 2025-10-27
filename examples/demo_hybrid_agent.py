"""Example usage of Hybrid Fiscal Agent.

Demonstrates the agent's hybrid capabilities:
1. Native LLM reasoning (no tools)
2. Specialized fiscal tools
3. Dynamic capabilities (code execution, web search)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.agent_core import create_agent


def example_native_intelligence():
    """Examples that DON'T require tools - agent answers directly."""
    
    print("\n" + "=" * 80)
    print("TIER 1: NATIVE INTELLIGENCE (No tools needed)")
    print("=" * 80)
    
    queries = [
        "O que é ICMS e como ele é calculado?",
        "Calculate 18% of R$ 5,432.10",
        "What's the difference between NFe and NFCe?",
        "Write Python code to validate a CNPJ number",
        "Explique a diferença entre compra e venda em termos fiscais",
    ]
    
    print("\nExample queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n💡 These queries are answered directly from the model's knowledge.")
    print("   No tools are invoked - just pure LLM reasoning!")


def example_fiscal_tools():
    """Examples that USE fiscal-specific tools."""
    
    print("\n" + "=" * 80)
    print("TIER 2: SPECIALIZED FISCAL TOOLS")
    print("=" * 80)
    
    queries = [
        "Quantas notas fiscais de compra temos no banco de dados?",
        "Generate a tax report for January 2024",
        "Valide o CNPJ 12.345.678/0001-90",
        "Search for invoices from supplier Acme Corp",
        "Gere um relatório Excel dos top 10 fornecedores por valor",
    ]
    
    print("\nExample queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n💡 These queries require database access or file operations.")
    print("   Tools like search_invoices_database, fiscal_report_export, etc. are used.")


def example_code_execution():
    """Examples that use Python code execution."""
    
    print("\n" + "=" * 80)
    print("TIER 3: DYNAMIC CAPABILITIES - Code Execution")
    print("=" * 80)
    
    queries = [
        "Calculate compound interest: R$ 10,000 at 5% annual for 10 years",
        "Parse this JSON and extract names: {'users': [{'name': 'João'}, {'name': 'Maria'}]}",
        "Find outliers in this data using statistics: [1, 2, 3, 100, 2, 3, 4]",
        "Calculate the factorial of 15",
        "What's the standard deviation of [10, 20, 30, 40, 50]?",
    ]
    
    print("\nExample queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n💡 These queries require complex calculations or data manipulation.")
    print("   The python_repl tool executes Python code in a safe sandbox.")


def example_web_search():
    """Examples that would use web search (if enabled)."""
    
    print("\n" + "=" * 80)
    print("TIER 3: DYNAMIC CAPABILITIES - Web Search")
    print("=" * 80)
    
    queries = [
        "What are the new SPED fiscal requirements for 2024?",
        "What's the current SELIC interest rate in Brazil?",
        "Find the official documentation for NFe version 4.0",
        "What are the recent changes in ICMS-ST legislation?",
    ]
    
    print("\nExample queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n💡 These queries require current/external information.")
    print("   The web_search tool searches DuckDuckGo for up-to-date data.")
    print("   ⚠️ Note: Web search must be enabled when creating the agent.")


def example_hybrid_chains():
    """Examples that combine multiple capabilities."""
    
    print("\n" + "=" * 80)
    print("HYBRID: Combining Multiple Tiers")
    print("=" * 80)
    
    queries = [
        "Get all January invoices from the database, then calculate the average using Python",
        "Search for CFOP 5102 definition online, then find all invoices using it in our database",
        "Explain what depreciation is, then calculate it for an asset worth R$ 50,000 over 10 years",
        "Generate a tax report, then write Python code to analyze the exported CSV file",
    ]
    
    print("\nExample queries:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")
    
    print("\n💡 These queries require chaining multiple tools/capabilities.")
    print("   The agent autonomously decides which tools to use and in what order!")


def interactive_demo():
    """Run an interactive demo with the agent."""
    
    print("\n" + "=" * 80)
    print("🤖 HYBRID FISCAL AGENT - INTERACTIVE DEMO")
    print("=" * 80)
    
    # Get API key
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n❌ GEMINI_API_KEY not found in environment.")
        print("   Set it with: export GEMINI_API_KEY='your-key'")
        return
    
    # Configuration
    print("\n🔧 Configuration:")
    print("   Model: gemini-2.0-flash-exp")
    print("   Temperature: 0.7 (balanced creativity)")
    print("   Code Execution: ✅ Enabled")
    print("   Web Search: ❌ Disabled (requires DuckDuckGo setup)")
    
    # Create agent
    print("\n📦 Creating hybrid agent...")
    agent = create_agent(
        api_key=api_key,
        model_name="gemini-2.0-flash-exp",
        enable_web_search=False,
        enable_code_execution=True,
    )
    print("✅ Agent created!")
    
    # Show capabilities
    capabilities = agent.get_capabilities()
    print("\n📊 Agent Capabilities:")
    print(f"   Total tools: {capabilities['total_tools']}")
    print(f"   Fiscal tools: {capabilities['fiscal_tools']}")
    print(f"   Code execution: {'✅' if capabilities['code_execution_enabled'] else '❌'}")
    print(f"   Web search: {'✅' if capabilities['web_search_enabled'] else '❌'}")
    
    # Interactive loop
    print("\n" + "=" * 80)
    print("💬 Chat Interface")
    print("=" * 80)
    print("\nCommands:")
    print("  'examples' - Show example queries")
    print("  'clear' - Clear conversation memory")
    print("  'quit' - Exit demo")
    print("\n" + "-" * 80)
    
    while True:
        try:
            query = input("\n🗣️  You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'examples':
                example_native_intelligence()
                example_fiscal_tools()
                example_code_execution()
                example_hybrid_chains()
                continue
            
            if query.lower() == 'clear':
                agent.reset_memory()
                print("✅ Memory cleared!")
                continue
            
            # Send to agent
            print("\n🤖 Agent: ", end="")
            response = agent.chat(query)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    
    print("\n" + "=" * 80)
    print("🚀 HYBRID FISCAL AGENT - EXAMPLES")
    print("=" * 80)
    
    # Show all example categories
    example_native_intelligence()
    example_fiscal_tools()
    example_code_execution()
    example_web_search()
    example_hybrid_chains()
    
    # Interactive demo
    print("\n" + "=" * 80)
    print("\nWould you like to try the interactive demo? (y/n): ", end="")
    
    try:
        choice = input().strip().lower()
        if choice in ['y', 'yes', 's', 'sim']:
            interactive_demo()
        else:
            print("\n👋 Thanks! Check the examples above to see what's possible.")
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
