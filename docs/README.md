# 📚 Documentation Guide

Welcome! This guide helps you navigate the documentation to understand the codebase.

## 🎯 Quick Start (5 minutes)

**If you're new to the project, start here:**

1. **[QUICKSTART.md](./QUICKSTART.md)** - Get up and running locally
2. **[AGENT_ARCHITECTURE_SUMMARY.md](./AGENT_ARCHITECTURE_SUMMARY.md)** - Understand how the agent works
3. **[AGENT_COMMUNICATION.md](./AGENT_COMMUNICATION.md)** - How agent talks to tools

## 📖 Core Architecture (Understanding the Code)

These documents explain how the system is designed:

### Agent & AI
- **[AGENT_ARCHITECTURE_SUMMARY.md](./AGENT_ARCHITECTURE_SUMMARY.md)** - Core architecture, data flow, ReAct pattern
- **[AGENT_COMMUNICATION.md](./AGENT_COMMUNICATION.md)** - Agent ↔ Tool interaction, parameter passing, response parsing
- **[AGENT_CAPABILITY_AUDIT.md](./AGENT_CAPABILITY_AUDIT.md)** - What tools exist, what they do, capabilities/limitations

### Database & Data Persistence
- **[SQLITE_INTEGRATION.md](./SQLITE_INTEGRATION.md)** - Database schema, tables, indexes
- **[DATABASE_OPTIMIZATIONS.md](./DATABASE_OPTIMIZATIONS.md)** - Query optimization, performance tuning, caching
- **[ARMAZENAMENTO_E_PERSISTENCIA.md](./ARMAZENAMENTO_E_PERSISTENCIA.md)** - Storage architecture, data flow

### Business Logic & Validations
- **[FISCAL_VALIDATIONS.md](./FISCAL_VALIDATIONS.md)** - **MOST IMPORTANT** - All validation rules, formulas, edge cases
- **[CLASSIFICATION.md](./CLASSIFICATION.md)** - ML-based classification, confidence scoring
- **[HIGH_IMPACT_VALIDATIONS_SUMMARY.md](./HIGH_IMPACT_VALIDATIONS_SUMMARY.md)** - Top 10 most important validations

### Document Processing
- **[CTE_MDFE_COMPLETE.md](./CTE_MDFE_COMPLETE.md)** - Transport document (CTe/MDFe) support, parsing, fields

### Reports & UI
- **[REPORTS.md](./REPORTS.md)** - Reporting system, available report types, data structures
- **[CHART_EXPORT.md](./CHART_EXPORT.md)** - Chart export feature, formats, cloud compatibility
- **[HISTORY_TAB.md](./HISTORY_TAB.md)** - Chat history persistence, session management
- **[UI_NON_BLOCKING_ARCHITECTURE.md](./UI_NON_BLOCKING_ARCHITECTURE.md)** - Non-blocking UI design, async handling

### Specialized Features
- **[TRANSPORT_FIELDS_EXTENSION.md](./TRANSPORT_FIELDS_EXTENSION.md)** - Transport-specific fields, CTe/MDFe enhancements
- **[EXPAND_NCM_TABLE_GUIDE.md](./EXPAND_NCM_TABLE_GUIDE.md)** - NCM table expansion, product codes
- **[CHAT_COMMAND_GUIDE.md](./CHAT_COMMAND_GUIDE.md)** - Chat commands, how to structure questions
- **[USER_QUESTIONS_GUIDE.md](./USER_QUESTIONS_GUIDE.md)** - Example questions, expected responses
- **[CLASSIFICATION_INTEGRATION.md](./CLASSIFICATION_INTEGRATION.md)** - Classification in the pipeline

### Fixes & Updates
- **[RECENT_FIXES.md](./RECENT_FIXES.md)** - Recent bug fixes, improvements, changes
- **[AGENT_SETUP.md](./AGENT_SETUP.md)** - Agent initialization, tool registration

## 🚀 Deployment (Setting Up Production)

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment, Streamlit Cloud setup

## 📊 Documentation Statistics

- **Total files**: 24 essential documents
- **Total lines**: ~8,500 lines of documentation
- **Organized into**: 5 key areas (Architecture, Database, Business Logic, Reports, Features)

## 🗺️ Code Areas to Documentation Mapping

| Code Area | Key Documentation |
|-----------|-------------------|
| `src/agent/` | AGENT_ARCHITECTURE_SUMMARY.md, AGENT_COMMUNICATION.md |
| `src/database/` | SQLITE_INTEGRATION.md, DATABASE_OPTIMIZATIONS.md |
| `src/services/` | REPORTS.md, FISCAL_VALIDATIONS.md |
| `src/tools/` | AGENT_CAPABILITY_AUDIT.md, CTE_MDFE_COMPLETE.md |
| `src/ui/` | REPORTS.md, CHART_EXPORT.md, HISTORY_TAB.md |
| `src/models/` | FISCAL_VALIDATIONS.md, CLASSIFICATION.md |

## 🎓 Learning Paths

### Path 1: I want to understand the agent (AI/LLM)
1. AGENT_ARCHITECTURE_SUMMARY.md
2. AGENT_COMMUNICATION.md
3. AGENT_CAPABILITY_AUDIT.md
4. CHAT_COMMAND_GUIDE.md

### Path 2: I want to understand business logic (Fiscal Validations)
1. FISCAL_VALIDATIONS.md
2. HIGH_IMPACT_VALIDATIONS_SUMMARY.md
3. CTE_MDFE_COMPLETE.md
4. CLASSIFICATION.md

### Path 3: I want to understand data storage
1. SQLITE_INTEGRATION.md
2. DATABASE_OPTIMIZATIONS.md
3. ARMAZENAMENTO_E_PERSISTENCIA.md
4. REPORTS.md

### Path 4: I want to add a new feature
1. AGENT_COMMUNICATION.md (understand tools)
2. AGENT_CAPABILITY_AUDIT.md (see existing tools)
3. AGENT_ARCHITECTURE_SUMMARY.md (understand flow)
4. Relevant domain doc (FISCAL_VALIDATIONS.md, REPORTS.md, etc)
5. Code the feature
6. Update RECENT_FIXES.md with change

### Path 5: I want to deploy to production
1. DEPLOYMENT.md
2. AGENT_SETUP.md
3. DATABASE_OPTIMIZATIONS.md (for performance)
4. Run through QUICKSTART.md locally first

## ❓ Common Questions

### "How does the agent understand user questions?"
→ Read **AGENT_COMMUNICATION.md** - explains ReAct pattern, parameter extraction

### "What validation rules exist?"
→ Read **FISCAL_VALIDATIONS.md** (complete reference) or **HIGH_IMPACT_VALIDATIONS_SUMMARY.md** (top 10)

### "How is data stored?"
→ Read **SQLITE_INTEGRATION.md** - schema, indexes, relationships

### "How do I add a new validation rule?"
→ Read **FISCAL_VALIDATIONS.md** then check `src/services/fiscal_validator.py`

### "How do reports work?"
→ Read **REPORTS.md** - available types, data sources, export formats

### "How do I deploy to production?"
→ Read **DEPLOYMENT.md** then **AGENT_SETUP.md**

### "What changed recently?"
→ Read **RECENT_FIXES.md** - recent improvements, bug fixes

### "How does classification work?"
→ Read **CLASSIFICATION.md** - ML model, confidence scoring, fallbacks

### "What about CTe/MDFe documents?"
→ Read **CTE_MDFE_COMPLETE.md** - fields, parsing, validation

## 📋 Document Metadata

Each core document includes:

- **Problem/Context**: Why this exists
- **Architecture/Design**: How it works
- **API Reference**: Functions, inputs, outputs
- **Examples**: Real-world usage
- **Testing**: How to verify
- **Performance**: Optimization notes
- **Related Docs**: Cross-references

## 🔄 Keeping Documentation Updated

When you make changes to the code:

1. Update the relevant documentation
2. Update **RECENT_FIXES.md** with your change
3. Update cross-references if needed
4. Keep examples current with actual code

## 📞 Documentation Maintenance

The documentation is organized to be:
- ✅ **Accurate** - Updated when code changes
- ✅ **Complete** - Covers all major features
- ✅ **Connected** - Cross-referenced throughout
- ✅ **Concise** - Removed redundant/outdated material
- ✅ **Useful** - Organized by learning goal

Last cleaned up: November 2, 2025
Removed: 24 redundant files (50% reduction)
Consolidated: FIX_*, CHART_EXPORT_*, CTE_MDFE_* files
