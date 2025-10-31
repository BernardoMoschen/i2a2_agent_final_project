#!/usr/bin/env python
"""Test that all 6 chart types now have proper code fence formatting."""

import json
import re
import sys
from io import StringIO

# Test each report type's output format
def test_chart_formatting():
    """Verify all chart generation functions use code fence markers."""
    
    print("=" * 70)
    print("VALIDATING CHART FORMATTING IN business_tools.py")
    print("=" * 70)
    
    # Read the file
    with open("src/agent/business_tools.py", "r") as f:
        content = f.read()
    
    # Pattern to match code fence markers
    code_fence_pattern = r'```json\s*\n\{.*?\n```'
    
    # Define the 6 functions that should generate charts
    functions_to_check = [
        "def _generate_sales_by_month",
        "def _generate_purchases_by_month",
        "def _generate_taxes_breakdown",
        "def _generate_supplier_ranking",
        "def _generate_invoices_timeline",
        "def _generate_issues_by_severity",
    ]
    
    all_passed = True
    
    for func_name in functions_to_check:
        print(f"\n🔍 Checking {func_name}...")
        
        # Find the function
        func_start = content.find(func_name)
        if func_start == -1:
            print(f"   ❌ Function not found!")
            all_passed = False
            continue
        
        # Find the end of the function (next "def " at same indentation level)
        func_end = content.find("\n    def ", func_start + 1)
        if func_end == -1:
            func_end = content.find("\n\nclass ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        # Check for fig.to_json() in this function
        if "fig.to_json()" not in func_body:
            print(f"   ℹ️  No chart generation in this function (might be data-only)")
            continue
        
        # Check for code fence markers
        if "```json" in func_body:
            print(f"   ✅ Uses code fence markers (```json...```)")
            
            # Verify the return statement has the format
            if "f\"\"\"" in func_body:
                print(f"   ✅ Uses f-string for formatting")
            
        else:
            print(f"   ❌ MISSING code fence markers!")
            print(f"      Found fig.to_json() but no ```json wrapper")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHARTS HAVE PROPER CODE FENCE FORMATTING!")
        print("=" * 70)
        return True
    else:
        print("❌ SOME CHARTS STILL MISSING CODE FENCES!")
        print("=" * 70)
        return False


def test_parser_extraction():
    """Test that the parser can extract all the formatted charts."""
    
    print("\n" + "=" * 70)
    print("TESTING PARSER EXTRACTION WITH FORMATTED CHARTS")
    print("=" * 70)
    
    # Import the parser class
    from src.utils.agent_response_parser import AgentResponseParser
    
    # Create a mock response with a chart in code fences
    mock_response = """
    📊 **Sales Report**
    
    Some text before the chart.
    
    ```json
    {"data": [{"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}], "layout": {"title": "Test Chart"}}
    ```
    
    Some text after the chart.
    """
    
    parser = AgentResponseParser()
    remaining_text, chart_data = parser.extract_plotly_chart(mock_response)
    
    print(f"\n✓ Parser executed successfully")
    print(f"  - Has remaining text: {bool(remaining_text)}")
    print(f"  - Has chart: {chart_data is not None}")
    
    if chart_data:
        print(f"  ✅ Chart extracted successfully!")
        print(f"     Chart has data: {bool(chart_data.get('data'))}")
        print(f"     Chart has layout: {bool(chart_data.get('layout'))}")
        return True
    else:
        print(f"  ❌ Chart not extracted!")
        print(f"  Remaining text: {remaining_text[:100]}...")
        return False


if __name__ == "__main__":
    print("\n")
    
    # Test 1: Check file formatting
    formatting_ok = test_chart_formatting()
    
    # Test 2: Test parser
    try:
        parser_ok = test_parser_extraction()
    except Exception as e:
        print(f"\n❌ Parser test failed: {e}")
        parser_ok = False
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if formatting_ok and parser_ok:
        print("✅ ALL VALIDATIONS PASSED!")
        print("\n📊 Charts should now display correctly in Streamlit!")
        sys.exit(0)
    else:
        print("❌ Some validations failed. Check output above.")
        sys.exit(1)
