#!/usr/bin/env python3
"""Check elevation parsing output."""
import sys
sys.path.insert(0, '/home/workspace/OpenEvaluator')
from sheet_parser import parse_elevation_reference, RAW_ROW

erp_raw = RAW_ROW.get("Elevation reference point (ERP) and elevations (if known)", "")
print(f"Raw ERP text: {erp_raw[:120]}")
erp = parse_elevation_reference(erp_raw)
print(f"Parsed keys ({len(erp)}):")
for k, v in erp.items():
    print(f"  {k} = {repr(v)}")
