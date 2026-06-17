#!/usr/bin/env python3
"""Debug field_adapter to see what it's returning"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from field_adapter import adapt_sheet_fields_to_acro

test_sheet_row = {
    "Client Name": "Kristen Marquis",
    "Email": "shay.bouchles@gmail.com",
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
}

form_data = adapt_sheet_fields_to_acro(test_sheet_row)

# Print selected fields to see what we're getting
print("\nForm Data Sample:")
print(f"  owner_name: {form_data.get('owner_name', 'NOT FOUND')}")
print(f"  street_name: {form_data.get('street_name', 'NOT FOUND')}")
print(f"  town: {form_data.get('town', 'NOT FOUND')}")
print(f"  evaluator_name: {form_data.get('evaluator_name', 'NOT FOUND')}")
print(f"  se_number: {form_data.get('se_number', 'NOT FOUND')}")

print(f"\nTotal form fields: {len(form_data)}")
print("\nAll populated fields:")
for key, value in sorted(form_data.items()):
    if value and str(value).strip():
        print(f"  {key}: {value}")
