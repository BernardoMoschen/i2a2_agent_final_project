"""End-to-end integration test for CTe/MDFe support."""

import pytest
from pathlib import Path

from src.utils.file_processing import FileProcessor
from src.models import DocumentType


# Use sample XMLs from test_cte_mdfe_parsers
from tests.test_cte_mdfe_parsers import SAMPLE_CTE_XML, SAMPLE_MDFE_XML


class TestCTeMDFeIntegration:
    """Test complete CTe/MDFe processing pipeline."""
    
    def setup_method(self):
        """Setup test processor (no database for tests)."""
        self.processor = FileProcessor(
            database_url="sqlite:///:memory:",
            save_to_db=False,  # Don't persist during tests
            auto_classify=False  # Skip classification for tests
        )
    
    def test_process_cte_file_complete_flow(self):
        """Test complete CTe processing: parse → validate → return."""
        # Process CTe XML
        results = self.processor.process_file(
            SAMPLE_CTE_XML.encode('utf-8'),
            "sample_cte.xml"
        )
        
        assert len(results) == 1
        filename, invoice, issues, classification = results[0]
        
        # Verify parsing
        assert filename == "sample_cte.xml"
        assert invoice.document_type == DocumentType.CTE
        assert invoice.document_number == "123456"
        
        # Verify validation ran (issues may or may not exist)
        assert isinstance(issues, list)
        
        # Verify classification was skipped
        assert classification is None
    
    def test_process_mdfe_file_complete_flow(self):
        """Test complete MDFe processing: parse → validate → return."""
        # Process MDFe XML
        results = self.processor.process_file(
            SAMPLE_MDFE_XML.encode('utf-8'),
            "sample_mdfe.xml"
        )
        
        assert len(results) == 1
        filename, invoice, issues, classification = results[0]
        
        # Verify parsing
        assert filename == "sample_mdfe.xml"
        assert invoice.document_type == DocumentType.MDFE
        assert invoice.document_number == "987654"
        
        # Verify validation ran
        assert isinstance(issues, list)
        
        # Verify classification was skipped
        assert classification is None
    
    def test_process_zip_with_mixed_documents(self):
        """Test ZIP containing NFe, CTe, and MDFe together."""
        import zipfile
        from io import BytesIO
        
        # Create a ZIP with multiple document types
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("cte_001.xml", SAMPLE_CTE_XML)
            zf.writestr("mdfe_001.xml", SAMPLE_MDFE_XML)
        
        zip_content = zip_buffer.getvalue()
        
        # Process ZIP
        results = self.processor.process_file(zip_content, "mixed_documents.zip")
        
        # Should have 2 results (CTe + MDFe)
        assert len(results) == 2
        
        # Extract document types
        doc_types = [invoice.document_type for _, invoice, _, _ in results]
        
        # Verify both types present
        assert DocumentType.CTE in doc_types
        assert DocumentType.MDFE in doc_types
    
    def test_cte_validation_checks(self):
        """Test that CTe goes through fiscal validation."""
        results = self.processor.process_file(
            SAMPLE_CTE_XML.encode('utf-8'),
            "cte_validation_test.xml"
        )
        
        _, invoice, issues, _ = results[0]
        
        # Validation should check:
        # - Document key (should be present)
        # - Totals consistency
        # - Date validity
        # - Party information
        
        # Check that validation was executed (may pass or have warnings)
        assert isinstance(issues, list)
        
        # Key should be valid (at least present and reasonable length)
        assert len(invoice.document_key) > 0
        assert invoice.document_type == DocumentType.CTE
    
    def test_mdfe_validation_handles_zero_values(self):
        """Test that MDFe with zero monetary values validates correctly."""
        results = self.processor.process_file(
            SAMPLE_MDFE_XML.encode('utf-8'),
            "mdfe_zero_values.xml"
        )
        
        _, invoice, issues, _ = results[0]
        
        # MDFe should have zero values
        assert invoice.total_invoice == 0
        assert invoice.total_products == 0
        assert invoice.total_taxes == 0
        
        # Validation may have errors from test data (fake CNPJs, IEs, etc)
        # but should successfully parse the MDFe structure
        assert invoice.document_type == DocumentType.MDFE
    
    def test_cte_transport_service_value_mapping(self):
        """Test that CTe transport service value maps correctly."""
        results = self.processor.process_file(
            SAMPLE_CTE_XML.encode('utf-8'),
            "cte_service_value.xml"
        )
        
        _, invoice, _, _ = results[0]
        
        # For CTe, total_products should equal transport service value
        assert invoice.total_products == invoice.total_invoice
        assert invoice.total_products > 0  # Should have service value
        
        # Items should be empty (transport has no product items)
        assert len(invoice.items) == 0
    
    def test_error_handling_invalid_cte(self):
        """Test error handling for malformed CTe."""
        invalid_cte = """<?xml version="1.0"?>
        <cteProc>
            <CTe>
                <infCte Id="CTe12345">
                    <!-- Missing required fields -->
                </infCte>
            </CTe>
        </cteProc>
        """
        
        # FileProcessor catches exceptions and returns empty results
        results = self.processor.process_file(
            invalid_cte.encode('utf-8'),
            "invalid_cte.xml"
        )
        
        # Should return empty results (error caught internally)
        assert len(results) == 0
    
    def test_file_processor_with_database_integration(self):
        """Test CTe/MDFe with database persistence enabled."""
        # Create processor with database
        db_processor = FileProcessor(
            database_url="sqlite:///:memory:",
            save_to_db=True,
            auto_classify=False
        )
        
        # Process CTe
        results = db_processor.process_file(
            SAMPLE_CTE_XML.encode('utf-8'),
            "cte_db_test.xml"
        )
        
        assert len(results) == 1
        _, invoice, _, _ = results[0]
        
        # Verify saved to database
        from src.database.db import DatabaseManager
        db = db_processor.db
        
        # Query back from database (use correct method name)
        saved_invoices = db.get_all_invoices()
        
        # Should have 1 invoice
        assert len(saved_invoices) >= 1
        
        # Find our CTe
        cte_invoices = [i for i in saved_invoices if i.document_type == "CTe"]
        assert len(cte_invoices) >= 1
        
        # Verify data persisted correctly
        saved_cte = cte_invoices[0]
        assert saved_cte.document_number == invoice.document_number
        assert saved_cte.issuer_cnpj == invoice.issuer_cnpj


class TestCTeMDFeFileUploadSimulation:
    """Simulate file upload scenarios for CTe/MDFe."""
    
    def test_upload_single_cte_xml(self):
        """Simulate uploading a single CTe XML file."""
        processor = FileProcessor(save_to_db=False, auto_classify=False)
        
        # Simulate file upload
        file_content = SAMPLE_CTE_XML.encode('utf-8')
        filename = "uploaded_cte.xml"
        
        results = processor.process_file(file_content, filename)
        
        assert len(results) == 1
        assert results[0][1].document_type == DocumentType.CTE
    
    def test_upload_zip_with_multiple_ctes(self):
        """Simulate uploading ZIP with multiple CTe files."""
        import zipfile
        from io import BytesIO
        
        processor = FileProcessor(save_to_db=False, auto_classify=False)
        
        # Create ZIP with 3 CTe files
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for i in range(3):
                zf.writestr(f"cte_00{i+1}.xml", SAMPLE_CTE_XML)
        
        results = processor.process_file(
            zip_buffer.getvalue(),
            "multiple_ctes.zip"
        )
        
        # Should process all 3 CTes
        assert len(results) == 3
        assert all(inv.document_type == DocumentType.CTE for _, inv, _, _ in results)
    
    def test_upload_mixed_nfe_cte_mdfe_zip(self):
        """Simulate real-world scenario: ZIP with mixed document types."""
        import zipfile
        from io import BytesIO
        
        processor = FileProcessor(save_to_db=False, auto_classify=False)
        
        # Sample NFe (minimal)
        sample_nfe = """<?xml version="1.0"?>
        <nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe Id="NFe35240112345678901234567890123456789012345" versao="4.00">
                    <ide>
                        <cUF>35</cUF>
                        <nNF>12345</nNF>
                        <serie>1</serie>
                        <dhEmi>2024-01-15T10:00:00-03:00</dhEmi>
                        <mod>55</mod>
                    </ide>
                    <emit>
                        <CNPJ>12345678901234</CNPJ>
                        <xNome>EMPRESA TESTE</xNome>
                        <CRT>1</CRT>
                    </emit>
                    <total>
                        <ICMSTot>
                            <vProd>100.00</vProd>
                            <vNF>100.00</vNF>
                            <vICMS>0</vICMS>
                            <vIPI>0</vIPI>
                            <vPIS>0</vPIS>
                            <vCOFINS>0</vCOFINS>
                        </ICMSTot>
                    </total>
                </infNFe>
            </NFe>
        </nfeProc>
        """
        
        # Create mixed ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("nfe_001.xml", sample_nfe)
            zf.writestr("cte_001.xml", SAMPLE_CTE_XML)
            zf.writestr("mdfe_001.xml", SAMPLE_MDFE_XML)
        
        results = processor.process_file(
            zip_buffer.getvalue(),
            "mixed_fiscal_docs.zip"
        )
        
        # Should process all 3 documents
        assert len(results) == 3
        
        # Verify all types present
        doc_types = {inv.document_type for _, inv, _, _ in results}
        assert DocumentType.NFE in doc_types
        assert DocumentType.CTE in doc_types
        assert DocumentType.MDFE in doc_types


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
