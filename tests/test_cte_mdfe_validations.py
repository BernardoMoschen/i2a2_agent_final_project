"""Tests for CTe and MDFe specific validations."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.models import DocumentType, InvoiceModel, TaxDetails
from src.tools.fiscal_validator import FiscalValidatorTool


# ===== CTe TEST SAMPLES =====

def create_valid_cte() -> InvoiceModel:
    """Create a valid CTe for testing."""
    cte_xml = """<?xml version="1.0" encoding="UTF-8"?>
<cteProc versao="3.00" xmlns="http://www.portalfiscal.inf.br/cte">
    <CTe>
        <infCte Id="CTe35240112345678000195570010001234561000123456" versao="3.00">
            <ide>
                <cUF>35</cUF>
                <cCT>12345678</cCT>
                <CFOP>6352</CFOP>
                <natOp>PRESTACAO DE SERVICO DE TRANSPORTE</natOp>
                <modal>01</modal>
                <mod>57</mod>
                <serie>1</serie>
                <nCT>123456</nCT>
                <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>12345678000195</CNPJ>
                <xNome>TRANSPORTADORA TESTE</xNome>
                <enderEmit>
                    <UF>SP</UF>
                    <xMun>SAO PAULO</xMun>
                    <CEP>01234567</CEP>
                </enderEmit>
            </emit>
            <rodo>
                <RNTRC>12345678</RNTRC>
                <veicTracao>
                    <placa>ABC1234</placa>
                </veicTracao>
            </rodo>
            <vPrest>
                <vTPrest>1500.00</vTPrest>
            </vPrest>
        </infCte>
    </CTe>
</cteProc>"""
    
    return InvoiceModel(
        document_type=DocumentType.CTE,
        document_key="35240112345678000195570010001234561000123456",
        document_number="123456",
        series="1",
        issue_date=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        issuer_cnpj="12345678000195",
        issuer_name="TRANSPORTADORA TESTE",
        recipient_cnpj_cpf="98765432000198",
        recipient_name="DESTINATARIO TESTE",
        issuer_uf="SP",
        recipient_uf="RS",
        total_products=Decimal("1500.00"),
        total_taxes=Decimal("180.00"),
        total_invoice=Decimal("1500.00"),
        items=[],
        taxes=TaxDetails(),
        # Transport-specific fields
        modal="01",
        rntrc="12345678",
        vehicle_plate="ABC1234",
        freight_value=Decimal("1500.00"),
        raw_xml=cte_xml
    )


def create_cte_invalid_modal() -> InvoiceModel:
    """Create CTe with invalid modal."""
    cte = create_valid_cte()
    cte.modal = "99"  # Invalid modal
    return cte


def create_cte_invalid_rntrc() -> InvoiceModel:
    """Create CTe with invalid RNTRC."""
    cte = create_valid_cte()
    cte.rntrc = "123"  # Too short
    return cte


def create_cte_invalid_cfop() -> InvoiceModel:
    """Create CTe with invalid CFOP for transport."""
    cte = create_valid_cte()
    cte.raw_xml = cte.raw_xml.replace("<CFOP>6352</CFOP>", "<CFOP>5102</CFOP>")
    return cte


def create_cte_zero_value() -> InvoiceModel:
    """Create CTe with zero service value."""
    cte = create_valid_cte()
    cte.total_invoice = Decimal("0")
    return cte


def create_cte_invalid_plate() -> InvoiceModel:
    """Create CTe with invalid vehicle plate."""
    cte = create_valid_cte()
    cte.vehicle_plate = "INVALID"  # Invalid format
    return cte


def create_cte_invalid_uf() -> InvoiceModel:
    """Create CTe with invalid UF."""
    cte = create_valid_cte()
    cte.issuer_uf = "XX"  # Invalid UF
    return cte


# ===== MDFe TEST SAMPLES =====

def create_valid_mdfe() -> InvoiceModel:
    """Create a valid MDFe for testing."""
    mdfe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<mdfeProc versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe">
    <MDFe>
        <infMDFe Id="MDFe35240112345678000195580010001234561000123450" versao="3.00">
            <ide>
                <cUF>35</cUF>
                <modal>01</modal>
                <mod>58</mod>
                <serie>1</serie>
                <nMDF>123456</nMDF>
                <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>12345678000195</CNPJ>
                <xNome>TRANSPORTADORA TESTE</xNome>
                <enderEmit>
                    <UF>SP</UF>
                    <xMun>SAO PAULO</xMun>
                </enderEmit>
            </emit>
            <infPercurso>
                <UFPer>SP</UFPer>
            </infPercurso>
            <infPercurso>
                <UFPer>PR</UFPer>
            </infPercurso>
            <infPercurso>
                <UFPer>SC</UFPer>
            </infPercurso>
            <rodo>
                <veicTracao>
                    <placa>DEF5678</placa>
                </veicTracao>
            </rodo>
            <tot>
                <qCarga>15000.5</qCarga>
            </tot>
        </infMDFe>
    </MDFe>
</mdfeProc>"""
    
    return InvoiceModel(
        document_type=DocumentType.MDFE,
        document_key="35240112345678000195580010001234561000123450",
        document_number="123456",
        series="1",
        issue_date=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        issuer_cnpj="12345678000195",
        issuer_name="TRANSPORTADORA TESTE",
        issuer_uf="SP",
        total_products=Decimal("0"),
        total_taxes=Decimal("0"),
        total_invoice=Decimal("0"),
        items=[],
        taxes=TaxDetails(),
        # Transport-specific fields
        modal="01",
        vehicle_plate="DEF5678",
        route_ufs=["SP", "PR", "SC"],
        cargo_weight=Decimal("15000.5"),
        raw_xml=mdfe_xml
    )


def create_mdfe_invalid_modal() -> InvoiceModel:
    """Create MDFe with invalid modal."""
    mdfe = create_valid_mdfe()
    mdfe.modal = "05"  # Pipeline not valid for MDFe
    return mdfe


def create_mdfe_duplicate_uf_route() -> InvoiceModel:
    """Create MDFe with duplicate UF in route."""
    mdfe = create_valid_mdfe()
    mdfe.route_ufs = ["SP", "PR", "SP"]  # Duplicate SP
    return mdfe


def create_mdfe_invalid_plate() -> InvoiceModel:
    """Create MDFe with invalid vehicle plate."""
    mdfe = create_valid_mdfe()
    mdfe.vehicle_plate = "12345"  # Invalid format
    return mdfe


def create_mdfe_zero_weight() -> InvoiceModel:
    """Create MDFe with zero weight."""
    mdfe = create_valid_mdfe()
    mdfe.cargo_weight = Decimal("0")
    return mdfe


# ===== VALIDATION TESTS =====

class TestCTeValidations:
    """Test CTe-specific validations."""
    
    def test_valid_cte_passes_all_validations(self):
        """Valid CTe should pass all validations."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_valid_cte()
        
        issues = validator.validate(cte)
        
        # Should have no errors (may have warnings/info)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Valid CTe should not have errors: {errors}"
    
    def test_cte_invalid_modal_fails_val050(self):
        """CTe with invalid modal should fail VAL050."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_invalid_modal()
        
        issues = validator.validate(cte)
        
        val050_issues = [i for i in issues if i.code == "VAL050"]
        assert len(val050_issues) == 1, "Should have VAL050 error"
        assert val050_issues[0].severity == "error"
    
    def test_cte_invalid_rntrc_fails_val051(self):
        """CTe with invalid RNTRC should fail VAL051."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_invalid_rntrc()
        
        issues = validator.validate(cte)
        
        val051_issues = [i for i in issues if i.code == "VAL051"]
        assert len(val051_issues) == 1, "Should have VAL051 warning"
        assert val051_issues[0].severity == "warning"
    
    def test_cte_invalid_cfop_fails_val052(self):
        """CTe with non-transport CFOP should fail VAL052."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_invalid_cfop()
        
        issues = validator.validate(cte)
        
        val052_issues = [i for i in issues if i.code == "VAL052"]
        assert len(val052_issues) == 1, "Should have VAL052 error"
        assert val052_issues[0].severity == "error"
    
    def test_cte_zero_value_fails_val053(self):
        """CTe with zero service value should fail VAL053."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_zero_value()
        
        issues = validator.validate(cte)
        
        val053_issues = [i for i in issues if i.code == "VAL053"]
        assert len(val053_issues) == 1, "Should have VAL053 error"
        assert val053_issues[0].severity == "error"
    
    def test_cte_invalid_plate_fails_val054(self):
        """CTe with invalid vehicle plate should fail VAL054."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_invalid_plate()
        
        issues = validator.validate(cte)
        
        val054_issues = [i for i in issues if i.code == "VAL054"]
        assert len(val054_issues) == 1, "Should have VAL054 warning"
        assert val054_issues[0].severity == "warning"
    
    def test_cte_invalid_uf_fails_val055(self):
        """CTe with invalid UF should fail VAL055."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_cte_invalid_uf()
        
        issues = validator.validate(cte)
        
        val055_issues = [i for i in issues if i.code == "VAL055"]
        assert len(val055_issues) == 1, "Should have VAL055 error"
        assert val055_issues[0].severity == "error"
    
    def test_cte_skips_item_validations(self):
        """CTe should skip item-based validations (VAL005-VAL008)."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        cte = create_valid_cte()
        
        issues = validator.validate(cte)
        
        # Should not have VAL005 error (items required)
        val005_issues = [i for i in issues if i.code == "VAL005"]
        assert len(val005_issues) == 0, "CTe should skip VAL005 (items not required)"


class TestMDFeValidations:
    """Test MDFe-specific validations."""
    
    def test_valid_mdfe_passes_all_validations(self):
        """Valid MDFe should pass all validations."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_valid_mdfe()
        
        issues = validator.validate(mdfe)
        
        # Should have no errors (may have warnings/info)
        errors = [i for i in issues if i.severity == "error"]
        assert len(errors) == 0, f"Valid MDFe should not have errors: {errors}"
    
    def test_mdfe_invalid_modal_fails_val060(self):
        """MDFe with invalid modal should fail VAL060."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_mdfe_invalid_modal()
        
        issues = validator.validate(mdfe)
        
        val060_issues = [i for i in issues if i.code == "VAL060"]
        assert len(val060_issues) == 1, "Should have VAL060 error"
        assert val060_issues[0].severity == "error"
    
    def test_mdfe_duplicate_uf_route_fails_val061(self):
        """MDFe with duplicate UF in route should fail VAL061."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_mdfe_duplicate_uf_route()
        
        issues = validator.validate(mdfe)
        
        val061_issues = [i for i in issues if i.code == "VAL061"]
        assert len(val061_issues) == 1, "Should have VAL061 warning"
        assert val061_issues[0].severity == "warning"
    
    def test_mdfe_invalid_plate_fails_val062(self):
        """MDFe with invalid vehicle plate should fail VAL062."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_mdfe_invalid_plate()
        
        issues = validator.validate(mdfe)
        
        val062_issues = [i for i in issues if i.code == "VAL062"]
        assert len(val062_issues) == 1, "Should have VAL062 warning"
        assert val062_issues[0].severity == "warning"
    
    def test_mdfe_zero_weight_fails_val063(self):
        """MDFe with zero weight should fail VAL063."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_mdfe_zero_weight()
        
        issues = validator.validate(mdfe)
        
        val063_issues = [i for i in issues if i.code == "VAL063"]
        assert len(val063_issues) == 1, "Should have VAL063 warning"
        assert val063_issues[0].severity == "warning"
    
    def test_mdfe_skips_item_validations(self):
        """MDFe should skip item-based validations (VAL005-VAL008)."""
        validator = FiscalValidatorTool(enable_api_validation=False)
        mdfe = create_valid_mdfe()
        
        issues = validator.validate(mdfe)
        
        # Should not have VAL005 error (items required)
        val005_issues = [i for i in issues if i.code == "VAL005"]
        assert len(val005_issues) == 0, "MDFe should skip VAL005 (items not required)"


class TestTransportValidatorHelpers:
    """Test transport validator helper functions."""
    
    def test_validate_modal(self):
        """Test modal validation."""
        from src.services.transport_validators import validate_modal
        
        assert validate_modal("01") == True  # Rodoviário
        assert validate_modal("02") == True  # Aéreo
        assert validate_modal("06") == True  # Multimodal
        assert validate_modal("99") == False  # Invalid
        assert validate_modal("") == True  # Skip if missing
    
    def test_validate_rntrc_format(self):
        """Test RNTRC format validation."""
        from src.services.transport_validators import validate_rntrc_format
        
        assert validate_rntrc_format("12345678") == True
        assert validate_rntrc_format("123") == False
        assert validate_rntrc_format("abcd1234") == False
        assert validate_rntrc_format("") == True  # Skip if missing
    
    def test_validate_vehicle_plate(self):
        """Test vehicle plate validation."""
        from src.services.transport_validators import validate_vehicle_plate
        
        # Old format
        assert validate_vehicle_plate("ABC1234") == True
        assert validate_vehicle_plate("abc1234") == True  # Case insensitive
        
        # Mercosul format
        assert validate_vehicle_plate("ABC1D23") == True
        assert validate_vehicle_plate("abc1d23") == True
        
        # Invalid
        assert validate_vehicle_plate("INVALID") == False
        assert validate_vehicle_plate("12345") == False
        assert validate_vehicle_plate("") == True  # Skip if missing
    
    def test_validate_cfop_for_transport(self):
        """Test CFOP validation for transport services."""
        from src.services.transport_validators import validate_cfop_for_transport
        
        # Valid transport CFOPs
        assert validate_cfop_for_transport("6352") == True
        assert validate_cfop_for_transport("5351") == True
        assert validate_cfop_for_transport("2351") == True
        
        # Invalid (product sale CFOP)
        assert validate_cfop_for_transport("5102") == False
        assert validate_cfop_for_transport("6101") == False
    
    def test_validate_uf_route(self):
        """Test UF route validation."""
        from src.services.transport_validators import validate_uf_route
        
        # Valid route
        assert validate_uf_route(["SP", "PR", "SC", "RS"]) == True
        
        # Duplicate UF
        assert validate_uf_route(["SP", "PR", "SP"]) == False
        
        # Invalid UF
        assert validate_uf_route(["SP", "XX", "RS"]) == False
        
        # Empty route (optional)
        assert validate_uf_route([]) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
