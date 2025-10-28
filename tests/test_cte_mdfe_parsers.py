"""Tests for CTe and MDFe XML parsers."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.models import DocumentType
from src.tools.xml_parser import XMLParserTool


# Sample CTe XML (minimal valid structure)
SAMPLE_CTE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<cteProc versao="3.00" xmlns="http://www.portalfiscal.inf.br/cte">
    <CTe>
        <infCte Id="CTe35240112345678901234567890123456789012" versao="3.00">
            <ide>
                <cUF>35</cUF>
                <cCT>12345678</cCT>
                <CFOP>6352</CFOP>
                <natOp>PRESTACAO DE SERVICO DE TRANSPORTE</natOp>
                <mod>57</mod>
                <serie>1</serie>
                <nCT>123456</nCT>
                <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <tpAmb>2</tpAmb>
            </ide>
            <emit>
                <CNPJ>12345678901234</CNPJ>
                <IE>123456789012</IE>
                <xNome>TRANSPORTADORA TESTE LTDA</xNome>
                <xFant>TRANSPORTADORA TESTE</xFant>
                <enderEmit>
                    <xLgr>RUA TESTE</xLgr>
                    <nro>100</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <CEP>01234567</CEP>
                    <UF>SP</UF>
                    <fone>1112345678</fone>
                </enderEmit>
            </emit>
            <rem>
                <CNPJ>98765432109876</CNPJ>
                <IE>987654321098</IE>
                <xNome>REMETENTE TESTE LTDA</xNome>
                <enderReme>
                    <xLgr>AV TESTE</xLgr>
                    <nro>200</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <CEP>01234000</CEP>
                    <UF>SP</UF>
                </enderReme>
            </rem>
            <dest>
                <CNPJ>11122233344455</CNPJ>
                <IE>111222333444</IE>
                <xNome>DESTINATARIO TESTE LTDA</xNome>
                <enderDest>
                    <xLgr>RUA DESTINO</xLgr>
                    <nro>300</nro>
                    <xBairro>VILA TESTE</xBairro>
                    <cMun>4314902</cMun>
                    <xMun>PORTO ALEGRE</xMun>
                    <CEP>90000000</CEP>
                    <UF>RS</UF>
                </enderDest>
            </dest>
            <vPrest>
                <vTPrest>1500.00</vTPrest>
                <vRec>1500.00</vRec>
                <Comp>
                    <xNome>FRETE PESO</xNome>
                    <vComp>1200.00</vComp>
                </Comp>
                <Comp>
                    <xNome>PEDAGIO</xNome>
                    <vComp>300.00</vComp>
                </Comp>
            </vPrest>
            <imp>
                <ICMS>
                    <ICMS00>
                        <CST>00</CST>
                        <vBC>1500.00</vBC>
                        <pICMS>12.00</pICMS>
                        <vICMS>180.00</vICMS>
                    </ICMS00>
                </ICMS>
            </imp>
        </infCte>
    </CTe>
</cteProc>
"""


# Sample MDFe XML (minimal valid structure)
SAMPLE_MDFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<mdfeProc versao="3.00" xmlns="http://www.portalfiscal.inf.br/mdfe">
    <MDFe>
        <infMDFe Id="MDFe35240112345678901234567890123456789012" versao="3.00">
            <ide>
                <cUF>35</cUF>
                <tpAmb>2</tpAmb>
                <tpEmit>1</tpEmit>
                <mod>58</mod>
                <serie>1</serie>
                <nMDF>987654</nMDF>
                <cMDF>12345678</cMDF>
                <dhEmi>2024-01-20T14:00:00-03:00</dhEmi>
                <tpEmis>1</tpEmis>
                <UFIni>SP</UFIni>
                <UFFim>RS</UFFim>
            </ide>
            <emit>
                <CNPJ>12345678901234</CNPJ>
                <IE>123456789012</IE>
                <xNome>TRANSPORTADORA MANIFESTO LTDA</xNome>
                <xFant>MANIFESTO TRANSPORT</xFant>
                <enderEmit>
                    <xLgr>RUA MANIFESTO</xLgr>
                    <nro>500</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <CEP>01234567</CEP>
                    <UF>SP</UF>
                </enderEmit>
            </emit>
            <infModal versaoModal="3.00">
                <rodo>
                    <infANTT>
                        <RNTRC>12345678</RNTRC>
                    </infANTT>
                </rodo>
            </infModal>
            <infDoc>
                <infMunDescarga>
                    <cMunDescarga>4314902</cMunDescarga>
                    <xMunDescarga>PORTO ALEGRE</xMunDescarga>
                </infMunDescarga>
            </infDoc>
            <infPercurso>
                <UFPer>PR</UFPer>
            </infPercurso>
            <infPercurso>
                <UFPer>SC</UFPer>
            </infPercurso>
            <infPercurso>
                <UFPer>RS</UFPer>
            </infPercurso>
        </infMDFe>
    </MDFe>
</mdfeProc>
"""


class TestCTeParser:
    """Test CTe XML parsing."""
    
    def test_parse_cte_basic_structure(self):
        """Test basic CTe parsing."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        
        assert invoice.document_type == DocumentType.CTE
        assert invoice.document_number == "123456"
        assert invoice.series == "1"
        assert invoice.document_key == "35240112345678901234567890123456789012"
    
    def test_parse_cte_dates(self):
        """Test CTe date parsing."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        
        assert isinstance(invoice.issue_date, datetime)
        assert invoice.issue_date.year == 2024
        assert invoice.issue_date.month == 1
        assert invoice.issue_date.day == 15
    
    def test_parse_cte_parties(self):
        """Test CTe party information."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        
        # Issuer (transport company)
        assert invoice.issuer_cnpj == "12345678901234"
        assert invoice.issuer_name == "TRANSPORTADORA TESTE LTDA"
        assert invoice.issuer_ie == "123456789012"
        assert invoice.issuer_uf == "SP"
        assert invoice.issuer_municipio == "SAO PAULO"
        assert invoice.issuer_cep == "01234567"
        
        # Recipient (destinatario)
        assert invoice.recipient_cnpj_cpf == "11122233344455"
        assert invoice.recipient_name == "DESTINATARIO TESTE LTDA"
        assert invoice.recipient_uf == "RS"
        assert invoice.recipient_municipio == "PORTO ALEGRE"
        assert invoice.recipient_cep == "90000000"
    
    def test_parse_cte_financial_totals(self):
        """Test CTe financial values."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        
        assert invoice.total_invoice == Decimal("1500.00")
        assert invoice.total_products == Decimal("1500.00")  # Transport service value
        assert invoice.total_taxes == Decimal("180.00")  # ICMS
        assert invoice.taxes.icms == Decimal("180.00")
    
    def test_parse_cte_no_items(self):
        """Test that CTe has no product items."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        
        assert invoice.items == []
        assert len(invoice.items) == 0


class TestMDFeParser:
    """Test MDFe XML parsing."""
    
    def test_parse_mdfe_basic_structure(self):
        """Test basic MDFe parsing."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        assert invoice.document_type == DocumentType.MDFE
        assert invoice.document_number == "987654"
        assert invoice.series == "1"
        assert invoice.document_key == "35240112345678901234567890123456789012"
    
    def test_parse_mdfe_dates(self):
        """Test MDFe date parsing."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        assert isinstance(invoice.issue_date, datetime)
        assert invoice.issue_date.year == 2024
        assert invoice.issue_date.month == 1
        assert invoice.issue_date.day == 20
    
    def test_parse_mdfe_issuer(self):
        """Test MDFe issuer information."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        assert invoice.issuer_cnpj == "12345678901234"
        assert invoice.issuer_name == "TRANSPORTADORA MANIFESTO LTDA"
        assert invoice.issuer_ie == "123456789012"
        assert invoice.issuer_uf == "SP"
        assert invoice.issuer_municipio == "SAO PAULO"
        assert invoice.issuer_cep == "01234567"
    
    def test_parse_mdfe_recipient(self):
        """Test MDFe recipient (first route UF)."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        # MDFe doesn't have traditional recipient, gets from route
        assert invoice.recipient_cnpj_cpf is None
        assert invoice.recipient_name is None
        assert invoice.recipient_uf == "PR"  # First infPercurso
    
    def test_parse_mdfe_zero_values(self):
        """Test that MDFe has zero monetary values."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        assert invoice.total_invoice == Decimal("0")
        assert invoice.total_products == Decimal("0")
        assert invoice.total_taxes == Decimal("0")
        assert invoice.taxes.icms == Decimal("0")
    
    def test_parse_mdfe_no_items(self):
        """Test that MDFe has no product items."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        
        assert invoice.items == []
        assert len(invoice.items) == 0


class TestDocumentTypeDetection:
    """Test automatic document type detection."""
    
    def test_detect_cte_from_xml(self):
        """Test CTe detection from XML tag."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_CTE_XML)
        assert invoice.document_type == DocumentType.CTE
    
    def test_detect_mdfe_from_xml(self):
        """Test MDFe detection from XML tag."""
        parser = XMLParserTool()
        invoice = parser.parse(SAMPLE_MDFE_XML)
        assert invoice.document_type == DocumentType.MDFE
    
    def test_invalid_xml_raises_error(self):
        """Test that invalid XML raises appropriate error."""
        parser = XMLParserTool()
        
        with pytest.raises(ValueError, match="Malformed XML"):
            parser.parse("not valid xml")
    
    def test_unsupported_document_type(self):
        """Test that unsupported document types raise error."""
        parser = XMLParserTool()
        
        # XML with unknown root tag
        invalid_xml = """<?xml version="1.0"?>
        <UnknownDoc>
            <test>data</test>
        </UnknownDoc>
        """
        
        with pytest.raises(ValueError, match="Unknown document type"):
            parser.parse(invalid_xml)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
