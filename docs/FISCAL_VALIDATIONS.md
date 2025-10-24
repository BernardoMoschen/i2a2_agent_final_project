# Fiscal Validations - Sistema de Validação de Notas Fiscais

## Visão Geral

Sim! O sistema possui um **módulo robusto de validação fiscal** implementado em `src/tools/fiscal_validator.py` que verifica automaticamente a consistência e conformidade de todas as notas fiscais processadas.

## Arquitetura de Validação

### Sistema Declarativo de Regras

- **Pattern**: Declarative rule-based validation
- **Extensível**: Permite adicionar/remover regras customizadas
- **Severidade**: 3 níveis (ERROR, WARNING, INFO)
- **Sugestões**: Cada regra fornece orientação para correção

### Quando as Validações Ocorrem?

```
Upload XML → Parse → VALIDAÇÃO → Classificação → Save Database
                         ↓
                  Lista de Issues
```

**Momento:** Imediatamente após o parsing, antes de salvar no banco de dados.

## Validações Implementadas Atualmente

### **🔵 VALIDAÇÕES BÁSICAS (VAL001-VAL010)**

### 1. Validação de Chave de Acesso - Formato (VAL001)

- **Severidade:** ERROR ❌
- **Regra:** Chave de acesso deve ter exatamente 44 dígitos numéricos
- **Campo:** `document_key`
- **Sugestão:** "Verify the access key format"

```python
✅ Valid:   "35240512345678000190650010000001231234567890"
❌ Invalid: "3524051234567800019" (too short)
❌ Invalid: "35240512345678000190650010000001231234567ABC" (non-numeric)
```

### 2. Validação de CNPJ do Emitente (VAL002)

- **Severidade:** ERROR ❌
- **Regra:** CNPJ deve ter 14 dígitos (após remover formatação)
- **Campo:** `issuer_cnpj`
- **Sugestão:** "Verify issuer CNPJ format"

```python
✅ Valid:   "12.345.678/0001-90" → 14 dígitos
❌ Invalid: "12.345.678/0001" → apenas 11 dígitos
```

### 3. Validação de Soma de Itens (VAL003)

- **Severidade:** WARNING ⚠️
- **Regra:** Soma dos valores dos itens deve bater com `total_products`
- **Tolerância:** ±0.02 (para arredondamentos)
- **Campo:** `total_products`
- **Sugestão:** "Check for rounding errors or missing items"

```python
# Exemplo:
Item 1: R$ 100.00
Item 2: R$ 50.50
Item 3: R$ 25.00
Soma calculada: R$ 175.50
Total declarado: R$ 175.52 → ✅ OK (diferença de 0.02)
Total declarado: R$ 180.00 → ❌ FAIL (diferença > tolerância)
```

### 4. Validação de Valor Total da Nota (VAL004)

- **Severidade:** WARNING ⚠️
- **Regra:** Valor total deve corresponder aos cálculos esperados
- **Fórmula:** `total_invoice ≈ total_products + frete + seguro - desconto`
- **Campo:** `total_invoice`
- **Sugestão:** "Verify freight, insurance, discounts, and other charges"

### 5. Validação de Existência de Itens (VAL005)

- **Severidade:** ERROR ❌
- **Regra:** Nota deve conter pelo menos 1 item
- **Campo:** `items`
- **Sugestão:** "Verify XML structure and item parsing"

```python
✅ Valid:   items = [Item(...)]
❌ Invalid: items = []
```

### 6. Validação de CFOP dos Itens (VAL006)

- **Severidade:** WARNING ⚠️
- **Regra:** CFOP deve ter exatamente 4 dígitos numéricos
- **Campo:** `items[].cfop`
- **Sugestão:** "Verify CFOP codes against fiscal operation table"

```python
✅ Valid CFOPs:
- "5102" (Venda de mercadoria adquirida/recebida de terceiros)
- "1102" (Compra para comercialização)
- "6102" (Venda de mercadoria - operação interestadual)

❌ Invalid:
- "510" (apenas 3 dígitos)
- "51A2" (contém letra)
```

### 7. Validação de NCM (VAL007)

- **Severidade:** INFO ℹ️
- **Regra:** Itens devem ter código NCM preenchido
- **Campo:** `items[].ncm`
- **Sugestão:** "NCM codes help with classification and tax reporting"

**Nota:** Esta é uma validação informativa (não bloqueia processamento), mas NCM é importante para:

- Classificação fiscal
- Apuração de impostos
- Comércio exterior
- Classificação automática de centro de custo

### 8. Validação de Cálculo de Item (VAL008)

- **Severidade:** WARNING ⚠️
- **Regra:** `quantidade × preço_unitário ≈ valor_total_item`
- **Tolerância:** ±0.02
- **Campo:** `items[].total_price`
- **Sugestão:** "Check for rounding errors in item calculations"

```python
# Exemplo:
Quantidade: 10
Preço unitário: R$ 3.33
Cálculo: 10 × 3.33 = 33.30
Total declarado: R$ 33.30 → ✅ OK
Total declarado: R$ 33.50 → ❌ FAIL (diferença > 0.02)
```

### 9. Validação de Valores Positivos (VAL009)

- **Severidade:** ERROR ❌
- **Regra:** Valor total da nota deve ser positivo (> 0)
- **Campo:** `total_invoice`
- **Sugestão:** "Verify if this is a return or cancellation document"

```python
✅ Valid:   total_invoice = 100.00
❌ Invalid: total_invoice = 0.00
❌ Invalid: total_invoice = -50.00
```

### 10. Validação de Data Futura (VAL010)

- **Severidade:** WARNING ⚠️
- **Regra:** Data de emissão não pode estar no futuro
- **Campo:** `issue_date`
- **Sugestão:** "Verify system clock and document date"

```python
# Se hoje é 16/10/2025:
✅ Valid:   issue_date = 15/10/2025
✅ Valid:   issue_date = 16/10/2025 (hoje)
❌ Invalid: issue_date = 17/10/2025 (futuro)
```

---

### **🟢 VALIDAÇÕES AVANÇADAS - PRIORIDADE ALTA (VAL011-VAL017)**

### 11. Validação de Dígito Verificador do CNPJ (VAL011) ⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** CNPJ deve ter dígito verificador válido (algoritmo mod-11)
- **Campo:** `issuer_cnpj`
- **Sugestão:** "Verify CNPJ is correct - check digit validation failed"
- **Algoritmo:** Calcula os 2 últimos dígitos do CNPJ e valida

```python
✅ Valid:   "11.222.333/0001-81" → DV correto
❌ Invalid: "11.222.333/0001-99" → DV incorreto
❌ Invalid: "00.000.000/0000-00" → CNPJ inválido (todos zeros)
```

**Como funciona:**

1. Remove formatação: `11.222.333/0001-81` → `11222333000181`
2. Calcula 1º dígito verificador com pesos [5,4,3,2,9,8,7,6,5,4,3,2]
3. Calcula 2º dígito verificador com pesos [6,5,4,3,2,9,8,7,6,5,4,3,2]
4. Compara com os 2 últimos dígitos do CNPJ

### 12. Validação de Dígito Verificador da Chave de Acesso (VAL012) ⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** Chave de acesso deve ter 44º dígito verificador válido (mod-11)
- **Campo:** `document_key`
- **Sugestão:** "Access key check digit (mod 11) validation failed - verify key integrity"
- **Algoritmo:** Calcula o dígito verificador dos primeiros 43 dígitos

```python
✅ Valid:   "35240512345678000190650010000001231234567890" → DV=0 correto
❌ Invalid: "35240512345678000190650010000001231234567899" → DV incorreto
```

**Importância:**

- Detecta erros de digitação na chave
- Valida integridade da chave NFe
- Previne fraudes com chaves adulteradas

### 13. Validação CFOP × Tipo de Operação (VAL013) ⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** CFOP deve ser consistente com o tipo de operação classificado
- **Campo:** `operation_type` / `items[].cfop`
- **Sugestão:** "Verify CFOP range: 1xxx/2xxx=entry, 5xxx/6xxx=exit, 3xxx=transfer"

```python
# REGRAS:
Compra (purchase):  CFOP deve começar com 1 ou 2
Venda (sale):       CFOP deve começar com 5 ou 6
Transferência:      CFOP deve começar com 5, 6 ou 3
Devolução (return): CFOP deve começar com 1 ou 2

# EXEMPLOS:
✅ Valid:   operation_type='purchase' + CFOP='1102' (compra dentro do estado)
✅ Valid:   operation_type='sale' + CFOP='5102' (venda dentro do estado)
✅ Valid:   operation_type='sale' + CFOP='6102' (venda fora do estado)
❌ Invalid: operation_type='purchase' + CFOP='5102' (CFOP de saída em compra!)
❌ Invalid: operation_type='sale' + CFOP='1102' (CFOP de entrada em venda!)
```

**Detecção de Erros Comuns:**

- Nota classificada como "compra" mas com CFOP de venda
- Nota classificada como "venda" mas com CFOP de compra
- Inconsistência entre natureza e direção fiscal

### 14. Validação de Cálculo ICMS (VAL014) ⭐ NOVO

- **Severidade:** WARNING ⚠️
- **Regra:** `icms_base × (icms_rate / 100) ≈ icms_value` (tolerância ±0.02)
- **Campo:** `items[].icms_value`
- **Sugestão:** "Verify ICMS base, rate, and value - recalculate: base × (rate/100) = value"

```python
# EXEMPLO CORRETO:
Base ICMS:   R$ 1.000,00
Alíquota:    18%
Cálculo:     1.000,00 × 0,18 = R$ 180,00
ICMS valor:  R$ 180,00 ✅

# EXEMPLO INCORRETO:
Base ICMS:   R$ 1.000,00
Alíquota:    18%
ICMS valor:  R$ 150,00 ❌ (deveria ser R$ 180,00)
```

### 15. Validação de Cálculo PIS (VAL015) ⭐ NOVO

- **Severidade:** WARNING ⚠️
- **Regra:** `pis_base × (pis_rate / 100) ≈ pis_value` (tolerância ±0.02)
- **Campo:** `items[].pis_value`
- **Sugestão:** "Verify PIS base, rate, and value - recalculate: base × (rate/100) = value"

### 16. Validação de Cálculo COFINS (VAL016) ⭐ NOVO

- **Severidade:** WARNING ⚠️
- **Regra:** `cofins_base × (cofins_rate / 100) ≈ cofins_value` (tolerância ±0.02)
- **Campo:** `items[].cofins_value`
- **Sugestão:** "Verify COFINS base, rate, and value - recalculate: base × (rate/100) = value"

### 17. Detecção de Duplicatas (VAL017) ⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** Chave de acesso não pode já existir no banco de dados
- **Campo:** `document_key`
- **Sugestão:** "This document was already processed - check for resubmission or duplicate file"
- **Requer:** Integração com banco de dados

```python
# CENÁRIO:
1. Usuário faz upload de NFe-123.xml → Salvo no BD ✅
2. Usuário faz upload de NFe-123.xml novamente → ❌ VAL017: Duplicata detectada!

# PREVINE:
- Reprocessamento acidental
- Duplicação de registros contábeis
- Inflação artificial de totais/estatísticas
```

---

### **🟢 VALIDAÇÕES FASE 2/3 - PRIORIDADE ALTA (VAL018, VAL021, VAL022, VAL025)**

### 18. Regime Tributário × CST/CSOSN (VAL018) ⭐⭐⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** CRT (regime tributário) deve ser consistente com CST/CSOSN
- **Campos:** `tax_regime`, `items[].cst`
- **Sugestão:** "CRT 1/2 (Simples) must use CSOSN (101-900); CRT 3 (Normal) must use CST (00-90)"

**Tabela de Regras:**

| CRT | Regime            | CST/CSOSN Válido | Exemplo                     |
| --- | ----------------- | ---------------- | --------------------------- |
| 1   | Simples Nacional  | CSOSN 101-900    | CSOSN 101, 102, 201, 500 ✅ |
| 2   | Simples (excesso) | CSOSN 101-900    | CSOSN 103, 300, 400 ✅      |
| 3   | Regime Normal     | CST 00-90        | CST 00, 10, 40, 60 ✅       |

**Exemplos de Erro:**

```python
❌ CRT=3 (Normal) + CSOSN 101 → VAL018 ERROR
   Empresa no regime normal não pode usar CSOSN (exclusivo Simples)

❌ CRT=1 (Simples) + CST 00 → VAL018 ERROR
   Empresa do Simples Nacional deve usar CSOSN, não CST

✅ CRT=3 (Normal) + CST 00 → OK
✅ CRT=1 (Simples) + CSOSN 101 → OK
```

**Importância:** Evita erro fiscal grave - regime tributário errado pode gerar autuação.

---

### 19. Formato do NCM (VAL021) ⭐⭐ NOVO

- **Severidade:** WARNING ⚠️
- **Regra:** NCM deve ter exatamente 8 dígitos numéricos
- **Campo:** `items[].ncm`
- **Sugestão:** "NCM must be exactly 8 numeric digits - verify product classification"

**Formato correto:**

```python
✅ "07032090" → Alho (NCM válido)
✅ "10059090" → Milho (NCM válido)
❌ "0703209"  → 7 dígitos (incompleto)
❌ "070320901" → 9 dígitos (excesso)
❌ "ABC12345" → Caracteres não numéricos
```

**Estrutura NCM:**

- **Primeiros 6 dígitos:** Código internacional (SH - Sistema Harmonizado)
- **Últimos 2 dígitos:** Especificação brasileira (TIPI)

**Importância:** NCM incorreto pode gerar:

- Alíquota de imposto errada
- Problemas em auditorias fiscais
- Dificuldade em classificação estatística

---

### 20. Alíquota ICMS Interestadual (VAL022) ⭐⭐ NOVO

- **Severidade:** WARNING ⚠️
- **Regra:** Alíquota ICMS deve ser plausível para operação interestadual
- **Campos:** `issuer_uf`, `recipient_uf`, `items[].icms_rate`
- **Sugestão:** "Verify ICMS rate for interstate operation (common rates: 4%, 7%, 12%)"

**Alíquotas Interestaduais Comuns (2024):**

| Origem            | Destino           | Alíquota ICMS |
| ----------------- | ----------------- | ------------- |
| Sul/Sudeste       | Norte/Nordeste/CO | 7%            |
| Sul/Sudeste       | Sul/Sudeste       | 12%           |
| Norte/Nordeste/CO | Qualquer          | 12%           |
| Importados        | Qualquer          | 4%            |

**Exemplos:**

```python
✅ SP → RJ + 12% → OK (Sul/Sudeste entre si)
✅ SP → BA + 7% → OK (Sul/Sudeste para Nordeste)
✅ SP → SP + 18% → OK (alíquota interna, mesma UF)
⚠️ SP → RJ + 25% → VAL022 WARNING (alíquota incomum)
```

**Importância:** Alíquota interestadual errada é erro frequente que gera:

- Diferencial de alíquota (DIFAL) incorreto
- Problemas com partilha ICMS entre estados
- Autuação fiscal

---

### 21. CFOP × UF Consistency (VAL025) ⭐⭐⭐ NOVO

- **Severidade:** ERROR ❌
- **Regra:** CFOP deve ser consistente com UF emitente/destinatário
- **Campos:** `items[].cfop`, `issuer_uf`, `recipient_uf`
- **Sugestão:** "CFOP 5xxx = within state (same UF); CFOP 6xxx = outside state (different UF)"

**Tabela de Regras:**

| CFOP | Operação              | Regra UF                      |
| ---- | --------------------- | ----------------------------- |
| 1xxx | Entrada dentro estado | Emitente UF = Destinatário UF |
| 2xxx | Entrada fora estado   | Emitente UF ≠ Destinatário UF |
| 5xxx | Saída dentro estado   | Emitente UF = Destinatário UF |
| 6xxx | Saída fora estado     | Emitente UF ≠ Destinatário UF |
| 3xxx | Transferência         | Sem regra específica          |

**Exemplos de Validação:**

```python
✅ CFOP 5102 + RN→RN → OK (venda dentro estado)
❌ CFOP 5102 + RN→SP → VAL025 ERROR (CFOP 5xxx exige mesma UF!)

✅ CFOP 6101 + MA→DF → OK (venda fora estado)
❌ CFOP 6101 + SP→SP → VAL025 ERROR (CFOP 6xxx exige UFs diferentes!)

✅ CFOP 1102 + SP→SP → OK (compra dentro estado)
✅ CFOP 2102 + RJ→SP → OK (compra fora estado)
```

**Importância:** Erro muito comum que causa:

- Rejeição pela SEFAZ em alguns estados
- Cálculo errado de impostos (alíquota interna vs interestadual)
- Problemas em apuração de ICMS

---

## Níveis de Severidade

### ❌ ERROR (Bloqueante)

- Problemas críticos que podem indicar documento inválido
- Exemplos: CNPJ inválido, chave de acesso malformada, sem itens

### ⚠️ WARNING (Alerta)

- Inconsistências que devem ser revisadas
- Não bloqueiam o processamento
- Exemplos: diferenças de cálculo, CFOP inválido

### ℹ️ INFO (Informativo)

- Sugestões de melhoria
- Não indicam problemas
- Exemplo: NCM faltante

## Validações por Indústria/Setor

### Estado Atual: **NÃO** ❌

Atualmente o sistema **não possui validações específicas por indústria**. As validações são **genéricas** e aplicam-se a todos os tipos de documentos fiscais.

### O que o Sistema TEM (relacionado a setores):

#### 1. Classificação de Centro de Custo por NCM

O `DocumentClassifier` usa mapeamentos NCM → Centro de Custo:

```python
NCM_COST_CENTERS = {
    "4901": "Livros e Material Didático",      # Editoras
    "490[1-9]": "Livros e Material Didático",   # Material impresso
    "6403": "Calçados",                         # Indústria calçadista
    "8471": "Equipamentos de Informática",      # TI
    # ... etc
}
```

**Uso:** Classificação automática, não validação.

### Como Adicionar Validações por Indústria/Setor

O sistema foi projetado para ser **extensível**. Você pode adicionar regras customizadas:

#### Exemplo: Validação para Setor Farmacêutico

```python
# Em src/tools/fiscal_validator.py ou arquivo customizado

# 1. Criar regra customizada
pharma_rule = ValidationRule(
    code="PHARMA001",
    severity=ValidationSeverity.ERROR,
    message="Pharmaceutical products must have registration number (Anvisa)",
    check=lambda inv: all(
        # Verifica se NCM é de medicamentos (30XX)
        not item.ncm.startswith("30") or
        # E se tem campo customizado com registro Anvisa
        hasattr(item, 'anvisa_reg') and item.anvisa_reg
        for item in inv.items
    ),
    field="items[].anvisa_reg",
    suggestion="Add Anvisa registration number in additional product info"
)

# 2. Adicionar ao validador
validator = FiscalValidatorTool()
validator.add_rule(pharma_rule)
```

#### Exemplo: Validação para Comércio Exterior

```python
import_export_rule = ValidationRule(
    code="TRADE001",
    severity=ValidationSeverity.ERROR,
    message="Import/export operations must have DI/DE number",
    check=lambda inv: (
        # Se CFOP é de importação (3XXX)
        not any(item.cfop.startswith("3") for item in inv.items) or
        # Deve ter documento de importação
        hasattr(inv, 'import_declaration') and inv.import_declaration
    ),
    field="import_declaration",
    suggestion="Verify DI (Declaração de Importação) number"
)
```

#### Exemplo: Validação para Substituição Tributária (ST)

```python
st_rule = ValidationRule(
    code="TAX001",
    severity=ValidationSeverity.WARNING,
    message="Items under ICMS-ST regime must have ST base and value",
    check=lambda inv: all(
        # Se item tem CST de substituição tributária (10, 30, 60, 70)
        item.cst not in ["10", "30", "60", "70"] or
        # Deve ter valores de ST calculados
        (hasattr(item, 'icms_st_base') and item.icms_st_base > 0 and
         hasattr(item, 'icms_st_value') and item.icms_st_value > 0)
        for item in inv.items
    ),
    field="items[].icms_st_value",
    suggestion="Calculate ICMS-ST base and value for items under ST regime"
)
```

## Roadmap de Validações

### Próximas Validações Genéricas (Sugeridas)

1. **VAL011**: Validação de CST/CSOSN

   - Verificar se códigos CST são válidos
   - Verificar compatibilidade CST × regime tributário

2. **VAL012**: Validação de alíquotas de impostos

   - ICMS: verificar alíquotas por UF
   - PIS/COFINS: verificar regimes (cumulativo/não-cumulativo)

3. **VAL013**: Validação de município

   - Código IBGE deve ter 7 dígitos
   - Município deve existir na tabela IBGE

4. **VAL014**: Validação de datas

   - Data de entrada/saída deve ser >= data de emissão
   - Data de autorização SEFAZ

5. **VAL015**: Validação de protocolo SEFAZ
   - Formato do protocolo de autorização
   - Status do documento (autorizado, cancelado, denegado)

### Validações por Indústria/Setor (Sugeridas)

#### 🏭 **Indústria de Transformação**

- Validar IPI (Imposto sobre Produtos Industrializados)
- Verificar NCM compatível com atividade industrial
- Validar enquadramento IPI

#### 💊 **Farmacêutica**

- Registro Anvisa obrigatório
- Controle de lote e validade
- NCM específico de medicamentos (30XX)

#### 🚗 **Automotiva**

- Validar código RENAVAM para veículos
- Verificar chassi e placa
- NCM específico de veículos e peças

#### 🌾 **Agronegócio**

- Validar NCM de produtos agrícolas
- Verificar impostos específicos (FUNRURAL, SENAR)
- Controle de rastreabilidade

#### 🏗️ **Construção Civil**

- Validar retenção de INSS na fonte
- Verificar código de obra (CEI)
- Desoneração da folha de pagamento

#### ⚡ **Energia Elétrica**

- Validar código ANEEL
- Verificar unidade consumidora
- Validar ICMS específico para energia

#### 📚 **Livros e Editorial**

- Validar imunidade tributária (Livro-Lei 10.753/2003)
- NCM específico (4901)
- Verificar ISBN

## Como o Sistema Reporta Validações

### 1. Na Interface (Streamlit)

Após upload, a aba **Upload** mostra:

```
📋 Validation Results

✅ NFe-001.xml
   Issues Found: 2 ⚠️

⚠️ VAL003 - WARNING
   Sum of item totals does not match total_products
   Field: total_products
   💡 Check for rounding errors or missing items

ℹ️ VAL007 - INFO
   One or more items missing NCM code
   Field: items[].ncm
   💡 NCM codes help with classification and tax reporting
```

### 2. No Banco de Dados

Tabela `validation_issues`:

```sql
invoice_id | code    | severity | message                          | field          | suggestion
-----------|---------|----------|----------------------------------|----------------|------------
1          | VAL003  | WARNING  | Sum of item totals does not...  | total_products | Check for...
1          | VAL007  | INFO     | One or more items missing NCM    | items[].ncm    | NCM codes...
```

### 3. Via Agent (Chat)

User: "Existem problemas na nota 001?"

Agent:

```
📊 Análise da Nota NFe-001:

Encontrei 2 inconsistências:

⚠️ WARNING: Diferença no total de produtos
   - Soma dos itens: R$ 175.50
   - Total declarado: R$ 175.52
   - Diferença: R$ 0.02 (dentro da tolerância)

ℹ️ INFO: Item sem código NCM
   - 1 item não possui NCM informado
   - Recomendo preencher para melhor classificação fiscal
```

## API de Validação

### Uso Programático

```python
from src.tools.fiscal_validator import FiscalValidatorTool
from src.models import InvoiceModel

# 1. Create validator
validator = FiscalValidatorTool()

# 2. Validate invoice
issues = validator.validate(invoice)

# 3. Check results
if issues:
    for issue in issues:
        print(f"{issue.severity}: {issue.message}")
        if issue.suggestion:
            print(f"💡 {issue.suggestion}")
else:
    print("✅ All validations passed!")

# 4. Add custom rule
custom_rule = ValidationRule(
    code="CUSTOM001",
    severity=ValidationSeverity.ERROR,
    message="Custom validation",
    check=lambda inv: inv.total_invoice > 1000,
    field="total_invoice",
    suggestion="Invoice must be over R$ 1,000"
)
validator.add_rule(custom_rule)

# 5. Re-validate with custom rule
issues = validator.validate(invoice)
```

## Comparação com Outras Soluções

| Feature               | Este Sistema | Validadores SEFAZ | Softwares ERP |
| --------------------- | ------------ | ----------------- | ------------- |
| Validações básicas    | ✅           | ✅                | ✅            |
| Regras customizáveis  | ✅           | ❌                | ⚠️ (limitado) |
| Validações por setor  | ❌ (roadmap) | ❌                | ✅            |
| Sugestões de correção | ✅           | ❌                | ⚠️            |
| API programática      | ✅           | ❌                | ⚠️            |
| Extensível            | ✅           | ❌                | ❌            |

## Conclusão

### ✅ O que o sistema FAZ hoje:

- **21 validações fiscais** (10 básicas + 7 avançadas prioridade alta + 4 avançadas fase 2/3)
  - **Básicas (VAL001-VAL010):** Formato, estrutura, cálculos simples
  - **Avançadas Prioridade Alta (VAL011-VAL017):** Dígitos verificadores, CFOP×Operação, cálculos de impostos, duplicatas
  - **Avançadas Fase 2/3 (VAL018, VAL021, VAL022, VAL025):** Regime tributário, NCM, ICMS interestadual, CFOP×UF
- **Sistema extensível** para adicionar regras customizadas
- **3 níveis de severidade** (ERROR, WARNING, INFO)
- **Sugestões automáticas** de correção para cada falha
- **Reportagem completa** (UI, DB, Agent)
- **Validações anti-fraude:** Dígito verificador, duplicatas, consistência CFOP
- **Extração avançada de campos:** UF, CRT, CST, alíquotas ICMS, base de cálculo

### ✨ NOVIDADES (Fase 2/3 implementada):

#### **Parser Enhancements (Phase 2):**

1. ✅ **Extração de UF:** Issuer/Recipient state
2. ✅ **Extração de CRT:** Tax regime (Simples/Normal)
3. ✅ **Extração de CST/CSOSN:** Situação tributária por item
4. ✅ **Extração de alíquota ICMS:** pICMS por item
5. ✅ **Extração de base ICMS:** vBC por item
6. ✅ **Extração de desconto:** vDesc (documento)
7. ✅ **Extração de outras despesas:** vOutro (documento)

#### **Advanced Validations (Phase 3):**

8. ✅ **VAL018:** Regime Tributário × CST/CSOSN
   - CRT 1/2 (Simples) deve usar CSOSN (101-900)
   - CRT 3 (Normal) deve usar CST (00-90)
9. ✅ **VAL021:** Formato do NCM (8 dígitos)
   - NCM deve ter exatamente 8 dígitos numéricos
10. ✅ **VAL022:** Alíquota ICMS Interestadual
    - Verifica alíquotas comuns (4%, 7%, 12%) para operações interestaduais
11. ✅ **VAL025:** CFOP × UF Consistency
    - CFOP 5xxx = mesma UF (dentro do estado)
    - CFOP 6xxx = UFs diferentes (fora do estado)

### ✨ NOVIDADES (Prioridade Alta - anteriormente implementada):

1. ✅ **VAL011:** Validação de dígito verificador CNPJ/CPF
2. ✅ **VAL012:** Validação de dígito verificador da chave de acesso (44º dígito)
3. ✅ **VAL013:** Consistência CFOP × Tipo de Operação
4. ✅ **VAL014-VAL016:** Validação de cálculos de impostos (ICMS, PIS, COFINS)
5. ✅ **VAL017:** Detecção de duplicatas por chave de acesso

### ❌ O que NÃO faz (ainda):

- Validações específicas por indústria/setor (farmacêutico, combustíveis, etc.)
- Integração com tabelas SEFAZ oficiais completas (NCM-SH detalhado, CFOP completo, IBGE)
- Validação de protocolo SEFAZ (consulta status NFe online)
- Validação detalhada de substituição tributária (ST)
- Análise de sequência de numeração (VAL020 - desconsiderado por uso de notas antigas)
- Validação de prazo de emissão (VAL024 - desconsiderado por uso de notas antigas)

### 🚀 Roadmap - Próximas Validações:

#### **Prioridade MÉDIA:**

- VAL019: Base de Cálculo ICMS ST (Substituição Tributária)
- VAL023: Validação de Notas Referenciadas (devolução, complemento)
- VAL026: Desconto × Acréscimo × Total

#### **Prioridade BAIXA:**

- VAL027: Peso × Quantidade (validação logística)
- Validações setoriais (pharma, combustíveis, agro)
- Machine Learning para detecção de anomalias de preço
- Análise de sazonalidade e padrões suspeitos

**NOTA:** VAL020 (sequência) e VAL024 (prazo) foram desconsiderados pois o sistema pode processar notas antigas/históricas, onde essas validações gerariam conflitos desnecessários.

O sistema foi projetado para ser **facilmente extensível** - você pode adicionar novas regras sem modificar o código core, seguindo o padrão `ValidationRule`.
