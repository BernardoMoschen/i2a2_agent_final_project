# 🎯 Validation Analysis Tool - Feature Documentation

## Overview

Uma nova ferramenta foi adicionada ao agente fiscal para **analisar e reportar os problemas de validação mais comuns** nos documentos fiscais. Isso permite que usuários façam perguntas como:

- "qual o problema de validação mais comum em 2024?"
- "quais são os erros mais frequentes?"
- "qual tipo de erro mais ocorre?"

## Architecture

### 1. Database Method: `get_validation_issue_analysis()`

**Localização:** `src/database/db.py` (classe `DatabaseManager`)

**Assinatura:**
```python
def get_validation_issue_analysis(
    self,
    year: Optional[int] = None,
    month: Optional[int] = None,
    limit: int = 10,
) -> dict:
```

**Funcionalidade:**
- Consulta a tabela `validation_issues` agrupando por código de erro
- Conta ocorrências de cada tipo de erro
- Agrupa por severidade (error, warning, info)
- Filtra opcionalmente por ano/mês
- Retorna ranking dos top N problemas com:
  - Código do problema
  - Frequência de ocorrência
  - Distribuição de severidade
  - Campo afetado
  - Mensagem de exemplo

**Retorno:**
```python
{
    "period": "2024",
    "total_issues": 4,
    "common_issues": [
        {
            "code": "VAL002",
            "count": 2,
            "severity": "error",
            "severity_breakdown": {"error": 2},
            "sample_message": "Issuer CNPJ must be 14 digits...",
            "field": "issuer_cnpj",
        },
        # ... mais problemas
    ],
    "by_severity": {
        "error": 2,
        "warning": 2,
    }
}
```

### 2. Agent Tool: `ValidationAnalysisTool`

**Localização:** `src/agent/tools.py`

**Características:**
- Classe `ValidationAnalysisTool` que estende `BaseTool` do LangChain
- Input schema: `AnalyzeValidationIssuesInput` com campos opcionais `year` e `month`
- Description automáticamente detecta quando o usuário faz perguntas sobre validação
- Output formatado amigavelmente com emojis e estrutura clara

**Exemplos de Trigger:**
```
"qual o problema de validação mais comum em 2024?"  → year=2024
"quais são os problemas de validação mais frequentes?"  → sem filtro (all time)
"qual erro mais ocorre nos documentos?"  → sem filtro
"problemas de validação de janeiro/2024"  → year=2024, month=1
```

### 3. Prompt Guidelines

**Localização:** `src/agent/prompts.py`

Adicionadas instruções ao agente para:
1. Reconhecer quando usar `analyze_validation_issues`
2. Exemplos de perguntas que devem triggar a ferramenta
3. Como interpretar resultados e apresentar ao usuário

## Usage Examples

### Via Agente (Chat)
```
Usuário: "qual o problema de validação mais comum em 2024?"

Agente:
1. Reconhece a pergunta como sobre "problemas de validação"
2. Chama: analyze_validation_issues(year=2024)
3. Recebe análise detalhada
4. Formata resposta amigável com:
   - TOP 3 problemas mais comuns
   - Frequência de cada um
   - Campo afetado
   - Sugestões para resolve-los
```

### Via Python Direto
```python
from src.agent.tools import validation_analysis_tool

# Análise de 2024
result = validation_analysis_tool._run(year=2024)
print(result)

# Análise de janeiro/2024
result = validation_analysis_tool._run(year=2024, month=1)
print(result)

# Análise de todo o histórico
result = validation_analysis_tool._run()
print(result)
```

### Via Database Manager
```python
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal_documents.db")

# Análise de 2024
analysis = db.get_validation_issue_analysis(year=2024, limit=10)

# Análise de janeiro
analysis = db.get_validation_issue_analysis(year=2024, month=1, limit=5)
```

## Output Examples

### Scenario 1: 2024 Analysis
```
📊 **Análise de Problemas de Validação**

**Período:** 2024
**Total de Problemas:** 4

**Distribuição por Severidade:**
- 🔴 ERROR: 2 problema(s)
- 🟡 WARNING: 2 problema(s)

**Top Problemas Mais Frequentes:**

1. **[VAL002]** - 2 ocorrências
   Severidade: error (error: 2)
   Campo afetado: issuer_cnpj
   Exemplo: Issuer CNPJ must be 14 digits...

2. **[VAL004]** - 2 ocorrências
   Severidade: warning (warning: 2)
   Campo afetado: total_invoice
   Exemplo: Total invoice value does not match expected calculation...
```

### Scenario 2: No Issues Found
```
❌ **Nenhum problema de validação encontrado**

Período analisado: 2024

Isso significa que todos os documentos foram validados com sucesso! 🎉
```

## Integration Points

### 1. Agente Chat
- A ferramenta é automaticamente registrada em `ALL_TOOLS`
- O agente pode chamá-la quando usuário faz perguntas sobre validação
- Respostas são formatadas automaticamente

### 2. UI (Streamlit)
- Atualmente acessível via chat com o agente na aba "Home"
- Potencial: Adicionar um widget dedicado na aba "Reports" para análise de validação

### 3. Business Reports
- Dados podem ser exportados para CSV/Excel
- Podem ser integrados em dashboards

## Testing

### Unit Tests
```bash
pytest tests/test_validation_analysis.py -v
```

### Manual Testing
```bash
# Via script de teste
python3 test_validation_analysis_tool.py

# Via CLI Python
python3 -c "from src.agent.tools import validation_analysis_tool; print(validation_analysis_tool._run(year=2024))"
```

## Performance Considerations

- ✅ Usa índices existentes na tabela `validation_issues`
- ✅ Eficiente para datasets até 100k+ registros
- ✅ Filtragem por data reduz significativamente a carga
- ⚠️  Sem limite (limit=None) pode retornar muitos resultados

## Future Enhancements

1. **Análise temporal:** Gráfico de evolução de erros ao longo do tempo
2. **Análise por emitente:** Quais emitentes têm mais erros
3. **Análise por CFOP:** Quais operações fiscais têm mais problemas
4. **Sugestões automáticas:** Baseada no tipo de erro, sugerir como corrigir
5. **Alertas:** Notificar quando um tipo de erro ultrapassar um threshold

## Commits

- **d54343b** - feat: add validation issue analysis tool for agent
- **463aba5** - docs: update agent prompts to include new validation analysis tool

## Related Files

- `src/database/db.py` - DatabaseManager class with analysis method
- `src/agent/tools.py` - ValidationAnalysisTool implementation
- `src/agent/prompts.py` - Agent instructions for using the tool
- `test_validation_analysis_tool.py` - Test script

---

**Status:** ✅ Implemented and Tested
**Last Updated:** 2025-10-29
