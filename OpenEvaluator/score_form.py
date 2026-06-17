#!/usr/bin/env python3
"""Accurate form field score with pikepdf 10.6.0."""
import pikepdf

EXCLUDED_PATTERNS = [
    "Installer", "Date (Property Owner", "Date for First LPI",
    "Date for Second LPI", "Issuing Municipality", "Permit #",
    "Permit Issued", "LPI Signature", "Fee Calculation", "Total Fee",
    "Town Share", "State 25%", "DEP WQS", "Revision Check",
    "Doubled Fee Check", "Variance Check", "Owner/ Applicant Signature"
]

pdf = pikepdf.open('/home/workspace/OpenEvaluator/HHE-200-filled.pdf')
fields_list = pdf.Root['/AcroForm']['/Fields']

filled = 0
total = 0
excluded_total = 0
excluded_filled = 0

for f_obj in fields_list:
    name = str(f_obj.get('/T', b'')).strip()
    
    # Check if excluded
    excluded = any(p in name for p in EXCLUDED_PATTERNS)
    
    # Check for value in pikepdf 10.6.0
    has_val = False
    if '/V' in f_obj:
        val = f_obj['/V']
        val_str = str(val).strip()
        if val_str and val_str.lower() not in ('', '/off'):
            has_val = True
    
    if excluded:
        excluded_total += 1
        if has_val:
            excluded_filled += 1
    else:
        total += 1
        if has_val:
            filled += 1

print(f"Scorable fields: {total}")
print(f"Scorable filled: {filled}")
print(f"Excluded fields: {excluded_total} (filled: {excluded_filled})")
print(f"Score: {filled}/{total} = {filled*100//total}%")
