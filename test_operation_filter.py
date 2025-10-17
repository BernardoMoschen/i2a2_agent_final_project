"""Demo script to test operation type filter."""

import logging
from pathlib import Path

from src.database.db import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate operation type filter."""
    
    db = DatabaseManager(database_url="sqlite:///fiscal_documents.db")
    
    # Get all invoices
    all_invoices = db.search_invoices()
    logger.info(f"\n📊 Total documents in database: {len(all_invoices)}")
    
    # Show breakdown by operation type
    operation_counts = {}
    for inv in all_invoices:
        op_type = inv.operation_type or "Not classified"
        operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
    
    logger.info("\n🏷️ Breakdown by Operation Type:")
    for op_type, count in sorted(operation_counts.items()):
        emoji = {
            "purchase": "📥",
            "sale": "📤",
            "transfer": "🔄",
            "return": "↩️",
            "Not classified": "❓"
        }.get(op_type, "📄")
        logger.info(f"  {emoji} {op_type.title()}: {count} document(s)")
    
    # Test filter for each operation type
    logger.info("\n🔍 Testing filters:")
    
    for op_type in ["purchase", "sale", "transfer", "return"]:
        results = db.search_invoices(operation_type=op_type)
        logger.info(f"  Filter '{op_type}': {len(results)} result(s)")
        
        if results:
            for inv in results[:2]:  # Show first 2
                logger.info(f"    - {inv.document_type} {inv.document_number} | {inv.issuer_name[:30]}")
    
    logger.info("\n✅ Filter test completed!")


if __name__ == "__main__":
    main()
