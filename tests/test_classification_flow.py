"""Test script to validate complete classification flow."""

import logging
from pathlib import Path

from src.database.db import DatabaseManager
from src.utils.file_processing import FileProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test classification flow with sample XML."""
    
    # Sample NFe XML for testing (purchase operation, CFOP 1102)
    sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35240112345678000190550010000000011234567890" versao="4.00">
      <ide>
        <cUF>35</cUF>
        <cNF>123456789</cNF>
        <natOp>COMPRA PARA COMERCIALIZACAO</natOp>
        <mod>55</mod>
        <serie>1</serie>
        <nNF>1</nNF>
        <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
        <tpNF>0</tpNF>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>FORNECEDOR TESTE LTDA</xNome>
      </emit>
      <dest>
        <CNPJ>98765432000100</CNPJ>
        <xNome>EMPRESA TESTE LTDA</xNome>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>001</cProd>
          <xProd>PRODUTO TESTE</xProd>
          <NCM>84715000</NCM>
          <CFOP>1102</CFOP>
          <uCom>UN</uCom>
          <qCom>10.00</qCom>
          <vUnCom>100.00</vUnCom>
          <vProd>1000.00</vProd>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <orig>0</orig>
              <CST>00</CST>
              <vBC>1000.00</vBC>
              <pICMS>18.00</pICMS>
              <vICMS>180.00</vICMS>
            </ICMS00>
          </ICMS>
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
          <vProd>1000.00</vProd>
          <vNF>1000.00</vNF>
          <vPIS>16.50</vPIS>
          <vCOFINS>76.00</vCOFINS>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>"""
    
    # Initialize processor with classification enabled
    processor = FileProcessor(
        database_url="sqlite:///fiscal_documents.db",
        save_to_db=True,
        auto_classify=True
    )
    
    # Process the XML
    logger.info("Processing sample NFe XML with CFOP 1102 (purchase) and NCM 84715000 (TI equipment)")
    results = processor.process_file(sample_xml, "test_nfe.xml")
    
    if not results:
        logger.error("Processing failed!")
        return
    
    # Check results
    for result in results:
        filename, invoice, issues = result[0], result[1], result[2]
        classification = result[3] if len(result) > 3 else None
        
        logger.info(f"\n{'='*60}")
        logger.info(f"File: {filename}")
        logger.info(f"Document: {invoice.document_type} {invoice.document_number}")
        logger.info(f"Key: {invoice.document_key}")
        logger.info(f"Validation Issues: {len(issues)}")
        
        if classification:
            logger.info(f"\n🏷️ CLASSIFICATION:")
            logger.info(f"  Operation Type: {classification['operation_type']}")
            logger.info(f"  Cost Center: {classification['cost_center']}")
            logger.info(f"  Confidence: {classification['confidence']:.0%}")
            logger.info(f"  Reasoning: {classification['reasoning']}")
            logger.info(f"  Used LLM: {classification['used_llm_fallback']}")
        else:
            logger.warning("  ⚠️ No classification available")
        
        logger.info(f"{'='*60}\n")
    
    # Verify database
    db = DatabaseManager(database_url="sqlite:///fiscal_documents.db")
    invoices = db.search_invoices(limit=1)
    
    if invoices:
        inv = invoices[0]
        logger.info("\n✅ DATABASE VERIFICATION:")
        logger.info(f"  Document Key: {inv.document_key}")
        logger.info(f"  Operation Type: {inv.operation_type}")
        logger.info(f"  Cost Center: {inv.cost_center}")
        logger.info(f"  Confidence: {inv.classification_confidence:.0%}" if inv.classification_confidence else "  Confidence: N/A")
        logger.info(f"  Used LLM Fallback: {inv.used_llm_fallback}")
    
    logger.info("\n✅ TEST COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
