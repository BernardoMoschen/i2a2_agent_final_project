# Quick Start Guide

## 🚀 Get Started in 3 Minutes

### 1. Activate Environment

```bash
cd /home/bmos/private/private_repos/i2a2/projeto_final
source venv/bin/activate
```

### 2. Run Tests

```bash
pytest tests/ -v
```

Expected: **21 tests passing** ✅

### 3. Launch Streamlit UI

```bash
streamlit run src/ui/app.py
```

Opens browser at `http://localhost:8501`

### 4. Run Demo Script

```bash
PYTHONPATH=/home/bmos/private/private_repos/i2a2/projeto_final python examples/demo_parser_validator.py
```

See parser and validator in action! ✨

---

## 📖 Common Tasks

### Run Code Quality Checks

```bash
# Format
black src/ tests/
isort src/ tests/

# Lint
ruff check src/ tests/

# All in one
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Individual Components

```bash
# XML Parser only
pytest tests/test_xml_parser.py -v

# Validator only
pytest tests/test_fiscal_validator.py -v
```

---

## 🧪 Try the Parser and Validator

Create a test script `test_manual.py`:

```python
from src.tools.xml_parser import XMLParserTool
from src.tools.fiscal_validator import FiscalValidatorTool

# Sample NFe XML (minimal valid structure)
xml = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35240112345678000190550010000000011234567890" versao="4.00">
      <ide>
        <mod>55</mod>
        <serie>1</serie>
        <nNF>1</nNF>
        <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>12345678000190</CNPJ>
        <xNome>EMPRESA TESTE LTDA</xNome>
      </emit>
      <dest>
        <CNPJ>98765432000100</CNPJ>
        <xNome>CLIENTE TESTE SA</xNome>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>PROD001</cProd>
          <xProd>PRODUTO TESTE</xProd>
          <NCM>12345678</NCM>
          <CFOP>5102</CFOP>
          <uCom>UN</uCom>
          <qCom>10.00</qCom>
          <vUnCom>100.00</vUnCom>
          <vProd>1000.00</vProd>
        </prod>
        <imposto>
          <ICMS><ICMS00><vICMS>180.00</vICMS></ICMS00></ICMS>
          <IPI><IPITrib><vIPI>100.00</vIPI></IPITrib></IPI>
          <PIS><PISAliq><vPIS>16.50</vPIS></PISAliq></PIS>
          <COFINS><COFINSAliq><vCOFINS>76.00</vCOFINS></COFINSAliq></COFINS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vProd>1000.00</vProd>
          <vICMS>180.00</vICMS>
          <vIPI>100.00</vIPI>
          <vPIS>16.50</vPIS>
          <vCOFINS>76.00</vCOFINS>
          <vNF>1100.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""

# Parse XML
parser = XMLParserTool()
invoice = parser.parse(xml)

print(f"✅ Parsed: {invoice.document_type} #{invoice.document_number}")
print(f"   Issuer: {invoice.issuer_name}")
print(f"   Total: R$ {invoice.total_invoice}")
print(f"   Items: {len(invoice.items)}")

# Validate
validator = FiscalValidatorTool()
issues = validator.validate(invoice)

print(f"\n📋 Validation: {len(issues)} issue(s)")
for issue in issues:
    print(f"   [{issue.severity.upper()}] {issue.code}: {issue.message}")
```

Run it:

```bash
python test_manual.py
```

---

## 🔧 Troubleshooting

### Import Errors

Make sure you're in the project root and virtual environment is active:

```bash
cd /home/bmos/private/private_repos/i2a2/projeto_final
source venv/bin/activate
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Streamlit Not Found

```bash
pip install streamlit
```

---

## 📁 Project Structure Quick Reference

```
projeto_final/
├── src/
│   ├── models/          # Pydantic models (InvoiceModel, ValidationIssue, etc.)
│   ├── tools/           # Parser, Validator (Classifier, DB, Archiver TODO)
│   ├── agent/           # LangChain agent (TODO)
│   ├── database/        # SQLite operations (TODO)
│   ├── ui/              # Streamlit app (placeholder)
│   └── utils/           # Config, helpers
├── tests/               # Unit tests (21 passing)
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Tool configuration
├── README.md            # Full documentation
├── STATUS.md            # Current status and roadmap
└── QUICKSTART.md        # This file
```

---

## 🎯 Next Actions

1. **Review** `STATUS.md` for full roadmap
2. **Explore** `README.md` for detailed setup
3. **Run tests** to verify everything works
4. **Check** `github/copilot-instructions.md` for requirements
5. **Start building** database, classifier, or archiver tools

---

Happy coding! 🚀
