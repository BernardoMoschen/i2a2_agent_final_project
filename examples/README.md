# Examples & Demo Scripts

This directory contains demonstration scripts and examples for the Fiscal Document Agent project.

## Project Management

**`manage_project.sh`** - Master project management script
- `./manage_project.sh setup` - Setup development environment (creates venv, installs dependencies)
- `./manage_project.sh deploy` - Setup for Streamlit Cloud deployment
- `./manage_project.sh run` - Run the Streamlit application
- `./manage_project.sh help` - Show help

## Example Demos

These scripts demonstrate different capabilities of the agent:

### Core Functionality
- **`demo_agent.py`** - Complete agent workflow with chat interface
- **`demo_agent_chat.py`** - Conversational agent with multi-turn interaction
- **`demo_parser_validator.py`** - XML parsing and fiscal validation examples

### Business Logic
- **`demo_reports.py`** - Generate reports and visualizations
- **`demo_high_impact_validations.py`** - Validate critical fiscal rules
- **`demo_phase2_phase3.py`** - Advanced processing workflows

### Knowledge & Tools
- **`demo_general_knowledge.py`** - General knowledge questions (non-database)
- **`demo_val026_cnpj_api.py`** - External API validation (CNPJ, CEP, NCM)
- **`demo_download_ncm_table.py`** - Download and process NCM commodity table

## Running Examples

```bash
# Install dependencies first
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run an example
python examples/demo_agent.py
python examples/demo_reports.py
```

## Example Categories

| Category | Purpose | Files |
|----------|---------|-------|
| **Core Agent** | Agent chat and interaction patterns | demo_agent.py, demo_agent_chat.py |
| **Processing** | XML parsing and document processing | demo_parser_validator.py |
| **Business** | Reports, validations, workflows | demo_reports.py, demo_high_impact_validations.py |
| **External APIs** | Third-party validation services | demo_val026_cnpj_api.py |
| **Maintenance** | Data management scripts | demo_download_ncm_table.py |

## Adding New Examples

When adding new demo scripts:
1. Name them `demo_*.py` following the existing pattern
2. Include a module docstring explaining the demo
3. Add usage instructions to this README
4. Keep examples focused and self-contained
5. Update the table above

---

See [../docs/QUICKSTART.md](../docs/QUICKSTART.md) for getting started instructions.
