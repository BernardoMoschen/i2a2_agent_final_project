"""Test database operations."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path

from src.database.db import DatabaseManager
from src.models import InvoiceModel, InvoiceItem, TaxDetails, ValidationIssue, ValidationSeverity


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(f"sqlite:///{db_path}")
    return db


@pytest.fixture
def sample_invoice():
    """Create a sample invoice for testing."""
    return InvoiceModel(
        document_type="NFe",
        document_key="35240112345678000190550010000000011234567890",
        document_number="1",
        series="1",
        issue_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        issuer_name="Empresa Teste LTDA",
        issuer_cnpj="12345678000190",
        recipient_name="Cliente Teste",
        recipient_cnpj_cpf="98765432000100",
        total_products=Decimal("100.00"),
        total_invoice=Decimal("115.00"),
        total_taxes=Decimal("15.00"),
        taxes=TaxDetails(
            icms=Decimal("10.00"),
            ipi=Decimal("5.00"),
        ),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD001",
                description="Produto Teste",
                ncm="12345678",
                cfop="5102",
                unit="UN",
                quantity=Decimal("2.00"),
                unit_price=Decimal("50.00"),
                total_price=Decimal("100.00"),
            )
        ],
        raw_xml="<xml/>",
    )


@pytest.fixture
def sample_issues():
    """Create sample validation issues."""
    return [
        ValidationIssue(
            code="VAL001",
            severity=ValidationSeverity.ERROR,
            message="Test error",
            field="test_field",
            suggestion="Fix it",
        ),
        ValidationIssue(
            code="VAL002",
            severity=ValidationSeverity.WARNING,
            message="Test warning",
        ),
    ]


def test_save_invoice(temp_db, sample_invoice, sample_issues):
    """Test saving an invoice to database."""
    invoice_db = temp_db.save_invoice(sample_invoice, sample_issues)
    
    assert invoice_db.id is not None
    assert invoice_db.document_key == sample_invoice.document_key
    assert invoice_db.issuer_name == sample_invoice.issuer_name
    assert len(invoice_db.items) == 1
    assert len(invoice_db.issues) == 2


def test_get_invoice_by_key(temp_db, sample_invoice, sample_issues):
    """Test retrieving an invoice by document key."""
    temp_db.save_invoice(sample_invoice, sample_issues)
    
    retrieved = temp_db.get_invoice_by_key(sample_invoice.document_key)
    
    assert retrieved is not None
    assert retrieved.document_key == sample_invoice.document_key
    assert retrieved.issuer_name == sample_invoice.issuer_name


def test_duplicate_invoice(temp_db, sample_invoice, sample_issues):
    """Test that duplicate invoices are not saved twice."""
    temp_db.save_invoice(sample_invoice, sample_issues)
    result = temp_db.save_invoice(sample_invoice, sample_issues)
    
    # Should return the existing invoice
    assert result is not None
    
    # Should only have one invoice in database
    all_invoices = temp_db.get_all_invoices()
    assert len(all_invoices) == 1


def test_search_invoices(temp_db, sample_invoice, sample_issues):
    """Test searching invoices with filters."""
    temp_db.save_invoice(sample_invoice, sample_issues)
    
    # Search by document type
    results = temp_db.search_invoices(document_type="NFe")
    assert len(results) == 1
    assert results[0].document_type == "NFe"
    
    # Search by issuer CNPJ
    results = temp_db.search_invoices(issuer_cnpj="12345678000190")
    assert len(results) == 1
    
    # Search by non-existent type
    results = temp_db.search_invoices(document_type="CTe")
    assert len(results) == 0


def test_get_statistics(temp_db, sample_invoice, sample_issues):
    """Test getting database statistics."""
    temp_db.save_invoice(sample_invoice, sample_issues)
    
    stats = temp_db.get_statistics()
    
    assert stats["total_invoices"] == 1
    assert stats["total_items"] == 1
    assert stats["total_issues"] == 2
    assert stats["by_type"]["NFe"] == 1
    assert stats["total_value"] > 0


def test_delete_invoice(temp_db, sample_invoice, sample_issues):
    """Test deleting an invoice."""
    temp_db.save_invoice(sample_invoice, sample_issues)
    
    # Delete invoice
    result = temp_db.delete_invoice(sample_invoice.document_key)
    assert result is True
    
    # Verify it's gone
    retrieved = temp_db.get_invoice_by_key(sample_invoice.document_key)
    assert retrieved is None
    
    # Try to delete again
    result = temp_db.delete_invoice(sample_invoice.document_key)
    assert result is False


def test_bulk_insert_empty(temp_db):
    """Test bulk insert with empty list."""
    result = temp_db.save_invoices_batch([])
    assert result == []


def test_bulk_insert_single(temp_db, sample_invoice, sample_issues):
    """Test bulk insert with single invoice."""
    batch = [(sample_invoice, sample_issues, None)]
    result = temp_db.save_invoices_batch(batch)
    
    assert len(result) == 1
    assert result[0].document_key == sample_invoice.document_key
    assert len(result[0].items) == 1
    assert len(result[0].issues) == 2


def test_bulk_insert_multiple(temp_db, sample_invoice, sample_issues):
    """Test bulk insert with multiple invoices."""
    # Create 3 different invoices
    invoices = []
    for i in range(3):
        inv = InvoiceModel(
            document_type=sample_invoice.document_type,
            document_key=f"{sample_invoice.document_key[:-2]}{i:02d}",  # Different keys
            document_number=str(i+1),
            series=sample_invoice.series,
            issue_date=sample_invoice.issue_date,
            issuer_name=sample_invoice.issuer_name,
            issuer_cnpj=sample_invoice.issuer_cnpj,
            recipient_name=sample_invoice.recipient_name,
            recipient_cnpj_cpf=sample_invoice.recipient_cnpj_cpf,
            total_products=sample_invoice.total_products,
            total_invoice=sample_invoice.total_invoice,
            total_taxes=sample_invoice.total_taxes,
            taxes=sample_invoice.taxes,
            items=sample_invoice.items,
            raw_xml=sample_invoice.raw_xml,
        )
        invoices.append((inv, sample_issues, None))
    
    # Bulk insert
    result = temp_db.save_invoices_batch(invoices)
    
    assert len(result) == 3
    assert all(inv.id is not None for inv in result)
    assert all(len(inv.items) == 1 for inv in result)
    assert all(len(inv.issues) == 2 for inv in result)
    
    # Verify all saved to DB
    all_invoices = temp_db.get_all_invoices()
    assert len(all_invoices) == 3


def test_bulk_insert_with_duplicates(temp_db, sample_invoice, sample_issues):
    """Test bulk insert skips duplicates."""
    # Save one invoice first
    temp_db.save_invoice(sample_invoice, sample_issues)
    
    # Try to bulk insert including the duplicate
    inv2 = InvoiceModel(
        document_type=sample_invoice.document_type,
        document_key=f"{sample_invoice.document_key[:-2]}99",
        document_number="2",
        series=sample_invoice.series,
        issue_date=sample_invoice.issue_date,
        issuer_name=sample_invoice.issuer_name,
        issuer_cnpj=sample_invoice.issuer_cnpj,
        recipient_name=sample_invoice.recipient_name,
        recipient_cnpj_cpf=sample_invoice.recipient_cnpj_cpf,
        total_products=sample_invoice.total_products,
        total_invoice=sample_invoice.total_invoice,
        total_taxes=sample_invoice.total_taxes,
        taxes=sample_invoice.taxes,
        items=sample_invoice.items,
        raw_xml=sample_invoice.raw_xml,
    )
    
    batch = [
        (sample_invoice, sample_issues, None),  # Duplicate
        (inv2, sample_issues, None),            # New
    ]
    
    result = temp_db.save_invoices_batch(batch)
    
    # Should return 2 items (existing + new)
    assert len(result) == 2
    
    # But only 2 total in DB (duplicate not re-inserted)
    all_invoices = temp_db.get_all_invoices()
    assert len(all_invoices) == 2


def test_bulk_insert_with_classification(temp_db, sample_invoice, sample_issues):
    """Test bulk insert with classification data."""
    classification = {
        "operation_type": "purchase",
        "cost_center": "CC001",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
        "used_llm_fallback": False,
    }
    
    batch = [(sample_invoice, sample_issues, classification)]
    result = temp_db.save_invoices_batch(batch)
    
    assert len(result) == 1
    assert result[0].operation_type == "purchase"
    assert result[0].cost_center == "CC001"
    assert result[0].classification_confidence == 0.95
    assert result[0].used_llm_fallback is False


def test_bulk_insert_performance(temp_db, sample_invoice, sample_issues, benchmark=None):
    """
    Test bulk insert performance vs individual inserts.
    
    Note: With SQLite PRAGMAs optimized, both methods are fast.
    Bulk insert advantage grows with larger batches (100+ documents).
    """
    import time
    
    # Create 50 different invoices
    batch = []
    for i in range(50):
        inv = InvoiceModel(
            document_type=sample_invoice.document_type,
            document_key=f"{sample_invoice.document_key[:-4]}{i:04d}",
            document_number=str(i+1),
            series=sample_invoice.series,
            issue_date=sample_invoice.issue_date,
            issuer_name=sample_invoice.issuer_name,
            issuer_cnpj=sample_invoice.issuer_cnpj,
            recipient_name=sample_invoice.recipient_name,
            recipient_cnpj_cpf=sample_invoice.recipient_cnpj_cpf,
            total_products=sample_invoice.total_products,
            total_invoice=sample_invoice.total_invoice,
            total_taxes=sample_invoice.total_taxes,
            taxes=sample_invoice.taxes,
            items=sample_invoice.items,
            raw_xml=sample_invoice.raw_xml,
        )
        batch.append((inv, sample_issues, None))
    
    # Measure bulk insert time
    start = time.time()
    result = temp_db.save_invoices_batch(batch)
    bulk_time = time.time() - start
    
    assert len(result) == 50
    print(f"\nBulk insert 50 invoices: {bulk_time:.3f}s ({bulk_time/50*1000:.1f}ms per invoice)")
    
    # For comparison, measure individual insert time (smaller sample)
    # Create new DB to avoid duplicates
    from pathlib import Path
    import tempfile
    temp_dir = tempfile.mkdtemp()
    db2_path = Path(temp_dir) / "test2.db"
    db2 = DatabaseManager(f"sqlite:///{db2_path}")
    
    individual_times = []
    for i in range(10):  # Just 10 for comparison
        inv = InvoiceModel(
            document_type=sample_invoice.document_type,
            document_key=f"99999999999999999999999999999999999999{i:04d}",
            document_number=str(i+1),
            series=sample_invoice.series,
            issue_date=sample_invoice.issue_date,
            issuer_name=sample_invoice.issuer_name,
            issuer_cnpj=sample_invoice.issuer_cnpj,
            recipient_name=sample_invoice.recipient_name,
            recipient_cnpj_cpf=sample_invoice.recipient_cnpj_cpf,
            total_products=sample_invoice.total_products,
            total_invoice=sample_invoice.total_invoice,
            total_taxes=sample_invoice.total_taxes,
            taxes=sample_invoice.taxes,
            items=sample_invoice.items,
            raw_xml=sample_invoice.raw_xml,
        )
        start = time.time()
        db2.save_invoice(inv, sample_issues)
        individual_times.append(time.time() - start)
    
    avg_individual = sum(individual_times) / len(individual_times)
    print(f"Individual insert average: {avg_individual:.3f}s ({avg_individual*1000:.1f}ms per invoice)")
    
    if bulk_time > 0 and avg_individual > 0:
        speedup = avg_individual / (bulk_time/50)
        print(f"Speedup: {speedup:.1f}x faster")
        
        # With optimized PRAGMAs, both are fast. Bulk should be at least as fast.
        # On larger batches (100+), speedup is 5-10x.
        assert (bulk_time / 50) <= avg_individual * 1.5  # Allow some variance

