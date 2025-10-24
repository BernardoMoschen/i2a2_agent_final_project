"""
Demo prático das funcionalidades da Fase 2 & 3.

Este script demonstra:
1. Extração dos novos campos do XML (UF, CRT, CST, alíquotas)
2. Validações avançadas (VAL018, VAL021, VAL022, VAL025)
3. Uso prático em cenários reais

Executar:
    python examples/demo_phase2_phase3.py
"""

from decimal import Decimal
from pathlib import Path

from src.tools.fiscal_validator import FiscalValidatorTool
from src.tools.xml_parser import XMLParserTool


def demo_parser_enhancements():
    """Demonstra extração dos novos campos."""
    print("=" * 80)
    print("DEMO 1: Parser Enhancements - Novos Campos Extraídos")
    print("=" * 80)
    
    parser = XMLParserTool()
    
    # Exemplo com XML real
    xml_path = Path("docs/mock/24240121172344000158550010000226611518005129.xml")
    
    if not xml_path.exists():
        print(f"❌ Arquivo não encontrado: {xml_path}")
        return
    
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    
    invoice = parser.parse(xml_content)
    
    print(f"\n📄 Documento: NFe {invoice.document_number}")
    print(f"   Emitente: {invoice.issuer_name}")
    print(f"   Destinatário: {invoice.recipient_name}")
    
    print("\n🆕 NOVOS CAMPOS EXTRAÍDOS:")
    print(f"   📍 UF Emitente:    {invoice.issuer_uf}")
    print(f"   📍 UF Destinatário: {invoice.recipient_uf}")
    print(f"   🏢 Regime Tributário (CRT): {invoice.tax_regime} → {'Simples Nacional' if invoice.tax_regime == '1' else 'Regime Normal'}")
    print(f"   💰 Desconto Total: R$ {invoice.discount}")
    print(f"   💰 Outras Despesas: R$ {invoice.other_expenses}")
    
    print(f"\n📦 DETALHES DOS ITENS:")
    for item in invoice.items:
        print(f"\n   Item {item.item_number}: {item.description}")
        print(f"      🔢 NCM:           {item.ncm}")
        print(f"      📊 CFOP:          {item.cfop}")
        print(f"      🏷️  CST/CSOSN:     {item.cst}")
        print(f"      🌍 Origem:        {item.icms_origin} → {'Nacional' if item.icms_origin == '0' else 'Importada'}")
        if item.icms_rate:
            print(f"      📈 Alíquota ICMS: {item.icms_rate}%")
            print(f"      💵 Base ICMS:     R$ {item.icms_base}")
        else:
            print(f"      ℹ️  ICMS:          Isento/Não tributado")


def demo_validation_val018():
    """Demonstra VAL018 - Regime Tributário × CST."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: VAL018 - Validação Regime Tributário × CST/CSOSN")
    print("=" * 80)
    
    from src.tools.fiscal_validator import validate_tax_regime_cst_consistency
    
    print("\n✅ CASOS VÁLIDOS:")
    print("   • CRT=3 (Normal) + CST=00  →", validate_tax_regime_cst_consistency("3", "00"))
    print("   • CRT=3 (Normal) + CST=40  →", validate_tax_regime_cst_consistency("3", "40"))
    print("   • CRT=1 (Simples) + CSOSN=101 →", validate_tax_regime_cst_consistency("1", "101"))
    print("   • CRT=1 (Simples) + CSOSN=500 →", validate_tax_regime_cst_consistency("1", "500"))
    
    print("\n❌ CASOS INVÁLIDOS:")
    print("   • CRT=3 (Normal) + CSOSN=101 →", validate_tax_regime_cst_consistency("3", "101"), "← ERRO!")
    print("   • CRT=1 (Simples) + CST=00   →", validate_tax_regime_cst_consistency("1", "00"), "← ERRO!")
    
    print("\n💡 IMPORTÂNCIA:")
    print("   Usar CST quando deveria ser CSOSN (ou vice-versa) é erro fiscal grave")
    print("   que pode gerar autuação pela Receita Federal!")


def demo_validation_val025():
    """Demonstra VAL025 - CFOP × UF."""
    print("\n\n" + "=" * 80)
    print("DEMO 3: VAL025 - Validação CFOP × UF (Estado)")
    print("=" * 80)
    
    from src.tools.fiscal_validator import validate_cfop_uf_consistency
    
    print("\n✅ CASOS VÁLIDOS:")
    print("   • CFOP 5102 + SP→SP (mesma UF)   →", validate_cfop_uf_consistency("5102", "SP", "SP"))
    print("   • CFOP 6102 + SP→RJ (dif UF)     →", validate_cfop_uf_consistency("6102", "SP", "RJ"))
    print("   • CFOP 1102 + RJ→SP (entrada)    →", validate_cfop_uf_consistency("1102", "RJ", "SP"))
    
    print("\n❌ CASOS INVÁLIDOS:")
    print("   • CFOP 5102 + SP→RJ (dif UF)     →", validate_cfop_uf_consistency("5102", "SP", "RJ"), "← ERRO!")
    print("   • CFOP 6102 + SP→SP (mesma UF)   →", validate_cfop_uf_consistency("6102", "SP", "SP"), "← ERRO!")
    
    print("\n📚 REGRAS:")
    print("   CFOP 5xxx = Operação DENTRO do estado (mesma UF)")
    print("   CFOP 6xxx = Operação FORA do estado (UF diferente)")
    print("   CFOP 1xxx/2xxx = Entrada (sem regra UF específica)")


def demo_validation_val021():
    """Demonstra VAL021 - Formato NCM."""
    print("\n\n" + "=" * 80)
    print("DEMO 4: VAL021 - Validação Formato NCM")
    print("=" * 80)
    
    from src.tools.fiscal_validator import validate_ncm_format
    
    print("\n✅ NCMs VÁLIDOS:")
    print("   • 07032090 (Alho)        →", validate_ncm_format("07032090"))
    print("   • 10059090 (Milho)       →", validate_ncm_format("10059090"))
    print("   • 22030000 (Cerveja)     →", validate_ncm_format("22030000"))
    
    print("\n❌ NCMs INVÁLIDOS:")
    print("   • 0703209 (7 dígitos)    →", validate_ncm_format("0703209"), "← ERRO!")
    print("   • 070320901 (9 dígitos)  →", validate_ncm_format("070320901"), "← ERRO!")
    print("   • ABC12345 (não numérico) →", validate_ncm_format("ABC12345"), "← ERRO!")
    
    print("\n📖 ESTRUTURA NCM:")
    print("   Posição 1-6: Código SH (Sistema Harmonizado - internacional)")
    print("   Posição 7-8: Especificação TIPI (Brasil)")
    print("   Exemplo: 0703.20.90")
    print("            ││││ ││ ││")
    print("            ││││ ││ └└─ Item TIPI (Brasil)")
    print("            ││││ └└──── Subposição SH")
    print("            └└└└────── Capítulo + Posição SH")


def demo_full_validation():
    """Demonstra validação completa de um XML real."""
    print("\n\n" + "=" * 80)
    print("DEMO 5: Validação Completa de XML Real")
    print("=" * 80)
    
    parser = XMLParserTool()
    validator = FiscalValidatorTool()
    
    xml_path = Path("docs/mock/24240121172344000158550010000226611518005129.xml")
    
    if not xml_path.exists():
        print(f"❌ Arquivo não encontrado: {xml_path}")
        return
    
    with open(xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    
    # Parse
    invoice = parser.parse(xml_content)
    
    # Validate
    issues = validator.validate(invoice)
    
    print(f"\n📄 Documento: NFe {invoice.document_number}")
    print(f"   {invoice.issuer_name}")
    print(f"   UF: {invoice.issuer_uf} → {invoice.recipient_uf}")
    print(f"   CFOP: {invoice.items[0].cfop if invoice.items else 'N/A'}")
    print(f"   CRT: {invoice.tax_regime} | CST: {invoice.items[0].cst if invoice.items else 'N/A'}")
    
    print(f"\n📊 RESULTADO DA VALIDAÇÃO:")
    print(f"   Total de issues: {len(issues)}")
    
    # Filtrar novas validações
    new_validations = [i for i in issues if i.code in ["VAL018", "VAL021", "VAL022", "VAL025"]]
    
    if new_validations:
        print(f"\n⚠️  NOVAS VALIDAÇÕES (VAL018/021/022/025):")
        for issue in new_validations:
            severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity]
            print(f"   {severity_icon} {issue.code}: {issue.message}")
            if issue.suggestion:
                print(f"      💡 {issue.suggestion}")
    else:
        print(f"\n✅ Todas as novas validações (VAL018/021/022/025) passaram!")
    
    # Mostrar todas as issues
    if issues:
        print(f"\n📋 TODAS AS ISSUES:")
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        infos = [i for i in issues if i.severity == "info"]
        
        if errors:
            print(f"   ❌ ERRORS ({len(errors)}):")
            for issue in errors:
                print(f"      • {issue.code}: {issue.message}")
        
        if warnings:
            print(f"   ⚠️  WARNINGS ({len(warnings)}):")
            for issue in warnings:
                print(f"      • {issue.code}: {issue.message}")
        
        if infos:
            print(f"   ℹ️  INFOS ({len(infos)}):")
            for issue in infos:
                print(f"      • {issue.code}: {issue.message}")


def main():
    """Run all demos."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "🎯 DEMO FASE 2 & 3 - FUNCIONALIDADES" + " " * 20 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        demo_parser_enhancements()
        demo_validation_val018()
        demo_validation_val025()
        demo_validation_val021()
        demo_full_validation()
        
        print("\n\n" + "=" * 80)
        print("✅ DEMO COMPLETO!")
        print("=" * 80)
        
        print("\n📚 PRÓXIMOS PASSOS:")
        print("   1. Teste com seus próprios XMLs em docs/mock/")
        print("   2. Execute: streamlit run src/ui/app.py")
        print("   3. Faça upload de XMLs e veja as validações em ação!")
        print("   4. Use o agente (Chat tab) para consultar documentos")
        
    except Exception as e:
        print(f"\n❌ Erro durante demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
