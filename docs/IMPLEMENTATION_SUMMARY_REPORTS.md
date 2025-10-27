# 📊 Sistema de Relatórios CSV/XLSX - Resumo da Implementação

## ✅ O Que Foi Implementado

### 1. **Gerador de Relatórios (`src/services/report_generator.py`)**

Um serviço completo para gerar relatórios Excel/CSV com visualizações, incluindo:

- **18 tipos de relatórios** organizados em 5 categorias:

  - ✅ Validação (5 relatórios)
  - ✅ Financeiros (4 relatórios)
  - ✅ Operacionais (3 relatórios)
  - ✅ Classificação (4 relatórios)
  - ✅ Produtos/Itens (3 relatórios)

- **Sistema de filtros flexível** (`ReportFilters`):

  - Período (start_date, end_date, days_back)
  - Tipo de documento (NFe, NFCe, CTe, MDFe)
  - Tipo de operação (purchase, sale, transfer, return)
  - Gravidade (error, warning, info)
  - CNPJ do emitente (busca parcial)
  - Centro de custo

- **Formatos de saída**:

  - Excel (.xlsx) com openpyxl
  - CSV (.csv) para compatibilidade universal
  - Gráficos PNG (.png) com matplotlib

- **Metadados ricos**:
  - Total de documentos, valor total, estatísticas específicas
  - Informações sobre filtros aplicados
  - Timestamps de geração

### 2. **Ferramenta LangChain (`src/agent/report_tool.py`)**

Integração com o agente LLM para aceitar **comandos em linguagem natural**:

- **Suporte bilíngue** (Português e Inglês)
- **Parsing inteligente** de queries:

  - Detecção automática de tipo de relatório
  - Extração de filtros de data (meses, anos, períodos)
  - Mapeamento de termos (compra→purchase, venda→sale, etc.)
  - Suporte a padrões como "entre X e Y", "últimos N dias"

- **Exemplos de queries aceitas**:
  ```
  "relatório de xmls com falhas entre janeiro e março"
  "relatório de falhas do mês de janeiro de 2024"
  "top 10 fornecedores por valor nos últimos 90 dias"
  "cache effectiveness report"
  "report of documents with errors severity error"
  ```

### 3. **UI Streamlit (`src/ui/components/reports_tab.py`)**

Interface visual completa na tab "📈 Reports":

- **Seleção de relatórios** por categoria
- **Configuração de filtros** visual e intuitiva
- **Opções de formato** (XLSX/CSV) e gráficos
- **Download direto** dos arquivos gerados
- **Visualização de gráficos** inline
- **Seção de ajuda** com exemplos e documentação

### 4. **Integração com Agente**

- Tool `generate_fiscal_report` adicionada a `ALL_TOOLS`
- Agente pode processar comandos de relatórios via chat
- Retorna feedback estruturado com paths e metadados

### 5. **Documentação Completa**

- **`/docs/REPORTS.md`**: Guia completo de uso

  - Lista de todos os relatórios disponíveis
  - Exemplos em Python, Chat e UI
  - Casos de uso reais
  - Troubleshooting

- **`/examples/demo_reports.py`**: Script demonstrativo
  - 8 exemplos práticos
  - Diferentes tipos de relatórios
  - Diferentes combinações de filtros

## 📋 Lista Completa de Relatórios

### Validação

1. ✅ **Documents with Issues** - XMLs com problemas
2. ✅ **Documents without Issues** - XMLs aprovados
3. ✅ **Issues by Type** - Problemas por tipo de erro
4. ✅ **Issues by Issuer** - Problemas por fornecedor
5. ✅ **Issues by Severity** - Problemas por gravidade

### Financeiros

6. ✅ **Taxes by Period** - Impostos detalhados (ICMS, IPI, PIS, COFINS, ISS)
7. ✅ **Total Value by Period** - Valor total por mês
8. ✅ **Top Suppliers by Value** - Principais fornecedores
9. ✅ **Costs by Cost Center** - Custos por centro

### Operacionais

10. ✅ **Documents by Operation Type** - Por tipo de operação
11. ✅ **Documents by Document Type** - Por tipo de documento
12. ✅ **Volume by Period** - Volume mensal

### Classificação

13. ✅ **Cache Effectiveness** - Efetividade do cache
14. ✅ **Unclassified Documents** - Documentos sem classificação
15. ✅ **Classification by Cost Center** - Por centro de custo
16. ✅ **LLM Fallback Usage** - Uso de fallback LLM

### Produtos/Itens

17. ✅ **Top Products by NCM** - Produtos mais comprados
18. ✅ **Analysis by CFOP** - Análise por CFOP
19. ✅ **Items with Issues** - Itens de docs problemáticos

## 🎯 Casos de Uso Implementados

### 1. Auditoria Fiscal

```python
# Relatório de impostos de compras do mês
filters = ReportFilters(
    start_date=datetime(2024, 10, 1),
    end_date=datetime(2024, 10, 31),
    operation_type="purchase",
)
result = generator.generate_report(
    ReportType.TAXES_BY_PERIOD, filters
)
```

**Chat**: `"relatório de impostos de compras de outubro de 2024"`

### 2. Análise de Fornecedores

```python
# Top fornecedores dos últimos 6 meses
filters = ReportFilters(days_back=180)
result = generator.generate_report(
    ReportType.TOP_SUPPLIERS_BY_VALUE, filters
)
```

**Chat**: `"top fornecedores nos últimos 6 meses"`

### 3. Correção de Erros

```python
# Documentos com erros críticos
filters = ReportFilters(severity="error", days_back=30)
result = generator.generate_report(
    ReportType.DOCUMENTS_WITH_ISSUES, filters
)
```

**Chat**: `"documentos com erros nos últimos 30 dias"`

### 4. Análise de Custos

```python
# Distribuição por centro de custo
filters = ReportFilters(operation_type="purchase", days_back=90)
result = generator.generate_report(
    ReportType.COSTS_BY_CENTER, filters
)
```

**Chat**: `"custos por centro de custo nos últimos 90 dias"`

### 5. Performance do Sistema

```python
# Efetividade do cache (sem filtros)
result = generator.generate_report(
    ReportType.CACHE_EFFECTIVENESS, ReportFilters()
)
```

**Chat**: `"efetividade do cache"`

## 🔧 Arquitetura

```
┌─────────────────┐
│  Streamlit UI   │ (reports_tab.py)
└────────┬────────┘
         │
         ├─────────────┐
         │             │
┌────────▼────────┐ ┌─▼──────────────┐
│ LangChain Agent │ │ DatabaseManager│
│  (report_tool)  │ └─┬──────────────┘
└────────┬────────┘   │
         │            │
         └────┬───────┘
              │
     ┌────────▼─────────┐
     │ ReportGenerator  │
     │  - 18 reports    │
     │  - Filters       │
     │  - Charts        │
     └────────┬─────────┘
              │
     ┌────────▼─────────┐
     │  Output Files    │
     │  - XLSX/CSV      │
     │  - PNG charts    │
     └──────────────────┘
```

## 📊 Exemplos de Outputs

### Metadados Retornados

```python
{
    "report_type": "documents_with_issues",
    "file_path": "reports/documents_with_issues_20241027_143022.xlsx",
    "chart_path": "reports/documents_with_issues_20241027_143022.png",
    "row_count": 42,
    "generated_at": "2024-10-27T14:30:22",
    "filters": {
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-03-31T23:59:59",
        "severity": "error",
        ...
    },
    "total_documents": 42,
    "total_value": 125000.50,
}
```

### Estrutura de Arquivo Excel

```
Documento | Data       | Emitente      | CNPJ           | Valor     | Issues
----------|------------|---------------|----------------|-----------|-------
NFe 123   | 2024-01-15 | Fornecedor A  | 12.345.678/... | R$ 1.500  | 3
NFe 124   | 2024-01-20 | Fornecedor B  | 98.765.432/... | R$ 2.300  | 1
...
```

### Gráfico Gerado

```
Gráfico de barras mostrando:
- Eixo X: Tipos de problemas (VAL001, VAL002, etc.)
- Eixo Y: Quantidade de ocorrências
- Título: "Issues by Type"
- Formato: PNG, 150 DPI
```

## 🚀 Como Usar

### Via UI (Streamlit)

1. Inicie a aplicação: `streamlit run src/ui/app.py`
2. Acesse a aba **"📈 Reports"**
3. Selecione relatório e filtros
4. Clique em **"📊 Generate Report"**
5. Baixe os arquivos gerados

### Via Chat (Agente)

1. Acesse a aba **"💬 Chat"**
2. Digite comando em português ou inglês:
   - `"relatório de falhas de janeiro"`
   - `"top 10 suppliers last 90 days"`
3. Agente gera relatório e retorna paths

### Via Python

```python
from src.database.db import DatabaseManager
from src.services.report_generator import (
    ReportGenerator,
    ReportFilters,
    ReportType,
)

db = DatabaseManager()
generator = ReportGenerator(db)

filters = ReportFilters(days_back=30)
result = generator.generate_report(
    ReportType.DOCUMENTS_WITH_ISSUES,
    filters,
)

print(result['file_path'])
```

## 🎨 Features Especiais

### 1. Suporte Bilíngue

- Comandos em **português** ou **inglês**
- Parsing automático de meses, períodos, termos
- Sistema interno em inglês para consistência

### 2. Visualizações Automáticas

- Gráficos gerados automaticamente quando relevante
- Tipos: barras, linhas, horizontais
- Alta qualidade (150 DPI)

### 3. Metadados Ricos

- Estatísticas específicas por tipo de relatório
- Filtros aplicados documentados
- Timestamps para auditoria

### 4. Extensibilidade

- Fácil adicionar novos tipos de relatórios
- Sistema modular de filtros
- Separação clara de responsabilidades

## 📦 Dependências

Já incluídas em `requirements.txt`:

```
pandas>=2.1.0        # DataFrames
openpyxl>=3.1.0      # Excel files
matplotlib>=3.8.0    # Charts
```

## ✅ Testes

Para testar o sistema:

```bash
# 1. Via script de exemplo
python examples/demo_reports.py

# 2. Via UI
streamlit run src/ui/app.py
# Acesse tab "📈 Reports"

# 3. Via chat
streamlit run src/ui/app.py
# Acesse tab "💬 Chat"
# Digite: "relatório de documentos com falhas"
```

## 📚 Documentação

- **Guia completo**: `/docs/REPORTS.md`
- **Exemplos**: `/examples/demo_reports.py`
- **Código fonte**:
  - `/src/services/report_generator.py`
  - `/src/agent/report_tool.py`
  - `/src/ui/components/reports_tab.py`

## 🎯 Próximos Passos (Sugestões)

1. **Relatórios agendados**: Cron jobs para gerar relatórios periodicamente
2. **Email delivery**: Enviar relatórios por email automaticamente
3. **Dashboards interativos**: Plotly para gráficos interativos
4. **Relatórios customizados**: UI para criar relatórios via drag-and-drop
5. **Exportação PDF**: Adicionar formato PDF com formatação profissional
6. **Templates**: Salvar configurações de relatórios favoritos
7. **Comparativos**: Comparar períodos diferentes no mesmo relatório

## 🎉 Conclusão

Sistema completo de relatórios implementado com:

- ✅ 18+ tipos de relatórios relevantes
- ✅ Interface visual (Streamlit)
- ✅ Comandos de linguagem natural (PT/EN)
- ✅ API Python programática
- ✅ Filtros flexíveis
- ✅ Múltiplos formatos de saída (XLSX, CSV, PNG)
- ✅ Documentação completa
- ✅ Exemplos de uso

O usuário pode agora:

1. Gerar relatórios via UI clicando em botões
2. Pedir relatórios via chat em português ou inglês
3. Integrar geração de relatórios em scripts Python
4. Aplicar filtros complexos por período, tipo, operação, etc.
5. Baixar arquivos Excel/CSV profissionais
6. Visualizar gráficos automaticamente gerados
