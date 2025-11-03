"""Report generation service for fiscal documents.

Generates CSV/XLSX reports and visualizations based on database queries.
Supports both English and Portuguese queries with internal English processing.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import func
from sqlmodel import Session, select

from src.database.db import (
    ClassificationCacheDB,
    DatabaseManager,
    InvoiceDB,
    InvoiceItemDB,
    ValidationIssueDB,
)

logger = logging.getLogger(__name__)


class ReportType:
    """Available report types."""

    # Validation reports
    DOCUMENTS_WITH_ISSUES = "documents_with_issues"
    DOCUMENTS_WITHOUT_ISSUES = "documents_without_issues"
    ISSUES_BY_TYPE = "issues_by_type"
    ISSUES_BY_ISSUER = "issues_by_issuer"
    ISSUES_BY_SEVERITY = "issues_by_severity"
    
    # Financial reports
    TAXES_BY_PERIOD = "taxes_by_period"
    TOTAL_VALUE_BY_PERIOD = "total_value_by_period"
    TOP_SUPPLIERS_BY_VALUE = "top_suppliers_by_value"
    COSTS_BY_CENTER = "costs_by_center"
    
    # Operational reports
    DOCUMENTS_BY_OPERATION_TYPE = "documents_by_operation_type"
    DOCUMENTS_BY_DOCUMENT_TYPE = "documents_by_document_type"
    VOLUME_BY_PERIOD = "volume_by_period"
    PROCESSING_METRICS = "processing_metrics"
    
    # Classification reports
    CACHE_EFFECTIVENESS = "cache_effectiveness"
    UNCLASSIFIED_DOCUMENTS = "unclassified_documents"
    CLASSIFICATION_BY_COST_CENTER = "classification_by_cost_center"
    LLM_FALLBACK_USAGE = "llm_fallback_usage"
    
    # Items/Products reports
    TOP_PRODUCTS_BY_NCM = "top_products_by_ncm"
    ANALYSIS_BY_CFOP = "analysis_by_cfop"
    ITEMS_WITH_ISSUES = "items_with_issues"


class ReportFilters:
    """Filters for report generation."""

    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        issuer_cnpj: Optional[str] = None,
        severity: Optional[str] = None,
        cost_center: Optional[str] = None,
        has_issues: Optional[bool] = None,
        days_back: Optional[int] = None,
    ):
        """Initialize report filters."""
        self.start_date = start_date
        self.end_date = end_date
        self.document_type = document_type
        self.operation_type = operation_type
        self.issuer_cnpj = issuer_cnpj
        self.severity = severity
        self.cost_center = cost_center
        self.has_issues = has_issues
        
        # Handle days_back
        if days_back:
            self.end_date = datetime.now()
            self.start_date = self.end_date - timedelta(days=days_back)


class ReportGenerator:
    """Generate reports and visualizations from fiscal documents database."""

    def __init__(self, database_manager: DatabaseManager):
        """Initialize report generator.
        
        Args:
            database_manager: Database manager instance
        """
        self.db = database_manager
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)

    def get_report_data(
        self,
        report_type: str,
        filters: Optional[ReportFilters] = None,
    ) -> Optional[pd.DataFrame]:
        """Get report data as DataFrame without saving to file.
        
        Useful for generating in-memory charts without disk I/O.
        
        Args:
            report_type: Type of report to generate
            filters: Optional filters for report data
            
        Returns:
            DataFrame with report data or None if error
        """
        try:
            report_methods = {
                ReportType.DOCUMENTS_WITH_ISSUES: self._report_documents_with_issues,
                ReportType.DOCUMENTS_WITHOUT_ISSUES: self._report_documents_without_issues,
                ReportType.ISSUES_BY_TYPE: self._report_issues_by_type,
                ReportType.ISSUES_BY_ISSUER: self._report_issues_by_issuer,
                ReportType.ISSUES_BY_SEVERITY: self._report_issues_by_severity,
                ReportType.TAXES_BY_PERIOD: self._report_taxes_by_period,
                ReportType.TOTAL_VALUE_BY_PERIOD: self._report_total_value_by_period,
                ReportType.TOP_SUPPLIERS_BY_VALUE: self._report_top_suppliers,
                ReportType.COSTS_BY_CENTER: self._report_costs_by_center,
                ReportType.DOCUMENTS_BY_OPERATION_TYPE: self._report_by_operation_type,
                ReportType.DOCUMENTS_BY_DOCUMENT_TYPE: self._report_by_document_type,
                ReportType.VOLUME_BY_PERIOD: self._report_volume_by_period,
                ReportType.CACHE_EFFECTIVENESS: self._report_cache_effectiveness,
                ReportType.UNCLASSIFIED_DOCUMENTS: self._report_unclassified,
                ReportType.CLASSIFICATION_BY_COST_CENTER: self._report_by_cost_center,
                ReportType.LLM_FALLBACK_USAGE: self._report_llm_fallback,
                ReportType.TOP_PRODUCTS_BY_NCM: self._report_top_products,
                ReportType.ANALYSIS_BY_CFOP: self._report_by_cfop,
                ReportType.ITEMS_WITH_ISSUES: self._report_items_with_issues,
            }
            
            if report_type not in report_methods:
                logger.error(f"Unknown report type: {report_type}")
                return None
            
            if filters is None:
                filters = ReportFilters()
            
            df, _ = report_methods[report_type](filters)
            return df
            
        except Exception as e:
            logger.error(f"Error getting report data: {e}", exc_info=True)
            return None

    def generate_report(
        self,
        report_type: str,
        filters: Optional[ReportFilters] = None,
        output_format: str = "xlsx",
        include_chart: bool = True,
    ) -> Dict[str, Any]:
        """Generate a report based on type and filters.
        
        Args:
            report_type: Type of report to generate (from ReportType)
            filters: Optional filters to apply
            output_format: Output format ('csv' or 'xlsx')
            include_chart: Whether to generate chart visualization
            
        Returns:
            Dictionary with report metadata and file paths
        """
        if filters is None:
            filters = ReportFilters()
        
        # Route to appropriate report generator
        report_methods = {
            ReportType.DOCUMENTS_WITH_ISSUES: self._report_documents_with_issues,
            ReportType.DOCUMENTS_WITHOUT_ISSUES: self._report_documents_without_issues,
            ReportType.ISSUES_BY_TYPE: self._report_issues_by_type,
            ReportType.ISSUES_BY_ISSUER: self._report_issues_by_issuer,
            ReportType.ISSUES_BY_SEVERITY: self._report_issues_by_severity,
            ReportType.TAXES_BY_PERIOD: self._report_taxes_by_period,
            ReportType.TOTAL_VALUE_BY_PERIOD: self._report_total_value_by_period,
            ReportType.TOP_SUPPLIERS_BY_VALUE: self._report_top_suppliers,
            ReportType.COSTS_BY_CENTER: self._report_costs_by_center,
            ReportType.DOCUMENTS_BY_OPERATION_TYPE: self._report_by_operation_type,
            ReportType.DOCUMENTS_BY_DOCUMENT_TYPE: self._report_by_document_type,
            ReportType.VOLUME_BY_PERIOD: self._report_volume_by_period,
            ReportType.CACHE_EFFECTIVENESS: self._report_cache_effectiveness,
            ReportType.UNCLASSIFIED_DOCUMENTS: self._report_unclassified,
            ReportType.CLASSIFICATION_BY_COST_CENTER: self._report_by_cost_center,
            ReportType.LLM_FALLBACK_USAGE: self._report_llm_fallback,
            ReportType.TOP_PRODUCTS_BY_NCM: self._report_top_products,
            ReportType.ANALYSIS_BY_CFOP: self._report_by_cfop,
            ReportType.ITEMS_WITH_ISSUES: self._report_items_with_issues,
        }
        
        if report_type not in report_methods:
            raise ValueError(f"Unknown report type: {report_type}")
        
        logger.info(f"Generating report: {report_type}")
        df, metadata = report_methods[report_type](filters)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}"
        
        if output_format == "csv":
            file_path = self.output_dir / f"{filename}.csv"
            df.to_csv(file_path, index=False)
        else:  # xlsx
            file_path = self.output_dir / f"{filename}.xlsx"
            df.to_excel(file_path, index=False, engine="openpyxl")
        
        # Generate chart if requested
        chart_path = None
        if include_chart and len(df) > 0:
            chart_path = self._generate_chart(df, report_type, filename)
        
        return {
            "report_type": report_type,
            "file_path": str(file_path),
            "chart_path": str(chart_path) if chart_path else None,
            "row_count": len(df),
            "generated_at": datetime.now().isoformat(),
            "filters": self._format_filters(filters),
            **metadata,
        }

    def _apply_invoice_filters(self, statement, filters: ReportFilters):
        """Apply common invoice filters to a SQLModel statement."""
        if filters.start_date:
            statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
        if filters.end_date:
            statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
        if filters.document_type:
            statement = statement.where(InvoiceDB.document_type == filters.document_type)
        if filters.operation_type:
            statement = statement.where(InvoiceDB.operation_type == filters.operation_type)
        if filters.issuer_cnpj:
            statement = statement.where(InvoiceDB.issuer_cnpj.contains(filters.issuer_cnpj))
        if filters.cost_center:
            statement = statement.where(InvoiceDB.cost_center == filters.cost_center)
        
        return statement

    # ========== VALIDATION REPORTS ==========

    def _report_documents_with_issues(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents with validation issues."""
        with Session(self.db.engine) as session:
            # Get invoices with issues
            statement = (
                select(InvoiceDB, func.count(ValidationIssueDB.id).label("issue_count"))
                .join(ValidationIssueDB)
                .group_by(InvoiceDB.id)
            )
            statement = self._apply_invoice_filters(statement, filters)
            
            if filters.severity:
                statement = statement.where(ValidationIssueDB.severity == filters.severity)
            
            statement = statement.order_by(func.count(ValidationIssueDB.id).desc())
            results = session.exec(statement).all()
            
            data = []
            for invoice, issue_count in results:
                data.append({
                    "Document Type": invoice.document_type,
                    "Document Number": invoice.document_number,
                    "Series": invoice.series,
                    "Issuer": invoice.issuer_name,
                    "Issuer CNPJ": invoice.issuer_cnpj,
                    "Issue Date": invoice.issue_date.strftime("%Y-%m-%d"),
                    "Total Value": float(invoice.total_invoice),
                    "Issue Count": issue_count,
                    "Operation Type": invoice.operation_type or "N/A",
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_documents": len(df),
                "total_value": df["Total Value"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    def _report_documents_without_issues(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents without validation issues."""
        with Session(self.db.engine) as session:
            # Subquery to get invoice IDs with issues
            subquery = select(ValidationIssueDB.invoice_id).distinct()
            
            # Get invoices NOT IN subquery
            statement = select(InvoiceDB).where(InvoiceDB.id.not_in(subquery))
            statement = self._apply_invoice_filters(statement, filters)
            statement = statement.order_by(InvoiceDB.issue_date.desc())
            
            invoices = session.exec(statement).all()
            
            data = []
            for invoice in invoices:
                data.append({
                    "Document Type": invoice.document_type,
                    "Document Number": invoice.document_number,
                    "Series": invoice.series,
                    "Issuer": invoice.issuer_name,
                    "Issuer CNPJ": invoice.issuer_cnpj,
                    "Issue Date": invoice.issue_date.strftime("%Y-%m-%d"),
                    "Total Value": float(invoice.total_invoice),
                    "Operation Type": invoice.operation_type or "N/A",
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_documents": len(df),
                "total_value": df["Total Value"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    def _report_issues_by_type(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of validation issues grouped by type/code."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    ValidationIssueDB.code,
                    ValidationIssueDB.severity,
                    func.count(ValidationIssueDB.id).label("count"),
                )
                .join(InvoiceDB)
                .group_by(ValidationIssueDB.code, ValidationIssueDB.severity)
                .order_by(func.count(ValidationIssueDB.id).desc())
            )
            
            # Apply date filters through invoice
            if filters.start_date:
                statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
            if filters.end_date:
                statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
            if filters.severity:
                statement = statement.where(ValidationIssueDB.severity == filters.severity)
            
            results = session.exec(statement).all()
            
            data = []
            for code, severity, count in results:
                data.append({
                    "Issue Code": code,
                    "Severity": severity,
                    "Occurrences": count,
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_issue_types": len(df),
                "total_occurrences": df["Occurrences"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    def _report_issues_by_issuer(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of validation issues grouped by issuer."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceDB.issuer_name,
                    InvoiceDB.issuer_cnpj,
                    func.count(ValidationIssueDB.id).label("issue_count"),
                    func.count(func.distinct(InvoiceDB.id)).label("doc_count"),
                )
                .join(ValidationIssueDB)
                .group_by(InvoiceDB.issuer_name, InvoiceDB.issuer_cnpj)
                .order_by(func.count(ValidationIssueDB.id).desc())
            )
            
            statement = self._apply_invoice_filters(statement, filters)
            results = session.exec(statement).all()
            
            data = []
            for issuer_name, issuer_cnpj, issue_count, doc_count in results:
                data.append({
                    "Issuer": issuer_name,
                    "CNPJ": issuer_cnpj,
                    "Documents with Issues": doc_count,
                    "Total Issues": issue_count,
                    "Avg Issues per Doc": round(issue_count / doc_count, 2),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_issuers": len(df),
            }
            
            return df, metadata

    def _report_issues_by_severity(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of validation issues grouped by severity."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    ValidationIssueDB.severity,
                    func.count(ValidationIssueDB.id).label("count"),
                )
                .join(InvoiceDB)
                .group_by(ValidationIssueDB.severity)
                .order_by(func.count(ValidationIssueDB.id).desc())
            )
            
            if filters.start_date:
                statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
            if filters.end_date:
                statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
            
            results = session.exec(statement).all()
            
            data = []
            for severity, count in results:
                data.append({
                    "Severity": severity,
                    "Count": count,
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_issues": df["Count"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    # ========== FINANCIAL REPORTS ==========

    def _report_taxes_by_period(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of taxes breakdown by period."""
        with Session(self.db.engine) as session:
            statement = select(InvoiceDB)
            statement = self._apply_invoice_filters(statement, filters)
            invoices = session.exec(statement).all()
            
            data = []
            for invoice in invoices:
                data.append({
                    "Document": f"{invoice.document_type} {invoice.document_number}",
                    "Issue Date": invoice.issue_date.strftime("%Y-%m-%d"),
                    "Issuer": invoice.issuer_name,
                    "Total Products": float(invoice.total_products),
                    "ICMS": float(invoice.tax_icms),
                    "IPI": float(invoice.tax_ipi),
                    "PIS": float(invoice.tax_pis),
                    "COFINS": float(invoice.tax_cofins),
                    "ISS": float(invoice.tax_issqn),
                    "Total Taxes": float(invoice.total_taxes),
                    "Total Invoice": float(invoice.total_invoice),
                })
            
            df = pd.DataFrame(data)
            
            metadata = {}
            if len(df) > 0:
                metadata = {
                    "total_icms": df["ICMS"].sum(),
                    "total_ipi": df["IPI"].sum(),
                    "total_pis": df["PIS"].sum(),
                    "total_cofins": df["COFINS"].sum(),
                    "total_iss": df["ISS"].sum(),
                    "total_taxes": df["Total Taxes"].sum(),
                    "total_invoice_value": df["Total Invoice"].sum(),
                }
            
            return df, metadata

    def _report_total_value_by_period(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of total value processed by period (daily/monthly)."""
        with Session(self.db.engine) as session:
            statement = select(InvoiceDB)
            statement = self._apply_invoice_filters(statement, filters)
            invoices = session.exec(statement).all()
            
            # Group by month
            monthly_data = {}
            for invoice in invoices:
                month_key = invoice.issue_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "count": 0,
                        "total_products": Decimal("0"),
                        "total_taxes": Decimal("0"),
                        "total_invoice": Decimal("0"),
                    }
                
                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["total_products"] += invoice.total_products
                monthly_data[month_key]["total_taxes"] += invoice.total_taxes
                monthly_data[month_key]["total_invoice"] += invoice.total_invoice
            
            data = []
            for month, values in sorted(monthly_data.items()):
                data.append({
                    "Period": month,
                    "Document Count": values["count"],
                    "Total Products": float(values["total_products"]),
                    "Total Taxes": float(values["total_taxes"]),
                    "Total Invoice": float(values["total_invoice"]),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "periods": len(df),
            }
            
            return df, metadata

    def _report_top_suppliers(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of top suppliers by total value."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceDB.issuer_name,
                    InvoiceDB.issuer_cnpj,
                    func.count(InvoiceDB.id).label("doc_count"),
                    func.sum(InvoiceDB.total_invoice).label("total_value"),
                )
                .group_by(InvoiceDB.issuer_name, InvoiceDB.issuer_cnpj)
                .order_by(func.sum(InvoiceDB.total_invoice).desc())
                .limit(50)
            )
            
            statement = self._apply_invoice_filters(statement, filters)
            results = session.exec(statement).all()
            
            data = []
            for issuer_name, issuer_cnpj, doc_count, total_value in results:
                data.append({
                    "Supplier": issuer_name,
                    "CNPJ": issuer_cnpj,
                    "Document Count": doc_count,
                    "Total Value": float(total_value or 0),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "suppliers_count": len(df),
            }
            
            return df, metadata

    def _report_costs_by_center(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of costs grouped by cost center."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceDB.cost_center,
                    func.count(InvoiceDB.id).label("doc_count"),
                    func.sum(InvoiceDB.total_invoice).label("total_value"),
                )
                .where(InvoiceDB.cost_center.is_not(None))
                .group_by(InvoiceDB.cost_center)
                .order_by(func.sum(InvoiceDB.total_invoice).desc())
            )
            
            statement = self._apply_invoice_filters(statement, filters)
            results = session.exec(statement).all()
            
            data = []
            total = Decimal("0")
            for cost_center, doc_count, total_value in results:
                value = total_value or Decimal("0")
                total += value
                data.append({
                    "Cost Center": cost_center,
                    "Document Count": doc_count,
                    "Total Value": float(value),
                })
            
            # Add percentage
            for row in data:
                if total > 0:
                    row["Percentage"] = round((row["Total Value"] / float(total)) * 100, 2)
                else:
                    row["Percentage"] = 0
            
            df = pd.DataFrame(data)
            metadata = {
                "cost_centers_count": len(df),
                "total_value": float(total),
            }
            
            return df, metadata

    # ========== OPERATIONAL REPORTS ==========

    def _report_by_operation_type(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents grouped by operation type."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceDB.operation_type,
                    func.count(InvoiceDB.id).label("count"),
                    func.sum(InvoiceDB.total_invoice).label("total_value"),
                )
                .group_by(InvoiceDB.operation_type)
                .order_by(func.count(InvoiceDB.id).desc())
            )
            
            statement = self._apply_invoice_filters(statement, filters)
            results = session.exec(statement).all()
            
            data = []
            for op_type, count, total_value in results:
                data.append({
                    "Operation Type": op_type or "Not Classified",
                    "Document Count": count,
                    "Total Value": float(total_value or 0),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_documents": df["Document Count"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    def _report_by_document_type(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents grouped by document type."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceDB.document_type,
                    func.count(InvoiceDB.id).label("count"),
                    func.sum(InvoiceDB.total_invoice).label("total_value"),
                )
                .group_by(InvoiceDB.document_type)
                .order_by(func.count(InvoiceDB.id).desc())
            )
            
            statement = self._apply_invoice_filters(statement, filters)
            results = session.exec(statement).all()
            
            data = []
            for doc_type, count, total_value in results:
                data.append({
                    "Document Type": doc_type,
                    "Count": count,
                    "Total Value": float(total_value or 0),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_documents": df["Count"].sum() if len(df) > 0 else 0,
            }
            
            return df, metadata

    def _report_volume_by_period(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of document volume by time period."""
        with Session(self.db.engine) as session:
            statement = select(InvoiceDB)
            statement = self._apply_invoice_filters(statement, filters)
            invoices = session.exec(statement).all()
            
            # Group by month
            monthly_data = {}
            for invoice in invoices:
                month_key = invoice.issue_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = 0
                monthly_data[month_key] += 1
            
            data = []
            for month, count in sorted(monthly_data.items()):
                data.append({
                    "Period": month,
                    "Document Count": count,
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "total_periods": len(df),
            }
            
            return df, metadata

    # ========== CLASSIFICATION REPORTS ==========

    def _report_cache_effectiveness(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of classification cache effectiveness."""
        with Session(self.db.engine) as session:
            statement = select(ClassificationCacheDB).order_by(
                ClassificationCacheDB.hit_count.desc()
            )
            
            cache_entries = session.exec(statement).all()
            
            data = []
            total_hits = 0
            for entry in cache_entries:
                total_hits += entry.hit_count
                data.append({
                    "Issuer CNPJ": entry.issuer_cnpj,
                    "NCM": entry.ncm or "N/A",
                    "CFOP": entry.cfop,
                    "Operation Type": entry.operation_type,
                    "Cost Center": entry.cost_center,
                    "Hit Count": entry.hit_count,
                    "Last Used": entry.last_used_at.strftime("%Y-%m-%d %H:%M"),
                    "Created": entry.created_at.strftime("%Y-%m-%d"),
                })
            
            df = pd.DataFrame(data)
            
            # Calculate effectiveness
            total_entries = len(df)
            avg_hits = total_hits / total_entries if total_entries > 0 else 0
            
            metadata = {
                "total_cache_entries": total_entries,
                "total_cache_hits": total_hits,
                "avg_hits_per_entry": round(avg_hits, 2),
                "estimated_llm_calls_saved": total_hits,
            }
            
            return df, metadata

    def _report_unclassified(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents without classification."""
        with Session(self.db.engine) as session:
            statement = select(InvoiceDB).where(InvoiceDB.operation_type.is_(None))
            statement = self._apply_invoice_filters(statement, filters)
            
            invoices = session.exec(statement).all()
            
            data = []
            for invoice in invoices:
                data.append({
                    "Document Type": invoice.document_type,
                    "Document Number": invoice.document_number,
                    "Issuer": invoice.issuer_name,
                    "CNPJ": invoice.issuer_cnpj,
                    "Issue Date": invoice.issue_date.strftime("%Y-%m-%d"),
                    "Total Value": float(invoice.total_invoice),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "unclassified_count": len(df),
            }
            
            return df, metadata

    def _report_by_cost_center(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of classifications grouped by cost center."""
        # Reuse costs_by_center logic
        return self._report_costs_by_center(filters)

    def _report_llm_fallback(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of documents that used LLM fallback."""
        with Session(self.db.engine) as session:
            statement = select(InvoiceDB).where(InvoiceDB.used_llm_fallback == True)
            statement = self._apply_invoice_filters(statement, filters)
            
            invoices = session.exec(statement).all()
            
            data = []
            for invoice in invoices:
                data.append({
                    "Document Type": invoice.document_type,
                    "Document Number": invoice.document_number,
                    "Issuer": invoice.issuer_name,
                    "Operation Type": invoice.operation_type or "N/A",
                    "Cost Center": invoice.cost_center or "N/A",
                    "Confidence": invoice.classification_confidence or 0,
                    "Issue Date": invoice.issue_date.strftime("%Y-%m-%d"),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "llm_fallback_count": len(df),
            }
            
            return df, metadata

    # ========== ITEMS/PRODUCTS REPORTS ==========

    def _report_top_products(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of top products by NCM."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceItemDB.ncm,
                    InvoiceItemDB.description,
                    func.sum(InvoiceItemDB.quantity).label("total_qty"),
                    func.sum(InvoiceItemDB.total_price).label("total_value"),
                    func.count(InvoiceItemDB.id).label("item_count"),
                )
                .join(InvoiceDB)
                .where(InvoiceItemDB.ncm.is_not(None))
                .group_by(InvoiceItemDB.ncm, InvoiceItemDB.description)
                .order_by(func.sum(InvoiceItemDB.total_price).desc())
                .limit(100)
            )
            
            # Apply invoice filters
            if filters.start_date:
                statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
            if filters.end_date:
                statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
            if filters.operation_type:
                statement = statement.where(InvoiceDB.operation_type == filters.operation_type)
            
            results = session.exec(statement).all()
            
            data = []
            for ncm, description, total_qty, total_value, item_count in results:
                data.append({
                    "NCM": ncm,
                    "Description": description[:100],  # Limit length
                    "Total Quantity": float(total_qty or 0),
                    "Total Value": float(total_value or 0),
                    "Item Count": item_count,
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "unique_ncm_count": len(df),
            }
            
            return df, metadata

    def _report_by_cfop(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of items grouped by CFOP."""
        with Session(self.db.engine) as session:
            statement = (
                select(
                    InvoiceItemDB.cfop,
                    func.count(InvoiceItemDB.id).label("item_count"),
                    func.sum(InvoiceItemDB.total_price).label("total_value"),
                )
                .join(InvoiceDB)
                .group_by(InvoiceItemDB.cfop)
                .order_by(func.count(InvoiceItemDB.id).desc())
            )
            
            # Apply invoice filters
            if filters.start_date:
                statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
            if filters.end_date:
                statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
            
            results = session.exec(statement).all()
            
            data = []
            for cfop, item_count, total_value in results:
                data.append({
                    "CFOP": cfop,
                    "Item Count": item_count,
                    "Total Value": float(total_value or 0),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "unique_cfop_count": len(df),
            }
            
            return df, metadata

    def _report_items_with_issues(
        self, filters: ReportFilters
    ) -> Tuple[pd.DataFrame, Dict]:
        """Report of items from documents with validation issues."""
        with Session(self.db.engine) as session:
            # Get invoices with issues
            invoices_with_issues = (
                select(InvoiceDB.id)
                .join(ValidationIssueDB)
                .distinct()
            )
            
            statement = (
                select(InvoiceItemDB, InvoiceDB)
                .join(InvoiceDB)
                .where(InvoiceDB.id.in_(invoices_with_issues))
            )
            
            # Apply filters
            if filters.start_date:
                statement = statement.where(InvoiceDB.issue_date >= filters.start_date)
            if filters.end_date:
                statement = statement.where(InvoiceDB.issue_date <= filters.end_date)
            
            results = session.exec(statement).all()
            
            data = []
            for item, invoice in results:
                data.append({
                    "Document": f"{invoice.document_type} {invoice.document_number}",
                    "Item Number": item.item_number,
                    "Product Code": item.product_code,
                    "Description": item.description[:100],
                    "NCM": item.ncm or "N/A",
                    "CFOP": item.cfop,
                    "Quantity": float(item.quantity),
                    "Total Price": float(item.total_price),
                })
            
            df = pd.DataFrame(data)
            metadata = {
                "items_count": len(df),
            }
            
            return df, metadata

    # ========== VISUALIZATION ==========

    def _generate_chart(
        self, df: pd.DataFrame, report_type: str, filename: str
    ) -> Optional[Path]:
        """Generate a chart visualization for the report.
        
        Args:
            df: DataFrame with report data
            report_type: Type of report
            filename: Base filename for chart
            
        Returns:
            Path to saved chart file or None
        """
        try:
            import matplotlib.pyplot as plt
            
            chart_path = self.output_dir / f"{filename}.png"
            
            plt.figure(figsize=(12, 6))
            
            # Different chart types based on report
            if report_type in [ReportType.ISSUES_BY_TYPE, ReportType.ISSUES_BY_SEVERITY]:
                if "Issue Code" in df.columns:
                    df.head(10).plot(x="Issue Code", y="Occurrences", kind="bar")
                elif "Severity" in df.columns:
                    df.plot(x="Severity", y="Count", kind="bar")
                plt.xticks(rotation=45, ha="right")
                
            elif report_type in [ReportType.DOCUMENTS_BY_OPERATION_TYPE, ReportType.DOCUMENTS_BY_DOCUMENT_TYPE]:
                if "Operation Type" in df.columns:
                    df.plot(x="Operation Type", y="Document Count", kind="bar")
                elif "Document Type" in df.columns:
                    df.plot(x="Document Type", y="Count", kind="bar")
                plt.xticks(rotation=45, ha="right")
                
            elif report_type == ReportType.VOLUME_BY_PERIOD:
                df.plot(x="Period", y="Document Count", kind="line", marker="o")
                plt.xticks(rotation=45, ha="right")
                
            elif report_type == ReportType.TOTAL_VALUE_BY_PERIOD:
                df.plot(x="Period", y="Total Invoice", kind="line", marker="o")
                plt.xticks(rotation=45, ha="right")
                
            elif report_type == ReportType.TOP_SUPPLIERS_BY_VALUE:
                df.head(10).plot(x="Supplier", y="Total Value", kind="barh")
                
            else:
                # Default: first numeric column
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) > 0:
                    df.head(10).plot(y=numeric_cols[0], kind="bar")
            
            plt.title(report_type.replace("_", " ").title())
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches="tight")
            plt.close()
            
            return chart_path
            
        except Exception as e:
            logger.warning(f"Failed to generate chart: {e}")
            return None

    def _generate_plotly_chart(
        self, df: pd.DataFrame, report_type: str
    ) -> Optional[Dict[str, Any]]:
        """Generate a Plotly chart (JSON) for Cloud-compatible rendering.
        
        Cloud-compatible alternative to PNG file-based charts.
        Returns Plotly figure dict that can be rendered with st.plotly_chart().
        
        Args:
            df: DataFrame with report data
            report_type: Type of report
            
        Returns:
            Plotly figure dict or None
        """
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            if df.empty:
                return None
            
            # Different chart types based on report
            if report_type in [ReportType.ISSUES_BY_TYPE, ReportType.ISSUES_BY_SEVERITY]:
                if "Issue Code" in df.columns:
                    fig = px.bar(
                        df.head(10),
                        x="Issue Code",
                        y="Occurrences",
                        title=report_type.replace("_", " ").title(),
                        labels={"Issue Code": "Issue Code", "Occurrences": "Count"}
                    )
                elif "Severity" in df.columns:
                    fig = px.bar(
                        df,
                        x="Severity",
                        y="Count",
                        title=report_type.replace("_", " ").title()
                    )
                else:
                    return None
                    
            elif report_type in [ReportType.DOCUMENTS_BY_OPERATION_TYPE, ReportType.DOCUMENTS_BY_DOCUMENT_TYPE]:
                if "Operation Type" in df.columns:
                    fig = px.bar(
                        df,
                        x="Operation Type",
                        y="Document Count",
                        title=report_type.replace("_", " ").title()
                    )
                elif "Document Type" in df.columns:
                    fig = px.bar(
                        df,
                        x="Document Type",
                        y="Count",
                        title=report_type.replace("_", " ").title()
                    )
                else:
                    return None
                    
            elif report_type == ReportType.VOLUME_BY_PERIOD:
                fig = px.line(
                    df,
                    x="Period",
                    y="Document Count",
                    title=report_type.replace("_", " ").title(),
                    markers=True
                )
                
            elif report_type == ReportType.TOTAL_VALUE_BY_PERIOD:
                fig = px.line(
                    df,
                    x="Period",
                    y="Total Invoice",
                    title=report_type.replace("_", " ").title(),
                    markers=True
                )
                
            elif report_type == ReportType.TOP_SUPPLIERS_BY_VALUE:
                fig = px.bar(
                    df.head(10),
                    x="Total Value",
                    y="Supplier",
                    orientation="h",
                    title=report_type.replace("_", " ").title()
                )
                
            else:
                # Default: first numeric column
                numeric_cols = df.select_dtypes(include=["number"]).columns
                if len(numeric_cols) > 0:
                    fig = px.bar(
                        df.head(10),
                        y=numeric_cols[0],
                        title=report_type.replace("_", " ").title()
                    )
                else:
                    return None
            
            # Update layout for better appearance
            fig.update_layout(
                height=500,
                margin=dict(l=50, r=50, t=50, b=50),
                hovermode="x unified",
                template="plotly_white"
            )
            
            # Convert to JSON-serializable dict
            import json
            import plotly.io as pio
            
            # Use plotly's JSON serialization to handle numpy types
            fig_json = pio.to_json(fig)
            chart_dict = json.loads(fig_json)
            
            return chart_dict
            
        except Exception as e:
            logger.warning(f"Failed to generate Plotly chart: {e}")
            return None

    def _format_filters(self, filters: ReportFilters) -> Dict[str, Any]:
        """Format filters for metadata output."""
        return {
            "start_date": filters.start_date.isoformat() if filters.start_date else None,
            "end_date": filters.end_date.isoformat() if filters.end_date else None,
            "document_type": filters.document_type,
            "operation_type": filters.operation_type,
            "issuer_cnpj": filters.issuer_cnpj,
            "severity": filters.severity,
            "cost_center": filters.cost_center,
            "has_issues": filters.has_issues,
        }
