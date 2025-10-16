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
