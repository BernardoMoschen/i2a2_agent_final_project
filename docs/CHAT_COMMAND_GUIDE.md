# Chat Command Guide - Fiscal Document Agent

**Agent:** LangChain + Gemini 2.5-flash-lite  
**Languages:** Portuguese & English  
**Interface:** Streamlit Chat Tab

---

## 📚 Quick Start

The agent understands natural language in **Portuguese** and **English**. You can ask questions or give commands conversationally - no need for exact syntax!

### Basic Principles

- Be conversational and natural
- Specify what you want (parse, search, validate, export, etc.)
- Add filters when needed (dates, types, suppliers)
- Ask follow-up questions - the agent remembers context

---

## 🔍 Searching Documents

### Count Documents

```
"quantos documentos temos?"
"how many invoices do we have?"
"total de notas fiscais"
"count all documents"
```

### Search by Year

```
"me traga documentos de 2024"
"show me invoices from 2023"
"quantas notas de 2024?"
"list all 2024 documents"
```

### Search by Date Range

```
"há documentos em 2024-01-19?"
"show invoices between January and March 2024"
"documentos do mês de janeiro"
"documents from last 30 days"
```

### Search by Document Type

```
"me mostre todas as NFe"
"show me all NFCe documents"
"quantas CTe temos?"
"list all MDFe invoices"
```

### Search by Operation Type

```
"quantas notas de compra?"
"show me all sales"
"documentos de transferência"
"purchase invoices only"
```

### Search by Supplier

```
"notas do fornecedor 12.345.678/0001-90"
"invoices from supplier X"
"documentos do CNPJ 00000000000191"
```

### Combined Filters

```
"NFe de compra de 2024"
"sales invoices from supplier X in January"
"todas as NFCe de venda dos últimos 90 dias"
"purchase documents with CNPJ 123... from last year"
```

---

## 📄 Document Processing

### Parse XML

```
"parse este XML: [paste XML content]"
"processar este documento fiscal"
"analyze this NFe"
```

### Validate Document

```
"validar este XML"
"check this invoice for issues"
"este documento está correto?"
"validate document with key 12345..."
```

### Classify Document

```
"classificar documento com chave 12345..."
"classify this invoice"
"qual o centro de custo desta nota?"
"is this a purchase or sale?"
```

---

## 📊 Reports & Analytics

### Generate Excel/CSV Reports

#### Validation Reports

```
"gerar relatório de documentos com falhas"
"report of XMLs with issues from January 2024"
"relatório de problemas por gravidade"
"issues by supplier report"
```

#### Financial Reports

```
"relatório de impostos por período"
"top 10 suppliers by value"
"tax breakdown for last quarter"
"costs by cost center report"
```

#### Operational Reports

```
"volume de documentos por período"
"documents by operation type"
"relatório por tipo de documento"
"volume report for 2024"
```

#### Classification Reports

```
"cache effectiveness report"
"relatório de documentos não classificados"
"LLM fallback usage report"
"classification by cost center"
```

#### Product Reports

```
"top products by NCM"
"análise por CFOP"
"relatório de itens com problemas"
```

### Generate Interactive Charts

```
"criar gráfico de vendas mensais"
"chart of monthly purchases"
"breakdown de impostos em pizza"
"supplier ranking chart"
"timeline de documentos"
```

---

## 📈 Statistics

### Database Statistics

```
"estatísticas do banco"
"database stats"
"resumo dos documentos processados"
"how many items and issues do we have?"
```

### Cache Statistics

```
"efetividade do cache"
"cache statistics"
"how much are we saving with cache?"
```

---

## 🗄️ Archiving

### Archive Single Document

```
"arquivar documento com chave 12345..."
"archive this invoice"
"organizar XML processado"
```

### Batch Archive

```
"arquivar todos os documentos deste mês"
"archive all invoices from last 30 days"
"organizar todos os XMLs processados"
"batch archive documents from 2024"
```

---

## ✅ External Validation

### CNPJ Validation

```
"validar CNPJ 00.000.000/0001-00"
"check CNPJ 12345678000190"
"qual a razão social deste CNPJ?"
"is this CNPJ active?"
```

### CEP Validation

```
"validar CEP 01310-100"
"check CEP 12345678"
"qual o endereço deste CEP?"
"where is this CEP located?"
```

### NCM Lookup

```
"o que é NCM 84713012?"
"lookup NCM 22030000"
"qual a descrição do NCM 12345678?"
"what's the IPI rate for this NCM?"
```

---

## 💡 General Knowledge

### Ask About Fiscal Concepts

```
"o que é NFe?"
"what is the difference between NFe and NFCe?"
"como funciona o ICMS?"
"what are CFOP codes?"
"explain NCM classification"
```

---

## 🎯 Pro Tips

### 1. Use Natural Language

❌ Bad: `search_invoices(document_type="NFe", days_back=9999)`  
✅ Good: `"me mostre todas as NFe"`

### 2. Be Specific with Dates

The agent automatically uses `days_back=9999` for comprehensive searches, but you can be explicit:

```
"documentos de 2024" → searches all time
"documentos dos últimos 30 dias" → searches last month
"documentos entre janeiro e março de 2024" → specific range
```

### 3. Combine Multiple Operations

```
"buscar documentos de compra de 2024, validar os 5 primeiros, e gerar relatório de problemas"
```

The agent will:

1. Search for purchase documents from 2024
2. Validate the first 5
3. Generate an issues report

### 4. Ask Follow-Up Questions

```
User: "quantas notas de compra de 2024?"
Agent: "Encontrados 15 documentos..."
User: "me mostre as 5 maiores por valor"
Agent: [uses context from previous search]
```

### 5. Request Specific Formats

```
"gerar relatório em CSV" → CSV format
"gerar relatório em Excel" → XLSX format
"criar gráfico" → Interactive Plotly chart
```

---

## 🚫 What the Agent CANNOT Do

1. **Upload Files** - Use the Upload tab for this
2. **Delete Documents** - Not implemented (manual database operation required)
3. **Modify Raw XMLs** - Agent is read-only for security

---

## 🐛 Troubleshooting

### "No documents found"

- Check if documents are actually in database: `"database statistics"`
- Verify date range is correct
- Make sure document type spelling is correct (NFe, not NF-e)

### "Error parsing XML"

- XML must be valid Brazilian fiscal format
- Check for encoding issues
- Verify XML is complete (not truncated)

### "Validation failed"

- This means the document HAS issues - that's the point!
- Ask: `"what are the specific problems?"`
- Request: `"suggest fixes for these issues"`

### "Classification confidence low"

- Document may be non-standard
- Check if issuer/recipient info is complete
- Try: `"show me the reasoning for this classification"`

---

## 📞 Support

For issues with the agent:

1. Check this guide first
2. Try rephrasing your question
3. Ask the agent: `"como posso fazer X?"` / `"how do I do X?"`
4. The agent explains its capabilities when asked

---

## 🔄 Example Workflows

### Daily Document Processing

```
1. Upload XMLs via UI
2. "quantos documentos foram processados hoje?"
3. "validar todos os documentos de hoje"
4. "gerar relatório de problemas"
5. "arquivar documentos processados"
```

### Monthly Closing

```
1. "relatório de impostos do mês passado"
2. "top 10 fornecedores por valor do último mês"
3. "gráfico de vendas mensais"
4. "arquivar todos os documentos do mês passado"
```

### Audit Preparation

```
1. "quantos documentos temos por tipo?"
2. "gerar relatório completo de 2024"
3. "documentos com problemas de validação"
4. "efetividade do cache de classificação"
```

### Supplier Analysis

```
1. "top suppliers by value last quarter"
2. "documentos do fornecedor X"
3. "validar CNPJ do fornecedor Y"
4. "relatório de problemas por fornecedor"
```

---

**Last Updated:** 2025-10-27  
**Version:** 1.0
