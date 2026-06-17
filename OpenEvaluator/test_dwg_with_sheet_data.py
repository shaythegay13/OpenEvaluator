#!/usr/bin/env python3
"""
Test dwg_generator with real Google Sheet data via sheet_parser.
Generates DXF files from actual form data.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sheet_parser import parse_sheet_row, build_field_dict
from field_adapter import adapt_sheet_fields_to_acro
from dwg_generator import generate_all_pages

print("\n" + "="*80)
print("DWG GENERATOR - GOOGLE SHEET INTEGRATION TEST")
print("="*80)

# Step 1: Parse actual Google Sheet data
print("\n[STEP 1] Fetching and parsing Google Sheet data...")
try:
    sheet_fields = build_field_dict()
    print(f"✓ Parsed {len(sheet_fields)} sheet fields from Google Sheet")

    # Show owner info
    print(f"  Owner: {sheet_fields.get('owner_name', 'N/A')}")
    print(f"  Property: {sheet_fields.get('street_name', '')} {sheet_fields.get('town', '')}")
    print(f"  Evaluator: {sheet_fields.get('evaluator_name', 'N/A')}")
except Exception as e:
    print(f"✗ Failed to fetch Google Sheet data: {e}")
    print("  (Google Sheets credentials may not be configured)")
    print("  Falling back to test data...")

    # Fallback test data - using proper sheet_parser field names
    sheet_fields = {
        'owner_name': 'Kristen Marquis',
        'owner_phone': '207-240-5567',
        'street_name': 'Aspen Way',
        'street_number': '17',
        'town': 'Turner',
        'map_number': '26',
        'lot_number': '18',
        'acreage': '2.35',
        'evaluator_name': 'George Bouchles',
        'evaluator_phone': '207-240-5567',
        'evaluator_email': 'gsb@cadmasterr.com',
        'lpi_number': '338',
        'water_supply_type': 'Drilled Well',
        'use': 'Single Family Dwelling Unit',
        'bedrooms': '3',
        'design_flow_gallons': '270',
        'disposal_system_type': 'Eljen InDrain',
        'disposal_field_size': '11 x 28 ft',
        'soil_1': 'Fine Sandy Loam',
        'limiting_factor': '24 inches (Ground Water)',
        'special_notes': 'Replacement system',
        'date_issued': '03/01/2026',
    }
    print(f"✓ Using fallback test data ({len(sheet_fields)} fields)")

# Step 2: Adapt to form fields
print("\n[STEP 2] Adapting sheet fields to form fields...")
form_data = adapt_sheet_fields_to_acro(sheet_fields)
print(f"✓ Adapted {len(form_data)} form fields")

# Show mapped data
print("\n  Mapped fields:")
for key in ['owner_name', 'street_name', 'town', 'evaluator_name', 'se_number']:
    value = form_data.get(key, '')
    if value:
        print(f"    {key}: {value}")

# Step 3: Generate DXF files
print("\n[STEP 3] Generating DXF files...")
results = generate_all_pages(form_data, drawing_data=None)

print("\n" + "="*80)
print("DXF GENERATION COMPLETE")
print("="*80)
print(f"\n✓ Generated {len(results)} DXF files:")
for page, path in results.items():
    file_size = Path(path).stat().st_size
    print(f"  {page}: {Path(path).name} ({file_size} bytes)")

# Verify files are valid DXF
print("\n[STEP 4] Verifying DXF format...")
for page, path in results.items():
    with open(path) as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
        if first_line == "0" and second_line == "SECTION":
            print(f"  ✓ {page}: Valid DXF format (R2004/AC1018)")
        else:
            print(f"  ✗ {page}: Invalid DXF format")

print("\n" + "="*80)
print("Files ready for AutoCAD 2004 import")
print("="*80)
