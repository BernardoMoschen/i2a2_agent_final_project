"""Document archiving tool for organizing fiscal XMLs."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.database.db import DatabaseManager

logger = logging.getLogger(__name__)


class ArchiveInvoiceInput(BaseModel):
    """Input schema for archiver."""

    document_key: str = Field(
        ...,
        description="44-digit access key of the invoice to archive",
    )
    base_dir: str = Field(
        default="./archives",
        description="Base directory for archives (default: ./archives)",
    )


class ArchiverTool(BaseTool):
    """
    Archive fiscal document XMLs in organized folder structure.
    
    Creates structure: archives/{year}/{issuer_cnpj}/{document_type}/
    Includes metadata JSON file with document summary.
    """

    name: str = "archive_invoice"
    description: str = """
    Archive fiscal document XML in organized folder structure.
    
    Organizes XMLs by:
    - Year of emission
    - Issuer CNPJ
    - Document type (NFe, NFCe, CTe, etc.)
    
    Creates metadata JSON with document summary.
    
    Use this when user asks to:
    - "Arquivar este documento"
    - "Organizar XMLs processados"
    - "Guardar este XML de forma organizada"
    
    Input: 44-digit access key
    Output: Archive path and metadata
    """
    args_schema: type[BaseModel] = ArchiveInvoiceInput

    def _run(self, document_key: str, base_dir: str = "./archives") -> str:
        """Archive invoice XML and create metadata."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            # Find invoice by key
            invoices = db.search_invoices(limit=10000)
            invoice = next((inv for inv in invoices if inv.document_key == document_key), None)
            
            if not invoice:
                return f"❌ Documento com chave {document_key} não encontrado no banco de dados."
            
            if not invoice.raw_xml:
                return f"❌ XML original não encontrado para documento {document_key}."
            
            # Build archive path
            year = invoice.issue_date.strftime("%Y")
            issuer_cnpj = invoice.issuer_cnpj.replace(".", "").replace("/", "").replace("-", "")
            doc_type = invoice.document_type
            
            archive_path = Path(base_dir) / year / issuer_cnpj / doc_type
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename: {document_number}_{series}_{date}.xml
            date_str = invoice.issue_date.strftime("%Y%m%d")
            xml_filename = f"{invoice.document_number}_{invoice.series}_{date_str}.xml"
            xml_path = archive_path / xml_filename
            
            # Save XML
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(invoice.raw_xml)
            
            # Create metadata JSON
            metadata = {
                "document_key": invoice.document_key,
                "document_type": invoice.document_type,
                "document_number": invoice.document_number,
                "series": invoice.series,
                "issue_date": invoice.issue_date.isoformat(),
                "issuer_cnpj": invoice.issuer_cnpj,
                "issuer_name": invoice.issuer_name,
                "recipient_cnpj_cpf": invoice.recipient_cnpj_cpf,
                "recipient_name": invoice.recipient_name,
                "total_products": str(invoice.total_products),
                "total_taxes": str(invoice.total_taxes),
                "total_invoice": str(invoice.total_invoice),
                "operation_type": invoice.operation_type,
                "cost_center": invoice.cost_center,
                "archived_at": datetime.now().isoformat(),
                "xml_path": str(xml_path.absolute()),
            }
            
            metadata_filename = f"{invoice.document_number}_{invoice.series}_{date_str}_metadata.json"
            metadata_path = archive_path / metadata_filename
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Calculate archive stats
            archive_files = list(archive_path.glob("*.xml"))
            archive_count = len(archive_files)
            
            return f"""
✅ **Documento Arquivado com Sucesso**

📄 **Documento:** {invoice.document_type} - {invoice.document_number}/{invoice.series}
🏢 **Emitente:** {invoice.issuer_name}
📅 **Data de Emissão:** {invoice.issue_date.strftime('%d/%m/%Y')}

**Arquivamento:**
📁 Pasta: `{archive_path}`
📄 XML: `{xml_filename}`
📋 Metadata: `{metadata_filename}`

**Estrutura:**
```
{base_dir}/
└── {year}/
    └── {issuer_cnpj}/
        └── {doc_type}/
            ├── {xml_filename}
            └── {metadata_filename}
```

📊 **Estatísticas desta pasta:**
- Total de documentos arquivados: {archive_count}

✅ Documento organizado e pronto para consulta futura!
"""
        
        except Exception as e:
            logger.error(f"Error archiving invoice: {e}", exc_info=True)
            return f"❌ Erro ao arquivar documento: {str(e)}"

    async def _arun(self, document_key: str, base_dir: str = "./archives") -> str:
        """Async version."""
        return self._run(document_key, base_dir)


class ArchiveAllInvoicesInput(BaseModel):
    """Input schema for batch archiving."""

    days_back: int = Field(
        default=30,
        description="Archive documents from last N days (default: 30)",
    )
    base_dir: str = Field(
        default="./archives",
        description="Base directory for archives (default: ./archives)",
    )


class ArchiveAllTool(BaseTool):
    """
    Archive multiple fiscal documents in batch.
    
    Archives all documents from a specified time period.
    """

    name: str = "archive_all_invoices"
    description: str = """
    Archive multiple fiscal documents in batch mode.
    
    Use this when user asks to:
    - "Arquivar todos os documentos deste mês"
    - "Organizar todos os XMLs processados"
    - "Arquivar documentos dos últimos 30 dias"
    
    Input: Number of days to look back
    Output: Summary of archived documents
    """
    args_schema: type[BaseModel] = ArchiveAllInvoicesInput

    def _run(self, days_back: int = 30, base_dir: str = "./archives") -> str:
        """Archive multiple invoices in batch."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            # Get all invoices from period
            invoices = db.search_invoices(days_back=days_back, limit=10000)
            
            if not invoices:
                return f"📊 Nenhum documento encontrado nos últimos {days_back} dias."
            
            # Archive each invoice
            archived = 0
            failed = 0
            archiver = ArchiverTool()
            
            for invoice in invoices:
                if not invoice.raw_xml:
                    failed += 1
                    continue
                
                try:
                    # Build archive path
                    year = invoice.issue_date.strftime("%Y")
                    issuer_cnpj = invoice.issuer_cnpj.replace(".", "").replace("/", "").replace("-", "")
                    doc_type = invoice.document_type
                    
                    archive_path = Path(base_dir) / year / issuer_cnpj / doc_type
                    archive_path.mkdir(parents=True, exist_ok=True)
                    
                    # Generate filename
                    date_str = invoice.issue_date.strftime("%Y%m%d")
                    xml_filename = f"{invoice.document_number}_{invoice.series}_{date_str}.xml"
                    xml_path = archive_path / xml_filename
                    
                    # Save XML
                    with open(xml_path, "w", encoding="utf-8") as f:
                        f.write(invoice.raw_xml)
                    
                    # Create metadata
                    metadata = {
                        "document_key": invoice.document_key,
                        "document_type": invoice.document_type,
                        "document_number": invoice.document_number,
                        "series": invoice.series,
                        "issue_date": invoice.issue_date.isoformat(),
                        "issuer_cnpj": invoice.issuer_cnpj,
                        "issuer_name": invoice.issuer_name,
                        "total_invoice": str(invoice.total_invoice),
                        "archived_at": datetime.now().isoformat(),
                    }
                    
                    metadata_filename = f"{invoice.document_number}_{invoice.series}_{date_str}_metadata.json"
                    metadata_path = archive_path / metadata_filename
                    
                    with open(metadata_path, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    
                    archived += 1
                    
                except Exception as e:
                    logger.error(f"Failed to archive {invoice.document_key}: {e}")
                    failed += 1
            
            return f"""
✅ **Arquivamento em Lote Concluído**

📊 **Resumo:**
- 📄 Documentos processados: {len(invoices)}
- ✅ Arquivados com sucesso: {archived}
- ❌ Falhas: {failed}

📁 **Diretório base:** `{base_dir}`

**Estrutura criada:**
```
{base_dir}/
└── [ano]/
    └── [cnpj_fornecedor]/
        └── [tipo_documento]/
            ├── [documento].xml
            └── [documento]_metadata.json
```

💡 **Dica:** Use `ls -R {base_dir}` para ver toda a estrutura de arquivos.
"""
        
        except Exception as e:
            logger.error(f"Error in batch archiving: {e}", exc_info=True)
            return f"❌ Erro ao arquivar documentos em lote: {str(e)}"

    async def _arun(self, days_back: int = 30, base_dir: str = "./archives") -> str:
        """Async version."""
        return self._run(days_back, base_dir)


# Tool instances
archiver_tool = ArchiverTool()
archive_all_tool = ArchiveAllTool()

# Export
ALL_ARCHIVER_TOOLS = [archiver_tool, archive_all_tool]
