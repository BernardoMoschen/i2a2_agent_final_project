#!/usr/bin/env python
"""Test chart export functionality."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.chart_export_tool import chart_export_tool

print("=" * 80)
print("TEST: Chart Export Tool")
print("=" * 80)

# Create a sample chart JSON
sample_chart = {
    "data": [
        {
            "type": "bar",
            "name": "Sales",
            "x": ["Jan", "Feb", "Mar", "Apr", "May"],
            "y": [1000, 2000, 1500, 3000, 2500]
        }
    ],
    "layout": {
        "title": "Monthly Sales",
        "xaxis": {"title": "Month"},
        "yaxis": {"title": "Revenue"}
    }
}

chart_json_str = json.dumps(sample_chart)

print("\n[1] Testing CSV Export...")
print("-" * 80)
result_csv = chart_export_tool._run(
    chart_json=chart_json_str,
    export_format="csv",
    filename="test_sales"
)
print(result_csv)

print("\n[2] Testing XML Export...")
print("-" * 80)
result_xml = chart_export_tool._run(
    chart_json=chart_json_str,
    export_format="xml",
    filename="test_sales"
)
print(result_xml)

print("\n[3] Testing HTML Export...")
print("-" * 80)
result_html = chart_export_tool._run(
    chart_json=chart_json_str,
    export_format="html",
    filename="test_sales"
)
print(result_html)

print("\n[4] Testing PNG Export (may require kaleido)...")
print("-" * 80)
result_png = chart_export_tool._run(
    chart_json=chart_json_str,
    export_format="png",
    filename="test_sales"
)
print(result_png)

print("\n[5] Testing Invalid Format...")
print("-" * 80)
result_invalid = chart_export_tool._run(
    chart_json=chart_json_str,
    export_format="pdf",
    filename="test_sales"
)
print(result_invalid)

print("\n" + "=" * 80)
print("✅ All tests completed!")
print("=" * 80)
