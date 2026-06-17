#!/usr/bin/env python3
"""Full integration: all enrichers + sheet data + Claude + fill form + DXF"""
import json, os, sys
sys.path.insert(0, ".")
from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import fill_acro
from parcel_enricher import get_parcel_dimensions
from road_enricher import get_road_info
from water_enricher import find_wetlands_near, find_nearby_waterbodies

# 1. Parse form data
print("1. Parsing sheet data...")
fields = parse_sheet_row(RAW_ROW)
print(f"   {len(fields)} raw fields")

# 2. Enrich with GeoLibrary
print("2. Enriching with Maine GeoLibrary...")
parcel = get_parcel_dimensions("Turner", "Aspen Way")
if parcel.get("found"):
    fields["parcel_width_ft"] = str(parcel["width_ft"])
    fields["parcel_depth_ft"] = str(parcel["depth_ft"])
    fields["parcel_map_lot"] = parcel["map_bk_lot"]
    print(f"   Parcel: {parcel['width_ft']}' x {parcel['depth_ft']}' ({parcel['area_ac']} ac)")

# 3. Road data
print("3. Fetching road data...")
roads = get_road_info("Turner")
if roads.get("town"):
    print(f"   {roads['town']}: {len(roads.get('roads', []))} roads")
    fields["town_roads_count"] = str(len(roads.get("roads", [])))

# 4. Water features
print("4. Checking water features...")
wetlands = find_wetlands_near("Turner", "Aspen Way")
water = find_nearby_waterbodies("Turner", "Aspen Way")
print(f"   Wetlands: {wetlands['wetlands']}, Waterbodies: {water['waterbodies']}")

# 5. Get GPS from Maps
print("5. Getting GPS coordinates...")
maps_key = os.environ.get("GOOGLE_MAPS_API_KEY")
if maps_key:
    import googlemaps
    gmaps = googlemaps.Client(key=maps_key)
    geo = gmaps.geocode("17 Aspen Way, Turner, Maine 04282")
    if geo:
        loc = geo[0]["geometry"]["location"]
        fields["gps_latitude"] = str(loc["lat"])
        fields["gps_longitude"] = str(loc["lng"])
        print(f"   GPS: {loc['lat']}, {loc['lng']}")

# 6. Adapt fields and fill form
print("6. Filling HHE-200 form...")
adapted = adapt_sheet_fields_to_acro(fields)
result = fill_acro(adapted, "HHE-200-filled.pdf")
print(f"   PDF: {result}")

print("\n✅ Full integration test complete")