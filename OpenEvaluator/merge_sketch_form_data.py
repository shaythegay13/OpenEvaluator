#!/usr/bin/env python3
"""
Merges sketch extraction output with sheet parser data into a single field dict
that can be passed to acro_fill for complete HHE-200 form filling.

Combines data from:
  1. Google Sheet form fields (via sheet_parser)
  2. Vision API sketch extraction (hermes_output.json)
  3. Google Maps API (adjacent roads, coordinates)
  4. Field adapter (converts to acro_fill keys)
"""
import json
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_sketch_data(sketch_json_path: str) -> dict:
    """Load hermes_output.json from sketch extraction."""
    path = Path(sketch_json_path)
    if not path.exists():
        logger.warning(f"Sketch data not found: {sketch_json_path}")
        return {}
    with open(path) as f:
        return json.load(f)


def merge_with_form_fields(sketch_data: dict, sheet_fields: dict) -> dict:
    """
    Merge sketch extraction data with sheet parser fields.
    Sketch data takes priority (it's directly from the drawing).
    Returns a flat dict ready for field_adapter.
    """
    merged = dict(sheet_fields)  # Base: all sheet_parser fields

    # ===== PRIORITY 1: GPS COORDINATES FROM DRAWING =====
    # Only use Maps API if coordinates NOT found in sketch
    gps_found_in_drawing = False
    gps = sketch_data.get("gps_locations", {})
    raw_gps = gps.get("raw", "")
    if raw_gps:
        # Parse DMS: "44° 15' 18.56""
        dms_match = re.search(r"(\d+)°\s*(\d+)'\s*([\d.]+)\"", raw_gps)
        if dms_match:
            merged["latitude_degrees"] = dms_match.group(1)
            merged["latitude_minutes"] = dms_match.group(2)
            merged["latitude_seconds"] = dms_match.group(3)
            gps_found_in_drawing = True
            logger.info(f"  ✓ GPS found in drawing: {raw_gps}")

    # ===== FALLBACK: COORDINATES from Maps API (only if not in drawing) =====
    maps_data = sketch_data.get("maps_data", {})
    coords = maps_data.get("coordinates", {})
    if not gps_found_in_drawing and coords.get("lat"):
        lat = float(coords["lat"])
        lng = float(coords["lng"])
        lat_deg = int(abs(lat))
        lat_min = int((abs(lat) - lat_deg) * 60)
        lat_sec = round(((abs(lat) - lat_deg) * 60 - lat_min) * 60, 2)
        lng_deg = int(abs(lng))
        lng_min = int((abs(lng) - lng_deg) * 60)
        lng_sec = round(((abs(lng) - lng_deg) * 60 - lng_min) * 60, 2)

        merged["latitude_degrees"] = str(lat_deg)
        merged["latitude_minutes"] = str(lat_min)
        merged["latitude_seconds"] = str(lat_sec)
        merged["longitude_degrees"] = str(lng_deg)
        merged["longitude_minutes"] = str(lng_min)
        merged["longitude_seconds"] = str(lng_sec)
        merged["gps_latitude"] = str(lat)
        merged["gps_longitude"] = str(lng)
        logger.info(f"  ✓ GPS from Maps API fallback: {lat}, {lng}")

    # GPS margin of error - hardcoded per ME requirements
    merged["gps_margin_of_error"] = "30"

    # ===== CONTACT INFO: Ensure client and evaluator data are present =====
    # Client contact (from Google Sheet)
    if not merged.get("owner_phone"):
        merged["owner_phone"] = sheet_fields.get("phone", "")
    if not merged.get("owner_email"):
        merged["owner_email"] = sheet_fields.get("email", "")

    # Evaluator contact (from Google Sheet) — already set, but verify
    if not merged.get("evaluator_name"):
        merged["evaluator_name"] = sheet_fields.get("evaluator_name", "")
    if not merged.get("evaluator_phone"):
        merged["evaluator_phone"] = sheet_fields.get("evaluator_phone", "")
    if not merged.get("evaluator_email"):
        merged["evaluator_email"] = sheet_fields.get("evaluator_email", "")

    # ===== SOIL INFO from sketch =====
    soil = sketch_data.get("soil_info", {})
    soil_desc = soil.get("description", "")
    soil_depth = soil.get("depth_inches", "")

    if soil_desc and not merged.get("soil_classification_hole1"):
        merged["soil_classification_hole1"] = soil_desc
        merged["soil_classification_hole2"] = soil_desc
    if soil_depth:
        if not merged.get("deepest_restrictive_layer_hole1"):
            merged["deepest_restrictive_layer_hole1"] = f"@ {soil_depth} in"
        if not merged.get("deepest_restrictive_layer_hole2"):
            merged["deepest_restrictive_layer_hole2"] = f"@ {soil_depth} in"

    # ===== ELEVATIONS from sketch =====
    elev = sketch_data.get("elevations", {})
    elev_val = elev.get("value", "")
    if elev_val:
        ref_name = f"Ref Nail (at {elev_val} ft)"
        merged["elevation_reference_point"] = ref_name
        if not merged.get("erp_reference_elevation"):
            merged["erp_reference_elevation"] = elev_val

    # ===== ADJACENT ROADS from Maps =====
    adjacent_roads = maps_data.get("adjacent_roads", [])
    if adjacent_roads:
        merged["adjacent_roads"] = "; ".join(adjacent_roads)

    # ===== ADJACENT LOTS from sketch =====
    prop_info = sketch_data.get("property_info", {})
    adjacent_lots = prop_info.get("adjacent_lots", [])
    if adjacent_lots:
        merged["adjacent_lots"] = ", ".join(adjacent_lots)

    # ===== TIE ITEMS from sketch =====
    tie_items = sketch_data.get("tie_items", [])
    if tie_items:
        tie_strings = []
        for item in tie_items:
            from_item = item.get("from", "")
            to_item = item.get("to", "")
            dist = item.get("distance_ft", "")
            if from_item and to_item:
                tie_strings.append(f"{from_item} to {to_item} = {dist}'")
        if tie_strings:
            merged["tie_items"] = "; ".join(tie_strings)

    # ===== ADJACENT STREETS from sketch =====
    adjacent_streets = prop_info.get("adjacent_streets", [])
    if adjacent_streets:
        merged["adjacent_streets"] = ", ".join(adjacent_streets)

    # ===== SKETCH TEXT RAW DATA (for field inference) =====
    sketch_text_entries = sketch_data.get("sketch_text", [])
    full_sketch_text = ""
    for entry in sketch_text_entries:
        full_sketch_text += entry.get("text", "") + "\n"

    uploaded_soil_raw = _infer_soil_from_sketch_text(full_sketch_text, merged)

    return merged


def _infer_soil_from_sketch_text(text: str, merged: dict) -> dict:
    """Extract additional soil data from raw sketch OCR text."""
    if not text:
        return merged

    upper = text.upper()

    # Extract limiting factor type
    lf_match = re.search(
        r"(?:LIMITING FACTOR|LF|L\.F\.)[:\s]*([\w\s]+?)(?:\n|$|\d)",
        upper
    )
    if lf_match and not merged.get("limiting_factor_type"):
        merged["limiting_factor_type"] = lf_match.group(1).strip()

    # Extract water table depth if present
    wt_match = re.search(
        r"(?:WATER TABLE|WT|GROUNDWATER|GROUND WATER)[:\s]*~?(\d+)\s*(?:IN|INCHES|\")",
        upper
    )
    if wt_match:
        depth = wt_match.group(1)
        if not merged.get("water_table_depth_hole1"):
            merged["water_table_depth_hole1"] = depth
            merged["water_table_depth_hole2"] = depth

    return merged


def merge_and_fill_form(
    sketch_json_path: str,
    sheet_fields_path: str,
    acro_fill_module: str = "acro_fill",
    field_adapter_module: str = "field_adapter"
) -> dict:
    """
    Full pipeline: combine sketch data + sheet data → field adapter → acro_fill.
    Returns the adapted field dict (for diagnostics).
    """
    import importlib
    acro_fill = importlib.import_module(acro_fill_module)

    # Load data sources
    sketch_data = load_sketch_data(sketch_json_path)

    with open(sheet_fields_path) as f:
        sheet_fields = json.load(f)

    # Merge
    merged_fields = merge_with_form_fields(sketch_data, sheet_fields)
    logger.info(f"Merged {len(sheet_fields)} sheet fields + sketch data → {len(merged_fields)} combined fields")

    # Adapt field names to acro_fill
    from importlib import import_module
    adapter = importlib.import_module(field_adapter_module)
    adapted = adapter.adapt_sheet_fields_to_acro(merged_fields)
    logger.info(f"Adapted to {len(adapted)} acro_fill keys")

    # Fill the form
    pdf = acro_fill.fill_acro(adapted, "HHE-200-filled.pdf")
    logger.info(f"✓ Form generated: {pdf}")

    return adapted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Merge sketch data and fill form")
    parser.add_argument("--sketch-json", required=True, help="Path to hermes_output.json")
    parser.add_argument("--sheet-json", default="sheet_row_data.json",
                        help="Path to sheet parser JSON output")
    parser.add_argument("--output", help="Save merged fields to file for inspection")

    args = parser.parse_args()

    adapted = merge_and_fill_form(args.sketch_json, args.sheet_json)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(adapted, f, indent=2)
        logger.info(f"Adapted fields saved to {args.output}")

    # Print summary
    print(f"\n=== FORM FILLING SUMMARY ===")
    print(f"Total adapted fields: {len(adapted)}")
    for k, v in sorted(adapted.items()):
        print(f"  {k} = {repr(v[:60])}")
