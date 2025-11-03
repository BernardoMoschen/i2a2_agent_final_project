#!/usr/bin/env python3
"""Test script for year filtering in database tools."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.database.db import DatabaseManager
from datetime import datetime


def test_database_filtering():
    """Test database year/month filtering."""
    print("=" * 60)
    print("DATABASE YEAR/MONTH FILTERING TESTS")
    print("=" * 60)
    print()
    
    db = DatabaseManager("sqlite:///fiscal_documents.db")
    
    # Test 1: All documents
    print("📊 TEST 1: All documents (no filter)")
    stats = db.get_statistics()
    print(f"   Total: {stats['total_invoices']}")
    print(f"   By type: {stats['by_type']}")
    assert stats['total_invoices'] == 48, f"Expected 48, got {stats['total_invoices']}"
    print("   ✅ PASS")
    print()
    
    # Test 2: Year 2024
    print("📊 TEST 2: Documents from 2024")
    stats = db.get_statistics(year=2024)
    print(f"   Total: {stats['total_invoices']}")
    print(f"   By type: {stats['by_type']}")
    assert stats['total_invoices'] == 21, f"Expected 21, got {stats['total_invoices']}"
    assert stats['by_type'] == {'NFe': 21}, f"Expected {{'NFe': 21}}, got {stats['by_type']}"
    print("   ✅ PASS")
    print()
    
    # Test 3: Year 2025
    print("📊 TEST 3: Documents from 2025")
    stats = db.get_statistics(year=2025)
    print(f"   Total: {stats['total_invoices']}")
    print(f"   By type: {stats['by_type']}")
    assert stats['total_invoices'] == 26, f"Expected 26, got {stats['total_invoices']}"
    assert stats['by_type'] == {'NFe': 26}, f"Expected {{'NFe': 26}}, got {stats['by_type']}"
    print("   ✅ PASS")
    print()
    
    # Test 4: January 2024
    print("📊 TEST 4: Documents from January 2024")
    stats = db.get_statistics(year=2024, month=1)
    print(f"   Total: {stats['total_invoices']}")
    print(f"   By type: {stats['by_type']}")
    assert stats['total_invoices'] == 20, f"Expected 20, got {stats['total_invoices']}"
    print("   ✅ PASS")
    print()
    
    # Test 5: October 2024
    print("📊 TEST 5: Documents from October 2024")
    stats = db.get_statistics(year=2024, month=10)
    print(f"   Total: {stats['total_invoices']}")
    print(f"   By type: {stats['by_type']}")
    assert stats['total_invoices'] == 1, f"Expected 1, got {stats['total_invoices']}"
    print("   ✅ PASS")
    print()
    
    # Test 6: Search with year filter
    print("🔍 TEST 6: Search invoices from 2024")
    invoices = db.search_invoices(
        days_back=None,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2025, 1, 1),
        limit=100
    )
    print(f"   Found: {len(invoices)}")
    assert len(invoices) == 21, f"Expected 21, got {len(invoices)}"
    print("   ✅ PASS")
    print()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_database_filtering()
