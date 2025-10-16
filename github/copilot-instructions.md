Copilot Guidelines (for LLM Fiscal XML Agent — LangChain + Gemini + Streamlit)

1. Project overview

This repository implements an LLM-backed Fiscal Document Agent to automate processing, validation, classification, and archiving of fiscal documents (XMLs like NFe/NFCe/CTe/MDF-e).
The agent is built with Python + LangChain, uses Gemini (API key provided by user at runtime), persists structured data to SQLite, and provides a Streamlit frontend for upload, chat interaction, and results visualization.

Primary responsibilities for Copilot suggestions:

Produce clean, type-annotated Python code following PEP8.

Use LangChain agent patterns and tools; create modular, testable "tools" for tasks (XML parsing, validation, classification, DB write/read, archiving, plotting).

Respect security and privacy: never hardcode secrets; always read from secure config/env or UI input.

2. Stack & tooling (what Copilot should assume)

Python 3.11+ (type hints everywhere)

LangChain (agent + tools pattern)

Gemini access via API key (user-provided at runtime)

SQLite (use sqlite3 or SQLModel/SQLAlchemy for ORM)

Streamlit for frontend

XML handling: xml.etree.ElementTree, lxml, or defusedxml for safety

Dataframe/reporting: pandas

Plotting: matplotlib (server-side), optionally plotly if interactive required

Linters & formatters: black, isort, ruff/flake8, mypy

Tests: pytest

Packaging: requirements.txt or pyproject.toml (Poetry optional)

Pre-commit hooks recommended

3. Coding standards & style (explicit)

Language: English (docstrings, variable names, comments).

Formatting: black + isort. Automatic formatting in pre-commit.

Typing: Use typing for all public functions. Aim for mypy-clean where reasonable.

Docstrings: Use Google style or NumPy style (be consistent). Each module/function/class must have a clear docstring explaining intent, args, return types, and exceptions raised.

Logging: Use Python logging. No print() in production code.

Error handling: Prefer explicit exceptions; do not swallow errors silently.

Security: No secrets in code. When returning or logging results, redact sensitive fields (tax IDs, full taxpayer names) unless user explicitly enables PII output.

4. Repo / architecture layout (recommended)
   /repo-root
   ├─ src/
   │ ├─ agent/
   │ │ ├─ **init**.py
   │ │ ├─ tools/ # LangChain tools: xml_parser, validator, classifier, archiver, db_tool, plot_tool
   │ │ ├─ agent_core.py # agent orchestration & tool registration
   │ │ ├─ prompts.py # canonical prompts & templates
   │ ├─ services/
   │ │ ├─ xml_parsers.py
   │ │ ├─ validators.py
   │ │ ├─ classifier.py
   │ │ ├─ db.py # sqlite wrapper / models
   │ │ ├─ archiver.py
   │ │ ├─ reports.py # plotting & csv/xlsx export
   │ ├─ schemas/
   │ │ ├─ models.py # pydantic models for normalized invoice
   │ ├─ utils/
   │ │ ├─ security.py # redaction, secrets utilities
   │ │ ├─ io_helpers.py
   ├─ streamlit_app/
   │ ├─ app.py
   │ ├─ components/
   │ ├─ static/
   ├─ tests/
   ├─ pyproject.toml / requirements.txt
   ├─ copilot-guidelines.md
   ├─ README.md

Copilot should suggest files in these folders and prefer modular single-responsibility functions.

5. Agent design & tools (explicit expectations)

The LLM agent receives a toolset. Each tool must have:

A short, precise name and purpose.

Type-hinted input and output models (use pydantic).

Deterministic fallback behavior on error.

Recommended tool list (implement as LangChain Tools):

xml_parser — parse uploaded XMLs (single or zipped). Output: standardized InvoiceModel.

fiscal_validator — validate fields: totals, CFOP, CST, NCM, tax rates, and cross-check computed taxes vs declared.

classifier — classify document type (purchase/sale/service) and cost center based on rules + ML model.

inconsistency_detector — return list of issues with severity (error/warning) and suggested fixes.

db_tool — persist normalized data to SQLite and query by filters.

archiver — move original documents to structured storage (local S3, folder structure by year/party/type).

report_generator — create CSV/Excel and produce plots for user; return paths and summary statistic.

custom_rules_engine — load company-specific rules (occupation-specific mapping) and apply them.

audit_trail — log agent decisions for traceability (who, when, input, output).

plot_tool — produce matplotlib figure and return file path or embed for Streamlit.

For each tool Copilot generates, include unit tests and input validation.

6. XML processing & normalization rules

Always use a safe XML library (e.g., defusedxml or lxml with safe options).

Map raw XML fields into a InvoiceModel (pydantic) with canonical names:

invoice_id, date, supplier, buyer, items[] (each with ncm, cfop, cst, quantity, unit_value, total_value, taxes), totals, raw_xml_reference.

Keep both normalized and raw copies in DB.

On parsing, compute derived values (sum items, computed tax totals) and compare with declared totals (use Decimal for money — never float).

7. Fiscal validation & rules

Copilot suggestions must:

Use authoritative rule files or configuration (YAML/JSON) rather than hard-coded rules.

Validate:

NCM format and ranges

CFOP valid for document type

CST matching tax regime

Quantity × unit price = item total within tolerance (document rounding rules)

Sum of items = invoice total

Tax base and tax calculations for ICMS, IPI, PIS, COFINS, ISS (basic checks)

Return structured findings: [{code, severity, message, field, suggestion}].

8. Classification & cost-centers

Use rule-based fallback first, then an ML model if configured.

Cost-center mapping must be overrideable per-branch/company. Provide UI for CSV mapping upload.

Maintain confidence score on classification. If confidence < threshold, mark for human review.

9. Database & storage

Use SQLite for quick setup. Keep schema migrations manageable; include migration script (e.g., alembic optional).

Tables:

invoices (id, date, supplier, type, totals, normalized_json, raw_xml_path, created_at)

issues (invoice_id, code, severity, resolved, notes)

classifications

archived_files

Index fields frequently queried (date, supplier, invoice_id).

For large scale: make code easily swappable to PostgreSQL/SQLAlchemy engine.

10. Streamlit frontend expectations

Pages/components:

Upload: XML single or ZIP; show parsing progress; preview parsed fields.

API Key Input: secure text_input (use st.secrets or ephemeral state). Do not store keys in repo.

Model selection: dropdown for Gemini models.

Chat: agent chat interface; user messages routed to LangChain agent; show structured outputs (issues list, attachments).

Document list: search/filter, view normalized fields, download original XML.

Reports: show generated plots and CSV download links.

Safety: warn user about sharing PII; provide toggle for redaction in UI.

11. Tests & CI

Unit tests for:

XML parsing with representative samples.

Validation rules (edge cases).

DB read/write.

Tool interface contracts.

Simple integration tests: agent flow on sample XML dataset.

CI pipeline (GitHub Actions):

Run black --check, ruff check, mypy, pytest.

Do not run any job that requires the Gemini key; provide a mock for LLM responses in tests.

12. Security & compliance (must follow)

Never hardcode API keys. Copilot must generate code that reads keys from environment variables or from secure Streamlit input at runtime.

Redact or hash PII in logs and the audit trail unless user enables full-mode.

Use safe XML parsing (defusedxml).

Provide explicit user consent UI for storing personal data and for enabling agent actions that modify/forward data.

13. Performance & scaling notes

Use streaming parsing for large XMLs if needed.

Use SQLite pragmas to optimize writes when ingesting batches; modularize DB code to support swapping to Postgres.

Batch validation for zip uploads: parse in parallel but enforce rate-limited calls to Gemini.

14. “Do / Don’t” directives for Copilot

Do:

Produce functions with type hints and docstrings.

Create small, testable units (SRP).

Suggest config files for linters and pre-commit.

Generate safe, non-sensitive example data in tests.

Create explicit exceptions and error messages that help users act.

Don’t:

Hardcode API keys, secrets, or production endpoints.

Suggest using pickle or insecure serialization for untrusted data.

Use floats for money calculations.

Log full taxpayer IDs or raw XML contents to public logs.

Produce legal or tax advice as factual — the agent should flag uncertain cases for human review.

15. Example prompts & templates for Copilot to follow

Use these prompt templates when asking Copilot to write functions:

Function skeleton

# Task: implement function to parse NFe XML into InvoiceModel

# Requirements:

# - Use defusedxml or lxml

# - Return InvoiceModel (pydantic)

# - Use Decimal for monetary fields

# - Include docstring and type hints

def parse_nfe_xml(xml_bytes: bytes) -> InvoiceModel:
"""Parse NFe XML bytes and return InvoiceModel.
Args:
xml_bytes: raw bytes of the XML file.
Returns:
InvoiceModel: normalized invoice representation.
Raises:
InvoiceParseError: if required fields are missing or malformed.
"""
...

Tool registration in agent_core

# Register these tools with LangChain agent:

# xml_parser, fiscal_validator, classifier, db_tool, archiver, report_generator

def create_agent(tools: List[Tool], model_name: str, api_key: str) -> Agent:
"""Create LangChain agent with given tools and model selection."""
...

Unit test example

def test_parse_nfe_xml_basic():
xml = SAMPLE_NFE_BYTES
invoice = parse_nfe_xml(xml)
assert invoice.invoice_id == "..."
assert invoice.totals.subtotal == Decimal("123.45")

16. Example of an ideal Copilot-generated function (short)

Should be fully typed

Include docstring and basic validation

Use Decimal and pydantic model

Raise meaningful exceptions

(Use the above skeleton as guide.)

17. Acceptance criteria for Copilot suggestions

When Copilot generates code, it should meet these checks:

Code compiles (no syntax errors) and passes mypy for the changed module.

Includes docstrings and tests for new public behavior.

Uses safe XML parsing and Decimal for money.

Avoids secrets in code.

Respects repository folder structure and modular design.

18. Commit & PR conventions

Commit message format: type(scope): short description (e.g., feat(parser): add NFe parser for xml v4.0)

Types: feat, fix, docs, chore, refactor, test.

Pull request should include:

Summary of changes

How to test locally

Security implications

Migration notes (if DB changes)

19. Examples of prompts to give the agent at runtime

These are natural-language templates the user may use in the Streamlit chat; include them in prompts.py to standardize outputs.

"Parse and normalize this invoice, list any inconsistencies, and suggest fixes."

"Classify uploaded invoices by cost center and return confidence scores."

"Archive invoices from 2024 for supplier X into folder structure year/supplier/type and return a CSV with paths."

"Generate a monthly taxes summary (ICMS, IPI, PIS/COFINS) and provide a plot."

Make sure the agent's responses are structured JSON when returning machine-readable outputs, and a human-friendly summary for chat display.

20. Final notes & meta

Keep the copilot-guidelines.md short and actionable (this file). For deeper rules (tax logic, CFOP/NCM catalogs), keep a rules/ directory with versioned YAML rulebooks.

Track changes to rules and agent prompts — they are part of compliance.

Encourage Copilot to generate unit tests together with features.
