#!/usr/bin/env python3
"""
Demonstration script for VAL026 - CNPJ validation via BrasilAPI.

This script shows:
1. How to enable/disable API validation
2. How to validate CNPJ status (active/inactive)
3. How to validate razão social and UF matching
4. How to use the CNPJValidator service directly
5. Full integration with FiscalValidatorTool

Run with:
    python examples/demo_val026_cnpj_api.py
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import InvoiceModel, InvoiceItem, DocumentType
from src.tools.fiscal_validator import FiscalValidatorTool, validate_cnpj_active_via_api


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def demo_basic_api_validation():
    """Demo 1: Basic CNPJ API validation."""
    print_section("DEMO 1: Basic CNPJ API Validation")
    
    print("\n1. Validating active CNPJ (Petrobras)...")
    result = validate_cnpj_active_via_api("33.000.167/0001-01", enable_api_validation=True)
    print(f"   CNPJ: 33.000.167/0001-01")
    print(f"   Result: {'✅ Active' if result else '❌ Inactive'}")
    
    print("\n2. Validating with API disabled (fail-safe mode)...")
    result = validate_cnpj_active_via_api("00.000.000/0000-00", enable_api_validation=False)
    print(f"   CNPJ: 00.000.000/0000-00")
    print(f"   Result: {'✅ Passes (fail-safe)' if result else '❌ Fails'}")
    print(f"   Note: API validation disabled - always returns True (fail-safe)")


def demo_cnpj_validator_service():
    """Demo 2: Using CNPJValidator service directly."""
    print_section("DEMO 2: CNPJValidator Service")
    
    try:
        from src.services.external_validators import CNPJValidator
        
        validator = CNPJValidator(timeout=10.0)
        
        print("\n1. Fetching CNPJ data from BrasilAPI...")
        cnpj_data = validator.validate_cnpj("33000167000101")
        
        if cnpj_data:
            print(f"\n   ✅ CNPJ Data Retrieved:")
            print(f"   CNPJ: {cnpj_data.cnpj}")
            print(f"   Razão Social: {cnpj_data.razao_social}")
            print(f"   Nome Fantasia: {cnpj_data.nome_fantasia or 'N/A'}")
            print(f"   Situação: {cnpj_data.situacao}")
            print(f"   UF: {cnpj_data.uf}")
            print(f"   Município: {cnpj_data.municipio}")
            print(f"   CNAE: {cnpj_data.cnae_fiscal} - {cnpj_data.cnae_fiscal_descricao}")
            print(f"   Porte: {cnpj_data.porte}")
            print(f"   Capital Social: R$ {cnpj_data.capital_social:,.2f}")
            print(f"   Data Abertura: {cnpj_data.data_abertura}")
            
            if cnpj_data.simples_nacional is not None:
                print(f"   Simples Nacional: {'Sim' if cnpj_data.simples_nacional else 'Não'}")
            if cnpj_data.mei is not None:
                print(f"   MEI: {'Sim' if cnpj_data.mei else 'Não'}")
        else:
            print("   ❌ CNPJ not found or API error")
        
        print("\n2. Testing is_cnpj_active() convenience method...")
        is_active = validator.is_cnpj_active("33000167000101")
        print(f"   CNPJ 33.000.167/0001-01 is active: {'✅ Yes' if is_active else '❌ No'}")
        
        print("\n3. Testing razão social validation...")
        matches = validator.validate_razao_social(
            "33000167000101",
            "PETRÓLEO BRASILEIRO S.A. - PETROBRAS",
            threshold=0.8
        )
        print(f"   Declared: PETRÓLEO BRASILEIRO S.A. - PETROBRAS")
        print(f"   Matches API: {'✅ Yes' if matches else '❌ No'}")
        
        print("\n4. Testing UF validation...")
        uf_matches = validator.validate_uf("33000167000101", "RJ")
        print(f"   Declared UF: RJ")
        print(f"   Matches API: {'✅ Yes' if uf_matches else '❌ No'}")
        
        uf_wrong = validator.validate_uf("33000167000101", "SP")
        print(f"   Declared UF: SP")
        print(f"   Matches API: {'✅ Yes' if uf_wrong else '❌ No (Expected: RJ)'}")
        
    except ImportError:
        print("\n   ⚠️  CNPJValidator service not available")
        print("   Install httpx: pip install httpx>=0.25.0")
    except Exception as e:
        print(f"\n   ❌ Error: {e}")


def demo_full_validation_api_disabled():
    """Demo 3: Full validation with API disabled."""
    print_section("DEMO 3: Full Validation with API Disabled (Fail-Safe Mode)")
    
    # Create validator with API disabled
    validator = FiscalValidatorTool(enable_api_validation=False)
    
    print("\n1. Creating invoice with potentially invalid CNPJ...")
    invoice = InvoiceModel(
        document_type=DocumentType.NFE,
        document_key="35240500000000000165550010000123451000123455",
        document_number="NFe-123",
        series="1",
        invoice_id="NFe-123",
        issue_date=datetime(2024, 1, 1),
        issuer_cnpj="00.000.000/0000-00",  # Invalid CNPJ
        recipient_cpf_cnpj="123.456.789-01",
        issuer_name="Invalid Company",
        recipient_name="Test Recipient",
        total_products=Decimal("100.00"),
        total_taxes=Decimal("10.00"),
        total_invoice=Decimal("110.00"),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD-001",
                description="Test Product",
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
    
    print(f"   CNPJ: {invoice.issuer_cnpj}")
    print(f"   Issuer: {invoice.issuer_name}")
    
    print("\n2. Running validation (API disabled)...")
    issues = validator.validate(invoice)
    
    val026_issues = [i for i in issues if i.code == "VAL026"]
    
    print(f"\n   Total issues: {len(issues)}")
    print(f"   VAL026 issues: {len(val026_issues)}")
    
    if val026_issues:
        print("\n   VAL026 Issues:")
        for issue in val026_issues:
            print(f"   - [{issue.severity.value}] {issue.message}")
    else:
        print("\n   ✅ No VAL026 issues (API validation disabled - fail-safe mode)")


def demo_full_validation_api_enabled():
    """Demo 4: Full validation with API enabled."""
    print_section("DEMO 4: Full Validation with API Enabled (Active CNPJ)")
    
    # Create validator with API enabled
    validator = FiscalValidatorTool(enable_api_validation=True)
    
    print("\n1. Creating invoice with active CNPJ (Petrobras)...")
    invoice = InvoiceModel(
        document_type=DocumentType.NFE,
        document_key="35240500000000000165550010000123451000123455",
        document_number="NFe-456",
        series="1",
        invoice_id="NFe-456",
        issue_date=datetime(2024, 1, 1),
        issuer_cnpj="33.000.167/0001-01",  # Petrobras - active
        recipient_cpf_cnpj="123.456.789-01",
        issuer_name="Petróleo Brasileiro S.A.",
        recipient_name="Test Recipient",
        total_products=Decimal("100.00"),
        total_taxes=Decimal("10.00"),
        total_invoice=Decimal("110.00"),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD-001",
                description="Test Product",
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
    
    print(f"   CNPJ: {invoice.issuer_cnpj}")
    print(f"   Issuer: {invoice.issuer_name}")
    
    print("\n2. Running validation (API enabled)...")
    try:
        issues = validator.validate(invoice)
        
        val026_issues = [i for i in issues if i.code == "VAL026"]
        
        print(f"\n   Total issues: {len(issues)}")
        print(f"   VAL026 issues: {len(val026_issues)}")
        
        if val026_issues:
            print("\n   VAL026 Issues:")
            for issue in val026_issues:
                print(f"   - [{issue.severity.value}] {issue.message}")
        else:
            print("\n   ✅ No VAL026 issues (CNPJ is active)")
        
        # Show other issues (if any)
        other_issues = [i for i in issues if i.code != "VAL026"]
        if other_issues:
            print(f"\n   Other validation issues: {len(other_issues)}")
            for issue in other_issues[:5]:  # Show first 5
                print(f"   - [{issue.code}] {issue.message}")
    
    except Exception as e:
        print(f"\n   ⚠️  API validation failed: {e}")
        print("   (This is expected if BrasilAPI is down or rate-limited)")


def demo_full_validation_inactive_cnpj():
    """Demo 5: Full validation with inactive CNPJ."""
    print_section("DEMO 5: Full Validation with Inactive/Invalid CNPJ")
    
    # Create validator with API enabled
    validator = FiscalValidatorTool(enable_api_validation=True)
    
    print("\n1. Creating invoice with invalid CNPJ...")
    invoice = InvoiceModel(
        document_type=DocumentType.NFE,
        document_key="35240500000000000165550010000123451000123455",
        document_number="NFe-789",
        series="1",
        invoice_id="NFe-789",
        issue_date=datetime(2024, 1, 1),
        issuer_cnpj="00.000.000/0000-00",  # Invalid CNPJ
        recipient_cpf_cnpj="123.456.789-01",
        issuer_name="Invalid Company",
        recipient_name="Test Recipient",
        total_products=Decimal("100.00"),
        total_taxes=Decimal("10.00"),
        total_invoice=Decimal("110.00"),
        items=[
            InvoiceItem(
                item_number=1,
                product_code="PROD-001",
                description="Test Product",
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
    
    print(f"   CNPJ: {invoice.issuer_cnpj}")
    print(f"   Issuer: {invoice.issuer_name}")
    
    print("\n2. Running validation (API enabled)...")
    try:
        issues = validator.validate(invoice)
        
        val026_issues = [i for i in issues if i.code == "VAL026"]
        
        print(f"\n   Total issues: {len(issues)}")
        print(f"   VAL026 issues: {len(val026_issues)}")
        
        if val026_issues:
            print("\n   ❌ VAL026 Issues Found:")
            for issue in val026_issues:
                print(f"   - [{issue.severity.value}] {issue.message}")
                if issue.suggestion:
                    print(f"     Suggestion: {issue.suggestion}")
        else:
            print("\n   No VAL026 issues")
        
    except Exception as e:
        print(f"\n   ⚠️  API validation failed: {e}")
        print("   (This is expected if BrasilAPI is down or rate-limited)")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  VAL026 - CNPJ Validation via BrasilAPI - Demo Suite")
    print("=" * 80)
    print("\n  This demo shows how to use external API validation for CNPJ verification.")
    print("  Note: Some demos require internet connection and BrasilAPI availability.")
    print("\n  Features:")
    print("  - Validate CNPJ status (active/inactive)")
    print("  - Fetch complete CNPJ data (razão social, UF, município, CNAE, etc.)")
    print("  - Fail-safe mode (skip API if disabled or if API fails)")
    print("  - Integration with FiscalValidatorTool")
    
    try:
        # Demo 1: Basic API validation
        demo_basic_api_validation()
        
        # Demo 2: CNPJValidator service
        demo_cnpj_validator_service()
        
        # Demo 3: Full validation with API disabled
        demo_full_validation_api_disabled()
        
        # Demo 4: Full validation with API enabled (active CNPJ)
        demo_full_validation_api_enabled()
        
        # Demo 5: Full validation with inactive CNPJ
        demo_full_validation_inactive_cnpj()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error running demos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("=" * 80)
    print("\n  Key Takeaways:")
    print("  1. VAL026 validates CNPJ status via BrasilAPI (free, no rate limits)")
    print("  2. Fail-safe mode: API errors don't block processing")
    print("  3. Can be enabled/disabled per validator instance")
    print("  4. Provides rich CNPJ data for additional validations")
    print("  5. Caches results for 24 hours to reduce API calls")
    print("\n  Next Steps:")
    print("  - Enable API validation in production: FiscalValidatorTool(enable_api_validation=True)")
    print("  - Add more API validations: CEP (ViaCEP), NCM (IBGE), SEFAZ status")
    print("  - Cross-validate CNPJ data with invoice fields (razão social, UF, etc.)")
    print()


if __name__ == "__main__":
    main()
