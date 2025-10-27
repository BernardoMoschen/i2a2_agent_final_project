"""Test agent tool integration and availability.

This script verifies that:
1. All tools are correctly registered in ALL_TOOLS
2. Tool names are unique (no conflicts)
3. Each tool has proper metadata (name, description, args_schema)
4. Agent can access all tools
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.tools import ALL_TOOLS


def test_all_tools_registered():
    """Verify all expected tools are registered."""
    print("=" * 80)
    print("TESTING: All tools registered in ALL_TOOLS")
    print("=" * 80)
    
    expected_tools = {
        "parse_fiscal_xml",
        "validate_fiscal_document",
        "fiscal_knowledge",
        "search_invoices_database",
        "get_database_statistics",
        "fiscal_report_export",  # NEW: CSV/XLSX file export
        "generate_report",  # EXISTING: Plotly charts
        "classify_invoice",
        "validate_cnpj",
        "validate_cep",
        "lookup_ncm",
        "archive_invoice",
        "archive_all_invoices",
    }
    
    registered_tools = {tool.name for tool in ALL_TOOLS}
    
    print(f"\n✅ Total tools registered: {len(ALL_TOOLS)}")
    print(f"✅ Expected tools: {len(expected_tools)}")
    
    # Check for missing tools
    missing = expected_tools - registered_tools
    if missing:
        print(f"\n❌ MISSING TOOLS: {missing}")
        return False
    
    # Check for unexpected tools
    extra = registered_tools - expected_tools
    if extra:
        print(f"\n⚠️  EXTRA TOOLS (not expected): {extra}")
    
    print("\n✅ All expected tools are registered!")
    return True


def test_tool_names_unique():
    """Verify no duplicate tool names."""
    print("\n" + "=" * 80)
    print("TESTING: Tool name uniqueness")
    print("=" * 80)
    
    tool_names = [tool.name for tool in ALL_TOOLS]
    unique_names = set(tool_names)
    
    if len(tool_names) != len(unique_names):
        print("\n❌ DUPLICATE TOOL NAMES FOUND:")
        from collections import Counter
        duplicates = [name for name, count in Counter(tool_names).items() if count > 1]
        for dup in duplicates:
            print(f"   - '{dup}' appears {Counter(tool_names)[dup]} times")
        return False
    
    print(f"\n✅ All {len(tool_names)} tool names are unique!")
    return True


def test_tool_metadata():
    """Verify each tool has proper metadata."""
    print("\n" + "=" * 80)
    print("TESTING: Tool metadata completeness")
    print("=" * 80)
    
    all_valid = True
    
    for tool in ALL_TOOLS:
        issues = []
        
        # Check name
        if not tool.name or not isinstance(tool.name, str):
            issues.append("missing or invalid name")
        
        # Check description
        if not tool.description or not isinstance(tool.description, str):
            issues.append("missing or invalid description")
        elif len(tool.description) < 20:
            issues.append("description too short")
        
        # Check args_schema
        if not hasattr(tool, 'args_schema'):
            issues.append("missing args_schema")
        
        if issues:
            print(f"\n❌ Tool '{tool.name}' has issues:")
            for issue in issues:
                print(f"   - {issue}")
            all_valid = False
    
    if all_valid:
        print(f"\n✅ All {len(ALL_TOOLS)} tools have valid metadata!")
    
    return all_valid


def test_report_tools_separation():
    """Verify report tools are properly separated and documented."""
    print("\n" + "=" * 80)
    print("TESTING: Report tools separation")
    print("=" * 80)
    
    report_tools = [tool for tool in ALL_TOOLS if 'report' in tool.name.lower()]
    
    print(f"\n📊 Found {len(report_tools)} report-related tools:")
    for tool in report_tools:
        print(f"\n   Tool: '{tool.name}'")
        print(f"   Type: {type(tool).__name__}")
        print(f"   Purpose: {tool.description[:100]}...")
    
    # Verify both report tools exist
    names = {tool.name for tool in report_tools}
    
    if "fiscal_report_export" not in names:
        print("\n❌ Missing 'fiscal_report_export' tool (CSV/XLSX export)")
        return False
    
    if "generate_report" not in names:
        print("\n❌ Missing 'generate_report' tool (Plotly charts)")
        return False
    
    print("\n✅ Both report tools are properly registered!")
    print("   - 'fiscal_report_export': Generates CSV/XLSX files for download")
    print("   - 'generate_report': Generates interactive Plotly charts for chat")
    
    return True


def print_all_tools_summary():
    """Print summary of all available tools."""
    print("\n" + "=" * 80)
    print("ALL AVAILABLE TOOLS SUMMARY")
    print("=" * 80)
    
    # Group tools by category
    categories = {
        "Core Processing": ["parse_fiscal_xml", "validate_fiscal_document"],
        "Database": ["search_invoices_database", "get_database_statistics"],
        "Reports & Visualization": ["fiscal_report_export", "generate_report"],
        "Classification": ["classify_invoice"],
        "External Validation": ["validate_cnpj", "validate_cep", "lookup_ncm"],
        "Knowledge": ["fiscal_knowledge"],
        "Archiving": ["archive_invoice", "archive_all_invoices"],
    }
    
    for category, tool_names_list in categories.items():
        print(f"\n📁 {category}:")
        for tool in ALL_TOOLS:
            if tool.name in tool_names_list:
                print(f"   ✓ {tool.name}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("AGENT TOOLS INTEGRATION TEST")
    print("=" * 80)
    
    tests = [
        ("Tool Registration", test_all_tools_registered),
        ("Name Uniqueness", test_tool_names_unique),
        ("Tool Metadata", test_tool_metadata),
        ("Report Tools", test_report_tools_separation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print_all_tools_summary()
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED! Agent tools are properly integrated.")
    else:
        print("❌ SOME TESTS FAILED! Please review the issues above.")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
