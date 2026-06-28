#!/usr/bin/env python3
"""
sheet_parser.py — Parse a Google Sheets HHE-200 application row into a
flat field dictionary matching field_map.yaml.

Reads from spreadsheet ID: 1ebjhzBSaH9zrJBORxKTkM56ukKV2IlNJ-3r1wJslNBc
Sheet: "Form Responses 1", row 2 (first data row after headers).
"""

from __future__ import annotations

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
MAP_PATH   = SCRIPT_DIR / "field_map.yaml"
OUTPUT_PDF = SCRIPT_DIR / "HHE-200-filled.pdf"

# ── Google Sheets data (row 2, headers = row 1) ────────────────────────────
# Captured from: spreadsheetId=1ebjhzBSaH9zrJBORxKTkM56ukKV2IlNJ-3r1wJslNBc
# sheetName="Form Responses 1", range=A1:T2, hasHeaders=true
RAW_ROW: Dict[str, str] = {
    "Timestamp":        "3/1/2026 11:17:21",
    "Client name, Phone number, and Address": "Kristen Marquis, , 17 Aspen Way, Turner, Maine 04282",
    "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
    "Map and Lot # and Acreage": "26, 18, 2.35",
    "Site Evaluator's Information": (
        "George Bouchles, 338, 207-240-5567, "
        "gsb@cadmasterr.com, Cadmasterr Drafting & Land Surveying"
    ),
    "Application Type": "Replacement system",
    "Use and bedrooms/flow": (
        "single family dwelling, 3 bedroom home, 270 gallons per day"
    ),
    "Seasonal use":          "Year-round",
    "Shoreland zoning":       "",
    "GPS Coordinates": "44'08'17.8\", 70'07'23.1\"",
    "Water supply and well": "existing drilled well, private, 125 ft.",
    "Soil summary at disposal area": (
        "brown fine sandy loam to 3 inches, "
        "yellowish brown fine sandy loam from 3 inches to 24 inches, "
        "olive gray fine sandy loam to pit depth of 36 inches,"
    ),
    "Limiting factor":          "limiting factor is ground water at 24 inches",
    "Disposal system type":     "Eljen-in Drain",
    "Septic tank setup": (
        "existing 1,000 gallon septic tank shall be exposed, "
        "inspected for structural integrity. if need, tank shall be "
        "replaced. outlet baffle shall be inspected and replaced if "
        "necessary. "
    ),
    "Design flow override":          "270 gallons per day",
    "Planned field size and layout (if known)": (
        "3 rows of 7 eljen-in-drain GSF-B43 Modules, 21 units total, "
        "11'x28' cluster formation."
    ),
    "Key distances between features": (
        "Tie Point A: maple tree (ERP), 45 feet, NW corner\n"
        "Tie Point B: oak tree, 62 feet, SE corner\n"
        "Pin/Reference: iron rod, 35 feet\n"
        "field to well 100 feet minimum"
    ),
    "Foundation Type": "Yes, full foundation/frost walls",
    "Requesting any variances?": "none",
    "Elevation reference point (ERP) and elevations (if known)": (
        "ERP = nail set 12 inches above grade in 6\" maple tree, "
        "finish grade elevation = 0\", top of pipe = -12\", "
        'bottom of proprietary device = -24", bottom of disposal area = -30"'
    ),
    "Uploads":    "https://drive.google.com/open?id=1Tg5V7uI99qcUgqIjQAlrqrASexL7B5yA",
    "Special Notes": "none",
    "Page 3 Site Plan Scale": "1 inch = 100 feet",
    "Page 4 Top (Septic Plan) Scale": "1 inch = 10 feet",
    "Page 4 Bottom Cross-Section Vertical Scale": "1 inch = 2.5 feet",
    "Page 4 Bottom Cross-Section Horizontal Scale": "1 inch = 5 feet",
}

# Test row 2: Roberts (26-123)
ROBERTS_ROW: Dict[str, str] = {
    "Timestamp":        "3/5/2026 14:22:15",
    "Client name, Phone number, and Address": "Charles Roberts, , 450 Lane Road, Greene, Maine 04236",
    "Property Location Details": "450 Lane Road, Greene, Maine 04236",
    "Map and Lot # and Acreage": "26, 123, 1.85",
    "Site Evaluator's Information": (
        "George Bouchles, 338, 207-240-5567, "
        "gsb@cadmasterr.com, Cadmasterr Drafting & Land Surveying"
    ),
    "Application Type": "New system",
    "Use and bedrooms/flow": (
        "single family dwelling, 2 bedroom mobile home, 180 gallons per day"
    ),
    "Seasonal use":          "Year-round",
    "Shoreland zoning":       "",
    "GPS Coordinates": "44'10'33.2\", 70'12'45.7\"",
    "Water supply and well": "new drilled well",
    "Soil summary at disposal area": (
        "brown fine sandy loam to 4 inches, "
        "yellowish brown loamy sand from 4 inches to 18 inches, "
        "gray sand to pit depth of 42 inches"
    ),
    "Limiting factor":          "limiting factor is fine sand at 18 inches",
    "Disposal system type":     "Infiltrator",
    "Septic tank setup":       "new 500 gallon septic tank to be installed",
    "Design flow override":     "180 gallons per day",
    "Planned field size and layout (if known)": (
        "2 rows of 4 infiltrator modules, 8 units total, 8'x20' cluster formation"
    ),
    "Key distances between features": (
        "Tie Point A: shed, 17.5 feet, NW corner\n"
        "Tie Point B: shed, 39.5 feet, NE corner\n"
        "Pin/Reference: telephone pole, 80 feet\n"
        "field to well 120 feet, field to house 25 feet, "
        "tank to field 8 feet, upslope backfill 4 inches, downslope backfill 10 inches"
    ),
    "Foundation Type": "Yes, slab/posts",
    "Requesting any variances?": "well setback",
    "Elevation reference point (ERP) and elevations (if known)": (
        "ERP = finish grade, finish grade elevation = 0\", top of pipe = -8\", "
        'bottom of proprietary device = -18", bottom of disposal area = -28"'
    ),
    "Uploads":    "https://drive.google.com/open?id=1Tg5V7uI99qcUgqIjQAlrqrASexL7B5yA",
    "Special Notes": "sloped site, mobile home",
    "Page 3 Site Plan Scale": "1 inch = 100 feet",
    "Page 4 Top (Septic Plan) Scale": "1 inch = 10 feet",
    "Page 4 Bottom Cross-Section Vertical Scale": "1 inch = 2.5 feet",
    "Page 4 Bottom Cross-Section Horizontal Scale": "1 inch = 5 feet",
}


# ── parsing helpers ──────────────────────────────────────────────────────────
def _strip(value: str) -> str:
    return value.strip().rstrip(",").rstrip(".").strip()


def _last(value: str) -> str:
    """Return the last comma-separated token, stripped."""
    parts = [p.strip() for p in value.split(",")]
    return parts[-1] if parts else ""


def _first(value: str) -> str:
    """Return the first comma-separated token, stripped."""
    parts = [p.strip() for p in value.split(",")]
    return parts[0] if parts else ""


def _parse_number(value: str) -> str:
    """Extract the first integer or float from a string."""
    m = re.search(r"[\d.]+", value)
    return m.group() if m else ""


def parse_map_lot_acreage(raw: str) -> Dict[str, str]:
    """
    '26, 18, 2.35' → map_number='26', lot_number='18', acreage='2.35'
    """
    parts = [p.strip() for p in raw.split(",")]
    while len(parts) < 3:
        parts.insert(0, "")
    return {
        "map_number":  parts[0],
        "lot_number":  parts[1],
        "acreage":     parts[2],
    }


def parse_evaluator_info(raw: str) -> Dict[str, str]:
    """
    'George Bouchles, 338, 207-240-5567, gsb@cadmasterr.com,
     Cadmasterr Drafting & Land Surveying'
    → evaluator_name='George Bouchles', lpi_number='338',
       evaluator_phone='207-240-5567', evaluator_email='gsb@cadmasterr.com',
       evaluator_company='Cadmasterr Drafting & Land Surveying'
    """
    parts = [p.strip() for p in raw.split(",")]
    # Pad to at least 5 so indexing is safe
    while len(parts) < 5:
        parts.append("")
    return {
        "evaluator_name":    parts[0],
        "lpi_number":        parts[1],
        "evaluator_phone":   parts[2],
        "evaluator_email":   parts[3],
        "evaluator_company": parts[4],
    }


def parse_use_bedrooms_flow(raw: str) -> Dict[str, str]:
    """
    'single family dwelling, 3 bedroom home, 270 gallons per day'
    → use='single family dwelling', bedrooms='3', design_flow='270'
    """
    parts = [p.strip() for p in raw.split(",")]
    while len(parts) < 3:
        parts.append("")
    bedrooms_raw = parts[1]
    bedrooms_num = re.sub(r"[^\d]", "", bedrooms_raw) if bedrooms_raw else ""
    flow_num = _parse_number(parts[2]) if parts[2] else ""
    return {
        "use":              parts[0],
        "bedrooms":         bedrooms_num,
        "design_flow_gallons": flow_num,
    }


def parse_water_supply(raw: str) -> Dict[str, str]:
    """
    'existing drilled well, private, 125 ft.'
    → water_supply_type='existing drilled well',
       well_type='drilled well' (extracted),
       well_ownership='private',
       well_depth='125 ft.'
    """
    parts = [p.strip() for p in raw.split(",")]
    while len(parts) < 3:
        parts.append("")
    # First token: "existing drilled well" → keep as-is for water_supply_type
    water_supply_type = parts[0]
    # well_type: extract the type word (drilled well / dug well / etc.)
    type_match = re.search(
        r"\b(drilled|dressed-dug|dug|cased|driven|boried|air-rotary)\s+(well)",
        water_supply_type, re.IGNORECASE
    )
    well_type = f"{type_match.group(1)} {type_match.group(2)}" if type_match else water_supply_type
    return {
        "water_supply_type": water_supply_type,
        "well_type":         well_type,
        "well_ownership":     parts[1],
        "well_depth":        parts[2],
    }


def parse_soil_by_depth(raw: str) -> Dict[str, str]:
    """
    Parse soil description into layers by depth, detecting pit/boring markers.

    Raw: 'brown fine sandy loam to 3 inches,
          yellowish brown fine sandy loam from 3 inches to 24 inches,
          olive gray fine sandy loam to pit depth of 36 inches'

    OR with pit markers:
    'Test Pit 1: brown fine sandy loam to 3 inches, ...'
    'Test Pit 2: ...'

    Returns 26 structured soil fields (13 per pit × 2):
    - soil_pit1_observation_hole_number, soil_pit1_textures, soil_pit1_consistence, etc.
    - soil_pit2_* (empty if no Pit 2 detected)
    - Also returns backward-compatible fields for non-pit parsing
    """
    result = {}

    # Detect pit/boring markers: "Test Pit 1:", "Test Pit 2:", "Test Boring 1:", etc.
    pit_pattern = r"(?:test\s+)?(?:pit|boring|observation\s+hole)\s+([12])\s*:\s*([^]*?)(?=(?:test\s+)?(?:pit|boring|observation\s+hole)\s+[12]\s*:|$)"
    pit_matches = re.findall(pit_pattern, raw, re.IGNORECASE | re.DOTALL)

    pits_found = {}
    for pit_num, pit_text in pit_matches:
        pits_found[int(pit_num)] = pit_text.strip()

    # If no pit markers found, treat entire text as Pit 1
    if not pits_found:
        pits_found[1] = raw

    # Parse each pit
    for pit_num in [1, 2]:
        pit_text = pits_found.get(pit_num, "")
        pit_prefix = f"soil_pit{pit_num}_"

        if pit_text:
            # Extract layers from pit (comma-delimited)
            layers = []
            segments = [s.strip() for s in pit_text.split(",")]

            for seg in segments:
                # Extract depth
                depth_m = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*inches?", seg, re.IGNORECASE)
                single_m = re.search(r"to\s*(\d+)\s*inches?", seg, re.IGNORECASE)
                if depth_m:
                    depth = f"{depth_m.group(1)}-{depth_m.group(2)}"
                elif single_m:
                    depth = f"0-{single_m.group(1)}"
                else:
                    depth = ""

                # Extract texture (color + soil type)
                color_match = re.search(
                    r"^([\w\s]+?)\s+(?:fine\s+)?(?:sandy\s+)?loam", seg, re.IGNORECASE
                )
                texture = color_match.group(1).strip() if color_match else seg.split()[0] if seg else ""

                # Truncate texture to 1-2 words
                texture_words = texture.split()[:2]
                texture_short = " ".join(texture_words)

                layers.append({
                    "depth": depth,
                    "texture": texture_short,
                    "full": seg
                })

            # Extract pit-specific fields from layers
            # Observation hole number: extract single digit if present
            oh_match = re.search(r"observation\s+hole\s+(\d)", pit_text, re.IGNORECASE)
            oh_num = oh_match.group(1) if oh_match else ""
            result[f"{pit_prefix}observation_hole_number"] = oh_num

            # Textures: first layer texture
            if layers:
                result[f"{pit_prefix}textures"] = layers[0].get("texture", "")[:20]  # Truncate to box width
            else:
                result[f"{pit_prefix}textures"] = ""

            # Consistence: extract from first layer if present (abbreviate)
            consistence = ""
            if layers and "friable" in layers[0].get("full", "").lower():
                consistence = "Fr"
            elif layers and "firm" in layers[0].get("full", "").lower():
                consistence = "Fm"
            result[f"{pit_prefix}consistence"] = consistence

            # Color: extract color from first layer
            color = ""
            if layers:
                color_match = re.search(r"^(\w+)\s+(?:fine\s+)?", layers[0].get("full", ""), re.IGNORECASE)
                if color_match:
                    color = color_match.group(1)[:15]  # Truncate
            result[f"{pit_prefix}color"] = color

            # Redox features: check for gleying, mottling, etc.
            redox = ""
            for seg in segments:
                if any(w in seg.lower() for w in ["gley", "mottle", "redox", "iron"]):
                    redox = "Yes"
                    break
            result[f"{pit_prefix}redox_features"] = redox

            # Profile: dominant soil type (last layer, 1-2 words)
            dominant_soil = layers[-1].get("texture", "") if layers else ""
            profile = " ".join(dominant_soil.split()[:2]) if dominant_soil else ""
            result[f"{pit_prefix}profile"] = profile

            # Condition: extract from pit text if present (abbreviate)
            condition = ""
            if "moist" in pit_text.lower():
                condition = "Moist"
            elif "dry" in pit_text.lower():
                condition = "Dry"
            result[f"{pit_prefix}condition"] = condition[:15]

            # Slope: extract percentage if present
            slope = ""
            slope_m = re.search(r"(?:slope|slop)\s+(\d+)\s*%", pit_text, re.IGNORECASE)
            if slope_m:
                slope = slope_m.group(1)
            result[f"{pit_prefix}slope"] = slope

            # Limiting factor: extract limiting factor depth (single number only)
            limiting_factor = ""
            lim_m = re.search(r"limiting\s+factor.*?(\d+)\s*inches?", pit_text, re.IGNORECASE)
            if lim_m:
                limiting_factor = lim_m.group(1)[:1]  # Single digit only
            result[f"{pit_prefix}limiting_factor"] = limiting_factor

            # Groundwater: check for water depth
            groundwater = ""
            gw_m = re.search(r"(?:ground\s+?water|water\s+table).*?(\d+)\s*inches?", pit_text, re.IGNORECASE)
            if gw_m:
                groundwater = gw_m.group(1)
            result[f"{pit_prefix}groundwater"] = groundwater

            # Restrictive layer: check for restricting layer type
            restrictive = ""
            if any(w in pit_text.lower() for w in ["clay", "hardpan", "bedrock", "impervious"]):
                restrictive = "Yes"
            result[f"{pit_prefix}restrictive_layer"] = restrictive

            # Bedrock: check for bedrock mention
            bedrock = ""
            bedrock_m = re.search(r"bedrock.*?(\d+)\s*inches?", pit_text, re.IGNORECASE)
            if bedrock_m:
                bedrock = bedrock_m.group(1)
            result[f"{pit_prefix}bedrock"] = bedrock

            # Pit depth: extract "pit depth of X inches" or final depth
            pit_depth = ""
            depth_m = re.search(r"pit depth\s+(?:of\s+)?(\d+)\s*inches?", pit_text, re.IGNORECASE)
            if depth_m:
                pit_depth = depth_m.group(1)
            elif layers:
                # Use last layer's depth
                last_depth = layers[-1].get("depth", "")
                if "-" in last_depth:
                    pit_depth = last_depth.split("-")[1].split()[0]
            result[f"{pit_prefix}pit_depth"] = pit_depth
        else:
            # Pit not present, fill all with empty
            for field in [
                "observation_hole_number", "textures", "consistence", "color",
                "redox_features", "profile", "condition", "slope", "limiting_factor",
                "groundwater", "restrictive_layer", "bedrock", "pit_depth"
            ]:
                result[f"{pit_prefix}{field}"] = ""

    # Backward compatibility: also return old-style fields
    pit1_profile = result.get("soil_pit1_profile", "")
    pit1_depth = result.get("soil_pit1_pit_depth", "")

    result["soil_type"] = pit1_profile
    result["deepest_soil_depth"] = f"{pit1_depth} in" if pit1_depth else ""
    result["soil_layers"] = []  # Legacy; not used in Phase 2

    return result


def _reverse_name_format(full_name: str) -> str:
    """
    Reverse name from 'FirstName LastName' to 'LastName, FirstName'.
    Handles single names, hyphenated names, etc.
    """
    if not full_name:
        return ""

    name_parts = full_name.strip().split()
    if len(name_parts) == 1:
        return name_parts[0]

    # Assume last part is surname
    first_parts = name_parts[:-1]
    last_part = name_parts[-1]
    return f"{last_part}, {' '.join(first_parts)}"


def _abbreviate_state(state_name: str) -> str:
    """Convert full state name to 2-letter abbreviation."""
    state_map = {
        'maine': 'ME',
        'new hampshire': 'NH',
        'vermont': 'VT',
        'massachusetts': 'MA',
        'rhode island': 'RI',
        'connecticut': 'CT',
        'new york': 'NY',
        'new jersey': 'NJ',
        'pennsylvania': 'PA',
    }
    return state_map.get(state_name.lower().strip(), state_name)


def parse_client_address(raw: str) -> Dict[str, str]:
    """
    'Kristen Marquis, [phone], [address]'
    → owner_name='Marquis, Kristen', phone='', mailing_street='[address]'
    """
    parts = [p.strip() for p in raw.split(",")]
    while len(parts) < 3:
        parts.append("")
    owner_name_raw = parts[0] if parts[0].lower() != "empty" else ""
    owner_name = _reverse_name_format(owner_name_raw)
    # parts[1] = phone (may be empty)
    # parts[2] = full mailing address or "empty"
    mailing_street = parts[2] if parts[2].lower() != "empty" else parts[1] if parts[1].lower() != "empty" else ""
    return {
        "owner_name":     owner_name,
        "mailing_street": mailing_street,
        "phone":          "",   # phone not provided in this cell
    }


def parse_property_location(raw: str) -> Dict[str, str]:
    """
    '17 Aspen Way, Turner, Maine 04282'
    → site_address='17 Aspen Way', town='Turner',
       state='Maine', zip='04282'
    """
    # Expect: street, city, state+zip (last token is zip, second-to-last is state)
    parts = [p.strip() for p in raw.split(",")]
    while len(parts) < 3:
        parts.insert(0, "")
    site_address = parts[0]
    city = parts[1]
    # Last part may be "Maine 04282"
    state_zip = parts[2] if len(parts) > 2 else ""
    sz_parts = state_zip.rsplit(" ", 1)
    state = sz_parts[0] if sz_parts else ""
    zip_code = sz_parts[1] if len(sz_parts) > 1 else ""
    # Try to extract zip from full string if parts didn't parse cleanly
    zip_m = re.search(r"\d{5}", raw)
    if zip_m:
        zip_code = zip_m.group()
    state_m = re.search(r"\b(Maine|New Hampshire|Vermont|Massachusetts)\b", raw)
    state = state_m.group() if state_m else state
    return {
        "site_address": site_address,
        "town":         city,
        "mailing_state": state,
        "mailing_zip":  zip_code,
    }


def parse_elevation_reference(raw: str) -> Dict[str, str]:
    """
    'ERP = nail set 12 inches above grade in 6" maple tree,
     finish grade elevation = 0", top of pipe = -12",
     bottom of proprietary device = -24", bottom of disposal area = -30"'

    Extracts individual elevation values (all four separately, no merging).
    """
    erp = {}
    mapping = {
        "finish_grade_elevation":                      r"finish grade elevation\s*=+\s*([-\d.]+)\"",
        "top_of_distribution_pipe_elevation":         r"top of pipe\s*=+\s*([-\d.]+)\"",
        "bottom_of_proprietary_device_elevation":     r"bottom of proprietary device\s*=+\s*([-\d.]+)\"",
        "bottom_of_disposal_field_elevation":         r"bottom of disposal area\s*=+\s*([-\d.]+)\"",
    }
    for key, pattern in mapping.items():
        m = re.search(pattern, raw, re.IGNORECASE)
        erp[key] = m.group(1) if m else ""
    # Page 6 equivalent fields
    erp["finished_grade_elevation_p6"]                = erp.get("finish_grade_elevation", "")
    erp["top_of_distribution_pipe_elevation_p6"]      = erp.get("top_of_distribution_pipe_elevation", "")
    erp["bottom_of_proprietary_device_elevation_p6"]  = erp.get("bottom_of_proprietary_device_elevation", "")
    erp["bottom_of_disposal_field_elevation_p6"]      = erp.get("bottom_of_disposal_field_elevation", "")
    return erp


def parse_field_layout(raw: str) -> Dict[str, str]:
    """
    Parse planned field layout text into structured dimensions.
    
    Input: '3 rows of 7 eljen-in-drain GSF-B43 Modules, 21 units total, 11'x28' cluster formation.'
    Output: rows=3, modules_per_row=7, total_modules=21, cluster_width=11, cluster_length=28, brand=Eljen
    """
    result = {}
    if not raw:
        return result
    
    # Extract rows: "3 rows" or "4 rows"
    m = re.search(r"(\d+)\s+rows?", raw, re.IGNORECASE)
    if m:
        result["num_rows"] = m.group(1)
    
    # Extract modules per row: "of 7 ... Modules" or "7 modules per row"
    m = re.search(r"of\s+(\d+)\s+\w+.*[Mm]odul", raw)
    if not m:
        m = re.search(r"(\d+)\s+(?:modul|units?)\s+per\s+row", raw, re.IGNORECASE)
    if m:
        result["mods_per_row"] = m.group(1)
    
    # Extract total modules: prefer explicit count like "21 units total"
    # Fall back to "43 Modules" only if no explicit count found
    m = re.search(r"(\d+)\s+(?:units?|total)\s+(?:total|units?)", raw, re.IGNORECASE)
    if m:
        result["total_modules"] = m.group(1)
    
    # Extract cluster dimensions: "11'x28'" or "11 ft x 28 ft"
    m = re.search(r"(\d+\.?\d*)\s*(?:'|ft|feet)?\s*[xX×]\s*(\d+\.?\d*)\s*(?:'|ft|feet)?", raw)
    if m:
        result["cluster_width_ft"] = m.group(1)  # first number = width
        result["cluster_length_ft"] = m.group(2)  # second number = length
    
    # Extract brand
    m = re.search(r"(eljen|infiltrator|presby|biotube|oceangrow|in\s*[Dd]rain)", raw, re.IGNORECASE)
    if m:
        result["brand"] = m.group(1).title()
    
    # Calculate area
    if "cluster_width_ft" in result and "cluster_length_ft" in result:
        try:
            w = float(result["cluster_width_ft"])
            l = float(result["cluster_length_ft"])
            result["area_sqft"] = str(int(w * l))
        except ValueError:
            pass
    
    return result


def parse_tie_points(raw: str) -> Dict[str, str]:
    """
    Parse structured tie-point data from the "Key distances" field.

    Expected format:
      Tie Point A: [object], [distance] feet, [field corner]
      Tie Point B: [object], [distance] feet, [field corner]
      Pin/Reference: [object], [distance] feet

    Returns:
      tie_point_a_object, tie_point_a_distance, tie_point_a_corner,
      tie_point_b_object, tie_point_b_distance, tie_point_b_corner,
      pin_object, pin_distance
    """
    result = {}
    if not raw:
        return result

    # Normalize: handle line breaks and tabs
    text = raw.replace("\n", " ").replace("\t", " ")

    # Tie Point A: [object], [distance] feet, [field corner]
    tp_a = re.search(
        r"Tie\s+Point\s+A\s*:\s*([^,]+)\s*,\s*(\d+(?:\.\d+)?)\s*feet?\s*,\s*([^,\n]+?)(?:\s*$|,|Tie|Pin)",
        text, re.IGNORECASE
    )
    if tp_a:
        result["tie_point_a_object"] = _strip(tp_a.group(1))
        result["tie_point_a_distance"] = tp_a.group(2)
        result["tie_point_a_corner"] = _strip(tp_a.group(3))

    # Tie Point B: [object], [distance] feet, [field corner]
    tp_b = re.search(
        r"Tie\s+Point\s+B\s*:\s*([^,]+)\s*,\s*(\d+(?:\.\d+)?)\s*feet?\s*,\s*([^,\n]+?)(?:\s*$|,|Pin)",
        text, re.IGNORECASE
    )
    if tp_b:
        result["tie_point_b_object"] = _strip(tp_b.group(1))
        result["tie_point_b_distance"] = tp_b.group(2)
        result["tie_point_b_corner"] = _strip(tp_b.group(3))

    # Pin/Reference: [object], [distance] feet
    pin = re.search(
        r"Pin\s*/?(?:Reference)?\s*:\s*([^,]+)\s*,\s*(\d+(?:\.\d+)?)\s*feet?",
        text, re.IGNORECASE
    )
    if pin:
        result["pin_object"] = _strip(pin.group(1))
        result["pin_distance"] = pin.group(2)

    return result


def parse_distances(raw: str) -> Dict[str, str]:
    """
    'house to tank = 8', tank to field may vary,
     field to well 100 feet minimum, upslope backfill 4 inches, downslope backfill 10 inches'

    Extract: house-to-tank, well setback, backfill upslope/downslope, etc.
    Also extracts structured tie-point data if present.
    """
    result = {}

    # Try structured tie-point parsing first
    tie_points = parse_tie_points(raw)
    result.update(tie_points)

    # Well setback: "field to well 100 feet"
    m = re.search(r"field to well\s*=?\s*(\d+)", raw, re.IGNORECASE)
    result["setback_well"] = f"{m.group(1)} ft" if m else ""

    # House to tank: "house to tank = 8'" or "house to tank 8 ft"
    m = re.search(r"(?:house|home)\s*to\s*tank\s*=?\s*(\d+)", raw, re.IGNORECASE)
    result["setback_tank_to_house"] = f"{m.group(1)}'" if m else ""

    # Field to house: "field to house 100 ft"
    m = re.search(r"field to (?:house|building|structure)\s*=?\s*(\d+)", raw, re.IGNORECASE)
    result["setback_field_to_house"] = f"{m.group(1)} ft" if m else ""

    # System to property line
    m = re.search(r"(?:system|field)\s*to\s*(?:property|line|boundary)\s*=?\s*(\d+)", raw, re.IGNORECASE)
    result["setback_property_line"] = f"{m.group(1)} ft" if m else ""

    # Backfill upslope: "upslope backfill 4 inches"
    m = re.search(r"upslope\s+backfill\s+(\d+)\s*(?:inches?|in)", raw, re.IGNORECASE)
    result["backfill_upslope_inches"] = m.group(1) if m else ""

    # Backfill downslope: "downslope backfill 10 inches"
    m = re.search(r"downslope\s+backfill\s+(\d+)\s*(?:inches?|in)", raw, re.IGNORECASE)
    result["backfill_downslope_inches"] = m.group(1) if m else ""

    return result


def parse_limiting_factor(raw: str) -> Dict[str, str]:
    """
    'limiting factor is ground water at 24 inches'
    → deepest_restrictive_layer_hole1 = 'Ground Water',
       water_table_depth_hole1 = '24'
    """
    depth_m = re.search(r"(\d+)\s*inches?", raw, re.IGNORECASE)
    depth = depth_m.group(1) if depth_m else ""
    # Replicate to page 4 mirrors
    return {
        "deepest_restrictive_layer_hole1":   "Ground Water",
        "deepest_restrictive_layer_hole2":   "Ground Water",
        "deepest_restrictive_layer_p4_hole1": "Ground Water",
        "deepest_restrictive_layer_p4_hole2": "Ground Water",
        "water_table_depth_hole1":           depth,
        "water_table_depth_hole2":           depth,
        "water_table_depth_p4_hole1":        depth,
        "water_table_depth_p4_hole2":         depth,
    }


def parse_septic_tank(raw: str) -> Dict[str, str]:
    """
    'existing 1,000 gallon septic tank shall be exposed...'
    The HHE-200 doesn't have a dedicated septic tank notes field,
    but the info belongs in the narrative section.
    Returns a note for site_notes / special_notes.
    """
    return {
        "site_notes": f"Septic tank: {raw}",
    }


def parse_foundation_type(raw: str) -> Dict[str, str]:
    """
    Parse foundation type from form response.
    
    Input: 'Yes, full foundation/frost walls' or 'Yes, slab/posts' or 'No'
    Output: foundation_type = 'full' | 'slab' | 'none'
    """
    if not raw:
        return {"foundation_type": ""}
    
    raw_lower = raw.lower().strip()
    if "full foundation" in raw_lower or "frost wall" in raw_lower:
        return {"foundation_type": "full"}
    elif "slab" in raw_lower or "post" in raw_lower:
        return {"foundation_type": "slab"}
    elif "no" in raw_lower or "none" in raw_lower:
        return {"foundation_type": "none"}
    else:
        return {"foundation_type": raw}


def parse_variance_types(raw: str) -> Dict[str, str]:
    """
    Parse variance declarations from form response.

    Input: 'none' or comma-separated list like 'well setback, building setback'
    Output: variance_types = list of variance types declared
           variance_types_str = comma-separated string for storage
    """
    if not raw:
        return {"variance_types": "", "variance_types_list": []}

    raw_lower = raw.lower().strip()
    if raw_lower == "none" or raw_lower == "":
        return {"variance_types": "", "variance_types_list": []}

    # Split on comma, strip each, keep as list
    types = [t.strip() for t in raw.split(",")]
    types = [t for t in types if t and t.lower() != "none"]  # Filter empty and 'none'

    return {
        "variance_types": ", ".join(types),
        "variance_types_list": types,
    }


def parse_gps_coordinates(raw: str) -> Dict[str, str]:
    """
    Parse GPS coordinates in apostrophe-delimited format.

    Input: "44'08'17.8\", 70'07'23.1\""
    Output: latitude_deg='44', latitude_min='08', latitude_sec='17.8',
           longitude_deg='70', longitude_min='07', longitude_sec='23.1'
    """
    result = {}
    if not raw:
        return {
            "latitude_deg": "", "latitude_min": "", "latitude_sec": "",
            "longitude_deg": "", "longitude_min": "", "longitude_sec": "",
        }

    # Match: DD'MM'SS.S" format (with optional quotes, spaces, etc.)
    # Pattern: digits, apostrophe, digits, apostrophe, digits with optional decimals
    coord_pattern = r"(\d+)['\s]+(\d+)['\s]+(\d+(?:\.\d+)?)"

    coords = re.findall(coord_pattern, raw)

    if len(coords) >= 2:
        # First match = latitude, second = longitude
        lat_deg, lat_min, lat_sec = coords[0]
        lon_deg, lon_min, lon_sec = coords[1]

        result["latitude_deg"] = lat_deg
        result["latitude_min"] = lat_min
        result["latitude_sec"] = lat_sec
        result["longitude_deg"] = lon_deg
        result["longitude_min"] = lon_min
        result["longitude_sec"] = lon_sec
    else:
        # Default to empty if parsing fails
        result["latitude_deg"] = ""
        result["latitude_min"] = ""
        result["latitude_sec"] = ""
        result["longitude_deg"] = ""
        result["longitude_min"] = ""
        result["longitude_sec"] = ""

    return result


def parse_scales(scale_page3: str, scale_page4_top: str, scale_page4_bottom_vert: str, scale_page4_bottom_horiz: str) -> Dict[str, str]:
    """
    Parse evaluator-provided scales from intake form columns AA-AD.

    Inputs:
    - scale_page3: Site plan scale (e.g. "1 inch = 100 feet")
    - scale_page4_top: Septic system plan scale (e.g. "1 inch = 10 feet")
    - scale_page4_bottom_vert: Cross-section vertical scale (e.g. "1 inch = 2.5 feet")
    - scale_page4_bottom_horiz: Cross-section horizontal scale (e.g. "1 inch = 5 feet")

    Returns dict with validated scale factors.
    """
    from scale_parser import parse_scale

    result = {}

    # Page 3 site plan scale
    page3_factor = parse_scale(scale_page3) if scale_page3 else None
    result["scale_page3_inches_per_feet"] = str(page3_factor) if page3_factor else "0.1"  # Default 1"=10'

    # Page 4 top (septic plan) scale
    page4_top_factor = parse_scale(scale_page4_top) if scale_page4_top else None
    result["scale_page4_top_inches_per_feet"] = str(page4_top_factor) if page4_top_factor else "0.1"  # Default 1"=10'

    # Page 4 bottom vertical scale
    page4_vert_factor = parse_scale(scale_page4_bottom_vert) if scale_page4_bottom_vert else None
    result["scale_page4_bottom_vertical_inches_per_feet"] = str(page4_vert_factor) if page4_vert_factor else "0.4"  # Default 1"=2.5'

    # Page 4 bottom horizontal scale
    page4_horiz_factor = parse_scale(scale_page4_bottom_horiz) if scale_page4_bottom_horiz else None
    result["scale_page4_bottom_horizontal_inches_per_feet"] = str(page4_horiz_factor) if page4_horiz_factor else "0.2"  # Default 1"=5'

    return result


def derive_missing(fields: Dict[str, str]) -> Dict[str, str]:
    """
    Fill all remaining fields defined in field_map.yaml that are still
    absent or empty after the prior parsing passes.
    """
    filled = dict(fields)

    # Acres → sqft (1 acre = 43,560 sq ft)
    acres_val = filled.get("acreage", "")
    if acres_val:
        try:
            acres_float = float(acres_val)
            sqft = int(acres_float * 43560)
            filled.setdefault("lot_size_sqft",    str(sqft))
            filled.setdefault("lot_size_acres",   str(acres_float))
        except ValueError:
            filled.setdefault("lot_size_sqft",   "")
            filled.setdefault("lot_size_acres",  acres_val)
    else:
        filled.setdefault("lot_size_sqft",   "")
        filled.setdefault("lot_size_acres",  "")

    # Shoreland zoning — blank in source
    filled.setdefault("shoreland_zoning", "")

    # System to serve
    use_val = filled.get("use", "Single Family Dwelling")
    filled.setdefault("system_to_serve", use_val.title())

    # Design flow override (already set via parse_use_bedrooms_flow)
    if not filled.get("design_flow_gallons"):
        filled.setdefault("design_flow_gallons", "")

    # Num bedrooms
    filled.setdefault("num_bedrooms", filled.get("bedrooms", ""))

    # Current use — seasonal use field
    seasonal = filled.get("seasonal_use", "")
    filled.setdefault("current_use", seasonal)

    # Disposal field type from disposal_system_type
    dst = filled.get("disposal_system_type", "")
    filled.setdefault("disposal_field_type", dst)

    # Dose (engineered systems) — not applicable for gravity system
    filled.setdefault("dose_gallons", "N/A")

    # Garbage disposal unit — not mentioned, default to "No"
    filled.setdefault("garbage_disposal_unit", "No")

    # Installer — not provided; leave blank
    filled.setdefault("installer_name",  "")
    filled.setdefault("installer_phone", "")

    # Owner/Applicant signature block
    owner = filled.get("owner_name", "")
    filled.setdefault("property_owner_signature", owner)
    filled.setdefault("property_owner_date",     "03/01/2026")
    filled.setdefault("owner_applicant_statement", "I hereby certify the information contained in this application is true and accurate.")

    # Evaluator fields page 3
    eval_name = filled.get("evaluator_name", "")
    eval_lpi  = filled.get("lpi_number",        "")
    filled.setdefault("evaluator_name_page3",    eval_name)
    filled.setdefault("evaluator_se_number",      eval_lpi)
    filled.setdefault("evaluator_date_page3",    "03/01/2026")

    # Page 6 SE# / Date
    filled.setdefault("se_number_page6",   eval_lpi)
    filled.setdefault("se_date_page6",     "03/01/2026")

    # Scale — separate scales for cross-section and plan view
    # Cross-section: vertical and horizontal (feet per inch)
    # Plan view: feet per inch
    filled.setdefault("cross_section_vertical_scale_ft_per_in",   "2.5")   # 1" = 2.5 ft
    filled.setdefault("cross_section_horizontal_scale_ft_per_in",  "5.0")  # 1" = 5 ft
    filled.setdefault("plan_view_scale_ft_per_in",                "10.0")  # 1" = 10 ft

    # Soil observation hole fields — not available in source
    filled.setdefault("oh1_organic_thickness",           "")
    filled.setdefault("oh1_ground_surface_elevation",     "")
    filled.setdefault("oh1_depth_to_exploration",         "")
    filled.setdefault("oh2_organic_thickness",            "")
    filled.setdefault("oh2_ground_surface_elevation",    "")
    filled.setdefault("oh2_depth_to_exploration",        "")

    # Soil classification — derive from soil type
    soil_type = filled.get("soil_type", "")
    filled.setdefault("soil_classification_hole1",  soil_type)
    filled.setdefault("soil_classification_hole2",  soil_type)
    filled.setdefault("soil_classification_p4_hole1", soil_type)
    filled.setdefault("soil_classification_p4_hole2", soil_type)

    # Slope — not provided in source
    filled.setdefault("slope_hole1",     "")
    filled.setdefault("slope_hole2",     "")
    filled.setdefault("slope_p4_hole1",  "")
    filled.setdefault("slope_p4_hole2",  "")

    # Bedrock depth — not mentioned, leave blank
    filled.setdefault("bedrock_depth_hole1",   "")
    filled.setdefault("bedrock_depth_hole2",   "")
    filled.setdefault("bedrock_depth_p4_hole1", "")
    filled.setdefault("bedrock_depth_p4_hole2", "")

    # Backfill depths — from parsed distances
    filled.setdefault("depth_backfill_upslope",    filled.get("backfill_upslope_inches", ""))
    filled.setdefault("depth_backfill_downslope",  filled.get("backfill_downslope_inches", ""))
    filled.setdefault("backfill_depth_upslope_p6",  filled.get("backfill_upslope_inches", ""))
    filled.setdefault("backfill_depth_downslope_p6", filled.get("backfill_downslope_inches", ""))

    # Issuing municipality — not in source, leave blank
    filled.setdefault("issuing_municipality", "")

    # Permit number — not in source, leave blank
    filled.setdefault("permit_number", "")

    # Date issued
    filled.setdefault("date_issued", "03/01/2026")

    # Municipal tax map
    filled.setdefault("municipal_tax_map", filled.get("map_number", ""))

    # Applicant name — same as owner when not separately provided
    if not filled.get("applicant_name"):
        filled["applicant_name"] = filled.get("owner_name", "")

    # Mailing city (same as property city if blank)
    if not filled.get("mailing_city"):
        filled["mailing_city"] = filled.get("town", "")

    # Email — blank in source
    filled.setdefault("email", "")

    # Site notes — already set via parse_septic_tank
    filled.setdefault("site_notes",  filled.get("site_notes", ""))
    filled.setdefault("special_notes", RAW_ROW.get("Special Notes", ""))

    return filled


# ── main parse function ──────────────────────────────────────────────────────
def parse_sheet_row(row: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Parse the Google Sheets row into a flat dict matching field_map.yaml keys.
    """
    raw = row if row is not None else RAW_ROW

    fields: Dict[str, str] = {}

    # ── 1. Client / owner ──────────────────────────────────────────────
    client = parse_client_address(raw.get("Client name, Phone number, and Address", ""))
    fields.update(client)

    # ── 2. Property location ─────────────────────────────────────────────
    prop = parse_property_location(raw.get("Property Location Details", ""))
    fields.update(prop)

    # ── 3. Map / Lot / Acreage ────────────────────────────────────────────
    mla = parse_map_lot_acreage(raw.get("Map and Lot # and Acreage", ""))
    fields.update(mla)

    # ── 4. Evaluator ─────────────────────────────────────────────────────
    ev = parse_evaluator_info(raw.get("Site Evaluator's Information", ""))
    fields.update(ev)

    # ── 5. Use / Bedrooms / Flow ─────────────────────────────────────────
    ubf = parse_use_bedrooms_flow(raw.get("Use and bedrooms/flow", ""))
    fields.update(ubf)

    # ── 6. Seasonal use ──────────────────────────────────────────────────
    fields["seasonal_use"] = raw.get("Seasonal use", "").strip()

    # ── 7. Shoreland zoning ──────────────────────────────────────────────
    fields["shoreland_zoning"] = raw.get("Shoreland zoning", "").strip()

    # ── 7b. GPS Coordinates ───────────────────────────────────────────────
    gps = parse_gps_coordinates(raw.get("GPS Coordinates", ""))
    fields.update(gps)

    # ── 8. Water supply ───────────────────────────────────────────────────
    ws = parse_water_supply(raw.get("Water supply and well", ""))
    fields.update(ws)

    # ── 9. Soil summary ──────────────────────────────────────────────────
    soil = parse_soil_by_depth(raw.get("Soil summary at disposal area", ""))
    fields.update(soil)

    # ── 10. Limiting factor ───────────────────────────────────────────────
    lf = parse_limiting_factor(raw.get("Limiting factor", ""))
    fields.update(lf)

    # ── 11. Disposal system type ──────────────────────────────────────────
    fields["disposal_system_type"] = raw.get("Disposal system type", "").strip()
    # Map disposal_system_type → disposal_field_type (field_map uses disposal_field_type on page 2)
    fields["disposal_field_type"] = raw.get("Disposal system type", "").strip()

    # ── 12. Septic tank ───────────────────────────────────────────────────
    st = parse_septic_tank(raw.get("Septic tank setup", ""))
    fields.update(st)

    # ── 13. Design flow override ──────────────────────────────────────────
    dfo_raw = raw.get("Design flow override", "")
    dfo_num = _parse_number(dfo_raw)
    if dfo_num:
        fields.setdefault("design_flow_gallons", dfo_num)

    # ── 14. Planned field size ────────────────────────────────────────────
    fields["planned_field_size"] = raw.get("Planned field size and layout (if known)", "").strip()
    fl = parse_field_layout(fields["planned_field_size"])
    fields.update(fl)
    
    # ── 15. Elevations ───────────────────────────────────────────────────
    erp = parse_elevation_reference(
        raw.get("Elevation reference point (ERP) and elevations (if known)", "")
    )
    fields.update(erp)

    # ── 16. Key distances / setbacks ─────────────────────────────────────
    dist = parse_distances(raw.get("Key distances between features", ""))
    fields.update(dist)

    # ── 17. Foundation type ───────────────────────────────────────────────
    ft = parse_foundation_type(raw.get("Foundation Type", ""))
    fields.update(ft)

    # ── 18. Variance declarations ─────────────────────────────────────────
    var = parse_variance_types(raw.get("Requesting any variances?", ""))
    fields.update(var)

    # ── 19. Submission timestamp ─────────────────────────────────────────
    fields["submission_timestamp"] = raw.get("Timestamp", "").strip()
    # Date from timestamp
    date_m = re.search(r"(\d+)/(\d+)/(\d+)", raw.get("Timestamp", ""))
    if date_m:
        month, day, year = date_m.groups()
        fields["date_issued"] = f"{month}/{day}/{year}"
        fields["property_owner_date"]     = f"{month}/{day}/{year}"
        fields["evaluator_date_page3"]    = f"{month}/{day}/{year}"
        fields["se_date_page6"]           = f"{month}/{day}/{year}"

    # ── 20. Drive URL ────────────────────────────────────────────────────
    fields["uploads_url"] = raw.get("Uploads", "").strip()

    # ── 21. Special notes ────────────────────────────────────────────────
    fields["special_notes"] = raw.get("Special Notes", "").strip()

    # ── 22. Evaluator-provided scales ────────────────────────────────────
    scales = parse_scales(
        raw.get("Page 3 Site Plan Scale", ""),
        raw.get("Page 4 Top (Septic Plan) Scale", ""),
        raw.get("Page 4 Bottom Cross-Section Vertical Scale", ""),
        raw.get("Page 4 Bottom Cross-Section Horizontal Scale", "")
    )
    fields.update(scales)

    # ── 23. Derive all remaining fields ───────────────────────────────────
    fields = derive_missing(fields)

    return fields


# ── build field dict that mirrors field_map keys ─────────────────────────────
def build_field_dict(raw: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Returns a flat dict keyed on field_map.yaml field names with values
    populated from the Google Sheet row.
    """
    parsed = parse_sheet_row(raw)

    # Load field_map.yaml to get the canonical key list
    with open(MAP_PATH) as fh:
        field_map = yaml.safe_load(fh)

    # Start with all keys from field_map, defaulting to empty string
    result: Dict[str, str] = {k: "" for k in field_map}

    # Map parsed keys → field_map keys (some renaming needed)
    key_mapping = {
        # Explicit renames
        "evaluator_license_number": "lpi_number",
        "design_flow_gallons":      "design_flow_gallons",
        "mailing_state":            "mailing_state",
        "mailing_zip":              "mailing_zip",
        # soil
        "soil_type":                "soil_classification_hole1",
        # elevations page 5
        "finished_grade_elevation": "finished_grade_elevation",
        "top_of_distribution_pipe_elevation": "top_of_distribution_pipe_elevation",
        "bottom_of_disposal_field_elevation": "bottom_of_disposal_field_elevation",
    }

    for fm_key, src_key in key_mapping.items():
        if src_key in parsed and fm_key in result:
            result[fm_key] = parsed[src_key]

    # Direct copy for all keys that already match
    for key, value in parsed.items():
        if key in result:
            result[key] = value

    return result


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    import subprocess

    print("Parsing Google Sheet row…")
    fields = build_field_dict()

    print(f"\nParsed field dictionary ({len(fields)} fields):")
    print(json.dumps(fields, indent=2))

    # Run fill_form
    print("\nRunning fill_form.py…")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "fill_form.py")],
            env={**__import__("os").environ, "FILL_FORM_FIELDS": json.dumps(fields)},
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as exc:
        print(f"fill_form.py error: {exc}")

    print(f"\nOutput PDF: {OUTPUT_PDF}")