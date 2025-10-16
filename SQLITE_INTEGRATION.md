# 💾 Integração com SQLite - Guia Completo

## ✅ O que foi implementado

O sistema agora possui integração completa com SQLite para **persistência automática** de todos os documentos fiscais processados!

### 🎯 Principais Funcionalidades

#### 1. **Salvamento Automático**

- ✅ Todos os XMLs processados são salvos automaticamente
- ✅ Funciona tanto no upload via UI quanto no chat
- ✅ Não duplica documentos (verifica chave de acesso)
- ✅ Salva itens, impostos e issues de validação

#### 2. **Consulta via Agente LLM**

- ✅ Agente pode buscar documentos no banco
- ✅ Filtra por tipo, emitente, período
- ✅ Retorna estatísticas e totais
- ✅ Responde perguntas sobre histórico

#### 3. **Performance Otimizada**

- ✅ Índices em campos-chave (document_key, CNPJ, data)
- ✅ Consultas rápidas com SQLModel
- ✅ Relacionamentos eficientes (invoices → items → issues)

---

## 📊 Estrutura do Banco de Dados

### Tabela: `invoices`

```sql
- id (PK)
- document_type (NFe, NFCe, CTe, MDFe)
- document_key (UNIQUE, 44 dígitos)
- document_number, series
- issue_date
- issuer_cnpj, issuer_name
- recipient_cnpj_cpf, recipient_name
- total_products, total_taxes, total_invoice
- tax_icms, tax_ipi, tax_pis, tax_cofins, tax_issqn
- raw_xml
- parsed_at, created_at
```

### Tabela: `invoice_items`

```sql
- id (PK)
- invoice_id (FK)
- item_number, product_code, description
- ncm, cfop, unit
- quantity, unit_price, total_price
- tax_icms, tax_ipi, tax_pis, tax_cofins, tax_issqn
```

### Tabela: `validation_issues`

```sql
- id (PK)
- invoice_id (FK)
- code, severity, message
- field, suggestion
- resolved
- created_at
```

---

## 🚀 Como Usar

### 1. **Processar e Salvar Documentos**

**Via Upload (Automático)**:

```bash
streamlit run src/ui/app.py
```

1. Vá para aba "📤 Upload"
2. Selecione XML/ZIP
3. Clique em "🔍 Process All Files"
4. ✅ **Salvamento automático no banco!**

**Via Chat (Automático)**:

```bash
# Cole XML no chat
```

1. Cole o conteúdo XML
2. Agente parseia e valida
3. ✅ **Salvamento automático no banco!**

### 2. **Consultar Histórico via Chat**

**Exemplos de perguntas:**

```
Quantos documentos temos no banco?
```

→ Usa `get_database_statistics` tool

```
Mostre os documentos processados esta semana
```

→ Usa `search_invoices_database` com days_back=7

```
Buscar NFes do emitente CNPJ 12345678000190
```

→ Usa `search_invoices_database` com filtros

```
Qual o valor total dos documentos processados?
```

→ Usa `get_database_statistics` e mostra total_value

### 3. **API Python Direta**

```python
from src.database.db import DatabaseManager

# Conectar ao banco
db = DatabaseManager("sqlite:///fiscal_documents.db")

# Buscar todos os documentos
invoices = db.get_all_invoices(limit=50)

# Buscar com filtros
nfes = db.search_invoices(
    document_type="NFe",
    start_date=datetime(2024, 1, 1),
    limit=100
)

# Estatísticas
stats = db.get_statistics()
print(f"Total: {stats['total_invoices']} documentos")
print(f"Valor: R$ {stats['total_value']:,.2f}")

# Buscar por chave
invoice = db.get_invoice_by_key("35240112345...")
print(f"Emitente: {invoice.issuer_name}")
print(f"Itens: {len(invoice.items)}")
print(f"Issues: {len(invoice.issues)}")
```

---

## 🛠️ Ferramentas do Agente

### `search_invoices_database`

**Descrição**: Busca documentos no banco com filtros

**Parâmetros**:

- `document_type` (opcional): "NFe", "NFCe", "CTe", "MDFe"
- `issuer_cnpj` (opcional): CNPJ do emitente (14 dígitos)
- `days_back` (opcional): Buscar últimos N dias (padrão: 7)

**Retorna**: Lista formatada de documentos com:

- Tipo, número, chave
- Emitente (nome e CNPJ)
- Data de emissão
- Valor total
- Quantidade de itens
- Status de validação

### `get_database_statistics`

**Descrição**: Retorna estatísticas gerais do banco

**Parâmetros**: Nenhum

**Retorna**:

- Total de documentos
- Total de itens cadastrados
- Total de issues de validação
- Valor total acumulado
- Breakdown por tipo de documento

---

## 📈 Benefícios da Integração

### ✅ Para o Usuário

1. **Histórico persistente** - Dados não se perdem
2. **Busca rápida** - Encontre qualquer documento em segundos
3. **Análises** - Compare períodos, emitentes, totais
4. **Auditoria** - Rastreie tudo que foi processado

### ✅ Para o Agente LLM

1. **Memória de longo prazo** - Acessa dados de sessões anteriores
2. **Consultas inteligentes** - Responde perguntas sobre histórico
3. **Análise de tendências** - Identifica padrões
4. **Relatórios automáticos** - Gera insights sem intervenção

### ✅ Performance

1. **Índices otimizados** - Consultas rápidas
2. **Relacionamentos** - Joins eficientes
3. **Paginação** - Não sobrecarrega memória
4. **Cache local** - SQLite é rápido

---

## 🔒 Segurança e Privacidade

- ✅ Banco local (SQLite) - Dados ficam na máquina do usuário
- ✅ Sem conexão externa necessária
- ✅ CNPJs indexados mas podem ser redacted em logs
- ⚠️ XML completo salvo em `raw_xml` (para auditoria)

**Nota**: Para produção, considere:

- Criptografar o arquivo `.db`
- Implementar controle de acesso
- Backup automático do banco

---

## 📁 Localização do Banco

**Padrão**: `fiscal_documents.db` no diretório raiz do projeto

**Personalizar**:

```python
# Na inicialização
db = DatabaseManager("sqlite:///caminho/customizado.db")

# No FileProcessor
processor = FileProcessor(database_url="sqlite:///meu_banco.db")
```

---

## 🧪 Testes

```bash
# Testar funcionalidade do banco
pytest tests/test_database.py -v

# Todos os testes
pytest -v
```

**Cobertura de testes**:

- ✅ Salvamento de invoices
- ✅ Busca por chave
- ✅ Detecção de duplicatas
- ✅ Filtros de busca
- ✅ Estatísticas
- ✅ Exclusão de documentos

---

## 🎯 Próximos Passos

### Implementado:

- ✅ Schema completo do banco
- ✅ Salvamento automático
- ✅ Ferramentas LangChain para o agente
- ✅ Consultas via chat
- ✅ Estatísticas

### Pendente:

- 🚧 Aba "Histórico" na UI Streamlit
- 🚧 Exportação de dados (CSV/Excel)
- 🚧 Gráficos e visualizações
- 🚧 Backup automático
- 🚧 Migration tools

---

## 💡 Exemplos de Uso Avançado

### 1. Análise Mensal

```python
# Via chat
"Mostre o total processado em janeiro de 2024"
```

### 2. Comparação de Emitentes

```python
# Via chat
"Compare os valores entre os 3 principais emitentes"
```

### 3. Auditoria de Erros

```python
# Via Python
db = DatabaseManager()
invoices = db.get_all_invoices()

for inv in invoices:
    errors = [i for i in inv.issues if i.severity == 'error']
    if errors:
        print(f"{inv.document_key}: {len(errors)} erros")
```

---

## ✨ Conclusão

A integração com SQLite transforma o agente fiscal em um sistema completo de **gestão de documentos** com:

1. **Persistência** - Nunca perca dados
2. **Inteligência** - LLM acessa histórico
3. **Performance** - Consultas otimizadas
4. **Flexibilidade** - APIs Python + Chat

**Tudo funcionando automaticamente!** 🎉
