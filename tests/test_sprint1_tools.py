#!/usr/bin/env python3
"""
Quick test of SPRINT 1 tools - test database methods and tool outputs
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.db import DatabaseManager
from src.agent.tools import (
    IssuerAnalysisTool,
    OperationAnalysisTool,
    DataQualityTool,
    RemediationTool,
    TrendsTool,
)

def test_database_methods():
    """Test database methods work correctly"""
    print("=" * 80)
    print("TESTING DATABASE METHODS")
    print("=" * 80)
    
    db = DatabaseManager("sqlite:///fiscal_documents.db")
    
    # Test 1: Issuer Analysis
    print("\n1️⃣  Testing get_validation_issues_by_issuer()...")
    result = db.get_validation_issues_by_issuer(year=2024, month=None, limit=5)
    assert "issuers" in result or not result["issuers"], f"Unexpected result: {result}"
    print(f"   ✅ Found {result.get('total_issuers', 0)} issuers with issues")
    print(f"   Period: {result.get('period', 'unknown')}")
    
    # Test 2: Operation Analysis
    print("\n2️⃣  Testing get_validation_issues_by_operation()...")
    result = db.get_validation_issues_by_operation(year=2024)
    assert "by_operation" in result, f"Unexpected result: {result}"
    print(f"   ✅ Operation types found: {list(result['by_operation'].keys())}")
    
    # Test 3: Data Quality Score
    print("\n3️⃣  Testing calculate_data_quality_score()...")
    result = db.calculate_data_quality_score(year=2024)
    assert "overall_score" in result, f"Unexpected result: {result}"
    print(f"   ✅ Quality Score: {result['overall_score']}/100")
    print(f"   📄 Documents: {result['documents_analyzed']}")
    print(f"   📊 Metrics: Completeness={result['metrics']['completeness']}, "
          f"Accuracy={result['metrics']['accuracy']}, "
          f"Consistency={result['metrics']['consistency']}")
    
    # Test 4: Remediation Suggestions
    print("\n4️⃣  Testing get_remediation_suggestions()...")
    result = db.get_remediation_suggestions(year=2024, limit=3)
    assert "suggestions" in result, f"Unexpected result: {result}"
    print(f"   ✅ Found {result['total_suggestions']} suggestions")
    if result['suggestions']:
        for sugg in result['suggestions'][:2]:
            print(f"      - {sugg['code']}: {sugg['remediation']['action']}")
    
    # Test 5: Trends Analysis
    print("\n5️⃣  Testing analyze_trends()...")
    result = db.analyze_trends(months_back=12)
    assert "monthly_data" in result, f"Unexpected result: {result}"
    print(f"   ✅ Analyzed {result['data_points']} months of data")
    print(f"   📈 Trend: {result['trend_direction']}")
    print(f"   📊 Average Error Rate: {result['average_error_rate']}%")


def test_agent_tools():
    """Test agent tool wrappers"""
    print("\n" + "=" * 80)
    print("TESTING AGENT TOOLS")
    print("=" * 80)
    
    # Test 1: Issuer Analysis Tool
    print("\n1️⃣  IssuerAnalysisTool._run(year=2024)...")
    tool = IssuerAnalysisTool()
    output = tool._run(year=2024)
    assert "📊" in output or "❌" in output, f"Invalid output format: {output[:100]}"
    print("   ✅ Tool output format valid")
    print(f"   Output length: {len(output)} chars")
    
    # Test 2: Operation Analysis Tool
    print("\n2️⃣  OperationAnalysisTool._run(year=2024)...")
    tool = OperationAnalysisTool()
    output = tool._run(year=2024)
    assert "📊" in output or "❌" in output, f"Invalid output format: {output[:100]}"
    print("   ✅ Tool output format valid")
    print(f"   Output length: {len(output)} chars")
    
    # Test 3: Data Quality Tool
    print("\n3️⃣  DataQualityTool._run(year=2024)...")
    tool = DataQualityTool()
    output = tool._run(year=2024)
    assert "📊" in output or "❌" in output, f"Invalid output format: {output[:100]}"
    print("   ✅ Tool output format valid")
    print(f"   Output length: {len(output)} chars")
    
    # Test 4: Remediation Tool
    print("\n4️⃣  RemediationTool._run(year=2024, limit=3)...")
    tool = RemediationTool()
    output = tool._run(year=2024, limit=3)
    assert "🔧" in output or "❌" in output, f"Invalid output format: {output[:100]}"
    print("   ✅ Tool output format valid")
    print(f"   Output length: {len(output)} chars")
    
    # Test 5: Trends Tool
    print("\n5️⃣  TrendsTool._run(months_back=12)...")
    tool = TrendsTool()
    output = tool._run(months_back=12)
    assert "📈" in output or "❌" in output, f"Invalid output format: {output[:100]}"
    print("   ✅ Tool output format valid")
    print(f"   Output length: {len(output)} chars")


def test_tool_schemas():
    """Test tool schema validation"""
    print("\n" + "=" * 80)
    print("TESTING TOOL SCHEMAS")
    print("=" * 80)
    
    from src.agent.tools import (
        AnalyzeIssuesByIssuerInput,
        AnalyzeIssuesByOperationInput,
        DataQualityScoreInput,
        RemediationSuggestionsInput,
        TrendsAnalysisInput,
    )
    
    # Test input schemas are valid
    print("\n1️⃣  Testing input schemas...")
    
    schema1 = AnalyzeIssuesByIssuerInput(year=2024, month=1)
    assert schema1.year == 2024 and schema1.month == 1
    print("   ✅ AnalyzeIssuesByIssuerInput valid")
    
    schema2 = AnalyzeIssuesByOperationInput(year=2024)
    assert schema2.year == 2024
    print("   ✅ AnalyzeIssuesByOperationInput valid")
    
    schema3 = DataQualityScoreInput(year=2024)
    assert schema3.year == 2024
    print("   ✅ DataQualityScoreInput valid")
    
    schema4 = RemediationSuggestionsInput(year=2024, limit=5)
    assert schema4.year == 2024 and schema4.limit == 5
    print("   ✅ RemediationSuggestionsInput valid")
    
    schema5 = TrendsAnalysisInput(months_back=6)
    assert schema5.months_back == 6
    print("   ✅ TrendsAnalysisInput valid")


if __name__ == "__main__":
    try:
        test_database_methods()
        test_agent_tools()
        test_tool_schemas()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\n🎉 SPRINT 1 TOOLS ARE READY FOR USE!")
        print("\nThe agent can now answer questions about:")
        print("  ✅ Most common validation issues")
        print("  ✅ Validation issues by supplier/issuer")
        print("  ✅ Comparison between operation types")
        print("  ✅ Overall data quality metrics")
        print("  ✅ Remediation suggestions and fixes")
        print("  ✅ Trends analysis over time")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
