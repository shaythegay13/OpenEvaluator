#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, ".")
from claude_sketch_extractor import extract_sketch_with_claude, merge_sketch_with_form
from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import fill_acro
import googlemaps

# GPS from Maps
client = googlemaps.Client(key=os.environ.get("GOOGLE_MAPS_API_KEY"))
geo = client.geocode("17 Aspen Way, Turner, Maine 04282")
loc = geo[0]["geometry"]["location"] if geo else {}

# Extract sketch, merge with form, generate
sketch = extract_sketch_with_claude("sketches/26-018 field worksheet - George Bouchles.pdf")
if sketch:
    print(f"Claude extracted: {len(sketch)} top-level keys")

form_fields = parse_sheet_row(RAW_ROW)
form_fields["gps_latitude"] = str(loc.get("lat", ""))
form_fields["gps_longitude"] = str(loc.get("lng", ""))

merged = merge_sketch_with_form(sketch, form_fields)
adapted = adapt_sheet_fields_to_acro(merged)
pdf = fill_acro(adapted, "HHE-200-filled.pdf")
print(f"Result: {pdf}")

# Score
import pikepdf
p = pikepdf.open(pdf)
acro = p.Root["/AcroForm"]
all_f = acro["/Fields"]
filled = sum(1 for f in all_f if f.resolve().get("/V") is not None)
print(f"Filled: {filled}/{len(all_f)}")
p.close()

