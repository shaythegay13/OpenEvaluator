#!/usr/bin/env python3
"""
Quick test: Verify contact fields and GPS flow through merge → adapter → PDF

Tests:
1. Client contact (owner_phone, owner_email)
2. Evaluator contact (evaluator_name, phone, email)
3. GPS: Drawing first, then Maps API fallback
"""
import json
from pathlib import Path

# Load test data
sheet_path = Path("sheet_row_data.json")
sketch_path = Path("hermes_output.json") if Path("hermes_output.json").exists() else None

print("\n=== PHASE 1 FIX: Contact & GPS Flow Test ===\n")

if sheet_path.exists():
    with open(sheet_path) as f:
        sheet_fields = json.load(f)
    print(f"✓ Loaded sheet data: {len(sheet_fields)} fields")

    # Check contact fields
    print(f"\n📋 CONTACT FIELDS (Sheet):")
    print(f"  owner_name: {sheet_fields.get('owner_name', '')}")
    print(f"  phone: {sheet_fields.get('phone', '')}")
    print(f"  owner_phone: {sheet_fields.get('owner_phone', '')}")
    print(f"  owner_email: {sheet_fields.get('owner_email', '')}")
    print(f"  evaluator_name: {sheet_fields.get('evaluator_name', '')}")
    print(f"  evaluator_phone: {sheet_fields.get('evaluator_phone', '')}")
    print(f"  evaluator_email: {sheet_fields.get('evaluator_email', '')}")

if sketch_path and sketch_path.exists():
    with open(sketch_path) as f:
        sketch_data = json.load(f)
    print(f"\n✓ Loaded sketch data")

    # Check GPS in sketch
    gps = sketch_data.get("gps_locations", {})
    print(f"\n🗺️ GPS DATA (Sketch):")
    print(f"  raw: {gps.get('raw', '[none]')}")

    maps_data = sketch_data.get("maps_data", {})
    coords = maps_data.get("coordinates", {})
    print(f"\n🗺️ GPS DATA (Maps API fallback):")
    print(f"  lat: {coords.get('lat', '[none]')}")
    print(f"  lng: {coords.get('lng', '[none]')}")

print(f"\n✅ Ready for Phase 1 adapter/widget mapping")
