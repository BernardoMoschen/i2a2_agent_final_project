"""Tests for automatic document classifier."""

import pytest
from decimal import Decimal

from src.models import InvoiceModel, InvoiceItem, TaxDetails
from src.services.classifier import DocumentClassifier


@pytest.fixture
def classifier():
    """Create classifier instance."""
    return DocumentClassifier()


@pytest.fixture
def purchase_invoice():
    """Sample purchase invoice (CFOP 1xxx)."""
    return InvoiceModel(
        document_type="NFe",
        document_key="35240112345678000190550010000000011234567890",
        document_number="123",
        series="1",
        issue_date="2024-01-26T10:30:00",
        issuer_cnpj="12.345.678/0001-90",
        issuer_name="Fornecedor de Materiais Ltda",
        recipient_cnpj_cpf="98.765.432/0001-10",
        recipient_name="Minha Empresa SA",
        total_products=Decimal("1000.00"),
        total_taxes=Decimal("180.00"),
        total_invoice=Decimal("1180.00"),
        taxes=TaxDetails(
            icms=Decimal("100.00"),
            ipi=Decimal("50.00"),
            pis=Decimal("15.00"),
            cofins=Decimal("15.00"),
            issqn=Decimal("0.00"),
        ),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD001",
                description="Notebook Dell Latitude",
                ncm="84713012",  # Computer equipment
                cfop="1102",  # Purchase from same state
                unit="UN",
                quantity=Decimal("2"),
                unit_price=Decimal("500.00"),
                total_price=Decimal("1000.00"),
                taxes=TaxDetails(
                    icms=Decimal("100.00"),
                    ipi=Decimal("50.00"),
                    pis=Decimal("15.00"),
                    cofins=Decimal("15.00"),
                    issqn=Decimal("0.00"),
                ),
            )
        ],
        raw_xml="<xml/>",
    )


@pytest.fixture
def sale_invoice():
    """Sample sale invoice (CFOP 5xxx)."""
    return InvoiceModel(
        document_type="NFe",
        document_key="35240112345678000190550010000000021234567890",
        document_number="456",
        series="1",
        issue_date="2024-01-26T14:30:00",
        issuer_cnpj="98.765.432/0001-10",
        issuer_name="Minha Empresa SA",
        recipient_cnpj_cpf="11.222.333/0001-44",
        recipient_name="Cliente Final Ltda",
        total_products=Decimal("2000.00"),
        total_taxes=Decimal("340.00"),
        total_invoice=Decimal("2340.00"),
        taxes=TaxDetails(
            icms=Decimal("200.00"),
            ipi=Decimal("100.00"),
            pis=Decimal("20.00"),
            cofins=Decimal("20.00"),
            issqn=Decimal("0.00"),
        ),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD002",
                description="Produto Exemplo",
                ncm="12345678",
                cfop="5102",  # Sale to same state
                unit="UN",
                quantity=Decimal("10"),
                unit_price=Decimal("200.00"),
                total_price=Decimal("2000.00"),
                taxes=TaxDetails(
                    icms=Decimal("200.00"),
                    ipi=Decimal("100.00"),
                    pis=Decimal("20.00"),
                    cofins=Decimal("20.00"),
                    issqn=Decimal("0.00"),
                ),
            )
        ],
        raw_xml="<xml/>",
    )


@pytest.fixture
def office_supplies_invoice():
    """Invoice for office supplies."""
    return InvoiceModel(
        document_type="NFe",
        document_key="35240112345678000190550010000000031234567890",
        document_number="789",
        series="1",
        issue_date="2024-01-26T16:00:00",
        issuer_cnpj="55.666.777/0001-88",
        issuer_name="Kalunga Papelaria Ltda",
        recipient_cnpj_cpf="98.765.432/0001-10",
        recipient_name="Minha Empresa SA",
        total_products=Decimal("350.00"),
        total_taxes=Decimal("63.00"),
        total_invoice=Decimal("413.00"),
        taxes=TaxDetails(
            icms=Decimal("42.00"),
            ipi=Decimal("17.50"),
            pis=Decimal("1.75"),
            cofins=Decimal("1.75"),
            issqn=Decimal("0.00"),
        ),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PAP001",
                description="Papel A4 Sulfite 75g",
                ncm="48209000",  # Paper products
                cfop="1102",
                unit="CX",
                quantity=Decimal("5"),
                unit_price=Decimal("70.00"),
                total_price=Decimal("350.00"),
                taxes=TaxDetails(
                    icms=Decimal("42.00"),
                    ipi=Decimal("17.50"),
                    pis=Decimal("1.75"),
                    cofins=Decimal("1.75"),
                    issqn=Decimal("0.00"),
                ),
            )
        ],
        raw_xml="<xml/>",
    )


def test_classify_purchase_operation(classifier, purchase_invoice):
    """Test classification of purchase operation."""
    result = classifier.classify(purchase_invoice)
    
    assert result.operation_type == "purchase"
    assert result.cost_center == "TI - Equipamentos"
    assert result.confidence >= 0.8
    assert not result.used_llm_fallback


def test_classify_sale_operation(classifier, sale_invoice):
    """Test classification of sale operation."""
    result = classifier.classify(sale_invoice)
    
    assert result.operation_type == "sale"
    # Should use fallback since no NCM match
    assert result.used_llm_fallback or result.cost_center == "Não Classificado"


def test_classify_by_ncm(classifier, purchase_invoice):
    """Test cost center classification by NCM."""
    result = classifier.classify(purchase_invoice)
    
    # NCM 8471xxxx should map to TI - Equipamentos
    assert result.cost_center == "TI - Equipamentos"
    assert "NCM" in result.reasoning


def test_classify_by_issuer_name(classifier, office_supplies_invoice):
    """Test cost center classification by issuer name."""
    result = classifier.classify(office_supplies_invoice)
    
    # Should classify by both NCM and issuer name
    assert "Administrativo" in result.cost_center or "Material Escritório" in result.cost_center
    assert result.confidence >= 0.8


def test_operation_type_purchase(classifier, purchase_invoice):
    """Test purchase operation type detection."""
    op_type = classifier._classify_operation_type(purchase_invoice)
    assert op_type == "purchase"


def test_operation_type_sale(classifier, sale_invoice):
    """Test sale operation type detection."""
    op_type = classifier._classify_operation_type(sale_invoice)
    assert op_type == "sale"


def test_operation_type_unknown_cfop(classifier, purchase_invoice):
    """Test unknown CFOP handling."""
    purchase_invoice.items[0].cfop = "9999"  # Invalid CFOP
    op_type = classifier._classify_operation_type(purchase_invoice)
    assert op_type == "unknown"


def test_operation_type_no_items(classifier, purchase_invoice):
    """Test handling invoice with no items."""
    purchase_invoice.items = []
    op_type = classifier._classify_operation_type(purchase_invoice)
    assert op_type == "unknown"


def test_update_ncm_mappings(classifier):
    """Test updating NCM mappings."""
    custom_mappings = {
        ("1234",): "Custom Cost Center",  # Use different NCM to avoid conflict
    }
    
    classifier.update_ncm_mappings(custom_mappings)
    
    # Check if mapping was added (use instance attribute, not class attribute)
    assert ("1234",) in classifier.ncm_cost_centers
    assert classifier.ncm_cost_centers[("1234",)] == "Custom Cost Center"


def test_get_available_cost_centers(classifier):
    """Test retrieving available cost centers."""
    centers = classifier.get_available_cost_centers()
    
    assert isinstance(centers, list)
    assert len(centers) > 0
    assert "TI - Equipamentos" in centers
    assert "Administrativo - Material Escritório" in centers


def test_confidence_score_range(classifier, purchase_invoice):
    """Test that confidence scores are within valid range."""
    result = classifier.classify(purchase_invoice)
    
    assert 0.0 <= result.confidence <= 1.0


def test_telecom_issuer_classification(purchase_invoice):
    """Test telecom issuer name pattern matching."""
    # Create fresh classifier for this test
    classifier = DocumentClassifier()
    
    purchase_invoice.issuer_name = "Vivo Telecomunicações SA"
    purchase_invoice.items[0].ncm = "99999999"  # No NCM match
    
    result = classifier.classify(purchase_invoice)
    
    assert "Telecomunicações" in result.cost_center
    assert result.confidence >= 0.8


def test_energy_issuer_classification(purchase_invoice):
    """Test energy supplier name pattern matching."""
    # Create fresh classifier for this test
    classifier = DocumentClassifier()
    
    purchase_invoice.issuer_name = "CEMIG - Companhia Energética"
    purchase_invoice.items[0].ncm = "99999999"
    
    result = classifier.classify(purchase_invoice)
    
    assert "Energia" in result.cost_center
    assert result.confidence >= 0.8
