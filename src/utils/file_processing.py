"""File processing utilities for uploaded fiscal documents."""

import logging
import zipfile
from io import BytesIO
from typing import List, Optional, Tuple

from src.database.db import DatabaseManager
from src.models import InvoiceModel
from src.services.classifier import DocumentClassifier
from src.tools.fiscal_validator import FiscalValidatorTool
from src.tools.xml_parser import XMLParserTool

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process uploaded XML and ZIP files."""

    def __init__(self, database_url: str = "sqlite:///fiscal_documents.db", save_to_db: bool = True, auto_classify: bool = True):
        """
        Initialize processor with parser, validator, and classifier.
        
        Args:
            database_url: SQLite database URL
            save_to_db: Whether to automatically save to database (default: True)
            auto_classify: Whether to automatically classify documents (default: True)
        """
        self.parser = XMLParserTool()
        self.validator = FiscalValidatorTool()
        self.classifier = DocumentClassifier() if auto_classify else None
        self.save_to_db = save_to_db
        self.auto_classify = auto_classify
        
        if save_to_db:
            self.db = DatabaseManager(database_url)
            logger.info("FileProcessor initialized with database integration")
        
        if auto_classify:
            logger.info("FileProcessor initialized with automatic classification enabled")

    def process_file(self, file_content: bytes, filename: str) -> List[Tuple[str, InvoiceModel, List]]:
        """
        Process uploaded file (XML or ZIP).

        Args:
            file_content: Raw file bytes
            filename: Name of the uploaded file

        Returns:
            List of tuples: (filename, invoice, validation_issues)
        """
        results = []

        if filename.lower().endswith(".zip"):
            results.extend(self._process_zip(file_content))
        elif filename.lower().endswith(".xml"):
            result = self._process_xml(file_content, filename)
            if result:
                results.append(result)
        else:
            logger.warning(f"Unsupported file type: {filename}")

        return results

    def _process_zip(self, zip_content: bytes) -> List[Tuple[str, InvoiceModel, List]]:
        """
        Extract and process all XML files from ZIP.

        Args:
            zip_content: ZIP file bytes

        Returns:
            List of processed invoices
        """
        results = []

        try:
            with zipfile.ZipFile(BytesIO(zip_content)) as zf:
                for file_info in zf.filelist:
                    if file_info.filename.lower().endswith(".xml"):
                        xml_content = zf.read(file_info.filename)
                        result = self._process_xml(xml_content, file_info.filename)
                        if result:
                            results.append(result)

            logger.info(f"Processed {len(results)} XMLs from ZIP")

        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP file: {e}")
        except Exception as e:
            logger.error(f"Error processing ZIP: {e}", exc_info=True)

        return results

    def _process_xml(self, xml_content: bytes, filename: str) -> Tuple[str, InvoiceModel, List, Optional[dict]] | None:
        """
        Parse, validate, and classify a single XML file.

        Args:
            xml_content: XML file bytes
            filename: Name of the file

        Returns:
            Tuple of (filename, invoice, issues, classification) or None if parsing failed
        """
        try:
            # Step 1: Parse XML
            invoice = self.parser.parse(xml_content)

            # Step 2: Validate
            issues = self.validator.validate(invoice)

            # Step 3: Classify (if enabled)
            classification_result = None
            if self.auto_classify and self.classifier:
                try:
                    classification = self.classifier.classify(invoice)
                    classification_result = {
                        "operation_type": classification.operation_type,
                        "cost_center": classification.cost_center,
                        "confidence": classification.confidence,
                        "reasoning": classification.reasoning,
                        "used_llm_fallback": classification.used_llm_fallback
                    }
                    logger.info(f"Classified {invoice.document_key}: {classification.operation_type} → {classification.cost_center} (confidence: {classification.confidence:.0%})")
                except Exception as e:
                    logger.error(f"Classification failed for {filename}: {e}", exc_info=True)
                    # Continue even if classification fails

            logger.info(f"Processed {filename}: {invoice.document_type} {invoice.document_key}")

            # Step 4: Save to database if enabled
            if self.save_to_db:
                try:
                    self.db.save_invoice(invoice, issues, classification_result)
                    logger.info(f"Saved {invoice.document_key} to database")
                except Exception as e:
                    logger.error(f"Failed to save to database: {e}")
                    # Continue even if DB save fails

            return (filename, invoice, issues, classification_result)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)
            return None


def format_invoice_summary(invoice: InvoiceModel) -> str:
    """
    Format invoice data into a readable summary.

    Args:
        invoice: Parsed invoice model

    Returns:
        Formatted string with invoice details
    """
    summary = f"""
### 📄 {invoice.document_type}

**Documento:**
- 🔑 Chave: `{invoice.document_key}`
- 📋 Número: {invoice.document_number} / Série: {invoice.series}
- 📅 Emissão: {invoice.issue_date.strftime('%d/%m/%Y %H:%M:%S')}

**Emitente:**
- 🏢 Razão Social: {invoice.issuer_name}
- 📄 CNPJ: {invoice.issuer_cnpj}

**Destinatário:**
- 👤 Nome: {invoice.recipient_name or 'Não especificado'}
- 📄 CNPJ/CPF: {invoice.recipient_cnpj_cpf or 'Não especificado'}

**Valores:**
- 💵 Total de Produtos: R$ {invoice.total_products:,.2f}
- 💰 Total da Nota: R$ {invoice.total_invoice:,.2f}

**Impostos:**
- ICMS: R$ {invoice.taxes.icms or 0:,.2f}
- IPI: R$ {invoice.taxes.ipi or 0:,.2f}
- PIS: R$ {invoice.taxes.pis or 0:,.2f}
- COFINS: R$ {invoice.taxes.cofins or 0:,.2f}

**Itens:** {len(invoice.items)} produto(s)
"""

    return summary


def format_items_table(invoice: InvoiceModel) -> str:
    """
    Format invoice items into a markdown table.

    Args:
        invoice: Parsed invoice model

    Returns:
        Markdown table with items
    """
    if not invoice.items:
        return "_Nenhum item encontrado_"

    # Header
    table = "| # | Produto | NCM | CFOP | Qtd | Valor Unit. | Total |\n"
    table += "|---|---------|-----|------|-----|-------------|-------|\n"

    # Items
    for item in invoice.items:
        # Use description instead of product_name, unit_price and total_price
        table += f"| {item.item_number} | {item.description[:30]} | {item.ncm or '-'} | {item.cfop or '-'} | "
        table += f"{item.quantity} | R$ {item.unit_price:,.2f} | R$ {item.total_price:,.2f} |\n"

    return table


def format_validation_issues(issues: List) -> str:
    """
    Format validation issues into a readable report.

    Args:
        issues: List of ValidationIssue objects

    Returns:
        Formatted string with issues grouped by severity
    """
    if not issues:
        return "✅ **Nenhum problema encontrado!** O documento passou em todas as validações."

    # Compare with enum values (lowercase strings)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    result = f"**Resumo:** {len(errors)} erro(s), {len(warnings)} aviso(s), {len(infos)} informação(ões)\n\n"

    if errors:
        result += "### ❌ Erros\n"
        for issue in errors:
            result += f"- **{issue.code}**: {issue.message}\n"
            if issue.suggestion:
                result += f"  💡 _Sugestão: {issue.suggestion}_\n"
        result += "\n"

    if warnings:
        result += "### ⚠️ Avisos\n"
        for issue in warnings:
            result += f"- **{issue.code}**: {issue.message}\n"
            if issue.suggestion:
                result += f"  💡 _Sugestão: {issue.suggestion}_\n"
        result += "\n"

    if infos:
        result += "### ℹ️ Informações\n"
        for issue in infos:
            result += f"- **{issue.code}**: {issue.message}\n"

    return result


def format_classification(classification: Optional[dict]) -> str:
    """
    Format classification results into a readable report.

    Args:
        classification: Dict with classification results or None

    Returns:
        Formatted string with classification details
    """
    if not classification:
        return "ℹ️ _Classificação não disponível para este documento._"

    operation_type = classification.get("operation_type", "Desconhecido")
    cost_center = classification.get("cost_center", "Não classificado")
    confidence = classification.get("confidence", 0)
    reasoning = classification.get("reasoning", "")
    used_llm = classification.get("used_llm_fallback", False)

    # Confidence badge
    if confidence >= 0.8:
        confidence_badge = "🟢 Alta"
        confidence_color = "green"
    elif confidence >= 0.6:
        confidence_badge = "🟡 Média"
        confidence_color = "orange"
    else:
        confidence_badge = "🔴 Baixa"
        confidence_color = "red"

    # Operation type emoji
    operation_emoji = {
        "purchase": "📥",
        "sale": "📤",
        "transfer": "🔄",
        "return": "↩️",
    }.get(operation_type.lower(), "📄")

    result = f"""
**Tipo de Operação:** {operation_emoji} {operation_type.title()}  
**Centro de Custo:** 🏢 {cost_center}  
**Confiança:** {confidence_badge} ({confidence:.0%})  
"""

    if reasoning:
        result += f"\n💡 **Justificativa:** {reasoning}"

    if used_llm:
        result += "\n\n🤖 _Classificação feita com auxílio de IA (LLM fallback)_"

    return result
