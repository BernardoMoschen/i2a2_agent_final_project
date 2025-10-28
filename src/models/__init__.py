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
    
    # Advanced fiscal fields (VAL018, VAL022)
    cst: str | None = Field(None, description="CST/CSOSN - Código de Situação Tributária")
    icms_origin: str | None = Field(None, description="Origem da mercadoria (0-8)")
    icms_rate: Decimal | None = Field(None, description="Alíquota de ICMS aplicada (%)")
    icms_base: Decimal | None = Field(None, description="Base de cálculo do ICMS")

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
    
    # Geographic data (VAL022, VAL025, VAL027)
    issuer_uf: str | None = Field(None, description="Issuer state (UF)")
    recipient_uf: str | None = Field(None, description="Recipient state (UF)")
    issuer_municipio: str | None = Field(None, description="Issuer municipality")
    recipient_municipio: str | None = Field(None, description="Recipient municipality")
    issuer_cep: str | None = Field(None, description="Issuer CEP (postal code)")
    recipient_cep: str | None = Field(None, description="Recipient CEP (postal code)")
    
    # Fiscal identifiers (VAL040)
    issuer_ie: str | None = Field(None, description="Issuer state registration (Inscrição Estadual)")
    recipient_ie: str | None = Field(None, description="Recipient state registration (Inscrição Estadual)")
    
    # Fiscal regime (VAL018)
    tax_regime: str | None = Field(None, description="Tax regime (CRT): 1=Simples, 2=Simples excesso, 3=Normal")

    # Financial totals
    total_products: Decimal = Field(..., description="Total value of products/services")
    total_taxes: Decimal = Field(..., description="Total tax value")
    total_invoice: Decimal = Field(..., description="Total invoice value")
    discount: Decimal = Field(default=Decimal("0"), description="Total discount (vDesc)")
    other_expenses: Decimal = Field(default=Decimal("0"), description="Other expenses (vOutro)")

    # Items
    items: list[InvoiceItem] = Field(default_factory=list, description="Invoice items")

    # Tax breakdown
    taxes: TaxDetails = Field(default_factory=TaxDetails, description="Document-level taxes")

    # Transport-specific fields (CTe/MDFe)
    modal: str | None = Field(
        None, 
        description="Transport mode: 01=Rodoviário, 02=Aéreo, 03=Aquaviário, 04=Ferroviário, 05=Dutoviário, 06=Multimodal"
    )
    rntrc: str | None = Field(
        None, 
        description="RNTRC - Registro Nacional de Transportadores de Carga (8 digits)"
    )
    vehicle_plate: str | None = Field(
        None, 
        description="Vehicle license plate (ABC1234 or ABC1D23 Mercosul format)"
    )
    vehicle_uf: str | None = Field(
        None, 
        description="Vehicle registration state (UF)"
    )
    route_ufs: list[str] = Field(
        default_factory=list, 
        description="Route UF sequence for MDFe (ordered list of states)"
    )
    cargo_weight: Decimal | None = Field(
        None, 
        description="Gross cargo weight in kg (peso bruto)"
    )
    cargo_weight_net: Decimal | None = Field(
        None, 
        description="Net cargo weight in kg (peso líquido)"
    )
    cargo_volume: Decimal | None = Field(
        None, 
        description="Cargo volume in m³"
    )
    service_taker_type: str | None = Field(
        None, 
        description="CTe service taker: 0=Remetente, 1=Expedidor, 2=Recebedor, 3=Destinatário, 4=Outros"
    )
    freight_value: Decimal | None = Field(
        None, 
        description="Freight/transport service value (valor do serviço)"
    )
    freight_type: str | None = Field(
        None, 
        description="Freight type: 0=CIF (remetente), 1=FOB (destinatário), 2=Terceiros, 9=Sem frete"
    )
    dangerous_cargo: bool = Field(
        default=False, 
        description="Indicates if cargo is dangerous/hazardous"
    )
    insurance_value: Decimal | None = Field(
        None, 
        description="Insurance value (valor do seguro)"
    )
    emission_type: str | None = Field(
        None, 
        description="Emission type: 1=Normal, 2=Contingência FS-IA, 3=Contingência SCAN, etc."
    )

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

    @field_validator(
        "cargo_weight", 
        "cargo_weight_net", 
        "cargo_volume", 
        "freight_value", 
        "insurance_value", 
        mode="before"
    )
    @classmethod
    def parse_decimal_optional(cls, v: Any) -> Decimal | None:
        """Parse optional decimal values safely."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            v = v.strip()
            if not v or v == "0" or v == "0.00":
                return None
            return Decimal(v.replace(",", "."))
        return None

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
