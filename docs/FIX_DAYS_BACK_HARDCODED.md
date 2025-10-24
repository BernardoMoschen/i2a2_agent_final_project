# Fix: Hardcoded days_back=9999 for Operation Type Queries

## Problem Identified

Even after fixing the default `days_back` to 3650 and adding explicit instructions to the LLM, the agent **still sometimes** didn't use `days_back=9999` when counting documents by operation type.

**User Query:**

```
"quantos arquivos de purchase nos temos no ano de 2024?"
```

**Agent Response (Wrong):**

```
❌ No momento, não há arquivos de compra registrados no banco de dados para o ano de 2024.
```

**Reality:**

- 2 purchase documents exist in database (from Jan 2024)
- Agent didn't use `days_back=9999`, so it couldn't find them

## Root Cause

LLM instruction reliance is not deterministic:

- Even with explicit instructions in tool description
- Even with examples in the prompt
- LLM may still choose default values or inappropriate parameters

## Solution: 3-Layer Defense

### Layer 1: Default Value (3650 days)

```python
days_back: int = Field(3650, description="Default is 3650 (10 years)")
```

✅ Covers 10 years of fiscal documents (retention period)

### Layer 2: LLM Instructions (Explicit)

```python
description: str = """
🚨 CRITICAL: When user asks about counting or listing documents, you MUST use days_back=9999!

⚠️ MANDATORY RULES (YOU MUST FOLLOW):
1. ANY question with "quantas", "quantos", "how many", "count" → days_back=9999
2. ANY question about a specific YEAR (2024, 2023, etc.) → days_back=9999
3. ANY question with "todas", "todos", "all", "list" → days_back=9999
...
"""
```

✅ Provides clear instructions to LLM

### Layer 3: **Hardcoded Enforcement** (NEW - Most Critical!)

```python
def _run(self, operation_type: Optional[str] = None, ..., days_back: int = 3650) -> str:
    # 🚨 CRITICAL FIX: Force days_back=9999 when filtering by operation_type
    # This ensures we search ALL documents when user asks for counts by type
    if operation_type is not None:
        days_back = 9999
        logger.info(f"🔧 Auto-forcing days_back=9999 because operation_type filter is active")
```

✅ **GUARANTEED**: When agent filters by operation_type, it WILL search all documents

## Why This Works

**Logic:**

- If user asks about "purchase notes" → LLM will use `operation_type='purchase'`
- Our code **automatically overrides** `days_back=9999`
- No reliance on LLM following instructions
- **Deterministic behavior**

**Examples:**

```python
# User: "Quantas notas de compra?"
# LLM calls: database_search_tool._run(operation_type='purchase')
# Our code: days_back = 9999  # Auto-forced!
# Result: ✅ Finds ALL purchase documents

# User: "Quantos arquivos de purchase no ano de 2024?"
# LLM calls: database_search_tool._run(operation_type='purchase')
# Our code: days_back = 9999  # Auto-forced!
# Result: ✅ Finds ALL purchase documents (including 2024)
```

## Validation Test

```bash
python -c "
from src.agent.tools import database_search_tool

# Simulate agent calling with operation_type='purchase'
result = database_search_tool._run(operation_type='purchase')
print(result)
"
```

**Output:**

```
📊 Encontrados 2 documento(s):

Por Tipo de Operação:
- 📥 Compras: 2

📥 NFe - 3510129/1 | Compra
   🏢 Emitente: COMPANHIA BRASILEIRA DE EDUC. E SIST. DE
   📅 Data: 18/01/2024
   💰 Valor: R$ 522.50

📥 NFe - 1/1 | Compra
   🏢 Emitente: FORNECEDOR TESTE LTDA
   📅 Data: 15/01/2024
   💰 Valor: R$ 1,000.00

Resumo Final:
- 📄 Total de documentos: 2
- 💰 Valor total: R$ 1,522.50
```

✅ **SUCCESS!** Auto-forced `days_back=9999` finds both 2024 documents.

## Benefits

1. **Reliability:** No dependency on LLM following instructions
2. **Performance:** Still efficient for operation-type queries (most common use case)
3. **User Experience:** Queries like "quantas compras?" always return complete results
4. **Maintainability:** Single point of enforcement in code

## Trade-offs

**Why not always force days_back=9999?**

- May be inefficient for date-range queries ("last 30 days")
- Operation type queries are the primary counting use case
- Provides best balance between UX and performance

**Why operation_type trigger?**

- Operation type queries are almost always counting queries ("quantas compras?")
- Very rare to ask "purchases from last 30 days only"
- Safe assumption that operation_type = need full dataset

## Files Modified

1. **src/agent/tools.py**
   - Added `import logging` and `logger = logging.getLogger(__name__)`
   - Updated `DatabaseSearchTool.description` with enhanced instructions
   - Added hardcoded enforcement in `_run()` method:
     ```python
     if operation_type is not None:
         days_back = 9999
         logger.info(f"🔧 Auto-forcing days_back=9999 because operation_type filter is active")
     ```

## Testing Recommendation

Test these queries in Streamlit Chat:

1. "Quantas notas de compra temos no sistema?"
2. "Quantos arquivos de purchase no ano de 2024?"
3. "How many sales do we have?"
4. "Mostre todas as transferências"

Expected: All should return accurate counts with full historical data.

## Conclusion

This 3-layer approach ensures:

- ✅ Default covers fiscal retention period (10 years)
- ✅ LLM has clear instructions (for edge cases)
- ✅ **Code guarantees correct behavior** (for common operation-type queries)

The hardcoded enforcement is the **critical piece** that makes agent queries reliable and predictable.
