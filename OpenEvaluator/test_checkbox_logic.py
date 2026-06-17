#!/usr/bin/env python3
"""Test checkbox logic for row 2."""
import sys
sys.path.insert(0, '/home/workspace/OpenEvaluator')

from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro

# Parse and adapt row 2
fields = parse_sheet_row(RAW_ROW)
adapted = adapt_sheet_fields_to_acro(fields)

print("=" * 80)
print("CHECKBOX LOGIC TEST")
print("=" * 80)

disposal_system = fields.get('disposal_system_type', '')
tank_type = fields.get('tank_type', '')

print(f"\nInput data:")
print(f"  disposal_system_type: {disposal_system}")
print(f"  tank_type: {tank_type}")

checkbox_fields = [
    'non_eng_field_check', 'eng_field_check',
    'tank_regular_check', 'tank_low_profile_check', 'tank_h20_check',
    'holding_tank_check', 'ces_check', 'cnes_check',
    'primitive_limited_check', 'alt_toilet_check',
    'proprietary_device_opt'
]

print(f"\nCheckbox status in adapted dict:")
for field in checkbox_fields:
    val = adapted.get(field, '<NOT SET>')
    status = "✓ SET" if val else "○ UNSET"
    print(f"  {status}  {field:30} = {repr(val)[:40]}")

print("\n" + "=" * 80)
