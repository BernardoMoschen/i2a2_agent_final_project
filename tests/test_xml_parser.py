"""Unit tests for XML parser tool."""

from decimal import Decimal

import pytest

from src.models import DocumentType, InvoiceModel
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


class TestXMLParserTool:
    """Test suite for XMLParserTool."""

    def test_parse_valid_nfe(self) -> None:
        """Test parsing a valid NFe XML."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_NFE_XML)

        assert isinstance(invoice, InvoiceModel)
        assert invoice.document_type == DocumentType.NFE
        assert invoice.document_key == "35240112345678000190550010000000011234567890"
        assert invoice.document_number == "1"
        assert invoice.series == "1"
        assert invoice.issuer_cnpj == "12345678000190"
        assert invoice.issuer_name == "EMPRESA TESTE LTDA"
        assert invoice.recipient_cnpj_cpf == "98765432000100"
        assert invoice.recipient_name == "CLIENTE TESTE SA"
        assert invoice.total_products == Decimal("1000.00")
        assert invoice.total_invoice == Decimal("1100.00")
        assert len(invoice.items) == 1

    def test_parse_nfe_item_details(self) -> None:
        """Test that item details are correctly parsed."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_NFE_XML)

        item = invoice.items[0]
        assert item.item_number == 1
        assert item.product_code == "PROD001"
        assert item.description == "PRODUTO TESTE"
        assert item.ncm == "12345678"
        assert item.cfop == "5102"
        assert item.unit == "UN"
        assert item.quantity == Decimal("10.00")
        assert item.unit_price == Decimal("100.00")
        assert item.total_price == Decimal("1000.00")
        assert item.taxes.icms == Decimal("180.00")
        assert item.taxes.ipi == Decimal("100.00")
        assert item.taxes.pis == Decimal("16.50")
        assert item.taxes.cofins == Decimal("76.00")

    def test_parse_nfe_tax_totals(self) -> None:
        """Test that tax totals are correctly calculated."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_NFE_XML)

        assert invoice.taxes.icms == Decimal("180.00")
        assert invoice.taxes.ipi == Decimal("100.00")
        assert invoice.taxes.pis == Decimal("16.50")
        assert invoice.taxes.cofins == Decimal("76.00")
        assert invoice.total_taxes == Decimal("372.50")  # Sum of all taxes

    def test_parse_malformed_xml(self) -> None:
        """Test that malformed XML raises ValueError."""
        parser = XMLParserTool()
        malformed_xml = "<invalid>xml without closing tag"

        with pytest.raises(ValueError, match="Malformed XML"):
            parser.parse(malformed_xml)

    def test_parse_missing_required_field(self) -> None:
        """Test that XML missing required fields raises ValueError."""
        parser = XMLParserTool()
        xml_missing_ide = """<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
          <NFe>
            <infNFe Id="NFe35240112345678000190550010000000011234567890" versao="4.00">
              <emit>
                <CNPJ>12345678000190</CNPJ>
                <xNome>EMPRESA TESTE LTDA</xNome>
              </emit>
            </infNFe>
          </NFe>
        </nfeProc>
        """

        with pytest.raises(ValueError, match="Missing ide element"):
            parser.parse(xml_missing_ide)

    def test_parse_unsupported_document_type(self) -> None:
        """Test that unsupported document types raise ValueError."""
        parser = XMLParserTool()
        # CTe and MDFe are not yet implemented
        cte_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <cteProc xmlns="http://www.portalfiscal.inf.br/cte">
          <CTe><infCte Id="CTe123"></infCte></CTe>
        </cteProc>
        """

        with pytest.raises(NotImplementedError, match="CTe parsing not yet implemented"):
            parser.parse(cte_xml)

    def test_decimal_parsing_with_commas(self) -> None:
        """Test that decimal values with commas are correctly parsed."""
        # This is implicitly tested in the validator, but we can add explicit tests
        # when we have edge-case XMLs with comma separators
        pass

    def test_nfce_detection(self) -> None:
        """Test that NFCe is correctly detected (model 65)."""
        # Modify SAMPLE_NFE_XML to have mod=65
        nfce_xml = SAMPLE_NFE_XML.replace("<mod>55</mod>", "<mod>65</mod>")
        parser = XMLParserTool()
        invoice = parser.parse(nfce_xml)

        assert invoice.document_type == DocumentType.NFCE
