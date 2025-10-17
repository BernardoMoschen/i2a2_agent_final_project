# Guia de Perguntas Comuns para Usuários

## 📝 Como Fazer Perguntas ao Agente Fiscal

Este guia mostra **exemplos de perguntas em linguagem simples** que você pode fazer ao agente. Não precisa usar termos técnicos!

---

## 📊 Consultando Documentos no Banco

### 🔢 Contando Documentos

✅ **Perguntas que funcionam:**
- "Quantas notas de compra temos?"
- "Quantos documentos temos no sistema?"
- "Quantas vendas fizemos?"
- "Total de notas fiscais"
- "Quantas compras no ano de 2024?"
- "Quantos cupons fiscais temos?"
- "Total de transferências"
- "Quantas devoluções?"

**O que o agente faz:**
- Busca no banco de dados
- Conta os documentos
- Mostra valor total
- Lista os documentos encontrados

**Exemplo de resposta:**
```
📊 Temos 2 notas de compra no sistema!

💰 Valor total: R$ 1,522.50

📥 Documentos encontrados:
1. NFe 3510129/1 - Compra
   • Fornecedor: COMPANHIA BRASILEIRA...
   • Data: 18/01/2024
   • Valor: R$ 522.50

2. NFe 1/1 - Compra
   • Fornecedor: FORNECEDOR TESTE LTDA
   • Data: 15/01/2024
   • Valor: R$ 1,000.00
```

---

### 📅 Filtrando por Período

✅ **Perguntas que funcionam:**
- "Vendas desta semana"
- "Compras do mês passado"
- "Notas de hoje"
- "Documentos de 2024"
- "Vendas de 2023"
- "Compras deste ano"

**Mapeamento automático:**
- "desta semana" → últimos 14 dias
- "deste mês" / "mês passado" → últimos 60 dias
- "hoje" → último dia
- "2024" / "deste ano" → todo o histórico
- "quantas", "total" → todo o histórico (sempre!)

---

### 🏢 Filtrando por Fornecedor/Cliente

✅ **Perguntas que funcionam:**
- "Notas do fornecedor CNPJ 12.345.678/0001-90"
- "Compras da empresa X"
- "Mostrar documentos do emitente [CNPJ]"
- "Vendas para o cliente [nome]"

**Dica:** Se souber o CNPJ, use-o para resultados mais precisos.

---

### 📦 Filtrando por Tipo de Documento

✅ **Perguntas que funcionam:**
- "Mostrar todas as notas fiscais" (NFe)
- "Quantos cupons fiscais temos?" (NFCe)
- "Listar conhecimentos de transporte" (CTe)

**Tipos reconhecidos:**
- "nota fiscal", "nf", "nota" → NFe
- "cupom", "cupom fiscal" → NFCe
- "conhecimento de transporte", "cte" → CTe
- "manifesto", "mdfe" → MDFe

---

## 📄 Processando Novos Documentos

### ✅ Enviando XML para Análise

✅ **Como fazer:**
1. Cole o conteúdo XML completo no chat, OU
2. Faça upload na aba "Upload"

**O que o agente faz automaticamente:**
1. ✅ Extrai todos os dados (emitente, itens, valores, impostos)
2. ✅ Valida contra regras fiscais brasileiras
3. ✅ Classifica por tipo de operação e centro de custo
4. ✅ **Salva no banco de dados** (você pode consultar depois!)
5. ✅ Mostra resumo completo

**Exemplo de resposta:**
```
✅ Documento processado e salvo com sucesso!

📄 DOCUMENTO
• Tipo: NFe (Nota Fiscal Eletrônica)
• Número: 3510129 / Série: 1
• Chave: 35240512345678000190650010000351291234567890
• Data: 18/01/2024

🏢 EMITENTE (FORNECEDOR)
• Nome: COMPANHIA BRASILEIRA DE EDUCAÇÃO
• CNPJ: 12.345.678/0001-90

👤 DESTINATÁRIO
• Nome: MINHA EMPRESA LTDA
• CNPJ: 98.765.432/0001-00

📦 ITENS (1 item)
1. Serviço de Educação
   • NCM: 4901 (Livros e Material Didático)
   • Quantidade: 1
   • Valor unitário: R$ 522.50
   • Total: R$ 522.50

💰 VALORES
• Produtos: R$ 522.50
• Total NF: R$ 522.50

✅ VALIDAÇÃO
Nenhum problema encontrado!

🏷️ CLASSIFICAÇÃO
• Tipo: Compra (entrada)
• Centro de Custo: Livros e Material Didático
• Confiança: 85%
```

---

## 💡 Perguntas sobre Fiscal (Conhecimento Geral)

✅ **Perguntas que funcionam:**
- "O que é CFOP?"
- "Explica o que é NCM"
- "Qual a diferença entre NFe e NFCe?"
- "Como funciona o ICMS?"
- "O que significa CST?"
- "Quando usar CFOP 5102?"

**O agente explica em linguagem simples!**

**Exemplo:**
```
📚 NCM (Nomenclatura Comum do Mercosul)

NCM é um código de 8 dígitos que classifica produtos no comércio internacional:

🔢 Estrutura:
• 2 primeiros dígitos: Capítulo (ex: 49 = Livros)
• 4 primeiros dígitos: Posição (ex: 4901 = Livros impressos)
• 8 dígitos: Item completo

💡 Para que serve:
• Identificar o produto para fins fiscais
• Calcular impostos corretos (ICMS, IPI)
• Comércio exterior (importação/exportação)
• Classificação em centros de custo

📖 Exemplos:
• 4901: Livros e material didático
• 6403: Calçados de couro
• 8471: Computadores e equipamentos de TI

⚠️ Importante: Usar o NCM errado pode resultar em impostos incorretos!
```

---

## 📈 Estatísticas e Resumos

✅ **Perguntas que funcionam:**
- "Mostra um resumo geral"
- "Estatísticas do banco de dados"
- "Quanto já processamos?"
- "Resumo de documentos"

**O que o agente mostra:**
- Total de documentos processados
- Breakdown por tipo (NFe, NFCe, etc.)
- Breakdown por operação (compra, venda, etc.)
- Valor total
- Período coberto
- Principais fornecedores/clientes

---

## 🔍 Investigando Problemas

### ❌ Problemas de Validação

✅ **Perguntas que funcionam:**
- "Existem documentos com erros?"
- "Mostra notas com problemas"
- "Quais documentos têm inconsistências?"
- "Validação da nota [número]"

### 💰 Verificando Valores

✅ **Perguntas que funcionam:**
- "Qual o valor total de compras?"
- "Quanto gastamos em 2024?"
- "Total de vendas do mês"
- "Soma de todas as notas"

---

## ⚠️ Evite Estes Erros Comuns

### ❌ NÃO use termos técnicos desnecessários

**Em vez de:**
```
"Execute search_invoices_database com operation_type='purchase' e days_back=365"
```

**Diga simplesmente:**
```
"Quantas compras do ano passado?"
```

### ❌ NÃO assuma que precisa fornecer datas exatas

**Em vez de:**
```
"Buscar documentos entre 01/01/2024 e 31/12/2024"
```

**Diga simplesmente:**
```
"Documentos de 2024"
```

### ❌ NÃO use jargão fiscal se não souber

**Em vez de:**
```
"Notas com CFOP 5102"
```

**Diga simplesmente:**
```
"Vendas de mercadorias"
```

O agente vai entender e usar os códigos corretos!

---

## 🎯 Exemplos de Conversas Completas

### Exemplo 1: Contando Compras

```
👤 Você: "Quantas notas de compra temos?"

🤖 Agente: 📊 Temos 2 notas de compra no sistema!

💰 Valor total: R$ 1,522.50

📥 Documentos encontrados:
1. NFe 3510129/1 - 18/01/2024 - R$ 522.50
2. NFe 1/1 - 15/01/2024 - R$ 1,000.00

✨ Posso mostrar detalhes de alguma nota específica?

👤 Você: "Mostra a primeira"

🤖 Agente: [Detalhes completos da NFe 3510129/1...]
```

### Exemplo 2: Investigando Período

```
👤 Você: "Vendas de 2024"

🤖 Agente: 📊 Encontrei 5 vendas em 2024:

💰 Valor total: R$ 12,450.00

📤 Documentos:
1. NFe 001/1 - 15/01/2024 - R$ 2,500.00
2. NFe 002/1 - 28/02/2024 - R$ 3,200.00
[...]

📈 Média por venda: R$ 2,490.00

✨ Quer ver algum detalhamento específico?
```

### Exemplo 3: Processando Novo Documento

```
👤 Você: [Cola XML da nota]

🤖 Agente: ✅ Documento processado e salvo!

📄 NFe 123/1 - Compra de R$ 1,500.00
🏢 Fornecedor: EMPRESA ABC LTDA
📅 Data: 16/10/2025

✅ Validação: Sem problemas
🏷️ Classificado como: Material de Escritório (90% confiança)

📊 Agora você tem 3 compras no total!

✨ Quer que eu mostre todas as compras?
```

---

## 🚀 Dicas para Melhores Resultados

### ✅ Seja Natural
Fale como você falaria com um colega de trabalho.

### ✅ Seja Específico (quando necessário)
- Em vez de "notas", especifique "notas de compra" ou "notas de venda"
- Se souber o CNPJ, fornecê-lo ajuda na precisão

### ✅ Explore!
O agente está aqui para ajudar. Faça perguntas, peça esclarecimentos, peca para ver mais detalhes.

### ✅ Use Follow-ups
```
Você: "Quantas compras?"
Agente: [Responde]
Você: "Mostra a mais cara"
Agente: [Mostra detalhes]
Você: "Essa nota tem problemas?"
Agente: [Valida e responde]
```

---

## 📞 Precisa de Ajuda?

Se o agente não entender sua pergunta:
1. Reformule de forma mais simples
2. Divida em perguntas menores
3. Use os exemplos deste guia como referência

**Exemplo:**
```
❌ Complexo: "Mostre análise comparativa de fluxo de caixa por tipo de operação fiscal segregado por centro de custo"

✅ Simples: 
  1. "Quantas compras temos?"
  2. "Quantas vendas temos?"
  3. "Qual o total de cada tipo?"
```

---

## 🎓 Aprendendo Mais

À medida que usar o sistema, você aprenderá:
- ✅ Termos fiscais básicos (NFe, CFOP, NCM)
- ✅ Como interpretar validações
- ✅ Padrões nos seus documentos
- ✅ Como otimizar suas perguntas

O agente sempre explica termos técnicos quando os usa! 📚

---

**Última atualização:** 16/10/2025
**Versão do Sistema:** 1.0
