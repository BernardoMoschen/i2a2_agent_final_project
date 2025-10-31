#!/usr/bin/env python
"""Debug: Check what's actually happening when parsing responses from business_tools."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.business_tools import report_generator_tool
from src.utils.agent_response_parser import AgentResponseParser
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=" * 80)
print("DEBUGGING CHART DISPLAY ISSUE")
print("=" * 80)

# Test 1: Generate a sales report
print("\n[1] GENERATING SALES REPORT...")
try:
    response = report_generator_tool._generate_sales_by_month(
        db=None,  # Mock - will fail but we can see the format
        days_back=365
    )
except Exception as e:
    # Expected to fail (no DB), but we don't care - we just want to see the format
    print(f"Note: DB operation failed (expected): {type(e).__name__}")
    # Let's create a mock response instead
    response = """
📊 **Relatório de Vendas Mensais**

📅 Período: 2024-01 a 2024-12
📄 Total de notas: 150
💰 Valor total: R$ 50.000,00
📊 Média mensal: R$ 4.166,67

🎨 Gráfico gerado:

```json
{"data": [{"x": ["2024-01", "2024-02", "2024-03"], "y": [1000, 2000, 3000], "marker": {"color": "rgb(55, 83, 109)"}, "text": ["R$ 1,000.00", "R$ 2,000.00", "R$ 3,000.00"], "textposition": "auto", "type": "bar"}], "layout": {"title": "📈 Vendas Mensais", "xaxis": {"title": "Mês"}, "yaxis": {"title": "Valor Total (R$)"}, "template": "plotly_white", "height": 400}}
```
"""

print(f"✓ Sample response created ({len(response)} chars)")
print(f"\nFirst 200 chars of response:")
print(response[:200])

# Test 2: Parse the response
print("\n[2] PARSING RESPONSE WITH AgentResponseParser...")
parsed = AgentResponseParser.parse_response(response)

print(f"✓ Response parsed")
print(f"  - Has text: {bool(parsed['text'])}")
print(f"  - Has chart: {parsed['chart'] is not None}")
print(f"  - Has file: {parsed['file'] is not None}")

if parsed['chart']:
    print(f"\n✅ CHART FOUND!")
    print(f"   Chart keys: {list(parsed['chart'].keys())}")
    print(f"   Chart has data: {bool(parsed['chart'].get('data'))}")
    print(f"   Chart has layout: {bool(parsed['chart'].get('layout'))}")
    
    if parsed['chart'].get('data'):
        print(f"   Number of series: {len(parsed['chart']['data'])}")
        print(f"   First series type: {parsed['chart']['data'][0].get('type', 'unknown')}")
else:
    print(f"\n❌ NO CHART FOUND!")
    print(f"   Text to display: {parsed['text'][:300]}")

# Test 3: Try to render it in Streamlit format
print("\n[3] CHECKING IF CHART CAN BE RENDERED BY st.plotly_chart()...")
if parsed['chart']:
    try:
        # st.plotly_chart expects a dict with 'data' and 'layout'
        # Let's verify the structure
        import plotly.graph_objects as go
        
        # Try to create a Figure from the dict
        fig = go.Figure(parsed['chart'])
        print(f"✅ Chart is valid Plotly format!")
        print(f"   Figure can be created from dict")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"⚠️  No chart to render (parse failed)")

print("\n" + "=" * 80)
