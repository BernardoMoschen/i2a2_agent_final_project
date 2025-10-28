"""LangChain tool wrappers for fiscal document processing."""

import logging
from datetime import datetime
from typing import Any, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.database.db import DatabaseManager
from src.models import InvoiceModel, ValidationIssue
from src.tools.fiscal_validator import FiscalValidatorTool
from src.tools.xml_parser import XMLParserTool

logger = logging.getLogger(__name__)


class ParseXMLInput(BaseModel):
    """Input schema for XML parsing tool."""

    xml_content: str = Field(..., description="Raw XML content to parse")


class ParseXMLTool(BaseTool):
    """Tool for parsing Brazilian fiscal XML documents (NFe, NFCe, CTe, MDFe)."""

    name: str = "parse_fiscal_xml"
    description: str = """
    Parse Brazilian fiscal XML documents (NFe, NFCe, CTe, MDFe) into structured data.
    Input: raw XML string (can be full XML or just the key parts)
    Output: Formatted summary with issuer, recipient, items, totals, and taxes
    
    Use this tool when:
    - User uploads or pastes XML content
    - User asks to "parse", "process", or "analyze" a fiscal document
    - User mentions NFe, NFCe, CTe, or MDFe
    
    The tool automatically extracts:
    - Document type and key
    - Issuer (emitente) information
    - Recipient (destinatário) information  
    - All items with prices and taxes
    - Total values and tax breakdown
    """
    args_schema: type[BaseModel] = ParseXMLInput

    def _run(self, xml_content: str) -> str:
        """Parse XML and return structured invoice data."""
        try:
            parser = XMLParserTool()
            invoice = parser.parse(xml_content)

            # Return a human-friendly summary
            result = f"""
✅ Documento fiscal parseado com sucesso!

📄 Tipo: {invoice.document_type}
🔑 Chave de Acesso: {invoice.document_key}
📋 Número: {invoice.document_number} / Série: {invoice.series}
📅 Data de Emissão: {invoice.issue_date.strftime('%d/%m/%Y %H:%M:%S')}

👤 Emitente: {invoice.issuer_name}
   CNPJ: {invoice.issuer_cnpj}

👥 Destinatário: {invoice.recipient_name or 'Não especificado'}
   {f"CNPJ/CPF: {invoice.recipient_cnpj_cpf}" if invoice.recipient_cnpj_cpf else ""}

💰 Valores:
   Produtos: R$ {invoice.total_products:,.2f}
   Impostos: R$ {invoice.total_taxes:,.2f}
   Total da NF: R$ {invoice.total_invoice:,.2f}

📦 Itens: {len(invoice.items)}
"""
            # Add item details
            for item in invoice.items[:5]:  # Show first 5 items
                result += f"\n   {item.item_number}. {item.description} - {item.quantity} {item.unit} × R$ {item.unit_price:,.2f} = R$ {item.total_price:,.2f}"

            if len(invoice.items) > 5:
                result += f"\n   ... e mais {len(invoice.items) - 5} itens"

            return result

        except Exception as e:
            return f"❌ Erro ao parsear XML: {str(e)}"

    async def _arun(self, xml_content: str) -> str:
        """Async version."""
        return self._run(xml_content)


class ValidateInvoiceInput(BaseModel):
    """Input schema for validation tool."""

    xml_content: str = Field(..., description="Raw XML content to validate")


class ValidateInvoiceTool(BaseTool):
    """Tool for validating Brazilian fiscal documents against fiscal rules."""

    name: str = "validate_fiscal_document"
    description: str = """
    Validate a Brazilian fiscal document (NFe, NFCe) against fiscal rules.
    Checks: document key format, CNPJ, totals, item calculations, CFOP, NCM, dates.
    Input: raw XML string
    Output: List of validation issues with severity (ERROR, WARNING, INFO) and suggestions.
    Use this after parsing to check document compliance.
    """
    args_schema: type[BaseModel] = ValidateInvoiceInput

    def _run(self, xml_content: str) -> str:
        """Validate document and return issues."""
        try:
            # First parse
            parser = XMLParserTool()
            invoice = parser.parse(xml_content)

            # Then validate
            validator = FiscalValidatorTool()
            issues = validator.validate(invoice)

            if not issues:
                return "✅ Documento válido! Nenhum problema encontrado."

            # Format issues
            result = f"📋 Validação concluída: {len(issues)} problema(s) encontrado(s)\n\n"

            errors = [i for i in issues if i.severity == "error"]
            warnings = [i for i in issues if i.severity == "warning"]
            infos = [i for i in issues if i.severity == "info"]

            if errors:
                result += "❌ ERROS:\n"
                for issue in errors:
                    result += f"  • {issue.code}: {issue.message}\n"
                    if issue.field:
                        result += f"    Campo: {issue.field}\n"
                    if issue.suggestion:
                        result += f"    Sugestão: {issue.suggestion}\n"
                result += "\n"

            if warnings:
                result += "⚠️  AVISOS:\n"
                for issue in warnings:
                    result += f"  • {issue.code}: {issue.message}\n"
                    if issue.field:
                        result += f"    Campo: {issue.field}\n"
                    if issue.suggestion:
                        result += f"    Sugestão: {issue.suggestion}\n"
                result += "\n"

            if infos:
                result += "ℹ️  INFORMAÇÕES:\n"
                for issue in infos:
                    result += f"  • {issue.code}: {issue.message}\n"
                    if issue.suggestion:
                        result += f"    Sugestão: {issue.suggestion}\n"
                result += "\n"

            # Summary
            result += f"📊 Resumo: {len(errors)} erro(s), {len(warnings)} aviso(s), {len(infos)} info(s)\n"

            if errors:
                result += "\n⛔ Documento possui ERROS e não deve ser processado!"
            elif warnings:
                result += "\n⚠️  Documento pode ser processado, mas com atenção aos avisos."
            else:
                result += "\n✅ Documento válido e pronto para processamento!"

            return result

        except Exception as e:
            return f"❌ Erro ao validar documento: {str(e)}"

    async def _arun(self, xml_content: str) -> str:
        """Async version."""
        return self._run(xml_content)


class AnswerQuestionInput(BaseModel):
    """Input schema for general questions."""

    question: str = Field(..., description="User's question about fiscal documents")


class FiscalKnowledgeTool(BaseTool):
    """Tool for answering general questions about Brazilian fiscal documents."""

    name: str = "fiscal_knowledge"
    description: str = """
    Answer general questions about Brazilian fiscal documents, tax rules, and processes.
    Use this for questions about:
    - What is NFe, NFCe, CTe, MDFe
    - Tax types (ICMS, IPI, PIS, COFINS, ISS)
    - CFOP codes and their meanings
    - NCM classification
    - Fiscal document requirements
    Do NOT use this for parsing or validating specific documents.
    """
    args_schema: type[BaseModel] = AnswerQuestionInput

    def _run(self, question: str) -> str:
        """Provide general fiscal knowledge."""
        # This would ideally use a knowledge base or RAG
        # For now, return a helpful message
        return """
Sou um agente especializado em documentos fiscais brasileiros. Posso ajudar com:

📄 **Tipos de Documentos:**
- NFe: Nota Fiscal Eletrônica (vendas em geral)
- NFCe: Nota Fiscal de Consumidor Eletrônica (varejo)
- CTe: Conhecimento de Transporte Eletrônico
- MDFe: Manifesto Eletrônico de Documentos Fiscais

💰 **Impostos:**
- ICMS: Imposto sobre Circulação de Mercadorias e Serviços
- IPI: Imposto sobre Produtos Industrializados
- PIS/COFINS: Contribuições sociais
- ISS: Imposto sobre Serviços

🔢 **Códigos:**
- CFOP: Código Fiscal de Operações (ex: 5102 = venda dentro do estado)
- NCM: Nomenclatura Comum do Mercosul (classificação de produtos)

Para perguntas específicas, forneça mais detalhes ou um documento XML para análise!
"""

    async def _arun(self, question: str) -> str:
        """Async version."""
        return self._run(question)


class SearchInvoicesInput(BaseModel):
    """Input schema for searching invoices in database."""

    document_type: Optional[str] = Field(None, description="Filter by document type: NFe, NFCe, CTe, or MDFe")
    operation_type: Optional[str] = Field(None, description="Filter by operation type: purchase (compra), sale (venda), transfer (transferência), or return (devolução)")
    issuer_cnpj: Optional[str] = Field(None, description="Filter by issuer CNPJ (14 digits)")
    days_back: Optional[int] = Field(9999, description="Search last N days. Default is 9999 to search ALL documents ever processed. ALWAYS use 9999 when user asks about counts, years, or 'all' documents.")


class DatabaseSearchTool(BaseTool):
    """Tool for searching invoices in the SQLite database."""

    name: str = "search_invoices_database"
    description: str = """
    Search for fiscal documents stored in the database with flexible filters.
    
    🚨 CRITICAL: When user asks about counting or listing documents, you MUST use days_back=9999!
    
    ⚠️ MANDATORY RULES (YOU MUST FOLLOW):
    1. ANY question with "quantas", "quantos", "how many", "count", "total" → days_back=9999
    2. ANY question about a specific YEAR (2024, 2023, etc.) → days_back=9999
    3. ANY question with "todas", "todos", "all", "list", "mostre", "traga" → days_back=9999
    4. ANY question about specific dates → days_back=9999
    5. Documents in database may be from any year → ALWAYS use days_back=9999
    
    ✅ CORRECT USAGE EXAMPLES:
    - "Quantas notas de compra?" → {"operation_type": "purchase", "days_back": 9999}
    - "Documentos de 2024?" → {"days_back": 9999}
    - "Me traga 5 XMLs de 2024" → {"days_back": 9999}
    - "Há documento na data 2024-01-19?" → {"days_back": 9999}
    - "Total de documentos" → {"days_back": 9999}
    
    ❌ WRONG - DO NOT DO THIS:
    - Using days_back=30 or days_back=365 for ANY query
    - Using "limit" parameter (not supported - tool returns up to 100 results)
    
    OPERATION TYPE MAPPING:
    - "compra", "purchase", "entrada" → operation_type="purchase"
    - "venda", "sale", "saída" → operation_type="sale"
    - "transferência", "transfer" → operation_type="transfer"
    - "devolução", "return" → operation_type="return"
    
    Returns: Count and detailed list of invoices with operation type, issuer, date, total value
    """
    args_schema: type[BaseModel] = SearchInvoicesInput

    def _run(
        self,
        document_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        issuer_cnpj: Optional[str] = None,
        days_back: int = 9999,
    ) -> str:
        """Search invoices in database."""
        try:
            logger.info(f"DatabaseSearchTool called with: document_type={document_type}, operation_type={operation_type}, issuer_cnpj={issuer_cnpj}, days_back={days_back}")
            
            # Create database connection (no state stored)
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            # Search database with all filters
            invoices = db.search_invoices(
                document_type=document_type,
                operation_type=operation_type,
                issuer_cnpj=issuer_cnpj,
                days_back=days_back,
                limit=100,
            )
            
            logger.info(f"DatabaseSearchTool found {len(invoices)} documents")
            
            if not invoices:
                filter_desc = []
                if document_type:
                    filter_desc.append(f"Tipo: {document_type}")
                if operation_type:
                    op_label = {"purchase": "Compra", "sale": "Venda", "transfer": "Transferência", "return": "Devolução"}.get(operation_type, operation_type)
                    filter_desc.append(f"Operação: {op_label}")
                if issuer_cnpj:
                    filter_desc.append(f"Emitente: {issuer_cnpj}")
                filter_desc.append(f"Período: Últimos {days_back} dias")
                
                return f"""
🔍 Nenhum documento encontrado com os filtros:
{chr(10).join(f'- {f}' for f in filter_desc)}

💡 Verifique se há documentos cadastrados no banco de dados.
Para ver TODOS os documentos sem filtros, use days_back=9999 sem outros parâmetros.
"""
            
            # Count by operation type
            op_counts = {}
            for inv in invoices:
                op = inv.operation_type or "not_classified"
                op_counts[op] = op_counts.get(op, 0) + 1
            
            # Format results
            result = f"""
📊 **Encontrados {len(invoices)} documento(s):**

"""
            
            # Show operation type breakdown if filtered or multiple types exist
            if len(op_counts) > 1 or operation_type:
                result += "**Por Tipo de Operação:**\n"
                op_labels = {
                    "purchase": "📥 Compras",
                    "sale": "📤 Vendas", 
                    "transfer": "🔄 Transferências",
                    "return": "↩️ Devoluções",
                    "not_classified": "❓ Não classificado"
                }
                for op, count in sorted(op_counts.items()):
                    label = op_labels.get(op, op)
                    result += f"- {label}: {count}\n"
                result += "\n"
            
            # Show first 15 documents
            for inv in invoices[:15]:
                op_emoji = {
                    "purchase": "📥",
                    "sale": "📤",
                    "transfer": "🔄",
                    "return": "↩️"
                }.get(inv.operation_type, "📄")
                
                op_label = {
                    "purchase": "Compra",
                    "sale": "Venda",
                    "transfer": "Transfer",
                    "return": "Devolução"
                }.get(inv.operation_type, "N/A") if inv.operation_type else "N/A"
                
                result += f"""
{op_emoji} **{inv.document_type}** - {inv.document_number}/{inv.series} | {op_label}
   🏢 Emitente: {inv.issuer_name[:40]}
   📅 Data: {inv.issue_date.strftime('%d/%m/%Y')}
   💰 Valor: R$ {inv.total_invoice:,.2f}

"""
            
            if len(invoices) > 15:
                result += f"\n_... e mais {len(invoices) - 15} documento(s)_\n\n"
            
            # Add statistics
            total_value = sum(inv.total_invoice for inv in invoices)
            result += f"""
**Resumo Final:**
- 📄 Total de documentos: {len(invoices)}
- 💰 Valor total: R$ {total_value:,.2f}
"""
            
            return result
            
        except Exception as e:
            return f"❌ Erro ao buscar no banco de dados: {str(e)}"

    async def _arun(
        self,
        document_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        issuer_cnpj: Optional[str] = None,
        days_back: int = 3650,
    ) -> str:
        """Async version."""
        return self._run(document_type, operation_type, issuer_cnpj, days_back)


class GetStatisticsInput(BaseModel):
    """Input schema for getting database statistics."""

    pass  # No input needed


class DatabaseStatsTool(BaseTool):
    """Tool for getting database statistics."""

    name: str = "get_database_statistics"
    description: str = """
    Get statistics about processed fiscal documents in the database.
    
    Use this when user asks:
    - "Quantos documentos temos?"
    - "Estatísticas do banco"
    - "Resumo dos documentos processados"
    
    Returns: Total documents, items, issues, and breakdown by document type
    """
    args_schema: type[BaseModel] = GetStatisticsInput

    def _run(self) -> str:
        """Get database statistics."""
        try:
            # Create database connection (no state stored)
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            stats = db.get_statistics()
            
            result = f"""
📊 **Estatísticas do Banco de Dados**

**Totais:**
- 📄 Documentos processados: {stats['total_invoices']}
- 🛒 Itens cadastrados: {stats['total_items']}
- ⚠️ Issues de validação: {stats['total_issues']}
- 💰 Valor total: R$ {stats['total_value']:,.2f}

**Por Tipo de Documento:**
"""
            
            for doc_type, count in stats['by_type'].items():
                result += f"- {doc_type}: {count} documento(s)\n"
            
            if stats['total_invoices'] == 0:
                result += "\n💡 **Dica:** Faça upload de XMLs na aba 'Upload' para começar!"
            
            return result
            
        except Exception as e:
            return f"❌ Erro ao obter estatísticas: {str(e)}"

    async def _arun(self) -> str:
        """Async version."""
        return self._run()


# Tool instances
parse_xml_tool = ParseXMLTool()
validate_invoice_tool = ValidateInvoiceTool()
fiscal_knowledge_tool = FiscalKnowledgeTool()
database_search_tool = DatabaseSearchTool()
database_stats_tool = DatabaseStatsTool()

# Import business tools
from src.agent.business_tools import ALL_BUSINESS_TOOLS
from src.agent.archiver_tools import ALL_ARCHIVER_TOOLS

# Import report generation tool
from .report_tool import FiscalReportExportTool
fiscal_report_export_tool = FiscalReportExportTool()

# All tools list
ALL_TOOLS = [
    parse_xml_tool,
    validate_invoice_tool,
    fiscal_knowledge_tool,
    database_search_tool,
    database_stats_tool,
    fiscal_report_export_tool,  # CSV/XLSX file export for download
    *ALL_BUSINESS_TOOLS,  # Includes 'generate_report' for interactive charts
    *ALL_ARCHIVER_TOOLS,
]


