#!/usr/bin/env python3
"""
Phase 1 Audit: Identify unmapped and checkbox-logic fields.

For row 2, show:
1. Fields in adapted dict that should reach the form but don't
2. Checkbox fields that need logic based on system type
3. Clear action list for Phase 1 implementation
"""
import sys
import json
sys.path.insert(0, '/home/workspace/OpenEvaluator')

from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import WIDGET_MAP

# Parse row 2
fields = parse_sheet_row(RAW_ROW)
adapted = adapt_sheet_fields_to_acro(fields)

print("=" * 80)
print("PHASE 1: WIDGET AUDIT FOR ROW 2")
print("=" * 80)

# 1. Find adapted fields with data that have NO WIDGET_MAP entry
print("\n[1] UNMAPPED FIELDS (data in adapted, no WIDGET_MAP):")
print("-" * 80)

unmapped = []
for key, val in sorted(adapted.items()):
    if val and key not in WIDGET_MAP:
        unmapped.append((key, val))
        print(f"  ❌ {key:40} = {repr(val)[:50]}")

print(f"\nTotal unmapped fields with data: {len(unmapped)}")

# 2. Fields in WIDGET_MAP that should be filled from adapted but aren't
print("\n[2] MAPPED FIELDS MISSING FROM ADAPTED (should be added):")
print("-" * 80)

needed_in_adapted = [
    "tank_regular_check", "tank_low_profile_check", "tank_h20_check",
    "eng_tank_check", "non_eng_tank_check",
    "cnes_check", "primitive_limited_check", "alt_toilet_check",
    "holding_tank_check", "non_eng_field_check", "ces_check", "eng_field_check",
    "disposal_field_type", "proprietary_device_opt",
    "mailing_street",
    "latitude_deg", "latitude_min", "latitude_sec",
    "longitude_deg", "longitude_min", "longitude_sec",
]

missing_logic = []
for key in needed_in_adapted:
    if key in WIDGET_MAP and key not in adapted:
        missing_logic.append(key)
        print(f"  ⚠️  {key:40} — needs logic or mapping")
    elif key in adapted and not adapted[key]:
        print(f"  ⚠️  {key:40} — in adapted but EMPTY")

print(f"\nTotal fields needing checkbox/logic: {len(missing_logic)}")

# 3. Checkbox fields that should be set based on system type
print("\n[3] CHECKBOX FIELDS NEEDING SYSTEM-TYPE LOGIC:")
print("-" * 80)

system_type = fields.get("disposal_system_type", "").lower()
tank_type = fields.get("tank_type", "").lower()
app_type = fields.get("application_type", "").lower()

checkbox_logic = {
    "non_eng_field_check": ("Non-Engineered Disposal Field" in system_type),
    "eng_field_check": ("Engineered" in system_type),
    "non_eng_tank_check": ("tank" in system_type and "treatment" in system_type),
    "eng_tank_check": ("Engineered Tank" in system_type),
    "holding_tank_check": ("Holding Tank" in system_type),
    "tank_regular_check": (tank_type == "regular"),
    "tank_low_profile_check": ("low" in tank_type or "profile" in tank_type),
    "tank_h20_check": ("h-20" in tank_type or "h20" in tank_type),
    "proprietary_device_opt": system_type if "proprietary" in system_type.lower() else "Eljen InDrain",
    "cnes_check": ("Non-Engineered" in system_type),
    "ces_check": ("Engineered" in system_type),
    "primitive_limited_check": ("Primitive" in system_type),
    "alt_toilet_check": ("Alternative Toilet" in system_type),
}

for field, should_check in checkbox_logic.items():
    status = "✓ SET" if should_check else "○ UNSET"
    print(f"  {status}  {field:40} (system_type={system_type[:20]}...)")

# 4. GPS fields — should be calculated from maps data
print("\n[4] GPS FIELDS (should be converted to DMS):")
print("-" * 80)

lat = adapted.get("latitude_deg", "")
lng = adapted.get("longitude_deg", "")
print(f"  Latitude DMS:   deg={lat}, min={adapted.get('latitude_min','')}, sec={adapted.get('latitude_sec','')}")
print(f"  Longitude DMS:  deg={lng}, min={adapted.get('longitude_min','')}, sec={adapted.get('longitude_sec','')}")
print(f"  GPS margin:     {adapted.get('gps_margin_error', '')}")

# 5. Summary & recommendations
print("\n" + "=" * 80)
print("PHASE 1 ACTION ITEMS:")
print("=" * 80)

recommendations = [
    f"1. Add {len(unmapped)} unmapped fields to WIDGET_MAP → field_adapter",
    f"2. Implement checkbox logic for {len(missing_logic)} system-dependent checkboxes",
    f"3. Verify GPS conversion logic (DMS format)",
    f"4. Map mailing_street and other contact fields",
    f"5. Retest: should increase from 31% → ~50%+ fill rate",
]

for rec in recommendations:
    print(f"\n{rec}")

print("\n" + "=" * 80)
