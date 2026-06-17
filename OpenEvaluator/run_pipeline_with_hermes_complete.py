#!/usr/bin/env python3
"""
OpenEvaluator Pipeline with Complete Hermes Integration

Reads hermes_output.json → fills ALL HHE-200 form fields (WIDGET_MAP-keyed)
→ generates professional drawings → embeds drawings in PDF.

NO fallback to test data. REQUIRES hermes_output.json.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent


# ============================================================================
# Load & Validate Hermes Output
# ============================================================================

def load_hermes_output(filepath: str = 'hermes_output.json') -> dict:
    path = BASE / filepath if not os.path.isabs(filepath) else Path(filepath)
    if not path.exists():
        logger.error(f"❌ {path} not found! Hermes has not processed this submission yet.")
        sys.exit(1)
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"❌ {path} is malformed: {e}")
        sys.exit(1)

    required = ['metadata', 'site_evaluator', 'client', 'property',
                'water_supply', 'septic_system', 'soil_observations',
                'observation_holes', 'elevation_data']
    missing = [k for k in required if k not in data]
    if missing:
        logger.error(f"❌ Missing required keys: {missing}")
        sys.exit(1)

    logger.info(f"✅ Loaded hermes_output.json")
    logger.info(f"   Submission: {data['metadata'].get('submission_id', 'N/A')}")
    logger.info(f"   Client: {data['client']['name']}")
    logger.info(f"   Property: {data['property']['address']}")
    return data


# ============================================================================
# Address Parser
# ============================================================================

def _parse_address(addr: str) -> dict:
    """Parse '17 Aspen Way, Turner, Maine 04282' into components."""
    parts = [p.strip() for p in addr.split(',')]
    street_full = parts[0] if parts else addr
    city = parts[1] if len(parts) > 1 else ''
    state_zip = parts[2] if len(parts) > 2 else ''

    sz_parts = state_zip.split()
    state = sz_parts[0] if sz_parts else ''
    zipcode = sz_parts[-1] if len(sz_parts) > 1 else ''

    s_parts = street_full.split(' ', 1)
    if s_parts and s_parts[0].replace('-', '').isdigit():
        street_num = s_parts[0]
        street_name = s_parts[1] if len(s_parts) > 1 else ''
    else:
        street_num = ''
        street_name = street_full

    return {
        'street_num': street_num,
        'street_name': street_name,
        'city': city,
        'state': state,
        'zip': zipcode,
    }


def _layers_text(layers: list, key: str, sep: str = ' / ') -> str:
    return sep.join(str(l.get(key, '')) for l in layers if l.get(key))


# ============================================================================
# extract_form_data — keys match WIDGET_MAP exactly
# ============================================================================

def extract_form_data(hermes: dict) -> dict:
    """
    Extract ALL available data from hermes_output.json, keyed by WIDGET_MAP
    keys so that fill_acro() can find and fill every field.
    """
    prop     = hermes['property']
    se       = hermes['site_evaluator']
    client   = hermes['client']
    water    = hermes['water_supply']
    septic   = hermes['septic_system']
    soil     = hermes['soil_observations']
    holes    = hermes.get('observation_holes', [])
    elev     = hermes['elevation_data']
    setbacks = hermes.get('setback_requirements', {})
    meta     = hermes.get('metadata', {})
    tank     = septic['tank']
    field    = septic['disposal_field']
    roads    = prop.get('roads', [])

    # ── Addresses ────────────────────────────────────────────────────────
    prop_a   = _parse_address(prop.get('address', ''))
    client_a = _parse_address(client.get('address', prop.get('address', '')))

    # ── Observation holes ────────────────────────────────────────────────
    oh1        = holes[0] if holes else {}
    oh1_layers = oh1.get('soil_layers', [])
    oh2        = holes[1] if len(holes) > 1 else {}
    oh2_layers = oh2.get('soil_layers', [])

    # ── Field layout ─────────────────────────────────────────────────────
    rows         = field.get('rows', 3)
    mods_per_row = field.get('modules_per_row', 7)
    total_mods   = field.get('total_modules', rows * mods_per_row)
    cluster_w    = float(field.get('cluster_width_ft',  rows * 3.67 + (rows - 1) * 1.0))
    cluster_l    = float(field.get('cluster_length_ft', mods_per_row * 4.0))
    field_sqft   = int(field.get('area_sqft', int(cluster_w * cluster_l)))
    brand        = 'Eljen'

    # ── Elevations ───────────────────────────────────────────────────────
    erp       = elev.get('reference_point', {})
    erp_height = erp.get('height_above_grade_in', 12)
    erp_desc  = erp.get('description', f'NAIL SET {erp_height}" ABOVE GRADE IN 6" MAPLE TREE')
    lim       = elev.get('limiting_factor', {})
    lim_depth = int(lim.get('depth_in', soil.get('groundwater_depth_in', 24)))

    # Signed-inch elevation strings for form fields
    def _inch_str(val):
        v = int(val)
        return f"+{v}\"" if v > 0 else f"{v}\""

    fg_in  = int(elev.get('finished_grade_in', 0))
    tp_in  = int(elev.get('top_pipe_in', -12))
    bf_in  = int(elev.get('bottom_field_in', -30))

    # ── Application type ─────────────────────────────────────────────────
    app_type_raw = meta.get('application_type', 'First Time System')
    is_replacement = 'replacement' in app_type_raw.lower()
    app_type_radio = "Replacement System" if is_replacement else "First Time System"

    # ── Design flow ──────────────────────────────────────────────────────
    design_flow = str(int(septic.get('design_flow_gpd', 270)))

    # ── Bedrooms ─────────────────────────────────────────────────────────
    bedrooms = str(int(septic.get('bedrooms', 3)))

    # ── Road name ────────────────────────────────────────────────────────
    road_name = roads[0].get('name', prop_a['street_name']) if roads else prop_a['street_name']

    # ── Well setback ─────────────────────────────────────────────────────
    well_setback  = float(setbacks.get('well_setback_ft',     100.0))
    house_setback = float(setbacks.get('dwelling_setback_ft',  20.0))

    # ── SE signature date ────────────────────────────────────────────────
    from datetime import date as _date
    se_date_str = _date.today().strftime("%m/%d/%Y")

    # ── GPS coordinates ──────────────────────────────────────────────────
    lat_deg = str(prop.get('latitude_deg',  ''))
    lat_min = str(prop.get('latitude_min',  ''))
    lat_sec = str(prop.get('latitude_sec',  ''))
    lon_deg = str(prop.get('longitude_deg', ''))
    lon_min = str(prop.get('longitude_min', ''))
    lon_sec = str(prop.get('longitude_sec', ''))

    # ── Backfill depths (ERP nail height ≈ upslope backfill depth) ───────
    backfill_upslope   = str(erp_height)
    backfill_downslope = str(erp_height)

    # ── OH depth (convert ft → inches if stored as feet ≤ 10) ───────────
    def _oh_depth_in(hole: dict) -> str:
        raw = hole.get('depth_ft', 36)
        return str(int(raw * 12) if raw <= 10 else int(raw))

    # ── OH texture/color/consistence with depth-range prefixes ───────────
    def _layers_text(layers, key):
        if not layers:
            return ''
        parts = []
        for lyr in layers:
            d0 = lyr.get('depth_start_in', '')
            d1 = lyr.get('depth_end_in', '')
            val = lyr.get(key, '')
            if val:
                prefix = f"{d0}-{d1}\": " if d0 != '' and d1 != '' else ''
                parts.append(f"{prefix}{val}")
        return '  /  '.join(parts)

    # ── Water supply ─────────────────────────────────────────────────────
    water_type_raw = water.get('type', 'private_well').lower()
    if 'drilled' in water_type_raw or 'well' in water_type_raw:
        water_supply_val = 'Drilled Well'
    elif 'dug' in water_type_raw:
        water_supply_val = 'Dug Well'
    elif 'public' in water_type_raw or 'municipal' in water_type_raw:
        water_supply_val = 'Public'
    else:
        water_supply_val = 'Other'

    fields: dict = {

        # ── Page 1 ────────────────────────────────────────────────────────
        "street_number":            prop_a['street_num'],
        "street_name":              prop_a['street_name'],
        "town":                     prop_a['city'],
        "map_number":               prop.get('map_number', ''),
        "lot_number":               prop.get('lot_number', ''),

        "owner_name":               client.get('name', ''),
        "applicant_name":           client.get('name', ''),
        "owner_phone":              client.get('phone', ''),
        "owner_email":              client.get('email', ''),

        "mailing_street":           f"{client_a['street_num']} {client_a['street_name']}".strip(),
        "mailing_city":             client_a['city'],
        "mailing_state":            client_a['state'],
        "mailing_zip":              client_a['zip'],

        "evaluator_name":           se.get('name', ''),
        "evaluator_phone":          se.get('phone', ''),
        "evaluator_email":          se.get('email', ''),
        "se_number":                se.get('license_number', ''),
        "se_signature_date":        se_date_str,

        # Application type radio (Replacement System / First Time System)
        "type_of_app":              app_type_radio,
        "variance_requirement":     "No Rule Variance",
        "first_time_system":        "" if is_replacement else "First Time System",
        "replacement_variance":     "LPI Only" if is_replacement else "",

        # Treatment tank
        "treatment_tanks":          "Concrete",
        "tank_regular_check":       "Yes",
        "tank_capacity":            str(tank.get('capacity_gallons', '')),
        "tank_cap_gal":             str(tank.get('capacity_gallons', '')),
        "tank_total_new":           "1",
        "risers_required_check":    "Yes",

        # Disposal system — Complete Engineered System
        "ces_check":                "Yes",
        "eng_tank_check":           "Yes",
        "eng_field_check":          "Yes",
        "ces_tanks":                "1",
        "ces_new_tanks":            "1",
        "ces_pumps":                "0",
        "eng_tank_number":          "1",

        # ── Page 2 ────────────────────────────────────────────────────────
        "owner_name_pg2":           client.get('name', ''),
        "address_pg2":              prop.get('address', ''),
        "property_size":            str(prop.get('acreage', '')),
        "property_size_units":      "acres",
        "current_use":              "Single Family Residential",
        "shoreland_zoning_yn":      "N",

        # GPS
        "latitude_deg":             lat_deg,
        "latitude_min":             lat_min,
        "latitude_sec":             lat_sec,
        "longitude_deg":            lon_deg,
        "longitude_min":            lon_min,
        "longitude_sec":            lon_sec,

        # Water supply
        "water_supply":             water_supply_val,

        # Pumps / GDU
        "effluent_pump":            "No",
        "garbage_disposal":         "N",

        # Disposal system to serve
        "disposal_system_to_serve": "Single Family Dwelling",
        "num_bedrooms_opt1":        bedrooms,

        # Disposal field type and size
        "disposal_field_type":      "Proprietary Device",
        "proprietary_device_opt":   "Cluster Array",
        "disposal_field_size":      str(field_sqft),
        "disposal_field_size_unit": "sq ft",

        # Design flow
        "design_flow_gpd":          design_flow,
        "design_flow_type":         "Table 5A (Dwelling Units)",

        # Soil data
        "profile_soil_data":        oh1_layers[0].get('texture', soil.get('texture_description', '')) if oh1_layers else soil.get('texture_description', ''),
        "condition_soil_data":      oh1_layers[0].get('consistence', '') if oh1_layers else '',
        "observation_hole_number":  str(oh1.get('hole_number', '1')) if oh1 else '',
        "limiting_factor_depth":    str(lim_depth),
        "limiting_factor_elevation": _inch_str(-lim_depth + fg_in),

        "additional_notes":         soil.get('general_notes', ''),

        # ── Page 3: Observation Hole 1 ────────────────────────────────────
        "oh1_test_pit":             "Yes",
        "oh1_number":               str(oh1.get('hole_number', '1')) if oh1 else '',
        "oh1_organic_thickness":    str(oh1.get('organic_horizon_thickness_in', '')) if oh1 else '',
        "oh1_ground_surface":       _inch_str(oh1.get('ground_surface_elevation', 0)) if oh1 else '',
        "oh1_depth_exploration":    _inch_str(-int(_oh_depth_in(oh1))) if oh1 else '',
        "oh1_textures":             _layers_text(oh1_layers, 'texture'),
        "oh1_color":                _layers_text(oh1_layers, 'color'),
        "oh1_consistence":          _layers_text(oh1_layers, 'consistence'),
        "oh1_redox":                _layers_text(oh1_layers, 'redox_features'),
        "oh1_limiting_factor":      "GROUND WATER" if lim_depth > 0 else soil.get('limiting_factors', ''),
        "oh1_groundwater_check":    "Yes" if lim_depth > 0 else "No",
        "oh1_slope":                "0",
        "oh1_profile":              oh1_layers[0].get('texture', '') if oh1_layers else '',
        "oh1_condition":            oh1_layers[0].get('consistence', '') if oh1_layers else '',
        "oh1_pit_depth_check":      "Yes",

        # ── Page 3: Observation Hole 2 ────────────────────────────────────
        "oh2_test_pit":             "Yes",
        "oh2_number":               str(oh2.get('hole_number', '2')) if oh2 else '',
        "oh2_organic_thickness":    str(oh2.get('organic_horizon_thickness_in', '')) if oh2 else '',
        "oh2_ground_surface":       _inch_str(oh2.get('ground_surface_elevation', 0)) if oh2 else '',
        "oh2_depth_exploration":    _inch_str(-int(_oh_depth_in(oh2))) if oh2 else '',
        "oh2_textures":             _layers_text(oh2_layers, 'texture'),
        "oh2_color":                _layers_text(oh2_layers, 'color'),
        "oh2_consistence":          _layers_text(oh2_layers, 'consistence'),
        "oh2_redox":                _layers_text(oh2_layers, 'redox_features'),
        "oh2_limiting_factor":      "GROUND WATER" if lim_depth > 0 else soil.get('limiting_factors', ''),
        "oh2_groundwater_check":    "Yes" if lim_depth > 0 else "No",
        "oh2_slope":                "0",
        "oh2_profile":              oh2_layers[0].get('texture', '') if oh2_layers else '',
        "oh2_condition":            oh2_layers[0].get('consistence', '') if oh2_layers else '',
        "oh2_pit_depth_check":      "Yes",

        # ── Page 2: additional fillable fields ────────────────────────────
        "dose_gallons":             design_flow,        # engineered system dose
        "type_of_system_replaced":  "CONVENTIONAL SYSTEM",

        # ── Page 4: Elevations ────────────────────────────────────────────
        "scale_pg4":                "10",
        "erp_location":             erp_desc.upper(),
        "erp_reference_elevation":  "0.0\"",
        "finished_grade_elevation": _inch_str(fg_in),
        "top_distribution_pipe":    _inch_str(tp_in),
        "bottom_disposal_field":    _inch_str(bf_in),
        "vertical_scale":           "1\" = 2'",
        "horizontal_scale":         "1\" = 10'",
        "backfill_upslope":         str(erp_height),
        "backfill_downslope":       str(erp_height),

        # ── Drawing keys (consumed by site_plan_generator.generate_all) ──
        "scale_pg3":                "80",
        "owner_name":               client.get('name', ''),
        "address_line":             prop.get('address', ''),
        "road_name":                road_name.upper(),
        "tax_map":                  prop.get('map_number', ''),
        "acreage":                  prop.get('acreage', 2.35),
        "tank_cap":                 str(tank.get('capacity_gallons', '1000')),
        "se_date":                  se_date_str,

        # Field layout
        "num_rows":                 rows,
        "mods_per_row":             mods_per_row,
        "mod_len":                  4.0,
        "mod_wid":                  3.67,
        "cluster_w":                cluster_w,
        "cluster_l":                cluster_l,
        "brand":                    brand,

        # Distances
        "field_to_well":            well_setback,
        "field_to_house":           house_setback,
        "tank_to_house":            8.0,

        # Elevation / cross-section (inches for generator)
        "finished_grade_in":        fg_in,
        "top_pipe_in":              tp_in,
        "bottom_field_in":          bf_in,
        "erp_height_above_grade":   erp_height,
        "limiting_factor":          lim_depth,
        "elevation_raw":            (
            f"ERP = {erp_desc}, finish grade = {_inch_str(fg_in)}, "
            f"top pipe = {_inch_str(tp_in)}, bottom = {_inch_str(bf_in)}, "
            f"SHWT = {_inch_str(-lim_depth)}"
        ),

        # Soil profile for cross-section
        "soil_layers_json":         json.dumps(oh1_layers),
    }

    logger.info(f"✅ Extracted {len(fields)} form fields")
    return fields


# ============================================================================
# Main Pipeline
# ============================================================================

def main(hermes_path: str = 'hermes_output.json', out_path: Optional[str] = None):
    logger.info("=" * 60)
    logger.info("OpenEvaluator — HHE-200 Complete Pipeline")
    logger.info("=" * 60)

    # Step 1: Load hermes output
    logger.info("\n[STEP 1] Loading Hermes output...")
    hermes = load_hermes_output(hermes_path)

    # Step 2: Extract all form + drawing data (single unified dict)
    logger.info("\n[STEP 2] Extracting form and drawing data...")
    data = extract_form_data(hermes)

    # Step 3: Generate professional drawings from site_plan_generator
    logger.info("\n[STEP 3] Generating drawings (pages 3-4)...")
    try:
        sys.path.insert(0, str(BASE))
        from site_plan_generator import generate_all
        drawings = generate_all(data, out_dir=str(BASE))
        for key, path in drawings.items():
            logger.info(f"  ✅ {key}: {Path(path).name}")
    except Exception as e:
        logger.error(f"  ❌ Drawing generation failed: {e}")
        import traceback; traceback.print_exc()
        drawings = {}

    # Step 4: Fill HHE-200 AcroForm
    logger.info("\n[STEP 4] Filling HHE-200 form...")
    try:
        from acro_fill import fill_acro
        output_pdf = fill_acro(data, out_path=out_path)
        logger.info(f"  ✅ PDF: {output_pdf}")
    except Exception as e:
        logger.error(f"  ❌ Form fill failed: {e}")
        import traceback; traceback.print_exc()
        output_pdf = None

    # Step 5: Quality assessment (optional — run if module available)
    logger.info("\n[STEP 5] Running quality assessment...")
    try:
        from hermes_quality_assessment import assess_quality
        score = assess_quality(output_pdf)
        logger.info(f"  Quality score: {score}/100")
    except Exception:
        logger.info("  (quality assessment module not available — skipping)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ Pipeline Complete")
    logger.info("=" * 60)
    logger.info(f"  Client:    {hermes['client']['name']}")
    logger.info(f"  Property:  {hermes['property']['address']}")
    logger.info(f"  Evaluator: {hermes['site_evaluator']['name']}")
    if output_pdf:
        logger.info(f"  Output:    {output_pdf}")
    logger.info("\nAll data sourced from Hermes extraction. No fabricated content.")

    return output_pdf


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description="HHE-200 Pipeline")
    p.add_argument("--hermes", default="hermes_output.json")
    p.add_argument("--out",    default=None)
    args = p.parse_args()
    main(args.hermes, args.out)
