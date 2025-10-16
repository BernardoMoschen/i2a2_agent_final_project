# Fiscal Document Agent

An LLM-backed intelligent agent for automated processing, validation, classification, and archiving of Brazilian fiscal XML documents (NFe, NFCe, CTe, MDF-e).

## Features

- **XML Parsing & Normalization**: Safe parsing of fiscal XMLs with defusedxml, producing normalized Pydantic models
- **Fiscal Validation**: Declarative rule-based validation with structured issue reporting
- **Classification**: LLM-backed classification with cost-center/category mapping and confidence scores
- **Database Persistence**: SQLite storage with SQLModel/SQLAlchemy for normalized data + raw XML
- **Archiving**: Organized file storage with metadata tracking
- **Reporting**: CSV/Excel exports and matplotlib visualizations
- **Streamlit UI**: Interactive upload (single/ZIP), chat interface, validation results, and visualizations
- **Audit Trail**: Complete logging and PII redaction by default

## Tech Stack

- **Python**: 3.11+
- **LLM Framework**: LangChain with Gemini
- **Database**: SQLite with SQLModel/SQLAlchemy
- **UI**: Streamlit
- **XML Parsing**: defusedxml, lxml
- **Data & Reporting**: pandas, matplotlib, openpyxl
- **Testing**: pytest
- **Code Quality**: black, isort, ruff, mypy

## Project Structure

```
projeto_final/
├── src/
│   ├── models/          # Pydantic models (InvoiceModel, ValidationIssue, etc.)
│   ├── tools/           # LangChain agent tools (xml_parser, validator, classifier, etc.)
│   ├── agent/           # Agent core with LangChain setup
│   ├── database/        # Database schemas and operations
│   ├── ui/              # Streamlit application
│   └── utils/           # Shared utilities
├── tests/               # Unit and integration tests
├── archives/            # Archived fiscal documents
├── reports/             # Generated reports
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Tool configuration
└── README.md
```

## Setup

### Prerequisites

- Python 3.11 or higher
- pip or uv for package management

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Required for LLM classification and chat
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: database location
DATABASE_URL=sqlite:///fiscal_documents.db

# Optional: archive directory
ARCHIVE_DIR=./archives

# Optional: logging level
LOG_LEVEL=INFO
```

## Usage

### Running the Streamlit UI

```bash
streamlit run src/ui/app.py
```

Then open your browser to `http://localhost:8501`.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_xml_parser.py -v
```

### Code Quality Checks

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Development Workflow

1. **Parse**: Upload XML files (single or ZIP) via the Streamlit UI
2. **Validate**: Automatic fiscal validation with structured issue reporting
3. **Classify**: LLM-backed classification for cost centers and categories
4. **Store**: Normalized data and raw XML persisted to SQLite
5. **Archive**: Original files organized with metadata
6. **Report**: Generate CSV/Excel reports and visualizations
7. **Chat**: Interactive Q&A about your fiscal documents

## Security

- **No hardcoded secrets**: All API keys via environment variables
- **Safe XML parsing**: Uses defusedxml to prevent XXE attacks
- **PII redaction**: Default redaction in logs (opt-in to preserve)
- **Input validation**: Pydantic models with strict validation

## Testing Strategy

- **Unit tests**: Parser, validator, classifier, DB operations (with mocked LLM)
- **Integration tests**: End-to-end flows with sample XMLs
- **CI/CD**: Automated checks for formatting, linting, type checking, and tests

## Contributing

1. Ensure all tests pass: `pytest`
2. Format code: `black src/ tests/ && isort src/ tests/`
3. Lint: `ruff check src/ tests/`
4. Type check: `mypy src/`

## License

Proprietary - i2a2 Final Project

## Support

For issues or questions, contact the development team.
