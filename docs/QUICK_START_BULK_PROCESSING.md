# Quick Start: Bulk Processing Fiscal Documents

## Overview

This guide shows how to efficiently process large batches of fiscal documents (NFe, NFCe, CTe, MDFe) using the optimized bulk insert API.

## Basic Usage

### 1. Process Single XML

```python
from src.tools.xml_parser import parse_xml
from src.tools.fiscal_validator import FiscalValidator
from src.database.db import DatabaseManager

# Initialize
db = DatabaseManager("sqlite:///fiscal.db")
validator = FiscalValidator()

# Parse XML
with open("invoice.xml", "rb") as f:
    xml_bytes = f.read()

invoice = parse_xml(xml_bytes)

# Validate
issues = validator.validate_invoice(invoice)

# Save to database
saved = db.save_invoice(invoice, issues)
print(f"Saved invoice {saved.document_key}")
```

---

## Bulk Processing (Recommended for ZIP Files)

### 2. Process ZIP Archive with 100+ Documents

```python
import zipfile
from pathlib import Path
from src.tools.xml_parser import parse_xml
from src.tools.fiscal_validator import FiscalValidator
from src.tools.classifier import InvoiceClassifier
from src.database.db import DatabaseManager

# Initialize
db = DatabaseManager("sqlite:///fiscal.db")
validator = FiscalValidator()
classifier = InvoiceClassifier()  # Optional

# Process ZIP
batch = []
with zipfile.ZipFile("invoices_2024_january.zip") as zf:
    xml_files = [name for name in zf.namelist() if name.endswith(".xml")]

    print(f"Processing {len(xml_files)} XML files...")

    for xml_name in xml_files:
        # Parse
        xml_bytes = zf.read(xml_name)
        invoice = parse_xml(xml_bytes)

        # Validate
        issues = validator.validate_invoice(invoice)

        # Classify (optional)
        classification = classifier.classify(invoice)

        # Add to batch
        batch.append((invoice, issues, classification))

        # Process in chunks of 100 to avoid memory issues
        if len(batch) >= 100:
            saved = db.save_invoices_batch(batch)
            print(f"Saved batch of {len(saved)} invoices")
            batch = []

    # Process remaining
    if batch:
        saved = db.save_invoices_batch(batch)
        print(f"Saved final batch of {len(saved)} invoices")

print("Done!")
```

**Performance:**

- Individual inserts: ~15 seconds for 100 documents
- Bulk insert: **~3 seconds for 100 documents** → **5x faster**

---

## Advanced: Process with Progress Bar

### 3. Process with tqdm Progress Bar

```python
import zipfile
from tqdm import tqdm
from src.tools.xml_parser import parse_xml
from src.tools.fiscal_validator import FiscalValidator
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")
validator = FiscalValidator()

batch = []
batch_size = 100

with zipfile.ZipFile("large_archive.zip") as zf:
    xml_files = [name for name in zf.namelist() if name.endswith(".xml")]

    with tqdm(total=len(xml_files), desc="Processing XMLs") as pbar:
        for xml_name in xml_files:
            xml_bytes = zf.read(xml_name)
            invoice = parse_xml(xml_bytes)
            issues = validator.validate_invoice(invoice)

            batch.append((invoice, issues, None))

            if len(batch) >= batch_size:
                db.save_invoices_batch(batch)
                pbar.update(len(batch))
                batch = []

        if batch:
            db.save_invoices_batch(batch)
            pbar.update(len(batch))

print(f"Processed {len(xml_files)} documents")
```

---

## Querying Saved Documents

### 4. Search by Filters

```python
from datetime import date
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

# Search NFe documents from January 2024
invoices = db.search_invoices(
    document_type="NFe",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)

print(f"Found {len(invoices)} NFe invoices in January 2024")

for inv in invoices:
    print(f"- {inv.document_number}: {inv.issuer_name} → {inv.total_invoice}")
```

### 5. Get Invoice by Document Key

```python
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

invoice = db.get_invoice_by_key("35240112345678000190550010000000011234567890")

if invoice:
    print(f"Invoice #{invoice.document_number}")
    print(f"Issuer: {invoice.issuer_name}")
    print(f"Total: R$ {invoice.total_invoice}")
    print(f"Items: {len(invoice.items)}")
    print(f"Issues: {len(invoice.issues)} validation issues")

    for issue in invoice.issues:
        print(f"  [{issue.severity}] {issue.code}: {issue.message}")
```

---

## Statistics & Reports

### 6. Get Database Statistics

```python
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

stats = db.get_statistics()

print(f"Total invoices: {stats['total_invoices']}")
print(f"Total items: {stats['total_items']}")
print(f"Total validation issues: {stats['total_issues']}")
print(f"Database size: {stats.get('db_size_mb', 0):.2f} MB")

print("\nBy document type:")
for doc_type, count in stats['by_type'].items():
    print(f"  {doc_type}: {count}")
```

### 7. Generate Monthly Tax Report

```python
from datetime import date
from decimal import Decimal
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

# Get all NFe from January 2024
invoices = db.search_invoices(
    document_type="NFe",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31)
)

# Calculate totals
total_icms = sum(inv.tax_icms or Decimal(0) for inv in invoices)
total_ipi = sum(inv.tax_ipi or Decimal(0) for inv in invoices)
total_pis = sum(inv.tax_pis or Decimal(0) for inv in invoices)
total_cofins = sum(inv.tax_cofins or Decimal(0) for inv in invoices)

print("Tax Report - January 2024")
print(f"Documents: {len(invoices)}")
print(f"ICMS: R$ {total_icms:,.2f}")
print(f"IPI: R$ {total_ipi:,.2f}")
print(f"PIS: R$ {total_pis:,.2f}")
print(f"COFINS: R$ {total_cofins:,.2f}")
```

---

## Transport Documents (CTe/MDFe)

### 8. Query Transport Documents by Modal

```python
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

# Get all road transport (modal 1)
cte_road = db.search_invoices(
    document_type="CTe",
    modal="1"  # 1=Rodoviário (Road)
)

print(f"Road transport CTe: {len(cte_road)}")

# Statistics
total_cargo_weight = sum(
    cte.cargo_weight or 0
    for cte in cte_road
    if cte.cargo_weight
)

print(f"Total cargo weight: {total_cargo_weight:,.2f} kg")
```

### 9. Analyze Transport Routes

```python
from collections import Counter
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

# Get all CTe documents
cte_docs = db.search_invoices(document_type="CTe")

# Count routes
routes = Counter()
for cte in cte_docs:
    if cte.route_ufs:
        # route_ufs is stored as comma-separated string
        route = cte.route_ufs
        routes[route] += 1

print("Top 10 transport routes:")
for route, count in routes.most_common(10):
    print(f"  {route}: {count} shipments")
```

---

## Error Handling

### 10. Handle Parsing Errors

```python
from src.tools.xml_parser import parse_xml, XMLParseError
from src.database.db import DatabaseManager

db = DatabaseManager("sqlite:///fiscal.db")

successful = []
failed = []

for xml_path in xml_files:
    try:
        with open(xml_path, "rb") as f:
            invoice = parse_xml(f.read())
        successful.append(invoice)
    except XMLParseError as e:
        failed.append((xml_path, str(e)))

# Save successful
if successful:
    batch = [(inv, [], None) for inv in successful]
    saved = db.save_invoices_batch(batch)
    print(f"Saved {len(saved)} invoices")

# Report failed
if failed:
    print(f"\nFailed to parse {len(failed)} files:")
    for path, error in failed:
        print(f"  {path}: {error}")
```

---

## Best Practices

### Memory Management

- **Small batches (<100 docs):** Load all into memory, use `save_invoices_batch()`
- **Large batches (>100 docs):** Process in chunks of 100-200 to avoid memory issues
- **Very large (>1000 docs):** Use chunked processing + progress tracking

### Performance Tips

1. **Use bulk insert** for 3+ documents (faster than individual inserts)
2. **Filter queries** with indexed columns: `issue_date`, `document_type`, `issuer_cnpj`, `modal`
3. **Avoid `SELECT *`** if you only need specific fields
4. **Run VACUUM monthly** to reclaim space: `db.run_maintenance()`

### Data Integrity

- **Validate before saving:** Always run `validator.validate_invoice()` first
- **Check for duplicates:** `save_invoices_batch()` automatically skips duplicates
- **Backup regularly:** SQLite file can be copied while database is running (WAL mode)

---

## Troubleshooting

### "Invoice already exists" warning

- Expected behavior: duplicates are automatically skipped
- To force update: delete first with `db.delete_invoice(document_key)`, then save

### Slow queries

- Check if indexes are being used: `EXPLAIN QUERY PLAN SELECT ...`
- Ensure you filter by indexed columns: `issue_date`, `document_type`, `issuer_cnpj`
- Run `ANALYZE` to update index statistics

### Large database file

- Run `VACUUM` to reclaim space from deleted records
- Consider enabling XML compression (future optimization)
- Archive old documents to separate database

---

## Next Steps

- **Streamlit UI:** See `streamlit_app/app.py` for web interface
- **LLM Agent:** See `src/agent/` for natural language queries
- **Custom Rules:** See `docs/CUSTOM_RULES.md` for occupation-specific mappings
- **API Documentation:** See `docs/API.md` for full reference

---

**Performance Benchmarks:**

- Single insert: ~5ms per document
- Bulk insert (100 docs): ~3ms per document (1.6x faster)
- Query with filters: ~2ms (indexed)
- Full database scan (10K docs): ~50ms

**See also:**

- [PERFORMANCE_IMPROVEMENTS.md](./PERFORMANCE_IMPROVEMENTS.md) - Full optimization details
- [DATABASE_OPTIMIZATIONS.md](./DATABASE_OPTIMIZATIONS.md) - Technical implementation guide
