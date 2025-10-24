# Guia: Expandir Tabela NCM com Dados Oficiais

## 📋 Visão Geral

Este guia explica como **expandir a tabela NCM** de 23 códigos para a **tabela TIPI completa** (~10.000 códigos) usando fontes oficiais do governo brasileiro.

---

## 🎯 Opções para Obter a Tabela NCM Completa

### **Opção 1: Download Manual da TIPI (Recomendado)**

#### **Fonte: Receita Federal do Brasil**

1. **Acesse o site da Receita Federal**:
   ```
   https://www.gov.br/receitafederal/pt-br
   ```

2. **Busque por "TIPI"** ou navegue:
   - Menu: Acesso à Informação → Legislação
   - Procure: "Tabela de Incidência do IPI - TIPI"

3. **Baixe a tabela** (disponível em):
   - **PDF** (mais comum) - requer conversão
   - **Excel/CSV** (ideal) - pode ser usado diretamente
   - **Anexo ao Decreto nº 11.158/2022** (última versão)

4. **URL Direto (verificar se ainda ativo)**:
   ```
   https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/
   tributos/ipi/tipi-tabela-de-incidencia-do-imposto-sobre-produtos-industrializados
   ```

#### **Formato Esperado**:
```csv
ncm,description,ipi_rate
01011000,Cavalos reprodutores de raça pura,0
01012100,Cavalos vivos,2
01022100,Bovinos reprodutores de raça pura,0
...
```

---

### **Opção 2: IBGE - Sistema de Nomenclaturas**

1. **Acesse CONCLA (Comissão Nacional de Classificação)**:
   ```
   https://concla.ibge.gov.br/classificacoes
   ```

2. **Navegue até NCM**:
   - Classificações → Produtos → NCM

3. **Baixe a tabela completa** (Excel ou CSV)

**Vantagens**:
- ✅ Dados oficiais do IBGE
- ✅ Atualização periódica
- ✅ Formato estruturado

**Desvantagens**:
- ⚠️ Pode não incluir alíquotas de IPI
- ⚠️ Requer processamento adicional

---

### **Opção 3: Sistema Siscomex (Para Importação)**

1. **Portal Siscomex**:
   ```
   https://www.gov.br/siscomex/
   ```

2. **Acesse**: 
   - Simulador de Tratamento Tributário e Administrativo
   - Tabela TEC (Tarifa Externa Comum)

3. **Baixe a TEC** (contém NCM + Imposto de Importação)

**Vantagens**:
- ✅ Inclui Imposto de Importação (II)
- ✅ Tarifa Externa Comum do Mercosul

**Desvantagens**:
- ⚠️ Foco em importação
- ⚠️ Não inclui IPI doméstico

---

### **Opção 4: API do Governo Federal (Futura)**

**Status**: Em desenvolvimento pelo governo

- Portal de Dados Abertos: `https://dados.gov.br`
- Buscar por: "NCM", "TIPI", "IPI"

**Quando disponível**:
```python
import requests

response = requests.get('https://api.dados.gov.br/v1/ncm')
ncm_data = response.json()
```

---

## 🛠️ Como Usar o Script de Download

### **Modo 1: Criar Sample Expandido (Teste)**

Cria uma amostra com ~120 NCMs cobrindo todos os capítulos principais:

```bash
python scripts/download_ncm_table.py --source sample --output data/ncm_codes.csv
```

**Resultado**:
```
✅ Created expanded sample with 120 NCM codes
   Saved to: data/ncm_codes.csv
```

---

### **Modo 2: Processar CSV Manual**

Depois de baixar a TIPI da Receita Federal:

```bash
# Se você tem um CSV
python scripts/download_ncm_table.py \
    --source manual \
    --input ~/Downloads/tipi_2024.csv \
    --output data/ncm_codes.csv

# Se você tem um Excel
python scripts/download_ncm_table.py \
    --source manual \
    --input ~/Downloads/tipi_2024.xlsx \
    --output data/ncm_codes.csv
```

**O script vai**:
1. ✅ Ler o arquivo CSV/Excel
2. ✅ Validar formato NCM (8 dígitos)
3. ✅ Remover duplicatas
4. ✅ Gerar estatísticas
5. ✅ Salvar em `data/ncm_codes.csv`

---

### **Modo 3: Processar PDF da TIPI**

Se você só tem o PDF da Receita Federal:

#### **Passo 1: Converter PDF para Excel**

Use ferramentas online ou locais:

**Online** (gratuito):
- https://www.ilovepdf.com/pdf_to_excel
- https://smallpdf.com/pdf-to-excel

**Local** (Python):
```bash
pip install tabula-py
python -c "import tabula; tabula.convert_into('tipi.pdf', 'tipi.csv', pages='all')"
```

#### **Passo 2: Processar CSV gerado**
```bash
python scripts/download_ncm_table.py \
    --source manual \
    --input tipi.csv \
    --output data/ncm_codes.csv
```

---

## 📊 Estrutura da Tabela NCM

### **Estrutura do Código NCM (8 dígitos)**

```
NCM: 8 5 1 7 1 2 3 1
     │ │ │ │ │ │ │ │
     │ │ │ │ │ │ └─┴─ Subitem
     │ │ │ │ └─┴───── Item
     │ │ └─┴───────── Subposição
     └─┴───────────── Capítulo
```

**Exemplo**: `85171231`
- **85**: Capítulo 85 - Máquinas e aparelhos elétricos
- **8517**: Posição - Aparelhos telefônicos
- **851712**: Subposição - Telefones para redes celulares
- **85171231**: Item - Telefones celulares

### **Capítulos da TIPI (96 capítulos)**

A tabela está organizada em **21 seções** e **96 capítulos**:

| Capítulos | Seção | Descrição |
|-----------|-------|-----------|
| 01-05 | I | Animais vivos e produtos do reino animal |
| 06-14 | II | Produtos do reino vegetal |
| 15 | III | Gorduras e óleos |
| 16-24 | IV | Produtos alimentícios, bebidas e fumo |
| 25-27 | V | Produtos minerais |
| 28-38 | VI | Produtos das indústrias químicas |
| 39-40 | VII | Plásticos e borracha |
| 41-43 | VIII | Peles e couros |
| 44-46 | IX | Madeira e cortiça |
| 47-49 | X | Pasta de madeira, papel |
| 50-63 | XI | Matérias têxteis |
| 64-67 | XII | Calçados, chapéus |
| 68-70 | XIII | Obras de pedra, cerâmica, vidro |
| 71 | XIV | Pérolas, pedras preciosas, metais preciosos |
| 72-83 | XV | Metais comuns |
| 84-85 | XVI | Máquinas e aparelhos elétricos |
| 86-89 | XVII | Material de transporte |
| 90-92 | XVIII | Instrumentos de precisão, óptica, música |
| 94-96 | XX | Mercadorias e produtos diversos |

---

## 🔧 Formato do CSV Gerado

### **Formato Mínimo (Requerido)**:
```csv
ncm,description
19059090,Outros pães, bolos e produtos de padaria
22030000,Cervejas de malte
```

### **Formato Completo (Recomendado)**:
```csv
ncm,description,ipi_rate
19059090,Outros pães, bolos e produtos de padaria,5
22030000,Cervejas de malte,15
85171231,Telefones celulares,12
```

### **Formato Estendido (Opcional)**:
```csv
ncm,description,ipi_rate,chapter,section,notes
19059090,Outros pães, bolos e produtos de padaria,5,19,IV,Produtos de padaria
22030000,Cervejas de malte,15,22,IV,Bebidas alcoólicas
85171231,Telefones celulares,12,85,XVI,Equipamentos de telecomunicação
```

---

## 🧪 Testar a Nova Tabela

Depois de expandir a tabela, teste:

```bash
# 1. Verificar quantos NCMs foram carregados
python -c "
from src.services.ncm_validator import get_ncm_validator
validator = get_ncm_validator()
print(f'NCMs carregados: {validator.get_table_size()}')
"

# 2. Testar validação
python -c "
from src.services.ncm_validator import get_ncm_validator
validator = get_ncm_validator()
print(f'NCM 85171231 (celular): {validator.is_valid_ncm(\"85171231\")}')
print(f'NCM 99999999 (inválido): {validator.is_valid_ncm(\"99999999\")}')
"

# 3. Rodar demo completo
python examples/demo_high_impact_validations.py
```

---

## 📈 Estatísticas Esperadas

### **Tabela TIPI Completa**:

- **Total de NCMs**: ~10.000 códigos
- **Capítulos**: 96
- **Média por capítulo**: ~100 códigos
- **Tamanho do arquivo**: ~500 KB - 1 MB
- **Tempo de carregamento**: < 100ms

### **Comparação**:

| Métrica | Sample Atual | TIPI Completa |
|---------|--------------|---------------|
| NCMs | 23 | ~10.000 |
| Cobertura | ~0.2% | 100% |
| Capítulos | 16 | 96 |
| Arquivo | ~2 KB | ~500 KB |
| Load time | < 1ms | ~50ms |

---

## 🚀 Próximos Passos Após Expandir

### **1. Validar Coverage**

Analise quantos NCMs seus invoices usam:

```python
from src.services.ncm_validator import get_ncm_validator
from src.tools.xml_parser import XMLParserTool

validator = get_ncm_validator()
parser = XMLParserTool()

# Parse todos os XMLs
invoices = [parser.parse(xml_path) for xml_path in xml_files]

# Encontre NCMs únicos
all_ncms = set()
for inv in invoices:
    for item in inv.items:
        if item.ncm:
            all_ncms.add(item.ncm)

# Verifique cobertura
valid_count = sum(1 for ncm in all_ncms if validator.is_valid_ncm(ncm))
print(f"Coverage: {valid_count}/{len(all_ncms)} ({valid_count/len(all_ncms)*100:.1f}%)")
```

### **2. Adicionar Alíquotas de IPI**

Use as alíquotas para validar impostos:

```python
# Em fiscal_validator.py - nova validação
def validate_ipi_rate(item, expected_rate):
    """Validate IPI rate matches NCM table."""
    ncm_validator = get_ncm_validator()
    official_rate = ncm_validator.get_ipi_rate(item.ncm)
    
    if official_rate and item.ipi_rate != official_rate:
        return ValidationIssue(
            code="VAL041",
            severity="warning",
            message=f"IPI rate {item.ipi_rate}% doesn't match NCM table ({official_rate}%)",
        )
```

### **3. Integrar com ICMS**

Combine NCM + UF para validar ICMS:

```python
# Exemplo: validar alíquota ICMS para NCM + UF
def validate_icms_rate_by_ncm_uf(ncm, uf, declared_rate):
    """Validate ICMS rate based on NCM and state."""
    # Tabela: NCM x UF → alíquota ICMS
    # Fonte: Regulamentos estaduais de cada SEFAZ
    pass
```

---

## 📚 Recursos Adicionais

### **Legislação**:
- Decreto nº 11.158/2022 (TIPI atualizada)
- Lei nº 10.637/2002 (PIS/PASEP)
- Lei nº 10.833/2003 (COFINS)

### **Sites Oficiais**:
- Receita Federal: https://www.gov.br/receitafederal/
- IBGE CONCLA: https://concla.ibge.gov.br/
- Siscomex: https://www.gov.br/siscomex/
- Dados Abertos: https://dados.gov.br/

### **Ferramentas Úteis**:
- Consulta NCM: http://www4.receita.fazenda.gov.br/simulador/
- Classificação Fiscal: https://www.gov.br/produtividade-e-comercio-exterior/

---

## ⚠️ Avisos Importantes

1. **Atualizações**: A TIPI é atualizada periodicamente (geralmente anualmente)
2. **Backup**: Sempre mantenha backup da tabela anterior
3. **Validação**: Teste com invoices reais antes de usar em produção
4. **Legal**: Este sistema não substitui consultoria tributária profissional
5. **Cache**: Limpe o cache após atualizar a tabela

---

## ✅ Checklist de Implementação

- [ ] Baixar TIPI da Receita Federal (PDF ou Excel)
- [ ] Converter para CSV se necessário
- [ ] Executar script de processamento
- [ ] Validar formato (8 dígitos, sem duplicatas)
- [ ] Testar com NCMs conhecidos
- [ ] Verificar coverage com XMLs reais
- [ ] Atualizar testes unitários
- [ ] Documentar versão da TIPI usada
- [ ] Configurar atualização periódica (anual)

---

**Última Atualização**: Dezembro 2024  
**TIPI Vigente**: Decreto nº 11.158/2022  
**Próxima Revisão**: Verificar anualmente no site da Receita Federal
