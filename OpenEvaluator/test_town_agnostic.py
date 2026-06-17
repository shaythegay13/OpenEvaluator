#!/usr/bin/env python3
"""
Test Phase 5.1: Town-Agnostic Database Expansion

Tests:
1. Town extraction from various location formats
2. Multi-town property database support
3. O'Donnell CAMA URL construction for different towns
"""

import logging
from pathlib import Path
from property_enrichment_engine import PropertyEnrichmentEngine, PropertyDatabase
from property_database_manager import PropertyDatabaseManager
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_town_extraction():
    """Test _extract_town_from_location with various formats"""
    print("\n" + "=" * 60)
    print("TEST 1: Town Extraction from Location Strings")
    print("=" * 60)

    engine = PropertyEnrichmentEngine()
    test_cases = [
        # (location_string, expected_town)
        ("17 Aspen Way, Turner, Maine 04282", "Turner"),
        ("123 Main Street, Portland, ME 04101", "Portland"),
        ("456 Oak Road, Auburn, Maine", "Auburn"),
        ("789 Pine Ave, Lewiston, ME 04240", "Lewiston"),
        ("100 Elm St, Bangor, Maine 04401", "Bangor"),
        ("200 Maple Lane, Rockland, Maine", "Rockland"),
        ("300 Birch Dr, Bath, ME 04530", "Bath"),
        ("400 Cedar Ct, Westbrook, Maine", "Westbrook"),
    ]

    passed = 0
    failed = 0

    for location, expected in test_cases:
        result = engine._extract_town_from_location(location)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status}: '{location}'")
        print(f"         Expected: {expected}, Got: {result}")

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_multi_town_database():
    """Test PropertyDatabaseManager with multiple towns"""
    print("\n" + "=" * 60)
    print("TEST 2: Multi-Town Property Database")
    print("=" * 60)

    # Create a fresh test database
    test_db_file = Path("/tmp/test_properties.json")
    if test_db_file.exists():
        test_db_file.unlink()

    manager = PropertyDatabaseManager(test_db_file)

    # Add properties from different towns
    test_properties = [
        {
            "town": "Turner",
            "map": "26",
            "lot": "18",
            "address": "17 Aspen Way",
            "owner": "George Bouchles",
            "acreage": 2.35,
            "road_name": "Aspen Way",
            "road_type": "Private",
            "confidence": "high",
        },
        {
            "town": "Auburn",
            "map": "15",
            "lot": "42",
            "address": "200 Court Street",
            "owner": "John Smith",
            "acreage": 1.5,
            "road_name": "Court Street",
            "road_type": "Public",
            "confidence": "high",
        },
        {
            "town": "Portland",
            "map": "88",
            "lot": "3",
            "address": "500 Commercial Ave",
            "owner": "Jane Doe",
            "acreage": 0.75,
            "road_name": "Commercial Avenue",
            "road_type": "Public",
            "confidence": "medium",
        },
        {
            "town": "Lewiston",
            "map": "45",
            "lot": "67",
            "address": "150 Park Avenue",
            "owner": "Bob Johnson",
            "acreage": 3.2,
            "road_name": "Park Avenue",
            "road_type": "Public",
            "confidence": "high",
        },
    ]

    # Add properties
    print("\nAdding properties to database...")
    for prop in test_properties:
        prop_data = {k: v for k, v in prop.items() if k not in ["town", "map", "lot"]}
        prop_data["research_date"] = datetime.now().isoformat()
        prop_data["sources"] = ["Test import"]
        manager.add_property(prop["town"], prop["map"], prop["lot"], prop_data)

    # Verify all towns are in database
    towns = manager.list_towns()
    print(f"\nTowns in database: {towns}")

    expected_towns = ["Auburn", "Lewiston", "Portland", "Turner"]
    if towns == expected_towns:
        print("✓ PASS: All expected towns present")
    else:
        print(f"✗ FAIL: Expected {expected_towns}, got {towns}")
        return False

    # Test lookups
    print("\nTesting property lookups...")
    tests_passed = 0
    tests_total = 0

    for prop in test_properties:
        tests_total += 1
        result = manager.get_property(prop["town"], prop["map"], prop["lot"])
        if result and result.get("owner") == prop["owner"]:
            print(f"✓ PASS: Found {prop['town']} Map {prop['map']} Lot {prop['lot']}")
            tests_passed += 1
        else:
            print(f"✗ FAIL: Could not find {prop['town']} Map {prop['map']} Lot {prop['lot']}")

    # Test count
    print(f"\nDatabase Summary:")
    for town in towns:
        count = manager.count_properties(town)
        print(f"  {town}: {count} properties")

    print(f"\nLookup results: {tests_passed}/{tests_total} passed")

    # Cleanup
    if test_db_file.exists():
        test_db_file.unlink()

    return tests_passed == tests_total


def test_enrichment_with_multiple_towns():
    """Test PropertyEnrichmentEngine with different towns"""
    print("\n" + "=" * 60)
    print("TEST 3: Enrichment Engine with Multiple Towns")
    print("=" * 60)

    # Create test database with multiple towns
    test_db_file = Path("/tmp/test_enrichment.json")
    if test_db_file.exists():
        test_db_file.unlink()

    manager = PropertyDatabaseManager(test_db_file)

    # Add test properties
    test_cases = [
        {
            "town": "Turner",
            "form_data": {
                "Map and Lot # and Acreage": "26, 18, 2.35",
                "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
            },
            "expected_town": "Turner",
        },
        {
            "town": "Auburn",
            "form_data": {
                "Map and Lot # and Acreage": "15, 42, 1.5",
                "Property Location Details": "200 Court Street, Auburn, Maine 04210",
            },
            "expected_town": "Auburn",
        },
        {
            "town": "Portland",
            "form_data": {
                "Map and Lot # and Acreage": "88, 3, 0.75",
                "Property Location Details": "500 Commercial Ave, Portland, ME 04101",
            },
            "expected_town": "Portland",
        },
    ]

    # Add properties to database
    print("Setting up test properties...")
    for case in test_cases:
        prop_data = {
            "address": case["form_data"]["Property Location Details"],
            "owner": "Test Owner",
            "acreage": 2.0,
            "road_name": "Test Road",
            "confidence": "high",
            "sources": ["Test"],
            "research_date": datetime.now().isoformat(),
        }
        form_map, form_lot, _ = case["form_data"]["Map and Lot # and Acreage"].split(",")
        manager.add_property(case["town"], form_map.strip(), form_lot.strip(), prop_data)

    # Now test enrichment
    PropertyDatabase._manager = manager  # Use our test manager
    engine = PropertyEnrichmentEngine()

    print("\nTesting enrichment with different towns...")
    passed = 0
    failed = 0

    for case in test_cases:
        result = engine.enrich_property(case["form_data"])
        if result.get("status") == "found" and result.get("town") == case["expected_town"]:
            print(f"✓ PASS: {case['expected_town']} property enriched correctly")
            passed += 1
        else:
            print(f"✗ FAIL: {case['expected_town']} enrichment failed")
            print(f"        Result: {result}")
            failed += 1

    print(f"\nEnrichment results: {passed} passed, {failed} failed")

    # Cleanup
    if test_db_file.exists():
        test_db_file.unlink()

    return failed == 0


def test_cama_url_construction():
    """Test O'Donnell CAMA URL construction for different towns"""
    print("\n" + "=" * 60)
    print("TEST 4: O'Donnell CAMA URL Construction")
    print("=" * 60)

    from odonnell_cama_scraper import ODonnellCAMA

    test_towns = ["Turner", "Auburn", "Portland", "Lewiston", "Bangor"]

    print("Testing CAMA URL construction for different towns...\n")
    all_pass = True

    for town in test_towns:
        cama = ODonnellCAMA(town)
        expected_url = f"https://jeodonnell.com/cama/{town.lower()}/"
        if cama.base_url == expected_url:
            print(f"✓ PASS: {town:12s} -> {cama.base_url}")
        else:
            print(f"✗ FAIL: {town:12s}")
            print(f"         Expected: {expected_url}")
            print(f"         Got:      {cama.base_url}")
            all_pass = False

    return all_pass


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PHASE 5.1: TOWN-AGNOSTIC DATABASE EXPANSION")
    print("Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Town Extraction", test_town_extraction()))
    results.append(("Multi-Town Database", test_multi_town_database()))
    results.append(("Enrichment with Multiple Towns", test_enrichment_with_multiple_towns()))
    results.append(("CAMA URL Construction", test_cama_url_construction()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed}/{total} test groups passed")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
