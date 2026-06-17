#!/usr/bin/env python3
"""Debug why owner_name isn't being mapped"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sheet_parser import build_field_dict
from field_adapter import adapt_sheet_fields_to_acro

sheet_fields = build_field_dict()

print("Sheet fields:")
print(f"  owner_name: {sheet_fields.get('owner_name', 'NOT FOUND')}")
print(f"  street_name: {sheet_fields.get('street_name', 'NOT FOUND')}")
print(f"  town: {sheet_fields.get('town', 'NOT FOUND')}")
print(f"  evaluator_name: {sheet_fields.get('evaluator_name', 'NOT FOUND')}")
print(f"  lpi_number: {sheet_fields.get('lpi_number', 'NOT FOUND')}")
print(f"  se_number: {sheet_fields.get('se_number', 'NOT FOUND')}")

print("\nAvailable keys in sheet_fields:")
for key in sorted(sheet_fields.keys()):
    if sheet_fields[key]:  # only non-empty
        print(f"  {key}: {sheet_fields[key]}")

form_data = adapt_sheet_fields_to_acro(sheet_fields)

print("\nForm data (after adaptation):")
print(f"  owner_name: '{form_data.get('owner_name', '')}'")
print(f"  street_name: '{form_data.get('street_name', '')}'")
print(f"  town: '{form_data.get('town', '')}'")
print(f"  evaluator_name: '{form_data.get('evaluator_name', '')}'")
print(f"  se_number: '{form_data.get('se_number', '')}'")

print("\nAll populated form fields:")
for key, val in sorted(form_data.items()):
    if val and str(val).strip():
        print(f"  {key}: {val}")
