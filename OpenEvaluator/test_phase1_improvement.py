#!/usr/bin/env python3
"""Test Phase 1 improvements: checkbox logic + field mapping."""
import sys
sys.path.insert(0, '/home/workspace/OpenEvaluator')

from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import fill_acro

# Parse form data
fields = parse_sheet_row(RAW_ROW)
adapted = adapt_sheet_fields_to_acro(fields)

# Count filled vs empty
filled = sum(1 for v in adapted.values() if v and isinstance(v, str) and v.strip())
empty = sum(1 for v in adapted.values() if not v or (isinstance(v, str) and not v.strip()))

print("=" * 80)
print("PHASE 1: FIELD ADAPTER IMPROVEMENT TEST")
print("=" * 80)

print(f"\nAdapted fields summary:")
print(f"  Total keys: {len(adapted)}")
print(f"  Filled: {filled}")
print(f"  Empty: {empty}")
print(f"  Fill rate: {filled / (filled + empty) * 100:.1f}%")

# Show checkbox fields set
print(f"\nCheckbox fields set:")
checkbox_keys = [k for k in adapted.keys() if 'check' in k or 'checkbox' in k]
for key in checkbox_keys:
    if adapted[key]:
        print(f"  ✓ {key} = {adapted[key]}")

# Show system-derived fields
print(f"\nSystem-derived fields:")
for key in ['disposal_field_type', 'proprietary_device_opt', 'non_eng_field_check', 'tank_regular_check']:
    val = adapted.get(key, '')
    print(f"  {key}: {val}")

# Now fill the PDF
print(f"\nGenerating PDF with adapted fields...")
try:
    pdf_path = fill_acro(adapted, "HHE-200-filled-phase1.pdf")
    print(f"✓ PDF generated: {pdf_path}")
except Exception as e:
    print(f"✗ PDF generation error: {e}")

print("\n" + "=" * 80)
