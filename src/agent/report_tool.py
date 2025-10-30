"""Report generation tool for LangChain agent.

Supports natural language queries in English and Portuguese for generating reports.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.database.db import DatabaseManager
from src.services.report_generator import ReportFilters, ReportGenerator, ReportType

logger = logging.getLogger(__name__)


class ReportRequestInput(BaseModel):
    """Input schema for report generation requests."""

    query: str = Field(
        description=(
            "Natural language query for report generation. "
            "Examples: "
            "'report of XMLs with issues between January and March', "
            "'relatório de falhas do mês de janeiro de 2024', "
            "'report of document X', "
            "'top 10 suppliers by value', "
            "'cache effectiveness report', "
            "'unclassified documents report'"
        )
    )
    output_format: str = Field(
        default="xlsx",
        description="Output format: 'csv' or 'xlsx' (default: 'xlsx')"
    )
    include_chart: bool = Field(
        default=True,
        description="Whether to generate visualization chart (default: True)"
    )


class FiscalReportExportTool(BaseTool):
    """Tool for generating fiscal document reports based on natural language queries."""

    name: str = "fiscal_report_export"
    description: str = """
    Generate Excel/CSV reports and visualizations from fiscal documents database.
    
    🎯 USAGE INSTRUCTIONS:
    - Accepts natural language queries in ENGLISH or PORTUGUESE
    - Automatically detects report type and filters from query
    - Generates XLSX (default) or CSV files with charts for DOWNLOAD
    
    ⚠️ NOTE: This tool generates FILES for download. For interactive charts 
    in the chat, use 'generate_report' tool instead.
    
    📊 AVAILABLE REPORTS:
    
    VALIDATION REPORTS:
    - "documents with issues" / "xmls com falhas"
    - "documents without issues" / "xmls sem falhas"
    - "issues by type" / "falhas por tipo"
    - "issues by issuer" / "falhas por fornecedor"
    - "issues by severity" / "falhas por gravidade"
    
    FINANCIAL REPORTS:
    - "taxes by period" / "impostos por período"
    - "total value by period" / "valor total por período"
    - "top suppliers" / "principais fornecedores"
    - "costs by center" / "custos por centro"
    
    OPERATIONAL REPORTS:
    - "by operation type" / "por tipo de operação"
    - "by document type" / "por tipo de documento"
    - "volume by period" / "volume por período"
    
    CLASSIFICATION REPORTS:
    - "cache effectiveness" / "efetividade do cache"
    - "unclassified documents" / "documentos não classificados"
    - "llm fallback usage" / "uso de fallback LLM"
    
    PRODUCTS REPORTS:
    - "top products by NCM" / "principais produtos por NCM"
    - "analysis by CFOP" / "análise por CFOP"
    - "items with issues" / "itens com problemas"
    
    🔍 FILTER EXAMPLES:
    - "between January and March 2024"
    - "do mês de janeiro de 2024"
    - "in the last 30 days"
    - "from supplier X"
    - "NFe documents only"
    - "purchase operations"
    - "severity error"
    
    📝 QUERY EXAMPLES:
    - "report of xmls with issues between january and march"
    - "relatório de falhas do mês de janeiro de 2024"
    - "top 10 suppliers by value in the last 90 days"
    - "cache effectiveness report"
    - "unclassified documents report"
    - "taxes by period for purchases only"
    - "documents with error severity issues"
    
    Returns: Dictionary with file path, row count, and metadata
    """
    args_schema: type[BaseModel] = ReportRequestInput

    def _run(
        self,
        query: str,
        output_format: str = "xlsx",
        include_chart: bool = True,
    ) -> str:
        """Generate report based on natural language query."""
        try:
            import json
            
            # Parse query to extract report type and filters
            report_type, filters = self._parse_query(query)
            
            if not report_type:
                return (
                    "❌ Could not determine report type from query. "
                    "Please specify what kind of report you want. "
                    "Examples: 'documents with issues', 'top suppliers', 'cache effectiveness'"
                )
            
            # Initialize database and generator
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            generator = ReportGenerator(db)
            
            # Generate report
            result = generator.generate_report(
                report_type=report_type,
                filters=filters,
                output_format=output_format,
                include_chart=include_chart,
            )
            
            # Get the DataFrame for chart generation
            df = generator.get_report_data(report_type=report_type, filters=filters)
            
            # Generate Plotly chart (Cloud-compatible)
            chart_dict = None
            if include_chart and df is not None and not df.empty:
                chart_dict = generator._generate_plotly_chart(df, report_type)
            
            # Format response
            response = f"""
✅ **Report Generated Successfully!**

📊 **Report Type:** {report_type.replace('_', ' ').title()}
📁 **File:** `{result['file_path']}`
 **Rows:** {result['row_count']}
⏰ **Generated:** {result['generated_at']}

**Filters Applied:**
"""
            
            # Add filter details
            for key, value in result['filters'].items():
                if value is not None:
                    response += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            # Add report-specific metadata
            if 'total_documents' in result:
                response += f"\n📊 Total Documents: {result['total_documents']}"
            if 'total_value' in result:
                response += f"\n💰 Total Value: R$ {result['total_value']:,.2f}"
            if 'total_issues' in result:
                response += f"\n⚠️ Total Issues: {result['total_issues']}"
            if 'total_cache_entries' in result:
                response += f"\n🗄️ Cache Entries: {result['total_cache_entries']}"
                response += f"\n🎯 Cache Hits: {result['total_cache_hits']}"
            
            response += f"\n\n💡 **Tip:** Open the file in Excel/LibreOffice to view full data."
            
            # Append Plotly chart as JSON if available
            if chart_dict:
                response += f"\n\n```json\n{json.dumps(chart_dict)}\n```"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return f"❌ Error generating report: {str(e)}"

    async def _arun(
        self,
        query: str,
        output_format: str = "xlsx",
        include_chart: bool = True,
    ) -> str:
        """Async version."""
        return self._run(query, output_format, include_chart)

    def _parse_query(self, query: str) -> tuple[Optional[str], ReportFilters]:
        """Parse natural language query to extract report type and filters.
        
        Args:
            query: Natural language query in English or Portuguese
            
        Returns:
            Tuple of (report_type, filters)
        """
        query_lower = query.lower()
        
        # Initialize filters
        filters = ReportFilters()
        
        # ========== DETECT REPORT TYPE ==========
        report_type = None
        
        # Validation reports
        if any(word in query_lower for word in ["with issues", "com falhas", "with errors", "com erros"]):
            report_type = ReportType.DOCUMENTS_WITH_ISSUES
        elif any(word in query_lower for word in ["without issues", "sem falhas", "approved", "aprovados"]):
            report_type = ReportType.DOCUMENTS_WITHOUT_ISSUES
        elif any(word in query_lower for word in ["issues by type", "falhas por tipo", "issue types"]):
            report_type = ReportType.ISSUES_BY_TYPE
        elif any(word in query_lower for word in ["issues by issuer", "falhas por fornecedor", "issues by supplier"]):
            report_type = ReportType.ISSUES_BY_ISSUER
        elif any(word in query_lower for word in ["issues by severity", "falhas por gravidade", "by severity"]):
            report_type = ReportType.ISSUES_BY_SEVERITY
            
        # Financial reports
        elif any(word in query_lower for word in ["taxes by period", "impostos por período", "tax breakdown"]):
            report_type = ReportType.TAXES_BY_PERIOD
        elif any(word in query_lower for word in ["total value", "valor total por", "value by period"]):
            report_type = ReportType.TOTAL_VALUE_BY_PERIOD
        elif any(word in query_lower for word in ["top suppliers", "principais fornecedores", "suppliers by value"]):
            report_type = ReportType.TOP_SUPPLIERS_BY_VALUE
        elif any(word in query_lower for word in ["costs by center", "custos por centro", "cost center"]):
            report_type = ReportType.COSTS_BY_CENTER
            
        # Operational reports
        elif any(word in query_lower for word in ["by operation type", "por tipo de operação", "operation breakdown"]):
            report_type = ReportType.DOCUMENTS_BY_OPERATION_TYPE
        elif any(word in query_lower for word in ["by document type", "por tipo de documento", "document breakdown"]):
            report_type = ReportType.DOCUMENTS_BY_DOCUMENT_TYPE
        elif any(word in query_lower for word in ["volume by period", "volume por período", "document volume"]):
            report_type = ReportType.VOLUME_BY_PERIOD
            
        # Classification reports
        elif any(word in query_lower for word in ["cache effectiveness", "efetividade do cache", "cache performance"]):
            report_type = ReportType.CACHE_EFFECTIVENESS
        elif any(word in query_lower for word in ["unclassified", "não classificados", "not classified"]):
            report_type = ReportType.UNCLASSIFIED_DOCUMENTS
        elif any(word in query_lower for word in ["llm fallback", "fallback usage", "uso de fallback"]):
            report_type = ReportType.LLM_FALLBACK_USAGE
        elif any(word in query_lower for word in ["by cost center", "por centro de custo"]):
            report_type = ReportType.CLASSIFICATION_BY_COST_CENTER
            
        # Products reports
        elif any(word in query_lower for word in ["top products", "principais produtos", "products by ncm"]):
            report_type = ReportType.TOP_PRODUCTS_BY_NCM
        elif any(word in query_lower for word in ["by cfop", "por cfop", "cfop analysis"]):
            report_type = ReportType.ANALYSIS_BY_CFOP
        elif any(word in query_lower for word in ["items with issues", "itens com problemas"]):
            report_type = ReportType.ITEMS_WITH_ISSUES
        
        # ========== EXTRACT FILTERS ==========
        
        # Date filters - Portuguese months
        months_pt = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        
        # Date filters - English months
        months_en = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        # Extract year
        year_match = re.search(r'\b(20\d{2})\b', query_lower)
        year = int(year_match.group(1)) if year_match else datetime.now().year
        
        # Check for month-based filters
        for month_name, month_num in {**months_pt, **months_en}.items():
            if month_name in query_lower:
                # Set start and end to cover entire month
                filters.start_date = datetime(year, month_num, 1)
                # Last day of month
                if month_num == 12:
                    filters.end_date = datetime(year, 12, 31, 23, 59, 59)
                else:
                    next_month = datetime(year, month_num + 1, 1)
                    filters.end_date = next_month - timedelta(seconds=1)
                break
        
        # Check for "between X and Y" pattern
        between_match = re.search(
            r'between\s+(\w+)\s+and\s+(\w+)',
            query_lower
        )
        if between_match:
            start_month_name = between_match.group(1)
            end_month_name = between_match.group(2)
            
            start_month = months_en.get(start_month_name) or months_pt.get(start_month_name)
            end_month = months_en.get(end_month_name) or months_pt.get(end_month_name)
            
            if start_month and end_month:
                filters.start_date = datetime(year, start_month, 1)
                if end_month == 12:
                    filters.end_date = datetime(year, 12, 31, 23, 59, 59)
                else:
                    next_month = datetime(year, end_month + 1, 1)
                    filters.end_date = next_month - timedelta(seconds=1)
        
        # Check for "last N days" pattern
        days_match = re.search(r'last\s+(\d+)\s+days?|últimos\s+(\d+)\s+dias?', query_lower)
        if days_match:
            days = int(days_match.group(1) or days_match.group(2))
            filters.days_back = days
        
        # Document type filter
        if "nfe" in query_lower and "nfce" not in query_lower:
            filters.document_type = "NFe"
        elif "nfce" in query_lower:
            filters.document_type = "NFCe"
        elif "cte" in query_lower:
            filters.document_type = "CTe"
        elif "mdfe" in query_lower or "mdf-e" in query_lower:
            filters.document_type = "MDFe"
        
        # Operation type filter
        if any(word in query_lower for word in ["purchase", "compra", "entrada"]):
            filters.operation_type = "purchase"
        elif any(word in query_lower for word in ["sale", "venda", "saída"]):
            filters.operation_type = "sale"
        elif any(word in query_lower for word in ["transfer", "transferência"]):
            filters.operation_type = "transfer"
        elif any(word in query_lower for word in ["return", "devolução"]):
            filters.operation_type = "return"
        
        # Severity filter
        if "severity error" in query_lower or "gravidade error" in query_lower:
            filters.severity = "error"
        elif "severity warning" in query_lower or "gravidade warning" in query_lower:
            filters.severity = "warning"
        elif "severity critical" in query_lower or "gravidade critical" in query_lower:
            filters.severity = "critical"
        
        # Issuer CNPJ filter (simple pattern)
        cnpj_match = re.search(r'\b(\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}|\d{14})\b', query)
        if cnpj_match:
            filters.issuer_cnpj = cnpj_match.group(1).replace(".", "").replace("/", "").replace("-", "")
        
        return report_type, filters
