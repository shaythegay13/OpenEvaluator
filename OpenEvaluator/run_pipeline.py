#!/usr/bin/env python3
"""
Pipeline runner for Site Evaluator submission:
  1. Generate site plan PNG drawings (site_plan_generator.py)
  2. Fill HHE-200-2025.pdf with row data → HHE-200-filled.pdf
  3. Upload PDF + DXF to Google Drive
"""

from __future__ import annotations
import sys, os, re, json, math
from pathlib import Path

_STANDARD_SCALES = [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200]

def _pick_scale_val(max_ft: float, fig_w: float, n_cols: int = 16) -> int:
    cells_per_inch = n_cols / fig_w
    usable_cells   = n_cols - 2
    for s in _STANDARD_SCALES:
        if (s / cells_per_inch) * usable_cells >= max_ft:
            return s
    return _STANDARD_SCALES[-1]

sys.path.insert(0, str(Path(__file__).parent))
from acro_fill import fill_acro
from integrate_professional_drawings import generate_professional_drawings

OUTPUT_DIR = Path(__file__).parent

# ── Sheet data (first data row) ─────────────────────────────────────────────
ROW = {
    "Timestamp": "3/1/2026 11:17:21",
    "Client name, Phone number, and Address": "Kristen Marquis, empty, empty",
    "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
    "Map and Lot # and Acreage": "26, 18, 2.35",
    "Site Evaluator's Information": (
        "George Bouchles, 338, 207-240-5567, "
        "gsb@cadmasterr.com, Cadmasterr Drafting & Land Surveying"
    ),
    "Application Type": "Replacement system",
    "Use and bedrooms/flow": "single family dwelling, 3 bedroom home, 270 gallons per day",
    "Seasonal use": "Year-round",
    "Shoreland zoning": "",
    "Water supply and well": "existing drilled well, private, 125 ft.",
    "Soil summary at disposal area": (
        "brown fine sandy loam to 3 inches, "
        "yellowish brown fine sandy loam from 3 inches to 24 inches, "
        "olive gray fine sandy loam to pit depth of 36 inches,"
    ),
    "Limiting factor": "limiting factor is ground water at 24 inches",
    "Disposal system type": "Eljen-in Drain",
    "Septic tank setup": (
        "existing 1,000 gallon septic tank shall be exposed, "
        "inspected for structural integrity. if need, tank shall be "
        "replaced. outlet baffle shall be inspected and replaced if necessary."
    ),
    "Design flow override": "270 gallons per day",
    "Planned field size and layout (if known)": (
        "3 rows of 7 eljen-in-drain GSF-B43 Modules, 21 units total, "
        "11'x28' cluster formation."
    ),
    "Key distances between features": (
        "house to tank = 8', tank to field may vary, "
        "field to well 100 feet minimum, unknown"
    ),
    "Elevation reference point (ERP) and elevations (if known)": (
        'ERP = nail set 12 inches above grade in 6" maple tree, '
        'finish grade elevation = 0", top of pipe = -12", '
        'bottom of proprietary device = -24", bottom of disposal area = -30"'
    ),
    "Uploads": "https://drive.google.com/open?id=1Tg5V7uI99qcUgqIjQAlrqrASexL7B5yA",
    "Latitude": "44 15 30",
    "Longitude": "70 14 45",
    "Special Notes": "System replacement due to aging tank",
}

# ── Helpers ─────────────────────────────────────────────────────────────────

def normalize_blank(val):
    if not val:
        return ""
    v = str(val).strip().lower()
    if v in ("empty", "none", "n/a", "na", "null", "---"):
        return ""
    return str(val).strip()


def parse_dms(s):
    if not s or s.strip().lower() in ("", "empty", "none"):
        return "", "", ""
    parts = s.strip().split()
    return (parts[0] if parts else "",
            parts[1] if len(parts) > 1 else "",
            parts[2] if len(parts) > 2 else "")


def extract_elev(text, key):
    m = re.search(rf"{re.escape(key)}\s*=\s*=?\s*([-+]?\d+)", text, re.I)
    return m.group(1).lstrip('+') if m else ""


def fmt_last_first(name):
    parts = name.strip().split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else name


def parse_field_layout(raw):
    """Parse disposal field layout text into structured dict."""
    result = {
        "num_rows": 3, "mods_per_row": 7, "mod_len": 4.0, "mod_wid": 3.67,
        "cluster_w": 11.0, "cluster_l": 28.0, "total_mods": 21,
        "description": raw, "brand": "",
    }
    m = re.search(r"(\d+)\s*row", raw, re.I)
    if m:
        result["num_rows"] = int(m.group(1))
    m = re.search(r"(\d+)\s*(?:eljen|gsf|infiltrator|module|unit)", raw, re.I)
    if m:
        result["total_mods"] = int(m.group(1))
        if result["num_rows"] > 0:
            result["mods_per_row"] = result["total_mods"] // result["num_rows"]
    # Cluster dimensions: e.g. "11'x28'"
    m = re.search(r"(\d+(?:\.\d+)?)'?\s*x\s*(\d+(?:\.\d+)?)'", raw)
    if m:
        result["cluster_w"] = float(m.group(1))
        result["cluster_l"] = float(m.group(2))
        if result["num_rows"] > 0:
            result["mod_wid"] = result["cluster_w"] / result["num_rows"]
        if result["mods_per_row"] > 0:
            result["mod_len"] = result["cluster_l"] / result["mods_per_row"]
    # Brand
    for brand in ("eljen", "infiltrator", "biodiffuser", "presby", "geomat"):
        if brand in raw.lower():
            result["brand"] = brand.capitalize()
            break
    return result


def parse_soil_layers(soil_summary):
    """Parse comma-separated soil description into structured layer list."""
    layers = []
    # Split carefully around depth transitions
    segments = re.split(r',\s*(?=(?:from\s+)?\d)', soil_summary)
    # Fallback to simple comma split
    if len(segments) <= 1:
        segments = [s.strip().rstrip(',') for s in soil_summary.split(',') if s.strip()]

    for i, seg in enumerate(segments):
        seg = seg.strip().rstrip(',')
        if not seg:
            continue
        # Color identification
        if re.search(r'yellowish\s*brown|yell\w*\s+brn', seg, re.I):
            color = "Yellowish Brown"
        elif re.search(r'olive\s*gray|olive\s*grey', seg, re.I):
            color = "Olive Gray"
        elif re.search(r'light\s+brown', seg, re.I):
            color = "Light Brown"
        elif re.search(r'dark\s+brown', seg, re.I):
            color = "Dark Brown"
        elif re.search(r'gray|grey', seg, re.I):
            color = "Gray"
        elif re.search(r'brown', seg, re.I):
            color = "Brown"
        else:
            color = "Brown"
        # Texture
        if re.search(r'fine\s+sandy\s+loam', seg, re.I):
            texture = "FSL"
        elif re.search(r'sandy\s+loam', seg, re.I):
            texture = "SL"
        elif re.search(r'loamy\s+sand', seg, re.I):
            texture = "LS"
        elif re.search(r'clay\s+loam', seg, re.I):
            texture = "CL"
        elif re.search(r'loam', seg, re.I):
            texture = "L"
        elif re.search(r'sand', seg, re.I):
            texture = "S"
        else:
            texture = "FSL"
        # Depth range
        dm = re.search(r'(?:from\s+)?(\d+)\s*inches?\s+to\s+(?:pit\s+depth\s+of\s+)?(\d+)', seg, re.I)
        if dm:
            top_d = int(dm.group(1))
            bot_d = int(dm.group(2))
        else:
            tm = re.search(r'to\s+(\d+)\s*inch', seg, re.I)
            if tm:
                top_d = layers[-1]["bot"] if layers else 0
                bot_d = int(tm.group(1))
            else:
                top_d = layers[-1]["bot"] if layers else 0
                bot_d = top_d + 12
        layers.append({
            "top": top_d, "bot": bot_d,
            "color": color, "texture": texture,
            "consistence": "Friable" if i < len(segments) - 1 else "",
        })
    return layers


def build_oh1_fields(layers, limit_depth_str):
    """Build observation hole 1 AcroForm field dict from soil layers."""
    lf = int(limit_depth_str) if limit_depth_str.isdigit() else 24
    pit_depth = max(l["bot"] for l in layers) if layers else 36

    textures = "\n".join(l["texture"] for l in layers) if layers else "FSL"
    colors = "\n".join(l["color"] for l in layers) if layers else "Brown"
    consistence = "\n".join(l.get("consistence", "") for l in layers)
    redox = "\n".join(
        "Mostle" if l["top"] >= lf else "" for l in layers
    )
    # Dominant profile type = deepest layer texture
    profile = layers[-1]["texture"] if layers else "FSL"

    return {
        "oh1_number": "1",
        "oh1_test_pit": "Yes",
        "oh1_boring": "",
        "oh1_organic_thickness": "2",
        "oh1_ground_surface": "0",
        "oh1_depth_exploration": str(pit_depth),
        "oh1_textures": textures,
        "oh1_consistence": consistence,
        "oh1_color": colors,
        "oh1_redox": redox,
        "oh1_profile": profile,
        "oh1_condition": "Moist",
        "oh1_slope": "",
        "oh1_limiting_factor": "Ground Water",
        "oh1_groundwater_check": "Yes",
        "oh1_restrictive_layer_check": "",
        "oh1_bedrock_check": "",
        "oh1_pit_depth_check": "Yes",
    }


def build_oh2_fields(layers=None, limit_depth_str="24"):
    """Build observation hole 2 AcroForm field dict (optional second hole data)."""
    if not layers:
        # If no second hole data provided, use same as OH1 or leave blank
        return {
            "oh2_number": "2",
            "oh2_test_pit": "",
            "oh2_boring": "",
            "oh2_organic_thickness": "",
            "oh2_ground_surface": "",
            "oh2_depth_exploration": "",
            "oh2_textures": "",
            "oh2_consistence": "",
            "oh2_color": "",
            "oh2_redox": "",
            "oh2_profile": "",
            "oh2_condition": "",
            "oh2_slope": "",
            "oh2_limiting_factor": "",
            "oh2_groundwater_check": "",
            "oh2_restrictive_layer_check": "",
            "oh2_bedrock_check": "",
            "oh2_pit_depth_check": "",
        }

    # If OH2 data is provided, process it like OH1
    lf = int(limit_depth_str) if limit_depth_str.isdigit() else 24
    pit_depth = max(l["bot"] for l in layers) if layers else 36

    textures = "\n".join(l["texture"] for l in layers) if layers else ""
    colors = "\n".join(l["color"] for l in layers) if layers else ""
    consistence = "\n".join(l.get("consistence", "") for l in layers)
    redox = "\n".join(
        "Mostle" if l["top"] >= lf else "" for l in layers
    )
    profile = layers[-1]["texture"] if layers else ""

    return {
        "oh2_number": "2",
        "oh2_test_pit": "Yes",
        "oh2_boring": "",
        "oh2_organic_thickness": "",
        "oh2_ground_surface": "",
        "oh2_depth_exploration": str(pit_depth) if pit_depth else "",
        "oh2_textures": textures,
        "oh2_consistence": consistence,
        "oh2_color": colors,
        "oh2_redox": redox,
        "oh2_profile": profile,
        "oh2_condition": "Moist",
        "oh2_slope": "",
        "oh2_limiting_factor": "Ground Water",
        "oh2_groundwater_check": "Yes",
        "oh2_restrictive_layer_check": "",
        "oh2_bedrock_check": "",
        "oh2_pit_depth_check": "",
    }


# ── Parse ROW ────────────────────────────────────────────────────────────────

# Location
loc_parts = [p.strip() for p in ROW["Property Location Details"].split(",")]
street = loc_parts[0] if loc_parts else ""
city = loc_parts[1].strip() if len(loc_parts) > 1 else ""
zip_m = re.search(r'\b(\d{5})\b', ROW["Property Location Details"])
zip_code = zip_m.group(1) if zip_m else ""
sm = re.match(r'^(\d+[A-Za-z]?)\s+(.+)$', street)
street_number = sm.group(1) if sm else ""
street_name_only = sm.group(2) if sm else street

# Map/lot/acreage
mla = [p.strip() for p in ROW["Map and Lot # and Acreage"].split(",")]
tax_map = mla[0] if mla else ""
lot_num = mla[1] if len(mla) > 1 else ""
acreage = mla[2] if len(mla) > 2 else ""

# Client
client_parts = [p.strip() for p in ROW["Client name, Phone number, and Address"].split(",")]
client_name = client_parts[0] if client_parts else ""
client_phone = normalize_blank(client_parts[1] if len(client_parts) > 1 else "")
owner_name_formatted = fmt_last_first(client_name)

# Evaluator
ep = [p.strip() for p in ROW["Site Evaluator's Information"].split(",")]
evaluator_name = ep[0] if ep else ""
evaluator_lic = ep[1] if len(ep) > 1 else ""
evaluator_phone = ep[2] if len(ep) > 2 else ""
evaluator_email = ep[3] if len(ep) > 3 else ""

# Use / bedrooms / flow
ubf = [p.strip() for p in ROW["Use and bedrooms/flow"].split(",")]
bedrooms = re.sub(r"[^\d]", "", ubf[1]) if len(ubf) > 1 else "3"
bedrooms = bedrooms or "3"
design_flow_raw = ROW["Design flow override"]
df_m = re.search(r"(\d+)", design_flow_raw)
design_flow_gpd = df_m.group(1) if df_m else "270"

# Water supply / shoreland
water_raw = ROW["Water supply and well"]
water_type = water_raw.split(",")[0].strip() if water_raw else ""
shoreland_yn = ROW.get("Shoreland zoning", "").strip() or "No"

# Soil
soil_summary = ROW["Soil summary at disposal area"].strip()
limiting_factor_raw = ROW["Limiting factor"].strip()
lf_m = re.search(r"(\d+)\s*inches", limiting_factor_raw)
limiting_depth = lf_m.group(1) if lf_m else "24"
soil_layers = parse_soil_layers(soil_summary)
oh1_fields = build_oh1_fields(soil_layers, limiting_depth)
# For now, OH2 is empty (no second hole data in test data)
oh2_fields = build_oh2_fields()

# Elevations
erp_raw = ROW["Elevation reference point (ERP) and elevations (if known)"]
finished_grade_str = extract_elev(erp_raw, "finish grade elevation") or "0"
top_of_pipe_str = extract_elev(erp_raw, "top of pipe") or "-12"
bottom_disposal_str = extract_elev(erp_raw, "bottom of disposal area") or "-30"

# ERP description
erp_desc_m = re.match(r"ERP\s*=\s*(.+?)(?:,\s*finish|\Z)", erp_raw, re.I | re.S)
erp_location = erp_desc_m.group(1).strip().upper() if erp_desc_m else "NAIL IN MAPLE TREE"

# Backfill: ERP nail is 12" above natural grade, finished grade = 0" (ERP level)
erp_height_above_grade = 12  # inches
backfill_upslope = str(erp_height_above_grade)
backfill_downslope = str(erp_height_above_grade)

# Limiting factor elevation relative to ERP
try:
    lf_elev = str(-erp_height_above_grade - int(limiting_depth))  # e.g. -12 - 24 = -36
except Exception:
    lf_elev = ""

# Field layout
field_raw = ROW["Planned field size and layout (if known)"]
field_info = parse_field_layout(field_raw)
cluster_sqft = int(field_info["cluster_w"] * field_info["cluster_l"])

# Tank
tank_m = re.search(r'([\d,]+)\s*gallon', ROW.get("Septic tank setup", ""), re.I)
tank_cap = tank_m.group(1).replace(",", "") if tank_m else "1000"

# Application type / replacement
app_type_raw = ROW.get("Application Type", "").lower()
setup_text = ROW.get("Septic tank setup", "").lower()
replacement_system_type = ""
if "replacement" in app_type_raw:
    if "cesspool" in setup_text:
        replacement_system_type = "Cesspool"
    elif "septic" in setup_text or "conventional" in setup_text:
        replacement_system_type = "Conventional Septic System"

year_installed = ""
for src in (ROW.get("Special Notes", ""), ROW.get("Septic tank setup", "")):
    ym = re.search(r'\b(19|20)\d{2}\b', src)
    if ym:
        year_installed = ym.group(0)
        break

# Disposal field type
disposal_type_raw = ROW.get("Disposal system type", "").lower()
_engineered_kws = ("eljen", "infiltrator", "biodiffuser", "presby", "geomat", "proprietary")
is_engineered = any(k in disposal_type_raw for k in _engineered_kws)

def map_disposal_type(raw):
    r = raw.lower().strip()
    if "stone bed" in r:
        return "Stone Bed"
    if "stone trench" in r or "trench" in r:
        return "Stone Trench"
    if any(k in r for k in _engineered_kws):
        return "Proprietary Device"
    return "Other"

def map_prop_subtype(layout):
    r = layout.lower()
    if "cluster" in r:
        return "Cluster Array"
    if "linear" in r:
        return "Linear"
    return "Cluster Array"

disposal_field_type_val = map_disposal_type(disposal_type_raw)
proprietary_subtype = map_prop_subtype(field_raw) if is_engineered else ""

# Distances
dist_raw = ROW["Key distances between features"]
field_to_well_str = ""
for seg in dist_raw.split(","):
    if "field to well" in seg.lower():
        nm = re.search(r"(\d+)", seg)
        if nm:
            field_to_well_str = nm.group(1)
field_to_well = float(field_to_well_str) if field_to_well_str.isdigit() else 100.0

# Drive folder
folder_id = ROW["Uploads"].split("id=")[-1].split("&")[0]

# GPS
lat_deg, lat_min, lat_sec = parse_dms(ROW.get("Latitude", ""))
lon_deg, lon_min, lon_sec = parse_dms(ROW.get("Longitude", ""))

# Limiting factor elevation
limiting_factor_elev_calc = ""
try:
    limiting_factor_elev_calc = str(int(finished_grade_str) - int(limiting_depth))
except Exception:
    pass

# ── Scale pre-calculation (matches site_plan_generator logic) ────────────────
acres_f = float(acreage) if acreage else 2.35
lot_w_ft_calc = math.sqrt(acres_f * 43560)
max_ft_pg3 = max(lot_w_ft_calc, field_to_well * 2.0, 200.0)
scale_pg3   = _pick_scale_val(max_ft_pg3, 5.76)   # matches generate_site_plan_pg3

max_ft_xsect  = max(field_info["cluster_l"] * 2.0, 40.0)
scale_pg4_horiz = _pick_scale_val(max_ft_xsect, 8.375)  # matches generate_cross_section_pg4

print(f"Drive folder ID: {folder_id}")

# ── Step 1: Generate site plan drawings ─────────────────────────────────────

drawing_data = {
    # Identity
    "owner_name":      owner_name_formatted,
    "address_line":    f"{street}, {city}, ME {zip_code}",
    "road_name":       street_name_only,
    "street_name":     street_name_only,
    "town":            city,
    "tax_map":         tax_map,
    "lot_number":      lot_num,
    "acreage":         float(acreage) if acreage else 2.35,
    "tank_cap":        tank_cap,
    "se_number":       evaluator_lic,
    "se_date":         "03/01/2026",
    "evaluator_name":  evaluator_name,
    # Field layout (structured)
    "planned_field":   field_raw,
    "num_rows":        field_info["num_rows"],
    "mods_per_row":    field_info["mods_per_row"],
    "mod_len":         field_info["mod_len"],
    "mod_wid":         field_info["mod_wid"],
    "cluster_w":       field_info["cluster_w"],
    "cluster_l":       field_info["cluster_l"],
    "brand":           field_info.get("brand", "Eljen"),
    # Distances
    "key_distances":   dist_raw,
    "field_to_well":   field_to_well,
    "field_to_house":  20.0,
    "tank_to_house":   8.0,
    # Elevations (inches relative to ERP)
    "elevation_raw":        erp_raw,
    "finished_grade_in":    int(finished_grade_str) if finished_grade_str.lstrip('-').isdigit() else 0,
    "top_pipe_in":          int(top_of_pipe_str) if top_of_pipe_str.lstrip('-').isdigit() else -12,
    "bottom_field_in":      int(bottom_disposal_str) if bottom_disposal_str.lstrip('-').isdigit() else -30,
    "erp_height_above_grade": erp_height_above_grade,
    "limiting_factor":       limiting_depth,
    "erp_location":          erp_location,
    # Soil layers
    "soil_layers":     soil_layers,
}

print("Generating professional CAD drawings…")
# Pass full ROW data for property research, plus system design data
site_plan_png, locus_map_png, disposal_plan_png, cross_section_png = \
    generate_professional_drawings(ROW, drawing_data, output_dir=str(OUTPUT_DIR))
print(f"  ✓ site_plan_pg3.png: {Path(site_plan_png).name}")
print(f"  ✓ locus_map.png: {Path(locus_map_png).name}")
print(f"  ✓ disposal_plan_pg4.png: {Path(disposal_plan_png).name}")
print(f"  ✓ cross_section_pg4.png: {Path(cross_section_png).name}")

# ── Step 2: Build AcroForm fields ────────────────────────────────────────────

fields = {
    # ── Page 1 ─────────────────────────────────────────────────────────────
    "street_number":            street_number,
    "street_name":              street_name_only,
    "town":                     city,
    "map_number":               tax_map,
    "lot_number":               lot_num,
    "owner_name":               owner_name_formatted,
    "applicant_name":           owner_name_formatted,
    "mailing_street":           street,
    "mailing_city":             city,
    "mailing_state":            "ME",
    "mailing_zip":              zip_code,
    "owner_phone":              client_phone,
    "owner_email":              "",
    "property_owner_signature_date": "03/01/2026",
    "installer_name":           "",
    "installer_phone":          "",
    "installer_email":          "",
    "issuing_municipality":     city,
    "permit_number":            "",
    "permit_issued_date":       "",
    "lpi_number":               evaluator_lic,
    "lpi_inspection1_date":     "",
    "lpi_inspection2_date":     "",
    "fee_area":                 "",
    "total_fee":                "",
    "town_share":               "",
    "state_25_pct":             "",
    "dep_wqs":                  "",
    "revision_check":           "",
    "doubled_fee_check":        "",
    "variance_check":           "",
    "seasonal_conversion_check": "",
    "type_of_app":              "Replacement system",
    "system_replaced":          replacement_system_type,
    "year_installed":           year_installed,
    "expansion":                "",
    "variance_requirement":     "No Rule Variance",
    "first_time_system":        "",
    "replacement_variance":     "",
    "treatment_tanks":          "Concrete",
    "tank_regular_check":       "Yes",
    "tank_low_profile_check":   "",
    "tank_h20_check":           "",
    "tank_capacity":            tank_cap,
    "tank_specify_other":       "",
    "tank_cap_gal":             tank_cap,
    "tank_total_new":           "0",
    "tank_notes":               "",
    "risers_required_check":    "Yes",
    "cnes_check":               "",
    "cnes_total_tanks":         "",
    "primitive_limited_check":  "",
    "primitive_limited_type":   "",
    "alt_toilet_check":         "",
    "alt_toilet_type":          "",
    "non_eng_tank_check":       "",
    "non_eng_tank_number":      "",
    "holding_tank_check":       "",
    "non_eng_field_check":      "",
    "ces_check":                "Yes" if is_engineered else "",
    "ces_tanks":                "0",
    "ces_new_tanks":            "0",
    "ces_pumps":                "0",
    "eng_tank_check":           "",
    "eng_tank_number":          "",
    "eng_field_check":          "Yes" if is_engineered else "",
    "misc_components_check":    "",
    "misc_components_specify":  "",
    "pre_treatment_tank_check": "",
    "pre_treatment_comp_check": "",
    "evaluator_name":           evaluator_name,
    "evaluator_phone":          evaluator_phone,
    "se_number":                evaluator_lic,
    "se_signature_date":        "03/01/2026",
    "evaluator_email":          evaluator_email,

    # ── Page 2 ─────────────────────────────────────────────────────────────
    "owner_name_pg2":           owner_name_formatted,
    "address_pg2":              f"{street}, {city}",
    "property_size":            acreage,
    "property_size_units":      "acres",
    "shoreland_zoning_yn":      shoreland_yn,
    "current_use":              ROW.get("Seasonal use", "Year-round"),
    "latitude_deg":             lat_deg,
    "latitude_min":             lat_min,
    "latitude_sec":             lat_sec,
    "longitude_deg":            lon_deg,
    "longitude_min":            lon_min,
    "longitude_sec":            lon_sec,
    "gps_margin_error":         "",
    "water_supply":             water_type,
    "water_supply_specify":     "",
    "effluent_pump":            "No",
    "dose_gallons":             design_flow_gpd,        # FIX: was "dose_engineered"
    "garbage_disposal":         "No",                   # FIX: was "gdu_ynm"
    "gdu_if_yes":               "",
    "disposal_system_to_serve": "Single Family Dwelling", # FIX: was "disposal_system_type"
    "num_bedrooms_opt1":        bedrooms,
    "num_bedrooms_opt2":        "",
    "num_bedrooms_opt3":        "",
    "disposal_field_type":      disposal_field_type_val,
    "proprietary_device_opt":   proprietary_subtype,    # FIX: was "proprietary_device"
    "disposal_field_size":      str(cluster_sqft),      # FIX: was "field_size"
    "disposal_field_size_unit": "sq ft",                # FIX: was "field_size_measurement"
    "design_flow_gpd":          design_flow_gpd,
    "design_flow_type":         "Table 5A (Dwelling Units)",
    "profile_soil_data":        soil_layers[-1]["texture"] if soil_layers else "",
    "condition_soil_data":      "Moist",                # FIX: was "condition_soil"
    "observation_hole_number":  "1",                    # FIX: was "observation_hole"
    "limiting_factor_depth":    limiting_depth,
    "limiting_factor_elevation": limiting_factor_elev_calc, # FIX: was "limiting_factor_elev"
    "additional_notes":         normalize_blank(ROW.get("Special Notes", "")),
    "pre_treatment_make1":      "",
    "pre_treatment_model1":     "",
    "pre_treatment_notes1":     "",
    "pre_treatment_make2":      "",
    "pre_treatment_model2":     "",
    "pre_treatment_notes2":     "",

    # ── Page 3: Observation Hole 1 (grid variant) ─────────────────────────────
    **oh1_fields,

    # ── Page 3 scale annotation ───────────────────────────────────────────
    "scale_pg3":                str(scale_pg3),

    # ── Page 4: Observation Hole 1 (blank variant, same data as page 3) ────────
    "oh1_number_blank": oh1_fields.get("oh1_number", "1"),
    "oh1_test_pit_blank": oh1_fields.get("oh1_test_pit", "Yes"),
    "oh1_boring_blank": oh1_fields.get("oh1_boring", ""),
    "oh1_organic_thickness_blank": oh1_fields.get("oh1_organic_thickness", "2"),
    "oh1_ground_surface_blank": oh1_fields.get("oh1_ground_surface", "0"),
    "oh1_depth_exploration_blank": oh1_fields.get("oh1_depth_exploration", "36"),
    "oh1_textures_blank": oh1_fields.get("oh1_textures", ""),
    "oh1_consistence_blank": oh1_fields.get("oh1_consistence", ""),
    "oh1_color_blank": oh1_fields.get("oh1_color", ""),
    "oh1_redox_blank": oh1_fields.get("oh1_redox", ""),
    "oh1_profile_blank": oh1_fields.get("oh1_profile", ""),
    "oh1_condition_blank": oh1_fields.get("oh1_condition", ""),
    "oh1_slope_blank": oh1_fields.get("oh1_slope", ""),
    "oh1_limiting_factor_blank": oh1_fields.get("oh1_limiting_factor", ""),
    "oh1_groundwater_check_blank": oh1_fields.get("oh1_groundwater_check", ""),
    "oh1_restrictive_layer_check_blank": oh1_fields.get("oh1_restrictive_layer_check", ""),
    "oh1_bedrock_check_blank": oh1_fields.get("oh1_bedrock_check", ""),
    "oh1_pit_depth_check_blank": oh1_fields.get("oh1_pit_depth_check", ""),

    # ── Observation Hole 2 (optional second hole - both grid and blank variants) ──
    **oh2_fields,

    # ── Page 4 scale annotation ───────────────────────────────────────────
    "scale_pg4":                str(scale_pg4_horiz),
    "backfill_upslope":         backfill_upslope,
    "backfill_downslope":       backfill_downslope,
    "finished_grade_elevation": f'{finished_grade_str}"',
    "top_distribution_pipe":    f'{top_of_pipe_str}"',
    "bottom_disposal_field":    f'{bottom_disposal_str}"',
    "erp_location":             erp_location,
    "erp_reference_elevation":  '0.0"',
    "vertical_scale":           "1",
    "horizontal_scale":         str(scale_pg4_horiz),

    # ── Pages 5-6: Page 4 grid and blank variants (elevation data) ─────────────
    "scale_pg4_grid":           str(scale_pg4_horiz),
    "backfill_upslope_grid":    backfill_upslope,
    "backfill_downslope_grid":  backfill_downslope,
    "finished_grade_elevation_grid": f'{finished_grade_str}"',
    "top_distribution_pipe_grid": f'{top_of_pipe_str}"',
    "bottom_disposal_field_grid": f'{bottom_disposal_str}"',
    "erp_location_grid":        erp_location,
    "erp_reference_elevation_grid": '0.0"',
    "vertical_scale_grid":      "1",
    "horizontal_scale_grid":    str(scale_pg4_horiz),

    "scale_pg4_blank":          str(scale_pg4_horiz),
    "backfill_upslope_blank":   backfill_upslope,
    "backfill_downslope_blank": backfill_downslope,
    "finished_grade_elevation_blank": f'{finished_grade_str}"',
    "top_distribution_pipe_blank": f'{top_of_pipe_str}"',
    "bottom_disposal_field_blank": f'{bottom_disposal_str}"',
    "erp_location_blank":       erp_location,
    "erp_reference_elevation_blank": '0.0"',
    "vertical_scale_blank":     "1",
    "horizontal_scale_blank":   str(scale_pg4_horiz),

    # ── Additional fields ───────────────────────────────────────────────────────
    "gdu_num_tanks":            "",
    "pre_treatment_maint1":     "",
    "pre_treatment_maint2":     "",
    "disposal_field_type_other": "",
    "disposal_system_other":    "",
    "design_flow_calculations": "",
    "site_eval_name_printed":   evaluator_name,
}

# ── Step 3: Fill AcroForm PDF ─────────────────────────────────────────────────

pdf_out = OUTPUT_DIR / "HHE-200-filled.pdf"
try:
    result_pdf = fill_acro(fields, str(pdf_out))
    print(f"✓ Filled PDF → {result_pdf}")
except Exception as e:
    import traceback
    print(f"✗ fill_acro failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ── Step 4: Upload to Google Drive ────────────────────────────────────────────

print("\nUploading files to Google Drive…")
upload_folder_id = "1luOtuHHylbOobofayoWR5FjtVPdUafey"

try:
    sys.path.insert(0, str(Path(__file__).parent / "toolkit" / "scripts"))
    import subprocess
    from gws_bridge import get_valid_token

    access_token = get_valid_token()
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token

    uploaded_links = []
    for filepath in [str(pdf_out)]:
        filename = Path(filepath).name
        result = subprocess.run(
            ["gws", "drive", "+upload", filepath, "--parent", upload_folder_id],
            env=env, capture_output=True, text=True,
        )
        if result.returncode == 0:
            try:
                file_data = json.loads(result.stdout)
                file_id = file_data.get("id", "")
                link = (
                    file_data.get("webViewLink")
                    or file_data.get("alternateLink")
                    or (f"https://drive.google.com/file/d/{file_id}/view" if file_id else "(unavailable)")
                )
            except Exception:
                link = result.stdout.strip() or "(uploaded)"
            uploaded_links.append((filename, link))
            print(f"  ✓ {filename} → {link}")
        else:
            raise RuntimeError(f"{filename}: {result.stderr.strip()}")

    print("\n=== PIPELINE COMPLETE ===")
    print(f"Filled PDF: {pdf_out}")
    print(f"Drive folder: https://drive.google.com/drive/folders/{upload_folder_id}")
    for name, link in uploaded_links:
        print(f"  → {name}: {link}")

except Exception as e:
    print(f"⚠  Upload failed: {e}")
    print(f"Files saved locally:")
    print(f"  PDF: {pdf_out}")
