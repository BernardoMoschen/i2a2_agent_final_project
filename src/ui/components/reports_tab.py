"""Reports tab UI component for Streamlit."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from src.database.db import DatabaseManager
from src.services.report_generator import ReportFilters, ReportGenerator, ReportType

logger = logging.getLogger(__name__)


def render_reports_tab(db: DatabaseManager):
    """Render the Reports tab with report generation interface.
    
    Args:
        db: Database manager instance
    """
    st.header("📊 Reports & Analytics")
    st.markdown(
        "Generate Excel/CSV reports and visualizations from your fiscal documents database."
    )
    
    # Initialize report generator
    generator = ReportGenerator(db)
    
    # Report selection
    st.subheader("📋 Report Type")
    
    report_categories = {
        "Validation Reports": {
            ReportType.DOCUMENTS_WITH_ISSUES: "Documents with Validation Issues",
            ReportType.DOCUMENTS_WITHOUT_ISSUES: "Documents without Issues (Approved)",
            ReportType.ISSUES_BY_TYPE: "Issues Grouped by Type",
            ReportType.ISSUES_BY_ISSUER: "Issues Grouped by Issuer/Supplier",
            ReportType.ISSUES_BY_SEVERITY: "Issues Grouped by Severity",
        },
        "Financial Reports": {
            ReportType.TAXES_BY_PERIOD: "Tax Breakdown by Period",
            ReportType.TOTAL_VALUE_BY_PERIOD: "Total Value by Period",
            ReportType.TOP_SUPPLIERS_BY_VALUE: "Top Suppliers by Value",
            ReportType.COSTS_BY_CENTER: "Costs by Cost Center",
        },
        "Operational Reports": {
            ReportType.DOCUMENTS_BY_OPERATION_TYPE: "Documents by Operation Type",
            ReportType.DOCUMENTS_BY_DOCUMENT_TYPE: "Documents by Document Type",
            ReportType.VOLUME_BY_PERIOD: "Document Volume by Period",
        },
        "Classification Reports": {
            ReportType.CACHE_EFFECTIVENESS: "Cache Effectiveness",
            ReportType.UNCLASSIFIED_DOCUMENTS: "Unclassified Documents",
            ReportType.CLASSIFICATION_BY_COST_CENTER: "Classification by Cost Center",
            ReportType.LLM_FALLBACK_USAGE: "LLM Fallback Usage",
        },
        "Products/Items Reports": {
            ReportType.TOP_PRODUCTS_BY_NCM: "Top Products by NCM",
            ReportType.ANALYSIS_BY_CFOP: "Analysis by CFOP",
            ReportType.ITEMS_WITH_ISSUES: "Items with Validation Issues",
        },
    }
    
    # Category selection
    category = st.selectbox(
        "Report Category",
        options=list(report_categories.keys()),
        key="report_category"
    )
    
    # Report type selection within category
    report_options = report_categories[category]
    report_display = st.selectbox(
        "Report Type",
        options=list(report_options.values()),
        key="report_type_display"
    )
    
    # Get actual report type key
    report_type = [k for k, v in report_options.items() if v == report_display][0]
    
    # Filters section
    st.subheader("🔍 Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Date filter
        date_filter_type = st.selectbox(
            "Date Range",
            options=["All Time", "Last 7 days", "Last 30 days", "Last 90 days", "Last Year", "Custom"],
            key="report_date_filter"
        )
        
        start_date = None
        end_date = None
        days_back = None
        
        if date_filter_type == "Last 7 days":
            days_back = 7
        elif date_filter_type == "Last 30 days":
            days_back = 30
        elif date_filter_type == "Last 90 days":
            days_back = 90
        elif date_filter_type == "Last Year":
            days_back = 365
        elif date_filter_type == "Custom":
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date", key="report_start_date")
            with col_end:
                end_date = st.date_input("End Date", key="report_end_date")
            
            if start_date:
                start_date = datetime.combine(start_date, datetime.min.time())
            if end_date:
                end_date = datetime.combine(end_date, datetime.max.time())
        
        # Document type filter
        doc_type = st.selectbox(
            "Document Type",
            options=["All", "NFe", "NFCe", "CTe", "MDFe"],
            key="report_doc_type"
        )
        document_type = None if doc_type == "All" else doc_type
        
    with col2:
        # Operation type filter
        op_type = st.selectbox(
            "Operation Type",
            options=["All", "Purchase", "Sale", "Transfer", "Return"],
            key="report_op_type"
        )
        operation_type = None if op_type == "All" else op_type.lower()
        
        # Severity filter (for validation reports)
        if category == "Validation Reports":
            sev_type = st.selectbox(
                "Severity",
                options=["All", "Error", "Warning", "Info"],
                key="report_severity"
            )
            severity = None if sev_type == "All" else sev_type.lower()
        else:
            severity = None
        
        # Issuer CNPJ filter
        issuer_cnpj = st.text_input(
            "Issuer CNPJ (contains)",
            placeholder="Filter by CNPJ...",
            key="report_issuer_cnpj"
        )
        issuer_cnpj = issuer_cnpj.strip() if issuer_cnpj else None
    
    # Output options
    st.subheader("⚙️ Output Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_format = st.radio(
            "File Format",
            options=["xlsx", "csv"],
            index=0,
            horizontal=True,
            key="report_output_format"
        )
    
    with col2:
        include_chart = st.checkbox(
            "Generate Visualization Chart",
            value=True,
            key="report_include_chart"
        )
    
    # Generate button
    st.divider()
    
    if st.button("📊 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                # Create filters
                filters = ReportFilters(
                    start_date=start_date,
                    end_date=end_date,
                    days_back=days_back,
                    document_type=document_type,
                    operation_type=operation_type,
                    severity=severity,
                    issuer_cnpj=issuer_cnpj,
                )
                
                # Generate report
                result = generator.generate_report(
                    report_type=report_type,
                    filters=filters,
                    output_format=output_format,
                    include_chart=include_chart,
                )
                
                # Display success message
                st.success(f"✅ Report generated successfully!")
                
                # Display metadata
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Rows", result["row_count"])
                
                with col2:
                    if "total_documents" in result:
                        st.metric("Documents", result["total_documents"])
                    elif "total_issues" in result:
                        st.metric("Issues", result["total_issues"])
                    elif "total_cache_entries" in result:
                        st.metric("Cache Entries", result["total_cache_entries"])
                
                with col3:
                    if "total_value" in result:
                        st.metric("Total Value", f"R$ {result['total_value']:,.2f}")
                    elif "total_cache_hits" in result:
                        st.metric("Cache Hits", result["total_cache_hits"])
                
                # Display file download
                st.divider()
                st.subheader("📁 Download Files")
                
                file_path = Path(result["file_path"])
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {output_format.upper()} File",
                            data=f.read(),
                            file_name=file_path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if output_format == "xlsx" else "text/csv",
                        )
                
                # Display chart if generated
                if result["chart_path"]:
                    chart_path = Path(result["chart_path"])
                    if chart_path.exists():
                        st.divider()
                        st.subheader("📈 Visualization")
                        st.image(str(chart_path), use_container_width=True)
                
                # Display filters applied
                st.divider()
                st.subheader("🔍 Filters Applied")
                
                filters_applied = []
                for key, value in result["filters"].items():
                    if value is not None:
                        filters_applied.append(f"**{key.replace('_', ' ').title()}:** {value}")
                
                if filters_applied:
                    for filter_str in filters_applied:
                        st.markdown(f"- {filter_str}")
                else:
                    st.info("No filters applied - showing all data")
                
            except Exception as e:
                logger.error(f"Error generating report: {e}", exc_info=True)
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Help section
    st.divider()
    
    with st.expander("💡 Help & Examples"):
        st.markdown("""
        ### 📊 Available Reports
        
        **Validation Reports:**
        - **Documents with Issues**: List of documents that have validation problems
        - **Documents without Issues**: List of approved/clean documents
        - **Issues by Type**: Count of each validation issue type
        - **Issues by Issuer**: Which suppliers have the most issues
        - **Issues by Severity**: Breakdown by error/warning/info
        
        **Financial Reports:**
        - **Taxes by Period**: Detailed tax breakdown (ICMS, IPI, PIS, COFINS, ISS)
        - **Total Value by Period**: Monthly totals of processed documents
        - **Top Suppliers**: Ranking by total invoice value
        - **Costs by Center**: Distribution across cost centers
        
        **Operational Reports:**
        - **By Operation Type**: Count purchase/sale/transfer/return
        - **By Document Type**: Count NFe/NFCe/CTe/MDFe
        - **Volume by Period**: Monthly document processing volume
        
        **Classification Reports:**
        - **Cache Effectiveness**: How well the classification cache is working
        - **Unclassified Documents**: Documents without operation type
        - **LLM Fallback Usage**: When ML model failed and used LLM
        
        **Products Reports:**
        - **Top Products by NCM**: Most purchased products
        - **Analysis by CFOP**: Operations grouped by CFOP code
        - **Items with Issues**: Products from problematic documents
        
        ### 🔍 Using Filters
        
        Combine filters to get exactly what you need:
        - **Date Range**: Focus on specific time periods
        - **Document Type**: Only NFe, NFCe, etc.
        - **Operation Type**: Only purchases, sales, etc.
        - **Severity**: Only errors, warnings, etc.
        - **Issuer CNPJ**: From specific suppliers
        
        ### 📝 Examples
        
        1. **Monthly tax summary for purchases**:
           - Report: "Tax Breakdown by Period"
           - Operation Type: "Purchase"
           - Date Range: "Last 30 days"
        
        2. **Top 10 suppliers this year**:
           - Report: "Top Suppliers by Value"
           - Date Range: "Last Year"
        
        3. **All validation errors**:
           - Report: "Documents with Issues"
           - Severity: "Error"
           - Date Range: "All Time"
        
        4. **Cache performance**:
           - Report: "Cache Effectiveness"
           - (no filters needed)
        """)
