"""LangChain tool wrappers for fiscal document processing."""

from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.models import InvoiceModel, ValidationIssue
from src.tools.fiscal_validator import FiscalValidatorTool
from src.tools.xml_parser import XMLParserTool


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


# Tool instances
parse_xml_tool = ParseXMLTool()
validate_invoice_tool = ValidateInvoiceTool()
fiscal_knowledge_tool = FiscalKnowledgeTool()

# List of all tools
ALL_TOOLS = [
    parse_xml_tool,
    validate_invoice_tool,
    fiscal_knowledge_tool,
]
