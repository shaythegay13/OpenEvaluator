#!/usr/bin/env python3
"""Phase 3: Drawing quality improvements for Pages 3-4.
Adds: dimension lines, callout labels, property boundaries, soil profile grid."""
import json, os, sys, re
sys.path.insert(0, '.')
from sheet_parser import parse_sheet_row, RAW_ROW
from site_plan_generator import generate_all, _fig, _draw_grid, _rect, _line, _txt

fields = parse_sheet_row(RAW_ROW)

def _parse_ft(val, default=0):
    if not val: return default
    m = re.search(r"(\d+\.?\d*)", str(val))
    return float(m.group(1)) if m else default

drawing_data = {
    "owner_name":    fields.get("owner_name", "").upper(),
    "address_line":  f"{fields.get('site_address','')}, {fields.get('town','')}, ME {fields.get('mailing_zip','')}",
    "road_name":     fields.get("site_address", ""),
    "town":          fields.get("town", ""),
    "tax_map":       fields.get("map_number", ""),
    "lot_number":    fields.get("lot_number", ""),
    "acreage":       float(fields.get("acreage", 1)),
    "tank_cap":      "1000",
    "se_number":     "338",
    "se_date":       "03/01/2026",
    "evaluator_name": fields.get("evaluator_name", "").upper(),
    "num_rows":      int(fields.get("num_rows", 3)),
    "mods_per_row":  int(fields.get("mods_per_row", 7)),
    "cluster_w":     float(fields.get("cluster_width_ft", 11)),
    "cluster_l":     float(fields.get("cluster_length_ft", 28)),
    "brand":         fields.get("brand", "Eljen"),
    "field_to_well":  _parse_ft(fields.get("setback_well", 100), 100),
    "field_to_house": _parse_ft(fields.get("setback_field_to_house", 40), 40),
    "tank_to_house":  _parse_ft(fields.get("setback_tank_to_house", 8), 8),
    "erp_height_above_grade": 12,
    "scale_pg3": 80,
    "se_date": "03/01/2026",
}

# Generate improved drawings
print("Generating Phase 3 drawings from form data...")
results = generate_all(drawing_data)
print("\nDone! Generated:")
for key, path in results.items():
    print(f"  {key}: {path}")
