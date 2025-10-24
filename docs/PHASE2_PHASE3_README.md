# 🚀 Fase 2 & 3: Parser Enhancements + Advanced Validations

## 📋 Visão Geral

Esta implementação adiciona **9 novos campos extraídos do XML** e **4 validações fiscais avançadas** ao sistema de processamento de documentos fiscais.

## ✅ Fase 2: Parser Enhancements

### Novos Campos Extraídos

#### Nível Documento (`InvoiceModel`)

| Campo            | Tipo      | Descrição                | Exemplo                         |
| ---------------- | --------- | ------------------------ | ------------------------------- |
| `issuer_uf`      | `str`     | UF do emitente           | `"RN"`, `"SP"`, `"MA"`          |
| `recipient_uf`   | `str`     | UF do destinatário       | `"DF"`, `"RJ"`, `"BA"`          |
| `tax_regime`     | `str`     | Regime tributário (CRT)  | `"1"` (Simples), `"3"` (Normal) |
| `discount`       | `Decimal` | Desconto total (vDesc)   | `Decimal("10.50")`              |
| `other_expenses` | `Decimal` | Outras despesas (vOutro) | `Decimal("5.00")`               |

#### Nível Item (`InvoiceItem`)

| Campo         | Tipo      | Descrição            | Exemplo                             |
| ------------- | --------- | -------------------- | ----------------------------------- |
| `cst`         | `str`     | CST/CSOSN            | `"00"`, `"40"`, `"101"`             |
| `icms_origin` | `str`     | Origem da mercadoria | `"0"` (Nacional), `"1"` (Importada) |
| `icms_rate`   | `Decimal` | Alíquota ICMS (%)    | `Decimal("18.0")`                   |
| `icms_base`   | `Decimal` | Base de cálculo ICMS | `Decimal("100.00")`                 |

### Exemplo de Uso

```python
from src.tools.xml_parser import XMLParserTool

parser = XMLParserTool()
invoice = parser.parse(xml_content)

# Acessar novos campos
print(f"Operação: {invoice.issuer_uf} → {invoice.recipient_uf}")
print(f"Regime: {'Simples' if invoice.tax_regime == '1' else 'Normal'}")

for item in invoice.items:
    print(f"Item: {item.description}")
    print(f"  CST: {item.cst}")
    print(f"  Alíquota ICMS: {item.icms_rate}%")
```

## ✅ Fase 3: Advanced Validations

### VAL018: Regime Tributário × CST/CSOSN ❌ ERROR

**Regra:** CRT (regime tributário) deve ser consistente com CST/CSOSN usado.

**Validações:**

- CRT 1/2 (Simples Nacional) → deve usar CSOSN (101-900)
- CRT 3 (Regime Normal) → deve usar CST (00-90)

**Exemplo:**

```python
❌ CRT=3 (Normal) + CSOSN 101 → ERRO!
✅ CRT=3 (Normal) + CST 00 → OK
✅ CRT=1 (Simples) + CSOSN 101 → OK
```

**Importância:** Evita erro fiscal grave que pode gerar autuação.

---

### VAL021: Formato NCM ⚠️ WARNING

**Regra:** NCM deve ter exatamente 8 dígitos numéricos.

**Estrutura NCM:**

- Posições 1-6: Código SH (Sistema Harmonizado)
- Posições 7-8: TIPI (especificação Brasil)

**Exemplo:**

```python
✅ "07032090" → OK (Alho)
✅ "10059090" → OK (Milho)
❌ "0703209"  → ERRO (7 dígitos)
❌ "ABC12345" → ERRO (não numérico)
```

---

### VAL022: ICMS Interestadual ⚠️ WARNING

**Regra:** Alíquota ICMS deve ser plausível para operação interestadual.

**Alíquotas Comuns (2024):**

- Sul/Sudeste → Norte/Nordeste/CO: **7%**
- Sul/Sudeste entre si: **12%**
- Importados: **4%**

**Exemplo:**

```python
✅ SP → RJ + 12% → OK
✅ SP → BA + 7%  → OK
⚠️ SP → RJ + 25% → WARNING (incomum)
```

---

### VAL025: CFOP × UF ❌ ERROR

**Regra:** CFOP deve ser consistente com UF emitente/destinatário.

**Regras:**

- **CFOP 5xxx:** Operação dentro do estado (mesma UF)
- **CFOP 6xxx:** Operação fora do estado (UF diferente)
- **CFOP 1xxx/2xxx:** Entrada (sem regra UF)

**Exemplo:**

```python
✅ CFOP 5102 + RN → RN → OK (mesma UF)
✅ CFOP 6101 + MA → DF → OK (UF diferente)
❌ CFOP 5102 + SP → RJ → ERRO! (5xxx exige mesma UF)
❌ CFOP 6101 + SP → SP → ERRO! (6xxx exige UF diferente)
```

## 🧪 Testes

### Executar Suite Completa

```bash
python tests/test_phase2_phase3.py
```

**Cobertura:**

- ✅ Extração de todos os 9 novos campos
- ✅ Validação de funções individuais
- ✅ Validação completa em XMLs reais
- ✅ 100% passing

### Executar Demo Interativo

```bash
python examples/demo_phase2_phase3.py
```

**Demonstrações:**

1. Extração de novos campos
2. VAL018 - Regime × CST
3. VAL025 - CFOP × UF
4. VAL021 - Formato NCM
5. Validação completa de XML real

## 📊 Estatísticas do Sistema

```
Total de validações:        21 regras
├─ Básicas (VAL001-VAL010): 10 regras
├─ Avançadas (VAL011-VAL017): 7 regras
└─ Fase 2/3 (VAL018, VAL021, VAL022, VAL025): 4 regras

Campos extraídos do XML:    35+ campos
Testes automatizados:       100% passing ✅
```

## 📂 Arquivos Modificados

### Core

- **`src/models/__init__.py`**

  - `InvoiceModel`: +5 campos
  - `InvoiceItem`: +4 campos

- **`src/tools/xml_parser.py`**

  - `_parse_nfe()`: Extração UF, CRT, desconto
  - `_parse_nfe_items()`: Extração CST, ICMS detalhado

- **`src/tools/fiscal_validator.py`**
  - +4 funções de validação
  - +4 `ValidationRule`

### Documentação

- **`docs/FISCAL_VALIDATIONS.md`**
  - Seção detalhada VAL018, VAL021, VAL022, VAL025
  - Exemplos práticos e tabelas de referência

### Testes

- **`tests/test_phase2_phase3.py`**

  - Suite completa de testes (3 fases)

- **`examples/demo_phase2_phase3.py`**
  - Demo interativo das funcionalidades

## 🎯 Uso no Sistema

### Upload de XMLs (Streamlit UI)

1. Acesse: `streamlit run src/ui/app.py`
2. Aba **Upload**
3. Faça upload de XMLs
4. Sistema automaticamente:
   - Extrai os novos campos
   - Executa as 21 validações
   - Exibe resultados com severidade

### Agent Chat

```
Usuário: "Quantas notas de compra foram de fora do estado?"

Agent: 🔍 Buscando notas com CFOP 6xxx (operações interestaduais)...
       📊 Encontradas 15 notas de compra com UF diferente
```

### API Programática

```python
from src.tools.xml_parser import XMLParserTool
from src.tools.fiscal_validator import FiscalValidatorTool

parser = XMLParserTool()
validator = FiscalValidatorTool()

invoice = parser.parse(xml_content)
issues = validator.validate(invoice)

# Filtrar novas validações
new_issues = [i for i in issues if i.code in ["VAL018", "VAL021", "VAL022", "VAL025"]]

for issue in new_issues:
    print(f"{issue.code}: {issue.message}")
```

## 🚀 Próximos Passos

### Sugestões de Melhorias

1. **Tabela NCM Oficial**

   - Baixar tabela TIPI da Receita Federal
   - Validar existência do NCM (VAL021 completo)

2. **VAL019: Base Cálculo ICMS ST**

   - Validar substituição tributária
   - Formula: Base ST = Base + IPI + Frete + MVA

3. **VAL023: Relacionamentos NFe**

   - Validar notas referenciadas (devoluções)
   - Verificar chaves de acesso referenciadas

4. **Dashboard de Validações**
   - Estatísticas por tipo de validação
   - Gráficos de issues por período
   - Top erros mais frequentes

## 📚 Referências

- [Manual de Orientação do Contribuinte - NFe v6.0](http://www.nfe.fazenda.gov.br/portal/principal.aspx)
- [Tabela CFOP - Confaz](https://www.confaz.fazenda.gov.br/legislacao/convenios/1970/CV015_70)
- [Tabela NCM/TIPI - Receita Federal](http://www.receita.fazenda.gov.br/publico/tipi/TabelaTipi.aspx)
- [Código de Situação Tributária - CST/CSOSN](https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=mJ2uxD9lBHY=)

## 🤝 Contribuindo

Para adicionar novas validações:

1. Crie função helper em `fiscal_validator.py`
2. Adicione `ValidationRule` em `_build_default_rules()`
3. Documente em `docs/FISCAL_VALIDATIONS.md`
4. Adicione testes em `tests/`

## 📝 Licença

Este projeto está sob a mesma licença do projeto principal.

---

**Implementado em:** Outubro 2025  
**Versão:** 2.0 (Fase 2 & 3)  
**Status:** ✅ Produção
