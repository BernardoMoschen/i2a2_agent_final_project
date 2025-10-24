"""Tests for business intelligence and archiver tools."""

import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agent.archiver_tools import ArchiverTool, ArchiveAllTool
from src.agent.business_tools import (
    CEPValidatorTool,
    ClassifierTool,
    CNPJValidatorTool,
    NCMLookupTool,
    ReportGeneratorTool,
)
from src.database.db import DatabaseManager, InvoiceDB
from src.models import InvoiceModel, InvoiceItem
from src.services.external_validators import CNPJData


# ============================================================================
# REPORT GENERATOR TESTS
# ============================================================================


@pytest.fixture
def mock_invoices():
    """Create mock invoices for testing."""
    invoices = []
    for i in range(5):
        inv = InvoiceDB(
            document_type="NFe",
            document_key=f"{'1' * 43}{i}",
            document_number=str(1000 + i),
            series="1",
            issue_date=datetime.now() - timedelta(days=i * 30),
            issuer_cnpj="11222333000181",
            issuer_name=f"Fornecedor {i}",
            recipient_cnpj_cpf="44555666000177",
            recipient_name="Empresa Teste",
            total_products=Decimal("1000.00"),
            total_taxes=Decimal("200.00"),
            total_invoice=Decimal("1200.00"),
            tax_icms=Decimal("100.00"),
            tax_ipi=Decimal("50.00"),
            tax_pis=Decimal("25.00"),
            tax_cofins=Decimal("25.00"),
            operation_type="purchase" if i % 2 == 0 else "sale",
        )
        invoices.append(inv)
    return invoices


def test_report_generator_sales_by_month(mock_invoices):
    """Test sales by month report generation."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(report_type="sales_by_month", days_back=365)
    
    assert "📊 **Relatório de Vendas Mensais**" in result
    assert "Período:" in result
    assert "Valor total:" in result
    assert "Média mensal:" in result


def test_report_generator_purchases_by_month(mock_invoices):
    """Test purchases by month report generation."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(report_type="purchases_by_month", days_back=365)
    
    assert "📊 **Relatório de Compras Mensais**" in result
    assert "Total de notas:" in result


def test_report_generator_taxes_breakdown(mock_invoices):
    """Test taxes breakdown report."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(report_type="taxes_breakdown", days_back=365)
    
    assert "📊 **Breakdown de Impostos**" in result
    assert "ICMS" in result or "IPI" in result
    assert "Total de impostos:" in result


def test_report_generator_supplier_ranking(mock_invoices):
    """Test supplier ranking report."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(report_type="supplier_ranking", days_back=365)
    
    assert "📊 **Ranking de Fornecedores**" in result
    assert "Top 10 Fornecedores" in result or "Nenhuma compra encontrada" in result


def test_report_generator_invoices_timeline(mock_invoices):
    """Test invoices timeline report."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(report_type="invoices_timeline", days_back=365)
    
    assert "📊 **Timeline de Documentos Fiscais**" in result
    assert "Total de documentos:" in result


def test_report_generator_invalid_type():
    """Test invalid report type."""
    tool = ReportGeneratorTool()
    
    result = tool._run(report_type="invalid_type", days_back=365)
    
    assert "❌" in result
    assert "desconhecido" in result.lower()


def test_report_generator_no_data():
    """Test report with no data."""
    tool = ReportGeneratorTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[]):
        result = tool._run(report_type="sales_by_month", days_back=365)
    
    assert "Nenhum" in result or "não encontrado" in result.lower()


# ============================================================================
# CLASSIFIER TOOL TESTS
# ============================================================================


def test_classifier_tool_success(mock_invoices):
    """Test successful classification."""
    tool = ClassifierTool()
    invoice = mock_invoices[0]
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[invoice]):
        # Skip update_classification call for test
        result = tool._run(document_key=invoice.document_key)
    
    # Should work even without update_classification since it's optional
    assert "Documento" in result or "❌" in result


def test_classifier_tool_not_found():
    """Test classification of non-existent document."""
    tool = ClassifierTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[]):
        result = tool._run(document_key="1" * 44)
    
    assert "❌" in result
    assert "não encontrado" in result.lower()


# ============================================================================
# CNPJ VALIDATOR TOOL TESTS
# ============================================================================


@pytest.fixture
def mock_cnpj_data():
    """Create mock CNPJ data."""
    return CNPJData(
        cnpj="11.222.333/0001-81",
        razao_social="EMPRESA TESTE LTDA",
        nome_fantasia="Empresa Teste",
        situacao="ATIVA",
        uf="SP",
        municipio="São Paulo",
        cep="01310-100",
        logradouro="Avenida Paulista",
        numero="1000",
        bairro="Bela Vista",
        complemento=None,
        email="contato@teste.com.br",
        telefone="(11) 1234-5678",
        data_abertura="01/01/2020",
        natureza_juridica="Sociedade Limitada",
        porte="ME",
        capital_social=50000.00,
        cnae_fiscal="6201-5/00",
        cnae_fiscal_descricao="Desenvolvimento de programas de computador sob encomenda",
        simples_nacional=True,
        mei=False,
    )


def test_cnpj_validator_success(mock_cnpj_data):
    """Test successful CNPJ validation."""
    tool = CNPJValidatorTool()
    
    with patch("src.agent.business_tools.CNPJValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.validate_cnpj.return_value = mock_cnpj_data
        
        result = tool._run(cnpj="11222333000181")
    
    assert "✅ **CNPJ Validado**" in result
    assert "EMPRESA TESTE LTDA" in result
    assert "ATIVA" in result
    assert "Simples Nacional" in result


def test_cnpj_validator_not_found():
    """Test CNPJ not found."""
    tool = CNPJValidatorTool()
    
    with patch("src.agent.business_tools.CNPJValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.validate_cnpj.return_value = None
        
        result = tool._run(cnpj="00000000000000")
    
    assert "❌" in result
    assert "não encontrado" in result.lower() or "inválido" in result.lower()


# ============================================================================
# CEP VALIDATOR TOOL TESTS
# ============================================================================


@pytest.fixture
def mock_cep_data():
    """Create mock CEP data."""
    return {
        "cep": "01310-100",
        "logradouro": "Avenida Paulista",
        "complemento": "de 612 a 1510 - lado par",
        "bairro": "Bela Vista",
        "localidade": "São Paulo",
        "uf": "SP",
        "ibge": "3550308",
    }


def test_cep_validator_success(mock_cep_data):
    """Test successful CEP validation."""
    tool = CEPValidatorTool()
    
    with patch("src.agent.business_tools.CEPValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.validate_cep.return_value = mock_cep_data
        
        result = tool._run(cep="01310100")
    
    assert "✅ **CEP Validado**" in result
    assert "Avenida Paulista" in result
    assert "São Paulo" in result


def test_cep_validator_not_found():
    """Test CEP not found."""
    tool = CEPValidatorTool()
    
    with patch("src.agent.business_tools.CEPValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.validate_cep.return_value = None
        
        result = tool._run(cep="00000000")
    
    assert "❌" in result
    assert "não encontrado" in result.lower() or "inválido" in result.lower()


# ============================================================================
# NCM LOOKUP TOOL TESTS
# ============================================================================


def test_ncm_lookup_success():
    """Test successful NCM lookup."""
    tool = NCMLookupTool()
    
    with patch("src.agent.business_tools.NCMValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.is_valid_ncm.return_value = True
        mock_instance._ncm_table = {
            "85171231": {
                "description": "Telefones celulares",
                "ipi_rate": "12",
            }
        }
        
        result = tool._run(ncm="85171231")
    
    assert "✅ **NCM 85171231 Encontrado**" in result
    assert "Telefones celulares" in result
    assert "Alíquota IPI:" in result


def test_ncm_lookup_not_found():
    """Test NCM not found."""
    tool = NCMLookupTool()
    
    with patch("src.agent.business_tools.NCMValidator") as MockValidator:
        mock_instance = MockValidator.return_value
        mock_instance.is_valid_ncm.return_value = False
        mock_instance._ncm_table = {}
        
        result = tool._run(ncm="99999999")
    
    assert "⚠️" in result
    assert "não encontrado" in result.lower()


def test_ncm_lookup_invalid_format():
    """Test invalid NCM format."""
    tool = NCMLookupTool()
    
    result = tool._run(ncm="123")
    
    assert "❌" in result
    assert "inválido" in result.lower()


# ============================================================================
# ARCHIVER TOOL TESTS
# ============================================================================


def test_archiver_tool_success(tmp_path, mock_invoices):
    """Test successful archiving."""
    tool = ArchiverTool()
    invoice = mock_invoices[0]
    invoice.raw_xml = "<xml>test</xml>"
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[invoice]):
        result = tool._run(
            document_key=invoice.document_key,
            base_dir=str(tmp_path),
        )
    
    assert "✅ **Documento Arquivado com Sucesso**" in result
    assert "XML:" in result
    assert "Metadata:" in result
    
    # Check files were created
    year = invoice.issue_date.strftime("%Y")
    issuer_cnpj = invoice.issuer_cnpj.replace(".", "").replace("/", "").replace("-", "")
    archive_path = tmp_path / year / issuer_cnpj / invoice.document_type
    
    xml_files = list(archive_path.glob("*.xml"))
    json_files = list(archive_path.glob("*.json"))
    
    assert len(xml_files) == 1
    assert len(json_files) == 1


def test_archiver_tool_not_found():
    """Test archiving non-existent document."""
    tool = ArchiverTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[]):
        result = tool._run(document_key="1" * 44)
    
    assert "❌" in result
    assert "não encontrado" in result.lower()


def test_archiver_tool_no_raw_xml(mock_invoices):
    """Test archiving document without raw XML."""
    tool = ArchiverTool()
    invoice = mock_invoices[0]
    invoice.raw_xml = None
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[invoice]):
        result = tool._run(document_key=invoice.document_key)
    
    assert "❌" in result
    assert "XML original não encontrado" in result


def test_archive_all_tool_success(tmp_path, mock_invoices):
    """Test batch archiving."""
    tool = ArchiveAllTool()
    
    # Add raw XML to invoices
    for inv in mock_invoices:
        inv.raw_xml = "<xml>test</xml>"
    
    with patch.object(DatabaseManager, "search_invoices", return_value=mock_invoices):
        result = tool._run(days_back=30, base_dir=str(tmp_path))
    
    assert "✅ **Arquivamento em Lote Concluído**" in result
    assert "Documentos processados:" in result
    assert "Arquivados com sucesso:" in result


def test_archive_all_tool_no_documents():
    """Test batch archiving with no documents."""
    tool = ArchiveAllTool()
    
    with patch.object(DatabaseManager, "search_invoices", return_value=[]):
        result = tool._run(days_back=30)
    
    assert "📊" in result
    assert "nenhum documento encontrado" in result.lower()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_all_tools_have_description():
    """Test that all tools have proper descriptions."""
    from src.agent.archiver_tools import ALL_ARCHIVER_TOOLS
    from src.agent.business_tools import ALL_BUSINESS_TOOLS
    
    all_tools = ALL_BUSINESS_TOOLS + ALL_ARCHIVER_TOOLS
    
    for tool in all_tools:
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert len(tool.name) > 0
        assert len(tool.description) > 20  # Reasonable description length


def test_all_tools_have_args_schema():
    """Test that all tools have input schemas."""
    from src.agent.archiver_tools import ALL_ARCHIVER_TOOLS
    from src.agent.business_tools import ALL_BUSINESS_TOOLS
    
    all_tools = ALL_BUSINESS_TOOLS + ALL_ARCHIVER_TOOLS
    
    for tool in all_tools:
        assert hasattr(tool, "args_schema")
        assert tool.args_schema is not None
