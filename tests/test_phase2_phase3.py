"""Test Phase 2 (parser enhancements) and Phase 3 (advanced validations)."""

from decimal import Decimal
from pathlib import Path

from src.tools.fiscal_validator import (
    FiscalValidatorTool,
    validate_cfop_uf_consistency,
    validate_icms_interstate_rate,
    validate_ncm_format,
    validate_tax_regime_cst_consistency,
)
from src.tools.xml_parser import XMLParserTool


def test_phase2_parser_enhancements():
    """Test that parser extracts new fields correctly."""
    print("=" * 60)
    print("PHASE 2: Parser Enhancements Test")
    print("=" * 60)
    
    parser = XMLParserTool()
    
    # Test with the 3 real XMLs
    xml_files = [
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/24240121172344000158550010000226611518005129.xml",
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/21240103526252000147558902430084471957013301.xml",
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/25240108761132000148558929001803761379847297.xml",
    ]
    
    for xml_file in xml_files:
        print(f"\n{'='*60}")
        print(f"Testing: {Path(xml_file).name}")
        print("=" * 60)
        
        with open(xml_file, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        invoice = parser.parse(xml_content)
        
        # Check new document-level fields
        print(f"\n📄 Document: {invoice.document_number}")
        print(f"   Issuer UF: {invoice.issuer_uf} ✅" if invoice.issuer_uf else "   Issuer UF: ❌ MISSING")
        print(f"   Recipient UF: {invoice.recipient_uf} ✅" if invoice.recipient_uf else "   Recipient UF: ❌ MISSING")
        print(f"   Tax Regime (CRT): {invoice.tax_regime} ✅" if invoice.tax_regime else "   Tax Regime: ❌ MISSING")
        print(f"   Discount: R$ {invoice.discount}")
        print(f"   Other Expenses: R$ {invoice.other_expenses}")
        
        # Check new item-level fields
        print(f"\n📦 Items ({len(invoice.items)}):")
        for item in invoice.items[:3]:  # Show first 3 items
            print(f"   Item {item.item_number}: {item.description[:30]}")
            print(f"      CFOP: {item.cfop}")
            print(f"      NCM: {item.ncm} ✅" if item.ncm else "      NCM: ❌ MISSING")
            print(f"      CST: {item.cst} ✅" if item.cst else "      CST: ❌ MISSING")
            print(f"      ICMS Origin: {item.icms_origin} ✅" if item.icms_origin else "      ICMS Origin: ❌ MISSING")
            print(f"      ICMS Rate: {item.icms_rate}% ✅" if item.icms_rate is not None else "      ICMS Rate: N/A")
            print(f"      ICMS Base: R$ {item.icms_base} ✅" if item.icms_base is not None else "      ICMS Base: N/A")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 2 TEST COMPLETE")
    print("=" * 60)


def test_phase3_validation_functions():
    """Test individual validation functions."""
    print("\n" + "=" * 60)
    print("PHASE 3: Validation Functions Test")
    print("=" * 60)
    
    # Test VAL018: Tax Regime × CST
    print("\n--- VAL018: Tax Regime × CST ---")
    test_cases_regime = [
        ("3", "00", True, "Normal regime + CST 00"),
        ("3", "40", True, "Normal regime + CST 40"),
        ("3", "101", False, "Normal regime + CSOSN 101 ❌"),
        ("1", "101", True, "Simples + CSOSN 101"),
        ("1", "00", False, "Simples + CST 00 ❌"),
    ]
    
    for crt, cst, expected, description in test_cases_regime:
        result = validate_tax_regime_cst_consistency(crt, cst)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {result}")
    
    # Test VAL021: NCM Format
    print("\n--- VAL021: NCM Format ---")
    test_cases_ncm = [
        ("07032090", True, "Valid 8-digit NCM"),
        ("10059090", True, "Valid 8-digit NCM"),
        ("0703209", False, "7 digits ❌"),
        ("070320901", False, "9 digits ❌"),
        ("ABC12345", False, "Non-numeric ❌"),
    ]
    
    for ncm, expected, description in test_cases_ncm:
        result = validate_ncm_format(ncm)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {result}")
    
    # Test VAL025: CFOP × UF
    print("\n--- VAL025: CFOP × UF ---")
    test_cases_cfop = [
        ("5102", "SP", "SP", True, "CFOP 5xxx same UF"),
        ("5102", "SP", "RJ", False, "CFOP 5xxx different UF ❌"),
        ("6101", "SP", "RJ", True, "CFOP 6xxx different UF"),
        ("6101", "SP", "SP", False, "CFOP 6xxx same UF ❌"),
        ("1102", "SP", "RJ", True, "CFOP 1xxx (entry) - no UF rule"),
    ]
    
    for cfop, uf_emit, uf_dest, expected, description in test_cases_cfop:
        result = validate_cfop_uf_consistency(cfop, uf_emit, uf_dest)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {result}")
    
    # Test VAL022: ICMS Interstate Rate
    print("\n--- VAL022: ICMS Interstate Rate ---")
    test_cases_icms = [
        ("SP", "RJ", Decimal("12"), True, "Interstate 12%"),
        ("SP", "RJ", Decimal("7"), True, "Interstate 7%"),
        ("SP", "RJ", Decimal("4"), True, "Interstate 4%"),
        ("SP", "SP", Decimal("18"), True, "Internal 18%"),
        ("SP", "RJ", Decimal("99"), True, "Unusual rate (accepted)"),
    ]
    
    for uf_emit, uf_dest, rate, expected, description in test_cases_icms:
        result = validate_icms_interstate_rate(uf_emit, uf_dest, rate)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {description}: {result}")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 3 VALIDATION FUNCTIONS TEST COMPLETE")
    print("=" * 60)


def test_phase3_full_validation():
    """Test full validation on real XMLs."""
    print("\n" + "=" * 60)
    print("PHASE 3: Full Validation on Real XMLs")
    print("=" * 60)
    
    parser = XMLParserTool()
    validator = FiscalValidatorTool()
    
    xml_files = [
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/24240121172344000158550010000226611518005129.xml",
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/21240103526252000147558902430084471957013301.xml",
        "/home/bmos/private/private_repos/i2a2/projeto_final/docs/mock/25240108761132000148558929001803761379847297.xml",
    ]
    
    for xml_file in xml_files:
        print(f"\n{'='*60}")
        print(f"Validating: {Path(xml_file).name}")
        print("=" * 60)
        
        with open(xml_file, "r", encoding="utf-8") as f:
            xml_content = f.read()
        
        invoice = parser.parse(xml_content)
        issues = validator.validate(invoice)
        
        # Filter for new validations (VAL018, VAL021, VAL022, VAL025)
        new_validations = [i for i in issues if i.code in ["VAL018", "VAL021", "VAL022", "VAL025"]]
        
        print(f"\n📊 Total issues: {len(issues)}")
        print(f"   New validations (VAL018/021/022/025): {len(new_validations)}")
        
        if new_validations:
            print("\n🆕 New Validation Results:")
            for issue in new_validations:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity]
                print(f"   {severity_icon} {issue.code}: {issue.message}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
        else:
            print("\n✅ All new validations passed!")
        
        # Show summary of all issues by code
        if issues:
            print("\n📋 All Issues Summary:")
            issue_counts = {}
            for issue in issues:
                issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1
            
            for code, count in sorted(issue_counts.items()):
                print(f"   {code}: {count}")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 3 FULL VALIDATION TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 PHASE 2 & 3 COMPREHENSIVE TESTS")
    print("=" * 60)
    
    # Phase 2: Parser enhancements
    test_phase2_parser_enhancements()
    
    # Phase 3: Validation functions
    test_phase3_validation_functions()
    
    # Phase 3: Full validation
    test_phase3_full_validation()
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETE!")
    print("=" * 60)
    print("\n✅ Implemented:")
    print("   - Phase 2: Parser extracts UF, CRT, CST, ICMS rate/base, discount, other_expenses")
    print("   - Phase 3: VAL018 (Tax Regime × CST)")
    print("   - Phase 3: VAL021 (NCM Format)")
    print("   - Phase 3: VAL022 (ICMS Interstate Rate)")
    print("   - Phase 3: VAL025 (CFOP × UF)")
    print()
