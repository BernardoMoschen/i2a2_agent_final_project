#!/usr/bin/env python3
"""Test chart extraction from various response formats."""

import sys
from pathlib import Path
import json

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.agent_response_parser import AgentResponseParser

def test_patterns():
    """Test extraction from different patterns."""
    
    test_cases = [
        {
            "name": "Pattern 1: ```json\\n...\\n```",
            "response": """Here's your report:

```json
{"data": [{"x": [1, 2], "y": [10, 20]}], "layout": {"title": "Test"}}
```

That's it!""",
        },
        {
            "name": "Pattern 2: ```json...\\n```",
            "response": """Report generated:

```json{"data": [{"x": [1, 2], "y": [10, 20]}], "layout": {"title": "Test"}}
```

Done!""",
        },
        {
            "name": "Pattern 3: ``` ... ```",
            "response": """Here's the chart:

```
{"data": [{"x": [1, 2], "y": [10, 20]}], "layout": {"title": "Test"}}
```

View it above!""",
        },
        {
            "name": "Pattern 4: Raw JSON",
            "response": """Analysis:
{"data": [{"x": [1, 2], "y": [10, 20]}], "layout": {"title": "Test"}}

That's your data.""",
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        response = test_case['response']
        print(f"Input Response:\n{response}\n")
        
        # Extract chart
        remaining_text, chart = AgentResponseParser.extract_plotly_chart(response)
        
        if chart:
            print("✅ Chart extracted successfully!")
            print(f"   Chart keys: {list(chart.keys())}")
            print(f"   Data traces: {len(chart.get('data', []))}")
            print(f"   Layout keys: {len(chart.get('layout', {}))}")
            print(f"\nRemaining text:\n{remaining_text}")
        else:
            print("❌ No chart found")
            print(f"Remaining text:\n{remaining_text}")

def test_real_plotly():
    """Test with real Plotly-like output."""
    print(f"\n\n{'='*60}")
    print("Test 5: Real Plotly Output")
    print(f"{'='*60}")
    
    real_plotly = """{
    "data": [
        {
            "type": "bar",
            "x": ["2024-01", "2024-02", "2024-03"],
            "y": [100, 150, 120],
            "name": "Sales"
        }
    ],
    "layout": {
        "title": "Sales by Month",
        "xaxis": {"title": "Month"},
        "yaxis": {"title": "Sales"}
    }
}"""
    
    response = f"""✅ Report Generated!

```json
{real_plotly}
```

Check the chart above!"""
    
    print(f"Response:\n{response}\n")
    
    remaining_text, chart = AgentResponseParser.extract_plotly_chart(response)
    
    if chart:
        print("✅ Real Plotly chart extracted!")
        print(f"   Title: {chart.get('layout', {}).get('title')}")
        print(f"   Data series: {len(chart.get('data', []))}")
        print(f"   First series name: {chart['data'][0].get('name')}")
    else:
        print("❌ Failed to extract real Plotly")

if __name__ == "__main__":
    test_patterns()
    test_real_plotly()
    print(f"\n{'='*60}\n✅ All extraction tests completed!\n")
