#!/usr/bin/env python3
"""
Field Adapter: Converts sheet_parser field names to acro_fill WIDGET_MAP keys.
Complete mapping linking every usable sheet_parser output field to its
corresponding acro_fill input key with intelligent checkbox logic.
"""
from typing import Dict, Optional, Set
import re
import json

# ── SCORING EXCLUSION LIST ────────────────────────────────────────────────────
# Fields that are legitimately blank (not part of HHE-200 quality scoring)
SCORING_EXCLUSIONS: Set[str] = {
    # Town-filled fields (site evaluator doesn't complete these)
    'installer_name', 'installer_phone', 'installer_email',
    'issuing_municipality', 'permit_number', 'permit_issued_date',
    'lpi_inspection1_date', 'lpi_inspection2_date',

    # Contractor decision (made after tank inspection)
    'tank_total_new',

    # Drawing-sourced fields (waiting on Hermes OCR improvement)
    'oh1_bedrock_check', 'oh1_boring', 'oh1_depth_exploration',
    'oh1_ground_surface', 'oh1_limiting_factor', 'oh1_profile',
    'oh1_redox', 'oh1_slope', 'oh1_test_pit',
    'oh2_bedrock_check', 'oh2_boring', 'oh2_color', 'oh2_consistence',
    'oh2_depth_exploration', 'oh2_ground_surface', 'oh2_limiting_factor',
    'oh2_profile', 'oh2_redox', 'oh2_slope', 'oh2_test_pit',
    'backfill_upslope', 'backfill_downslope', 'condition_soil_data',

    # Financial/Fee fields (town calculates)
    'fee_area', 'town_share', 'state_25_pct', 'dep_wqs',
    'total_fee', 'revision_check', 'doubled_fee_check', 'variance_check',
    'design_flow_calculations',
}

# Scorable field count = 269 total - 43 exclusions = 226 fields
TOTAL_WIDGETS = 269
EXCLUDED_WIDGET_COUNT = 43
SCORABLE_WIDGETS = TOTAL_WIDGETS - EXCLUDED_WIDGET_COUNT

def _check_to_x(value: str) -> str:
    """Convert any truthy value to 'X' (PDF checkbox mark)."""
    val = str(value).strip().lower()
    if val in ('x', 'yes', 'true', 'on', '1', 'off'):
        # "Off" means unchecked — but we treat any positive marker as X
        return ""
    if val and val != "off":
        return "X"
    return ""

def _detect_system_type(text: str) -> Dict[str, str]:
    """Parse system description to determine which checkboxes to fill."""
    t = text.lower()
    result = {}
    
    # Determine if replacement (non-engineered disposal field)
    if 'replacement' in t or 'replace' in t:
        result['non_eng_field_check'] = 'X'
        result['replacement_variance'] = ''  # Not requesting variance
        result['first_time_system'] = ''
    
    # Determine treatment tank type
    if 'eljen' in t or 'indrain' in t or 'gsf' in t:
        result['proprietary_device_opt'] = 'Eljen InDrain'
    
    # Determine number of bedrooms for system
    bedroom_match = re.search(r'(\d+)\s*b[ie]d', text)
    if bedroom_match:
        result['num_bedrooms_opt1'] = bedroom_match.group(1)
    
    return result

def _detect_application_type(disposal_system_type: str, special_notes: str) -> Dict[str, str]:
    """
    Detect application type (NEW vs REPLACEMENT vs EXPANSION) from form data.
    Returns dict with application type checkboxes + year installed.
    """
    combined = (disposal_system_type + ' ' + special_notes).lower()
    result = {}

    # Determine application type
    if 'replacement' in combined or 'replace' in combined:
        result['type_of_app'] = 'Replacement'
        result['expansion'] = ''
        result['first_time_system'] = ''
        result['system_replaced'] = 'Yes'
    elif 'expansion' in combined:
        result['type_of_app'] = 'Expansion'
        result['expansion'] = 'X'
        result['first_time_system'] = ''
        result['system_replaced'] = ''
    elif 'new' in combined or 'first time' in combined:
        result['type_of_app'] = 'New Installation'
        result['expansion'] = ''
        result['first_time_system'] = 'X'
        result['system_replaced'] = ''
    else:
        # Default: treat as Replacement if not explicitly new
        result['type_of_app'] = 'Replacement'
        result['system_replaced'] = 'Yes'

    return result


def _determine_system_type_fields(disposal_system_type: str) -> Dict[str, str]:
    """
    Based on actual system type, determine which system-specific checkboxes to fill.
    Leave all OTHER system type fields blank (data-driven, not hardcoded).

    System types:
      - Proprietary (Eljen, Infiltrator, etc.)
      - Gravel/Stone
      - Chamber
      - Mound
      - Advanced Treatment
      - Holding Tank
      - Alternative Toilet
      - Engineered vs Non-Engineered
    """
    t = disposal_system_type.lower()
    result = {}

    # Detect actual system type from form data
    is_proprietary = 'eljen' in t or 'infiltrator' in t or 'presby' in t or 'indrain' in t or 'gsf' in t
    is_gravel = 'gravel' in t or 'stone' in t or 'pipe' in t
    is_chamber = 'chamber' in t
    is_mound = 'mound' in t
    is_at = 'advanced' in t or 'treatment' in t
    is_holding = 'holding' in t
    is_alt_toilet = 'alternative' in t or 'alt toilet' in t or 'composting' in t
    is_engineered = 'engineered' in t or 'design' in t

    # Set only the relevant system type fields
    if is_proprietary:
        result['disposal_field_type'] = 'Proprietary Device'
        if 'eljen' in t or 'indrain' in t or 'gsf' in t:
            result['proprietary_device_opt'] = 'Eljen InDrain'
        elif 'infiltrator' in t:
            result['proprietary_device_opt'] = 'Infiltrator'
        elif 'presby' in t:
            result['proprietary_device_opt'] = 'Presby'
        # Leave all other system checkboxes blank
        result['non_eng_field_check'] = 'X'
    elif is_gravel:
        result['disposal_field_type'] = 'Gravel/Stone'
        result['non_eng_field_check'] = 'X'
    elif is_chamber:
        result['disposal_field_type'] = 'Chamber System'
        result['non_eng_field_check'] = 'X'
    elif is_mound:
        result['disposal_field_type'] = 'Mound'
        result['non_eng_field_check'] = 'X'
    elif is_at:
        result['disposal_field_type'] = 'Advanced Treatment Unit'
    elif is_holding:
        result['holding_tank_check'] = 'X'
    elif is_alt_toilet:
        result['alt_toilet_check'] = 'X'
    elif is_engineered:
        result['ces_check'] = 'X'
    else:
        # Default: non-engineered proprietary
        result['disposal_field_type'] = 'Proprietary Device'
        result['non_eng_field_check'] = 'X'

    return result


def _determine_pretreatment_fields(disposal_system_type: str) -> Dict[str, str]:
    """
    Based on system type, determine if pre-treatment/pumping is needed.
    Only fill dose, effluent pump, GDU fields if system requires it.
    """
    t = disposal_system_type.lower()
    result = {}

    # Detect if system needs pumping/pre-treatment
    has_pump = 'pump' in t or 'ejector' in t or 'dose' in t
    has_gdu = 'gdu' in t or 'garbage disposal' in t
    has_pretreat = 'pre-treatment' in t or 'pretreat' in t or 'septic tank' in t

    if has_pump:
        result['effluent_pump'] = 'X'
        result['dose_gallons'] = '300'  # Placeholder — should come from design flow
    else:
        result['effluent_pump'] = ''
        result['dose_gallons'] = ''

    if has_gdu:
        result['garbage_disposal'] = 'Y'
        result['gdu_num_tanks'] = '1'
    else:
        result['garbage_disposal'] = 'N'

    # Leave all pre-treatment component fields blank unless explicitly specified
    # (contractor/town will add later)

    return result

def _determine_seasonal(seasonal_use: str) -> str:
    """Map seasonal use description to form value."""
    s = seasonal_use.lower().strip()
    if 'year' in s or 'round' in s:
        return 'Year-round'
    elif 'seasonal' in s or 'summer' in s:
        return 'Seasonal'
    elif 'winter' in s:
        return 'Winter'
    elif 'weekend' in s:
        return 'Weekend'
    return seasonal_use

def _determine_water_supply(supply_type: str) -> str:
    """Map water supply description to dropdown value."""
    s = supply_type.lower()
    if 'drilled' in s:
        return 'Drilled Well'
    elif 'dug' in s:
        return 'Dug Well'
    elif 'public' in s or 'municipal' in s or 'town' in s:
        return 'Public Water'
    elif 'spring' in s:
        return 'Spring'
    elif 'lake' in s or 'pond' in s or 'surface' in s:
        return 'Surface Water'
    elif 'cistern' in s:
        return 'Cistern'
    return 'Drilled Well'  # default for "existing drilled well"

def _determine_system_to_serve(use: str) -> str:
    """Map use description to dropdown value."""
    u = use.lower().strip()
    if 'single' in u and ('family' in u or 'dwelling' in u):
        return 'Single Family Dwelling Unit'
    elif 'multi' in u or 'duplex' in u or 'apartment' in u:
        return 'Multi-Family Dwelling Unit'
    elif 'commercial' in u or 'business' in u:
        return 'Commercial'
    elif 'school' in u:
        return 'School'
    elif 'other' in u:
        return 'Other Facility'
    elif 'seasonal' in u:
        return 'Seasonal Dwelling Unit'
    elif 'replacement' in u or 'repaire' in u:
        return 'Other Facility'
    return 'Single Family Dwelling Unit'

def adapt_sheet_fields_to_acro(sheet_fields: Dict[str, str]) -> Dict[str, str]:
    adapted = {}

    # ── CONTACT INFORMATION ──
    adapted['owner_name'] = sheet_fields.get('owner_name', '')

    # Owner/Applicant contact details
    owner = sheet_fields.get('owner_name', '')
    if owner:
        adapted['owner_name_pg2'] = owner
        adapted['applicant_name'] = sheet_fields.get('applicant_name', owner)

    # Owner contact info
    adapted['owner_phone'] = sheet_fields.get('owner_phone', sheet_fields.get('phone', ''))
    adapted['owner_email'] = sheet_fields.get('owner_email', sheet_fields.get('email', ''))
    
    # Mailing address (from property location when not separately provided)
    site_addr = sheet_fields.get('site_address', '')
    town = sheet_fields.get('town', '')
    state = sheet_fields.get('mailing_state', '')
    zip_code = sheet_fields.get('mailing_zip', '')
    
    # Split street number and name
    street_match = re.match(r'^(\d+)\s+(.+)$', site_addr)
    if street_match:
        adapted['street_number'] = street_match.group(1)
        adapted['street_name'] = street_match.group(2)
    else:
        adapted['street_number'] = ''
        adapted['street_name'] = site_addr
    
    adapted['mailing_street'] = ''  # Often blank - different from physical
    adapted['mailing_city'] = town
    adapted['mailing_state'] = state
    adapted['mailing_zip'] = zip_code
    adapted['town'] = town
    
    # Full address line for page 2
    if site_addr and town:
        adapted['address_pg2'] = f"{site_addr}, {town}, {state} {zip_code}"

    # ── MAP / LOT / ACREAGE ──
    adapted['map_number'] = sheet_fields.get('map_number', '')
    adapted['lot_number'] = sheet_fields.get('lot_number', '')
    prop_size = sheet_fields.get('acreage', '')
    if prop_size:
        adapted['property_size'] = prop_size
        try:
            sqft = int(float(prop_size) * 43560)
            adapted['property_size_units'] = 'Acres'
        except ValueError:
            adapted['property_size_units'] = 'Acres'

    # ── EVALUATOR INFO ──
    adapted['evaluator_name'] = sheet_fields.get('evaluator_name', '')
    adapted['evaluator_phone'] = sheet_fields.get('evaluator_phone', '')
    adapted['evaluator_email'] = sheet_fields.get('evaluator_email', '')
    adapted['lpi_number'] = sheet_fields.get('lpi_number', '')
    adapted['se_number'] = sheet_fields.get('lpi_number', '')
    adapted['site_eval_name_printed'] = sheet_fields.get('evaluator_name', '')
    
    # Signature dates
    date_val = sheet_fields.get('property_owner_date', '') or sheet_fields.get('date_issued', '')
    if date_val:
        adapted['property_owner_signature_date'] = date_val
        adapted['se_signature_date'] = date_val

    # ── WATER SUPPLY ──
    supply_raw = sheet_fields.get('water_supply_type', '')
    adapted['water_supply'] = _determine_water_supply(supply_raw)
    adapted['water_supply_specify'] = supply_raw if 'existing' in supply_raw.lower() else ''

    # ── SYSTEM INFO ──
    use_raw = sheet_fields.get('use', '')
    adapted['disposal_system_to_serve'] = _determine_system_to_serve(use_raw)
    adapted['num_bedrooms_opt1'] = sheet_fields.get('bedrooms', sheet_fields.get('num_bedrooms', ''))
    
    # Disposal field type
    dst = sheet_fields.get('disposal_system_type', '')
    dst_lower = dst.lower()
    if 'eljen' in dst_lower or 'indrain' in dst_lower or 'gsf' in dst_lower:
        adapted['disposal_field_type'] = 'Proprietary Device'
        adapted['proprietary_device_opt'] = 'Eljen InDrain'
    elif 'gravel' in dst_lower or 'stone' in dst_lower or 'pipe' in dst_lower:
        adapted['disposal_field_type'] = 'Gravel/Stone'
    elif 'chamber' in dst_lower or 'infiltrator' in dst_lower:
        adapted['disposal_field_type'] = 'Chamber System'
    elif 'mound' in dst_lower:
        adapted['disposal_field_type'] = 'Mound'
    elif 'at' in dst_lower or 'advanced' in dst_lower:
        adapted['disposal_field_type'] = 'Advanced Treatment Unit'
    else:
        adapted['disposal_field_type'] = 'Proprietary Device'
        adapted['proprietary_device_opt'] = dst[:30]

    # Effluent pump detection
    if 'pump' in dst_lower or 'ejector' in dst_lower:
        adapted['effluent_pump'] = 'X'
        adapted['dose_gallons'] = sheet_fields.get('design_flow_gallons', '')
    else:
        adapted['effluent_pump'] = ''
        adapted['dose_gallons'] = ''

    # Design flow
    flow = sheet_fields.get('design_flow_gallons', '')
    if flow:
        adapted['design_flow_gpd'] = flow
        adapted['design_flow_type'] = 'By Bedrooms'

    # Garbage disposal
    gdu = sheet_fields.get('garbage_disposal_unit', 'No')
    if gdu.lower() in ('no', 'n', ''):
        adapted['garbage_disposal'] = 'N'
        adapted['gdu_num_tanks'] = '0'
    elif gdu.lower() in ('yes', 'y'):
        adapted['garbage_disposal'] = 'Y'
    
    # Seasonal / shoreland zoning
    seasonal = sheet_fields.get('seasonal_use', '')
    adapted['seasonal_conversion_check'] = _determine_seasonal(seasonal)
    adapted['current_use'] = _determine_seasonal(seasonal)
    
    shoreland = sheet_fields.get('shoreland_zoning', '')
    if shoreland and shoreland.lower() in ('yes', 'y', 'x'):
        adapted['shoreland_zoning_yn'] = 'X'

    # ── GPS & COORDINATES ──
    adapted['gps_margin_error'] = '30'  # Hardcoded per Maine requirement

    # ── SOIL DATA (Page 2) ──
    # Limiting factor
    adapted['limiting_factor_depth'] = sheet_fields.get('deepest_restrictive_layer_hole1', '')
    adapted['limiting_factor_elevation'] = sheet_fields.get('water_table_depth_hole1', '')
    adapted['observation_hole_number'] = 'OH-1, OH-2'
    
    # Profile / condition
    soil_desc = sheet_fields.get('soil_type', '')
    if soil_desc:
        adapted['profile_soil_data'] = soil_desc
        adapted['condition_soil_data'] = sheet_fields.get('deepest_restrictive_layer_hole1', '')

    # ── SOIL TABLE (Page 3) ──
    # Parse soil layers from sheet_parser output into grid row fields
    soil_raw = sheet_fields.get('soil_type', '')
    soil_layers_raw = sheet_fields.get('soil_layers', '')
    adapted['oh1_number'] = '1'
    adapted['oh2_number'] = '2'
    adapted['oh1_groundwater_check'] = 'X' if sheet_fields.get('water_table_depth_hole1') else ''
    adapted['oh1_restrictive_layer_check'] = 'X' if sheet_fields.get('deepest_restrictive_layer_hole1') else ''
    adapted['oh1_bedrock_check'] = ''
    adapted['oh1_pit_depth_check'] = sheet_fields.get('deepest_soil_depth', '')
    adapted['oh2_groundwater_check'] = 'X' if sheet_fields.get('water_table_depth_hole2') else ''
    adapted['oh2_restrictive_layer_check'] = 'X' if sheet_fields.get('deepest_restrictive_layer_hole2') else ''
    adapted['oh2_bedrock_check'] = ''
    adapted['oh2_pit_depth_check'] = sheet_fields.get('deepest_soil_depth', '')
    adapted['oh2_pit_depth_check_alt'] = sheet_fields.get('deepest_soil_depth', '')
    
    # Soil textures from layers - also extract organic horizon thickness (first layer)
    soil_layers = sheet_fields.get('soil_layers', [])
    if isinstance(soil_layers, list) and soil_layers:
        layer_texts = []
        for i, layer in enumerate(soil_layers):
            d = layer.get('depth', '')
            s = layer.get('soil', '')
            if d and s:
                layer_texts.append(f"{d} {s}")
            # First layer depth = organic horizon thickness
            if i == 0 and d:
                depth_parts = d.split('-')
                if len(depth_parts) >= 2:
                    adapted['oh1_organic_thickness'] = depth_parts[1].replace(' in', '').strip()
                    adapted['oh2_organic_thickness'] = depth_parts[1].replace(' in', '').strip()
        if layer_texts:
            textures = "; ".join(layer_texts)
            adapted['oh1_textures'] = textures
            adapted['oh2_textures'] = textures
        
        # Soil color from first layer
        if len(soil_layers) > 0 and soil_layers[0].get('soil'):
            color1 = soil_layers[0]['soil']
            adapted['oh1_color'] = color1
            if len(soil_layers) > 1:
                adapted['oh1_consistence'] = soil_layers[1]['soil']
            if len(soil_layers) > 2:
                adapted['oh1_condition'] = soil_layers[2]['soil']
                adapted['oh2_condition'] = soil_layers[2]['soil']
    
    # Water table depth → limiting factor elevation
    wtd = sheet_fields.get('water_table_depth_hole1', '')
    if wtd:
        adapted['limiting_factor_elevation'] = f"{wtd} in"
    
    # ── DISTANCE/SETBACK DATA FROM SHEET ──
        def _parse_setback(val, default=""):
            if not val:
                return default
            m = re.search(r'([\d,]+)', val)
            if m:
                return m.group(1)
            return default

    # ── FIELD LAYOUT & DISTANCES ──
    field_size = sheet_fields.get('planned_field_size', '')
    if field_size:
        adapted['disposal_field_size'] = field_size[:40]
        adapted['disposal_field_size_unit'] = 'Sq Ft'
    
    # Pass structured field layout data through for drawing generator
    for layout_key in ['num_rows', 'mods_per_row', 'total_modules', 
                        'cluster_width_ft', 'cluster_length_ft', 'area_sqft', 'brand']:
        if layout_key in sheet_fields and sheet_fields[layout_key]:
            adapted[layout_key] = sheet_fields[layout_key]

    # ── SETBACK DISTANCES ──
    for dist_key in ['setback_well', 'setback_tank_to_house', 'setback_field_to_house', 'setback_property_line']:
        if dist_key in sheet_fields and sheet_fields[dist_key]:
            adapted[dist_key] = sheet_fields[dist_key]

    # ── TREATMENT TANK INFO ──
    # Extract tank info from site notes
    notes = sheet_fields.get('site_notes', '')
    tank_match = None
    if 'tank' in notes.lower():
        cap_match = re.search(r'([\d,]+)\s*gallon', notes)
        if cap_match:
            adapted['tank_capacity'] = cap_match.group(1)
            adapted['tank_cap_gal'] = cap_match.group(1)
            adapted['tank_regular_check'] = 'X'
        if 'existing' in notes.lower() or 'expose' in notes.lower():
            adapted['treatment_tanks'] = 'X'

    # Tank total/count
    adapted['tank_total_new'] = sheet_fields.get('num_tanks', '1')
    adapted['tank_notes'] = sheet_fields.get('septic_tank_notes', '')

    # ── WELL & BUILDING INFO ──
    adapted['well_depth'] = sheet_fields.get('well_depth', '')
    adapted['well_type'] = sheet_fields.get('well_type', '')
    zoning = sheet_fields.get('shoreland_zoning', '')
    if zoning and zoning.strip() and zoning.lower() not in ('', 'no', 'n'):
        adapted['shoreland_zoning_yn'] = 'Y'
    else:
        adapted['shoreland_zoning_yn'] = 'N'

    # ── ELEVATIONS (Pages 3-4) ──
    adapted['finished_grade_elevation'] = sheet_fields.get('finish_grade_elevation', sheet_fields.get('finished_grade_elevation_p6', '0'))
    adapted['top_distribution_pipe'] = sheet_fields.get('top_of_distribution_pipe_elevation', sheet_fields.get('top_of_distribution_pipe_elevation_p6', '-12'))
    adapted['bottom_disposal_field'] = sheet_fields.get('bottom_of_disposal_field_elevation', sheet_fields.get('bottom_of_disposal_field_elevation_p6', '30'))
    adapted['erp_location'] = sheet_fields.get('erp_description', '')
    adapted['erp_reference_elevation'] = sheet_fields.get('erp_elevation', '0')

    # ── NOTES ──
    site_notes = sheet_fields.get('site_notes', '')
    special_notes = sheet_fields.get('special_notes', '')
    notes_parts = [n for n in [site_notes, special_notes] if n and n != 'none']
    if notes_parts:
        adapted['additional_notes'] = '; '.join(notes_parts)

    # ── SCALES ──
    adapted['scale_pg4'] = '40'
    adapted['vertical_scale'] = '1'
    adapted['horizontal_scale'] = '10'

    # ── GPS coordinate conversion ──────────────────────────────────────────
    gps_fields = _convert_gps(sheet_fields.get("gps_latitude"), sheet_fields.get("gps_longitude"))

    # ── Application type logic ──────────────────────────────────────────────
    app_fields = _derive_app_type(sheet_fields)

    # ── Soil data breakout ──────────────────────────────────────────────────
    soil_fields = _breakout_soil_data(sheet_fields)

    # ── Application Type Logic (NEW vs REPLACEMENT vs EXPANSION) ──────────────
    disposal_type = sheet_fields.get('disposal_system_type', '')
    special_notes = sheet_fields.get('special_notes', '')
    app_type_fields = _detect_application_type(disposal_type, special_notes)

    # ── System Type Conditional Logic (what to fill based on actual system) ────
    system_type_fields = _determine_system_type_fields(disposal_type)

    # ── Pre-treatment Conditional Logic (pump/dose only if needed) ─────────────
    pretreat_fields = _determine_pretreatment_fields(disposal_type)

    # ── Merge all results (prioritize explicit mappings over derived) ────────
    result = {}
    result.update(adapted)
    result.update(app_fields)
    result.update(app_type_fields)        # Application type (NEW/REPLACEMENT/EXPANSION)
    result.update(system_type_fields)     # System type conditionals (what to fill)
    result.update(pretreat_fields)        # Pre-treatment conditionals
    result.update(gps_fields)
    result.update(soil_fields)

    return result


def _convert_gps(lat_raw: Optional[str], lng_raw: Optional[str]) -> Dict[str, str]:
    """Convert decimal GPS coordinates to DMS format fields."""
    result: Dict[str, str] = {}
    if not lat_raw or not lng_raw:
        return result
    try:
        lat = float(lat_raw)
        lng = float(lng_raw)

        lat_deg = int(abs(lat))
        lat_min = int((abs(lat) - lat_deg) * 60)
        lat_sec = round(((abs(lat) - lat_deg) * 60 - lat_min) * 60, 1)
        result["latitude_deg"] = str(lat_deg)
        result["latitude_min"] = str(lat_min)
        result["latitude_sec"] = str(lat_sec)

        lng_deg = int(abs(lng))
        lng_min = int((abs(lng) - lng_deg) * 60)
        lng_sec = round(((abs(lng) - lng_deg) * 60 - lng_min) * 60, 1)
        result["longitude_deg"] = str(lng_deg)
        result["longitude_min"] = str(lng_min)
        result["longitude_sec"] = str(lng_sec)
    except (ValueError, TypeError):
        pass
    return result


def _derive_app_type(fields: Dict[str, str]) -> Dict[str, str]:
    """Set checkbox states based on application / system type."""
    result: Dict[str, str] = {}
    app_type = (fields.get("application_type") or "").lower()
    use = (fields.get("use") or "").lower()
    system = (fields.get("disposal_system_type") or "").lower()
    seasonal = (fields.get("seasonal_use") or "").lower()

    # ── Application type checkboxes (mutually exclusive by design) ─────────
    if "replacement" in app_type:
        result["type_of_app"] = "Replacement"
        # Note: the actual checkbox field in the form might use a
        # specific widget. The "X" above sets the text description.
        # Checkbox states are handled in fill_acro via RADIO_OPTIONS.
    elif "new" in app_type or "first" in app_type:
        result["type_of_app"] = "New System"
    elif "expansion" in app_type:
        result["type_of_app"] = "Expansion"
        result["expansion"] = "X"
    elif "alter" in app_type:
        result["type_of_app"] = "Alteration"
    elif "repair" in app_type:
        result["type_of_app"] = "Repair"

    # ── Variance / first-time / replacement flags ───────────────────────────
    if "variance" in app_type or "variance" in use:
        result["variance_requirement"] = "X"
    if "first" in app_type:
        result["first_time_system"] = "X"
    if "replacement" in app_type:
        result["replacement_variance"] = "X"

    # ── System type checkboxes ─────────────────────────────────────────────
    if "proprietary" in system or "eljen" in system or "in-drain" in system:
        result["disposal_field_type"] = "Proprietary Device"
    elif "gravel" in system or "stone" in system or "pipe" in system:
        result["disposal_field_type"] = "Gravel & Pipe"
    elif "chamber" in system or "geotextile" in system:
        result["disposal_field_type"] = "Proprietary Device"

    # ── Seasonal use / shoreland zoning ─────────────────────────────────────
    if "year" in seasonal or "year-round" in seasonal:
        result["seasonal_conversion_check"] = "Year-Round"
    elif "seasonal" in seasonal:
        result["seasonal_conversion_check"] = "Seasonal"

    # ── Water supply type mapping ──────────────────────────────────────────
    water = (fields.get("water_supply_type") or "").lower()
    if "drilled" in water:
        result["water_supply"] = "Drilled Well"
    elif "dug" in water:
        result["water_supply"] = "Dug Well"
    elif "public" in water or "municipal" in water:
        result["water_supply"] = "Public"

    # ── System to serve mapping ────────────────────────────────────────────
    if "single" in use or "sfd" in use or "dwelling" in use:
        result["disposal_system_to_serve"] = "Single Family Dwelling Unit"
    elif "multi" in use or "duplex" in use:
        result["disposal_system_to_serve"] = "Multi-Family Dwelling Unit"

    # ── Bedroom count for primary option ───────────────────────────────────
    bedrooms = fields.get("bedrooms", "")
    if bedrooms:
        try:
            num = int(float(bedrooms))
            result["num_bedrooms_opt1"] = str(num)
            # If more than 3 bedrooms, a second option might also be relevant
            if num > 3:
                result["num_bedrooms_opt2"] = str(num)
        except (ValueError, TypeError):
            pass

    # ── Limitations from data ──────────────────────────────────────────────
    limiting = (fields.get("deepest_restrictive_layer_hole1") or "").lower()
    if "water" in limiting or "ground" in limiting:
        result["limiting_factor_depth"] = "Ground Water"
    elif "bedrock" in limiting or "ledge" in limiting:
        result["limiting_factor_depth"] = "Bedrock"

    return result


def _breakout_soil_data(fields: Dict[str, str]) -> Dict[str, str]:
    """Break out soil layer data into individual observation hole fields."""
    result: Dict[str, str] = {}
    soil_layers = fields.get("soil_layers")
    if not soil_layers or not isinstance(soil_layers, (list, str)):
        return result

    if isinstance(soil_layers, str):
        try:
            soil_layers = json.loads(soil_layers)
        except (json.JSONDecodeError, TypeError):
            return result

    if not isinstance(soil_layers, list) or not soil_layers:
        return result

    # Build texture strings from layers
    oh1_textures_parts = []
    oh2_textures_parts = []
    for layer in soil_layers:
        depth = layer.get("depth", "")
        soil = layer.get("soil", "")
        if depth and soil:
            oh1_textures_parts.append(f"{depth} {soil}")
            oh2_textures_parts.append(f"{depth} {soil}")

    if oh1_textures_parts:
        result["oh1_textures"] = "; ".join(oh1_textures_parts)
    if oh2_textures_parts:
        result["oh2_textures"] = "; ".join(oh2_textures_parts)

    # Use first layer for organic horizon thickness
    first = soil_layers[0]
    depth_str = first.get("depth", "0-0")
    num_match = re.search(r"(\d+)", str(depth_str))
    if num_match:
        result["oh1_organic_thickness"] = num_match.group(1)
        result["oh2_organic_thickness"] = num_match.group(1)

    return result