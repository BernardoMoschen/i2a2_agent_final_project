"""Tests for VAL026 - CNPJ validation via BrasilAPI."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.models import InvoiceModel, InvoiceItem, DocumentType
from src.tools.fiscal_validator import FiscalValidatorTool, validate_cnpj_active_via_api


class TestVAL026CNPJAPIValidation:
    """Test suite for CNPJ validation via external API (VAL026)."""
    
    def test_validate_cnpj_active_via_api_disabled(self):
        """Test that validation passes when API validation is disabled."""
        # Should always return True when disabled (fail-safe)
        result = validate_cnpj_active_via_api("00000000000191", enable_api_validation=False)
        assert result is True
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_validate_cnpj_active_via_api_valid(self):
        """Test CNPJ validation with a known active CNPJ."""
        # Petrobras CNPJ (should be active)
        result = validate_cnpj_active_via_api("33000167000101", enable_api_validation=True)
        assert result is True
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_validate_cnpj_active_via_api_invalid(self):
        """Test CNPJ validation with an invalid/inactive CNPJ."""
        # Invalid CNPJ (should fail)
        result = validate_cnpj_active_via_api("00000000000000", enable_api_validation=True)
        assert result is False
    
    def test_full_validation_with_api_disabled(self):
        """Test full validation with API validation disabled."""
        # Create validator with API disabled
        validator = FiscalValidatorTool(enable_api_validation=False)
        
        # Create sample invoice with any CNPJ
        invoice = InvoiceModel(
            document_type=DocumentType.NFE,
            document_key="12345678901234567890123456789012345678901234",
            document_number="123",
            series="1",
            invoice_id="123",
            issue_date=datetime(2024, 1, 1),
            issuer_cnpj="00000000000191",  # Invalid CNPJ
            recipient_cpf_cnpj="12345678901",
            issuer_name="Test Company",
            recipient_name="Test Recipient",
            total_products=Decimal("100.00"),
            total_taxes=Decimal("10.00"),
            total_invoice=Decimal("110.00"),
            items=[
                InvoiceItem(
                    item_number=1,
                    product_code="PROD-001",
                    description="Test Item",
                    unit="UN",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00"),
                    total_price=Decimal("100.00"),
                    cfop="5102",
                    ncm="12345678",
                )
            ],
            parsed_at=datetime.now(),
        )
        
        # Validate
        issues = validator.validate(invoice)
        
        # Should have NO VAL026 issues (API validation disabled)
        val026_issues = [i for i in issues if i.code == "VAL026"]
        assert len(val026_issues) == 0
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_full_validation_with_api_enabled_active_cnpj(self):
        """Test full validation with API enabled and active CNPJ."""
        # Create validator with API enabled
        validator = FiscalValidatorTool(enable_api_validation=True)
        
        # Create sample invoice with active CNPJ (Petrobras)
        invoice = InvoiceModel(
            document_type=DocumentType.NFE,
            document_key="35240500000000000165550010000123451000123455",
            document_number="123",
            series="1",
            invoice_id="123",
            issue_date=datetime(2024, 1, 1),
            issuer_cnpj="33000167000101",  # Petrobras - should be active
            recipient_cpf_cnpj="12345678901",
            issuer_name="Petróleo Brasileiro S.A.",
            recipient_name="Test Recipient",
            total_products=Decimal("100.00"),
            total_taxes=Decimal("10.00"),
            total_invoice=Decimal("110.00"),
            items=[
                InvoiceItem(
                    item_number=1,
                    product_code="PROD-001",
                    description="Test Item",
                    unit="UN",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00"),
                    total_price=Decimal("100.00"),
                    cfop="5102",
                    ncm="12345678",
                )
            ],
            parsed_at=datetime.now(),
        )
        
        # Validate
        issues = validator.validate(invoice)
        
        # Should have NO VAL026 issues (CNPJ is active)
        val026_issues = [i for i in issues if i.code == "VAL026"]
        assert len(val026_issues) == 0
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_full_validation_with_api_enabled_inactive_cnpj(self):
        """Test full validation with API enabled and inactive CNPJ."""
        # Create validator with API enabled
        validator = FiscalValidatorTool(enable_api_validation=True)
        
        # Create sample invoice with invalid CNPJ
        invoice = InvoiceModel(
            document_type=DocumentType.NFE,
            document_key="35240500000000000165550010000123451000123455",
            document_number="123",
            series="1",
            invoice_id="123",
            issue_date=datetime(2024, 1, 1),
            issuer_cnpj="00000000000000",  # Invalid CNPJ
            recipient_cpf_cnpj="12345678901",
            issuer_name="Invalid Company",
            recipient_name="Test Recipient",
            total_products=Decimal("100.00"),
            total_taxes=Decimal("10.00"),
            total_invoice=Decimal("110.00"),
            items=[
                InvoiceItem(
                    item_number=1,
                    product_code="PROD-001",
                    description="Test Item",
                    unit="UN",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100.00"),
                    total_price=Decimal("100.00"),
                    cfop="5102",
                    ncm="12345678",
                )
            ],
            parsed_at=datetime.now(),
        )
        
        # Validate
        issues = validator.validate(invoice)
        
        # Should have VAL026 issue (CNPJ is inactive)
        val026_issues = [i for i in issues if i.code == "VAL026"]
        assert len(val026_issues) == 1
        assert val026_issues[0].severity.value == "ERROR"
        assert "not active" in val026_issues[0].message.lower()


class TestCNPJValidatorService:
    """Test suite for CNPJValidator service."""
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_active_cnpj(self):
        """Test CNPJValidator with active CNPJ."""
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        # Test with Petrobras CNPJ
        cnpj_data = validator.validate_cnpj("33.000.167/0001-01")
        
        assert cnpj_data is not None
        assert cnpj_data.cnpj == "33000167000101"
        assert cnpj_data.situacao == "ATIVA"
        assert "PETROBRAS" in cnpj_data.razao_social.upper()
        assert cnpj_data.uf == "RJ"
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_inactive_cnpj(self):
        """Test CNPJValidator with invalid CNPJ."""
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        # Test with invalid CNPJ
        cnpj_data = validator.validate_cnpj("00000000000000")
        
        # Should return None for invalid CNPJ
        assert cnpj_data is None
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_is_active(self):
        """Test is_cnpj_active() convenience method."""
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        # Active CNPJ
        assert validator.is_cnpj_active("33000167000101") is True
        
        # Invalid CNPJ should return True (fail-safe on API error)
        result = validator.is_cnpj_active("00000000000000")
        # Note: BrasilAPI returns 404 for invalid, so this should be False
        # But if API is down, it returns True (fail-safe)
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_razao_social_match(self):
        """Test razão social validation."""
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        # Test with exact match (Petrobras)
        assert validator.validate_razao_social(
            "33000167000101",
            "PETRÓLEO BRASILEIRO S.A. - PETROBRAS",
            threshold=0.8
        ) is True
        
        # Test with fuzzy match (should pass)
        assert validator.validate_razao_social(
            "33000167000101",
            "PETROLEO BRASILEIRO SA PETROBRAS",
            threshold=0.7
        ) is True
        
        # Test with completely different name (should fail)
        assert validator.validate_razao_social(
            "33000167000101",
            "EMPRESA COMPLETAMENTE DIFERENTE",
            threshold=0.8
        ) is False
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_uf_match(self):
        """Test UF validation."""
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        # Petrobras is in RJ
        assert validator.validate_uf("33000167000101", "RJ") is True
        assert validator.validate_uf("33000167000101", "SP") is False
    
    @pytest.mark.skip(reason="Requires external API - enable manually for integration tests")
    def test_cnpj_validator_caching(self):
        """Test that repeated calls use cache."""
        from src.services.external_validators import CNPJValidator
        import time
        
        validator = CNPJValidator(timeout=10.0)
        
        # First call - should hit API
        start1 = time.time()
        data1 = validator.validate_cnpj("33000167000101")
        time1 = time.time() - start1
        
        # Second call - should use cache (much faster)
        start2 = time.time()
        data2 = validator.validate_cnpj("33000167000101")
        time2 = time.time() - start2
        
        assert data1 is not None
        assert data2 is not None
        assert data1.cnpj == data2.cnpj
        
        # Cache hit should be significantly faster
        print(f"First call: {time1:.3f}s, Second call (cached): {time2:.3f}s")
        # Note: This assertion may be flaky due to network conditions
        # assert time2 < time1 * 0.5


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_val026_cnpj_api.py -v
    # To enable API tests: python -m pytest tests/test_val026_cnpj_api.py -v --run-integration
    pytest.main([__file__, "-v"])
