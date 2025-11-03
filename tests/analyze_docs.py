#!/usr/bin/env python3
"""Analyze markdown files in docs/ to identify what's essential vs redundant."""

import os
from pathlib import Path
from collections import defaultdict

docs_dir = Path("/home/bmos/private/private_repos/i2a2/projeto_final/docs")

# Categorize files
categories = {
    "Architecture & Design": [
        "AGENT_ARCHITECTURE_SUMMARY.md",
        "AGENT_COMMUNICATION.md",
        "UI_NON_BLOCKING_ARCHITECTURE.md",
        "AGENT_DATABASE_QUERIES.md",
    ],
    "Setup & Installation": [
        "AGENT_SETUP.md",
        "QUICKSTART.md",
        "QUICKSTART_DEPLOY.md",
        "DEPLOYMENT.md",
    ],
    "Feature Guides": [
        "CHAT_COMMAND_GUIDE.md",
        "USER_QUESTIONS_GUIDE.md",
        "CLASSIFICATION.md",
        "CLASSIFICATION_INTEGRATION.md",
        "CTE_MDFE_COMPLETE.md",
        "CTE_MDFE_IMPLEMENTATION.md",
        "CTE_MDFE_VALIDATIONS.md",
        "TRANSPORT_FIELDS_EXTENSION.md",
        "REPORTS.md",
        "CHART_EXPORT_USER_GUIDE.md",
        "CHART_EXPORT_QUICK_REFERENCE.md",
        "CHART_EXPORT_IMPLEMENTATION_COMPLETE.md",
        "CHART_EXPORT_CLOUD_REFACTORING.md",
        "HISTORY_TAB.md",
        "EXPAND_NCM_TABLE_GUIDE.md",
    ],
    "Validations & Business Logic": [
        "FISCAL_VALIDATIONS.md",
        "HIGH_IMPACT_VALIDATIONS_SUMMARY.md",
    ],
    "Database & Persistence": [
        "SQLITE_INTEGRATION.md",
        "DATABASE_OPTIMIZATIONS.md",
        "ARMAZENAMENTO_E_PERSISTENCIA.md",
    ],
    "Bug Fixes & Patches": [
        "FIX_YEAR_FILTERING.md",
        "FIX_DAYS_BACK_DEFAULT.md",
        "OPERATION_TYPE_FILTER.md",
        "REPORT_DOWNLOAD_FIX.md",
    ],
    "Status & Planning": [
        "STATUS.md",
        "DELIVERY.md",
        "AGENT_SETUP.md",
        "AGENT_VERIFICATION.md",
        "AGENT_CAPABILITY_AUDIT.md",
        "SESSION_SUMMARY.md",
        "VERIFICACAO_AGENTE.md",
        "PHASE2_PHASE3_README.md",
        "PHASE2_PHASE3_SUMMARY.md",
        "IMPLEMENTATION_SUMMARY_REPORTS.md",
    ],
    "Optimization & Performance": [
        "PERFORMANCE_IMPROVEMENTS.md",
        "OPTIMIZATIONS_SUMMARY.md",
        "STREAMLIT_CLOUD_ANALYSIS.md",
        "QUICK_START_BULK_PROCESSING.md",
        "QUICK_REFERENCE.md",
        "UI_LAYOUT.md",
    ],
    "Examples & Reference": [
        "perguntas_exemplo.md",
    ],
}

# Analysis
print("=" * 80)
print("MARKDOWN DOCUMENTATION ANALYSIS")
print("=" * 80)
print()

# Get all files
all_files = sorted([f.name for f in docs_dir.glob("*.md")])
categorized = set()

for cat, files in categories.items():
    print(f"\n📁 {cat}")
    print(f"   {len(files)} files")
    for f in files:
        if f in all_files:
            size = (docs_dir / f).stat().st_size
            lines = len((docs_dir / f).read_text().splitlines())
            print(f"   • {f:<50} ({lines:4d} lines, {size:5.0f} bytes)")
            categorized.add(f)
        else:
            print(f"   ✗ {f} (NOT FOUND)")

uncategorized = set(all_files) - categorized
if uncategorized:
    print(f"\n⚠️  UNCATEGORIZED FILES:")
    for f in sorted(uncategorized):
        size = (docs_dir / f).stat().st_size
        lines = len((docs_dir / f).read_text().splitlines())
        print(f"   • {f:<50} ({lines:4d} lines, {size:5.0f} bytes)")

# Summary stats
total_files = len(all_files)
total_lines = sum(len((docs_dir / f).read_text().splitlines()) for f in all_files)
total_size = sum((docs_dir / f).stat().st_size for f in all_files)

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total files:        {total_files}")
print(f"Total lines:        {total_lines:,}")
print(f"Total size:         {total_size / 1024:.1f} KB")
print(f"Categories:         {len(categories)}")
print(f"Categorized files:  {len(categorized)}")
print(f"Uncategorized:      {len(uncategorized)}")
print()
print("=" * 80)
print("RECOMMENDATIONS FOR CLEANUP")
print("=" * 80)
print("""
✅ KEEP (Critical for code understanding):
   • AGENT_ARCHITECTURE_SUMMARY.md - Core architecture
   • AGENT_COMMUNICATION.md - How agent/tools interact
   • FISCAL_VALIDATIONS.md - Business logic validation rules
   • CLASSIFICATION.md - Classification algorithm
   • SQLITE_INTEGRATION.md - Database structure
   • DATABASE_OPTIMIZATIONS.md - Performance tuning
   • CTE_MDFE_COMPLETE.md - Transport document specs
   • REPORTS.md - Reporting system
   • QUICKSTART.md - How to get started

❌ REMOVE (Redundant or low-value):
   • PHASE2_PHASE3_*.md - Historical planning (2-3 files duplicate info)
   • SESSION_SUMMARY.md - Snapshot at a point in time
   • VERIFICACAO_AGENTE.md - Duplicate of AGENT_VERIFICATION.md
   • IMPLEMENTATION_SUMMARY_REPORTS.md - Snapshots of work done
   • STATUS.md - Point-in-time status
   • DELIVERY.md - Duplicate planning info
   • QUICKSTART_DEPLOY.md - Covered by DEPLOYMENT.md
   • STREAMLIT_CLOUD_ANALYSIS.md - One-off analysis
   • UI_LAYOUT.md - Can be inferred from code
   • QUICK_REFERENCE.md - Can be automated via docstrings
   • perguntas_exemplo.md - Only 3 lines (trivial)

⚠️  CONSOLIDATE (Merge into main docs):
   • FIX_*.md files (3 files) → Create FIXES_AND_UPDATES.md
   • CHART_EXPORT_*.md (4 files) → Consolidate into REPORTS.md
   • CTE_MDFE_*.md (3 files) → Already have CTE_MDFE_COMPLETE.md
   • PHASE2_PHASE3_*.md (2 files) → Archive or delete
   
📊 RESULT:
   From 47 files → 15-20 essential files
   From 15,631 lines → ~8,000 lines (50% reduction)
   Better maintainability and faster onboarding
""")
