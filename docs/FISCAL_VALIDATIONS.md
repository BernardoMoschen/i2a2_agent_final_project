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

### 1. Validação de Chave de Acesso (VAL001)

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

- **10 validações fiscais fundamentais**
- **Sistema extensível** para adicionar regras
- **3 níveis de severidade** (ERROR, WARNING, INFO)
- **Sugestões automáticas** de correção
- **Reportagem completa** (UI, DB, Agent)

### ❌ O que NÃO faz (ainda):

- **Validações específicas por indústria/setor**
- Validação de CST/CSOSN avançada
- Integração com tabelas SEFAZ (NCM, CFOP, municípios)
- Validação de protocolo SEFAZ

### 🚀 Como Expandir:

1. **Adicionar validações genéricas** (VAL011-VAL015)
2. **Criar módulos por setor** (pharma, auto, agro, etc.)
3. **Integrar tabelas oficiais** (NCM-SH, CFOP, IBGE)
4. **Validação com SEFAZ** (consulta protocolo, status)

O sistema foi projetado para ser **facilmente extensível** - você pode adicionar novas regras sem modificar o código core, seguindo o padrão `ValidationRule`.
