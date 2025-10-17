"""Pydantic models for fiscal documents and validation."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentType(str, Enum):
    """Supported fiscal document types."""

    NFE = "NFe"  # Nota Fiscal Eletrônica
    NFCE = "NFCe"  # Nota Fiscal de Consumidor Eletrônica
    CTE = "CTe"  # Conhecimento de Transporte Eletrônico
    MDFE = "MDFe"  # Manifesto Eletrônico de Documentos Fiscais


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Structured validation issue."""

    code: str = Field(..., description="Unique validation rule code (e.g., 'VAL001')")
    severity: ValidationSeverity = Field(..., description="Issue severity level")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(None, description="Field that failed validation")
    suggestion: str | None = Field(None, description="Suggested fix or action")

    model_config = ConfigDict(use_enum_values=True)


class TaxDetails(BaseModel):
    """Tax breakdown for an item or document."""

    icms: Decimal = Field(default=Decimal("0"), description="ICMS value")
    ipi: Decimal = Field(default=Decimal("0"), description="IPI value")
    pis: Decimal = Field(default=Decimal("0"), description="PIS value")
    cofins: Decimal = Field(default=Decimal("0"), description="COFINS value")
    issqn: Decimal = Field(default=Decimal("0"), description="ISSQN value (for services)")

    @field_validator("icms", "ipi", "pis", "cofins", "issqn", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Decimal:
        """Parse decimal values safely."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v.replace(",", "."))
        return Decimal("0")


class InvoiceItem(BaseModel):
    """Individual item in a fiscal invoice."""

    item_number: int = Field(..., description="Sequential item number")
    product_code: str = Field(..., description="Product code (SKU or internal code)")
    description: str = Field(..., description="Product description")
    ncm: str | None = Field(None, description="NCM (Nomenclatura Comum do Mercosul)")
    cfop: str = Field(..., description="CFOP (Código Fiscal de Operações e Prestações)")
    unit: str = Field(..., description="Unit of measurement")
    quantity: Decimal = Field(..., description="Quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_price: Decimal = Field(..., description="Total item price")
    taxes: TaxDetails = Field(default_factory=TaxDetails, description="Tax breakdown")

    @field_validator("quantity", "unit_price", "total_price", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Decimal:
        """Parse decimal values safely."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v.replace(",", "."))
        return Decimal("0")


class InvoiceModel(BaseModel):
    """Normalized fiscal invoice model (NFe, NFCe, CTe, MDFe)."""

    # Document metadata
    document_type: DocumentType = Field(..., description="Type of fiscal document")
    document_key: str = Field(..., description="44-digit access key (chave de acesso)")
    document_number: str = Field(..., description="Invoice number")
    series: str = Field(..., description="Invoice series")
    issue_date: datetime = Field(..., description="Issue date and time")

    # Parties
    issuer_cnpj: str = Field(..., description="Issuer CNPJ (redacted in logs by default)")
    issuer_name: str = Field(..., description="Issuer legal name")
    recipient_cnpj_cpf: str | None = Field(
        None, description="Recipient CNPJ/CPF (redacted in logs by default)"
    )
    recipient_name: str | None = Field(None, description="Recipient name")

    # Financial totals
    total_products: Decimal = Field(..., description="Total value of products/services")
    total_taxes: Decimal = Field(..., description="Total tax value")
    total_invoice: Decimal = Field(..., description="Total invoice value")

    # Items
    items: list[InvoiceItem] = Field(default_factory=list, description="Invoice items")

    # Tax breakdown
    taxes: TaxDetails = Field(default_factory=TaxDetails, description="Document-level taxes")

    # Additional metadata
    raw_xml: str | None = Field(None, description="Original XML (for storage)")
    parsed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Parse timestamp"
    )

    @field_validator("total_products", "total_taxes", "total_invoice", mode="before")
    @classmethod
    def parse_decimal(cls, v: Any) -> Decimal:
        """Parse decimal values safely."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v.replace(",", "."))
        return Decimal("0")

    model_config = ConfigDict(use_enum_values=True)


class ClassificationResult(BaseModel):
    """Result of document classification."""

    operation_type: str = Field(..., description="Operation type (purchase/sale/transfer/return)")
    cost_center: str = Field(..., description="Assigned cost center")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")
    reasoning: str | None = Field(None, description="Explanation of classification")
    used_llm_fallback: bool = Field(
        default=False, description="Whether LLM fallback was used"
    )

    model_config = ConfigDict(use_enum_values=True)
