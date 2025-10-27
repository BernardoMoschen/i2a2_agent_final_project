"""Interactive agent chat demo for testing tool autonomy.

This script demonstrates the agent's ability to autonomously use all available
tools via natural language chat in Portuguese or English.

Usage:
    python examples/demo_agent_chat.py --api-key YOUR_GEMINI_KEY

Interactive mode - type queries and see how the agent selects and uses tools.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.agent_core import create_agent
from src.agent.tools import ALL_TOOLS


def print_header():
    """Print welcome header."""
    print("\n" + "=" * 80)
    print("🤖 FISCAL DOCUMENT AGENT - INTERACTIVE CHAT DEMO")
    print("=" * 80)
    print("\nThis demo tests the agent's autonomous tool usage via chat.")
    print(f"Available tools: {len(ALL_TOOLS)}")
    print("\nTool categories:")
    print("  📄 Document Processing: parse_fiscal_xml, validate_fiscal_document")
    print("  🗄️  Database: search_invoices_database, get_database_statistics")
    print("  📊 Reports: fiscal_report_export (CSV/XLSX), generate_report (charts)")
    print("  🏷️  Classification: classify_invoice")
    print("  ✓  Validation: validate_cnpj, validate_cep, lookup_ncm")
    print("  📚 Knowledge: fiscal_knowledge")
    print("  📦 Archiving: archive_invoice, archive_all_invoices")
    print("\n" + "=" * 80)


def print_tools_list():
    """Print detailed list of all available tools."""
    print("\n" + "=" * 80)
    print("AVAILABLE TOOLS DETAIL")
    print("=" * 80)
    
    for i, tool in enumerate(ALL_TOOLS, 1):
        print(f"\n{i}. {tool.name}")
        print(f"   Type: {type(tool).__name__}")
        # Print first line of description
        desc_lines = tool.description.strip().split('\n')
        first_line = desc_lines[0] if desc_lines else "No description"
        print(f"   {first_line}")


def print_example_queries():
    """Print example queries for testing."""
    print("\n" + "=" * 80)
    print("EXAMPLE QUERIES TO TEST")
    print("=" * 80)
    
    examples = [
        {
            "category": "📊 Report Generation (Portuguese)",
            "queries": [
                "Gere um relatório de documentos com falhas de janeiro 2024",
                "Crie relatório Excel dos top 10 fornecedores por valor",
                "Exportar para CSV todos os impostos do último trimestre",
            ]
        },
        {
            "category": "📈 Interactive Charts (English)",
            "queries": [
                "Show me a chart of taxes breakdown",
                "Generate sales by month visualization",
                "Create supplier ranking chart",
            ]
        },
        {
            "category": "🔍 Database Search",
            "queries": [
                "Busque todas as notas fiscais de compra com falhas",
                "Search for invoices from supplier CNPJ 12.345.678/0001-90",
                "Mostre estatísticas do banco de dados",
            ]
        },
        {
            "category": "✓ Validation",
            "queries": [
                "Valide o CNPJ 12.345.678/0001-90",
                "Validate CEP 01310-100",
                "Lookup NCM code 84714900",
            ]
        },
        {
            "category": "🔗 Multi-tool Chains",
            "queries": [
                "Busque notas com falhas e exporte para Excel",
                "Valide este CNPJ e mostre todas as notas dele",
                "Gere relatório de impostos e crie um gráfico",
            ]
        },
    ]
    
    for example in examples:
        print(f"\n{example['category']}:")
        for query in example['queries']:
            print(f"  • {query}")


def run_interactive_mode(agent):
    """Run interactive chat mode."""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("\nType your queries in Portuguese or English.")
    print("Commands:")
    print("  'help' - Show example queries")
    print("  'tools' - List all available tools")
    print("  'quit' or 'exit' - Exit demo")
    print("\n" + "-" * 80)
    
    while True:
        try:
            # Get user input
            query = input("\n🗣️  You: ").strip()
            
            if not query:
                continue
            
            # Check for commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print_example_queries()
                continue
            
            if query.lower() == 'tools':
                print_tools_list()
                continue
            
            # Send query to agent
            print("\n🤖 Agent: Processing query...")
            print("=" * 80)
            
            try:
                response = agent.process_query(query)
                print(f"\n{response}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def run_batch_test_mode(agent):
    """Run batch tests with predefined queries."""
    print("\n" + "=" * 80)
    print("BATCH TEST MODE")
    print("=" * 80)
    
    test_queries = [
        # Report generation
        {
            "query": "Gere relatório de documentos com falhas de janeiro 2024",
            "expected_tool": "fiscal_report_export",
            "description": "Portuguese report request with date filter",
        },
        {
            "query": "Show me taxes by period for last 90 days",
            "expected_tool": "fiscal_report_export",
            "description": "English report request with relative date",
        },
        # Interactive charts
        {
            "query": "Generate taxes breakdown chart",
            "expected_tool": "generate_report",
            "description": "Chart generation request",
        },
        # Database operations
        {
            "query": "Search for purchase invoices with issues",
            "expected_tool": "search_invoices_database",
            "description": "Database search with filters",
        },
        {
            "query": "Get database statistics",
            "expected_tool": "get_database_statistics",
            "description": "Database stats request",
        },
        # Validation
        {
            "query": "Validate CNPJ 12.345.678/0001-90",
            "expected_tool": "validate_cnpj",
            "description": "CNPJ validation",
        },
        # Knowledge
        {
            "query": "What is CFOP 5102?",
            "expected_tool": "fiscal_knowledge",
            "description": "Fiscal knowledge question",
        },
    ]
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(test_queries)}: {test['description']}")
        print(f"{'=' * 80}")
        print(f"Query: {test['query']}")
        print(f"Expected tool: {test['expected_tool']}")
        print(f"{'-' * 80}")
        
        try:
            response = agent.process_query(test['query'])
            print(f"\nResponse:\n{response}")
            
            # Check if expected tool was used (this is a simplified check)
            tool_used = test['expected_tool'] in str(response).lower()
            results.append({
                "test": test['description'],
                "passed": tool_used,
                "query": test['query'],
            })
            
            status = "✅ LIKELY PASSED" if tool_used else "⚠️  NEEDS VERIFICATION"
            print(f"\n{status}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results.append({
                "test": test['description'],
                "passed": False,
                "query": test['query'],
                "error": str(e),
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("BATCH TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['passed'] else "❌"
        print(f"{status} Test {i}: {result['test']}")
        if 'error' in result:
            print(f"   Error: {result['error']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive agent chat demo for testing tool autonomy"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Gemini API key (or set GEMINI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.0-flash-exp",
        help="Model to use (default: gemini-2.0-flash-exp)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["interactive", "batch"],
        default="interactive",
        help="Run mode: interactive chat or batch tests (default: interactive)",
    )
    
    args = parser.parse_args()
    
    # Get API key
    import os
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: Gemini API key required.")
        print("\nProvide via:")
        print("  --api-key YOUR_KEY")
        print("  or set GEMINI_API_KEY environment variable")
        return 1
    
    # Print header
    print_header()
    
    # Create agent
    print(f"\n🔧 Creating agent with model: {args.model}")
    try:
        agent = create_agent(api_key=api_key, model_name=args.model)
        print("✅ Agent created successfully!")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return 1
    
    # Run appropriate mode
    if args.mode == "interactive":
        print("\n💬 Starting interactive mode...")
        print_example_queries()
        run_interactive_mode(agent)
    else:
        print("\n🧪 Starting batch test mode...")
        run_batch_test_mode(agent)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
