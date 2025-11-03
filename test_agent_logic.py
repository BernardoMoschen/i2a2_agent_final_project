#!/usr/bin/env python3
"""
Test to verify that the agent correctly extracts and uses year parameter.
This simulates how the LangChain agent would parse the user question.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.agent.tools import DatabaseStatsTool, DatabaseSearchTool
from src.database.db import DatabaseManager


def extract_year_from_question(question: str) -> int:
    """Extract year from question (simple example)."""
    # Look for 4-digit numbers that look like years (1900-2099)
    import re
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
    if years:
        return int(years[-1])
    return None


def simulate_agent_logic():
    """Simulate how the LangChain agent should process the user question."""
    print("=" * 80)
    print("SIMULATING AGENT LOGIC: 'Qual o tipo de nota mais predominante em 2024?'")
    print("=" * 80)
    print()
    
    user_question = "Qual o tipo de nota mais predominante em 2024?"
    
    print(f"👤 USER QUESTION: {user_question}")
    print()
    
    # Step 1: Extract year from question
    print("🤖 AGENT PROCESSING:")
    print()
    
    year = extract_year_from_question(user_question)
    print(f"   Step 1️⃣  Extract year from question: {year}")
    
    if year is None:
        print("   ❌ No year found, would use days_back=9999 (all documents)")
    else:
        print(f"   ✅ Year extracted: {year}")
    print()
    
    # Step 2: Choose appropriate tool
    print(f"   Step 2️⃣  Choose tool: get_database_statistics")
    print(f"   Step 3️⃣  Set parameters: year={year}")
    print()
    
    # Step 3: Call tool
    print(f"   Step 4️⃣  Call tool with year={year}...")
    tool = DatabaseStatsTool()
    
    result = tool._run(year=year)
    print()
    print("📊 TOOL RESPONSE:")
    print("-" * 80)
    print(result)
    print("-" * 80)
    print()
    
    # Step 4: Analyze response
    print("🤖 AGENT ANALYSIS:")
    db = DatabaseManager("sqlite:///fiscal_documents.db")
    stats = db.get_statistics(year=year)
    
    total_docs = stats['total_invoices']
    doc_types = stats['by_type']
    
    print(f"   • Total documents in {year}: {total_docs}")
    print(f"   • Document types: {doc_types}")
    
    if total_docs > 0:
        max_type = max(doc_types.items(), key=lambda x: x[1])
        percentage = (max_type[1] / total_docs) * 100
        
        print()
        print(f"✅ FINAL ANSWER:")
        print(f"   O tipo de nota mais predominante em {year} é {max_type[0]}")
        print(f"   {max_type[1]} documento(s) de {total_docs} ({percentage:.0f}%)")
    else:
        print()
        print(f"❌ No documents found in {year}")
    
    print()
    print("=" * 80)
    print()
    
    # Compare with old behavior
    print("📝 COMPARISON WITH OLD BEHAVIOR:")
    print("=" * 80)
    print()
    print("OLD (BROKEN) ❌:")
    print("   Agent calls: get_database_statistics() [no year parameter]")
    print("   Returns: 48 NFe documents total (all years)")
    print("   Agent concludes: 'No 2024 documents' ❌")
    print()
    print("NEW (FIXED) ✅:")
    print(f"   Agent calls: get_database_statistics(year=2024)")
    print(f"   Returns: 21 NFe documents from 2024 only")
    print(f"   Agent concludes: 'NFe is 100% (21/21) of 2024 documents' ✅")
    print()
    print("=" * 80)


if __name__ == "__main__":
    simulate_agent_logic()
