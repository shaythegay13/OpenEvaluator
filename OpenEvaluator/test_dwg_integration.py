#!/usr/bin/env python3
"""
Test dwg_generator integration with field_adapter.
Generates DXF files from test form data.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from field_adapter import adapt_sheet_fields_to_acro
from dwg_generator import generate_all_pages


# Test data simulating a Google Sheet row
test_sheet_row = {
    "Client Name": "Kristen Marquis",
    "Email": "shay.bouchles@gmail.com",  # Row 2 - real client data
    "Property Street": "17 Aspen Way",
    "Property Town": "Turner",
    "Property Map #": "26",
    "Property Lot #": "18",
    "Property Acreage": "2.35",
    "Site Evaluator": "George Bouchles",
    "SE Phone": "207-240-5567",
    "SE Email": "gsb@cadmasterr.com",
    "SE #": "338",
    "SE Signature Date": "03/01/2026",
    "Application Type": "Replacement",
    "System Being Replaced": "Yes",
    "Water Supply": "Drilled Well",
    "Property Use": "Single Family Dwelling Unit",
    "# Bedrooms (opt 1)": "3",
    "Design Flow (GPD)": "270",
    "Disposal Field Type": "Proprietary Device",
    "Disposal Field Size": "11 x 28 ft",
    "Soil Classification (Hole 1)": "Fine Sandy Loam",
    "Limiting Factor / Depth": "24 inches (Ground Water)",
    "Scale PG3": "40",
    "Scale PG4": "40",
    "Finished Grade Elevation": "0\"",
    "Top Distribution Pipe Elevation": "-12\"",
    "Bottom of Disposal Field": "30\"",
}

print("\n" + "="*80)
print("DWG GENERATOR INTEGRATION TEST")
print("="*80)

# Step 1: Adapt sheet fields to form fields
print("\n[STEP 1] Adapting Google Sheet fields to form fields...")
form_data = adapt_sheet_fields_to_acro(test_sheet_row)
print(f"✓ Adapted {len(form_data)} form fields")

# Step 2: Generate DXF files
print("\n[STEP 2] Generating DXF files...")
results = generate_all_pages(form_data, drawing_data=None)

print("\n" + "="*80)
print("DXF GENERATION COMPLETE")
print("="*80)
print(f"\n✓ Generated {len(results)} DXF files:")
for page, path in results.items():
    file_size = Path(path).stat().st_size
    print(f"  {page}: {Path(path).name} ({file_size} bytes)")

# Verify files are valid DXF
print("\n[STEP 3] Verifying DXF format...")
for page, path in results.items():
    with open(path) as f:
        first_line = f.readline().strip()
        second_line = f.readline().strip()
        if first_line == "0" and second_line == "SECTION":
            print(f"  ✓ {page}: Valid DXF format")
        else:
            print(f"  ✗ {page}: Invalid DXF format")

print("\n" + "="*80)
