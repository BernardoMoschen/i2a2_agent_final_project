# 💾 Como os Dados São Armazenados - Guia Completo

## 🎯 Resposta Direta

**NÃO, o agente NÃO grava dados em memória!**

Tudo é **persistido em disco** em um banco de dados **SQLite** físico que fica no servidor. Veja:

```bash
📁 /home/bmos/.../projeto_final/
└── fiscal_documents.db  ← Arquivo físico de 236 KB no disco
    ├── invoices (20 documentos salvos)
    ├── invoice_items
    └── validation_issues
```

---

## 🔄 Fluxo Completo de Armazenamento

### 1️⃣ **Upload do Arquivo (Streamlit UI)**

```python
# src/ui/app.py - linha 108
uploaded_files = st.file_uploader(
    "Choose XML or ZIP files",
    type=["xml", "zip"],
    accept_multiple_files=True,
)

# Quando o usuário faz upload:
# - O arquivo fica temporariamente na memória do Streamlit
# - É um objeto UploadedFile (bytes)
```

### 2️⃣ **Processamento Automático**

```python
# src/ui/app.py - linha 118
if st.button("🔍 Process All Files"):
    processor = FileProcessor()  # ← INICIALIZA COM BANCO

    # src/utils/file_processing.py - linha 20
    def __init__(self, save_to_db: bool = True):  # ← DEFAULT = True!
        self.parser = XMLParserTool()
        self.save_to_db = save_to_db

        if save_to_db:
            self.db = DatabaseManager("sqlite:///fiscal_documents.db")
            #                           ↑
            #                   CRIA CONEXÃO COM BANCO FÍSICO
```

### 3️⃣ **Salvamento AUTOMÁTICO no Banco**

```python
# src/utils/file_processing.py - linha 136-144
def _process_xml(self, xml_content: bytes, filename: str):
    # 1. Parse XML
    invoice = self.parser.parse(xml_content)

    # 2. Valida
    issues = self.validator.validate(invoice)

    # 3. Classifica
    classification = self.classifier.classify(invoice)

    # 4. ⭐ SALVA NO BANCO (AUTOMÁTICO!) ⭐
    if self.save_to_db:
        self.db.save_invoice(invoice, issues, classification)
        logger.info(f"Saved {invoice.document_key} to database")
        #            ↑
        #   GRAVAÇÃO EM DISCO ACONTECE AQUI!
```

### 4️⃣ **Gravação Física no SQLite**

```python
# src/database/db.py - linha 134-230
class DatabaseManager:
    def __init__(self, database_url: str = "sqlite:///fiscal_documents.db"):
        self.engine = create_engine(database_url)  # ← SQLAlchemy
        self._create_tables()  # ← Cria tabelas se não existirem

    def save_invoice(self, invoice_model, validation_issues, classification):
        with Session(self.engine) as session:
            # Cria registro no banco
            invoice_db = InvoiceDB(
                document_key=invoice_model.document_key,
                document_number=invoice_model.document_number,
                issuer_cnpj=invoice_model.issuer_cnpj,
                # ... todos os campos ...
                operation_type=classification["operation_type"],  # ← Classificação
                cost_center=classification["cost_center"],
                raw_xml=invoice_model.raw_xml,  # ← XML completo!
            )

            session.add(invoice_db)  # ← Adiciona na sessão
            session.commit()         # ← ⭐ GRAVA NO DISCO! ⭐
            #        ↑
            #  AQUI O SQLITE ESCREVE NO ARQUIVO .db
```

---

## 🗄️ Estrutura do Banco Físico

```
fiscal_documents.db (arquivo no disco - 236 KB)
│
├─ invoices (tabela principal)
│  ├─ id (PRIMARY KEY)
│  ├─ document_key (UNIQUE - 44 dígitos)
│  ├─ document_type, number, series
│  ├─ issuer_cnpj, issuer_name
│  ├─ recipient_cnpj_cpf, recipient_name
│  ├─ total_products, total_taxes, total_invoice
│  ├─ operation_type ← CLASSIFICAÇÃO
│  ├─ cost_center ← CLASSIFICAÇÃO
│  ├─ classification_confidence
│  ├─ raw_xml ← XML COMPLETO ARMAZENADO!
│  └─ created_at, parsed_at
│
├─ invoice_items (itens de cada nota)
│  ├─ id
│  ├─ invoice_id (FOREIGN KEY → invoices.id)
│  ├─ product_code, description
│  ├─ ncm, cfop, quantity, unit_price
│  └─ tax_icms, tax_ipi, tax_pis, tax_cofins
│
└─ validation_issues (problemas encontrados)
   ├─ id
   ├─ invoice_id (FOREIGN KEY → invoices.id)
   ├─ code (ex: "NCM001", "CFOP002")
   ├─ severity ("error" ou "warning")
   ├─ message, field, suggestion
   └─ created_at
```

---

## 📊 Verificação no Sistema

Você pode verificar que os dados estão salvos:

```python
# Via Python
import sqlite3
conn = sqlite3.connect('fiscal_documents.db')
cursor = conn.cursor()

# Ver quantos documentos estão salvos
cursor.execute('SELECT COUNT(*) FROM invoices')
print(f"Total: {cursor.fetchone()[0]}")  # Resultado: 20 documentos

# Ver último documento salvo
cursor.execute('''
    SELECT document_key, issuer_name, operation_type, cost_center
    FROM invoices
    ORDER BY created_at DESC
    LIMIT 1
''')
print(cursor.fetchone())
```

---

## 🔍 O Agente LLM e o Banco

**Importante:** O agente LLM (Gemini) **NÃO tem acesso direto ao banco**!

### Como Funciona:

```
┌──────────────────────────────────────────────────────┐
│ USUÁRIO: "Mostrar vendas de hoje"                   │
└───────────────┬──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────┐
│ AGENTE LLM (Gemini)                                  │
│ • Analisa a pergunta                                 │
│ • Decide usar ferramenta: search_invoices_database   │
│ • Gera parâmetros: {operation_type: 'sale', ...}     │
└───────────────┬──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────┐
│ TOOL: DatabaseSearchTool                             │
│ • Recebe parâmetros do agente                        │
│ • Conecta no banco SQLite                            │
│ • Executa query SQL                                  │
│ • Retorna resultados para o agente                   │
└───────────────┬──────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────────────────┐
│ AGENTE LLM                                           │
│ • Recebe dados do banco                              │
│ • Formata resposta em linguagem natural             │
│ • Retorna para o usuário                             │
└──────────────────────────────────────────────────────┘
```

### Código da Tool:

```python
# src/agent/tools.py - linha 234
class DatabaseSearchTool(BaseTool):
    name: str = "search_invoices_database"

    def _run(self, **filters) -> str:
        # 1. Conecta no banco físico
        db = DatabaseManager("sqlite:///fiscal_documents.db")

        # 2. Busca no banco
        invoices = db.search_invoices(**filters)
        #              ↑
        #     QUERY SQL NO SQLITE

        # 3. Formata resultado para o LLM
        return format_results(invoices)
```

---

## 💡 Diferenças Cruciais: Memória vs Disco

### ❌ Se Fosse em Memória (NÃO É ASSIM):

```python
# EXEMPLO DO QUE NÃO FAZEMOS
class BadProcessor:
    def __init__(self):
        self.invoices = []  # ← Lista em RAM

    def process(self, xml):
        invoice = parse(xml)
        self.invoices.append(invoice)  # ← Só na memória

# PROBLEMA: Se reiniciar app, PERDE TUDO! ❌
```

### ✅ Como Realmente Funciona (Com SQLite):

```python
class FileProcessor:
    def __init__(self):
        self.db = DatabaseManager()  # ← Conexão com arquivo .db

    def process(self, xml):
        invoice = parse(xml)
        self.db.save_invoice(invoice)  # ← GRAVA NO DISCO
        #        ↑
        #  PERSISTE MESMO SE REINICIAR! ✅
```

---

## 🔄 Ciclo de Vida dos Dados

```
┌─────────────────────────────────────────────────────┐
│ 1. UPLOAD                                           │
│    • Arquivo XML em memória temporária (Streamlit)  │
│    • Dura alguns segundos                           │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 2. PROCESSAMENTO                                    │
│    • InvoiceModel criado em memória (Pydantic)      │
│    • Validação e classificação em memória           │
│    • Dura milissegundos                             │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 3. PERSISTÊNCIA ⭐                                  │
│    • INSERT no banco SQLite                         │
│    • Gravação física em fiscal_documents.db         │
│    • PERMANENTE - fica no disco                     │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 4. CONSULTA (quando necessário)                     │
│    • SELECT do banco SQLite                         │
│    • Dados carregados em memória temporariamente    │
│    • Exibidos na UI ou usados pelo agente           │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Onde Estão os Dados?

### Banco de Dados:

```bash
/home/bmos/private/private_repos/i2a2/projeto_final/
└── fiscal_documents.db  ← 236 KB, 20 documentos salvos
```

### XMLs Originais (se arquivado):

```bash
/home/bmos/private/private_repos/i2a2/projeto_final/
└── archives/
    └── 2024/
        └── 11222333000181/  ← CNPJ do emitente
            └── NFe/
                ├── 35240...67890.xml
                └── 35240...67890_metadata.json
```

---

## 🎯 Resumo Final

| Aspecto              | Como Funciona                                   |
| -------------------- | ----------------------------------------------- |
| **Upload**           | Arquivo em memória temporária (Streamlit)       |
| **Parsing**          | Cria objeto Python em memória (segundos)        |
| **Validação**        | Processa regras em memória (milissegundos)      |
| **Classificação**    | LLM ou regras em memória (1-2 segundos)         |
| **⭐ Armazenamento** | **SQLite no disco - PERMANENTE**                |
| **XML Original**     | Salvo como string dentro do banco SQLite        |
| **Consultas**        | Lê do banco, carrega temporariamente na memória |
| **Agente**           | Usa ferramentas que consultam o banco           |
| **Persistência**     | Sobrevive a reinicializações do app ✅          |

---

## 🔐 Segurança e Integridade

### Proteções Implementadas:

1. **Parsing Seguro**

   - Uso de `defusedxml` para prevenir XXE attacks
   - Validação de estrutura XML antes do processamento

2. **Precisão Numérica**

   - Uso de `Decimal` para valores monetários
   - Evita erros de arredondamento com float

3. **Validação de Duplicatas**

   - Chave única no `document_key`
   - Impede inserção do mesmo documento 2x

4. **Transações Atômicas**

   - SQLite garante consistência com ACID
   - Rollback automático em caso de erro

5. **Logging Completo**

   - Rastreabilidade de todas as operações
   - Auditoria de processamento

6. **PII Redaction**
   - Opção de reduzir dados sensíveis em logs
   - Proteção de informações fiscais

---

## 🚀 Performance e Escalabilidade

### Otimizações Atuais:

```python
# Índices criados automaticamente
class InvoiceDB(SQLModel, table=True):
    document_key: str = Field(unique=True, index=True)  # ← Busca rápida
    issuer_cnpj: str = Field(index=True)                # ← Filtro por CNPJ
    issue_date: datetime = Field(index=True)            # ← Filtro por data
    operation_type: str = Field(index=True)             # ← Classificação
    cost_center: str = Field(index=True)                # ← Classificação
```

### Capacidade:

- **Atual**: SQLite suporta até ~281 TB
- **Documentos**: Testado com 20, suporta milhões
- **Consultas**: Milissegundos com índices
- **Batch Upload**: Processa múltiplos XMLs em paralelo

### Migração Futura:

Se precisar escalar para PostgreSQL:

```python
# Apenas mudar a connection string!
db = DatabaseManager("postgresql://user:pass@host/dbname")
# O código SQLModel funciona sem alterações ✅
```

---

## 🛠️ Troubleshooting

### Problema: "Banco de dados travado"

```bash
# Verificar processos usando o banco
lsof fiscal_documents.db

# Fechar conexões abertas
pkill -f streamlit
```

### Problema: "Dados não aparecem"

```python
# Verificar se save_to_db está habilitado
processor = FileProcessor(save_to_db=True)  # ← Deve ser True

# Verificar logs
tail -f logs/app.log | grep "Saved"
```

### Problema: "Banco corrompido"

```bash
# Backup
cp fiscal_documents.db fiscal_documents.db.backup

# Verificar integridade
sqlite3 fiscal_documents.db "PRAGMA integrity_check;"

# Recuperar (se necessário)
sqlite3 fiscal_documents.db ".recover" > recovered.sql
```

---

## 📚 Referências

- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **SQLModel**: https://sqlmodel.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Streamlit File Uploads**: https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader

---

## 🎓 Conclusão

**O sistema implementa persistência completa e profissional:**

- ✅ Todos os dados são salvos em disco (SQLite)
- ✅ Classificação automática integrada ao banco
- ✅ XMLs originais preservados no banco
- ✅ Agente acessa dados via ferramentas (não diretamente)
- ✅ Sobrevive a reinicializações
- ✅ Pronto para produção
- ✅ Fácil migração para PostgreSQL se necessário

**Nenhum dado é perdido e tudo é rastreável!** 🚀
