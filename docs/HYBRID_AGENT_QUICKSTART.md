# 🤖 Hybrid Agent - Guia Rápido

## TL;DR

O agente agora funciona como **ChatGPT/Claude** mas com **ferramentas fiscais especializadas**.

---

## 🎯 3 Níveis de Capacidade

| Tier | O que faz | Quando usar | Exemplo |
|------|-----------|-------------|---------|
| **1️⃣ Inteligência Nativa** | Responde do conhecimento do modelo | Perguntas conceituais | "O que é ICMS?" |
| **2️⃣ Tools Especializadas** | Acessa banco de dados | Consultas aos dados | "Quantas notas temos?" |
| **3️⃣ Capacidades Dinâmicas** | Executa Python, busca web | Cálculos complexos | "Calcule juros compostos" |

---

## ⚡ Uso Rápido

```python
from src.agent.agent_core import create_agent

# Criar agente
agent = create_agent(api_key="sua-chave-gemini")

# Perguntas conceituais (responde direto)
agent.chat("O que é ICMS?")

# Cálculos (sem tools)
agent.chat("Calculate 18% of R$ 1000")

# Código Python (gera direto)
agent.chat("Write code to validate CNPJ")

# Consultas ao banco (usa tools)
agent.chat("Quantas notas fiscais temos?")

# Relatórios (usa tools)
agent.chat("Gere relatório de impostos de janeiro")

# Python complexo (executa código)
agent.chat("Calculate compound interest: R$ 10k at 5% for 10 years")
```

---

## 💡 Diferenças vs Agente Antigo

### ❌ Antes (Limitado)

```python
User: "O que é CFOP?"
Agent: "Não tenho ferramenta para isso"

User: "Calcule 18% de R$ 1000"
Agent: "Não posso fazer cálculos"

User: "Escreva código Python"
Agent: "Não gero código"
```

### ✅ Agora (Híbrido)

```python
User: "O que é CFOP?"
Agent: "CFOP é o Código Fiscal de Operações..." ✅

User: "Calcule 18% de R$ 1000"
Agent: "R$ 180,00" ✅

User: "Escreva código Python"
Agent: [gera código completo] ✅
```

---

## 🔧 Configuração

### Básico (Padrão)

```python
agent = create_agent(api_key="...")
# ✅ Inteligência nativa: ON
# ✅ Tools fiscais: ON
# ✅ Execução Python: ON
# ❌ Busca web: OFF
```

### Completo

```python
agent = create_agent(
    api_key="...",
    enable_web_search=True,      # Busca na internet
    enable_code_execution=True,  # Executa Python
)
```

---

## 📝 Exemplos por Categoria

### 🧠 Tier 1: Sem Tools (Resposta Direta)

```python
"O que é ICMS?"
"Explique a diferença entre NFe e NFCe"
"Calculate 15% + 3% of R$ 1000"
"Write Python code to parse CSV"
"Traduza: Electronic Invoice"
```

### 🛠️ Tier 2: Tools Fiscais

```python
"Quantas notas fiscais temos?"
"Gere relatório Excel de janeiro"
"Valide CNPJ 12.345.678/0001-90"
"Busque notas do fornecedor X"
"Arquive documentos de 2024"
```

### 🚀 Tier 3: Python/Web

```python
"Calculate compound interest: R$ 10k at 5% for 10 years"
"Find outliers in data: [1, 2, 3, 100, 2, 3]"
"Parse JSON: {'users': [...]}"
"What's the current SELIC rate?" (web search)
```

### 🔗 Híbrido (Multi-Tool)

```python
"Get January invoices and calculate average"
# → search_invoices_database + python_repl

"Explain ICMS then calculate it on R$ 1000"
# → Tier 1 knowledge + Tier 1 math

"Generate report then analyze the CSV"
# → fiscal_report_export + python_repl
```

---

## ⚠️ Limitações

### Execução Python

**✅ Pode:**
- Cálculos matemáticos
- Parsing JSON/CSV
- Estatísticas (pandas/numpy)
- String manipulation

**❌ Não Pode:**
- Acessar arquivos do disco
- Requests de rede
- Subprocess
- Importar módulos não seguros

### Busca Web

- Requer configuração DuckDuckGo
- Pode ter rate limits
- Resultados não garantidos 100%

---

## 🎯 Melhores Práticas

### ✅ DO

```python
# Deixe o agente decidir qual tool usar
"Quantas notas temos?"

# Seja natural
"Explique ICMS"

# Combine capacidades
"Explique depreciação e calcule para R$ 50k em 10 anos"
```

### ❌ DON'T

```python
# Não force tools
"Use search_invoices_database para..."

# Não use SQL direto
"Execute: SELECT COUNT(*) FROM..."

# Não peça relatório para conceitos
"Gere relatório explicando ICMS"
```

---

## 🚀 Demo Rápido

```bash
# Configurar API key
export GEMINI_API_KEY='sua-chave'

# Rodar demo interativo
python examples/demo_hybrid_agent.py

# Ou direto no Python
python -c "
from src.agent.agent_core import create_agent
agent = create_agent(api_key='...')
print(agent.chat('O que é ICMS?'))
"
```

---

## 📚 Documentação Completa

- **Guia Detalhado:** `docs/HYBRID_AGENT.md`
- **Código Fonte:** `src/agent/hybrid_agent.py`
- **Exemplos:** `examples/demo_hybrid_agent.py`
- **Verificação Tools:** `docs/AGENT_VERIFICATION.md`

---

**Agora o agente é verdadeiramente autônomo e capaz de se virar em qualquer situação!** 🎉
