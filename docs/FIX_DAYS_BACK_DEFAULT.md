# 🔧 Fix: Agente Agora Encontra Documentos Antigos

## ❌ Problema Identificado

**Sintoma:**

```
Usuário: "Quantas notas de compra temos?"

Agente: "❌ Não encontramos nenhuma nota de compra..."
```

**Causa Raiz:**

- `days_back` padrão era **30 dias**
- Documentos de teste eram de **janeiro/2024** (muito antigos)
- Agente buscava apenas últimos 30 dias → não encontrava nada

---

## ✅ Solução Implementada

### 1. **Aumentado `days_back` padrão**

**ANTES:**

```python
days_back: int = Field(30, description="...")
```

**AGORA:**

```python
days_back: int = Field(3650, description="Default is 3650 (10 years)")
#                      ^^^^
#                      10 anos!
```

### 2. **Instruções Explícitas para o LLM**

Adicionado na description da tool:

```python
"""
⚠️ IMPORTANT FOR COUNTING/LISTING DOCUMENTS:
- ALWAYS use days_back=9999 when user asks "quantas", "how many", "list all"
- This ensures ALL documents are searched
- Documents may be very old (2023, 2024, etc.)

CRITICAL RULES:
- When user asks "quantas" or "how many" → ALWAYS use days_back=9999
"""
```

---

## 🧪 Teste de Validação

### Antes da Correção:

```bash
$ python -c "from src.agent.tools import database_search_tool; \
  result = database_search_tool._run(operation_type='purchase', days_back=30); \
  print(result)"

🔍 Nenhum documento encontrado...
❌ Documentos de 2024 não aparecem!
```

### Depois da Correção:

```bash
$ python -c "from src.agent.tools import database_search_tool; \
  result = database_search_tool._run(operation_type='purchase'); \
  print(result)"

📊 Encontrados 2 documento(s):

Por Tipo de Operação:
- 📥 Compras: 2

📥 NFe - 3510129/1 | Compra
   🏢 Emitente: COMPANHIA BRASILEIRA DE EDUC...
   📅 Data: 18/01/2024
   💰 Valor: R$ 522.50

📥 NFe - 1/1 | Compra
   🏢 Emitente: FORNECEDOR TESTE LTDA
   📅 Data: 15/01/2024
   💰 Valor: R$ 1,000.00

Resumo Final:
- 📄 Total: 2 documentos
- 💰 Valor total: R$ 1,522.50

✅ FUNCIONA!
```

---

## 📊 Comportamento Atualizado

| Pergunta                   | days_back usado   | Resultado                |
| -------------------------- | ----------------- | ------------------------ |
| "Quantas notas de compra?" | **3650** (padrão) | ✅ Encontra 2            |
| "How many purchases?"      | **3650** (padrão) | ✅ Encontra 2            |
| "Compras da última semana" | LLM escolhe 7     | ✅ Busca apenas recentes |
| "Todas as vendas"          | LLM escolhe 9999  | ✅ Busca tudo            |

---

## 🎯 Mudanças no Código

### `src/agent/tools.py`

**SearchInvoicesInput:**

```python
days_back: Optional[int] = Field(
    3650,  # ← MUDOU: 30 → 3650 (10 anos)
    description="Search last N days. Default is 3650 (10 years). Use 9999 for ALL."
)
```

**DatabaseSearchTool.description:**

```python
"""
⚠️ IMPORTANT FOR COUNTING/LISTING DOCUMENTS:
- ALWAYS use days_back=9999 when user asks "quantas", "how many", "list all"
- Documents may be very old (2023, 2024, etc.)

CRITICAL RULES:
- When user asks "quantas" or "how many" → ALWAYS use days_back=9999
"""
```

---

## 🔍 Por Que 3650 Dias?

- **3650 dias = ~10 anos**
- Cobre período fiscal típico (7 anos de retenção + margem)
- Garante que documentos de teste (2023/2024) sejam encontrados
- LLM ainda pode escolher valores menores quando apropriado

### Quando usar 9999?

- **9999 = "todos os documentos de sempre"**
- Use quando precisar garantir busca completa
- LLM instrução explícita para usar em contagens

---

## ✅ Checklist de Validação

- [x] `days_back` padrão alterado: 30 → 3650
- [x] Description atualizada com instruções para LLM
- [x] Testado com documentos de 2024 (funcionando)
- [x] Async version também atualizada
- [x] Documentação criada

---

## 🚀 Teste Agora

### Via Streamlit:

```bash
streamlit run src/ui/app.py

# Na aba Chat, pergunte:
"Quantas notas de compra temos no sistema?"

# Resposta esperada:
"📊 Encontrados 2 documento(s):
 📥 Compras: 2
 ..."
```

### Via Script:

```bash
export GEMINI_API_KEY="sua-chave"
python test_agent_purchase_query.py
```

---

## 📝 Perguntas que Agora Funcionam

| Pergunta                           | Resultado Esperado          |
| ---------------------------------- | --------------------------- |
| "Quantas notas de compra temos?"   | ✅ 2 compras                |
| "How many purchase items?"         | ✅ 2 compras                |
| "Quantas vendas existem?"          | ✅ 0 vendas (se não houver) |
| "Total de documentos processados?" | ✅ 2 documentos             |
| "Mostre todas as notas"            | ✅ Lista completa           |

---

## 🎉 Resultado Final

**ANTES:**

```
Usuário: "Quantas notas de compra temos?"
Agente: "❌ Não encontramos nenhuma nota..."
```

**AGORA:**

```
Usuário: "Quantas notas de compra temos?"
Agente: "📊 Encontrados 2 documento(s):
         📥 Compras: 2

         [detalhes completos...]

         Resumo Final:
         - Total: 2 documentos
         - Valor total: R$ 1,522.50"
```

---

**Problema resolvido! O agente agora encontra documentos antigos automaticamente!** 🎯
