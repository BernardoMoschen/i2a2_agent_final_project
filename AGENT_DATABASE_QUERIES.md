# 🤖 Agente com Consulta ao Banco de Dados

## ✅ Problema Resolvido

**ANTES:**

```
Usuário: "Quantas notas de compra temos no sistema?"

Agente: "Atualmente, temos 20 documentos NFe processados."
❌ Resposta genérica, sem filtrar por tipo de operação
```

**AGORA:**

```
Usuário: "Quantas notas de compra temos no sistema?"

Agente:
📊 Encontrados 2 documento(s):

Por Tipo de Operação:
- 📥 Compras: 2

📥 NFe - 3510129/1 | Compra
   🏢 Emitente: COMPANHIA BRASILEIRA...
   📅 Data: 18/01/2024
   💰 Valor: R$ 522.50

📥 NFe - 1/1 | Compra
   🏢 Emitente: FORNECEDOR TESTE LTDA
   📅 Data: 15/01/2024
   💰 Valor: R$ 1,000.00

Resumo Final:
- 📄 Total: 2 documentos
- 💰 Valor total: R$ 1,522.50

✅ Resposta precisa com detalhes!
```

---

## 🔧 O que foi modificado

### 1. **Tool: `search_invoices_database`**

Atualizada para suportar filtro de **tipo de operação**:

```python
class SearchInvoicesInput(BaseModel):
    document_type: Optional[str]    # NFe, NFCe, CTe, MDFe
    operation_type: Optional[str]   # 🆕 purchase, sale, transfer, return
    issuer_cnpj: Optional[str]      # CNPJ do emitente
    days_back: Optional[int] = 30   # 🆕 Padrão aumentado para 30 dias
```

### 2. **Description da Tool**

Agora inclui instruções explícitas:

```python
description: str = """
Search for fiscal documents stored in the database with flexible filters.

IMPORTANT:
- For "notas de compra" use operation_type='purchase'
- For "notas de venda" use operation_type='sale'
- For "transferências" use operation_type='transfer'
- For "devoluções" use operation_type='return'
- Default days_back is 30, increase for older documents
"""
```

### 3. **Resposta Aprimorada**

Agora mostra:

- ✅ Contagem por tipo de operação
- ✅ Emojis descritivos (📥 📤 🔄 ↩️)
- ✅ Lista detalhada de documentos
- ✅ Resumo com total e valor

---

## 📚 Perguntas que o Agente Agora Responde

### ✅ Compras

```
"Quantas notas de compra temos?"
"Mostre todas as compras dos últimos 60 dias"
"Qual o valor total de compras?"
```

### ✅ Vendas

```
"Quantas notas de venda existem?"
"Liste as vendas de janeiro"
"Vendas acima de R$ 1.000"
```

### ✅ Transferências

```
"Quantas transferências foram feitas?"
"Mostre transferências dos últimos 30 dias"
```

### ✅ Devoluções

```
"Quantas devoluções temos?"
"Liste devoluções do mês passado"
```

### ✅ Filtros Combinados

```
"Quantas NFes de compra do CNPJ 12.345.678?"
"Vendas dos últimos 7 dias"
"Todas as transferências de 2024"
```

---

## 🧪 Como Testar

### 1. Via Terminal (sem UI)

```bash
# Definir API key
export GEMINI_API_KEY="sua-chave-aqui"

# Rodar teste
python test_agent_purchase_query.py
```

### 2. Via Streamlit UI

```bash
# Subir interface
streamlit run src/ui/app.py

# 1. Inserir API Key na sidebar
# 2. Ir para aba "Chat"
# 3. Perguntar: "Quantas notas de compra temos no sistema?"
```

---

## 🎯 Exemplos de Interação

### Exemplo 1: Contagem Simples

**Pergunta:**

> Quantas notas de compra temos?

**Agente usa:**

```python
search_invoices_database(
    operation_type="purchase",
    days_back=30
)
```

**Resposta:**

```
📊 Encontrados 2 documento(s):

Por Tipo de Operação:
- 📥 Compras: 2

...detalhes dos documentos...

Resumo Final:
- 📄 Total: 2 documentos
- 💰 Valor total: R$ 1,522.50
```

---

### Exemplo 2: Período Específico

**Pergunta:**

> Quantas vendas tivemos nos últimos 7 dias?

**Agente usa:**

```python
search_invoices_database(
    operation_type="sale",
    days_back=7
)
```

---

### Exemplo 3: Filtro por Emitente

**Pergunta:**

> Mostre compras do fornecedor 12.345.678

**Agente usa:**

```python
search_invoices_database(
    operation_type="purchase",
    issuer_cnpj="12345678",
    days_back=90
)
```

---

## 🔍 Parâmetros da Ferramenta

| Parâmetro        | Tipo   | Descrição                        | Exemplo      |
| ---------------- | ------ | -------------------------------- | ------------ |
| `document_type`  | string | NFe, NFCe, CTe, MDFe             | `"NFe"`      |
| `operation_type` | string | purchase, sale, transfer, return | `"purchase"` |
| `issuer_cnpj`    | string | CNPJ do emitente (substring)     | `"12345678"` |
| `days_back`      | int    | Últimos N dias (padrão 30)       | `60`         |

---

## 📊 Mapeamento de Termos

O agente entende diferentes formas de perguntar:

| Pergunta do Usuário    | operation_type |
| ---------------------- | -------------- |
| "notas de **compra**"  | `purchase`     |
| "notas de **entrada**" | `purchase`     |
| "notas de **venda**"   | `sale`         |
| "notas de **saída**"   | `sale`         |
| "**transferências**"   | `transfer`     |
| "**devoluções**"       | `return`       |

---

## 🚀 Benefícios

✅ **Respostas Precisas**: Conta exatamente o que foi perguntado  
✅ **Contexto Rico**: Mostra detalhes relevantes (emitente, data, valor)  
✅ **Agregações**: Totaliza valores automaticamente  
✅ **Filtros Inteligentes**: Combina múltiplos critérios  
✅ **Período Flexível**: Ajusta automaticamente o intervalo de busca

---

## 📝 Logs de Debug

Quando o agente usa a ferramenta, você verá:

```
> Entering new AgentExecutor chain...

Thought: O usuário quer saber quantas notas de compra existem.
         Vou usar a ferramenta search_invoices_database com
         operation_type='purchase'.

Action: search_invoices_database
Action Input: {"operation_type": "purchase", "days_back": 9999}

Observation:
📊 Encontrados 2 documento(s):
...

Thought: Tenho a resposta final.
Final Answer: Temos 2 notas de compra no sistema, totalizando R$ 1.522,50.
```

---

## 🔄 Fluxo Completo

```
┌────────────────────────────────────────────────────┐
│  USUÁRIO                                           │
│  "Quantas notas de compra temos?"                 │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  AGENTE (LangChain + Gemini)                      │
│  1. Analisa a pergunta                            │
│  2. Identifica: precisa buscar no banco           │
│  3. Reconhece: "compra" = operation_type purchase │
│  4. Decide: usar tool search_invoices_database    │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  TOOL: search_invoices_database                   │
│  - operation_type: "purchase"                     │
│  - days_back: 30 (padrão)                         │
│  - Consulta SQLite                                │
│  - Retorna resultados formatados                  │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  AGENTE                                            │
│  1. Recebe resultado da tool                      │
│  2. Formata resposta amigável                     │
│  3. Adiciona contexto se necessário               │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│  RESPOSTA AO USUÁRIO                              │
│  "Temos 2 notas de compra, totalizando R$ 1.522" │
│  + Detalhes dos documentos                        │
└────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Implementação

- [x] Atualizado `SearchInvoicesInput` com `operation_type`
- [x] Modificado `DatabaseSearchTool._run()` para aceitar filtro
- [x] Atualizada description com instruções explícitas
- [x] Aumentado `days_back` padrão de 7 para 30 dias
- [x] Adicionada quebra por tipo de operação na resposta
- [x] Adicionados emojis descritivos (📥 📤 🔄 ↩️)
- [x] Testado com banco real (2 compras encontradas)
- [x] Criado script de teste `test_agent_purchase_query.py`
- [x] Documentação completa criada

---

## 🎉 Resultado Final

**Agora o agente é capaz de:**

1. ✅ Entender perguntas sobre tipos de operação
2. ✅ Filtrar documentos por purchase/sale/transfer/return
3. ✅ Retornar contagens precisas
4. ✅ Mostrar detalhes relevantes
5. ✅ Agregar valores totais
6. ✅ Combinar múltiplos filtros

**Tudo pronto para uso em produção!** 🚀

---

## 🧪 Teste Agora

```bash
# 1. Configure sua API key
export GEMINI_API_KEY="sua-chave-aqui"

# 2. Suba o Streamlit
streamlit run src/ui/app.py

# 3. Na aba Chat, pergunte:
"Quantas notas de compra temos no sistema?"
```

O agente vai responder com precisão! 🎯
