"""Example script demonstrating report generation.

This script shows how to generate various types of reports using the
ReportGenerator service.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from src.database.db import DatabaseManager
from src.services.report_generator import (
    ReportFilters,
    ReportGenerator,
    ReportType,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate report generation functionality."""
    
    # Initialize database and generator
    db = DatabaseManager("sqlite:///fiscal_documents.db")
    generator = ReportGenerator(db)
    
    logger.info("=" * 60)
    logger.info("📊 FISCAL DOCUMENT REPORTS - EXAMPLES")
    logger.info("=" * 60)
    
    # Example 1: Documents with validation issues (last 30 days)
    logger.info("\n📋 Example 1: Documents with Issues (Last 30 Days)")
    logger.info("-" * 60)
    
    filters = ReportFilters(days_back=30, severity="error")
    
    result = generator.generate_report(
        report_type=ReportType.DOCUMENTS_WITH_ISSUES,
        filters=filters,
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'total_documents' in result:
        logger.info(f"   Documents: {result['total_documents']}")
    if 'total_value' in result:
        logger.info(f"   Total Value: R$ {result['total_value']:,.2f}")
    if result['chart_path']:
        logger.info(f"   Chart: {result['chart_path']}")
    
    # Example 2: Top suppliers by value (last quarter)
    logger.info("\n📋 Example 2: Top Suppliers by Value (Last 90 Days)")
    logger.info("-" * 60)
    
    filters = ReportFilters(days_back=90)
    
    result = generator.generate_report(
        report_type=ReportType.TOP_SUPPLIERS_BY_VALUE,
        filters=filters,
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'suppliers_count' in result:
        logger.info(f"   Suppliers: {result['suppliers_count']}")
    
    # Example 3: Tax breakdown for purchases (specific month)
    logger.info("\n📋 Example 3: Tax Breakdown for Purchases (October 2024)")
    logger.info("-" * 60)
    
    filters = ReportFilters(
        start_date=datetime(2024, 10, 1),
        end_date=datetime(2024, 10, 31),
        operation_type="purchase",
    )
    
    result = generator.generate_report(
        report_type=ReportType.TAXES_BY_PERIOD,
        filters=filters,
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'total_icms' in result:
        logger.info(f"   Total ICMS: R$ {result['total_icms']:,.2f}")
    if 'total_ipi' in result:
        logger.info(f"   Total IPI: R$ {result['total_ipi']:,.2f}")
    if 'total_pis' in result:
        logger.info(f"   Total PIS: R$ {result['total_pis']:,.2f}")
    if 'total_cofins' in result:
        logger.info(f"   Total COFINS: R$ {result['total_cofins']:,.2f}")
    
    # Example 4: Cache effectiveness
    logger.info("\n📋 Example 4: Cache Effectiveness")
    logger.info("-" * 60)
    
    result = generator.generate_report(
        report_type=ReportType.CACHE_EFFECTIVENESS,
        filters=ReportFilters(),  # No filters for cache report
        output_format="csv",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'total_cache_entries' in result:
        logger.info(f"   Cache Entries: {result['total_cache_entries']}")
    if 'total_cache_hits' in result:
        logger.info(f"   Cache Hits: {result['total_cache_hits']}")
    if 'estimated_llm_calls_saved' in result:
        logger.info(f"   LLM Calls Saved: {result['estimated_llm_calls_saved']}")
    
    # Example 5: Unclassified documents
    logger.info("\n📋 Example 5: Unclassified Documents")
    logger.info("-" * 60)
    
    filters = ReportFilters(days_back=365)  # Last year
    
    result = generator.generate_report(
        report_type=ReportType.UNCLASSIFIED_DOCUMENTS,
        filters=filters,
        output_format="xlsx",
        include_chart=False,  # No chart needed
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'unclassified_count' in result:
        logger.info(f"   Unclassified: {result['unclassified_count']}")
    
    # Example 6: Top products by NCM (purchases only)
    logger.info("\n📋 Example 6: Top Products by NCM (Purchases)")
    logger.info("-" * 60)
    
    filters = ReportFilters(
        operation_type="purchase",
        days_back=180,  # Last 6 months
    )
    
    result = generator.generate_report(
        report_type=ReportType.TOP_PRODUCTS_BY_NCM,
        filters=filters,
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'unique_ncm_count' in result:
        logger.info(f"   Unique NCMs: {result['unique_ncm_count']}")
    
    # Example 7: Documents by operation type (all time)
    logger.info("\n📋 Example 7: Documents by Operation Type (All Time)")
    logger.info("-" * 60)
    
    result = generator.generate_report(
        report_type=ReportType.DOCUMENTS_BY_OPERATION_TYPE,
        filters=ReportFilters(),  # No filters = all time
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'total_documents' in result:
        logger.info(f"   Total Documents: {result['total_documents']}")
    
    # Example 8: Issues by issuer (specific supplier)
    logger.info("\n📋 Example 8: Issues by Issuer (Specific CNPJ)")
    logger.info("-" * 60)
    
    filters = ReportFilters(
        issuer_cnpj="12345678",  # Partial CNPJ search
        days_back=90,
    )
    
    result = generator.generate_report(
        report_type=ReportType.ISSUES_BY_ISSUER,
        filters=filters,
        output_format="xlsx",
        include_chart=True,
    )
    
    logger.info(f"✅ Report generated: {result['file_path']}")
    logger.info(f"   Rows: {result['row_count']}")
    if 'total_issuers' in result:
        logger.info(f"   Issuers: {result['total_issuers']}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)
    logger.info("All reports generated successfully!")
    logger.info(f"Reports directory: {generator.output_dir}")
    
    # List generated files
    reports = list(generator.output_dir.glob("*"))
    logger.info(f"\n📁 Generated Files ({len(reports)}):")
    for report_file in sorted(reports)[-10:]:  # Show last 10
        logger.info(f"   - {report_file.name}")
    
    logger.info("\n💡 TIP: Open the XLSX files in Excel or LibreOffice to view the data.")
    logger.info("💡 TIP: View PNG charts for quick visualization.")
    logger.info("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
