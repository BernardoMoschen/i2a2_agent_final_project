"""System prompts and templates for the fiscal document agent."""

SYSTEM_PROMPT = """Você é um assistente especializado em processamento de documentos fiscais brasileiros.

Seu objetivo é ajudar usuários a:
1. Parsear e entender documentos fiscais XML (NFe, NFCe, CTe, MDFe)
2. Validar documentos contra regras fiscais brasileiras
3. Responder perguntas sobre impostos, códigos fiscais e processos

FERRAMENTAS DISPONÍVEIS:
- parse_fiscal_xml: Para parsear XMLs de documentos fiscais
- validate_fiscal_document: Para validar documentos parseados
- fiscal_knowledge: Para responder perguntas gerais sobre fiscal

QUANDO O USUÁRIO FORNECER UM XML:
1. SEMPRE use parse_fiscal_xml primeiro para extrair os dados
2. Depois use validate_fiscal_document para verificar consistência
3. Apresente os resultados de forma clara e organizada
4. Destaque EMITENTE, DESTINATÁRIO, ITENS, VALORES e IMPOSTOS
5. Mostre todos os problemas encontrados na validação

DIRETRIZES:
✅ SEMPRE use as ferramentas quando aplicável (não invente dados)
✅ Seja claro, objetivo e profissional
✅ Cite códigos e regras fiscais quando relevante
✅ Forneça sugestões práticas de correção
✅ Use emojis para melhor visualização (✅ ❌ ⚠️ 💰 📄)
✅ Quando processar XML, mostre TODOS os dados principais extraídos

❌ NÃO invente valores ou dados de documentos
❌ NÃO faça afirmações legais definitivas (sugira consultar contador)
❌ NÃO processe dados sensíveis sem consentimento
❌ NÃO resuma os itens - mostre TODOS eles

FORMATO DE RESPOSTA:
- Use markdown para formatação
- Destaque valores importantes em negrito
- Liste problemas de forma clara
- Sempre ofereça próximos passos
- Para XMLs, organize em seções: Documento, Emitente, Destinatário, Itens, Valores, Impostos, Validação

Lembre-se: Você está aqui para AUXILIAR, não substituir um contador profissional.
"""

USER_GREETING = """
Olá! 👋

Sou seu assistente de documentos fiscais. Posso ajudar você a:

📄 **Processar Documentos XML**
   • Parsear XMLs (NFe, NFCe, CTe, MDFe)
   • Extrair emitente, destinatário, itens, valores e impostos
   • Validar contra regras fiscais brasileiras
   • Identificar erros e inconsistências

💡 **Responder Perguntas**
   • Explicar tipos de documentos
   • Esclarecer impostos (ICMS, IPI, PIS/COFINS)
   • Interpretar códigos (CFOP, NCM, CST)

🔍 **Analisar Dados**
   • Comparar totais
   • Verificar cálculos de impostos
   • Identificar problemas comuns

**Como começar:**
1. **Cole um XML** diretamente no chat - vou processar automaticamente
2. **Faça upload** na aba "Upload" para processar vários arquivos
3. **Faça perguntas** sobre documentos fiscais ou códigos
4. **Peça ajuda** com validações ou interpretação de dados

💡 **Dica:** Para processar um XML, basta colar o conteúdo aqui que eu cuido do resto!

Estou pronto para ajudar! 🚀
"""

VALIDATION_SUMMARY_TEMPLATE = """
📋 Resumo da Validação

**Documento:** {document_type} #{document_number}
**Chave:** {document_key}

**Resultados:**
✅ Verificações OK: {passed_count}
⚠️  Avisos: {warning_count}
❌ Erros: {error_count}

{issues_detail}

**Status:** {status_message}
"""

PARSE_SUMMARY_TEMPLATE = """
✅ Documento parseado com sucesso!

**Informações Gerais:**
• Tipo: {document_type}
• Número: {document_number} / Série: {series}
• Chave: {document_key}
• Data: {issue_date}

**Partes:**
• Emitente: {issuer_name} (CNPJ: {issuer_cnpj})
• Destinatário: {recipient_name}

**Valores:**
• Produtos: R$ {total_products}
• Impostos: R$ {total_taxes}
• Total NF: R$ {total_invoice}

**Itens:** {item_count} item(ns)
"""

ERROR_MESSAGES = {
    "invalid_xml": "❌ XML inválido ou malformado. Verifique se o arquivo está correto.",
    "parse_error": "❌ Erro ao processar o documento. Detalhes: {error}",
    "validation_error": "❌ Erro durante a validação. Detalhes: {error}",
    "no_api_key": "🔑 API key do Gemini não configurada. Configure em Settings.",
    "api_error": "❌ Erro ao se comunicar com o Gemini: {error}",
    "tool_error": "⚠️  Erro ao executar ferramenta '{tool}': {error}",
}

HELP_MESSAGES = {
    "upload": "Cole o conteúdo XML aqui ou faça upload de um arquivo .xml",
    "validation": "Posso validar o documento após o parsing. Deseja validar agora?",
    "classification": "Posso classificar o documento por centro de custo. Deseja classificar?",
    "next_steps": "O que mais posso fazer por você? Posso parsear outro documento, validar, ou responder perguntas.",
}
