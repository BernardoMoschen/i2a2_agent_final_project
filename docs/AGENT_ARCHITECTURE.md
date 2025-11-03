# 🎯 Agent Architecture & Communication Guide

This document explains how the Fiscal Document Agent works internally and how it communicates with tools.

## 📊 Quick Architecture Overview

The agent uses the **ReAct (Reasoning + Acting)** pattern from LangChain:

```
User Question → Agent Reasoning → Tool Selection → Tool Execution → Result Processing → Response
```

## 🔑 Core Components

### 1. **Agent Core** (`src/agent/agent_core.py`)
- Main orchestrator
- Manages conversation memory (history)
- Connects LLM with tools

### 2. **System Prompt** (`src/agent/prompts.py`)
- Instructions for the LLM
- Mappings from layperson terms → technical terms
- Critical rules for tool usage
- Examples of correct interpretation

### 3. **Tools** (`src/agent/tools.py`)
- `DatabaseSearchTool` ⭐ PRIMARY
- `DatabaseStatsTool`
- `ParseXMLTool`
- `ValidateInvoiceTool`
- `FiscalKnowledgeTool`
- And 11 more...

### 4. **Database Manager** (`src/database/db.py`)
- SQLite database wrapper
- Query optimization
- Result formatting

## 📊 Simplified Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                      │
│                 "How many purchase notes do we have?"            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT CORE                                    │
│  1. Receives user question                                      │
│  2. Adds to memory (conversation history)                       │
│  3. Sends to LLM (Gemini) with:                                 │
│     • System Prompt (instructions)                              │
│     • Conversation history                                      │
│     • Available tools list                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM (Google Gemini)                            │
│  Reasoning (ReAct Pattern):                                      │
│                                                                  │
│  Thought: "User wants to COUNT PURCHASE notes.                  │
│            I need search_invoices_database"                     │
│                                                                  │
│  Interprets terms:                                               │
│    • "how many" → count, use days_back=9999                    │
│    • "purchase" → operation_type='purchase'                    │
│                                                                  │
│  Action: search_invoices_database                               │
│  Action Input: {                                                │
│    "operation_type": "purchase",                               │
│    "days_back": 9999                                            │
│  }                                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               LANGCHAIN EXECUTOR                                 │
│  1. Validates tool exists                                       │
│  2. Validates parameters (Pydantic schema)                      │
│  3. Executes DatabaseSearchTool._run()                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              TOOL: DatabaseSearchTool                            │
│                                                                  │
│  def _run(operation_type='purchase', days_back=9999):          │
│    # Query database                                             │
│    db = DatabaseManager()                                       │
│    invoices = db.search_invoices(                               │
│        operation_type='purchase',                               │
│        days_back=9999                                            │
│    )                                                             │
│                                                                  │
│    # Format result                                              │
│    return """                                                   │
│    📊 Found 2 document(s):                                      │
│    - 📥 Purchases: 2                                            │
│    [details...]                                                 │
│    """                                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                DATABASE (SQLite)                                 │
│                                                                  │
│  SELECT * FROM invoices                                         │
│  WHERE operation_type = 'purchase'                              │
│    AND issue_date >= (TODAY - 9999 days)                        │
│                                                                  │
│  Returns: 2 documents                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESULT RETURNED TO LLM                              │
│                                                                  │
│  Observation: "Found 2 purchase documents..."                   │
│                                                                  │
│  LLM processes:                                                  │
│    Thought: "I now have complete information"                   │
│    Final Answer: [Formatted response for user]                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                RESPONSE TO USER                                  │
│                                                                  │
│  📊 We have 2 purchase notes in the system!                     │
│                                                                  │
│  💰 Total Value: R$ 1,522.50                                    │
│                                                                  │
│  📥 Documents found:                                             │
│  1. NFe 3510129/1 - Company X - R$ 522.50 (18/01/2024)         │
│  2. NFe 1/1 - Supplier Y - R$ 1,000.00 (15/01/2024)            │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Step-by-Step Communication Example

### Question: "How many purchase notes in 2024?"

**Step 1: User asks**
```
User: "How many purchase notes in 2024?"
```

**Step 2: Agent Core receives**
```python
def chat(self, message: str) -> str:
    response = self.executor.invoke({"input": message})
    return response.get("output")
```

**Step 3: LLM (Gemini) reasons**
```
Thought: User wants to know how many PURCHASE notes exist in 2024.
         I need search_invoices_database with:
         - operation_type='purchase'
         - Period filtered to 2024
```

**Step 4: LLM chooses tool and parameters**
```
Action: search_invoices_database
Action Input: {
    "operation_type": "purchase",
    "year": 2024
}
```

**Step 5: LangChain executes the tool**
```python
# src/agent/tools.py - DatabaseSearchTool
def _run(self, operation_type='purchase', year=2024):
    db = DatabaseManager()
    invoices = db.search_invoices(
        operation_type=operation_type,
        year=year,
    )

    return """
    📊 Found 2 document(s):

    By Operation Type:
    - 📥 Purchases: 2

    📥 NFe - 3510129/1 | Purchase
       🏢 Issuer: COMPANY X...
       📅 Date: 18/01/2024
       💰 Value: R$ 522.50
    ...
    """
```

**Step 6: LLM processes the result**
```
Observation: Found 2 purchase documents from 2024, total R$ 1,522.50
```

**Step 7: LLM formulates final response**
```
Thought: I have all the information needed.
Final Answer: 📊 We have 2 purchase notes in 2024!

💰 Total Value: R$ 1,522.50

📥 Documents:
1. NFe 3510129/1 - COMPANY X - R$ 522.50 (18/01/2024)
2. NFe 1/1 - SUPPLIER Y - R$ 1,000.00 (15/01/2024)
```

**Step 8: Response to user**
```
Streamlit displays the formatted markdown response
```

## 🛠️ Anatomy of a Tool

### Base Structure

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# 1. Define input schema
class SearchInvoicesInput(BaseModel):
    """Schema for search inputs."""
    
    operation_type: Optional[str] = Field(
        None,
        description="purchase, sale, transfer, or return"
    )
    days_back: int = Field(
        9999,
        description="Default 9999 (search all documents)"
    )

# 2. Create the tool
class DatabaseSearchTool(BaseTool):
    """Tool for searching invoices in database."""
    
    name: str = "search_invoices_database"
    description: str = """
    Search fiscal documents with filters.
    
    CRITICAL RULES:
    - For "how many" → ALWAYS use days_back=9999
    - For "purchase" → operation_type='purchase'
    - For specific year → use year parameter
    
    EXAMPLES:
    - "How many purchase notes?" → operation_type='purchase', days_back=9999
    - "Notes from 2024?" → year=2024
    - "Sales in 2024?" → operation_type='sale', year=2024
    """
    args_schema: type[BaseModel] = SearchInvoicesInput

    def _run(self, operation_type=None, days_back=9999) -> str:
        """Execute search."""
        db = DatabaseManager()
        results = db.search_invoices(
            operation_type=operation_type,
            days_back=days_back
        )
        return format_results(results)

    async def _arun(self, ...) -> str:
        """Async version."""
        return self._run(...)
```

### Critical Elements

1. **`name`**: Unique identifier the LLM uses to call the tool
2. **`description`**: Clear instructions for WHEN and HOW to use it
3. **`args_schema`**: Pydantic schema that validates parameters
4. **`_run()`**: Execution logic (required)
5. **`_arun()`**: Async version (optional, recommended)

## 📚 Best Practices for Tools

### ✅ DO: Clear Instructions in Description

```python
description: str = """
Search for fiscal documents.

CRITICAL RULES (YOU MUST FOLLOW):
1. For "how many", "total", "count" → ALWAYS use days_back=9999
2. For "purchase", "buy" → operation_type='purchase'
3. For "sale", "sell" → operation_type='sale'
4. For specific year (2024) → use year=2024, not days_back

CORRECT USAGE EXAMPLES:
- "How many purchases?" → operation_type='purchase', days_back=9999
- "Purchases in 2024?" → operation_type='purchase', year=2024
- "Monthly sales?" → operation_type='sale', days_back=30
"""
```

**Why?** The LLM reads `description` to decide whether to use the tool and what parameters to pass.

### ✅ DO: Input Validation with Pydantic

```python
from pydantic import BaseModel, Field
from typing import Literal

class SearchInput(BaseModel):
    operation_type: Optional[Literal["purchase", "sale", "transfer", "return"]] = None
    days_back: int = Field(9999, ge=1, le=9999)  # Clear limits
    year: Optional[int] = Field(None, ge=2015, le=2100)
```

### ✅ DO: Structured & Formatted Output

```python
def _run(self, ...) -> str:
    results = db.search(...)
    
    # Consistent format that LLM can easily understand
    return f"""
    📊 Found {len(results)} document(s):

    By Operation Type:
    {breakdown}

    {detailed_list}

    Summary:
    - 📄 Total documents: {total}
    - 💰 Total value: R$ {value}
    """
```

### ✅ DO: Explicit Error Handling

```python
def _run(self, ...) -> str:
    try:
        results = db.search(...)
        return format_results(results)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"❌ Error searching database: {str(e)}"
```

### ❌ DON'T: Vague Descriptions

```python
# ❌ BAD
description = "Search database"

# ✅ GOOD
description = """
Search fiscal documents by operation type, period, issuer.
Use operation_type='purchase' for purchases.
ALWAYS use days_back=9999 for counting ALL documents.
"""
```

### ❌ DON'T: Unstructured Responses

```python
# ❌ BAD
return str(results)  # LLM struggles to parse this

# ✅ GOOD
return format_with_emojis_and_sections(results)
```

## 🎯 Term Mappings (Layperson → Technical)

### Operation Types
- "buy", "purchase", "buying", "entrada" → `operation_type='purchase'`
- "sell", "sale", "selling", "saída" → `operation_type='sale'`
- "transfer", "transferência" → `operation_type='transfer'`
- "return", "devolvemos", "devolução" → `operation_type='return'`

### Periods
- "2024", "this year", "current year" → `year=2024`
- "last month", "previous month" → `days_back=30`
- "this week" → `days_back=7`
- "today", "now" → `days_back=1`
- "all", "everything", "total" → `days_back=9999`

### Document Types
- "note", "nf", "fiscal note" → `document_type='NFe'`
- "receipt", "ticket" → `document_type='NFCe'`
- "transport" → `document_type='CTe'`

### Actions
- "how many", "count", "total" → Count the results and return number
- "show", "list", "display" → Use search and show details
- "statistics", "summary" → Use get_database_statistics

## 📋 Common Questions → Tool Mapping

| User Question | Tool | Parameters |
|---|---|---|
| "How many purchase notes?" | `search_invoices_database` | `operation_type='purchase', days_back=9999` |
| "Sales in 2024?" | `search_invoices_database` | `operation_type='sale', year=2024` |
| "Total documents?" | `get_database_statistics` | (none) |
| "Documents this week?" | `search_invoices_database` | `days_back=7` |
| "Show notes from supplier X?" | `search_invoices_database` | `issuer_cnpj='X', days_back=9999` |
| "Receipts?" | `search_invoices_database` | `document_type='NFCe', days_back=9999` |

## 🚀 Key Lessons Learned

### 1. Three Layers of Protection

1. **Default Values** (9999 days = 27 years)
2. **LLM Instructions** (clear prompts and examples)
3. **Hardcoded Enforcement** ⭐ (guarantee in code)

Never trust just the LLM—hardcode critical validations in tool code!

### 2. Don't Trust Only the LLM

Even with perfect instructions, the LLM can:
- Misinterpret context
- Choose wrong parameters
- Ignore rules

**Solution**: Hardcode validations in tool implementations!

### 3. Simplicity for End Users

Users should NOT know:
- Tool names
- Technical parameters
- Data structure details

Just ask natural questions! 🗣️

## 🔗 Related Documentation

- **[AGENT_CAPABILITY_AUDIT.md](./AGENT_CAPABILITY_AUDIT.md)** - What tools exist and their capabilities
- **[USER_QUESTIONS_GUIDE.md](./USER_QUESTIONS_GUIDE.md)** - Example questions users can ask
- **[FISCAL_VALIDATIONS.md](./FISCAL_VALIDATIONS.md)** - Validation rules implemented
- **[QUICKSTART.md](./QUICKSTART.md)** - Quick setup guide

