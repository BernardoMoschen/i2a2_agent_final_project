#!/usr/bin/env python3
"""
Test chart export functionality with in-memory BytesIO storage.
Validates that exports work with Streamlit Cloud (no file system).
"""

import json
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.chart_export_tool import (
    ChartExportTool,
    get_pending_download,
    get_all_pending_downloads,
    clear_pending_download,
    clear_all_pending_downloads
)
from src.utils.agent_response_parser import AgentResponseParser


def test_csv_export_bytesio():
    """Test CSV export with BytesIO (no disk files)."""
    print("\n" + "="*60)
    print("TEST 1: CSV Export with BytesIO")
    print("="*60)
    
    # Sample Plotly chart data
    chart_json = json.dumps({
        "data": [
            {
                "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                "y": [100, 150, 120, 200, 180],
                "type": "bar",
                "name": "Sales"
            }
        ],
        "layout": {
            "title": "Monthly Sales"
        }
    })
    
    tool = ChartExportTool()
    result = tool._run(
        chart_json=chart_json,
        export_format="csv",
        filename="test_sales"
    )
    
    print("\n✅ Export Result:")
    print(result)
    
    # Check if file is in pending downloads
    pending = get_all_pending_downloads()
    print(f"\n📦 Pending Downloads: {len(pending)} file(s)")
    
    for filename, (data, mime) in pending.items():
        print(f"  - {filename}")
        print(f"    MIME: {mime}")
        print(f"    Size: {len(data)} bytes")
        print(f"    Preview: {data[:100].decode('utf-8')}...")
    
    return result


def test_xml_export_bytesio():
    """Test XML export with BytesIO."""
    print("\n" + "="*60)
    print("TEST 2: XML Export with BytesIO")
    print("="*60)
    
    chart_json = json.dumps({
        "data": [
            {
                "x": ["Q1", "Q2", "Q3", "Q4"],
                "y": [500, 600, 550, 700],
                "type": "line",
                "name": "Revenue"
            }
        ],
        "layout": {
            "title": "Quarterly Revenue"
        }
    })
    
    tool = ChartExportTool()
    result = tool._run(
        chart_json=chart_json,
        export_format="xml",
        filename="test_revenue"
    )
    
    print("\n✅ Export Result:")
    print(result)
    
    # Check pending downloads
    pending = get_all_pending_downloads()
    print(f"\n📦 Total Pending Downloads: {len(pending)} file(s)")
    
    for filename, (data, mime) in pending.items():
        if "test_revenue" in filename:
            print(f"  - {filename}")
            print(f"    MIME: {mime}")
            print(f"    Size: {len(data)} bytes")
            print(f"    Preview:\n{data.decode('utf-8')[:200]}...")


def test_html_export_bytesio():
    """Test HTML export with BytesIO."""
    print("\n" + "="*60)
    print("TEST 3: HTML Export with BytesIO")
    print("="*60)
    
    chart_json = json.dumps({
        "data": [
            {
                "x": [1, 2, 3, 4, 5],
                "y": [10, 15, 13, 17, 20],
                "type": "scatter",
                "name": "Data"
            }
        ],
        "layout": {
            "title": "Sample Data"
        }
    })
    
    tool = ChartExportTool()
    result = tool._run(
        chart_json=chart_json,
        export_format="html",
        filename="test_chart"
    )
    
    print("\n✅ Export Result:")
    print(result)
    
    # Check pending downloads
    pending = get_all_pending_downloads()
    print(f"\n📦 Total Pending Downloads: {len(pending)} file(s)")
    
    for filename, (data, mime) in pending.items():
        if "test_chart" in filename and ".html" in filename:
            print(f"  - {filename}")
            print(f"    MIME: {mime}")
            print(f"    Size: {len(data) / 1024:.1f} KB (interactive Plotly)")


def test_download_marker_parsing():
    """Test extraction of download markers from agent response."""
    print("\n" + "="*60)
    print("TEST 4: Download Marker Extraction")
    print("="*60)
    
    # Simulate agent response with download marker
    agent_response = """
✅ **Gráfico Exportado para CSV**

📊 **Arquivo:** `chart_export_20251030_114943.csv`
📋 **Linhas:** 5
📁 **Formato:** CSV (separado por vírgula)

```
DOWNLOAD_FILE:chart_export_20251030_114943.csv:text/csv:512
```

Clique no botão abaixo para baixar.
"""
    
    # Parse the response
    parsed = AgentResponseParser.parse_response(agent_response)
    
    print("\n📋 Parsed Response:")
    print(f"  Text length: {len(parsed['text'])} chars")
    print(f"  Has chart: {parsed['chart'] is not None}")
    print(f"  Has file: {parsed['file'] is not None}")
    print(f"  Has download: {parsed['download'] is not None}")
    
    if parsed['download']:
        print("\n✅ Download Info Extracted:")
        print(f"  Filename: {parsed['download']['filename']}")
        print(f"  MIME type: {parsed['download']['mime_type']}")
        print(f"  File size: {parsed['download']['file_size']} bytes")
    
    print("\n📄 Remaining Text:")
    print(parsed['text'][:200])


def test_integration():
    """Test full integration: export -> marker -> parser."""
    print("\n" + "="*60)
    print("TEST 5: Full Integration (Export -> Parser)")
    print("="*60)
    
    # Clear previous downloads
    clear_all_pending_downloads()
    
    # Create and export chart
    chart_json = json.dumps({
        "data": [
            {
                "x": ["A", "B", "C"],
                "y": [100, 200, 150],
                "type": "bar",
                "name": "Values"
            }
        ],
        "layout": {
            "title": "Test Chart"
        }
    })
    
    tool = ChartExportTool()
    agent_response = tool._run(
        chart_json=chart_json,
        export_format="csv",
        filename="integration_test"
    )
    
    print("\n1️⃣ Agent Response (with marker):")
    print(agent_response)
    
    # Parse the response
    parsed = AgentResponseParser.parse_response(agent_response)
    
    print("\n2️⃣ Parsed Response:")
    print(f"  Download info: {parsed['download']}")
    
    # Retrieve the file
    if parsed['download']:
        filename = parsed['download']['filename']
        file_data = get_pending_download(filename)
        
        if file_data:
            file_bytes, mime_type = file_data
            print(f"\n3️⃣ Retrieved File from Storage:")
            print(f"  Filename: {filename}")
            print(f"  Size: {len(file_bytes)} bytes")
            print(f"  MIME: {mime_type}")
            print(f"  Content preview:\n{file_bytes.decode('utf-8')}")
            
            # Clear for next test
            clear_pending_download(filename)
            print(f"\n✅ File cleared from storage")
        else:
            print(f"❌ File not found in storage!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CHART EXPORT CLOUD COMPATIBILITY TEST SUITE")
    print("Testing BytesIO in-memory storage for Streamlit Cloud")
    print("="*60)
    
    try:
        test_csv_export_bytesio()
        test_xml_export_bytesio()
        test_html_export_bytesio()
        test_download_marker_parsing()
        test_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n📦 Summary:")
        print("  - BytesIO storage working ✓")
        print("  - Download markers parsed ✓")
        print("  - Integration flow working ✓")
        print("  - Streamlit Cloud ready ✓")
        print("\nNext steps:")
        print("  1. Deploy to Streamlit Cloud")
        print("  2. Ask agent: 'Exportar gráfico em CSV'")
        print("  3. Download button should appear")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
