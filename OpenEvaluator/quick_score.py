#!/usr/bin/env python3
"""Quick scoring: count filled widgets in PDF."""
import fitz
from pathlib import Path

def count_widgets(pdf_path):
    """Count filled vs empty widgets in PDF."""
    doc = fitz.open(str(pdf_path))
    total = 0
    filled = 0
    empty = 0

    for page in doc:
        widgets = page.widgets()
        if not widgets:
            continue
        for w in widgets:
            total += 1
            val = w.field_value
            if val and str(val).strip() and str(val).strip() != 'Off':
                filled += 1
            else:
                empty += 1

    doc.close()
    return total, filled, empty

# Score both PDFs
print("=" * 80)
print("PHASE 1 SCORE COMPARISON")
print("=" * 80)

old_pdf = "HHE-200-filled.pdf"
new_pdf = "HHE-200-filled-phase1.pdf"

for pdf_file in [old_pdf, new_pdf]:
    if Path(pdf_file).exists():
        total, filled, empty = count_widgets(pdf_file)
        pct = filled / total * 100 if total > 0 else 0
        label = "BEFORE Phase 1" if pdf_file == old_pdf else "AFTER Phase 1"
        print(f"\n{label}:")
        print(f"  Total widgets: {total}")
        print(f"  Filled: {filled} ({pct:.1f}%)")
        print(f"  Empty: {empty}")

print("\n" + "=" * 80)
