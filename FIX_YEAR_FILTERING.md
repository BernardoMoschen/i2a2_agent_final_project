# Fix: Year-Based Database Filtering

## Problem Statement
When users asked for statistics about a specific year (e.g., "Qual o tipo de nota mais predominante em 2024?"), the agent would return documents from ALL years without proper filtering, leading to incorrect results like "no documents found for 2024" when the database actually contained 21 documents from 2024.

## Root Cause
The database tools (`DatabaseStatsTool` and `DatabaseSearchTool`) did not have `year` and `month` parameters, forcing the agent to use `days_back=9999` which returned all documents regardless of year without any year-specific filtering.

## Solution Implemented

### 1. **Updated Input Schemas** (`src/agent/tools.py`)

#### GetStatisticsInput
Added year/month parameters:
```python
class GetStatisticsInput(BaseModel):
    year: Optional[int] = Field(None, description="Year to filter by (e.g., 2024)")
    month: Optional[int] = Field(None, description="Month to filter by (1-12), requires year")
```

#### SearchInvoicesInput
Added year/month parameters:
```python
year: Optional[int] = Field(None, description="Filter by specific year (e.g., 2024)...")
month: Optional[int] = Field(None, description="Filter by specific month (1-12), requires year...")
```

### 2. **Updated Database Layer** (`src/database/db.py`)

Modified `DatabaseManager.get_statistics()` to accept and filter by year/month:
```python
def get_statistics(self, year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Get database statistics, optionally filtered by year/month."""
    # Filters invoices by issue_date between calculated start and end dates
    # For year=2024: filters 2024-01-01 to 2024-12-31
    # For year=2024, month=1: filters 2024-01-01 to 2024-01-31
```

### 3. **Updated Tool Implementations** (`src/agent/tools.py`)

#### DatabaseStatsTool._run()
Now accepts and uses year/month parameters:
- Converts year/month to date range
- Passes to `db.get_statistics(year=year, month=month)`
- Formats response with period context (e.g., "em 2024")

#### DatabaseSearchTool._run()
Now accepts and uses year/month parameters:
- Converts year/month to start_date/end_date date range (priority: year > specific_date > days_back)
- Passes to `db.search_invoices()` with calculated dates
- Filters results to only matching year/month

### 4. **Updated LLM System Prompt** (`src/agent/prompts.py`)

Added explicit instructions for year extraction:
```
2. **SEMPRE** que o usuário mencionar um ANO específico (2024, 2023, etc.):
   → **EXTRAIA o ANO da pergunta e PASSE como parâmetro year= para search_invoices_database ou get_database_statistics**
   → Exemplo: Pergunta "Qual o tipo de nota mais predominante em 2024?"
   → Você deve chamar: search_invoices_database(year=2024) OU get_database_statistics(year=2024)
```

### 5. **Updated Tool Descriptions**

Updated search tool description to show correct usage:
```
✅ CORRECT USAGE EXAMPLES:
- "Quantas notas de compra?" → {"operation_type": "purchase", "days_back": 9999}
- "Documentos de 2024?" → {"year": 2024}
- "Compras em 2024?" → {"operation_type": "purchase", "year": 2024}
- "Documentos em janeiro/2024?" → {"year": 2024, "month": 1}
```

## Testing Results

All tests pass:

```
📊 TEST 1: All documents (no filter)
   Total: 48 ✅ PASS

📊 TEST 2: Documents from 2024
   Total: 21 ✅ PASS

📊 TEST 3: Documents from 2025
   Total: 26 ✅ PASS

📊 TEST 4: Documents from January 2024
   Total: 20 ✅ PASS

📊 TEST 5: Documents from October 2024
   Total: 1 ✅ PASS

📊 TEST 6: Search invoices from 2024
   Found: 21 ✅ PASS
```

## User-Facing Behavior

### Before Fix
```
User: "Qual o tipo de nota mais predominante em 2024?"
Agent: "Todos os 48 documentos encontrados são NFe. 
        As datas de emissão são 27/10/2025.
        Não há documentos de 2024..."  ❌ WRONG
```

### After Fix
```
User: "Qual o tipo de nota mais predominante em 2024?"
Agent: "📊 Estatísticas do Banco de Dados em 2024

        Totais:
        - 📄 Documentos processados: 21
        - 🛒 Itens cadastrados: 89
        - 💰 Valor total: R$ 61,551.68
        
        Por Tipo de Documento:
        - NFe: 21 documento(s)"  ✅ CORRECT
```

## Files Modified

1. **src/agent/tools.py**
   - Modified `GetStatisticsInput` class
   - Modified `SearchInvoicesInput` class
   - Modified `DatabaseStatsTool._run()` method
   - Modified `DatabaseStatsTool._arun()` method
   - Modified `DatabaseSearchTool._run()` method
   - Modified `DatabaseSearchTool._arun()` method
   - Updated tool descriptions

2. **src/database/db.py**
   - Modified `DatabaseManager.get_statistics()` method

3. **src/agent/prompts.py**
   - Updated system prompt with year extraction rules
   - Updated examples to show year/month usage
   - Updated tool descriptions

## Backward Compatibility

All changes are backward compatible:
- `year` and `month` parameters are optional
- Existing code using `days_back` continues to work
- When both `year` and `days_back` are provided, `year` takes priority

## Testing Files Created

- `test_year_filtering.py` - Comprehensive database filtering tests
- `test_user_scenario.py` - Simulates the exact user question

Run tests with:
```bash
python test_year_filtering.py
python test_user_scenario.py
```
