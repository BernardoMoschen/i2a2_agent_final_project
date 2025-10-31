#!/usr/bin/env python3
"""Test the exact user question scenario."""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.agent.tools import GetStatisticsInput, DatabaseStatsTool
from src.database.db import DatabaseManager


def test_user_scenario():
    """Test the exact user question: Qual o tipo de nota mais predominante em 2024?"""
    print("=" * 70)
    print("TESTING USER SCENARIO: 'Qual o tipo de nota mais predominante em 2024?'")
    print("=" * 70)
    print()
    
    # Create the tool
    tool = DatabaseStatsTool()
    
    print("📊 Calling tool with year=2024...")
    result = tool._run(year=2024)
    print()
    print("Tool response:")
    print(result)
    print()
    
    # Parse the response to show structured data
    if "total_invoices" in result:
        # Try to extract stats from the response
        db = DatabaseManager("sqlite:///fiscal_documents.db")
        stats = db.get_statistics(year=2024)
        
        print("=" * 70)
        print("ANALYSIS:")
        print("=" * 70)
        print(f"📊 Total documents in 2024: {stats['total_invoices']}")
        print(f"📊 By type: {stats['by_type']}")
        
        # Determine predominant type
        if stats['total_invoices'] > 0:
            max_type = max(stats['by_type'].items(), key=lambda x: x[1])
            percentage = (max_type[1] / stats['total_invoices']) * 100
            print()
            print(f"🎯 ANSWER: The predominant type in 2024 is: {max_type[0]}")
            print(f"   {max_type[1]} out of {stats['total_invoices']} documents ({percentage:.0f}%)")
        else:
            print()
            print("❌ No documents found in 2024")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    test_user_scenario()
