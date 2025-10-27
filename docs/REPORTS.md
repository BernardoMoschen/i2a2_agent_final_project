# 📊 Sistema de Relatórios - Documentação

## Visão Geral

O sistema de relatórios permite gerar arquivos Excel/CSV e visualizações a partir dos documentos fiscais processados, suportando consultas em linguagem natural tanto em **inglês** quanto em **português**.

## 📋 Relatórios Disponíveis

### 1. Relatórios de Validação

| Relatório                    | Descrição                                 | Casos de Uso                                 |
| ---------------------------- | ----------------------------------------- | -------------------------------------------- |
| **Documents with Issues**    | Documentos com problemas de validação     | Identificar XMLs problemáticos para correção |
| **Documents without Issues** | Documentos aprovados sem problemas        | Verificar XMLs processados corretamente      |
| **Issues by Type**           | Agrupamento de problemas por tipo de erro | Identificar erros mais comuns                |
| **Issues by Issuer**         | Problemas agrupados por fornecedor        | Identificar fornecedores com mais erros      |
| **Issues by Severity**       | Problemas agrupados por gravidade         | Priorizar correções (erro/warning/info)      |

### 2. Relatórios Financeiros

| Relatório                  | Descrição                               | Casos de Uso                                 |
| -------------------------- | --------------------------------------- | -------------------------------------------- |
| **Taxes by Period**        | Detalhamento de impostos por período    | Análise fiscal (ICMS, IPI, PIS, COFINS, ISS) |
| **Total Value by Period**  | Valor total processado por mês          | Acompanhamento de volume financeiro          |
| **Top Suppliers by Value** | Principais fornecedores por valor       | Análise de concentração de compras           |
| **Costs by Cost Center**   | Custos distribuídos por centro de custo | Controle de despesas por setor               |

### 3. Relatórios Operacionais

| Relatório             | Descrição                               | Casos de Uso                          |
| --------------------- | --------------------------------------- | ------------------------------------- |
| **By Operation Type** | Documentos por tipo de operação         | Separar compras/vendas/transferências |
| **By Document Type**  | Documentos por tipo (NFe/NFCe/CTe/MDFe) | Análise por modal fiscal              |
| **Volume by Period**  | Volume de documentos por mês            | Acompanhamento de processamento       |

### 4. Relatórios de Classificação

| Relatório                  | Descrição                              | Casos de Uso                             |
| -------------------------- | -------------------------------------- | ---------------------------------------- |
| **Cache Effectiveness**    | Efetividade do cache de classificações | Economia de custos LLM                   |
| **Unclassified Documents** | Documentos sem classificação           | Identificar XMLs que precisam de atenção |
| **LLM Fallback Usage**     | Uso de fallback LLM                    | Monitorar quando modelo ML falhou        |
| **By Cost Center**         | Classificações por centro de custo     | Distribuição de operações                |

### 5. Relatórios de Produtos/Itens

| Relatório               | Descrição                         | Casos de Uso                |
| ----------------------- | --------------------------------- | --------------------------- |
| **Top Products by NCM** | Produtos mais comprados por NCM   | Análise de compras          |
| **Analysis by CFOP**    | Análise por CFOP                  | Entender tipos de operações |
| **Items with Issues**   | Itens de documentos com problemas | Produtos que causam erros   |

## 🎯 Exemplos de Uso

### Via Interface (Streamlit)

1. Acesse a aba **"📈 Reports"**
2. Escolha a **categoria** e **tipo de relatório**
3. Configure **filtros** (período, tipo de documento, operação, etc.)
4. Selecione **formato** (XLSX ou CSV) e se deseja **gráfico**
5. Clique em **"📊 Generate Report"**
6. Faça **download** dos arquivos gerados

### Via Agente (Chat)

O agente aceita comandos em **português** ou **inglês**:

#### Português:

```
"gere um relatório de XMLs com falhas entre janeiro e março"
"relatório de falhas do mês de janeiro de 2024"
"relatório de impostos do ano de 2024"
"top 10 fornecedores por valor nos últimos 90 dias"
"efetividade do cache de classificações"
"documentos não classificados"
```

#### English:

```
"generate report of xmls with issues between january and march"
"report of issues from january 2024"
"tax report for 2024"
"top 10 suppliers by value in the last 90 days"
"cache effectiveness report"
"unclassified documents report"
```

### Via API Python

```python
from src.database.db import DatabaseManager
from src.services.report_generator import (
    ReportGenerator,
    ReportFilters,
    ReportType,
)
from datetime import datetime, timedelta

# Inicializar
db = DatabaseManager()
generator = ReportGenerator(db)

# Exemplo 1: Relatório de falhas do último mês
filters = ReportFilters(
    days_back=30,
    severity="error",
)

result = generator.generate_report(
    report_type=ReportType.DOCUMENTS_WITH_ISSUES,
    filters=filters,
    output_format="xlsx",
    include_chart=True,
)

print(f"Relatório gerado: {result['file_path']}")
print(f"Total de documentos: {result['total_documents']}")
print(f"Valor total: R$ {result['total_value']:,.2f}")

# Exemplo 2: Top fornecedores de 2024
filters = ReportFilters(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
)

result = generator.generate_report(
    report_type=ReportType.TOP_SUPPLIERS_BY_VALUE,
    filters=filters,
    output_format="xlsx",
)

# Exemplo 3: Impostos de compras nos últimos 90 dias
filters = ReportFilters(
    days_back=90,
    operation_type="purchase",
)

result = generator.generate_report(
    report_type=ReportType.TAXES_BY_PERIOD,
    filters=filters,
)
```

## 🔍 Filtros Disponíveis

| Filtro           | Tipo     | Descrição                                |
| ---------------- | -------- | ---------------------------------------- |
| `start_date`     | datetime | Data inicial do período                  |
| `end_date`       | datetime | Data final do período                    |
| `days_back`      | int      | Últimos N dias (alternativa a start/end) |
| `document_type`  | str      | NFe, NFCe, CTe, MDFe                     |
| `operation_type` | str      | purchase, sale, transfer, return         |
| `issuer_cnpj`    | str      | CNPJ do emitente (busca parcial)         |
| `severity`       | str      | error, warning, info                     |
| `cost_center`    | str      | Centro de custo específico               |

## 📊 Formatos de Saída

### Excel (.xlsx)

- Formatação profissional
- Múltiplas planilhas (futuro)
- Fórmulas e totalizadores
- Compatível com Excel, LibreOffice, Google Sheets

### CSV (.csv)

- Formato universal
- Importável em qualquer ferramenta
- Menor tamanho de arquivo
- Ideal para integração com outras ferramentas

### Gráficos (.png)

- Visualizações automáticas
- Gráficos de barra, linha, pizza
- Alta resolução (150 DPI)
- Prontos para apresentações

## 🎨 Personalização via Linguagem Natural

O sistema de parsing de linguagem natural suporta:

### Períodos

- **Português**: "janeiro", "fevereiro", "entre março e junho", "últimos 30 dias", "ano de 2024"
- **English**: "january", "february", "between march and june", "last 30 days", "year 2024"

### Tipos de Documento

- "NFe", "NFCe", "CTe", "MDFe"

### Tipos de Operação

- **Português**: "compra", "venda", "transferência", "devolução"
- **English**: "purchase", "sale", "transfer", "return"

### Gravidade

- **Português**: "erro", "aviso", "info"
- **English**: "error", "warning", "info"

## 📂 Estrutura de Arquivos Gerados

Os relatórios são salvos em:

```
/reports/
  ├── documents_with_issues_20241027_143022.xlsx
  ├── documents_with_issues_20241027_143022.png
  ├── top_suppliers_by_value_20241027_144512.xlsx
  ├── top_suppliers_by_value_20241027_144512.png
  └── ...
```

Formato do nome: `{report_type}_{timestamp}.{extension}`

## 🚀 Casos de Uso Reais

### 1. Auditoria Fiscal Mensal

```python
# Gerar relatório de impostos do mês passado
filters = ReportFilters(
    start_date=datetime(2024, 10, 1),
    end_date=datetime(2024, 10, 31),
    operation_type="purchase",
)

result = generator.generate_report(
    report_type=ReportType.TAXES_BY_PERIOD,
    filters=filters,
)
```

**Comando de chat**: `"relatório de impostos de compras de outubro de 2024"`

### 2. Análise de Fornecedores

```python
# Top 20 fornecedores dos últimos 6 meses
filters = ReportFilters(days_back=180)

result = generator.generate_report(
    report_type=ReportType.TOP_SUPPLIERS_BY_VALUE,
    filters=filters,
)
```

**Comando de chat**: `"top fornecedores nos últimos 6 meses"`

### 3. Correção de Erros

```python
# Documentos com erros críticos
filters = ReportFilters(
    severity="error",
    days_back=30,
)

result = generator.generate_report(
    report_type=ReportType.DOCUMENTS_WITH_ISSUES,
    filters=filters,
)
```

**Comando de chat**: `"documentos com erros nos últimos 30 dias"`

### 4. Análise de Custos por Setor

```python
# Distribuição de custos por centro de custo
filters = ReportFilters(
    operation_type="purchase",
    days_back=90,
)

result = generator.generate_report(
    report_type=ReportType.COSTS_BY_CENTER,
    filters=filters,
)
```

**Comando de chat**: `"custos por centro de custo nos últimos 90 dias"`

### 5. Eficiência do Sistema

```python
# Cache effectiveness (sem filtros)
result = generator.generate_report(
    report_type=ReportType.CACHE_EFFECTIVENESS,
    filters=ReportFilters(),
)
```

**Comando de chat**: `"efetividade do cache"`

## 🔧 Extensibilidade

### Adicionar Novo Tipo de Relatório

1. Adicione constante em `ReportType`:

```python
NEW_REPORT_TYPE = "new_report_type"
```

2. Implemente método no `ReportGenerator`:

```python
def _report_new_type(
    self, filters: ReportFilters
) -> Tuple[pd.DataFrame, Dict]:
    # Sua lógica aqui
    with Session(self.db.engine) as session:
        # Query database
        ...

    df = pd.DataFrame(data)
    metadata = {"custom_metric": value}

    return df, metadata
```

3. Registre no dicionário `report_methods`:

```python
report_methods = {
    ...
    ReportType.NEW_REPORT_TYPE: self._report_new_type,
}
```

4. Adicione parsing de linguagem natural em `report_tool.py`:

```python
elif any(word in query_lower for word in ["new type", "novo tipo"]):
    report_type = ReportType.NEW_REPORT_TYPE
```

## 📈 Métricas e Metadados

Cada relatório retorna metadados úteis:

```python
{
    "report_type": "documents_with_issues",
    "file_path": "reports/documents_with_issues_20241027_143022.xlsx",
    "chart_path": "reports/documents_with_issues_20241027_143022.png",
    "row_count": 42,
    "generated_at": "2024-10-27T14:30:22",
    "filters": {...},
    "total_documents": 42,  # Específico do relatório
    "total_value": 125000.50,  # Específico do relatório
}
```

## 🛡️ Segurança e Privacidade

- Dados sensíveis (CNPJ completo, razão social) podem ser redactados via configuração
- Relatórios salvos localmente (não enviados para cloud)
- Logs não incluem dados de PII por padrão
- Suporte para filtros específicos para compliance (LGPD/GDPR)

## 💡 Dicas de Performance

1. **Use filtros**: Relatórios menores são gerados mais rápido
2. **Desabilite gráficos**: Para grandes volumes, gere apenas Excel/CSV
3. **Batch processing**: Para múltiplos relatórios, use loop Python
4. **Cache**: Sistema automático de cache de classificações economiza LLM calls

## ❓ Troubleshooting

### Relatório vazio

- Verifique se há documentos no período filtrado
- Use "All Time" para ver se há dados no banco
- Confirme que filtros estão corretos

### Gráfico não gerado

- Verifique se matplotlib está instalado: `pip install matplotlib`
- Confirme que há dados suficientes (mínimo 1 linha)

### Erro de permissão no arquivo

- Verifique se pasta `reports/` existe e tem permissão de escrita
- Fecha arquivo se estiver aberto no Excel

### Query em português não funciona

- Verifique ortografia dos meses
- Use acentuação correta: "março", não "marco"

## 📞 Suporte

Para dúvidas ou sugestões sobre o sistema de relatórios:

- GitHub Issues: [link]
- Documentação completa: `/docs/REPORTS.md`
- Exemplos adicionais: `/examples/demo_reports.py`
