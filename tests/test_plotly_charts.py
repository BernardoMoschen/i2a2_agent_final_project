#!/usr/bin/env python3
"""Quick test to verify chart generation with new Plotly integration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.services.report_generator import ReportGenerator, ReportFilters, ReportType
from src.database.db import DatabaseManager

def test_plotly_chart_generation():
    """Test generating Plotly charts."""
    print("🧪 Testing Plotly chart generation...\n")
    
    # Create sample DataFrame
    df = pd.DataFrame({
        "Period": ["2024-01", "2024-02", "2024-03", "2024-04"],
        "Document Count": [10, 15, 12, 18]
    })
    
    print(f"📊 Sample data:\n{df}\n")
    
    # Initialize generator
    try:
        db = DatabaseManager("sqlite:///fiscal_documents.db")
        generator = ReportGenerator(db)
        
        # Test chart generation
        chart_dict = generator._generate_plotly_chart(
            df,
            ReportType.VOLUME_BY_PERIOD
        )
        
        if chart_dict:
            print("✅ Chart generated successfully!")
            print(f"📈 Chart keys: {list(chart_dict.keys())}")
            print(f"📊 Data traces: {len(chart_dict.get('data', []))}")
            print(f"🎨 Layout keys: {len(chart_dict.get('layout', {})) if 'layout' in chart_dict else 0}")
            
            # Verify JSON structure
            import json
            json_str = json.dumps(chart_dict)
            print(f"\n📄 JSON size: {len(json_str)} bytes")
            print("\n✅ All tests passed!")
            return True
        else:
            print("❌ Chart generation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_plotly_chart_generation()
    sys.exit(0 if success else 1)
