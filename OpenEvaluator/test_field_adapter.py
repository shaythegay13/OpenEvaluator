#!/usr/bin/env python3
"""Full end-to-end test: parse form data, generate drawings from it, fill form."""
import json, os, sys
sys.path.insert(0, '.')
from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import fill_acro
from site_plan_generator import generate_all
import re

# Parse distances (values may include units like "8'" or "100 ft")
def _parse_ft(val, default):
    if not val:
        return default
    m = re.search(r"(\d+\.?\d*)", str(val))
    return float(m.group(1)) if m else default

# 1. Get GPS from Maps
maps_key = os.environ.get("GOOGLE_MAPS_API_KEY")
import googlemaps
client = googlemaps.Client(key=maps_key)
geo = client.geocode("17 Aspen Way, Turner, Maine 04282")
loc = geo[0]["geometry"]["location"] if geo else {}
lat = str(loc.get("lat", ""))
lng = str(loc.get("lng", ""))

# 2. Parse form fields
fields = parse_sheet_row(RAW_ROW)
fields["gps_latitude"] = lat
fields["gps_longitude"] = lng

# 3. Build drawing data dict from parsed form data
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
    # Field layout from form data (not hardcoded)
    "num_rows":      int(fields.get("num_rows", 3)),
    "mods_per_row":  int(fields.get("mods_per_row", 7)),
    "cluster_w":     float(fields.get("cluster_width_ft", 11)),
    "cluster_l":     float(fields.get("cluster_length_ft", 28)),
    "brand":         fields.get("brand", "Eljen"),
    # Distances
    "field_to_well":  _parse_ft(fields.get("setback_well", 100), 100),
    "field_to_house": _parse_ft(fields.get("setback_field_to_house", 40), 40),
    "tank_to_house":  _parse_ft(fields.get("setback_tank_to_house", 8), 8),
    # Elevations
    "finished_grade_in":   0,
    "top_pipe_in":        -12,
    "bottom_field_in":     -30,
    "limiting_factor":     24,
    "scale_pg3":           80,
}

print("=== Drawing data ===")
for k, v in drawing_data.items():
    print(f"  {k} = {repr(v)}")

# 4. Generate drawings from form data
print("\n=== Generating drawings from form data ===")
drawings = generate_all(drawing_data)

# 5. Adapt fields and fill form
adapted = adapt_sheet_fields_to_acro(fields)
print(f"\nAdapted fields: {len(adapted)}")

result = fill_acro(adapted, "HHE-200-filled.pdf")
print(f"\nResult: {result}")

# 6. Score
import pikepdf
pdf = pikepdf.open(result)
fields_list = pdf.Root['/AcroForm']['/Fields']
filled = sum(1 for f in fields_list if f.get("/V", None) is not None)
total = len(fields_list)
print(f"\nFilled: {filled}, Empty: {total - filled}, Total: {total}")
