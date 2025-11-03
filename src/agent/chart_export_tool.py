"""Tool for exporting charts to various file formats (XML, CSV, PNG, HTML).

Exports are returned as BytesIO objects stored in Streamlit session state
for compatibility with Streamlit Cloud (no persistent file storage).
"""

import json
import logging
from io import BytesIO, StringIO
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Global storage for exported files (keyed by filename)
# In a Streamlit app, this would be st.session_state
_pending_downloads: Dict[str, Tuple[bytes, str]] = {}


class ExportChartInput(BaseModel):
    """Input schema for chart export."""

    chart_json: str = Field(
        ...,
        description="Plotly chart JSON as string (from chart generation tool)"
    )
    export_format: str = Field(
        default="csv",
        description="Export format: 'csv', 'xml', 'html', 'png'"
    )
    filename: str = Field(
        default="chart_export",
        description="Base filename without extension"
    )


class ChartExportTool(BaseTool):
    """
    Export generated charts to various file formats.
    
    Converts Plotly chart data to CSV, XML, HTML, or PNG formats
    for easy sharing and analysis.
    """

    name: str = "export_chart"
    description: str = """
    Export a generated chart to various formats for download.
    
    Use this when user asks to:
    - "Baixar o gráfico em CSV"
    - "Exportar gráfico em XML"
    - "Salvar gráfico como PNG"
    - "Exportar dados do gráfico"
    
    Input: 
    - chart_json: The chart JSON from generate_report
    - export_format: 'csv', 'xml', 'html', or 'png'
    
    Output: File ready for download with path and summary
    """
    args_schema: type[BaseModel] = ExportChartInput

    def _run(
        self,
        chart_json: str,
        export_format: str = "csv",
        filename: str = "chart_export"
    ) -> str:
        """Export chart to specified format."""
        try:
            # Parse the chart JSON
            try:
                if isinstance(chart_json, str):
                    chart_data = json.loads(chart_json)
                else:
                    chart_data = chart_json
            except json.JSONDecodeError as e:
                return f"❌ Erro ao parsear JSON do gráfico: {str(e)}"

            # Validate it's a Plotly chart
            if not isinstance(chart_data, dict) or 'data' not in chart_data:
                return "❌ JSON inválido: não é um gráfico Plotly válido"

            # Export based on format
            export_format = export_format.lower().strip()

            if export_format == "csv":
                result = self._export_to_csv(chart_data, filename)
            elif export_format == "xml":
                result = self._export_to_xml(chart_data, filename)
            elif export_format == "html":
                result = self._export_to_html(chart_data, filename)
            elif export_format == "png":
                result = self._export_to_png(chart_data, filename)
            else:
                return f"❌ Formato desconhecido: {export_format}. Use: csv, xml, html, png"

            return result

        except Exception as e:
            logger.error(f"Error exporting chart: {e}", exc_info=True)
            return f"❌ Erro ao exportar gráfico: {str(e)}"

    def _export_to_csv(self, chart_data: Dict[str, Any], filename: str) -> str:
        """Export chart data to CSV (returns BytesIO for Streamlit Cloud)."""
        try:
            # Extract data from chart
            csv_data = self._extract_chart_data_as_dataframe(chart_data)

            if csv_data is None or csv_data.empty:
                return "❌ Nenhum dado para exportar"

            # Create BytesIO object (in-memory file)
            csv_buffer = StringIO()
            csv_data.to_csv(csv_buffer, index=False, encoding='utf-8')
            
            # Get bytes
            csv_bytes = csv_buffer.getvalue().encode('utf-8-sig')
            
            # Create filename
            filename_full = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Store in global dictionary for UI to retrieve
            _pending_downloads[filename_full] = (csv_bytes, 'text/csv')

            return f"""
✅ **Gráfico Exportado para CSV**

📊 **Arquivo:** `{filename_full}`
📋 **Linhas:** {len(csv_data)}
📁 **Formato:** CSV (separado por vírgula)

**Colunas:**
{', '.join(csv_data.columns.tolist())}

💡 **Dica:** Use o botão de download abaixo para baixar o arquivo.

```
DOWNLOAD_FILE:{filename_full}:text/csv:{len(csv_bytes)}
```
"""

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            return f"❌ Erro ao exportar para CSV: {str(e)}"

    def _export_to_xml(self, chart_data: Dict[str, Any], filename: str) -> str:
        """Export chart data to XML (returns BytesIO for Streamlit Cloud)."""
        try:
            # Get title - handle both string and dict format
            title = chart_data.get("layout", {})
            if isinstance(title, dict):
                title = title.get("title", "Gráfico")
            if isinstance(title, dict):
                title = title.get("text", "Gráfico")
            if not isinstance(title, str):
                title = str(title)

            # Build XML structure
            xml_lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<chart>',
                f'  <title>{title}</title>',
                '  <data>',
            ]

            # Add series data
            series_count = 0
            for series_idx, series in enumerate(chart_data.get('data', [])):
                series_count += 1
                series_type = series.get('type', 'unknown')
                series_name = series.get('name', f'Series {series_idx + 1}')

                xml_lines.append(f'    <series index="{series_idx}" type="{series_type}" name="{series_name}">')

                # Get x and y data
                x_data = series.get('x', [])
                y_data = series.get('y', [])

                # If y_data is a dict (binary data), skip for now
                if isinstance(y_data, dict):
                    xml_lines.append('      <!-- Dados em formato binário (pule) -->')
                else:
                    # Add data points
                    for i in range(min(len(x_data), len(y_data) if isinstance(y_data, list) else 0)):
                        x_val = x_data[i] if i < len(x_data) else ""
                        y_val = y_data[i] if isinstance(y_data, list) and i < len(y_data) else ""
                        xml_lines.append(f'      <point x="{x_val}" y="{y_val}" />')

                xml_lines.append('    </series>')

            xml_lines.extend([
                '  </data>',
                '</chart>'
            ])

            xml_content = '\n'.join(xml_lines)
            xml_bytes = xml_content.encode('utf-8')
            filename_full = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            # Store in global dictionary for UI to retrieve
            _pending_downloads[filename_full] = (xml_bytes, 'text/xml')

            return f"""
✅ **Gráfico Exportado para XML**

📊 **Arquivo:** `{filename_full}`
📈 **Séries:** {series_count}
📁 **Formato:** XML estruturado

**Estrutura:**
- title: Título do gráfico
- data: Dados das séries
  - series: Cada série de dados com pontos x,y

💡 **Dica:** Use o botão de download abaixo para baixar o arquivo.

```
DOWNLOAD_FILE:{filename_full}:text/xml:{len(xml_bytes)}
```
"""

        except Exception as e:
            logger.error(f"Error exporting to XML: {e}", exc_info=True)
            return f"❌ Erro ao exportar para XML: {str(e)}"

    def _export_to_html(self, chart_data: Dict[str, Any], filename: str) -> str:
        """Export chart to interactive HTML (returns BytesIO for Streamlit Cloud)."""
        try:
            import io

            # Create Plotly figure from data
            fig = go.Figure(chart_data)

            # Create BytesIO buffer in binary mode
            html_buffer = io.BytesIO()
            # write_html needs a file path or a text mode file, so we write to string first
            html_str = fig.to_html()
            html_bytes = html_str.encode('utf-8')
            html_buffer.write(html_bytes)
            html_buffer.seek(0)
            
            filename_full = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Store in global dictionary for UI to retrieve
            _pending_downloads[filename_full] = (html_bytes, 'text/html')

            return f"""
✅ **Gráfico Exportado para HTML (Interativo)**

📊 **Arquivo:** `{filename_full}`
📁 **Formato:** HTML interativo (Plotly)
📊 **Tamanho:** {len(html_bytes) / (1024*1024):.2f} MB

**Características:**
- ✓ Gráfico completamente interativo
- ✓ Zoom, pan, hover, download de imagem
- ✓ Funciona offline em qualquer navegador
- ✓ Sem dependências externas

💡 **Dica:** Abra o arquivo em qualquer navegador web (Chrome, Firefox, Safari, etc.)

```
DOWNLOAD_FILE:{filename_full}:text/html:{len(html_bytes)}
```
"""

        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}", exc_info=True)
            return f"❌ Erro ao exportar para HTML: {str(e)}"

    def _export_to_png(self, chart_data: Dict[str, Any], filename: str) -> str:
        """Export chart to PNG image (returns BytesIO for Streamlit Cloud)."""
        try:
            from io import BytesIO as IOBytesIO

            # Create Plotly figure from data
            fig = go.Figure(chart_data)

            # Try to save as PNG
            try:
                png_buffer = IOBytesIO()
                fig.write_image(file=png_buffer, format='png')
                png_bytes = png_buffer.getvalue()
                png_buffer.close()

                filename_full = f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
                # Store in global dictionary for UI to retrieve
                _pending_downloads[filename_full] = (png_bytes, 'image/png')

                return f"""
✅ **Gráfico Exportado para PNG**

📊 **Arquivo:** `{filename_full}`
🖼️ **Formato:** PNG (imagem rasterizada)
📏 **Tamanho:** {len(png_bytes) / 1024:.1f} KB

**Características:**
- ✓ Imagem estática em alta resolução
- ✓ Perfeita para compartilhar e impressão
- ✓ Compatível com todos os programas

💡 **Dica:** Use para relatórios, apresentações e documentos.

```
DOWNLOAD_FILE:{filename_full}:image/png:{len(png_bytes)}
```
"""
            except ImportError:
                return """
⚠️ **Exportação PNG Não Disponível**

Para exportar gráficos como PNG, é necessário ter Kaleido instalado:

```bash
pip install kaleido
```

Alternativas:
- Exporte como HTML interativo (funciona em navegadores)
- Use CSV para importar em outras ferramentas
- Screenshot manual do gráfico interativo
"""

        except Exception as e:
            logger.error(f"Error exporting to PNG: {e}", exc_info=True)
            return f"❌ Erro ao exportar para PNG: {str(e)}"

    def _extract_chart_data_as_dataframe(
        self,
        chart_data: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """Extract chart data into a pandas DataFrame."""
        try:
            rows = []

            # Process each series in the chart
            for series in chart_data.get('data', []):
                series_name = series.get('name', 'Data')
                series_type = series.get('type', 'unknown')

                x_data = series.get('x', [])
                y_data = series.get('y', [])

                # Handle binary encoded y_data (skip for now)
                if isinstance(y_data, dict):
                    continue

                # Convert to list if necessary
                if not isinstance(x_data, list):
                    x_data = list(x_data) if hasattr(x_data, '__iter__') else [x_data]
                if not isinstance(y_data, list):
                    y_data = list(y_data) if hasattr(y_data, '__iter__') else [y_data]

                # Add data points
                for i in range(min(len(x_data), len(y_data))):
                    rows.append({
                        'Series': series_name,
                        'Type': series_type,
                        'X': x_data[i],
                        'Y': y_data[i]
                    })

            if not rows:
                return None

            return pd.DataFrame(rows)

        except Exception as e:
            logger.error(f"Error extracting chart data: {e}", exc_info=True)
            return None

    async def _arun(
        self,
        chart_json: str,
        export_format: str = "csv",
        filename: str = "chart_export"
    ) -> str:
        """Async version."""
        return self._run(chart_json, export_format, filename)


def get_pending_download(filename: str) -> Optional[Tuple[bytes, str]]:
    """Retrieve a pending download by filename.
    
    Returns:
        Tuple of (file_bytes, mime_type) or None if not found
    """
    return _pending_downloads.get(filename)


def get_all_pending_downloads() -> Dict[str, Tuple[bytes, str]]:
    """Retrieve all pending downloads."""
    return dict(_pending_downloads)


def clear_pending_download(filename: str) -> bool:
    """Clear a pending download. Returns True if it was found."""
    if filename in _pending_downloads:
        del _pending_downloads[filename]
        return True
    return False


def clear_all_pending_downloads() -> None:
    """Clear all pending downloads."""
    _pending_downloads.clear()


# Create tool instance
chart_export_tool = ChartExportTool()
