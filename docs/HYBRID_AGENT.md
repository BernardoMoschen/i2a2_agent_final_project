# 🤖 Hybrid Fiscal Agent - Documentação Completa

## Visão Geral

O **Hybrid Fiscal Agent** é um agente LLM avançado que combina três níveis de capacidade:

1. **🧠 Inteligência Nativa** - Conhecimento e raciocínio do próprio modelo
2. **🛠️ Ferramentas Especializadas** - Acesso ao banco de dados e funções fiscais
3. **🚀 Capacidades Dinâmicas** - Execução de código e busca na web

---

## 🎯 Filosofia: ChatGPT-Level com Especialização Fiscal

### Problema que Resolvemos

**Antes (Agent Limitado):**
```
User: "O que é ICMS?"
Agent: ❌ "Não tenho ferramenta para isso"

User: "Calcule 18% de R$ 1000"
Agent: ❌ "Não posso fazer cálculos"

User: "Escreva código Python para validar CNPJ"
Agent: ❌ "Não gero código"
```

**Agora (Hybrid Agent):**
```
User: "O que é ICMS?"
Agent: ✅ "ICMS é o Imposto sobre Circulação de Mercadorias e Serviços..." (explica diretamente)

User: "Calcule 18% de R$ 1000"
Agent: ✅ "18% de R$ 1.000,00 = R$ 180,00" (calcula diretamente)

User: "Escreva código Python para validar CNPJ"
Agent: ✅ [gera código funcional completo] (sem usar tools)
```

---

## 📊 Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────┐
│  USER QUERY                                             │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Native LLM Intelligence (SEMPRE ATIVO)        │
│  ✅ Responde perguntas gerais                           │
│  ✅ Explica conceitos                                   │
│  ✅ Faz cálculos básicos                                │
│  ✅ Gera código                                         │
│  ✅ Traduz idiomas                                      │
└────────────────────┬────────────────────────────────────┘
                     ↓ Precisa de dados?
┌─────────────────────────────────────────────────────────┐
│  TIER 2: Specialized Fiscal Tools                      │
│  🗄️  search_invoices_database                          │
│  📊 fiscal_report_export                                │
│  ✓  validate_fiscal_document                           │
│  🏷️  classify_invoice                                   │
│  📦 archive_invoice                                     │
│  ... 13 tools total                                    │
└────────────────────┬────────────────────────────────────┘
                     ↓ Precisa de mais?
┌─────────────────────────────────────────────────────────┐
│  TIER 3: Dynamic Capabilities                          │
│  🐍 python_repl - Execute Python code                  │
│  🌐 web_search - Search internet (optional)            │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  RESPONSE (pode combinar múltiplos tiers)              │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Uso Básico

### 1. Criar o Agente

```python
from src.agent.agent_core import create_agent

# Básico (código Python habilitado)
agent = create_agent(
    api_key="sua-chave-gemini",
    model_name="gemini-2.0-flash-exp",
)

# Completo (com todas as capacidades)
agent = create_agent(
    api_key="sua-chave-gemini",
    model_name="gemini-2.0-flash-exp",
    enable_web_search=True,      # Requer DuckDuckGo
    enable_code_execution=True,  # Execução de Python
)
```

### 2. Usar o Agente

```python
# Perguntas conceituais (Tier 1 - sem tools)
response = agent.chat("O que é ICMS?")
# → Explica diretamente do conhecimento

# Cálculos (Tier 1 - sem tools)
response = agent.chat("Calculate 18% of R$ 5,432.10")
# → R$ 977,78 (calcula diretamente)

# Gerar código (Tier 1 - sem tools)
response = agent.chat("Write Python code to validate CNPJ")
# → Gera código funcional completo

# Consultas ao banco (Tier 2 - usa tools)
response = agent.chat("Quantas notas fiscais temos?")
# → Usa search_invoices_database

# Relatórios (Tier 2 - usa tools)
response = agent.chat("Gere relatório de impostos de janeiro 2024")
# → Usa fiscal_report_export

# Cálculos complexos (Tier 3 - python_repl)
response = agent.chat("Calculate compound interest: R$ 10k at 5% for 10 years")
# → Executa código Python para calcular

# Busca web (Tier 3 - web_search, se habilitado)
response = agent.chat("What's the current SELIC rate?")
# → Busca na internet
```

---

## 📖 Exemplos por Tier

### TIER 1: Native Intelligence (No Tools)

Perguntas que o agente responde **diretamente** do conhecimento:

```python
# Conceitos fiscais
"O que é CFOP 5102?"
"Explain the difference between NFe and NFCe"
"Como funciona o cálculo de ICMS-ST?"

# Matemática
"Calculate 18% of R$ 1,234.56"
"What's 15% + 3% + 2% of R$ 10,000?"
"Convert USD 500 to BRL at rate 5.20"

# Programação
"Write Python code to parse a CSV file"
"How do I validate a CNPJ in Python?"
"Create a function to calculate depreciation"

# Tradução
"Translate to English: Nota Fiscal Eletrônica"
"Como se diz 'purchase invoice' em português?"

# Explicações
"How does depreciation work in accounting?"
"What are the main types of taxes in Brazil?"
"Explain the concept of tax substitution"
```

**✅ Vantagem:** Resposta instantânea, sem overhead de tools.

### TIER 2: Specialized Tools (Database & Reports)

Quando precisa acessar **dados reais** do sistema:

```python
# Busca no banco de dados
"Quantas notas fiscais de compra temos?"
"Search for invoices from supplier Acme Corp"
"Show me all documents with validation issues"

# Geração de relatórios
"Generate Excel report of January taxes"
"Top 10 suppliers by total value"
"Create CSV of unclassified documents"

# Validação
"Validate this document: [XML content]"
"Check if CNPJ 12.345.678/0001-90 is valid"
"Verify this CEP: 01310-100"

# Classificação
"Classify this invoice as purchase or sale"
"What's the operation type of document #12345?"

# Arquivamento
"Archive all processed invoices from 2024"
"Move this document to archive"
```

**✅ Vantagem:** Acesso aos dados reais e persistência.

### TIER 3: Dynamic Capabilities

#### 3A. Python Code Execution

Para **cálculos complexos** ou manipulação de dados:

```python
# Cálculos avançados
"Calculate compound interest: R$ 10,000 at 5% annual for 10 years"
# → Executa:
# principal = 10000
# rate = 0.05
# years = 10
# result = principal * (1 + rate) ** years
# → R$ 16,288.95

# Análise estatística
"Find outliers in this data: [1, 2, 3, 100, 2, 3, 4]"
# → Usa numpy/pandas para calcular

# Parsing de dados
"Parse this JSON and extract all names: {'users': [...]}"
# → Executa código Python para extrair

# Matemática complexa
"Calculate the factorial of 15"
"What's the standard deviation of [10, 20, 30, 40, 50]?"
```

**✅ Vantagem:** Sem limitação de complexidade matemática.

#### 3B. Web Search (Opcional)

Para informações **atuais** ou **externas**:

```python
# Legislação recente
"What are the new SPED fiscal requirements for 2024?"

# Taxas atuais
"What's the current SELIC interest rate?"

# Documentação oficial
"Find the official NFe 4.0 documentation"

# Mudanças recentes
"Recent changes in ICMS-ST legislation"
```

**✅ Vantagem:** Informação sempre atualizada.

---

## 🔗 Consultas Híbridas (Multi-Tool)

O agente pode **encadear múltiplas capacidades**:

```python
# Tier 2 → Tier 3
"Get all January invoices, then calculate the average using Python"
# 1. search_invoices_database (Tier 2)
# 2. python_repl para calcular média (Tier 3)

# Tier 3 → Tier 2
"Search online for CFOP 5102 definition, then find all invoices using it"
# 1. web_search para definição (Tier 3)
# 2. search_invoices_database com filtro (Tier 2)

# Tier 1 → Tier 3
"Explain depreciation, then calculate it for R$ 50k over 10 years"
# 1. Explica conceito (Tier 1 - conhecimento)
# 2. python_repl para calcular (Tier 3)

# Tier 2 → Tier 1
"Generate tax report, then explain what each tax means"
# 1. fiscal_report_export (Tier 2)
# 2. Explica ICMS, IPI, PIS, COFINS (Tier 1)
```

---

## ⚙️ Configuração Avançada

### Modelos Disponíveis

```python
# Mais rápido e barato
agent = create_agent(
    api_key="...",
    model_name="gemini-2.0-flash-exp",  # Recomendado
)

# Mais inteligente (para casos complexos)
agent = create_agent(
    api_key="...",
    model_name="gemini-1.5-pro",
)
```

### Temperature

```python
# Mais determinístico (respostas consistentes)
agent = create_agent(
    api_key="...",
    temperature=0.0,  # Sempre mesma resposta
)

# Balanceado (padrão)
agent = create_agent(
    api_key="...",
    temperature=0.7,  # Criativo mas controlado
)

# Mais criativo
agent = create_agent(
    api_key="...",
    temperature=1.0,  # Respostas variadas
)
```

### Capacidades Dinâmicas

```python
# Apenas fiscal tools (sem code/web)
agent = create_agent(
    api_key="...",
    enable_web_search=False,
    enable_code_execution=False,
)

# Com código Python (padrão)
agent = create_agent(
    api_key="...",
    enable_code_execution=True,
)

# Com busca web (requer configuração)
agent = create_agent(
    api_key="...",
    enable_web_search=True,  # DuckDuckGo
)
```

---

## 🔍 Verificando Capacidades

```python
agent = create_agent(api_key="...")

# Ver o que está habilitado
capabilities = agent.get_capabilities()

print(capabilities)
# {
#   "model": "gemini-2.0-flash-exp",
#   "temperature": 0.7,
#   "total_tools": 15,
#   "fiscal_tools": 13,
#   "web_search_enabled": False,
#   "code_execution_enabled": True,
#   "capabilities": {
#     "native_intelligence": {"enabled": True, "features": [...]},
#     "specialized_tools": {"enabled": True, "count": 13},
#     "dynamic_capabilities": {"web_search": False, "code_execution": True}
#   }
# }
```

---

## 🎓 Melhores Práticas

### 1. Deixe o Agente Decidir

❌ **Não force o uso de tools:**
```python
# Ruim
"Use a ferramenta search_invoices_database para mostrar quantas notas temos"
```

✅ **Deixe o agente escolher:**
```python
# Bom
"Quantas notas fiscais temos?"
# → Agente automaticamente usa search_invoices_database
```

### 2. Seja Natural

❌ **Não use comandos técnicos:**
```python
"Execute SQL: SELECT COUNT(*) FROM invoices"
```

✅ **Pergunte naturalmente:**
```python
"Quantos documentos existem no banco?"
```

### 3. Use Tier Apropriado

Para conceitos, **não peça relatórios**:

❌ **Ruim:**
```python
"Gere relatório explicando o que é ICMS"
```

✅ **Bom:**
```python
"O que é ICMS?"
# → Responde diretamente (mais rápido)
```

### 4. Combine Capacidades

✅ **Aproveite o híbrido:**
```python
"Explique o que é depreciação e calcule para um ativo de R$ 50.000 em 10 anos"
# → Explica (Tier 1) + Calcula (Tier 3)
```

---

## 🚨 Limitações e Segurança

### Execução de Código Python

**O que PODE fazer:**
- ✅ Cálculos matemáticos
- ✅ Manipulação de strings
- ✅ Parsing de JSON/CSV (em memória)
- ✅ Bibliotecas padrão: math, datetime, re, etc.
- ✅ pandas, numpy (se instalados)

**O que NÃO PODE fazer:**
- ❌ Acessar arquivos do sistema
- ❌ Fazer requisições de rede
- ❌ Executar subprocess
- ❌ Usar eval() ou exec() externo
- ❌ Importar módulos não seguros

### Busca Web

- ⚠️ Requer configuração do DuckDuckGo
- ⚠️ Resultados podem não ser 100% precisos
- ⚠️ Use com moderação (rate limits)

---

## 📊 Comparação: Antigo vs Híbrido

| Capacidade | Agente Antigo | Hybrid Agent |
|-----------|---------------|--------------|
| **Explicar conceitos** | ❌ "Não tenho tool" | ✅ Explica diretamente |
| **Calcular** | ❌ Limitado | ✅ Cálculos complexos |
| **Gerar código** | ❌ Não | ✅ Python completo |
| **Buscar BD** | ✅ Sim | ✅ Sim |
| **Gerar relatórios** | ✅ Sim | ✅ Sim |
| **Validar docs** | ✅ Sim | ✅ Sim |
| **Busca web** | ❌ Não | ✅ Sim (opcional) |
| **Exec Python** | ❌ Não | ✅ Sim |
| **Encadear tools** | ⚠️ Limitado | ✅ Ilimitado |

---

## 🎯 Casos de Uso Reais

### 1. Suporte ao Usuário

```python
User: "O que significa este erro: CFOP inválido?"
Agent: [explica CFOP, lista valores válidos, sugere correção]
# → Tier 1 (conhecimento) + possível Tier 2 (busca exemplos no BD)
```

### 2. Análise de Dados

```python
User: "Mostre os top 10 fornecedores e calcule a variação % mês a mês"
Agent: [gera relatório + executa Python para calcular variações]
# → Tier 2 (report) + Tier 3 (Python)
```

### 3. Compliance

```python
User: "Verifique se temos documentos com ICMS-ST incorreto"
Agent: [busca no BD, valida cada um, lista problemas]
# → Tier 2 (search + validate)
```

### 4. Onboarding

```python
User: "Como funciona o sistema? Quais relatórios posso gerar?"
Agent: [explica sistema, lista 18 tipos de relatórios com exemplos]
# → Tier 1 (conhecimento do sistema)
```

---

## 🔧 Troubleshooting

### Agente não usa tools quando deveria

**Possível causa:** Query muito vaga

```python
# Vago
"Me ajude com notas fiscais"

# Específico
"Quantas notas fiscais de compra temos no banco?"
```

### Erros de código Python

**Possível causa:** Código complexo demais

```python
# Complexo
"Execute machine learning model on invoices"

# Simples
"Calculate average value of invoices"
```

### Respostas genéricas

**Possível causa:** Temperature muito baixa

```python
# Aumente temperature para respostas mais elaboradas
agent = create_agent(api_key="...", temperature=0.8)
```

---

## 📚 Referências

- **Código:** `src/agent/hybrid_agent.py`
- **Wrapper:** `src/agent/agent_core.py`
- **Exemplos:** `examples/demo_hybrid_agent.py`
- **Tools:** `docs/AGENT_VERIFICATION.md`

---

**O Hybrid Agent transforma o sistema em um assistente verdadeiramente inteligente, capaz de se virar e adaptar a qualquer requisição do usuário!** 🚀
