# Otimizações de Banco de Dados - SQLite Performance

## 📊 Análise Atual e Oportunidades de Otimização

### Estado Atual

- **Banco**: SQLite (bom para desenvolvimento e small-medium workloads)
- **Tabelas**: 4 (invoices, invoice_items, validation_issues, classification_cache)
- **Índices**: 15 índices criados automaticamente pelos Fields
- **Relacionamentos**: Cascata de deleção configurada
- **Transações**: Não otimizadas para batch insert

---

## 🚀 Otimizações Implementáveis

### 1️⃣ **SQLite Performance Pragmas** (CRÍTICO)

**Problema**: SQLite usa configurações conservadoras por default.

**Solução**: Adicionar PRAGMAs na conexão para otimizar performance.

```python
# Em DatabaseManager.__init__()
from sqlalchemy import event

@event.listens_for(self.engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    # Journal mode WAL permite leituras concorrentes
    cursor.execute("PRAGMA journal_mode=WAL")
    # Sincronização otimizada (NORMAL é seguro e mais rápido)
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Cache de páginas maior (10MB)
    cursor.execute("PRAGMA cache_size=-10000")
    # Habilita chaves estrangeiras
    cursor.execute("PRAGMA foreign_keys=ON")
    # Temp store em memória
    cursor.execute("PRAGMA temp_store=MEMORY")
    # Mmap para leituras mais rápidas (256MB)
    cursor.execute("PRAGMA mmap_size=268435456")
    cursor.close()
```

**Impacto**:

- ✅ **2-5x mais rápido** em operações de escrita
- ✅ **Leituras concorrentes** sem bloqueio
- ✅ **Menor latência** em queries

---

### 2️⃣ **Bulk Insert API** (ALTO IMPACTO)

**Problema**: `save_invoice()` faz commit individual (lento para batches).

**Solução**: Criar método para batch insert.

```python
def save_invoices_batch(
    self,
    invoices_data: List[Tuple[InvoiceModel, List, Optional[dict]]]
) -> List[InvoiceDB]:
    """
    Save multiple invoices in a single transaction.

    Args:
        invoices_data: List of (invoice_model, validation_issues, classification)

    Returns:
        List of saved InvoiceDB instances
    """
    saved = []

    with Session(self.engine) as session:
        for invoice_model, validation_issues, classification in invoices_data:
            # Check duplicates
            existing = session.exec(
                select(InvoiceDB).where(
                    InvoiceDB.document_key == invoice_model.document_key
                )
            ).first()

            if existing:
                logger.warning(f"Skipping duplicate: {invoice_model.document_key}")
                saved.append(existing)
                continue

            # Create invoice (sem commit individual)
            invoice_db = self._create_invoice_db(invoice_model, classification)
            session.add(invoice_db)
            session.flush()  # Get ID without committing

            # Add items and issues
            for item in invoice_model.items:
                item_db = self._create_item_db(invoice_db.id, item)
                session.add(item_db)

            for issue in validation_issues:
                issue_db = self._create_issue_db(invoice_db.id, issue)
                session.add(issue_db)

            saved.append(invoice_db)

        # Single commit for all
        session.commit()

        # Refresh all at once
        for inv in saved:
            session.refresh(inv)

    return saved
```

**Impacto**:

- ✅ **10-50x mais rápido** para importar ZIP com múltiplos XMLs
- ✅ Reduz I/O disk (um único commit)
- ✅ Transação atômica (all-or-nothing)

---

### 3️⃣ **Índices Compostos** (MÉDIO IMPACTO)

**Problema**: Queries com múltiplos filtros fazem full scan.

**Solução**: Criar índices compostos para queries comuns.

```python
from sqlalchemy import Index

class InvoiceDB(SQLModel, table=True):
    # ... campos existentes ...

    # Índices compostos para queries frequentes
    __table_args__ = (
        # Busca por período + tipo
        Index('ix_invoices_date_type', 'issue_date', 'document_type'),

        # Busca por emitente + período
        Index('ix_invoices_issuer_date', 'issuer_cnpj', 'issue_date'),

        # Busca por destinatário + período
        Index('ix_invoices_recipient_date', 'recipient_cnpj_cpf', 'issue_date'),

        # Busca por centro de custo + tipo operação
        Index('ix_invoices_cost_center_op', 'cost_center', 'operation_type'),

        # Busca transport: modal + período
        Index('ix_invoices_modal_date', 'modal', 'issue_date'),

        # Busca transport: RNTRC + tipo
        Index('ix_invoices_rntrc_type', 'rntrc', 'document_type'),
    )
```

**Impacto**:

- ✅ **5-20x mais rápido** em queries com filtros compostos
- ✅ Dashboards e relatórios mais responsivos

---

### 4️⃣ **Otimização de Relacionamentos** (BAIXO IMPACTO)

**Problema**: N+1 queries ao carregar invoice + items + issues.

**Solução**: Já está usando `selectinload` corretamente! ✅

**Verificação adicional**: Garantir uso consistente.

```python
def get_invoice_by_key(self, document_key: str) -> Optional[InvoiceDB]:
    """Get invoice with eager loading of relationships."""
    with Session(self.engine) as session:
        statement = (
            select(InvoiceDB)
            .where(InvoiceDB.document_key == document_key)
            .options(
                selectinload(InvoiceDB.items),
                selectinload(InvoiceDB.issues)
            )
        )
        return session.exec(statement).first()
```

---

### 5️⃣ **Compressão do raw_xml** (MÉDIO IMPACTO)

**Problema**: Campo `raw_xml` ocupa muito espaço (10-50KB por doc).

**Solução**: Comprimir XML antes de salvar.

```python
import gzip
import base64

class InvoiceDB(SQLModel, table=True):
    # Trocar raw_xml por compressed_xml
    compressed_xml: Optional[str] = Field(default=None)

    def set_raw_xml(self, xml_str: str):
        """Compress and store XML."""
        if xml_str:
            compressed = gzip.compress(xml_str.encode('utf-8'))
            self.compressed_xml = base64.b64encode(compressed).decode('ascii')

    def get_raw_xml(self) -> Optional[str]:
        """Decompress and return XML."""
        if self.compressed_xml:
            compressed = base64.b64decode(self.compressed_xml.encode('ascii'))
            return gzip.decompress(compressed).decode('utf-8')
        return None
```

**Impacto**:

- ✅ **70-80% redução** no tamanho do banco
- ✅ Backups mais rápidos
- ⚠️ Pequeno overhead em CPU (aceitável)

---

### 6️⃣ **Particionamento de raw_xml** (OPCIONAL)

**Problema**: raw_xml aumenta tamanho da tabela principal.

**Solução**: Mover para tabela separada.

```python
class InvoiceXMLDB(SQLModel, table=True):
    """Separate table for XML storage."""

    __tablename__ = "invoice_xmls"

    invoice_id: int = Field(foreign_key="invoices.id", primary_key=True)
    compressed_xml: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# Em InvoiceDB, adicionar relationship:
class InvoiceDB(SQLModel, table=True):
    xml_storage: Optional["InvoiceXMLDB"] = Relationship()
```

**Impacto**:

- ✅ Queries em `invoices` são mais rápidas (tabela menor)
- ✅ XML só é carregado quando necessário
- ⚠️ Complexidade adicional

---

### 7️⃣ **Cache de Queries Frequentes** (BAIXO IMPACTO)

**Problema**: Mesmas queries executadas repetidamente.

**Solução**: Usar cache em memória (functools.lru_cache).

```python
from functools import lru_cache
from datetime import datetime, timedelta

class DatabaseManager:

    @lru_cache(maxsize=100)
    def get_invoice_count_by_type(self, document_type: str) -> int:
        """Cached count query."""
        with Session(self.engine) as session:
            statement = select(InvoiceDB).where(
                InvoiceDB.document_type == document_type
            )
            return len(session.exec(statement).all())

    def clear_cache(self):
        """Clear all cached queries."""
        self.get_invoice_count_by_type.cache_clear()
```

**Impacto**:

- ✅ **Instantâneo** para queries repetidas
- ⚠️ Requer invalidação manual ao inserir/deletar

---

### 8️⃣ **Vacuum e Analyze Automático** (MANUTENÇÃO)

**Problema**: SQLite acumula espaço não usado.

**Solução**: Agendar VACUUM e ANALYZE.

```python
def optimize_database(self):
    """Run VACUUM and ANALYZE to optimize database."""
    with self.engine.begin() as conn:
        logger.info("Running VACUUM...")
        conn.exec_driver_sql("VACUUM")
        logger.info("Running ANALYZE...")
        conn.exec_driver_sql("ANALYZE")
        logger.info("Database optimization complete")
```

**Uso**: Executar mensalmente ou após bulk deletes.

---

## 📈 Priorização de Implementação

### ⚡ **CRÍTICAS (Implementar Imediatamente)**

1. ✅ **SQLite PRAGMAs** - 5 minutos, 2-5x speedup
2. ✅ **Bulk Insert API** - 30 minutos, 10-50x speedup em batches

### 🎯 **ALTAS (Implementar Esta Semana)**

3. ✅ **Índices Compostos** - 15 minutos, 5-20x speedup em queries
4. ✅ **Compressão XML** - 45 minutos, 70% redução de espaço

### 📊 **MÉDIAS (Implementar Quando Necessário)**

5. ⏳ **Particionamento XML** - 1-2 horas, queries mais rápidas
6. ⏳ **VACUUM Automático** - 30 minutos, manutenção preventiva

### 🔮 **BAIXAS (Nice to Have)**

7. ⏳ **Query Cache** - 30 minutos, benefício limitado com SQLite
8. ⏳ **Migração para PostgreSQL** - 4-8 horas, quando escalar muito

---

## 🧪 Benchmarks Esperados

### Antes das Otimizações

- **Insert single**: ~50ms
- **Insert batch (100 docs)**: ~5000ms (50ms cada)
- **Query com filtros**: ~100-500ms
- **Tamanho DB (1000 docs)**: ~50MB

### Depois das Otimizações

- **Insert single**: ~20ms (PRAGMAs)
- **Insert batch (100 docs)**: ~200ms (bulk insert)
- **Query com filtros**: ~10-50ms (índices compostos)
- **Tamanho DB (1000 docs)**: ~15MB (compressão)

**Ganho Total**: **10-25x mais rápido** + **70% menos espaço**

---

## 🔧 Implementação Passo a Passo

### Passo 1: PRAGMAs (5 min)

```python
# Adicionar em DatabaseManager.__init__()
from sqlalchemy import event

@event.listens_for(self.engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-10000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")
    cursor.close()
```

### Passo 2: Bulk Insert (30 min)

- Criar método `save_invoices_batch()`
- Testar com ZIP de 100 XMLs
- Comparar tempo antes/depois

### Passo 3: Índices Compostos (15 min)

- Adicionar `__table_args__` em InvoiceDB
- Executar migração ou recriar banco
- Testar queries de dashboard

### Passo 4: Compressão XML (45 min)

- Adicionar campo `compressed_xml`
- Criar métodos `set_raw_xml()` e `get_raw_xml()`
- Migrar dados existentes (script)
- Atualizar parsers e validators

---

## ✅ Checklist de Implementação

- [ ] Implementar SQLite PRAGMAs
- [ ] Criar bulk insert API
- [ ] Adicionar índices compostos
- [ ] Implementar compressão de XML
- [ ] Adicionar método VACUUM automático
- [ ] Criar testes de performance
- [ ] Documentar uso de bulk insert
- [ ] Atualizar FileProcessor para usar bulk

---

## 📚 Recursos Adicionais

- [SQLite Performance Tips](https://www.sqlite.org/performance.html)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/faq/performance.html)
- [WAL Mode](https://www.sqlite.org/wal.html)

---

**Data**: 28 de outubro de 2025  
**Autor**: AI Agent (GitHub Copilot)
