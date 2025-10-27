# 🤖 Agente Fiscal - Guia Rápido de Consultas

## Status: ✅ OPERACIONAL

O agente está pronto para uso via chat em **Português** ou **Inglês**!

---

## 🎯 13 Ferramentas Disponíveis

| # | Ferramenta | Quando Usar | Exemplo |
|---|-----------|-------------|---------|
| 1 | `parse_fiscal_xml` | Parse de XMLs fiscais | "Parse este XML da NFe" |
| 2 | `validate_fiscal_document` | Validar regras fiscais | "Valide este documento" |
| 3 | `search_invoices_database` | Buscar notas no BD | "Busque notas de compra com falhas" |
| 4 | `get_database_statistics` | Estatísticas do BD | "Mostre stats do banco" |
| 5 | `fiscal_report_export` | Relatórios CSV/XLSX | "Gere relatório Excel de impostos" |
| 6 | `generate_report` | Gráficos interativos | "Mostre gráfico de vendas" |
| 7 | `classify_invoice` | Classificar operação | "Classifique este documento" |
| 8 | `validate_cnpj` | Validar CNPJ | "Valide CNPJ 12.345.678/0001-90" |
| 9 | `validate_cep` | Validar CEP | "Valide CEP 01310-100" |
| 10 | `lookup_ncm` | Consultar NCM | "O que é NCM 84714900?" |
| 11 | `fiscal_knowledge` | Perguntas fiscais | "O que é CFOP 5102?" |
| 12 | `archive_invoice` | Arquivar documento | "Arquive esta nota" |
| 13 | `archive_all_invoices` | Arquivar em lote | "Arquive todas de 2024" |

---

## 💬 Consultas Prontas para Testar

### 📊 Relatórios CSV/XLSX (ferramenta: `fiscal_report_export`)

```
Gere um relatório de documentos com falhas do mês de janeiro de 2024
```
```
Create an Excel report of taxes by period for the last quarter
```
```
Exportar para CSV todos os impostos entre março e junho
```
```
Top 10 suppliers by value in last 90 days
```
```
Relatório de documentos sem falhas de 2024
```

### 📈 Gráficos Interativos (ferramenta: `generate_report`)

```
Mostre um gráfico de breakdown de impostos
```
```
Show me sales by month chart
```
```
Gere gráfico de ranking de fornecedores
```
```
Create purchases timeline visualization
```

### 🔍 Busca no Banco de Dados

```
Busque todas as notas fiscais de compra
```
```
Search for invoices with issues from supplier CNPJ 12.345.678/0001-90
```
```
Mostre estatísticas do banco de dados
```
```
Find all documents processed in January 2024
```

### ✓ Validações

```
Valide o CNPJ 12.345.678/0001-90
```
```
Validate CEP 01310-100
```
```
Lookup NCM code 84714900
```
```
O que é CFOP 5102?
```

### 🔗 Consultas Multi-Ferramentas (Complexas)

```
Busque notas de compra com falhas e exporte para Excel
```
```
Valide este CNPJ e mostre todas as notas dele
```
```
Gere relatório de impostos de janeiro e crie um gráfico
```
```
Parse este XML, valide e classifique o tipo de operação
```
```
Top 10 fornecedores, valide os CNPJs e mostre gráfico de evolução
```

---

## 📋 18 Tipos de Relatórios Disponíveis

### Validação (5)
- `documents_with_issues` - Documentos com falhas
- `documents_without_issues` - Documentos sem falhas  
- `issues_by_type` - Falhas por tipo
- `issues_by_issuer` - Falhas por fornecedor
- `issues_by_severity` - Falhas por gravidade

### Financeiro (4)
- `taxes_by_period` - Impostos por período
- `total_value_by_period` - Valor total por período
- `top_suppliers_by_value` - Top fornecedores por valor
- `costs_by_center` - Custos por centro

### Operacional (3)
- `documents_by_operation_type` - Por tipo de operação
- `documents_by_document_type` - Por tipo de documento
- `volume_by_period` - Volume por período

### Classificação (4)
- `cache_effectiveness` - Efetividade do cache
- `unclassified_documents` - Documentos não classificados
- `classification_by_cost_center` - Por centro de custo
- `llm_fallback_usage` - Uso de fallback LLM

### Produtos (3)
- `top_products_by_ncm` - Top produtos por NCM
- `analysis_by_cfop` - Análise por CFOP
- `items_with_issues` - Itens com problemas

---

## 🎨 Filtros Suportados

### Datas
```
"do mês de janeiro de 2024"
"between January and March 2024"
"nos últimos 30 dias"
"in the last 90 days"
"entre 01/01/2024 e 31/03/2024"
```

### Tipos de Operação
```
"de compra" / "purchase"
"de venda" / "sale"
"de serviço" / "service"
```

### Tipos de Documento
```
"NFe"
"NFCe"
"CTe"
"MDFe"
```

### Gravidade de Falhas
```
"error" / "erro"
"warning" / "aviso"
```

### Outros
```
"CNPJ 12.345.678/0001-90"
"centro de custo X"
"top 10"
"limit 50"
```

---

## 🚀 Como Usar

### Via Streamlit (Interface Web)
```bash
streamlit run src/ui/app.py
```
1. Insira chave API Gemini
2. Vá para aba "💬 Chat"
3. Digite suas consultas
4. Aguarde resposta do agente

### Via Demo Interativo
```bash
python examples/demo_agent_chat.py --api-key SUA_CHAVE
```
Comandos dentro do demo:
- `help` - Mostrar exemplos
- `tools` - Listar ferramentas
- `quit` - Sair

### Via Código Python
```python
from src.agent.agent_core import create_agent

agent = create_agent(api_key="...", model_name="gemini-2.0-flash-exp")
response = agent.process_query("Sua consulta aqui")
print(response)
```

---

## 💡 Dicas de Uso

### ✅ Boas Práticas
- Seja específico nos filtros de data
- Use termos em PT ou EN, mas consistentemente
- Para relatórios, especifique o formato desejado (CSV/XLSX)
- Para gráficos, mencione "gráfico" ou "chart"

### ⚠️ Evite
- Misturar PT e EN na mesma frase
- Filtros muito vagos ("alguns documentos")
- Nomes de campos incorretos

### 🔧 Se o agente não entender
- Reformule a pergunta
- Adicione mais contexto
- Especifique a ferramenta: "use fiscal_report_export para..."
- Consulte `help` para exemplos

---

## 📚 Documentação Completa

- **Verificação (PT):** `docs/VERIFICACAO_AGENTE.md`
- **Verificação (EN):** `docs/AGENT_VERIFICATION.md`
- **Sistema de Relatórios:** `docs/REPORTS.md`
- **Implementação Técnica:** `docs/IMPLEMENTATION_SUMMARY_REPORTS.md`

---

## 🧪 Teste Rápido

Execute este teste para confirmar que tudo está funcionando:

```bash
python tests/test_agent_tools_integration.py
```

Esperado:
```
✅ PASSED: Tool Registration
✅ PASSED: Name Uniqueness
✅ PASSED: Tool Metadata
✅ PASSED: Report Tools
```

---

**O agente está pronto! Comece digitando suas consultas no chat.** 🚀
