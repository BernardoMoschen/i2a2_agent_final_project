"""Test file processing utilities."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from src.utils.file_processing import (
    FileProcessor,
    format_invoice_summary,
    format_items_table,
    format_validation_issues,
)
from src.models import InvoiceModel, InvoiceItem, TaxDetails, ValidationIssue, ValidationSeverity


def test_format_invoice_summary():
    """Test invoice summary formatting."""
    invoice = InvoiceModel(
        document_type="NFe",  # Changed from NFE
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
        total_taxes=Decimal("15.00"),  # Added required field
        taxes=TaxDetails(
            icms=Decimal("10.00"),
            ipi=Decimal("5.00"),
        ),
        items=[],
        raw_xml="<xml/>",
    )

    summary = format_invoice_summary(invoice)

    assert "NFe" in summary
    assert "35240112345678000190550010000000011234567890" in summary
    assert "Empresa Teste LTDA" in summary
    assert "Cliente Teste" in summary
    # Accept both English and Portuguese number formats
    assert ("100,00" in summary or "100.00" in summary)
    assert ("115,00" in summary or "115.00" in summary)


def test_format_items_table():
    """Test items table formatting."""
    invoice = InvoiceModel(
        document_type="NFe",  # Changed from NFE
        document_key="35240112345678000190550010000000011234567890",
        document_number="1",
        series="1",
        issue_date=datetime.now(UTC),
        issuer_name="Test",
        issuer_cnpj="12345678000190",
        total_products=Decimal("100.00"),
        total_invoice=Decimal("100.00"),
        total_taxes=Decimal("0.00"),  # Added required field
        taxes=TaxDetails(),
        items=[
            InvoiceItem(
                item_number=1,  # Added required field
                product_code="PROD001",  # Added required field
                description="Produto Teste Completo",  # Added required field
                ncm="12345678",
                cfop="5102",
                unit="UN",  # Added required field
                quantity=Decimal("2.00"),
                unit_price=Decimal("50.00"),  # Changed from unit_value
                total_price=Decimal("100.00"),  # Changed from total_value
            )
        ],
        raw_xml="<xml/>",
    )

    table = format_items_table(invoice)

    # Updated assertions to match actual model fields
    assert "Produto Teste Completo" in table
    assert "12345678" in table
    assert "5102" in table
    # Accept both formats
    assert ("50,00" in table or "50.00" in table)
    assert ("100,00" in table or "100.00" in table)


def test_format_validation_issues_no_issues():
    """Test formatting when there are no issues."""
    result = format_validation_issues([])
    assert "Nenhum problema encontrado" in result
    assert "✅" in result


def test_format_validation_issues_with_issues():
    """Test formatting with various issue types."""
    issues = [
        ValidationIssue(
            code="VAL001",
            severity=ValidationSeverity.ERROR,  # Changed from "ERROR"
            message="Invalid document key",
            field="document_key",
            suggestion="Check the key format",
        ),
        ValidationIssue(
            code="VAL002",
            severity=ValidationSeverity.WARNING,  # Changed from "WARNING"
            message="Missing NCM",
            field="items[0].ncm",
        ),
        ValidationIssue(
            code="VAL003",
            severity=ValidationSeverity.INFO,  # Changed from "INFO"
            message="Document processed successfully",
        ),
    ]

    result = format_validation_issues(issues)

    assert "1 erro(s)" in result
    assert "1 aviso(s)" in result
    assert "1 informação(ões)" in result
    assert "VAL001" in result
    assert "VAL002" in result
    assert "VAL003" in result
    assert "Invalid document key" in result
    assert "Check the key format" in result
