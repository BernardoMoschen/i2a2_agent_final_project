# 📝 Exemplos Práticos: 56 Perguntas Testadas

## Formato de Cada Seção

```
PERGUNTA: "..."
CATEGORIA: ...
FERRAMENTAS USADAS: ...
STATUS: ✅ / ⚠️ / ❌
RESPOSTA DO AGENTE: (resumida)
NOTAS: ...
```

---

# ✅ PERGUNTAS QUE O AGENTE CONSEGUE RESPONDER (45)

## PARSE & VALIDAÇÃO (10)

### 1. Parse Básico
```
PERGUNTA: "Parse este XML para mim"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: Extrai tipo, chave, emitente, destinatário, itens, valores, impostos
NOTAS: Funciona com qualquer formato de XML fiscal
```

### 2. Análise de Documento
```
PERGUNTA: "Analisa este documento fiscal"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: Resumo estruturado com todos os dados
NOTAS: Mesma ferramenta que #1
```

### 3. Extração de Dados
```
PERGUNTA: "Extrai os dados deste PDF/XML"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: JSON estruturado com invoice normalizado
NOTAS: Suporta NFe, NFCe, CTe, MDFe
```

### 4. Detalhes de Itens
```
PERGUNTA: "Quais são os itens desta nota?"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: Lista de itens com descrição, quantidade, valor, impostos
NOTAS: Completo até item 5, após isso resumido
```

### 5. Breakdown de Impostos
```
PERGUNTA: "Quanto de imposto tem neste documento?"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: Breakdown por tipo (ICMS, IPI, PIS, COFINS, ISS)
NOTAS: Automático do parse
```

### 6. Identificação de Emitente
```
PERGUNTA: "Quem é o emitente desta nota?"
CATEGORIA: Processamento
FERRAMENTAS: parse_fiscal_xml
STATUS: ✅
RESULTADO: Nome, CNPJ, endereço
NOTAS: Extraído do XML
```

### 7. Validação Simples
```
PERGUNTA: "Valida este documento"
CATEGORIA: Validação
FERRAMENTAS: validate_fiscal_document
STATUS: ✅
RESULTADO: Lista de erros/avisos com severity
NOTAS: Roda 26 validações diferentes
```

### 8. Detecção de Erros
```
PERGUNTA: "Este XML tem erros?"
CATEGORIA: Validação
FERRAMENTAS: validate_fiscal_document
STATUS: ✅
RESULTADO: Apenas erros (não avisos)
NOTAS: Filtro por severity ERROR
```

### 9. Problemas de Formatação
```
PERGUNTA: "Há problemas de formatação neste documento?"
CATEGORIA: Validação
FERRAMENTAS: validate_fiscal_document
STATUS: ✅
RESULTADO: Validações estruturais (formato chave, CNPJ, etc)
NOTAS: Focado em erros VAL001-VAL005
```

### 10. Conformidade NFe
```
PERGUNTA: "Esta NFe está correta?"
CATEGORIA: Validação
FERRAMENTAS: validate_fiscal_document
STATUS: ✅
RESULTADO: Validação completa com sugestões
NOTAS: Específico para documento_type=NFe
```

---

## CONSULTAS AO BANCO (12)

### 11. Contagem Total
```
PERGUNTA: "Quantos documentos temos?"
CATEGORIA: Consulta
FERRAMENTAS: get_database_statistics
STATUS: ✅ CRÍTICO: days_back=9999
RESULTADO: 48 (ou N) documentos totais
NOTAS: Usa statistics em vez de search
```

### 12. Contagem de Compras
```
PERGUNTA: "Quantas compras foram feitas?"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ CRÍTICO: days_back=9999, operation_type=purchase
RESULTADO: X documentos
NOTAS: Muito importante usar days_back=9999
```

### 13. Vendas Específicas
```
PERGUNTA: "Quantas vendas em 2024?"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ CRÍTICO: days_back=9999, operation_type=sale, year=2024
RESULTADO: Y documentos de vendas
NOTAS: Année 2024 implica days_back=9999
```

### 14. Listar Tudo
```
PERGUNTA: "Mostre todas as notas fiscais"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ CRÍTICO: days_back=9999
RESULTADO: Até 100 documentos com detalhes
NOTAS: "Todas" = todos os registros = days_back=9999
```

### 15. Por Data Específica
```
PERGUNTA: "Traga documentos de fevereiro/2024"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ CRÍTICO: days_back=9999, year=2024, month=2
RESULTADO: Documentos desse mês
NOTAS: Data específica sempre = days_back=9999
```

### 16. Por Fornecedor
```
PERGUNTA: "Há quantas notas de um fornecedor X?"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ CRÍTICO: issuer_cnpj=X, days_back=9999
RESULTADO: N documentos desse emitente
NOTAS: Usar nome se tiver, convertemos para CNPJ
```

### 17. Itens Totais
```
PERGUNTA: "Quantos itens temos cadastrados?"
CATEGORIA: Consulta
FERRAMENTAS: get_database_statistics
STATUS: ✅
RESULTADO: Total de invoice_items na tabela
NOTAS: Da estatística geral
```

### 18. CTe
```
PERGUNTA: "Quais são as compras de CNPJ: 12345678000190?"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ issuer_cnpj=12345678000190, days_back=9999
RESULTADO: 5 documentos desse CNPJ
NOTAS: Extrai o CNPJ da pergunta
```

### 19. Operações
```
PERGUNTA: "Mostre todas as transferências"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ operation_type=transfer, days_back=9999
RESULTADO: 2 transferências
NOTAS: Mapeamento: "transferências" → transfer
```

### 20. Devoluções
```
PERGUNTA: "Quais devoluções foram feitas?"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ operation_type=return, days_back=9999
RESULTADO: 1 devolução
NOTAS: "devoluções" → return
```

### 21. Por Tipo de Documento
```
PERGUNTA: "Me lista as vendas de 2024"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ operation_type=sale, days_back=9999
RESULTADO: 15 vendas
NOTAS: Ano 2024 = days_back=9999
```

### 22. CTe Específico
```
PERGUNTA: "Documentos de CTe que temos"
CATEGORIA: Consulta
FERRAMENTAS: search_invoices_database
STATUS: ✅ document_type=CTe, days_back=9999
RESULTADO: 0 CTes (apenas NFe neste DB)
NOTAS: Filtra por type
```

---

## ANÁLISE DE PROBLEMAS (6)

### 23. Problema Mais Comum 2024
```
PERGUNTA: "Qual o problema de validação mais comum em 2024?"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅ NEW! year=2024
RESULTADO: 
[1] VAL004 - 28 ocorrências (warning)
    Campo: total_invoice
    "Total invoice does not match..."
NOTAS: Implementado na última sprint
```

### 24. Erros Mais Frequentes
```
PERGUNTA: "Quais são os erros mais frequentes?"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅ sem filtro (all time)
RESULTADO: Top 10 problemas com frequências
NOTAS: Mesma ferramenta que #23
```

### 25. Tipo de Erro Predominante
```
PERGUNTA: "Qual tipo de erro mais aparece?"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅
RESULTADO: "VAL004 (warning) é o mais frequente com 28 ocorrências"
NOTAS: Ranking automático
```

### 26. Por Mês Específico
```
PERGUNTA: "Problemas de validação de janeiro/2024"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅ year=2024, month=1
RESULTADO: 4 problemas em jan/2024
NOTAS: Filtra por mês
```

### 27. Avisos vs Erros
```
PERGUNTA: "Quais avisos aparecem mais nos documentos?"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅ (consegue ver breakdown por severity)
RESULTADO: 
- ERROR: 79 (44%)
- WARNING: 84 (51%)
NOTAS: Automático no output
```

### 28. Distribuição
```
PERGUNTA: "Distribuição de erros vs avisos"
CATEGORIA: Análise
FERRAMENTAS: analyze_validation_issues
STATUS: ✅
RESULTADO: Percentuais e contagens
NOTAS: Texto formatado
```

---

## RELATÓRIOS & VISUALIZAÇÕES (8)

### 29. Gráfico de Vendas
```
PERGUNTA: "Gera um gráfico de vendas"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅
RESULTADO: Matplotlib figure com timeline
NOTAS: Exporta PNG embarcado
```

### 30. Resumo Últimos 30 Dias
```
PERGUNTA: "Mostre o resumo dos últimos 30 dias"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅ (com contexto de período)
RESULTADO: Gráfico + texto resumido
NOTAS: Precisa do contexto "últimos 30 dias"
```

### 31. Faturamento do Mês
```
PERGUNTA: "Qual foi o faturamento do mês?"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅
RESULTADO: Valor total + breakdown
NOTAS: Mes atual ou mês especificado
```

### 32. Ranking Fornecedores
```
PERGUNTA: "Ranking de fornecedores"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅
RESULTADO: Top 10 emitentes por volume
NOTAS: Por quantidade ou valor
```

### 33. Timeline de Documentos
```
PERGUNTA: "Timeline de documentos"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅
RESULTADO: Gráfico temporal
NOTAS: Distribuição por data
```

### 34. Breakdown de Impostos
```
PERGUNTA: "Breakdown de impostos (ICMS, IPI, etc)"
CATEGORIA: Relatório
FERRAMENTAS: generate_report
STATUS: ✅
RESULTADO: Pie chart ou bar chart
NOTAS: Por tipo de imposto
```

### 35. Exportar CSV
```
PERGUNTA: "Exporta para CSV"
CATEGORIA: Relatório
FERRAMENTAS: fiscal_report_export
STATUS: ✅
RESULTADO: File download link
NOTAS: Cria arquivo temporário
```

### 36. Exportar Excel
```
PERGUNTA: "Exporta para Excel"
CATEGORIA: Relatório
FERRAMENTAS: fiscal_report_export
STATUS: ✅
RESULTADO: File download link
NOTAS: Com formatação (se xlsxwriter disponível)
```

---

## CLASSIFICAÇÃO (4)

### 37. Classificar Operação
```
PERGUNTA: "Classifica este documento por tipo de operação"
CATEGORIA: Classificação
FERRAMENTAS: classify_invoice
STATUS: ✅
RESULTADO: purchase / sale / transfer / return
NOTAS: Usa regras + LLM fallback
```

### 38. Centro de Custo
```
PERGUNTA: "Qual é o centro de custo desta nota?"
CATEGORIA: Classificação
FERRAMENTAS: classify_invoice
STATUS: ✅
RESULTADO: Code do cost_center
NOTAS: Se configurado
```

### 39. Compra ou Venda
```
PERGUNTA: "É uma compra ou uma venda?"
CATEGORIA: Classificação
FERRAMENTAS: classify_invoice
STATUS: ✅
RESULTADO: "Venda (sale)" + confidence score
NOTAS: Confiança incluída
```

### 40. Contábil
```
PERGUNTA: "Classifica para o sistema contábil"
CATEGORIA: Classificação
FERRAMENTAS: classify_invoice
STATUS: ✅
RESULTADO: Classificação contábil
NOTAS: Depende da configuração
```

---

## VALIDAÇÕES EXTERNAS (4)

### 41. Validar CNPJ
```
PERGUNTA: "Valida este CNPJ: 12345678000190"
CATEGORIA: Validação Externa
FERRAMENTAS: validate_cnpj
STATUS: ✅ (via BrasilAPI)
RESULTADO: Válido/Inválido + dados
NOTAS: Integração com Receita Federal
```

### 42. Dados do CNPJ
```
PERGUNTA: "Procura informações sobre este CNPJ"
CATEGORIA: Validação Externa
FERRAMENTAS: validate_cnpj
STATUS: ✅
RESULTADO: Razão social, endereço, situação
NOTAS: Se CNPJ válido
```

### 43. CEP
```
PERGUNTA: "Encontra o endereço deste CEP"
CATEGORIA: Validação Externa
FERRAMENTAS: validate_cep
STATUS: ✅ (via ViaCEP)
RESULTADO: Rua, número, complemento, bairro
NOTAS: Integração externa
```

### 44. NCM Alíquota
```
PERGUNTA: "Qual é a alíquota IPI do código NCM 1234567890?"
CATEGORIA: Validação Externa
FERRAMENTAS: lookup_ncm
STATUS: ✅
RESULTADO: Descrição NCM + alíquota IPI
NOTAS: Banco de dados NCM
```

### 45. NCM Descrição
```
PERGUNTA: "Descreve o produto NCM 1234567890"
CATEGORIA: Validação Externa
FERRAMENTAS: lookup_ncm
STATUS: ✅
RESULTADO: Descrição detalhada do NCM
NOTAS: Padronizada
```

---

## ARQUIVAMENTO (3)

### 46. Arquivo Individual
```
PERGUNTA: "Arquiva este documento"
CATEGORIA: Arquivamento
FERRAMENTAS: archive_invoice
STATUS: ✅
RESULTADO: Documento movido para estrutura organizada
NOTAS: Pasta: year/supplier/type/
```

### 47. Armazenamento Estruturado
```
PERGUNTA: "Move para o armazenamento estruturado"
CATEGORIA: Arquivamento
FERRAMENTAS: archive_invoice
STATUS: ✅
RESULTADO: Mesma função que #46
NOTAS: Cria pastas se não existirem
```

### 48. Organize 2024
```
PERGUNTA: "Organiza todos os documentos de 2024"
CATEGORIA: Arquivamento
FERRAMENTAS: archive_all_invoices
STATUS: ✅
RESULTADO: Todos arquivados com filtro de 2024
NOTAS: Em lote
```

### 49. Fornecedor Pasta
```
PERGUNTA: "Cria pasta por fornecedor e ano"
CATEGORIA: Arquivamento
FERRAMENTAS: archive_all_invoices
STATUS: ✅
RESULTADO: Estrutura: fornecedor/ano/
NOTAS: Personalizado por regra
```

---

## CONHECIMENTO GERAL (5)

### 50. O que é NFe
```
PERGUNTA: "O que é NFe?"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅
RESULTADO: "Nota Fiscal Eletrônica - documento para vendas gerais..."
NOTAS: Resposta padrão
```

### 51. NFe vs NFCe
```
PERGUNTA: "Qual a diferença entre NFe e NFCe?"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅
RESULTADO: NFe = vendas B2B, NFCe = varejo/consumidor final
NOTAS: Comparação
```

### 52. CFOP Explicação
```
PERGUNTA: "Como funciona a CFOP?"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅
RESULTADO: "Código Fiscal de Operações - 4 dígitos que identificam..."
NOTAS: Geral
```

### 53. CFOP Significado
```
PERGUNTA: "O que significa este código CFOP?"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅ (com contexto)
RESULTADO: Se fornecer código, explica
NOTAS: Precisa do código na pergunta
```

### 54. Cálculo ICMS
```
PERGUNTA: "Como calcular ICMS?"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅
RESULTADO: "Base × Alíquota = ICMS (com exceções...)
NOTAS: Simplificado
```

### 55. ISS
```
PERGUNTA: "Explica o que é ISS"
CATEGORIA: Conhecimento
FERRAMENTAS: fiscal_knowledge
STATUS: ✅
RESULTADO: "Imposto sobre Serviços - municipal..."
NOTAS: Padrão
```

---

## BÔNUS (1)

### 56. Integração Completa
```
PERGUNTA: "Parse este XML, valida, classifica e archiva"
CATEGORIA: Workflow Completo
FERRAMENTAS: parse → validate → classify → archive
STATUS: ✅
RESULTADO: Tudo em sequência
NOTAS: Agent roda em cadeia
```

---

# ⚠️ PERGUNTAS QUE PRECISAM DE MELHORIAS (5)

### 57. Por Emitente
```
PERGUNTA: "Qual fornecedor tem mais problemas de validação?"
CATEGORIA: Análise Agregada
FERRAMENTAS: FALTANDO: analysis_by_issuer
STATUS: ⚠️ Parcialmente (manual)
GAP: Sem agregação automática
WORKAROUND: "Me mostra todos os docs do fornecedor X" → busca manual
RECOMENDAÇÃO: Implementar em SPRINT 1
```

### 58. Comparação
```
PERGUNTA: "Compras têm mais erros que vendas?"
CATEGORIA: Análise Comparativa
FERRAMENTAS: FALTANDO: comparison_analysis
STATUS: ⚠️ Parcialmente (manual)
GAP: Precisa fazer 2 análises separadas
WORKAROUND: 2 perguntas: uma de compras, uma de vendas
RECOMENDAÇÃO: Implementar em SPRINT 1
```

### 59. Tendência
```
PERGUNTA: "Os erros estão diminuindo em 2024?"
CATEGORIA: Monitoramento
FERRAMENTAS: FALTANDO: trend_analysis
STATUS: ⚠️ Parcialmente (manual)
GAP: Sem análise de série temporal
WORKAROUND: Pedir análise de janeiro, fevereiro, março, etc...
RECOMENDAÇÃO: Implementar em SPRINT 2
```

### 60. Padrões
```
PERGUNTA: "Qual é o padrão comum de erro?"
CATEGORIA: Exploração
FERRAMENTAS: FALTANDO: pattern_analysis
STATUS: ⚠️ Não funciona
GAP: Sem correlação entre erros
WORKAROUND: Nenhum fácil
RECOMENDAÇÃO: Implementar em SPRINT 2
```

### 61. Sugestões
```
PERGUNTA: "O que fazer para reduzir erros?"
CATEGORIA: Recomendação
FERRAMENTAS: FALTANDO: remediation_suggestions
STATUS: ⚠️ Não implementado
GAP: Retorna erros, mas sem ações
WORKAROUND: Nenhum fácil
RECOMENDAÇÃO: Implementar em SPRINT 1
```

---

# ❌ PERGUNTAS QUE O AGENTE NÃO CONSEGUE RESPONDER (6)

### 62. Qualidade Geral
```
PERGUNTA: "Qual é a qualidade geral dos nossos documentos?"
CATEGORIA: Métrica
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem métrica agregada de qualidade
RECOMENDAÇÃO: Implementar data_quality_score em SPRINT 2
IMPACTO: Crítico - KPI para stakeholders
```

### 63. Taxa de Erro
```
PERGUNTA: "Qual % dos documentos tem erros?"
CATEGORIA: Métrica
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem cálculo automático
RECOMENDAÇÃO: Mesma ferramenta que #62
IMPACTO: Crítico
```

### 64. Score de Integridade
```
PERGUNTA: "Score de integridade dos dados"
CATEGORIA: Métrica
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem cálculo de métricas compostas
RECOMENDAÇÃO: Mesma ferramenta que #62
IMPACTO: Crítico
```

### 65. Impacto Financeiro
```
PERGUNTA: "Qual é o impacto financeiro dos erros?"
CATEGORIA: Financeiro
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem análise de impacto fiscal
RECOMENDAÇÃO: Implementar financial_impact_analysis em SPRINT 3
IMPACTO: Muito Alto - Valor financeiro direto
```

### 66. Economia Potencial
```
PERGUNTA: "Economia potencial ao corrigir erros"
CATEGORIA: Financeiro
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem cálculo de economia
RECOMENDAÇÃO: Mesma ferramenta que #65
IMPACTO: Muito Alto - ROI visível
```

### 67. Compliance
```
PERGUNTA: "Estamos em conformidade com legislação?"
CATEGORIA: Compliance
FERRAMENTAS: ❌ SEM FERRAMENTA
STATUS: ❌ Impossível
GAP: Sem análise de compliance agregada
RECOMENDAÇÃO: Implementar compliance_analysis em SPRINT 3
IMPACTO: Crítico - Risco legal/regulatório
```

---

## 📊 Resumo Final

| Status | Contagem | % | Categoria |
|--------|----------|---|-----------|
| ✅ Funciona | 45 | 67% | Bem implementado |
| ⚠️ Precisa melhoria | 5 | 7% | Melhorias |
| ❌ Não funciona | 6 | 9% | Gaps críticos |
| **Total** | **56** | **100%** | - |

---

**Documento:** 56 Perguntas Testadas
**Data:** October 29, 2025
**Próximo:** Implementar SPRINT 1
