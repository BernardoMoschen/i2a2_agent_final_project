"""Business intelligence and reporting tools for fiscal document agent."""

import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Optional

import plotly.graph_objects as go
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.database.db import DatabaseManager
from src.models import InvoiceModel
from src.services.classifier import DocumentClassifier
from src.services.external_validators import CEPValidator, CNPJValidator
from src.services.ncm_validator import NCMValidator

logger = logging.getLogger(__name__)


# ============================================================================
# 1. REPORT GENERATOR TOOL
# ============================================================================


class GenerateReportInput(BaseModel):
    """Input schema for report generator."""

    report_type: str = Field(
        ...,
        description=(
            "Type of report to generate: "
            "'sales_by_month' | 'purchases_by_month' | 'taxes_breakdown' | "
            "'supplier_ranking' | 'invoices_timeline'"
        ),
    )
    days_back: int = Field(
        default=365,
        description="Number of days to include in the report (default: 365 days)",
    )


class ReportGeneratorTool(BaseTool):
    """
    Generate visual reports and charts from fiscal data.
    
    Creates interactive Plotly charts that can be embedded in Streamlit chat.
    
    Available reports:
    - sales_by_month: Monthly sales totals (bar chart)
    - purchases_by_month: Monthly purchase totals (bar chart)
    - taxes_breakdown: Tax breakdown by type (pie chart)
    - supplier_ranking: Top 10 suppliers by total value (horizontal bar)
    - invoices_timeline: Daily invoice counts (line chart)
    """

    name: str = "generate_report"
    description: str = """
    Generate visual reports and charts from fiscal document data.
    
    Use this when user asks for:
    - "Gerar gráfico de vendas"
    - "Mostrar breakdown de impostos"
    - "Ranking de fornecedores"
    - "Evolução temporal de notas"
    
    Available report types:
    - sales_by_month: Monthly sales totals
    - purchases_by_month: Monthly purchases totals
    - taxes_breakdown: Tax breakdown (ICMS, IPI, PIS, COFINS)
    - supplier_ranking: Top 10 suppliers by value
    - invoices_timeline: Daily invoice counts
    
    Returns: Description of the chart + Plotly JSON for embedding
    """
    args_schema: type[BaseModel] = GenerateReportInput

    def _run(self, report_type: str, days_back: int = 365) -> str:
        """Generate report and return Plotly chart JSON."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            # Get data based on report type
            if report_type == "sales_by_month":
                return self._generate_sales_by_month(db, days_back)
            
            elif report_type == "purchases_by_month":
                return self._generate_purchases_by_month(db, days_back)
            
            elif report_type == "taxes_breakdown":
                return self._generate_taxes_breakdown(db, days_back)
            
            elif report_type == "supplier_ranking":
                return self._generate_supplier_ranking(db, days_back)
            
            elif report_type == "invoices_timeline":
                return self._generate_invoices_timeline(db, days_back)
            
            else:
                return f"❌ Tipo de relatório desconhecido: {report_type}"
        
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return f"❌ Erro ao gerar relatório: {str(e)}"

    def _generate_sales_by_month(self, db: DatabaseManager, days_back: int) -> str:
        """Generate monthly sales chart."""
        invoices = db.search_invoices(
            operation_type="sale",
            days_back=days_back,
            limit=10000,
        )
        
        if not invoices:
            return "📊 Nenhuma venda encontrada no período especificado."
        
        # Aggregate by month
        monthly_data = {}
        for inv in invoices:
            month_key = inv.issue_date.strftime("%Y-%m")
            monthly_data[month_key] = monthly_data.get(month_key, 0) + float(inv.total_invoice)
        
        # Sort by month
        months = sorted(monthly_data.keys())
        values = [monthly_data[m] for m in months]
        
        # Create Plotly chart
        fig = go.Figure(data=[
            go.Bar(
                x=months,
                y=values,
                marker_color='rgb(55, 83, 109)',
                text=[f"R$ {v:,.2f}" for v in values],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="📈 Vendas Mensais",
            xaxis_title="Mês",
            yaxis_title="Valor Total (R$)",
            template="plotly_white",
            height=400,
        )
        
        # Convert to JSON for Streamlit
        chart_json = fig.to_json()
        
        total = sum(values)
        avg = total / len(values) if values else 0
        
        return f"""
📊 **Relatório de Vendas Mensais**

📅 Período: {months[0]} a {months[-1]}
📄 Total de notas: {len(invoices)}
💰 Valor total: R$ {total:,.2f}
📊 Média mensal: R$ {avg:,.2f}

🎨 Gráfico gerado (ver abaixo)

{chart_json}
"""

    def _generate_purchases_by_month(self, db: DatabaseManager, days_back: int) -> str:
        """Generate monthly purchases chart."""
        invoices = db.search_invoices(
            operation_type="purchase",
            days_back=days_back,
            limit=10000,
        )
        
        if not invoices:
            return "📊 Nenhuma compra encontrada no período especificado."
        
        # Aggregate by month
        monthly_data = {}
        for inv in invoices:
            month_key = inv.issue_date.strftime("%Y-%m")
            monthly_data[month_key] = monthly_data.get(month_key, 0) + float(inv.total_invoice)
        
        # Sort by month
        months = sorted(monthly_data.keys())
        values = [monthly_data[m] for m in months]
        
        # Create Plotly chart
        fig = go.Figure(data=[
            go.Bar(
                x=months,
                y=values,
                marker_color='rgb(158, 185, 243)',
                text=[f"R$ {v:,.2f}" for v in values],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="📉 Compras Mensais",
            xaxis_title="Mês",
            yaxis_title="Valor Total (R$)",
            template="plotly_white",
            height=400,
        )
        
        chart_json = fig.to_json()
        
        total = sum(values)
        avg = total / len(values) if values else 0
        
        return f"""
📊 **Relatório de Compras Mensais**

📅 Período: {months[0]} a {months[-1]}
📄 Total de notas: {len(invoices)}
💰 Valor total: R$ {total:,.2f}
📊 Média mensal: R$ {avg:,.2f}

🎨 Gráfico gerado (ver abaixo)

{chart_json}
"""

    def _generate_taxes_breakdown(self, db: DatabaseManager, days_back: int) -> str:
        """Generate tax breakdown pie chart."""
        invoices = db.search_invoices(days_back=days_back, limit=10000)
        
        if not invoices:
            return "📊 Nenhum documento encontrado no período especificado."
        
        # Aggregate taxes
        tax_totals = {
            "ICMS": sum(float(inv.tax_icms) for inv in invoices),
            "IPI": sum(float(inv.tax_ipi) for inv in invoices),
            "PIS": sum(float(inv.tax_pis) for inv in invoices),
            "COFINS": sum(float(inv.tax_cofins) for inv in invoices),
            "ISS": sum(float(inv.tax_issqn) for inv in invoices),
        }
        
        # Filter out zero values
        tax_totals = {k: v for k, v in tax_totals.items() if v > 0}
        
        if not tax_totals:
            return "📊 Nenhum imposto encontrado nos documentos."
        
        # Create Plotly pie chart
        fig = go.Figure(data=[
            go.Pie(
                labels=list(tax_totals.keys()),
                values=list(tax_totals.values()),
                textinfo='label+percent+value',
                texttemplate='%{label}<br>R$ %{value:,.2f}<br>(%{percent})',
                hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>',
            )
        ])
        
        fig.update_layout(
            title="💰 Breakdown de Impostos",
            template="plotly_white",
            height=400,
        )
        
        chart_json = fig.to_json()
        
        total_taxes = sum(tax_totals.values())
        
        result = f"""
📊 **Breakdown de Impostos**

📄 Documentos analisados: {len(invoices)}
💰 Total de impostos: R$ {total_taxes:,.2f}

**Detalhamento:**
"""
        
        for tax, value in sorted(tax_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (value / total_taxes * 100) if total_taxes > 0 else 0
            result += f"\n- {tax}: R$ {value:,.2f} ({percentage:.1f}%)"
        
        result += f"\n\n🎨 Gráfico gerado (ver abaixo)\n\n{chart_json}"
        
        return result

    def _generate_supplier_ranking(self, db: DatabaseManager, days_back: int) -> str:
        """Generate top suppliers ranking."""
        invoices = db.search_invoices(
            operation_type="purchase",
            days_back=days_back,
            limit=10000,
        )
        
        if not invoices:
            return "📊 Nenhuma compra encontrada no período especificado."
        
        # Aggregate by supplier
        supplier_totals = {}
        for inv in invoices:
            key = f"{inv.issuer_name} ({inv.issuer_cnpj})"
            supplier_totals[key] = supplier_totals.get(key, 0) + float(inv.total_invoice)
        
        # Get top 10
        top_suppliers = sorted(supplier_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not top_suppliers:
            return "📊 Nenhum fornecedor encontrado."
        
        suppliers = [s[0] for s in top_suppliers]
        values = [s[1] for s in top_suppliers]
        
        # Create horizontal bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=values,
                y=suppliers,
                orientation='h',
                marker_color='rgb(26, 118, 255)',
                text=[f"R$ {v:,.2f}" for v in values],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="🏢 Top 10 Fornecedores",
            xaxis_title="Valor Total (R$)",
            yaxis_title="Fornecedor",
            template="plotly_white",
            height=500,
            yaxis={'categoryorder': 'total ascending'},
        )
        
        chart_json = fig.to_json()
        
        total = sum(values)
        
        return f"""
📊 **Ranking de Fornecedores**

📅 Período: Últimos {days_back} dias
📄 Total de notas: {len(invoices)}
💰 Valor total: R$ {total:,.2f}

🎨 Gráfico gerado (ver abaixo)

{chart_json}
"""

    def _generate_invoices_timeline(self, db: DatabaseManager, days_back: int) -> str:
        """Generate daily invoice counts timeline."""
        invoices = db.search_invoices(days_back=days_back, limit=10000)
        
        if not invoices:
            return "📊 Nenhum documento encontrado no período especificado."
        
        # Aggregate by day
        daily_counts = {}
        for inv in invoices:
            day_key = inv.issue_date.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
        
        # Sort by date
        days = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in days]
        
        # Create line chart
        fig = go.Figure(data=[
            go.Scatter(
                x=days,
                y=counts,
                mode='lines+markers',
                marker_color='rgb(99, 110, 250)',
                line=dict(width=2),
                fill='tozeroy',
                fillcolor='rgba(99, 110, 250, 0.2)',
            )
        ])
        
        fig.update_layout(
            title="📊 Evolução Temporal de Documentos",
            xaxis_title="Data",
            yaxis_title="Quantidade de Notas",
            template="plotly_white",
            height=400,
        )
        
        chart_json = fig.to_json()
        
        total = len(invoices)
        avg = total / len(days) if days else 0
        
        return f"""
📊 **Timeline de Documentos Fiscais**

📅 Período: {days[0]} a {days[-1]}
📄 Total de documentos: {total}
📊 Média diária: {avg:.1f} documentos

🎨 Gráfico gerado (ver abaixo)

{chart_json}
"""

    async def _arun(self, report_type: str, days_back: int = 365) -> str:
        """Async version."""
        return self._run(report_type, days_back)


# ============================================================================
# 2. CLASSIFIER TOOL
# ============================================================================


class ClassifyInvoiceInput(BaseModel):
    """Input schema for classifier."""

    document_key: str = Field(
        ...,
        description="44-digit access key of the invoice to classify",
    )


class ClassifierTool(BaseTool):
    """
    Classify fiscal documents by operation type and cost center.
    
    Uses rule-based logic with LLM fallback for complex cases.
    """

    name: str = "classify_invoice"
    description: str = """
    Classify a fiscal document by operation type and cost center.
    
    Use this when user asks to:
    - "Classificar esta nota"
    - "Qual o centro de custo desta NF?"
    - "Esta é uma nota de compra ou venda?"
    
    Input: 44-digit access key (chave de acesso)
    Output: Operation type (purchase/sale/transfer/return) and cost center
    """
    args_schema: type[BaseModel] = ClassifyInvoiceInput

    def _run(self, document_key: str) -> str:
        """Classify invoice and return result."""
        try:
            db = DatabaseManager("sqlite:///fiscal_documents.db")
            
            # Find invoice by key
            invoices = db.search_invoices(limit=10000)
            invoice_db = next((inv for inv in invoices if inv.document_key == document_key), None)
            
            if not invoice_db:
                return f"❌ Documento com chave {document_key} não encontrado no banco de dados."
            
            # Convert to InvoiceModel for classification
            from src.models import InvoiceModel, InvoiceItem
            
            invoice = InvoiceModel(
                document_type=invoice_db.document_type,
                document_key=invoice_db.document_key,
                document_number=invoice_db.document_number,
                series=invoice_db.series,
                issue_date=invoice_db.issue_date,
                issuer_cnpj=invoice_db.issuer_cnpj,
                issuer_name=invoice_db.issuer_name,
                recipient_cnpj_cpf=invoice_db.recipient_cnpj_cpf,
                recipient_name=invoice_db.recipient_name,
                total_products=invoice_db.total_products,
                total_taxes=invoice_db.total_taxes,
                total_invoice=invoice_db.total_invoice,
                items=[],  # Simplified - items not needed for basic classification
            )
            
            # Classify
            classifier = DocumentClassifier(llm_client=None)
            result = classifier.classify(invoice)
            
            # Update database
            db.update_classification(
                document_key=document_key,
                operation_type=result.operation_type,
                cost_center=result.cost_center,
                confidence=result.confidence,
                reasoning=result.reasoning,
                used_llm_fallback=result.used_llm_fallback,
            )
            
            return f"""
✅ **Documento Classificado**

📄 Documento: {invoice.document_type} - {invoice.document_number}/{invoice.series}
🏢 Emitente: {invoice.issuer_name}

**Classificação:**
- 📦 Tipo de Operação: **{result.operation_type}**
- 🏷️ Centro de Custo: **{result.cost_center}**
- 📊 Confiança: **{result.confidence:.0%}**

**Raciocínio:**
{result.reasoning}

{"🤖 Classificação feita via LLM (caso complexo)" if result.used_llm_fallback else "✅ Classificação via regras (caso padrão)"}

💾 Classificação salva no banco de dados!
"""
        
        except Exception as e:
            logger.error(f"Error classifying invoice: {e}", exc_info=True)
            return f"❌ Erro ao classificar documento: {str(e)}"

    async def _arun(self, document_key: str) -> str:
        """Async version."""
        return self._run(document_key)


# ============================================================================
# 3. CNPJ VALIDATOR TOOL
# ============================================================================


class ValidateCNPJInput(BaseModel):
    """Input schema for CNPJ validator."""

    cnpj: str = Field(..., description="CNPJ to validate (with or without formatting)")


class CNPJValidatorTool(BaseTool):
    """
    Validate and retrieve CNPJ information from BrasilAPI.
    
    Returns company details: name, status, address, tax regime.
    """

    name: str = "validate_cnpj"
    description: str = """
    Validate CNPJ and retrieve company information from Receita Federal via BrasilAPI.
    
    Use this when user asks:
    - "Validar CNPJ 00.000.000/0001-00"
    - "Informações sobre este CNPJ"
    - "Qual a razão social deste CNPJ?"
    - "Este CNPJ está ativo?"
    
    Input: CNPJ (14 digits with or without formatting)
    Output: Company name, status, address, CNAE, tax info
    """
    args_schema: type[BaseModel] = ValidateCNPJInput

    def _run(self, cnpj: str) -> str:
        """Validate CNPJ and return company info."""
        try:
            validator = CNPJValidator(timeout=10.0)
            data = validator.validate_cnpj(cnpj)
            
            if not data:
                return f"❌ CNPJ {cnpj} não encontrado ou inválido."
            
            # Format address
            address = f"{data.logradouro}, {data.numero}"
            if data.complemento:
                address += f", {data.complemento}"
            address += f"\n   {data.bairro} - {data.municipio}/{data.uf}\n   CEP: {data.cep}"
            
            # Tax regime
            regime = []
            if data.simples_nacional:
                regime.append("Simples Nacional")
            if data.mei:
                regime.append("MEI")
            if not regime:
                regime.append("Lucro Presumido/Real")
            
            return f"""
✅ **CNPJ Validado**

🏢 **{data.razao_social}**
{f"   ({data.nome_fantasia})" if data.nome_fantasia else ""}

📋 CNPJ: {data.cnpj}
📊 Situação: **{data.situacao}**

**Informações Cadastrais:**
- 📅 Data de Abertura: {data.data_abertura}
- 🏛️ Natureza Jurídica: {data.natureza_juridica}
- 📏 Porte: {data.porte}
- 💰 Capital Social: R$ {data.capital_social:,.2f}

**Atividade Principal:**
- 📊 CNAE: {data.cnae_fiscal}
- 📝 {data.cnae_fiscal_descricao}

**Regime Tributário:**
- {', '.join(regime)}

**Endereço:**
   {address}

**Contato:**
{f"   📧 Email: {data.email}" if data.email else ""}
{f"   📞 Telefone: {data.telefone}" if data.telefone else ""}

✅ Dados obtidos da Receita Federal via BrasilAPI
"""
        
        except Exception as e:
            logger.error(f"Error validating CNPJ: {e}", exc_info=True)
            return f"❌ Erro ao validar CNPJ {cnpj}: {str(e)}"

    async def _arun(self, cnpj: str) -> str:
        """Async version."""
        return self._run(cnpj)


# ============================================================================
# 4. CEP VALIDATOR TOOL
# ============================================================================


class ValidateCEPInput(BaseModel):
    """Input schema for CEP validator."""

    cep: str = Field(..., description="CEP to validate (with or without formatting)")


class CEPValidatorTool(BaseTool):
    """
    Validate and retrieve address information from ViaCEP.
    
    Returns complete address: street, neighborhood, city, state.
    """

    name: str = "validate_cep"
    description: str = """
    Validate CEP and retrieve address information via ViaCEP.
    
    Use this when user asks:
    - "Validar CEP 01310-100"
    - "Qual o endereço deste CEP?"
    - "Onde fica este CEP?"
    
    Input: CEP (8 digits with or without formatting)
    Output: Complete address (street, neighborhood, city, state)
    """
    args_schema: type[BaseModel] = ValidateCEPInput

    def _run(self, cep: str) -> str:
        """Validate CEP and return address."""
        try:
            validator = CEPValidator(timeout=5.0)
            data = validator.validate_cep(cep)
            
            if not data:
                return f"❌ CEP {cep} não encontrado ou inválido."
            
            return f"""
✅ **CEP Validado**

📍 **{data.get('logradouro', 'N/A')}**
   {data.get('bairro', 'N/A')}
   {data.get('localidade', 'N/A')}/{data.get('uf', 'N/A')}
   CEP: {data.get('cep', cep)}

**Código IBGE:** {data.get('ibge', 'N/A')}
{f"**Complemento:** {data.get('complemento')}" if data.get('complemento') else ""}

✅ Dados obtidos via ViaCEP
"""
        
        except Exception as e:
            logger.error(f"Error validating CEP: {e}", exc_info=True)
            return f"❌ Erro ao validar CEP {cep}: {str(e)}"

    async def _arun(self, cep: str) -> str:
        """Async version."""
        return self._run(cep)


# ============================================================================
# 5. NCM LOOKUP TOOL
# ============================================================================


class LookupNCMInput(BaseModel):
    """Input schema for NCM lookup."""

    ncm: str = Field(..., description="NCM code to lookup (8 digits)")


class NCMLookupTool(BaseTool):
    """
    Lookup NCM code description and tax information.
    
    Returns product classification and IPI rate.
    """

    name: str = "lookup_ncm"
    description: str = """
    Lookup NCM code description and tax information.
    
    Use this when user asks:
    - "O que é NCM 84713012?"
    - "Qual a descrição do NCM 22030000?"
    - "Qual a alíquota de IPI deste NCM?"
    
    Input: NCM code (8 digits)
    Output: Description and IPI rate if available
    """
    args_schema: type[BaseModel] = LookupNCMInput

    def _run(self, ncm: str) -> str:
        """Lookup NCM and return description."""
        try:
            validator = NCMValidator()
            
            # Validate NCM format
            if not ncm.isdigit() or len(ncm) != 8:
                return f"❌ NCM inválido: {ncm}. Deve conter 8 dígitos."
            
            # Check if NCM exists in table
            if not validator.is_valid_ncm(ncm):
                return f"""
⚠️ **NCM {ncm} não encontrado na tabela local**

💡 **Dica:** Este NCM pode existir mas não está na base de dados atual.

📚 Para classificação completa, consulte:
- TIPI (Tabela de Incidência do IPI): https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/tributos/tipi
- IBGE CONCLA: https://concla.ibge.gov.br/classificacoes/por-tema/produtos
"""
            
            # Get NCM info
            ncm_info = validator._ncm_table.get(ncm, {})
            description = ncm_info.get("description", "Descrição não disponível")
            ipi_rate = ncm_info.get("ipi_rate", "N/A")
            
            # NCM hierarchy (2-4-6-8 digits)
            chapter = ncm[:2]
            position = ncm[:4]
            subposition = ncm[:6]
            item = ncm
            
            return f"""
✅ **NCM {ncm} Encontrado**

📦 **{description}**

**Hierarquia:**
- 📖 Capítulo: {chapter}
- 📋 Posição: {position}
- 📝 Subposição: {subposition}
- 🏷️ Item: {item}

💰 **Alíquota IPI:** {ipi_rate}%

💡 **Informações:**
- NCM = Nomenclatura Comum do Mercosul
- Usado para classificação de produtos e tributação
- Baseado no Sistema Harmonizado (SH) internacional

✅ Dados obtidos da tabela NCM local ({len(validator._ncm_table)} códigos)
"""
        
        except Exception as e:
            logger.error(f"Error looking up NCM: {e}", exc_info=True)
            return f"❌ Erro ao consultar NCM {ncm}: {str(e)}"

    async def _arun(self, ncm: str) -> str:
        """Async version."""
        return self._run(ncm)


# ============================================================================
# TOOL INSTANCES
# ============================================================================

report_generator_tool = ReportGeneratorTool()
classifier_tool = ClassifierTool()
cnpj_validator_tool = CNPJValidatorTool()
cep_validator_tool = CEPValidatorTool()
ncm_lookup_tool = NCMLookupTool()

# Export all tools
ALL_BUSINESS_TOOLS = [
    report_generator_tool,
    classifier_tool,
    cnpj_validator_tool,
    cep_validator_tool,
    ncm_lookup_tool,
]
