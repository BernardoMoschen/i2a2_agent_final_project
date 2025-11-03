# Scripts & Project Management Guide

This guide explains the project management structure and available scripts.

## Quick Start

```bash
# Setup development environment
./manage_project.sh setup

# Run the application
./manage_project.sh run
```

## Project Management Script

**File:** `manage_project.sh`

This is the main entry point for all project management tasks:

### Commands

```bash
./manage_project.sh setup    # Setup dev environment (venv, dependencies)
./manage_project.sh deploy   # Setup for Streamlit Cloud deployment
./manage_project.sh run      # Run Streamlit application
./manage_project.sh help     # Show help
```

### Setup Process (`setup`)
1. Creates Python virtual environment
2. Installs dependencies from `requirements.txt`
3. Creates necessary directories (`data/cache`, `data/archives`, `logs`)
4. Sets proper file permissions

### Deployment Process (`deploy`)
- Prepares environment for Streamlit Cloud
- Creates required directories
- Sets environment variables

### Running the App (`run`)
1. Activates virtual environment
2. Checks for GEMINI_API_KEY configuration
3. Launches Streamlit application

## Environment Setup

### Manual Setup (if not using `manage_project.sh`)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set API key (required for agent)
export GEMINI_API_KEY="your-key-here"

# Run the app
streamlit run src/ui/app.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for agent |
| `STREAMLIT_SERVER_PORT` | No | Port for Streamlit (default: 8501) |
| `DATABASE_URL` | No | Database connection string |

## Demo & Example Scripts

See [`examples/README.md`](examples/README.md) for complete list of example scripts.

Quick examples:
```bash
python examples/demo_agent.py                    # Agent chat demo
python examples/demo_parser_validator.py         # XML parsing demo
python examples/demo_reports.py                  # Reports demo
python examples/demo_download_ncm_table.py       # NCM data download
```

## Directory Structure

```
.
├── manage_project.sh           # Main project management script
├── examples/
│   ├── README.md               # Examples documentation
│   ├── demo_agent.py
│   ├── demo_agent_chat.py
│   ├── demo_parser_validator.py
│   ├── demo_reports.py
│   ├── demo_high_impact_validations.py
│   ├── demo_phase2_phase3.py
│   ├── demo_general_knowledge.py
│   ├── demo_val026_cnpj_api.py
│   └── demo_download_ncm_table.py
├── src/                        # Source code
├── tests/                      # Unit tests
├── docs/                       # Documentation
├── data/                       # Data files
│   ├── cache/                  # Cached data
│   ├── archives/               # Archived documents
│   └── *.csv                   # Reference tables
└── requirements.txt            # Python dependencies
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
./manage_project.sh setup
```

### Missing Dependencies
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

### GEMINI_API_KEY Not Found
1. Get API key from: https://aistudio.google.com/app/apikey
2. Set it: `export GEMINI_API_KEY="your-key"`
3. Or enter in Streamlit interface when running

### Port Already in Use
```bash
# Use different port
streamlit run src/ui/app.py --server.port=8502
```

## CI/CD Integration

The `manage_project.sh setup` command is compatible with:
- GitHub Actions (Linux)
- GitLab CI/CD
- Streamlit Cloud (uses `deploy` variant)
- Docker deployments

## Contributing

When adding new scripts:
1. Place in `examples/` directory
2. Name as `demo_*.py` or `run_*.py`
3. Update `examples/README.md`
4. Add usage instructions
5. Test with `python examples/your_script.py`

---

For more information, see the [project documentation](docs/README.md).
