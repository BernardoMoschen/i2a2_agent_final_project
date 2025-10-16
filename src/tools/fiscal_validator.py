"""Fiscal validation tool with declarative rules."""

from collections.abc import Callable
from decimal import Decimal

from src.models import InvoiceModel, ValidationIssue, ValidationSeverity


class ValidationRule:
    """Single validation rule."""

    def __init__(
        self,
        code: str,
        severity: ValidationSeverity,
        message: str,
        check: Callable[[InvoiceModel], bool],
        field: str | None = None,
        suggestion: str | None = None,
    ):
        self.code = code
        self.severity = severity
        self.message = message
        self.check = check
        self.field = field
        self.suggestion = suggestion

    def validate(self, invoice: InvoiceModel) -> ValidationIssue | None:
        """Run validation check and return issue if failed."""
        if not self.check(invoice):
            return ValidationIssue(
                code=self.code,
                severity=self.severity,
                message=self.message,
                field=self.field,
                suggestion=self.suggestion,
            )
        return None


class FiscalValidatorTool:
    """Fiscal validator with declarative rules for Brazilian fiscal documents."""

    # Tolerance for decimal comparisons (to handle rounding differences)
    DECIMAL_TOLERANCE = Decimal("0.02")

    def __init__(self) -> None:
        """Initialize validator with default rules."""
        self.rules = self._build_default_rules()

    def validate(self, invoice: InvoiceModel) -> list[ValidationIssue]:
        """
        Validate invoice against all rules.

        Args:
            invoice: Normalized invoice to validate

        Returns:
            List of validation issues (empty if all pass)
        """
        issues = []
        for rule in self.rules:
            issue = rule.validate(invoice)
            if issue:
                issues.append(issue)
        return issues

    def _build_default_rules(self) -> list[ValidationRule]:
        """Build default validation rules."""
        return [
            # Document key validation
            ValidationRule(
                code="VAL001",
                severity=ValidationSeverity.ERROR,
                message="Document key (chave de acesso) must be 44 digits",
                check=lambda inv: len(inv.document_key) == 44 and inv.document_key.isdigit(),
                field="document_key",
                suggestion="Verify the access key format",
            ),
            # CNPJ validation
            ValidationRule(
                code="VAL002",
                severity=ValidationSeverity.ERROR,
                message="Issuer CNPJ must be 14 digits",
                check=lambda inv: len(
                    inv.issuer_cnpj.replace(".", "").replace("/", "").replace("-", "")
                )
                == 14,
                field="issuer_cnpj",
                suggestion="Verify issuer CNPJ format",
            ),
            # Total validation: sum of items should match total_products
            ValidationRule(
                code="VAL003",
                severity=ValidationSeverity.WARNING,
                message="Sum of item totals does not match total_products (tolerance: 0.02)",
                check=lambda inv: abs(
                    sum(item.total_price for item in inv.items) - inv.total_products
                )
                <= FiscalValidatorTool.DECIMAL_TOLERANCE,
                field="total_products",
                suggestion="Check for rounding errors or missing items",
            ),
            # Total validation: total_invoice should equal
            # total_products + other charges - discounts
            ValidationRule(
                code="VAL004",
                severity=ValidationSeverity.WARNING,
                message="Total invoice value does not match expected calculation",
                check=lambda inv: abs(inv.total_invoice - inv.total_products)
                <= FiscalValidatorTool.DECIMAL_TOLERANCE,
                field="total_invoice",
                suggestion="Verify freight, insurance, discounts, and other charges",
            ),
            # Items must exist
            ValidationRule(
                code="VAL005",
                severity=ValidationSeverity.ERROR,
                message="Invoice must contain at least one item",
                check=lambda inv: len(inv.items) > 0,
                field="items",
                suggestion="Verify XML structure and item parsing",
            ),
            # Each item must have valid CFOP
            ValidationRule(
                code="VAL006",
                severity=ValidationSeverity.WARNING,
                message="One or more items have invalid CFOP (must be 4 digits)",
                check=lambda inv: all(
                    len(item.cfop) == 4 and item.cfop.isdigit() for item in inv.items
                ),
                field="items[].cfop",
                suggestion="Verify CFOP codes against fiscal operation table",
            ),
            # Each item should have NCM (optional but recommended)
            ValidationRule(
                code="VAL007",
                severity=ValidationSeverity.INFO,
                message="One or more items missing NCM code",
                check=lambda inv: all(
                    item.ncm is not None and item.ncm != "" for item in inv.items
                ),
                field="items[].ncm",
                suggestion="NCM codes help with classification and tax reporting",
            ),
            # Item quantity * unit_price should match total_price
            ValidationRule(
                code="VAL008",
                severity=ValidationSeverity.WARNING,
                message="One or more items have quantity * unit_price != total_price",
                check=lambda inv: all(
                    abs(item.quantity * item.unit_price - item.total_price)
                    <= FiscalValidatorTool.DECIMAL_TOLERANCE
                    for item in inv.items
                ),
                field="items[].total_price",
                suggestion="Check for rounding errors in item calculations",
            ),
            # Positive values
            ValidationRule(
                code="VAL009",
                severity=ValidationSeverity.ERROR,
                message="Total invoice value must be positive",
                check=lambda inv: inv.total_invoice > 0,
                field="total_invoice",
                suggestion="Verify if this is a return or cancellation document",
            ),
            # Future date check
            ValidationRule(
                code="VAL010",
                severity=ValidationSeverity.WARNING,
                message="Issue date is in the future",
                check=lambda inv: inv.issue_date <= inv.parsed_at,
                field="issue_date",
                suggestion="Verify system clock and document date",
            ),
        ]

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule."""
        self.rules.append(rule)

    def remove_rule(self, code: str) -> None:
        """Remove a validation rule by code."""
        self.rules = [r for r in self.rules if r.code != code]
