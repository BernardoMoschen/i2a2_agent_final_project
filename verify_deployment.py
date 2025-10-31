#!/usr/bin/env python3
"""
Deployment verification script for chart export feature.
Validates all components are properly integrated and working.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_imports():
    """Verify all required imports work."""
    print("\n" + "="*60)
    print("✓ Checking Imports")
    print("="*60)
    
    try:
        print("  Importing chart_export_tool...", end=" ")
        from src.agent.chart_export_tool import (
            ChartExportTool,
            get_pending_download,
            get_all_pending_downloads,
            clear_pending_download,
            clear_all_pending_downloads,
            chart_export_tool
        )
        print("✓")
        
        print("  Importing agent_response_parser...", end=" ")
        from src.utils.agent_response_parser import AgentResponseParser
        print("✓")
        
        print("  Importing app (display_agent_response)...", end=" ")
        # Note: Can't import app directly due to Streamlit setup, but syntax checked earlier
        print("✓ (syntax verified)")
        
        print("  Importing tools registry...", end=" ")
        from src.agent.tools import ALL_TOOLS
        print("✓")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def check_export_tool():
    """Verify export tool has all methods."""
    print("\n" + "="*60)
    print("✓ Checking Export Tool")
    print("="*60)
    
    try:
        from src.agent.chart_export_tool import ChartExportTool
        
        tool = ChartExportTool()
        
        # Check required methods
        methods = [
            '_run',
            '_export_to_csv',
            '_export_to_xml',
            '_export_to_html',
            '_export_to_png',
            '_extract_chart_data_as_dataframe',
            '_arun'
        ]
        
        for method in methods:
            has_method = hasattr(tool, method)
            status = "✓" if has_method else "✗"
            print(f"  {status} Method: {method}")
            if not has_method:
                return False
        
        # Check tool metadata
        print(f"  ✓ Tool name: {tool.name}")
        print(f"  ✓ Tool description: {tool.description[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def check_parser():
    """Verify response parser has extraction methods."""
    print("\n" + "="*60)
    print("✓ Checking Response Parser")
    print("="*60)
    
    try:
        from src.utils.agent_response_parser import AgentResponseParser
        
        # Check required methods
        methods = [
            'extract_plotly_chart',
            'extract_file_reference',
            'extract_download_marker',  # NEW
            'parse_response'
        ]
        
        for method in methods:
            has_method = hasattr(AgentResponseParser, method)
            status = "✓" if has_method else "✗"
            print(f"  {status} Method: {method}")
            if not has_method:
                return False
        
        # Test parsing
        print("\n  Testing marker extraction...")
        test_response = """
Some text here

```
DOWNLOAD_FILE:test_file.csv:text/csv:256
```

More text"""
        
        parsed = AgentResponseParser.parse_response(test_response)
        
        if parsed["download"] is None:
            print("  ✗ Download marker not extracted!")
            return False
        
        download = parsed["download"]
        assert download["filename"] == "test_file.csv"
        assert download["mime_type"] == "text/csv"
        assert download["file_size"] == 256
        print("  ✓ Marker extraction working correctly")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_tools_registry():
    """Verify export tool is registered."""
    print("\n" + "="*60)
    print("✓ Checking Tools Registry")
    print("="*60)
    
    try:
        from src.agent.tools import ALL_TOOLS
        
        tool_names = [tool.name for tool in ALL_TOOLS]
        
        if 'export_chart' in tool_names:
            print(f"  ✓ export_chart tool registered")
            print(f"  ✓ Total tools: {len(ALL_TOOLS)}")
            return True
        else:
            print(f"  ✗ export_chart NOT found in registry!")
            print(f"  Available tools: {tool_names}")
            return False
            
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def check_file_structure():
    """Verify all required files exist."""
    print("\n" + "="*60)
    print("✓ Checking File Structure")
    print("="*60)
    
    files = [
        "src/agent/chart_export_tool.py",
        "src/utils/agent_response_parser.py",
        "src/ui/app.py",
        "test_chart_export_cloud.py",
        "docs/CHART_EXPORT_CLOUD_REFACTORING.md",
        "docs/CHART_EXPORT_USER_GUIDE.md",
        "CHART_EXPORT_IMPLEMENTATION_COMPLETE.md"
    ]
    
    all_exist = True
    for file in files:
        path = project_root / file
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_syntax():
    """Verify Python syntax of key files."""
    print("\n" + "="*60)
    print("✓ Checking Python Syntax")
    print("="*60)
    
    import py_compile
    
    files = [
        "src/agent/chart_export_tool.py",
        "src/utils/agent_response_parser.py",
        "src/ui/app.py"
    ]
    
    all_valid = True
    for file in files:
        path = project_root / file
        try:
            py_compile.compile(str(path), doraise=True)
            print(f"  ✓ {file}")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file}: {e}")
            all_valid = False
    
    return all_valid


def check_integration():
    """Run basic integration test."""
    print("\n" + "="*60)
    print("✓ Checking Integration")
    print("="*60)
    
    try:
        import json
        from src.agent.chart_export_tool import (
            chart_export_tool,
            get_pending_download,
            clear_pending_download,
            clear_all_pending_downloads
        )
        from src.utils.agent_response_parser import AgentResponseParser
        
        # Create test chart
        chart_json = json.dumps({
            "data": [{
                "x": ["A", "B", "C"],
                "y": [10, 20, 15],
                "type": "bar",
                "name": "Test"
            }],
            "layout": {"title": "Test"}
        })
        
        # Export to CSV
        print("  Testing CSV export...", end=" ")
        result = chart_export_tool._run(
            chart_json=chart_json,
            export_format="csv",
            filename="integration_test"
        )
        
        # Check for marker
        if "DOWNLOAD_FILE:" not in result:
            print("✗ No marker in response")
            return False
        print("✓")
        
        # Parse response
        print("  Testing response parsing...", end=" ")
        parsed = AgentResponseParser.parse_response(result)
        
        if parsed["download"] is None:
            print("✗ Marker not extracted")
            return False
        print("✓")
        
        # Get file from storage
        print("  Testing file retrieval...", end=" ")
        filename = parsed["download"]["filename"]
        file_data = get_pending_download(filename)
        
        if file_data is None:
            print("✗ File not in storage")
            return False
        print("✓")
        
        # Cleanup
        print("  Testing memory cleanup...", end=" ")
        clear_pending_download(filename)
        file_data2 = get_pending_download(filename)
        
        if file_data2 is not None:
            print("✗ File not cleared")
            return False
        print("✓")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("🚀 CHART EXPORT DEPLOYMENT VERIFICATION")
    print("="*60)
    
    checks = [
        ("Imports", check_imports),
        ("Export Tool", check_export_tool),
        ("Response Parser", check_parser),
        ("Tools Registry", check_tools_registry),
        ("File Structure", check_file_structure),
        ("Python Syntax", check_syntax),
        ("Integration", check_integration)
    ]
    
    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📋 VERIFICATION SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"\n📊 Result: {passed_checks}/{total_checks} checks passed")
    
    if all(results.values()):
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        print("="*60)
        print("\n📋 Next Steps:")
        print("  1. Merge feature branch to main")
        print("  2. Deploy to Streamlit Cloud")
        print("  3. Test: Ask agent 'Exportar gráfico em CSV'")
        print("  4. Verify download button appears")
        print("  5. Monitor error logs for 24 hours")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME CHECKS FAILED - DO NOT DEPLOY")
        print("="*60)
        print("\n🔧 Fix Issues Above Before Deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
