"""Unit tests for fiscal validator tool."""

from datetime import datetime, timedelta
from decimal import Decimal

from src.models import (
    DocumentType,
    InvoiceItem,
    InvoiceModel,
    TaxDetails,
    ValidationSeverity,
)
from src.tools.fiscal_validator import FiscalValidatorTool, ValidationRule


def create_valid_invoice() -> InvoiceModel:
    """Create a valid invoice for testing."""
    return InvoiceModel(
        document_type=DocumentType.NFE,
        document_key="35240112345678000190550010000000011234567890",
        document_number="1",
        series="1",
        issue_date=datetime.utcnow() - timedelta(days=1),  # Yesterday
        issuer_cnpj="12345678000190",
        issuer_name="EMPRESA TESTE LTDA",
        recipient_cnpj_cpf="98765432000100",
        recipient_name="CLIENTE TESTE SA",
        total_products=Decimal("1000.00"),
        total_taxes=Decimal("372.50"),
        total_invoice=Decimal("1000.00"),  # Simplified: no freight/discounts
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD001",
                description="PRODUTO TESTE",
                ncm="12345678",
                cfop="5102",
                unit="UN",
                quantity=Decimal("10.00"),
                unit_price=Decimal("100.00"),
                total_price=Decimal("1000.00"),
                taxes=TaxDetails(
                    icms=Decimal("180.00"),
                    ipi=Decimal("100.00"),
                    pis=Decimal("16.50"),
                    cofins=Decimal("76.00"),
                ),
            )
        ],
        taxes=TaxDetails(
            icms=Decimal("180.00"),
            ipi=Decimal("100.00"),
            pis=Decimal("16.50"),
            cofins=Decimal("76.00"),
        ),
    )


class TestFiscalValidatorTool:
    """Test suite for FiscalValidatorTool."""

    def test_validate_valid_invoice(self) -> None:
        """Test that a valid invoice passes all validations."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        issues = validator.validate(invoice)

        # Should have no errors, only possible info/warnings
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0

    def test_invalid_document_key_length(self) -> None:
        """Test that invalid document key length fails validation."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.document_key = "123"  # Too short

        issues = validator.validate(invoice)
        key_issues = [i for i in issues if i.code == "VAL001"]

        assert len(key_issues) == 1
        assert key_issues[0].severity == ValidationSeverity.ERROR
        assert key_issues[0].field == "document_key"

    def test_invalid_issuer_cnpj(self) -> None:
        """Test that invalid issuer CNPJ fails validation."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.issuer_cnpj = "123"  # Too short

        issues = validator.validate(invoice)
        cnpj_issues = [i for i in issues if i.code == "VAL002"]

        assert len(cnpj_issues) == 1
        assert cnpj_issues[0].severity == ValidationSeverity.ERROR

    def test_item_total_mismatch(self) -> None:
        """Test that mismatched item totals trigger warning."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        # Make sum of items != total_products
        invoice.total_products = Decimal("999.00")  # Should be 1000.00

        issues = validator.validate(invoice)
        total_issues = [i for i in issues if i.code == "VAL003"]

        assert len(total_issues) == 1
        assert total_issues[0].severity == ValidationSeverity.WARNING

    def test_no_items_fails_validation(self) -> None:
        """Test that invoice with no items fails validation."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.items = []

        issues = validator.validate(invoice)
        item_issues = [i for i in issues if i.code == "VAL005"]

        assert len(item_issues) == 1
        assert item_issues[0].severity == ValidationSeverity.ERROR

    def test_invalid_cfop_format(self) -> None:
        """Test that invalid CFOP format triggers warning."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.items[0].cfop = "ABC"  # Invalid format

        issues = validator.validate(invoice)
        cfop_issues = [i for i in issues if i.code == "VAL006"]

        assert len(cfop_issues) == 1
        assert cfop_issues[0].severity == ValidationSeverity.WARNING

    def test_missing_ncm_info(self) -> None:
        """Test that missing NCM triggers info-level issue."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.items[0].ncm = None

        issues = validator.validate(invoice)
        ncm_issues = [i for i in issues if i.code == "VAL007"]

        assert len(ncm_issues) == 1
        assert ncm_issues[0].severity == ValidationSeverity.INFO

    def test_item_price_calculation_error(self) -> None:
        """Test that item quantity * unit_price != total_price triggers warning."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.items[0].total_price = Decimal("999.00")  # Should be 1000.00

        issues = validator.validate(invoice)
        calc_issues = [i for i in issues if i.code == "VAL008"]

        assert len(calc_issues) == 1
        assert calc_issues[0].severity == ValidationSeverity.WARNING

    def test_negative_total_invoice(self) -> None:
        """Test that negative total invoice fails validation."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.total_invoice = Decimal("-100.00")

        issues = validator.validate(invoice)
        negative_issues = [i for i in issues if i.code == "VAL009"]

        assert len(negative_issues) == 1
        assert negative_issues[0].severity == ValidationSeverity.ERROR

    def test_future_date_warning(self) -> None:
        """Test that future issue date triggers warning."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        invoice.issue_date = datetime.utcnow() + timedelta(days=1)  # Tomorrow

        issues = validator.validate(invoice)
        date_issues = [i for i in issues if i.code == "VAL010"]

        assert len(date_issues) == 1
        assert date_issues[0].severity == ValidationSeverity.WARNING

    def test_add_custom_rule(self) -> None:
        """Test adding a custom validation rule."""
        validator = FiscalValidatorTool()

        # Add custom rule: issuer name must not be empty
        custom_rule = ValidationRule(
            code="CUSTOM001",
            severity=ValidationSeverity.ERROR,
            message="Issuer name cannot be empty",
            check=lambda inv: inv.issuer_name != "",
            field="issuer_name",
        )
        validator.add_rule(custom_rule)

        invoice = create_valid_invoice()
        invoice.issuer_name = ""

        issues = validator.validate(invoice)
        custom_issues = [i for i in issues if i.code == "CUSTOM001"]

        assert len(custom_issues) == 1

    def test_remove_rule(self) -> None:
        """Test removing a validation rule."""
        validator = FiscalValidatorTool()
        validator.remove_rule("VAL001")  # Remove document key check

        invoice = create_valid_invoice()
        invoice.document_key = "123"  # Invalid, but rule removed

        issues = validator.validate(invoice)
        key_issues = [i for i in issues if i.code == "VAL001"]

        assert len(key_issues) == 0  # Rule was removed

    def test_decimal_tolerance(self) -> None:
        """Test that decimal tolerance works correctly."""
        validator = FiscalValidatorTool()
        invoice = create_valid_invoice()
        # Create small rounding difference within tolerance
        invoice.total_products = Decimal("1000.01")  # 0.01 difference, within 0.02 tolerance

        issues = validator.validate(invoice)
        total_issues = [i for i in issues if i.code == "VAL003"]

        assert len(total_issues) == 0  # Should pass due to tolerance
