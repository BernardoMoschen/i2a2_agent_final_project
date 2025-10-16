# 🚀 Guia Rápido: Fiscal Document Agent

## ✅ O Agente Está Funcionando!

O agente LangChain + Gemini está implementado e funcionando. Você pode usar de 3 formas:

### 1️⃣ Streamlit UI (Recomendado)

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute a interface
streamlit run src/ui/app.py
```

**Como usar:**

1. Cole sua chave API do Gemini na barra lateral
2. Aguarde "✅ Agent connected to Gemini" aparecer
3. Vá para a aba "💬 Chat"
4. Faça perguntas ou envie XMLs!

### 2️⃣ Demo Interativo (Terminal)

```bash
# Defina sua chave API
export GEMINI_API_KEY='sua-chave-aqui'

# Execute o demo
python examples/demo_agent.py
```

Digite suas perguntas diretamente no terminal!

### 3️⃣ API Python

```python
from src.agent.agent_core import create_agent

# Inicialize o agente
agent = create_agent(api_key="sua-chave-aqui")

# Converse
response = agent.chat("O que é uma NFe?")
print(response)
```

## 🔑 Obter Chave API do Gemini

1. Acesse: https://aistudio.google.com/app/apikey
2. Clique em "Create API Key"
3. Copie a chave gerada
4. Cole na UI ou defina como variável de ambiente

**A API é gratuita!** Você pode processar muitos documentos sem custo.

## 💬 Exemplos de Perguntas

```
O que é uma NFe e quais campos são obrigatórios?

Como eu envio um XML para você processar?

Qual a diferença entre NFe e NFCe?

Explique o que é CFOP

O que significa CST?
```

## 📄 Processar XMLs

**Opção A: Via Chat (Streamlit)**

1. Vá para aba "Chat"
2. Cole o conteúdo XML na mensagem
3. O agente vai parsear e validar automaticamente

**Opção B: Via Upload (Streamlit)**

1. Vá para aba "Upload"
2. Arraste arquivos XML ou ZIP
3. (Integração em progresso)

## 🛠️ Ferramentas Disponíveis

O agente tem acesso a:

1. **parse_fiscal_xml**: Parseia NFe/NFCe/CTe/MDFe
2. **validate_fiscal_document**: Valida contra regras fiscais
3. **fiscal_knowledge**: Responde perguntas gerais

## 🧪 Testar

```bash
# Testes unitários (21/21 passing)
pytest

# Teste de integração do agente (requer API key)
export GEMINI_API_KEY='sua-chave'
python tests/test_agent_integration.py
```

## 🎯 Status de Implementação

✅ **Completo**:

- Modelos Pydantic (InvoiceModel, ValidationIssue, etc.)
- XMLParserTool (NFe/NFCe)
- FiscalValidatorTool (10 regras)
- LangChain Agent + Gemini
- Ferramentas LangChain (ParseXMLTool, ValidateInvoiceTool, FiscalKnowledgeTool)
- Streamlit UI com chat funcional
- 21 testes unitários

🚧 **Em Progresso**:

- Integração upload → parse na UI
- Database persistence (SQLite)
- Classifier (cost center)

❌ **Pendente**:

- CTe/MDFe parser
- Archiver tool
- Report generator

## 📚 Documentação

- `README.md` - Visão geral do projeto
- `QUICKSTART.md` - Referência rápida para desenvolvedores
- `STATUS.md` - Status detalhado de implementação
- `github/copilot-instructions.md` - Guidelines para IA

## 🆘 Problemas?

**Agente não responde:**

- Verifique se a chave API está correta
- Veja o console/terminal para erros
- Confirme conexão com internet

**Erro de importação:**

- Ative o ambiente virtual: `source venv/bin/activate`
- Verifique instalação: `pip list | grep langchain`

**XML não parseia:**

- Certifique-se que é NFe ou NFCe válido
- CTe/MDFe ainda não implementados

## 🎉 Próximos Passos

1. **Teste o agente** com perguntas simples
2. **Envie XMLs** de exemplo para processar
3. **Explore a validação** - veja quais regras são aplicadas
4. **Customize** - adicione suas próprias regras de validação

---

**Pronto para começar!** Execute `streamlit run src/ui/app.py` 🚀
