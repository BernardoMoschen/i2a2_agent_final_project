#!/usr/bin/env python
"""Test the EXACT flow that happens in the Streamlit app."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.agent_response_parser import AgentResponseParser

# Mock response exactly as it comes from the agent
mock_agent_response = """
📊 **Relatório de Vendas Mensais**

📅 Período: 2024-01 a 2024-12
📄 Total de notas: 150
💰 Valor total: R$ 50.000,00

🎨 Gráfico gerado:

```json
{"data": [{"x": ["2024-01", "2024-02"], "y": [1000, 2000], "type": "bar"}], "layout": {"title": "Sales"}}
```
"""

print("=" * 80)
print("EXACT STREAMLIT FLOW TEST")
print("=" * 80)

print("\n[1] Simulating Streamlit chat display:")
print("-" * 80)

# This is EXACTLY what happens in display_agent_response()
parsed = AgentResponseParser.parse_response(mock_agent_response)

print(f"\nParsed result:")
print(f"  - chart type: {type(parsed['chart'])}")
print(f"  - chart value: {parsed['chart']}")
print(f"  - text: {parsed['text'][:100]}...")

# Check what st.plotly_chart would receive
if parsed["chart"]:
    print(f"\n✅ Chart extracted!")
    print(f"   st.plotly_chart() will receive: {type(parsed['chart'])}")
    print(f"   Content: {str(parsed['chart'])[:100]}...")
else:
    print(f"\n❌ No chart extracted!")

print("\n" + "=" * 80)
