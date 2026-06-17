#!/usr/bin/env python3
"""Analyze field mapping gaps between sheet_parser output and acro_fill WIDGET_MAP."""

import json
from pathlib import Path

# Load sheet data
with open("sheet_row_data.json") as f:
    sheet_fields = json.load(f)

# Import acro_fill WIDGET_MAP
from acro_fill import WIDGET_MAP

sheet_keys = set(sheet_fields.keys())
acro_keys = set(WIDGET_MAP.keys())

print("=" * 80)
print("FIELD MAPPING ANALYSIS")
print("=" * 80)

print(f"\nsheet_parser returns {len(sheet_keys)} field keys")
print(f"acro_fill expects {len(acro_keys)} field keys")

# Fields sheet returns but acro doesn't use
orphaned = sheet_keys - acro_keys
if orphaned:
    print(f"\n✗ Fields from sheet_parser NOT used by acro_fill ({len(orphaned)}):")
    for key in sorted(list(orphaned)[:20]):
        print(f"    {key}")
    if len(orphaned) > 20:
        print(f"    ... and {len(orphaned) - 20} more")

# Fields acro needs but sheet doesn't provide
missing = acro_keys - sheet_keys
if missing:
    print(f"\n✓ Fields needed by acro_fill but NOT in sheet_parser ({len(missing)}):")
    for key in sorted(list(missing)[:20]):
        print(f"    {key}")
    if len(missing) > 20:
        print(f"    ... and {len(missing) - 20} more")

# Fields that match
common = sheet_keys & acro_keys
print(f"\n✓ Fields in both ({len(common)}):")
for key in sorted(list(common)[:15]):
    print(f"    {key}")
if len(common) > 15:
    print(f"    ... and {len(common) - 15} more")

print("\n" + "=" * 80)
print("TOP MISSING FIELDS THAT SHOULD BE FILLED")
print("=" * 80)

# Try to find natural mappings
potential_mappings = {
    "site_address": ["street_number", "street_name"],  # combine with town
    "town": ["town"],
    "design_flow_gallons": ["design_flow"],
    "water_supply_type": ["water_supply"],
}

for sheet_key, acro_key_list in potential_mappings.items():
    if sheet_key in sheet_fields:
        for acro_key in acro_key_list:
            if acro_key in acro_keys and acro_key not in sheet_fields:
                print(f"  Potential mapping: {sheet_key} → {acro_key}")

