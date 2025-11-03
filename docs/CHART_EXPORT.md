# 📊 Chart Export & Data Visualization

This document consolidates information about exporting charts and generating visualizations.

## Overview

The reporting system supports exporting charts and data in multiple formats for analysis in external tools (Excel, databases, web dashboards, etc.).

## Export Formats

### 1. CSV (Comma-Separated Values)
- **Best for**: Excel, spreadsheets, analysis
- **File size**: ~100-500 KB typically
- **Use case**: Import into Excel/Sheets, data manipulation
- **Example**: Sales by period, tax breakdown

### 2. XML (Extensible Markup Language)  
- **Best for**: Integration with enterprise systems, structured data
- **File size**: ~200-800 KB typically
- **Use case**: System-to-system data exchange, compliance records
- **Example**: Fiscal data export for archiving

### 3. HTML (HyperText Markup Language)
- **Best for**: Sharing, web viewing, email
- **File size**: ~50-200 KB typically
- **Use case**: Send report via email, view in browser, share with non-technical users
- **Example**: Executive summary report

### 4. PNG (Portable Network Graphics)
- **Best for**: Presentations, documents, visual sharing
- **File size**: ~50-300 KB typically
- **Use case**: Embed in Word/PowerPoint, print reports, social media
- **Example**: Sales trend visualization

## How to Export (Chat Interface)

### Via Portuguese Commands
```
"Exportar o gráfico em CSV"
"Exportar em XML"
"Baixar gráfico como HTML"
"Salvar gráfico como PNG"
"Consegue exportar os dados?"
"Download do gráfico em Excel"
```

### Via English Commands
```
"Export chart to CSV"
"Export to XML"
"Export as HTML"
"Save as PNG"
"Download the data"
"Export the report"
```

## Usage Flow

1. **Generate a chart** (ask agent for a report)
2. **Ask to export** (specify format)
3. **Download button appears** below the response
4. **Click to download** to your computer
5. **Use the file** in your external tool

## Technical Details

### Input to Export Tool

The `export_chart` tool receives:
- `chart_json` - The Plotly chart JSON structure
- `export_format` - Format requested (CSV, XML, HTML, PNG)
- Optional filters applied to source data

### Output Behavior

- **CSV/XML**: Returns tabular/structured data extracted from chart
- **HTML**: Returns interactive HTML page with chart
- **PNG**: Returns static image of the chart
- All exports include metadata (date, source, filters applied)

### Data Extraction

For CSV/XML exports from visualizations:
- Data is extracted from the chart series
- Timestamps, values, and labels are included
- Multi-dimensional data preserved where possible
- Headers include descriptive names

## In-Memory Architecture (Cloud Compatible)

All exports use BytesIO (in-memory storage) instead of disk files:
- ✅ Works on Streamlit Cloud (ephemeral filesystem)
- ✅ No temporary files needed
- ✅ Fast download delivery
- ✅ Automatic cleanup

Implementation:
```python
from io import BytesIO

# Export to BytesIO
buffer = BytesIO()
# ... write data to buffer ...
buffer.seek(0)

# Return for download
st.download_button(
    label="Download",
    data=buffer.getvalue(),
    file_name="report.csv",
    mime="text/csv"
)
```

## Common Export Scenarios

### Scenario 1: Monthly Tax Analysis
1. Agent generates tax breakdown chart (ICMS, IPI, PIS, COFINS)
2. User asks: "Export the tax data to CSV"
3. CSV file downloaded with tax amounts by type/period
4. Import into Excel for further analysis

### Scenario 2: Supplier Performance Report
1. Agent creates top suppliers chart
2. User asks: "Save this as HTML"
3. HTML file contains interactive chart + summary
4. Email to stakeholders

### Scenario 3: Presentation Slide
1. Agent generates sales trend chart
2. User asks: "Export as PNG"
3. PNG image downloaded
4. Insert into PowerPoint presentation

### Scenario 4: System Integration
1. Agent creates invoice summary
2. User asks: "Export to XML"
3. XML file with structured fiscal data
4. Import into accounting system

## API Reference

### export_chart Tool

**Purpose**: Convert chart visualizations to various formats

**Input Parameters**:
```python
chart_json: str          # Plotly JSON structure
export_format: str       # 'csv', 'xml', 'html', or 'png'
include_headers: bool    # Include data headers (default: True)
```

**Output**: 
- BytesIO buffer containing exported data
- Response with download button

**Example**:
```
User: "Export the sales chart to CSV"
Agent: Calls export_chart(chart_json=<data>, export_format='csv')
Response: CSV file ready to download
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Download button doesn't appear | Chart not properly exported | Ask agent to regenerate chart first |
| File too large | Complex dataset | Try CSV instead of HTML |
| PNG quality low | Chart resolution | Regenerate with specific dimensions |
| XML parsing error | Malformed XML | Check encoding, retry export |

## Performance Considerations

- **CSV exports**: Fastest (100-500ms)
- **XML exports**: Medium (200-800ms)
- **HTML exports**: Medium (300-1000ms)
- **PNG exports**: Slower (1-3s for complex charts)

All exports are cached in session memory for 1 hour to avoid regeneration.

## Cloud Deployment Notes

### Streamlit Cloud Compatibility

The export system is fully compatible with Streamlit Cloud:
- ✅ No disk I/O required (uses BytesIO)
- ✅ All exports work within ephemeral environment
- ✅ Download buttons properly streamed to user
- ✅ Session memory automatically cleaned up

### Environment Variables

No special configuration needed. Exports use only standard Python libraries:
- `io` - BytesIO buffers
- `csv` - CSV writing
- `xml.etree` - XML generation
- `plotly` - Chart rendering to PNG

## Related Documents

- [REPORTS.md](./REPORTS.md) - Main reporting system
- [AGENT_COMMUNICATION.md](./AGENT_COMMUNICATION.md) - How agent uses tools
