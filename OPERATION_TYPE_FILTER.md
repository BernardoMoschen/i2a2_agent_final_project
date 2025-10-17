# 🔍 Filtro de Tipo de Operação - Guia de Uso

## ✅ Implementado

Agora você pode **filtrar documentos por tipo de operação** na aba **History**!

---

## 🎯 Como Usar

### 1. Acesse a aba "History"

```
streamlit run src/ui/app.py
```

### 2. Veja os novos filtros

```
┌────────────────────────────────────────────────────────────┐
│  🔍 Filters                                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Document Type│  │ Operation    │  │ Issuer CNPJ  │    │
│  │    ▼         │  │ Type ▼       │  │              │    │
│  │              │  │              │  │              │    │
│  │ • All        │  │ • All        │  │ Contains...  │    │
│  │ • NFe        │  │ • Purchase   │  │              │    │
│  │ • NFCe       │  │ • Sale       │  │              │    │
│  │ • CTe        │  │ • Transfer   │  │              │    │
│  │ • MDFe       │  │ • Return     │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ┌──────────────┐                                         │
│  │ Date Range ▼ │                                         │
│  │              │                                         │
│  │ • All Time   │                                         │
│  │ • Last 7 days│                                         │
│  │ • Last 30... │                                         │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 3. Selecione o tipo de operação

**Opções disponíveis:**

| Opção        | Descrição                         | Emoji |
| ------------ | --------------------------------- | ----- |
| **All**      | Todos os documentos               | -     |
| **Purchase** | Compras/Entradas (CFOP 1xxx-3xxx) | 📥    |
| **Sale**     | Vendas/Saídas (CFOP 5xxx-7xxx)    | 📤    |
| **Transfer** | Transferências                    | 🔄    |
| **Return**   | Devoluções                        | ↩️    |

---

## 📊 Visualização na Tabela

A tabela agora inclui a coluna **"Operation"**:

```
┌──────────────┬──────┬────────────┬────────┬─────────────────┬──────────────────┬────────────┬───────┐
│ Date         │ Type │ Operation  │ Number │ Issuer          │ CNPJ             │ Total      │ Items │
├──────────────┼──────┼────────────┼────────┼─────────────────┼──────────────────┼────────────┼───────┤
│ 2024-01-15   │ NFe  │ 📥 Purchase│ 1234   │ FORNECEDOR XYZ  │ 12.345.678/0001  │ R$ 1.000,00│ 5     │
│ 2024-01-14   │ NFe  │ 📤 Sale    │ 5678   │ CLIENTE ABC     │ 98.765.432/0001  │ R$ 2.500,00│ 3     │
│ 2024-01-13   │ NFe  │ 🔄 Transfer│ 9012   │ FILIAL SUL      │ 11.222.333/0001  │ R$ 500,00  │ 2     │
└──────────────┴──────┴────────────┴────────┴─────────────────┴──────────────────┴────────────┴───────┘
```

---

## 🔧 Implementação Técnica

### Mudanças no código:

#### 1. **UI (src/ui/app.py)**

```python
# Novo filtro adicionado
with col2:
    filter_operation = st.selectbox(
        "Operation Type",
        options=["All", "Purchase", "Sale", "Transfer", "Return"],
        key="history_filter_operation"
    )

# Aplicação do filtro
if filter_operation != "All":
    db_filters["operation_type"] = filter_operation.lower()
```

#### 2. **Database (src/database/db.py)**

```python
def search_invoices(
    self,
    operation_type: Optional[str] = None,  # 🆕 NOVO parâmetro
    # ... outros parâmetros
):
    # ...
    if operation_type:
        statement = statement.where(InvoiceDB.operation_type == operation_type)
```

#### 3. **Tabela com coluna "Operation"**

```python
# Emoji por tipo de operação
operation_emoji = {
    "purchase": "📥",
    "sale": "📤",
    "transfer": "🔄",
    "return": "↩️",
}.get(inv.operation_type, "📄")

# Display na tabela
"Operation": f"{operation_emoji} {inv.operation_type.title()}"
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Listar todas as compras

1. Vá para **History**
2. Selecione **"Purchase"** no filtro "Operation Type"
3. Veja apenas documentos de entrada

### Exemplo 2: Vendas dos últimos 30 dias

1. Vá para **History**
2. Selecione **"Sale"** em "Operation Type"
3. Selecione **"Last 30 days"** em "Date Range"

### Exemplo 3: Transferências de um fornecedor específico

1. Vá para **History**
2. Selecione **"Transfer"** em "Operation Type"
3. Digite o CNPJ parcial em "Issuer CNPJ"

---

## 🧪 Testes

### Script de teste standalone:

```bash
python test_operation_filter.py
```

**Saída:**

```
📊 Total documents in database: 1

🏷️ Breakdown by Operation Type:
  📥 Purchase: 1 document(s)

🔍 Testing filters:
  Filter 'purchase': 1 result(s)
    - NFe 1 | FORNECEDOR TESTE LTDA
  Filter 'sale': 0 result(s)
  Filter 'transfer': 0 result(s)
  Filter 'return': 0 result(s)

✅ Filter test completed!
```

### Testes automatizados:

```bash
pytest tests/test_database.py -v
```

✅ **6/6 testes passando**

---

## 🎨 Preview Visual

### Antes:

```
Filters:
[Document Type ▼] [Issuer CNPJ] [Date Range ▼]
```

### Agora:

```
Filters:
[Document Type ▼] [Operation Type ▼] [Issuer CNPJ] [Date Range ▼]
                   📥 Purchase
                   📤 Sale
                   🔄 Transfer
                   ↩️ Return
```

---

## 🚀 Benefícios

✅ **Filtragem rápida** por tipo de operação  
✅ **Visualização clara** com emojis descritivos  
✅ **Combinação de filtros** (tipo + data + CNPJ)  
✅ **Performance otimizada** (query no banco)  
✅ **UX melhorada** com 4 colunas de filtros

---

## 📚 Próximos Passos

Outras ideias de filtros:

- 🏢 **Centro de Custo** (cost_center)
- 💯 **Nível de Confiança** (classification_confidence >= X%)
- ⚠️ **Documentos com Issues** (has_validation_errors)
- 🤖 **Usou LLM** (used_llm_fallback)

---

**Tudo pronto para usar! 🎉**

Abra o Streamlit e teste os novos filtros na aba History!

```bash
streamlit run src/ui/app.py
```
