#!/usr/bin/env python3
"""Test script for validation issues chart generation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.business_tools import ReportGeneratorTool

def test_issues_report():
    """Test generating issues_by_severity report."""
    print("🧪 Testing Issues Report Generation\n")
    
    tool = ReportGeneratorTool()
    
    # Test 1: All issues
    print("Test 1: All Issues (no year filter)")
    print("-" * 50)
    result = tool._run(report_type="issues_by_severity")
    print(result)
    print("\n")
    
    # Test 2: Issues for 2024
    print("Test 2: Issues for 2024")
    print("-" * 50)
    result = tool._run(report_type="issues_by_severity", year=2024)
    print(result)
    print("\n")
    
    # Test 3: Invalid report type (should show error message)
    print("Test 3: Invalid Report Type (should show helpful error)")
    print("-" * 50)
    result = tool._run(report_type="invalid_report_type")
    print(result)
    print("\n")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_issues_report()
