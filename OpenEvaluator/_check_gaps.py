#!/usr/bin/env python3
"""Check which fields from sheet_parser are NOT reaching the form."""
import sys
sys.path.insert(0, '/home/workspace/OpenEvaluator')
from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro

fields = parse_sheet_row()
adapted = adapt_sheet_fields_to_acro(fields)

# Check specific fields
keys = [
    "applicant_name", "owner_name", "site_address", "phone", "email",
    "client_name", "mailing_street", "setback_well", "setback_tank_to_house",
    "elevation_reference_point", "erp_reference_elevation", "gps_margin_error",
    "num_rows", "mods_per_row", "cluster_width_ft", "cluster_length_ft",
    "design_flow_gallons", "bedrooms", "well_type", "well_depth",
    "deepest_restrictive_layer_hole1", "water_table_depth_hole1",
    "soil_type", "soil_layers", "site_notes", "special_notes"
]
for k in keys:
    v = fields.get(k, "<MISSING>")
    if v:
        adapted_val = adapted.get(k.replace("_", ""), adapted.get(k, "<NOT IN ADAPTED>"))
        print(f"  {k} = {repr(v)[:60]}")

print(f"\nTotal sheet_parser fields: {len(fields)}")
print(f"Total adapted fields: {len(adapted)}")
print(f"Non-empty adapted: {sum(1 for v in adapted.values() if v)}")
