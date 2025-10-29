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


class AnalyzeValidationIssuesInput(BaseModel):
    """Input schema for analyzing validation issues."""
    
    year: Optional[int] = Field(None, description="Year to filter by (e.g., 2024)")
    month: Optional[int] = Field(None, description="Month to filter by (1-12), requires year")


class ValidationAnalysisTool(BaseTool):
    """Tool for analyzing and reporting on validation issues."""

    name: str = "analyze_validation_issues"
    description: str = """
    Analyze validation issues to identify the most common problems in fiscal documents.
    
    Use this when user asks:
    - "qual o problema de validação mais comum em 2024?"
    - "quais são os problemas de validação mais frequentes?"
    - "qual erro mais ocorre nos documentos?"
    - "problemas de validação do mês de janeiro/fevereiro/etc"
    
    You can optionally filter by year and month.
    
    Returns: A detailed analysis of the most common validation issues, their frequency, 
    and severity levels.
    """
    args_schema: type[BaseModel] = AnalyzeValidationIssuesInput

    def _run(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Analyze validation issues."""
        try:
            # Create database connection
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            analysis = db.get_validation_issue_analysis(year=year, month=month, limit=10)
            
            if analysis["total_issues"] == 0:
                period_str = f"{year}/{month:02d}" if month else str(year) if year else "all time"
                return f"""
❌ **Nenhum problema de validação encontrado**

Período analisado: {period_str}

Isso significa que todos os documentos foram validados com sucesso! 🎉
"""
            
            # Build result
            period_str = analysis["period"]
            result = f"""
📊 **Análise de Problemas de Validação**

**Período:** {period_str}
**Total de Problemas:** {analysis['total_issues']}

**Distribuição por Severidade:**
"""
            
            for severity, count in sorted(analysis["by_severity"].items(), key=lambda x: x[1], reverse=True):
                severity_emoji = "🔴" if severity == "error" else "🟡" if severity == "warning" else "ℹ️"
                result += f"\n- {severity_emoji} {severity.upper()}: {count} problema(s)"
            
            result += "\n\n**Top Problemas Mais Frequentes:**\n"
            
            for idx, issue in enumerate(analysis["common_issues"], 1):
                result += f"\n{idx}. **[{issue['code']}]** - {issue['count']} ocorrências"
                result += f"\n   Severidade: {issue['severity']}"
                
                if issue['severity_breakdown']:
                    severity_detail = ", ".join(
                        f"{sev}: {cnt}" 
                        for sev, cnt in sorted(
                            issue['severity_breakdown'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )
                    )
                    result += f" ({severity_detail})"
                
                if issue['field']:
                    result += f"\n   Campo afetado: {issue['field']}"
                
                if issue['sample_message']:
                    result += f"\n   Exemplo: {issue['sample_message'][:100]}..."
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing validation issues: {e}")
            return f"❌ Erro ao analisar problemas de validação: {str(e)}"

    async def _arun(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Async version."""
        return self._run(year=year, month=month)


class AnalyzeIssuesByIssuerInput(BaseModel):
    """Input schema for analyzing issues by issuer."""
    
    year: Optional[int] = Field(None, description="Year to filter by (e.g., 2024)")
    month: Optional[int] = Field(None, description="Month to filter by (1-12)")


class IssuerAnalysisTool(BaseTool):
    """Tool for analyzing validation issues grouped by issuer/supplier."""

    name: str = "analyze_issues_by_issuer"
    description: str = """
    Analyze validation issues grouped by issuer (supplier/emitente).
    
    Use this when user asks:
    - "Qual fornecedor tem mais problemas?"
    - "Ranking de fornecedores por taxa de erro"
    - "Quais emitentes têm documentos com erros?"
    - "Análise de qualidade por fornecedor"
    
    You can optionally filter by year and month.
    
    Returns: Detailed analysis of validation issues per issuer with error rates
    and top problems for each supplier.
    """
    args_schema: type[BaseModel] = AnalyzeIssuesByIssuerInput

    def _run(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Analyze issues by issuer."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            analysis = db.get_validation_issues_by_issuer(year=year, month=month, limit=15)
            
            if not analysis or not analysis.get("issuers"):
                return f"""
❌ **Nenhum problema de validação encontrado por emitente**

Período: {analysis.get('period', 'all time')}
"""
            
            result = f"""
📊 **Análise de Problemas de Validação por Emitente**

**Período:** {analysis['period']}
**Total de Emitentes com Problemas:** {analysis['total_issuers']}

"""
            
            for idx, issuer in enumerate(analysis["issuers"], 1):
                result += f"""
{idx}. **{issuer['name']}** (CNPJ: {issuer['cnpj']})
   📄 Documentos: {issuer['document_count']}
   🔴 Erros: {issuer['error_count']}
   🟡 Avisos: {issuer['warning_count']}
   📊 Taxa de Erro: {issuer['error_rate']}%
"""
                
                if issuer['top_issues']:
                    result += "   Top Problemas: "
                    result += ", ".join([f"{code}({cnt}x)" for code, cnt in issuer['top_issues']])
                    result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing issues by issuer: {e}")
            return f"❌ Erro ao analisar problemas por emitente: {str(e)}"

    async def _arun(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Async version."""
        return self._run(year=year, month=month)


class AnalyzeIssuesByOperationInput(BaseModel):
    """Input schema for analyzing issues by operation type."""
    
    year: Optional[int] = Field(None, description="Year to filter by (e.g., 2024)")
    month: Optional[int] = Field(None, description="Month to filter by (1-12)")


class OperationAnalysisTool(BaseTool):
    """Tool for comparing validation issues across operation types."""

    name: str = "analyze_issues_by_operation"
    description: str = """
    Compare validation issues across different operation types (purchase, sale, transfer, return).
    
    Use this when user asks:
    - "Compras têm mais erros que vendas?"
    - "Qual tipo de operação tem mais problemas?"
    - "Comparação de qualidade entre compras e vendas"
    - "Qual operação fiscal tem mais taxa de erro?"
    
    You can optionally filter by year and month.
    
    Returns: Comparison of validation metrics across all operation types.
    """
    args_schema: type[BaseModel] = AnalyzeIssuesByOperationInput

    def _run(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Analyze issues by operation type."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            analysis = db.get_validation_issues_by_operation(year=year, month=month)
            
            if not analysis.get("by_operation"):
                return f"""
❌ **Nenhum documento encontrado para análise**

Período: {analysis.get('period', 'all time')}
"""
            
            result = f"""
📊 **Comparação de Problemas por Tipo de Operação**

**Período:** {analysis['period']}

"""
            
            # Sort by error rate
            sorted_ops = sorted(
                analysis["by_operation"].items(),
                key=lambda x: x[1]["error_rate"],
                reverse=True
            )
            
            for operation, metrics in sorted_ops:
                op_label = {
                    "purchase": "📥 COMPRAS",
                    "sale": "📤 VENDAS",
                    "transfer": "🔄 TRANSFERÊNCIAS",
                    "return": "↩️ DEVOLUÇÕES",
                    "unclassified": "❓ NÃO CLASSIFICADO"
                }.get(operation, f"📄 {operation.upper()}")
                
                result += f"""
**{op_label}**
   📄 Documentos: {metrics['document_count']}
   🔴 Erros: {metrics['error_count']}
   🟡 Avisos: {metrics['warning_count']}
   📊 Taxa de Erro: {metrics['error_rate']}%
   📈 Média de Problemas/Doc: {metrics['avg_issues_per_doc']}

"""
            
            # Find best and worst
            best_op = min(sorted_ops, key=lambda x: x[1]["error_rate"])
            worst_op = max(sorted_ops, key=lambda x: x[1]["error_rate"])
            
            result += f"""
**📈 Resumo:**
✅ Melhor: {best_op[0].upper()} ({best_op[1]['error_rate']}% de erro)
❌ Pior: {worst_op[0].upper()} ({worst_op[1]['error_rate']}% de erro)
"""
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing issues by operation: {e}")
            return f"❌ Erro ao analisar por tipo de operação: {str(e)}"

    async def _arun(self, year: Optional[int] = None, month: Optional[int] = None) -> str:
        """Async version."""
        return self._run(year=year, month=month)


class DataQualityScoreInput(BaseModel):
    """Input schema for data quality score."""
    
    year: Optional[int] = Field(None, description="Year to analyze (e.g., 2024). If None, uses all data.")


class DataQualityTool(BaseTool):
    """Tool for calculating overall data quality metrics."""

    name: str = "calculate_data_quality"
    description: str = """
    Calculate overall data quality metrics and score (0-100 scale).
    
    Use this when user asks:
    - "Qual é a qualidade dos nossos documentos?"
    - "Qual % dos documentos tem erros?"
    - "Score de qualidade dos dados"
    - "Dashboard de qualidade"
    - "Como está a integridade dos dados?"
    
    Optionally filter by year.
    
    Returns: Quality metrics including completeness, accuracy, consistency,
    and overall quality score.
    """
    args_schema: type[BaseModel] = DataQualityScoreInput

    def _run(self, year: Optional[int] = None) -> str:
        """Calculate data quality score."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            quality = db.calculate_data_quality_score(year=year)
            
            if quality["documents_analyzed"] == 0:
                return f"""
❌ **Nenhum documento para análise**

Período: {'Year ' + str(year) if year else 'all time'}
"""
            
            # Determine quality level
            score = quality["overall_score"]
            if score >= 90:
                emoji = "🟢"
                level = "EXCELENTE"
            elif score >= 80:
                emoji = "🟡"
                level = "BOM"
            elif score >= 70:
                emoji = "🟠"
                level = "ACEITÁVEL"
            else:
                emoji = "🔴"
                level = "CRÍTICO"
            
            result = f"""
📊 **Análise de Qualidade de Dados**

**Período:** {'Year ' + str(year) if year else 'all time'}

{emoji} **Score Geral: {quality['overall_score']}/100 ({level})**

**Resumo:**
- 📄 Documentos Analisados: {quality['documents_analyzed']}
- ✅ Documentos Sem Problemas: {quality['documents_clean']}
- 🔴 Documentos com Erros: {quality['documents_with_errors']}
- 🟡 Documentos com Avisos: {quality['documents_with_warnings']}

**Problemas Detectados:**
- 🔴 Total de Erros: {quality['error_count']} ({quality['error_rate']}%)
- 🟡 Total de Avisos: {quality['warning_count']} ({quality['warning_rate']}%)
- 📊 Total de Problemas: {quality['total_issues']}

**Métricas Detalhadas:**
- ✅ Completeness: {quality['metrics']['completeness']}/100
- 🎯 Accuracy: {quality['metrics']['accuracy']}/100
- 🔗 Consistency: {quality['metrics']['consistency']}/100
"""
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return f"❌ Erro ao calcular qualidade dos dados: {str(e)}"

    async def _arun(self, year: Optional[int] = None) -> str:
        """Async version."""
        return self._run(year=year)


class RemediationSuggestionsInput(BaseModel):
    """Input schema for remediation suggestions."""
    
    year: Optional[int] = Field(None, description="Year to filter by (e.g., 2024)")
    month: Optional[int] = Field(None, description="Month to filter by (1-12)")
    limit: int = Field(10, description="Max number of suggestions (default 10)")


class RemediationTool(BaseTool):
    """Tool for getting remediation suggestions for validation issues."""

    name: str = "get_remediation_suggestions"
    description: str = """
    Get remediation suggestions for the most common validation issues.
    
    Use this when user asks:
    - "Como corrigir os erros?"
    - "Quais ações tomar para resolver os problemas?"
    - "Sugestões de remediação"
    - "Como melhorar a qualidade?"
    
    Returns: Prioritized list of issues with recommended actions and steps to fix.
    """
    args_schema: type[BaseModel] = RemediationSuggestionsInput

    def _run(
        self, 
        year: Optional[int] = None, 
        month: Optional[int] = None,
        limit: int = 10
    ) -> str:
        """Get remediation suggestions."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            suggestions = db.get_remediation_suggestions(year=year, month=month, limit=limit)
            
            if suggestions.get("error"):
                return f"❌ Erro ao gerar sugestões: {suggestions['error']}"
            
            if not suggestions.get("suggestions"):
                return f"""
❌ **Nenhuma sugestão de remediação disponível**

Período: {suggestions['period']}
"""
            
            result = f"""
🔧 **Sugestões de Remediação para Problemas de Validação**

**Período:** {suggestions['period']}
**Total de Sugestões:** {suggestions['total_suggestions']}

"""
            
            for idx, suggestion in enumerate(suggestions["suggestions"], 1):
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(suggestion["remediation"]["priority"], "⚪")
                
                severity_icon = "❌" if suggestion["severity"] == "error" else "⚠️"
                
                result += f"""
{idx}. **{suggestion['code']}** {severity_icon}
   📊 Frequência: {suggestion['frequency']}x
   🎯 Ação: {suggestion['remediation']['action']}
   {priority_emoji} Prioridade: {suggestion['remediation']['priority'].upper()}
   📌 Exemplo: {suggestion['sample_message'][:80]}...
   
   **Passos para Corrigir:**
"""
                for step_idx, step in enumerate(suggestion["remediation"]["steps"], 1):
                    result += f"      {step_idx}. {step}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting remediation suggestions: {e}")
            return f"❌ Erro ao gerar sugestões de remediação: {str(e)}"

    async def _arun(
        self, 
        year: Optional[int] = None, 
        month: Optional[int] = None,
        limit: int = 10
    ) -> str:
        """Async version."""
        return self._run(year=year, month=month, limit=limit)


class TrendsAnalysisInput(BaseModel):
    """Input schema for trends analysis."""
    
    months_back: int = Field(12, description="Number of months to analyze (default 12)")


class TrendsTool(BaseTool):
    """Tool for analyzing validation issue trends over time."""

    name: str = "analyze_validation_trends"
    description: str = """
    Analyze trends in validation issues over time (monthly aggregation).
    
    Use this when user asks:
    - "Os erros estão aumentando ou diminuindo?"
    - "Qual é a tendência de qualidade?"
    - "Análise de tendências de problemas"
    - "Evolução da qualidade dos documentos"
    - "Problemas estão melhorando?"
    
    You can optionally specify number of months to analyze (default 12).
    
    Returns: Monthly aggregation of errors/warnings with trend direction.
    """
    args_schema: type[BaseModel] = TrendsAnalysisInput

    def _run(self, months_back: int = 12) -> str:
        """Analyze trends."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            trends = db.analyze_trends(months_back=months_back)
            
            if trends.get("error"):
                return f"❌ Erro ao analisar tendências: {trends['error']}"
            
            if trends["data_points"] == 0:
                return f"""
❌ **Dados insuficientes para análise de tendências**

Meses analisados: {months_back}
"""
            
            result = f"""
📈 **Análise de Tendências de Problemas de Validação**

**Período:** {trends['first_period']} até {trends['last_period']}
**Meses Analisados:** {trends['months_analyzed']}
**Pontos de Dados:** {trends['data_points']}

{trends['trend_direction']}

📊 **Taxa Média de Erro:** {trends['average_error_rate']}%

**Dados Mensais:**

"""
            
            for month_data in trends["monthly_data"]:
                # Visual bar representation
                error_bar = "█" * int(month_data["error_rate"] / 2)
                
                result += f"""
**{month_data['period']}**
   📄 Documentos: {month_data['documents']}
   🔴 Erros: {month_data['errors']}
   🟡 Avisos: {month_data['warnings']}
   📊 Taxa de Erro: {month_data['error_rate']}% {error_bar}
"""
            
            # Analysis
            if trends["data_points"] >= 2:
                first = trends["monthly_data"][0]
                last = trends["monthly_data"][-1]
                
                change = last["error_rate"] - first["error_rate"]
                pct_change = (change / first["error_rate"] * 100) if first["error_rate"] > 0 else 0
                
                result += f"""
**📊 Análise:**
   Primeira medição: {first['period']} ({first['error_rate']}%)
   Última medição: {last['period']} ({last['error_rate']}%)
   Mudança: {change:+.2f}pp ({pct_change:+.1f}%)
"""
                
                if change < -0.5:
                    result += "   ✅ **POSITIVO**: Qualidade está melhorando!\n"
                elif change > 0.5:
                    result += "   ⚠️ **NEGATIVO**: Qualidade está piorando. Investigar!\n"
                else:
                    result += "   ➡️ **ESTÁVEL**: Qualidade mantém-se consistente.\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return f"❌ Erro ao analisar tendências: {str(e)}"

    async def _arun(self, months_back: int = 12) -> str:
        """Async version."""
        return self._run(months_back=months_back)


# Tool instances
parse_xml_tool = ParseXMLTool()
validate_invoice_tool = ValidateInvoiceTool()
fiscal_knowledge_tool = FiscalKnowledgeTool()
database_search_tool = DatabaseSearchTool()
database_stats_tool = DatabaseStatsTool()
validation_analysis_tool = ValidationAnalysisTool()
issuer_analysis_tool = IssuerAnalysisTool()
operation_analysis_tool = OperationAnalysisTool()
data_quality_tool = DataQualityTool()
remediation_tool = RemediationTool()
trends_tool = TrendsTool()

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
    validation_analysis_tool,           # New: analyze common validation issues
    issuer_analysis_tool,               # New: SPRINT 1 - analyze by issuer
    operation_analysis_tool,            # New: SPRINT 1 - compare by operation type
    data_quality_tool,                  # New: SPRINT 1 - overall quality metrics
    remediation_tool,                   # New: SPRINT 1 - remediation suggestions
    trends_tool,                        # New: SPRINT 1 - trend analysis
    fiscal_report_export_tool,          # CSV/XLSX file export for download
    *ALL_BUSINESS_TOOLS,                # Includes 'generate_report' for interactive charts
    *ALL_ARCHIVER_TOOLS,
]



