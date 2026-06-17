#!/usr/bin/env python3
"""
Live pipeline — reads Google Sheet row + hermes_output.json, fills HHE-200-2025.pdf.

Data priority:
  1. hermes_output.json (structured, Hermes-generated) — preferred for complex fields
  2. Raw Google Sheet row parsing — fallback for anything hermes doesn't have
"""
import json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from acro_fill import fill_acro
from sketch_extractor import main as extract_sketches

SCRIPT_DIR  = Path(__file__).parent
CONFIG_AUTH = {
    "credentials": Path.home() / ".config" / "google_oauth_credentials.json",
    "token":       Path.home() / ".config" / "google_token_store.json",
}
LEGACY_AUTH = {
    "credentials": Path.home() / ".hermes" / "google_client_secret.json",
    "token":       Path.home() / ".hermes" / "google_token.json",
}


def _first_existing_path(*paths: Path) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError(f"None of these auth files exist: {[str(p) for p in paths]}")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _auth_block(cred_data: dict) -> dict:
    return cred_data.get("installed") or cred_data.get("web") or cred_data


def _sheet_value(row: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key, "")
        if value not in ("", None):
            return value
    return default


# ── Auth ─────────────────────────────────────────────────────────────────────

def refresh_hermes_token():
    token_path = _first_existing_path(CONFIG_AUTH["token"], LEGACY_AUTH["token"])
    cred_path  = _first_existing_path(CONFIG_AUTH["credentials"], LEGACY_AUTH["credentials"])
    token_data = _load_json(token_path)
    cred_data  = _load_json(cred_path)

    inst = _auth_block(cred_data)
    token_data.setdefault("client_id",     inst["client_id"])
    token_data.setdefault("client_secret", inst["client_secret"])
    token_data.setdefault("token_uri",     inst.get("token_uri", "https://oauth2.googleapis.com/token"))

    refresh = token_data.get("refresh_token")
    if not refresh:
        raise RuntimeError("No refresh_token in token store")

    body = urllib.parse.urlencode({
        "client_id":     token_data["client_id"],
        "client_secret": token_data["client_secret"],
        "refresh_token": refresh,
        "grant_type":    "refresh_token",
    }).encode()

    req = urllib.request.Request(token_data["token_uri"], data=body)
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())

    access_token = result.get("access_token") or token_data.get("access_token")
    os.environ["GOOGLE_WORKSPACE_CLI_TOKEN"] = access_token
    return access_token


def gws(*args: str) -> dict:
    env = os.environ.copy()
    if "GOOGLE_WORKSPACE_CLI_TOKEN" not in env:
        refresh_hermes_token()
    result = subprocess.run(
        ["gws"] + list(args),
        capture_output=True, text=True, timeout=30, env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gws failed: {result.stderr}")
    return json.loads(result.stdout)


# ── Step 0: Load hermes_output.json (primary structured source) ──────────────

hermes: dict = {}
hermes_path = SCRIPT_DIR / "hermes_output.json"
if hermes_path.exists():
    hermes = _load_json(hermes_path)
    print(f"Loaded hermes_output.json (primary data source)")
else:
    print("hermes_output.json not found — using raw sheet parsing only")


def _h(path: str, default: str = "") -> str:
    """Retrieve nested value from hermes dict via dot-path, e.g. 'property.acreage'."""
    if not hermes:
        return default
    val = hermes
    for part in path.split("."):
        if isinstance(val, dict):
            val = val.get(part)
        elif isinstance(val, list) and part.isdigit():
            idx = int(part)
            val = val[idx] if idx < len(val) else None
        else:
            return default
        if val is None:
            return default
    return str(val) if val is not None else default


def _h_layers(hole_idx: int) -> list:
    """Return soil layers for observation hole at hole_idx (0 or 1)."""
    holes = hermes.get("observation_holes", [])
    if hole_idx < len(holes):
        return holes[hole_idx].get("soil_layers", [])
    return []


def _format_soil_col(layers: list, field: str) -> str:
    lines = []
    for layer in layers:
        depth_start = layer.get("depth_start_in", 0)
        depth_end   = layer.get("depth_end_in", 0)
        val         = layer.get(field, "")
        if val:
            lines.append(f'{depth_start}"-{depth_end}": {val}')
    return "\n".join(lines)


# ── Step 1: Read Google Sheet row (for metadata sheet can't easily capture) ──

print("=== LIVE PIPELINE RUN ===")
refresh_hermes_token()

print("Reading sheet row…")

# Allow row selection via command line: python3 live_run_pipeline.py [row_number]
row_num = 2  # default
if len(sys.argv) > 1:
    try:
        row_num = int(sys.argv[1])
        print(f"Reading row {row_num} (from command line argument)")
    except ValueError:
        print(f"Invalid row number: {sys.argv[1]}, using default row 2")

sheet_data = gws(
    "sheets", "spreadsheets", "values", "get",
    "--params", json.dumps({
        "spreadsheetId": "1VHJq0vBMGrme-wmHuPooko0G5JpbfP_o1ZeozjEZ94M",
        "range":         f"Form Responses 1!A{row_num}:W{row_num}",   # A-W includes GPS in col W
    })
)

values = sheet_data.get("values", [])
if not values:
    print("No data rows found in sheet. Exiting.")
    sys.exit(0)

row = values[0]

# Actual Google Form question headers (A-W)
headers = [
    "Timestamp", "Email Address",
    "Client name, Phone number, and Address",
    "Property Location Details", "Map and Lot # and Acreage",
    "Site Evaluator's Information", "Application Type",
    "What will the system serve, and what is the design basis?",
    "Seasonal Use", "Shoreland Zoning",
    "Water supply and Well", "Soil summary at disposal area",
    "Limiting Factor", "Disposal system type", "Septic tank setup",
    "Design flow overflow", "Planned field size and layout (if known)",
    "Key distances between features",
    "Elevation reference point (ERP) and elevations (if known)",
    "Uploads", "Special Notes",
    "Dispersal Area Required (sq. ft.) based on Permeability Class and Design Flow",
    "Latitude and Longitude",
]

while len(row) < len(headers):
    row.append("")

ROW = dict(zip(headers, row))
client_name = ROW["Client name, Phone number, and Address"].split(",")[0].strip()
print(f"Processing: {client_name} — {ROW['Property Location Details']}")

uploads_url = ROW.get("Uploads", "")
drive_id = ""
if "id=" in uploads_url:
    drive_id = uploads_url.split("id=")[-1].split("&")[0].split("?")[0]
print(f"Upload folder ID: {drive_id}")

# Extract sketch data from Drive folder
sketch_data = {}
if drive_id:
    try:
        prop_address = ROW.get("Property Location Details", "")
        print(f"Extracting sketch data from Drive folder {drive_id}...")
        sketch_data = extract_sketches(drive_id, prop_address, dry_run=False)
        print(f"Sketch extraction complete: {len(sketch_data.get('sketch_files', []))} files processed")
    except Exception as e:
        print(f"Warning: Sketch extraction failed: {e}")
        sketch_data = {}

# ── Radio-button value maps ───────────────────────────────────────────────────

def _radio(val: str, mapping: dict) -> str:
    key = val.strip().lower()
    for k, v in mapping.items():
        if key == k.lower():
            return v
    # fuzzy: check if key starts with any map key
    for k, v in mapping.items():
        if key.startswith(k.lower()) or k.lower().startswith(key):
            return v
    return val.strip()


APP_TYPE_MAP = {
    "new construction":            "first time system",
    "first time":                  "first time system",
    "first time system":           "first time system",
    "replacement":                 "replacement system",
    "replacement system":          "replacement system",
    "expansion":                   "Expansion",
    "experimental":                "Experimental System",
    "seasonal conversion":         "Seasonal Conversion Permit",
    "seasonal conversion permit":  "Seasonal Conversion Permit",
}
CURRENT_USE_MAP = {
    "seasonal":    "Seasonal",
    "year-round":  "Year-Round",
    "year round":  "Year-Round",
    "undeveloped": "Undeveloped",
    "commercial":  "Commercial",
}
WATER_SUPPLY_MAP = {
    "drilled well":          "Drilled Well",
    "existing drilled well": "Drilled Well",
    "drilled":               "Drilled Well",
    "private drilled well":  "Drilled Well",
    "dug well":              "Dug/ Point Well",
    "dug/point well":        "Dug/ Point Well",
    "dug":                   "Dug/ Point Well",
    "point well":            "Dug/ Point Well",
    "private":               "Drilled Well",   # default private = drilled
    "public":                "Public",
    "municipal":             "Public",
    "other":                 "Other",
    "drilled_well":          "Drilled Well",
    "dug_well":              "Dug/ Point Well",
}
DISPOSAL_SYSTEM_MAP = {
    "single family dwelling unit":   "Single Family Dwelling Unit",
    "single family dwelling":        "Single Family Dwelling Unit",
    "single family":                 "Single Family Dwelling Unit",
    "sfd":                           "Single Family Dwelling Unit",
    "multiple family dwelling unit": "Multiple Family Dwelling Unit",
    "multi-family":                  "Multiple Family Dwelling Unit",
    "accessory dwelling unit":       "Accessory Dwelling Unit(s)",
    "adu":                           "Accessory Dwelling Unit(s)",
    "other":                         "Other",
}
DISPOSAL_FIELD_TYPE_MAP = {
    "eljen":               "Proprietary Device",
    "eljen-in drain":      "Proprietary Device",
    "eljen in drain":      "Proprietary Device",
    "eljen gsf":           "Proprietary Device",
    "infiltrator":         "Proprietary Device",
    "biodiffuser":         "Proprietary Device",
    "presby":              "Proprietary Device",
    "geomat":              "Proprietary Device",
    "proprietary device":  "Proprietary Device",
    "proprietary":         "Proprietary Device",
    "stone trench":        "Stone Trench",
    "stone bed":           "Stone Bed",
    "other":               "Other",
}
DESIGN_FLOW_MAP = {
    "table 5a":            "Table 5A (Dwelling Units)",
    "table 5c":            "Table 5C",
    "section 5g":          "Section 5(G)",
    "section 5(g)":        "Section 5(G)",
}
PROPERTY_SIZE_UNIT_MAP = {
    "acres":        "acres",
    "acre":         "acres",
    "sq ft":        "sq ft",
    "sqft":         "sq ft",
    "square feet":  "sq ft",
}
SLZ_MAP = {"yes": "Yes", "y": "Yes", "no": "No", "n": "No"}
TANK_MATERIAL_MAP = {
    "concrete":   "Concrete",
    "plastic":    "Plastic",
    "fiberglass": "Plastic",
    "poly":       "Plastic",
    "other":      "Other",
}

# ── Parse helpers ─────────────────────────────────────────────────────────────

def _parse_number(value: str) -> str:
    m = re.search(r"[\d.]+", value)
    return m.group() if m else ""


def _parse_elev(text: str, *patterns) -> str:
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = m.group(1).strip().lstrip("=").strip()
            try:
                float(val)
                return val
            except ValueError:
                return val
    return ""


# ── Parse raw sheet row fields ────────────────────────────────────────────────

# Map / Lot / Acreage
map_lot_raw = _sheet_value(ROW, "Map and Lot # and Acreage")
map_lot_parts = [p.strip() for p in map_lot_raw.split(",")]
tax_map  = map_lot_parts[0] if len(map_lot_parts) > 0 else _h("property.map_number")
lot_num  = map_lot_parts[1] if len(map_lot_parts) > 1 else _h("property.lot_number")
acreage  = map_lot_parts[2] if len(map_lot_parts) > 2 else _h("property.acreage")

# Size units: check if 3rd part is a word (acres/sqft) or a number (value)
size_units = "acres"  # default
if len(map_lot_parts) > 2:
    third = map_lot_parts[2].strip().lower()
    for k, v in PROPERTY_SIZE_UNIT_MAP.items():
        if k in third:
            size_units = v
            break
    # If third part looks like a pure number → it's the value, units are acres
    try:
        float(third.replace("acres", "").replace("sq ft", "").strip())
    except ValueError:
        pass  # non-numeric means it contained unit text, already handled above

# Site Evaluator
ep = [p.strip() for p in _sheet_value(ROW, "Site Evaluator's Information").split(",")]
evaluator_name    = ep[0] if ep else _h("site_evaluator.name")
evaluator_lic     = ep[1] if len(ep) > 1 else _h("site_evaluator.license_number")
evaluator_phone   = ep[2] if len(ep) > 2 else _h("site_evaluator.phone")
evaluator_email   = ep[3] if len(ep) > 3 else _h("site_evaluator.email")

# Client info
client_raw    = _sheet_value(ROW, "Client name, Phone number, and Address")
client_parts  = [p.strip() for p in client_raw.split(",")]
owner_name    = client_parts[0] if client_parts else _h("client.name")
owner_phone   = client_parts[1] if len(client_parts) > 1 else _h("client.phone")
mailing_street = client_parts[2] if len(client_parts) > 2 else ""
mailing_city  = client_parts[3] if len(client_parts) > 3 else ""
mailing_state = ""
mailing_zip   = ""
if len(client_parts) > 4:
    sz = client_parts[4].strip().split()
    mailing_state = sz[0] if sz else ""
    mailing_zip   = sz[1] if len(sz) > 1 else ""

# Strip "empty"/"none" placeholders from mailing fields before fallback check
_MAIL_PLACEHOLDERS = {"empty", "none", "n/a", "unknown"}
for _f in ["mailing_street", "mailing_city", "mailing_state", "mailing_zip"]:
    if locals()[_f].strip().lower() in _MAIL_PLACEHOLDERS:
        locals()[_f]  # read — exec below resets it
mailing_street = "" if mailing_street.strip().lower() in _MAIL_PLACEHOLDERS else mailing_street.strip()
mailing_city   = "" if mailing_city.strip().lower()   in _MAIL_PLACEHOLDERS else mailing_city.strip()
mailing_state  = "" if mailing_state.strip().lower()  in _MAIL_PLACEHOLDERS else mailing_state.strip()
mailing_zip    = "" if mailing_zip.strip().lower()    in _MAIL_PLACEHOLDERS else mailing_zip.strip()

# Note: mailing address fallback (to property address) is applied below after prop_loc_raw is parsed

# Property address
prop_loc_raw   = _sheet_value(ROW, "Property Location Details")
if not prop_loc_raw:
    prop_loc_raw = _h("property.address")
prop_loc_parts = prop_loc_raw.split(",")
street_parts   = prop_loc_parts[0].strip().split()
address_line   = prop_loc_raw.strip()

# Mailing address fallback — use property address when mailing fields were not submitted
if not mailing_street:
    _pa = [p.strip() for p in prop_loc_raw.split(",")]
    mailing_street = _pa[0] if _pa else ""
    if len(_pa) >= 2:
        mailing_city = _pa[1]
    if len(_pa) >= 3:
        _sc = _pa[2].strip().split()
        mailing_state = _sc[0] if _sc else ""
        mailing_zip   = _sc[1] if len(_sc) > 1 else ""

# Application type
app_type_raw   = _sheet_value(ROW, "Application Type")
if not app_type_raw:
    app_type_raw = _h("metadata.application_type", "First Time System")
app_type_norm  = _radio(app_type_raw, APP_TYPE_MAP)

# Special notes
special_notes  = _sheet_value(ROW, "Special Notes")

# Year installed (for replacements)
year_sys_installed = ""
if "replacement" in app_type_raw.lower():
    year_match = re.search(r"\b(19|20)\d{2}\b", special_notes)
    if year_match:
        year_sys_installed = year_match.group(0)

# Seasonal use / current use
seasonal_raw   = _sheet_value(ROW, "Seasonal Use", "Seasonal use") or "Seasonal"
current_use_norm = _radio(seasonal_raw, CURRENT_USE_MAP)
if not current_use_norm:
    current_use_norm = "Year-Round"

# Shoreland zoning
slz_raw = _sheet_value(ROW, "Shoreland Zoning", "Shoreland zoning") or "No"
slz_norm = _radio(slz_raw, SLZ_MAP) or "No"

# Water supply
water_raw = _sheet_value(ROW, "Water supply and Well", "Water supply and well", "Water supply").split(",")[0].strip()
if not water_raw:
    water_raw = _h("water_supply.type", "drilled well")
water_norm = _radio(water_raw, WATER_SUPPLY_MAP) or "Drilled Well"

# GPS coordinates — prefer hermes, fall back to column W
lat_deg  = _h("property.latitude_deg")
lat_min  = _h("property.latitude_min")
lat_sec  = _h("property.latitude_sec")
lon_deg  = _h("property.longitude_deg")
lon_min  = _h("property.longitude_min")
lon_sec  = _h("property.longitude_sec")
gps_error = ""

if not lat_deg:
    gps_raw = _sheet_value(ROW, "Latitude and Longitude") or ""
    if not gps_raw:
        gps_raw = _sheet_value(ROW, "Elevation reference point (ERP) and elevations (if known)")
    lon_m = re.search(
        r"(\d+)\s*[°\s]\s*(\d+)\s*[\''\s]\s*([0-9.]+)[^,]+,\s*(\d+)\s*[°\s]\s*(\d+)\s*[\''\s]\s*([0-9.]+)",
        gps_raw,
    )
    lat_m = re.search(r"(\d+)\s*[°\s]\s*(\d+)\s*[\''\s]\s*([0-9.]+)", gps_raw)
    if lon_m:
        lat_deg, lat_min, lat_sec = lon_m.group(1), lon_m.group(2), lon_m.group(3)
        lon_deg, lon_min, lon_sec = lon_m.group(4), lon_m.group(5), lon_m.group(6)
    elif lat_m:
        lat_deg, lat_min, lat_sec = lat_m.group(1), lat_m.group(2), lat_m.group(3)
    err_m = re.search(r"(?:margin|error)[:\s]+([0-9.]+)\s*(?:ft|feet|m|meters)", gps_raw, re.I)
    if err_m:
        gps_error = err_m.group(1)

# Limiting factor
lf_raw = _sheet_value(ROW, "Limiting Factor", "Limiting factor")
if not lf_raw:
    lf_raw = _h("soil_observations.limiting_factors", "limiting factor is ground water at 24 inches")

lf_depth_in = int(_h("elevation_data.limiting_factor.depth_in") or "0")
if not lf_depth_in:
    m = re.search(r"(\d+)\s*(?:inches?|in)", lf_raw, re.I)
    if m:
        lf_depth_in = int(m.group(1))

lf_depth_str    = f'-{lf_depth_in}"' if lf_depth_in else ""
lf_elevation_ft = f"-{round(lf_depth_in / 12, 1)}" if lf_depth_in else ""
lf_type_is_gw   = "ground water" in lf_raw.lower() or "groundwater" in lf_raw.lower()

# Elevation / ERP data
elev_raw       = _sheet_value(ROW, "Elevation reference point (ERP) and elevations (if known)")
finished_grade = _parse_elev(elev_raw, r"finish(?:ed)? grade elevation\s*=?\s*([+-]?\d+)")
top_pipe       = _parse_elev(elev_raw, r"top of (?:pipe|distribution)\s*=?\s*([+-]?\d+)")
bottom_field   = _parse_elev(elev_raw, r"bottom of (?:disposal area|proprietary device)\s*=?\s*([+-]?\d+)")
erp_loc_raw    = _parse_elev(elev_raw, r"ERP\s*=\s*(.+?)(?:,|$)")

# Prefer hermes elevation data (more reliable than sheet text parsing)
if hermes:
    elev_h = hermes.get("elevation_data", {})
    if not finished_grade:
        fg = elev_h.get("finished_grade_in")
        if fg is not None:
            finished_grade = str(fg)
    if not top_pipe:
        tp = elev_h.get("top_pipe_in")
        if tp is not None:
            top_pipe = str(tp)
    # Always prefer hermes for bottom_field — sheet text often has sign errors
    bf = elev_h.get("bottom_field_in")
    if bf is not None:
        bottom_field = str(bf)
    if not erp_loc_raw:
        erp = elev_h.get("reference_point", {})
        erp_loc_raw = erp.get("description", "")

# Septic tank
tank_info   = _sheet_value(ROW, "Septic tank setup")
tank_cap    = _h("septic_system.tank.capacity_gallons") or _parse_number(tank_info)
tank_notes  = tank_info.strip()

tank_material = "Concrete"  # most common default
tank_info_lower = tank_info.lower()
for k, v in TANK_MATERIAL_MAP.items():
    if k in tank_info_lower:
        tank_material = v
        break

tank_type = "regular"
if "low profile" in tank_info_lower:
    tank_type = "low profile"
elif "h-20" in tank_info_lower or "h20" in tank_info_lower:
    tank_type = "h20"

# Disposal system type
disposal_type_raw = _sheet_value(ROW, "Disposal system type", "Disposal System Type")
if not disposal_type_raw:
    disposal_type_raw = _h("septic_system.disposal_field.type", "Proprietary Device")

disposal_type_lower  = disposal_type_raw.lower()
disposal_field_type_norm = _radio(disposal_type_raw.split(",")[0].strip(), DISPOSAL_FIELD_TYPE_MAP) or "Proprietary Device"

# Is this a proprietary device system?
is_proprietary = disposal_field_type_norm == "Proprietary Device"
is_eljen       = "eljen" in disposal_type_lower

# System type checkboxes
ces_check     = "Yes" if any(x in disposal_type_lower for x in ["engineered", "ces", "eljen", "infiltrator", "biodiffuser", "proprietary", "presby", "geomat"]) else ""
cnes_check    = "Yes" if any(x in disposal_type_lower for x in ["non-engineered", "cnes"]) else ""
non_eng_field = "" if (ces_check or cnes_check) else "Yes"

# Planned field / layout
planned_field_text = _sheet_value(ROW, "Planned field size and layout (if known)")
if not planned_field_text:
    df = hermes.get("septic_system", {}).get("disposal_field", {})
    planned_field_text = (
        f"{df.get('rows','')} rows of {df.get('modules_per_row','')} "
        f"{df.get('type','')} modules, {df.get('total_modules','')} total, "
        f"{df.get('cluster_width_ft','') }x{df.get('cluster_length_ft','')}' cluster"
    )

# Field area
field_area = _h("septic_system.disposal_field.area_sqft")
if not field_area:
    dim_m = re.search(r"(\d+)[\'x×](\d+)", planned_field_text)
    if dim_m:
        field_area = str(int(dim_m.group(1)) * int(dim_m.group(2)))

# Proprietary device arrangement
proprietary_opt = ""
if is_proprietary:
    plan_lower = planned_field_text.lower()
    if "cluster" in plan_lower:
        proprietary_opt = "Cluster Array"
    elif "linear" in plan_lower:
        proprietary_opt = "Linear"
    elif "load" in plan_lower:
        proprietary_opt = "Load Profile"
    else:
        proprietary_opt = "Cluster Array"   # Eljen default

# Design flow
design_flow_raw = _sheet_value(ROW, "Design flow overflow", "Design flow override")
design_flow_gpd_val = _h("septic_system.design_flow_gpd")
if not design_flow_gpd_val:
    m = re.search(r"(\d+)\s*(?:gallons?\s*per\s*day|gpd)", design_flow_raw, re.I)
    if m:
        design_flow_gpd_val = m.group(1)
    elif design_flow_raw and design_flow_raw.split()[0].isdigit():
        design_flow_gpd_val = design_flow_raw.split()[0]

design_flow_type_val = "Table 5A (Dwelling Units)"   # default for residential
if "table 5c" in design_flow_raw.lower():
    design_flow_type_val = "Table 5C"
elif any(x in design_flow_raw.lower() for x in ["5g", "meter", "section 5"]):
    design_flow_type_val = "Section 5(G)"

# Bedrooms
bedrooms = _h("septic_system.bedrooms")
if not bedrooms:
    serve_raw = _sheet_value(ROW, "What will the system serve, and what is the design basis?")
    br_m = re.search(r"(\d+)\s*bedroom", serve_raw, re.I)
    if br_m:
        bedrooms = br_m.group(1)
    else:
        bedrooms = "3"

# Disposal system to serve
serve_raw = _sheet_value(ROW, "What will the system serve, and what is the design basis?")
disposal_to_serve_norm = _radio(serve_raw.split(",")[0].strip(), DISPOSAL_SYSTEM_MAP) or "Single Family Dwelling Unit"

# Soil profile — Observation Hole 1
oh1_layers     = _h_layers(0)
oh1_depth_in   = int(_h("observation_holes.0.depth_ft") or "0") * 12  # feet → inches
oh1_org_thick  = _h("observation_holes.0.organic_horizon_thickness_in") or _h("soil_observations.organic_horizon_thickness_in", "2")
oh1_gse        = _h("observation_holes.0.ground_surface_elevation", "0.0")

if oh1_layers:
    oh1_textures  = _format_soil_col(oh1_layers, "texture")
    oh1_colors    = _format_soil_col(oh1_layers, "color")
    oh1_consistence = _format_soil_col(oh1_layers, "consistence") or "Friable"
    oh1_redox     = _format_soil_col(oh1_layers, "redox_features")
    last_depth    = oh1_layers[-1].get("depth_end_in", oh1_depth_in)
    oh1_depth_exp = f'-{last_depth}"'
else:
    # Fall back to raw sheet parsing
    soil_raw      = _sheet_value(ROW, "Soil summary at disposal area")
    oh1_textures  = soil_raw
    oh1_colors    = ""
    oh1_consistence = "Friable"
    oh1_redox     = ""
    depth_m       = re.search(r"(?:to\s+)?pit\s+depth\s+of\s+(\d+)", soil_raw, re.I)
    oh1_depth_exp = f'-{depth_m.group(1)}"' if depth_m else ""

# Soil profile — Observation Hole 2
oh2_layers     = _h_layers(1)
oh2_depth_in   = int(_h("observation_holes.1.depth_ft") or "0") * 12
oh2_org_thick  = _h("observation_holes.1.organic_horizon_thickness_in", "")
oh2_gse        = _h("observation_holes.1.ground_surface_elevation", "")

if oh2_layers:
    oh2_textures    = _format_soil_col(oh2_layers, "texture")
    oh2_colors      = _format_soil_col(oh2_layers, "color")
    oh2_consistence = _format_soil_col(oh2_layers, "consistence") or "Friable"
    oh2_redox       = _format_soil_col(oh2_layers, "redox_features")
    last_depth2     = oh2_layers[-1].get("depth_end_in", oh2_depth_in)
    oh2_depth_exp   = f'-{last_depth2}"'
    oh2_lf_depth    = lf_depth_str  # same LF applies to OH2
    oh2_gw_check    = "Yes" if lf_type_is_gw else ""
else:
    oh2_textures = oh2_colors = oh2_consistence = oh2_redox = oh2_depth_exp = ""
    oh2_lf_depth = oh2_gw_check = ""

# Distances
dist_raw      = _sheet_value(ROW, "Key distances between features")
field_to_well = ""
for seg in dist_raw.split(","):
    if "field to well" in seg.lower():
        m = re.search(r"(\d+)", seg)
        if m:
            field_to_well = m.group(1)

# ── Merge sketch-extracted data ───────────────────────────────────────────────
# Augment form fields with data extracted from submitted sketches
if sketch_data:
    # Merge soil info into soil observation fields
    soil_info = sketch_data.get("soil_info", {})
    if soil_info:
        if not oh1_textures and soil_info.get("description"):
            oh1_textures = soil_info.get("description", "")
        if not oh1_colors and soil_info.get("color"):
            oh1_colors = soil_info.get("color", "")

    # Merge elevation data
    elevations = sketch_data.get("elevations", {})
    if elevations:
        if not finished_grade and elevations.get("finished_grade"):
            finished_grade = elevations.get("finished_grade", "")
        if not top_pipe and elevations.get("top_pipe"):
            top_pipe = elevations.get("top_pipe", "")
        if not bottom_field and elevations.get("bottom_field"):
            bottom_field = elevations.get("bottom_field", "")

    # Merge GPS coordinates
    gps_locations = sketch_data.get("gps_locations", {})
    if gps_locations:
        if not lat_deg and gps_locations.get("latitude"):
            lat_deg = gps_locations.get("latitude_deg", "")
            lat_min = gps_locations.get("latitude_min", "")
            lat_sec = gps_locations.get("latitude_sec", "")
        if not lon_deg and gps_locations.get("longitude"):
            lon_deg = gps_locations.get("longitude_deg", "")
            lon_min = gps_locations.get("longitude_min", "")
            lon_sec = gps_locations.get("longitude_sec", "")

    # Merge tie items (distances)
    tie_items = sketch_data.get("tie_items", [])
    if tie_items and not field_to_well:
        for item in tie_items:
            if "well" in item.get("feature", "").lower():
                field_to_well = item.get("distance", "")
                break

# ── Build fields dict ─────────────────────────────────────────────────────────

fields = {
    # ── Page 1: Site / Applicant Info ──────────────────────────────────────────
    "street_number":           street_parts[0] if street_parts else "",
    "street_name":             " ".join(street_parts[1:]),
    "town":                    prop_loc_parts[1].strip() if len(prop_loc_parts) > 1 else "",
    "map_number":              tax_map,
    "lot_number":              lot_num,
    "owner_name":              owner_name,
    "applicant_name":          owner_name,
    "owner_phone":             owner_phone,
    "owner_email":             _h("client.email"),
    "mailing_street":          mailing_street,
    "mailing_city":            mailing_city,
    "mailing_state":           mailing_state,
    "mailing_zip":             mailing_zip,
    "installer_name":          "",
    "installer_phone":         "",
    "installer_email":         "",
    "evaluator_name":          evaluator_name,
    "evaluator_phone":         evaluator_phone,
    "evaluator_email":         evaluator_email,
    "se_number":               evaluator_lic,
    "se_signature_date":       "03/01/2026",
    "issuing_municipality":    prop_loc_parts[1].strip() if len(prop_loc_parts) > 1 else "",
    "permit_number":           "",
    "permit_issued_date":      "",

    # Type of Application (Radio)
    "type_of_app":             app_type_norm,
    "system_replaced":         "Septic System" if "replacement" in app_type_raw.lower() else "",
    "year_installed":          year_sys_installed,

    # Variance
    "variance_check":          "Yes" if "variance" in special_notes.lower() else "",
    "variance_requirement":    "No Rule Variance",

    # Treatment Tank(s)
    "treatment_tanks":         tank_material,    # Radio: Concrete / Plastic / Other
    "tank_regular_check":      "Yes" if tank_type == "regular" else "",
    "tank_low_profile_check":  "Yes" if tank_type == "low profile" else "",
    "tank_h20_check":          "Yes" if tank_type == "h20" else "",
    "tank_cap_gal":            tank_cap,
    "tank_capacity":           tank_cap,
    "tank_total_new":          "1",
    "tank_notes":              tank_notes,

    # Disposal system components
    "ces_check":               ces_check,
    "cnes_check":              cnes_check,
    "non_eng_field_check":     non_eng_field,
    "eng_field_check":         "Yes" if ces_check else "",
    "eng_tank_check":          "",      # not adding a new tank
    "non_eng_tank_number":     "",

    # ── Page 2: Property & System Details ──────────────────────────────────────
    "owner_name_pg2":          owner_name,
    "address_pg2":             address_line,
    "property_size":           acreage,
    "property_size_units":     size_units,
    "current_use":             current_use_norm,
    "shoreland_zoning_yn":     slz_norm,

    # GPS
    "latitude_deg":            lat_deg,
    "latitude_min":            lat_min,
    "latitude_sec":            lat_sec,
    "longitude_deg":           lon_deg,
    "longitude_min":           lon_min,
    "longitude_sec":           lon_sec,
    "gps_margin_error":        gps_error,

    # Water / GDU
    "water_supply":            water_norm,
    "water_supply_specify":    "",
    "effluent_pump":           "No",       # no pump for gravity system
    "garbage_disposal":        "No",       # key must match WIDGET_MAP
    "dose_gallons":            "",

    # Disposal system
    "disposal_system_to_serve": disposal_to_serve_norm,
    "num_bedrooms_opt1":       bedrooms,
    "disposal_field_type":     disposal_field_type_norm,
    "proprietary_device_opt":  proprietary_opt,
    "disposal_field_size":     field_area,
    "disposal_field_size_unit": "sq ft" if field_area else "",

    # Design flow
    "design_flow_gpd":         design_flow_gpd_val,
    "design_flow_type":        design_flow_type_val,

    # Soil summary / limiting factor
    "profile_soil_data":       oh1_textures,
    "condition_soil_data":     "Friable",
    "observation_hole_number": "1",
    "limiting_factor_depth":   lf_depth_str,
    "limiting_factor_elevation": lf_elevation_ft,
    "additional_notes":        special_notes,

    # ── Page 3: Observation Hole 1 ──────────────────────────────────────────────
    "oh1_number":              "1",
    "oh1_test_pit":            "Yes",
    "oh1_organic_thickness":   f'{oh1_org_thick}"' if oh1_org_thick else "2\"",
    "oh1_ground_surface":      oh1_gse,
    "oh1_depth_exploration":   oh1_depth_exp,
    "oh1_textures":            oh1_textures,
    "oh1_consistence":         oh1_consistence if isinstance(oh1_consistence, str) else "Friable",
    "oh1_color":               oh1_colors,
    "oh1_redox":               oh1_redox if isinstance(oh1_redox, str) else "",
    "oh1_profile":             oh1_colors.split("\n")[0] if oh1_colors else "",
    "oh1_condition":           "Friable",
    "oh1_slope":               "",
    "oh1_limiting_factor":     lf_depth_str,
    "oh1_groundwater_check":   "Yes" if lf_type_is_gw else "",
    "oh1_restrictive_layer_check": "" if lf_type_is_gw else "Yes",

    # ── Page 3: Observation Hole 2 ──────────────────────────────────────────────
    "oh2_number":              "2" if oh2_layers else "",
    "oh2_test_pit":            "Yes" if oh2_layers else "",
    "oh2_organic_thickness":   f'{oh2_org_thick}"' if oh2_org_thick else "",
    "oh2_ground_surface":      oh2_gse,
    "oh2_depth_exploration":   oh2_depth_exp,
    "oh2_textures":            oh2_textures,
    "oh2_consistence":         oh2_consistence if isinstance(oh2_consistence, str) else "",
    "oh2_color":               oh2_colors,
    "oh2_redox":               oh2_redox if isinstance(oh2_redox, str) else "",
    "oh2_profile":             oh2_colors.split("\n")[0] if oh2_colors else "",
    "oh2_condition":           "Friable" if oh2_layers else "",
    "oh2_slope":               "",
    "oh2_limiting_factor":     oh2_lf_depth,
    "oh2_groundwater_check":   oh2_gw_check,

    # ── Page 4 (output): Backfill / Elevation / ERP ────────────────────────────
    "scale_pg3":               "40",
    "scale_pg4":               "8",
    "backfill_upslope":        "",
    "backfill_downslope":      "",
    "finished_grade_elevation": f'{finished_grade}"' if finished_grade else "",
    "top_distribution_pipe":   f'{top_pipe}"' if top_pipe else "",
    "bottom_disposal_field":   f'{bottom_field}"' if bottom_field else "",
    "erp_location":            erp_loc_raw,
    "erp_reference_elevation": "0.0",
    "vertical_scale":          "1",
    "horizontal_scale":        "8",
}

# Strip placeholder strings
PLACEHOLDERS = {"empty", "none", "n/a", "unknown"}
for k, v in list(fields.items()):
    if isinstance(v, str) and v.strip().lower() in PLACEHOLDERS:
        fields[k] = ""

# ── Step 2: Generate DXF drawings ────────────────────────────────────────────

print("\nGenerating site plan drawings…")
from site_plan_generator import generate_all as _generate_drawings

_drawing_data = {
    "owner_name":     owner_name,
    "address_line":   address_line,
    "street_name":    " ".join(street_parts[1:]),
    "road_name":      " ".join(street_parts[1:]),
    "town":           prop_loc_parts[1].strip() if len(prop_loc_parts) > 1 else "",
    "tax_map":        tax_map,
    "lot_number":     lot_num,
    "acreage":        acreage,
    "tank_cap":       tank_cap,
    "se_number":      evaluator_lic,
    "se_date":        "03/01/2026",
    "planned_field":  planned_field_text,
    "key_distances":  dist_raw,
    "elevation_raw":  elev_raw,
    "limiting_factor": lf_raw,
    "erp_location":   erp_loc_raw,
}

_drawings = _generate_drawings(_drawing_data, out_dir=SCRIPT_DIR)
dxf_out = SCRIPT_DIR / "site_plan_pg3.dxf"
print(f"✓ Generated {len(_drawings)} drawing files")

# ── Step 3: Fill PDF ──────────────────────────────────────────────────────────

filled_count = sum(1 for v in fields.values() if v)
print(f"\nField count: {filled_count} / {len(fields)} with data")
pdf_out = SCRIPT_DIR / "HHE-200-filled.pdf"

try:
    result_pdf = fill_acro(fields, out_path=str(pdf_out))
    print(f"✓ Filled PDF → {result_pdf}")
except Exception as e:
    print(f"✗ fill_acro failed: {e}")
    sys.exit(1)

# ── Step 4: Upload to Drive ───────────────────────────────────────────────────

print("\nUploading to Drive…")
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    token_path = _first_existing_path(CONFIG_AUTH["token"], LEGACY_AUTH["token"])
    cred_path  = _first_existing_path(CONFIG_AUTH["credentials"], LEGACY_AUTH["credentials"])
    token_data = _load_json(token_path)
    cred_data  = _load_json(cred_path)

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=_auth_block(cred_data).get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=_auth_block(cred_data)["client_id"],
        client_secret=_auth_block(cred_data)["client_secret"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    drive = build("drive", "v3", credentials=creds)
    upload_folder_id = "1luOtuHHylbOobofayoWR5FjtVPdUafey"

    files_to_upload = [
        (str(pdf_out), "application/pdf"),
        (str(dxf_out), "application/x-msdownload"),
    ]

    uploaded = []
    for filepath, mime_type in files_to_upload:
        fname = Path(filepath).name
        metadata = {"name": fname, "parents": [upload_folder_id]}
        media = MediaFileUpload(filepath, mimetype=mime_type)
        f = drive.files().create(body=metadata, media_body=media, fields="id, webViewLink").execute()
        link = f.get("webViewLink", "")
        uploaded.append({"name": fname, "id": f["id"], "link": link})
        print(f"  ✓ {fname} → {link}")

    print(f"\n=== PIPELINE COMPLETE ===")
    print(f"Client: {client_name}")
    for u in uploaded:
        print(f"  {u['name']}: {u['link']}")

except ImportError as e:
    print(f"⚠ Upload skipped — missing lib: {e}")
except Exception as e:
    print(f"⚠ Upload failed: {e}")
    print(f"Files saved locally at: {pdf_out}, {dxf_out}")
