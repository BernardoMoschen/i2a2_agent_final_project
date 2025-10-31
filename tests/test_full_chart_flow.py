#!/usr/bin/env python3
"""Debug script to test the full chart generation and display flow."""

import sys
from pathlib import Path
import json

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.report_generator import ReportGenerator, ReportFilters, ReportType
from src.database.db import DatabaseManager
from src.utils.agent_response_parser import AgentResponseParser

def test_full_flow():
    """Test the complete flow: generate -> format -> parse -> display."""
    
    print("="*70)
    print("FULL CHART DISPLAY FLOW TEST")
    print("="*70)
    
    try:
        # Step 1: Generate report data
        print("\n[1] Generating report data...")
        db = DatabaseManager("sqlite:///fiscal_documents.db")
        generator = ReportGenerator(db)
        
        # Get data for volume by period
        df = generator.get_report_data(
            report_type=ReportType.VOLUME_BY_PERIOD,
            filters=ReportFilters()
        )
        
        if df is None or df.empty:
            print("❌ No data available for report!")
            return False
        
        print(f"✅ Got DataFrame with {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        
        # Step 2: Generate Plotly chart
        print("\n[2] Generating Plotly chart...")
        chart_dict = generator._generate_plotly_chart(df, ReportType.VOLUME_BY_PERIOD)
        
        if not chart_dict:
            print("❌ Chart generation failed!")
            return False
        
        print(f"✅ Chart generated")
        print(f"   Keys: {list(chart_dict.keys())}")
        print(f"   Data series: {len(chart_dict.get('data', []))}")
        
        # Step 3: Create agent response (simulating what report_tool does)
        print("\n[3] Creating agent response...")
        chart_json = json.dumps(chart_dict)
        response = f"""✅ **Report Generated Successfully!**

📊 **Report Type:** Volume By Period
📄 **Rows:** {len(df)}

**Report Summary:**
This report shows the document volume over time periods.

📈 Chart Visualization:

```json
{chart_json}
```

Done! Check the chart above."""
        
        print(f"✅ Response created ({len(response)} chars)")
        print(f"   JSON size: {len(chart_json)} chars")
        
        # Step 4: Test parser extraction
        print("\n[4] Testing parser extraction...")
        remaining_text, extracted_chart = AgentResponseParser.extract_plotly_chart(response)
        
        if not extracted_chart:
            print("❌ Parser failed to extract chart!")
            print(f"\nResponse text:\n{response[:500]}...")
            return False
        
        print(f"✅ Chart extracted successfully!")
        print(f"   Chart keys: {list(extracted_chart.keys())}")
        print(f"   Data series: {len(extracted_chart.get('data', []))}")
        print(f"   Remaining text length: {len(remaining_text)} chars")
        
        # Step 5: Test full parse_response
        print("\n[5] Testing full response parsing...")
        parsed = AgentResponseParser.parse_response(response)
        
        print(f"✅ Response parsed!")
        print(f"   Has chart: {parsed['chart'] is not None}")
        print(f"   Has file: {parsed['file'] is not None}")
        print(f"   Text length: {len(parsed['text'])} chars")
        
        if parsed['chart']:
            print(f"   Chart data keys: {list(parsed['chart'].keys())}")
        
        # Step 6: Verify chart can be rendered
        print("\n[6] Verifying chart can be rendered...")
        if parsed['chart'] and 'data' in parsed['chart'] and 'layout' in parsed['chart']:
            print(f"✅ Chart is valid Plotly format!")
            print(f"   Data points in first series: {len(parsed['chart']['data'][0].get('x', []))}")
            print(f"   Layout title: {parsed['chart']['layout'].get('title', 'N/A')}")
            
            # Can we convert back to JSON?
            test_json = json.dumps(parsed['chart'])
            print(f"   Can convert to JSON: ✅ ({len(test_json)} bytes)")
        else:
            print("❌ Chart is not valid Plotly format!")
            return False
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED - CHART SHOULD DISPLAY!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_flow()
    sys.exit(0 if success else 1)
