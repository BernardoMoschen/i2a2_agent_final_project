"""
Quick demo of XML parser and fiscal validator.

Run: python examples/demo_parser_validator.py
"""

from src.tools.fiscal_validator import FiscalValidatorTool
from src.tools.xml_parser import XMLParserTool

# Sample NFe XML (minimal valid structure)
SAMPLE_NFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35240112345678000190550010000000011234567890" versao="4.00">
      <ide>
        <cUF>35</cUF>
        <cNF>123456789</cNF>
        <natOp>VENDA</natOp>
        <mod>55</mod>
        <serie>1</serie>
        <nNF>1</nNF>
        <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
        <tpNF>1</tpNF>
        <idDest>1</idDest>
        <cMunFG>3550308</cMunFG>
        <tpImp>1</tpImp>
        <tpEmis>1</tpEmis>
        <tpAmb>2</tpAmb>
        <finNFe>1</finNFe>
        <indFinal>0</indFinal>
        <indPres>1</indPres>
        <procEmi>0</procEmi>
        <verProc>1.0</verProc>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>EMPRESA TESTE LTDA</xNome>
        <xFant>TESTE</xFant>
        <enderEmit>
          <xLgr>RUA TESTE</xLgr>
          <nro>123</nro>
          <xBairro>CENTRO</xBairro>
          <cMun>3550308</cMun>
          <xMun>SAO PAULO</xMun>
          <UF>SP</UF>
          <CEP>01000000</CEP>
        </enderEmit>
        <IE>123456789012</IE>
      </emit>
      <dest>
        <CNPJ>98765432000100</CNPJ>
        <xNome>CLIENTE TESTE SA</xNome>
        <enderDest>
          <xLgr>AV TESTE</xLgr>
          <nro>456</nro>
          <xBairro>JARDIM</xBairro>
          <cMun>3550308</cMun>
          <xMun>SAO PAULO</xMun>
          <UF>SP</UF>
          <CEP>02000000</CEP>
        </enderDest>
        <IE>987654321098</IE>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>PROD001</cProd>
          <cEAN></cEAN>
          <xProd>PRODUTO TESTE</xProd>
          <NCM>12345678</NCM>
          <CFOP>5102</CFOP>
          <uCom>UN</uCom>
          <qCom>10.00</qCom>
          <vUnCom>100.00</vUnCom>
          <vProd>1000.00</vProd>
          <cEANTrib></cEANTrib>
          <uTrib>UN</uTrib>
          <qTrib>10.00</qTrib>
          <vUnTrib>100.00</vUnTrib>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <orig>0</orig>
              <CST>00</CST>
              <modBC>0</modBC>
              <vBC>1000.00</vBC>
              <pICMS>18.00</pICMS>
              <vICMS>180.00</vICMS>
            </ICMS00>
          </ICMS>
          <IPI>
            <IPITrib>
              <CST>50</CST>
              <vBC>1000.00</vBC>
              <pIPI>10.00</pIPI>
              <vIPI>100.00</vIPI>
            </IPITrib>
          </IPI>
          <PIS>
            <PISAliq>
              <CST>01</CST>
              <vBC>1000.00</vBC>
              <pPIS>1.65</pPIS>
              <vPIS>16.50</vPIS>
            </PISAliq>
          </PIS>
          <COFINS>
            <COFINSAliq>
              <CST>01</CST>
              <vBC>1000.00</vBC>
              <pCOFINS>7.60</pCOFINS>
              <vCOFINS>76.00</vCOFINS>
            </COFINSAliq>
          </COFINS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>1000.00</vBC>
          <vICMS>180.00</vICMS>
          <vICMSDeson>0.00</vICMSDeson>
          <vFCP>0.00</vFCP>
          <vBCST>0.00</vBCST>
          <vST>0.00</vST>
          <vFCPST>0.00</vFCPST>
          <vFCPSTRet>0.00</vFCPSTRet>
          <vProd>1000.00</vProd>
          <vFrete>0.00</vFrete>
          <vSeg>0.00</vSeg>
          <vDesc>0.00</vDesc>
          <vII>0.00</vII>
          <vIPI>100.00</vIPI>
          <vIPIDevol>0.00</vIPIDevol>
          <vPIS>16.50</vPIS>
          <vCOFINS>76.00</vCOFINS>
          <vOutro>0.00</vOutro>
          <vNF>1100.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""


def main() -> None:
    """Run demo of parser and validator."""
    print("=" * 70)
    print("🚀 Fiscal Document Agent - Parser & Validator Demo")
    print("=" * 70)

    # 1. Parse XML
    print("\n📄 Step 1: Parsing NFe XML...")
    parser = XMLParserTool()
    invoice = parser.parse(SAMPLE_NFE_XML)

    print(f"✅ Successfully parsed {invoice.document_type}")
    print(f"   Document Key: {invoice.document_key}")
    print(f"   Number: {invoice.document_number} / Series: {invoice.series}")
    print(f"   Issue Date: {invoice.issue_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Issuer: {invoice.issuer_name} (CNPJ: {invoice.issuer_cnpj})")
    print(f"   Recipient: {invoice.recipient_name} (CNPJ: {invoice.recipient_cnpj_cpf})")

    print(f"\n💰 Financial Summary:")
    print(f"   Products Total: R$ {invoice.total_products:,.2f}")
    print(f"   Taxes Total: R$ {invoice.total_taxes:,.2f}")
    print(f"   Invoice Total: R$ {invoice.total_invoice:,.2f}")

    print(f"\n📦 Items ({len(invoice.items)}):")
    for item in invoice.items:
        print(
            f"   {item.item_number}. {item.description} "
            f"({item.quantity} {item.unit} × R$ {item.unit_price:,.2f} = "
            f"R$ {item.total_price:,.2f})"
        )
        print(
            f"      CFOP: {item.cfop}, NCM: {item.ncm}, "
            f"Taxes: ICMS={item.taxes.icms}, IPI={item.taxes.ipi}"
        )

    # 2. Validate
    print("\n" + "=" * 70)
    print("✔️  Step 2: Running Fiscal Validation...")
    validator = FiscalValidatorTool()
    issues = validator.validate(invoice)

    if not issues:
        print("✅ All validations passed! No issues found.")
    else:
        print(f"⚠️  Found {len(issues)} validation issue(s):\n")
        for issue in issues:
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
            print(f"{icon} [{issue.severity.upper()}] {issue.code}: {issue.message}")
            if issue.field:
                print(f"   Field: {issue.field}")
            if issue.suggestion:
                print(f"   Suggestion: {issue.suggestion}")
            print()

    # Summary
    print("=" * 70)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    print("📊 Validation Summary:")
    print(f"   ✅ Checks Passed: {10 - len(errors) - len(warnings)}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    print(f"   ❌ Errors: {len(errors)}")
    print(f"   ℹ️  Info: {len(infos)}")

    if errors:
        print("\n⛔ Document has ERRORS and should not be processed!")
    elif warnings:
        print("\n⚠️  Document has warnings but can be processed with caution.")
    else:
        print("\n✅ Document is valid and ready for processing!")

    print("=" * 70)
    print("🎉 Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
