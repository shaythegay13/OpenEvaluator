#!/usr/bin/env python3
"""Fill HHE-200 AcroForm widgets and draw DXF site plan on pages 3 and 4."""

from pathlib import Path
from typing import Dict, List, Optional
import sys

# Import field coordinates
sys.path.insert(0, str(Path(__file__).parent))
try:
    from field_coordinates import get_page_fields, map_field_name
except ImportError:
    get_page_fields = None
    map_field_name = lambda x: x

PDF_PATH = Path(__file__).parent / "HHE-200-2025.pdf"

WIDGET_MAP: Dict[str, List[str]] = {
    # ── Page 1 ───────────────────────────────────────────────────────────────
    "street_number":          ["Street #"],
    "street_name":            ["Street Name"],
    "town":                   ["City/ Town/ Plantation"],
    "map_number":             ["Map #"],
    "lot_number":             ["Lot #"],
    "owner_name":             ["Owner Name"],
    "applicant_name":         ["Applicant Name"],
    "mailing_street":         ["Street (Mailing Address)"],
    "mailing_city":           ["City (Mailing Address)"],
    "mailing_state":          ["State (Mailing Address)"],
    "mailing_zip":            ["Zip Code (Mailing Address)"],
    "owner_phone":            ["Owner/ Applicant Phone Number"],
    "owner_email":            ["Owner/ Applicant Email"],
    "property_owner_signature_date": ["Date (Property Owner Signature)"],
    "installer_name":         ["Installer Name"],
    "installer_phone":        ["Installer Phone #"],
    "installer_email":        ["Installer Email"],
    "issuing_municipality":   ["Issuing Municipality or Territory"],
    "permit_number":          ["Permit #"],
    "permit_issued_date":     ["Permit Issued Date"],
    "lpi_number":             ["LPI #"],
    "lpi_inspection1_date":   ["Date for First LPI Inspection"],
    "lpi_inspection2_date":   ["Date for Second LPI Inspection"],
    "fee_area":               ["Fee Calculation Area"],
    "total_fee":              ["Total Fee"],
    "town_share":             ["Town Share"],
    "state_25_pct":           ["State 25%"],
    "dep_wqs":                ["DEP WQS"],
    "revision_check":         ["Revision Check Box"],
    "doubled_fee_check":      ["Doubled Fee Check Box"],
    "variance_check":         ["Variance Check Box"],
    "seasonal_conversion_check": ["Seasonal Conversion Check Box"],
    "type_of_app":            ["Type of Application"],
    "system_replaced":        ["Type of System Replaced"],
    "year_installed":         ["Year Installed"],
    "expansion":              ["Expansion"],
    "variance_requirement":   ["Variance Requirement"],
    "first_time_system":      ["First Time System Requirement"],
    "replacement_variance":   ["Replacement Variance Requirement"],
    "treatment_tanks":        ["Treatment Tanks"],
    "tank_regular_check":     ["Regular Check Box (Treatment Tank)"],
    "tank_low_profile_check": ["Low Profile Check Box (Treatment Tank)"],
    "tank_h20_check":         ["H-20 Check Box (Treatment Tank)"],
    "tank_capacity":          ["Capacity (Treatment Tank)"],
    "tank_specify_other":     ["Specify Other Tank (Treatment Tank)"],
    "tank_cap_gal":           ["Tank Capacity (Treatment Tank)"],
    "tank_total_new":         ["Total # of New Tanks (Treatment Tank)"],
    "tank_notes":             ["Notes (Treatment Tank)"],
    "risers_required_check":  ["Risers Required Checkbox"],
    "cnes_check":             ["Complete Non-Engineered System Check Box"],
    "cnes_total_tanks":       ["Specify Total Number of New Tanks (CNES)"],
    "primitive_limited_check": ["Primitive/ Limited System Check Box"],
    "primitive_limited_type": ["Specify Type (Primitive/ Limited System)"],
    "alt_toilet_check":       ["Alternative Toilet Check Box"],
    "alt_toilet_type":        ["Specify Type (Alt Toilet)"],
    "non_eng_tank_check":     ["Non-Engineered Treatment Tank Check Box"],
    "non_eng_tank_number":    ["Specify # of New Tanks (Non-Engineered Disposal Field)"],
    "holding_tank_check":     ["Holding Tank Check Box"],
    "non_eng_field_check":    ["Non-Engineered Disposal Field Check Box"],
    "ces_check":              ["Complete Engineered System Check Box"],
    "ces_tanks":              ["# of New Disposal Tanks"],
    "ces_new_tanks":          ["# of New Tanks (CES)"],
    "ces_pumps":              ["# of Pumps (CES)"],
    "eng_tank_check":         ["Engineered Tank Check Box"],
    "eng_tank_number":        ["Specify # of New Tanks (Engineered Tank)"],
    "eng_field_check":        ["Engineered Field Check Box"],
    "misc_components_check":  ["Misc. Components Check Box"],
    "misc_components_specify": ["Specify (Misc. Components)"],
    "pre_treatment_tank_check": ["Pre-Treatment Tank Check Box"],
    "pre_treatment_comp_check": ["Pre-Treatment Component Check Box"],
    "evaluator_name":         ["Site Evaluator Name"],
    "evaluator_phone":        ["Site Evaluator Phone #"],
    # SE # (with space) on pages 1,2,5 and SE# (no space) on pages 3,4
    "se_number":              ["SE #", "SE#"],
    # One key covers all SE date variants across all pages
    "se_signature_date":      [
        "Date of Site Evaluator Signature",
        "Date of SE signature/ initial (pg2)",
        "Date of SE signature / initial-pg3 grid",
        "Date of SE signature/ initials- pg3 blank",
        "Date of SE Sig (pg 4 grid)",
        "Date of SE sig (pg 4 blank)",
        "Date of SE signature on Alt Page 3",
        "Date of SE signature (alt design pg)",
    ],
    "evaluator_email":        ["Site Evaluator Email"],

    # ── Page 2 ───────────────────────────────────────────────────────────────
    # Owner / Address appear on pages 2-8 with the same widget name
    "owner_name_pg2":         ["Owner"],
    "address_pg2":            ["Address"],
    "property_size":          ["Property Size"],
    "property_size_units":    ["property size measurement"],
    "shoreland_zoning_yn":    ["SLZ y/n"],
    "current_use":            ["Current Use"],
    "latitude_deg":           ["Latitude (degrees)"],
    "latitude_min":           ["Latitude (minutes)"],
    "latitude_sec":           ["Latitude (seconds)"],
    "longitude_deg":          ["Longitude (degrees)"],
    "longitude_min":          ["Longitude (minutes)"],
    "longitude_sec":          ["Longitude (seconds)"],
    "gps_margin_error":       ["GPS margin of error"],
    "water_supply":           ["Type of Water Supply"],
    "water_supply_specify":   ["specify box (type of water supply)"],
    "effluent_pump":          ["Effluent/Ejector Pump"],
    "dose_gallons":           ["Dose (Engineered Systems)"],
    "garbage_disposal":       ["GDU Y/N/M"],
    "gdu_if_yes":             ["GDU if yes"],
    "disposal_system_to_serve": ["Disposal System to Serve"],
    "num_bedrooms_opt1":      ["# of bedrooms for option 1 (disposal system to serve)"],
    "num_bedrooms_opt2":      ["# of bedrooms for option 2 (disposal system to serve)"],
    "num_bedrooms_opt3":      ["# of bedrooms for option 3 (disposal system to serve)"],
    "disposal_field_type":    ["Disposal Field Type & Size"],
    "proprietary_device_opt": ["Proprietary Device Options"],
    "disposal_field_size":    ["size (disposal field type and size)"],
    "disposal_field_size_unit": ["Disposal Field Size Measurement"],
    "design_flow_gpd":        ["gallons per day (design flow)"],
    "design_flow_type":       ["Design Flow"],
    "profile_soil_data":      ["profile (soil data & design class)"],
    "condition_soil_data":    ["condition (soil data & design class)"],
    "observation_hole_number": ["observation hole # (soil data & design class)"],
    "limiting_factor_depth":  ["limiting factor depth (soil data & design class)"],
    "limiting_factor_elevation": ["limiting factor elevation (soil data & design class)"],
    "additional_notes":       ["Additional Notes"],
    "pre_treatment_make1":    ["make #1 (pre-treatment)"],
    "pre_treatment_model1":   ["model #1 (pre-treatment)"],
    "pre_treatment_notes1":   ["Notes #1 (pre-treatment)"],
    "pre_treatment_make2":    ["make #2 (pre-treatment)"],
    "pre_treatment_model2":   ["model #2 (pre-treatment)"],
    "pre_treatment_notes2":   ["Notes #2 (pre-treatment)"],

    # ── Page 3: Observation Hole 1 ────────────────────────────────────────────
    "oh1_number": [
        "Observation Hole-table1-grid", "Observation Hole-table1-blank", "Observation Hole_table1",
    ],
    "oh1_test_pit": [
        "Test Pit-table1-grid", "Test Pit-table1-blank", "Test Pit_table1",
    ],
    "oh1_boring": [
        "Boring-table1-grid", "Boring-table1-blank", "Boring_table1",
    ],
    "oh1_organic_thickness": [
        "Organic Horizon Thickness-table1-grid", "Organic Horizon Thickness-table1-blank",
        "Organic Horizon Thickness_table1",
    ],
    "oh1_ground_surface": [
        "Ground Surface Elevation-table1-grid", "Ground Surface Elevation-table1-blank",
        "Ground Surface Elevation_table1",
    ],
    "oh1_depth_exploration": [
        "Depth to Exploration or Refusal-table1-grid", "Depth to Exploration or Refusal-table1-blank",
        "Depth to Exploration or Refusal_table1",
    ],
    "oh1_textures": [
        "Textures-table1-grid", "Textures-table1-blank", "Textures_table1",
    ],
    "oh1_consistence": [
        "Cosistence-table1-grid",   # typo in original PDF
        "Consistence-table1-blank", "Consistence_table1",
    ],
    "oh1_color": [
        "Color-table1-grid", "Color-table1-blank", "Color_table1",
    ],
    "oh1_redox": [
        "Redox Features-table1-grid", "Redox Features-table1-blank", "Redox Features_table1",
    ],
    "oh1_profile": [
        "Profile-table1-grid", "Profile-table1-blank", "Profile_table1",
    ],
    "oh1_condition": [
        "Condition-table1-grid", "Condition-table1-blank", "Condition_table1",
    ],
    "oh1_slope": [
        "Slope-table1-grid", "Slope-table1-blank", "Slope_table1",
    ],
    "oh1_limiting_factor": [
        "Limiting Factor-table1-grid", "Limiting Factor-table1-blank", "Limiting Factor_table1",
    ],
    "oh1_groundwater_check": [
        "Ground water- table1-grid",  # note: trailing space is in original PDF
        "Ground Water- table1-blank", "Groundwater_table1",
    ],
    "oh1_restrictive_layer_check": [
        "Restrictive Layer-table1-grid", "Restrictive Layer-table1-blank", "RestrictiveLayer_table1",
    ],
    "oh1_bedrock_check": [
        "Bedrock-table1-grid", "Bedrock-table1-blank", "Bedrock_table1",
    ],
    "oh1_pit_depth_check": [
        "Pit Depth-table1-grid", "Pit Depth-table1-blank", "Pit Depth_table1",
    ],

    # ── Page 3: Observation Hole 2 ────────────────────────────────────────────
    "oh2_number": [
        "Observation Hole-table2-grid", "Observation Hole-table2-blank", "Observation Hole_table2",
    ],
    "oh2_test_pit": [
        "Test Pit-table2-grid", "Test Pit-table2-blank", "Test Pit_table2",
    ],
    "oh2_boring": [
        "Boring-table2-grid", "Boring-table2-blank", "Boring_table2",
    ],
    "oh2_pit_depth_check": [
        "Pit Depth-table2-grid", "Pit Depth-table2-blank", "Pit Depth_table2",
    ],
    "oh2_organic_thickness": [
        "Organic Horizon Thickness-table2-grid", "Organic Horizon Thickness-table2-blank",
        "Organic Horizon Thickness_table2",
    ],
    "oh2_ground_surface": [
        "Ground Surface Elevation-table2-grid", "Ground Surface Elevation-table2-blank",
        "Ground Surface Elevation_table2",
    ],
    "oh2_depth_exploration": [
        "Depth to Exploration or Refusal-table2-grid", "Depth to Exploration or Refusal-table2-blank",
        "Depth to Exploration or Refusal_table2",
    ],
    "oh2_textures": [
        "Textures-table2-grid", "textures-table2-grid",
        "Textures-table2-blank", "Textures_table2",
    ],
    "oh2_consistence": [
        "Consistence-table2-grid", "Cosistence-table2-grid",
        "Consistence-table2-blank", "Consistence_table2",
    ],
    "oh2_color": [
        "Color-table2-grid", "Color-table2-blank", "Color_table2",
    ],
    "oh2_redox": [
        "Redox Features-table2-grid", "Redox Features-table2-blank", "Redox Features_table2",
    ],
    "oh2_profile": [
        "Profile-table2-grid", "Profile-table2-blank", "Profile_table2",
    ],
    "oh2_condition": [
        "Condition-table2-grid", "Condition-table2-blank", "Condition_table2",
    ],
    "oh2_slope": [
        "Slope-table2-grid", "Slope-table2-blank", "Slope_table2",
    ],
    "oh2_limiting_factor": [
        "Limiting Factor-table2-grid", "Limiting Factor-table2-blank", "Limiting Factor_table2",
    ],
    "oh2_groundwater_check": [
        "Ground water-table2-grid", "Ground Water-table2-blank", "Groundwater_table2",
    ],
    "oh2_restrictive_layer_check": [
        "Restrictive Layer-table2-grid", "Restrictive Layer-table2-blank", "RestrictiveLayer_table2",
    ],
    "oh2_bedrock_check": [
        "Bedrock-table2-grid", "Bedrock-table2-blank", "Bedrock_table2",
    ],
    "oh2_pit_depth_check_alt": [
        "PitDepth_table2",
    ],

    # ── Page 5 (output page 4): Backfill / Elevations / Scales ───────────────
    "scale_pg4": [
        "scale (pg 4 grid)", "Scale (pg 4 blank)",
    ],
    "backfill_upslope": [
        "Depth of Backfill (upslope) (pg 4 grid)", "Depth of Backfill (upslope) (pg 4 blank)",
        "Depth of Backfill (upslope)",
    ],
    "backfill_downslope": [
        "Depth of Backfill (downslop) (pg 4 grid)",   # typo in PDF
        "Depth of Backfill (download) (pg 4 blank)",  # different typo
        "Depth of Backfill (downslope)",
    ],
    "finished_grade_elevation": [
        "Finished Grade Elevation (pg 4 grid)", "Finished Grade Elevation (pg 4 blank)",
        "Finished Grade Elevation",
    ],
    "top_distribution_pipe": [
        "Top Distribution Pipe or Proprietary Device (pg 4 grid)",
        "Top of Distribution Pipe or Proprietary Device (pg 4 blank)",
        "Top of Distribution Pipe or Proprietary Device",
    ],
    "bottom_disposal_field": [
        "Bottom of Disposal Field (pg 4 grid)", "Bottom of Disposal Field (pg 4 blank)",
        "Bottom of Disposal Field",
    ],
    "erp_location": [
        "Location & Description (pg 4 grid)", "Location & Description (pg 4 blank)",
        "Location & Description",
    ],
    "erp_reference_elevation": [
        "Reference Elevation (pg 4 grid)", "Reference Elevation (pg 4 blank)",
        "Reference Elevation",
    ],
    "vertical_scale": [
        "Vertical Scale (pg 4 grid)", "Vertical Scale (pg 4 blank)",
    ],
    "horizontal_scale": [
        "Horizontal Scale (pg 4 grid)", "Horizontal Scale (pg 4 blank)",
    ],

    # ── Additional dropdown/specify fields ─────────────────────────────────────
    "gdu_num_tanks": [
        "# of Tanks (garbage disposal unit)",
    ],
    "pre_treatment_maint1": [
        "Maintenance Contract #1 (pre-treatment)",
    ],
    "pre_treatment_maint2": [
        "Maintenance Contract #2 (pre-treatment)",
    ],
    "disposal_field_type_other": [
        "specify for other (disposal field type and size)",
    ],
    "disposal_system_other": [
        "specify for other (disposal system to serve)",
    ],
    "design_flow_calculations": [
        "show calculations for \"other facilities\" (design flow)",
    ],
    "site_eval_name_printed": [
        "Site Evaluator Name (Printed)",
    ],
}

RADIO_OPTIONS: Dict[str, Dict[str, int]] = {
    # Page 1 radio groups
    "Type of Application": {
        "First Time System": 0, "first time system": 0,
        "Replacement System": 1, "replacement system": 1, "Replacement": 1,
        "Expansion": 2,
        "Experimental System": 3,
        "Seasonal Conversion Permit": 4,
    },
    "Variance Requirement": {
        "No Rule Variance": 0,
        "First Time System": 1,
        "Replacement System": 2,
        "Minimum Lot Size": 3,
        "Seasonal Conversion": 4,
    },
    "Treatment Tanks": {
        "Concrete": 0, "Plastic": 1, "External Grease Interceptor": 2, "Other": 3,
    },
    # Page 2 radio groups
    "property size measurement": {"sq ft": 0, "sq. ft.": 0, "sqft": 0, "acres": 1, "acre": 1},
    "SLZ y/n": {"Yes": 0, "Y": 0, "No": 1, "N": 1},
    "Current Use": {
        "Seasonal": 0, "Year-Round": 1, "Year Round": 1,
        "Single Family Residential": 1, "Residential": 1,
        "Undeveloped": 2, "Commercial": 3,
    },
    "Type of Water Supply": {
        "Drilled Well": 0, "Drilled": 0,
        "Dug/ Point Well": 1, "Dug Well": 1, "Dug": 1, "Point Well": 1,
        "Private": 2, "Private Well": 0,
        "Public": 3, "Municipal": 3,
        "Other": 4,
    },
    "Effluent/Ejector Pump": {"Yes": 0, "No": 1, "N": 1, "Maybe": 2},
    "GDU Y/N/M": {"Yes": 0, "No": 1, "N": 1, "Maybe": 2},
    "Disposal System to Serve": {
        "Single Family Dwelling Unit": 0, "Single Family Dwelling": 0,
        "Single Family": 0, "SFD": 0,
        "Multiple Family Dwelling Unit": 1, "Multi-Family": 1,
        "Accessory Dwelling Unit(s)": 2, "ADU": 2,
        "Other": 3,
    },
    "Disposal Field Type & Size": {
        "Stone Bed": 0, "Stone Trench": 1,
        "Proprietary Device": 2, "Eljen": 2, "Infiltrator": 2, "Biodiffuser": 2,
        "Presby": 2, "Geomat": 2, "Other": 3,
    },
    "Proprietary Device Options": {
        "Cluster Array": 0, "Linear": 1, "Regular": 2, "Load Profile": 3, "Load": 3,
    },
    "Disposal Field Size Measurement": {
        "sq ft": 0, "sq. ft.": 0, "sqft": 0, "acres": 1,
        "lin ft": 1, "lin. ft.": 1, "linear ft": 1,  # kept for compat
    },
    "Design Flow": {
        "Table 5A (Dwelling Units)": 0, "Table 5A": 0, "1. Table 5A": 0,
        "Table 5C": 1, "Table 5C (Other Facilities)": 1, "2. Table 5C": 1,
        "Section 5(G)": 2, "Section 5(G) - Meter Readings": 2, "5. Section 5G": 2,
    },
}

# ── Hardcoded text blocks required by Maine DHHS HHE-200 ─────────────────────

SITE_LOCATION_DISCLAIMER = (
    "Note: Location of septic system has been sited on the property based upon boundary "
    "line/property information provided by owner or owner's agent. No independent "
    "verification of boundary line locations has been made by this site evaluator. "
    "Property lines shown shall be verified by owner/installer prior to the construction "
    "of system. Any discrepancy from that shown shall be immediately brought to the "
    "attention of the design site evaluator prior to the beginning of work."
)

PG3_SPECIAL_NOTE = (
    "SPECIAL NOTE: EXISTING DISPOSAL FIELD, EXISTING BIOMATT AND A MINIMUM OF 12 INCHES "
    "OF EXISTING SOIL BELOW PROPOSED DISPOSAL AREA AND FILL EXTENSIONS SHALL BE REMOVED, "
    "WHERE ENCOUNTERED, AND REPLACED WITH SUITABLE SOIL BACKFILL PER SECTION 11(E) OF "
    "THE CODE."
)

PG4_SEPTIC_TANK_NOTE = (
    "SEPTIC TANK NOTE: EXISTING 1,000 GALLON SEPTIC TANK SHALL BE EXPOSED, PUMPED AND "
    "INSPECTED FOR STRUCTURAL INTEGRITY. IF TANK OR BAFFLES ARE DETERIORATED, TANK SHALL "
    "BE REPLACED AND/OR NEW PLASTIC BAFFLES INSTALLED AS APPROPRIATE. INSTALL 18\" DIA "
    "ACCESS RISER PER SECTION 7F(A)(2)."
)

PG4_GENERAL_NOTES = (
    "NOTES:\n"
    "1. REFER TO GENERAL NOTES ON THE BACKSIDE OF THIS PAGE\n"
    "2. ALL DISTURBED AREAS AND FINISHED SURFACE SHALL BE LOAMED, SEEDED, AND MULCHED "
    "TO PREVENT EROSION\n"
    "3. SEPTIC TANK SHALL BE SEALED TO PREVENT GROUND WATER OR SURFACE WATER "
    "INFILTRATION INTO SYSTEM\n"
    "4. PROVIDE SURFACE WATER DRAINAGE (FLOW) AWAY FROM SYSTEM\n"
    "MINIMUM SEPARATION DISTANCES:\n"
    "A) SEPTIC TANK FROM HOUSE 8 FEET\n"
    "   SEPTIC TANK FROM WELL 50 FEET\n"
    "   DISPOSAL FIELD FROM HOUSE 20 FEET\n"
    "   DISPOSAL FIELD FROM WELL 100 FEET"
)

PG4_CROSS_SECTION_LEFT = (
    "XXX DENOTES TRANSITION HORIZON: THE AREA UNDER THE DISPOSAL AREA MUST BE "
    "\"ROUGHENED\" AT LEAST 6\" TO 8\" DEEP, THEN PLACE A MINIMUM OF 4\" OF CLEAN FILL "
    "OVER THIS AREA AND MIX (BY PLOWING, DISKING OR ROTOTILING) INTO ORIGINAL SOIL "
    "PER SECTION 10(B) OF THE \"RULES\""
)

PG4_CROSS_SECTION_RIGHT = (
    "NOTES\n"
    "1) USE ONLY CLEAN \"GRAVELY COARSE SAND\" BACKFILL MATERIAL WHICH MEETS THE BACKFILL "
    "STANDARDS OF SECTION 12(E) OF THE \"RULES\" FREE OF FOREIGN MATERIALS (ROOTS, LARGE "
    "ROCKS, ETC.) PLACED IN 8\" LIFTS AND LIGHTLY COMPACTED AS PLACED.\n"
    "2) REMOVE ALL ORGANIC MATERIALS (ROOTS, STUMPS, AND LARGE ROCKS) UNDER SYSTEM AND "
    "FILL EXTENSIONS AND PREPARE TRANSITION HORIZON BY PLACING A MINIMUM OF 4\" OF CLEAN "
    "FILL OVER ORIGINAL SOIL AND MIX (BY PLOWING, DISKING, OR ROTOTILING) INTO ORIGINAL "
    "SOIL PER SECTION 12(B) OF THE \"RULES\".\n"
    "3) PLACE \"ANTI-SILTATION FABRIC\" OVER MODULES AND PERFORATED DISTRIBUTION PIPES "
    "TO KEEP FINES OUT OF THE ELJEN GSF MODULES."
)


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Word-wrap text preserving explicit newlines."""
    result = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            result.append("")
            continue
        line = ""
        for word in words:
            candidate = (line + " " + word).strip()
            if len(candidate) <= max_chars:
                line = candidate
            else:
                if line:
                    result.append(line)
                line = word
        if line:
            result.append(line)
    return result


def _draw_text_block(page, text: str, x: float, y: float, max_width: float,
                     fontsize: float = 6.5, color: tuple = (0, 0, 0)) -> None:
    """Draw word-wrapped text block starting at (x, y)."""
    import fitz
    max_chars = max(1, int(max_width / (fontsize * 0.52)))
    line_height = fontsize * 1.3
    for i, line in enumerate(_wrap_text(text, max_chars)):
        page.insert_text(fitz.Point(x, y + i * line_height), line, fontsize=fontsize, color=color)



def _calc_dxf_bounds(msp):
    """Return (min_x, min_y, max_x, max_y) for msp, or (None,None,None,None)."""
    bx = by = Bx = By = None
    for entity in msp:
        try:
            et = entity.dxftype()
            coords = []
            if et == "LINE":
                p1, p2 = entity.dxf.start, entity.dxf.end
                coords = [(p1.x, p1.y), (p2.x, p2.y)]
            elif et in ("LWPOLYLINE", "POLYLINE"):
                coords = [(p[0], p[1]) for p in entity.get_points()]
            elif et == "CIRCLE":
                c, r = entity.dxf.center, entity.dxf.radius
                coords = [(c.x - r, c.y - r), (c.x + r, c.y + r)]
            elif et == "ARC":
                c, r = entity.dxf.center, entity.dxf.radius
                coords = [(c.x - r, c.y - r), (c.x + r, c.y + r)]
            elif et in ("TEXT", "MTEXT"):
                t = entity.dxf.insert
                coords = [(t.x, t.y)]
            for x, y in coords:
                bx = x if bx is None else min(bx, x)
                by = y if by is None else min(by, y)
                Bx = x if Bx is None else max(Bx, x)
                By = y if By is None else max(By, y)
        except Exception:
            pass
    return bx, by, Bx, By


def _transform_point(x, y, bx, by, x0, y0, scale):
    import fitz
    return fitz.Point((x - bx) * scale + x0, y0 - (y - by) * scale)


def _draw_dxf_on_page(page, msp, draw_rect, margin: float = 8.0) -> float:
    """Draw DXF msp onto page within draw_rect. Returns scale (pts/unit) or 0."""
    import fitz, math
    bx, by, Bx, By = _calc_dxf_bounds(msp)
    if bx is None or Bx <= bx or By <= by:
        return 0.0
    dxf_w, dxf_h = Bx - bx, By - by
    aw = draw_rect.width - 2 * margin
    ah = draw_rect.height - 2 * margin
    scale = min(aw / dxf_w, ah / dxf_h)
    sw, sh = dxf_w * scale, dxf_h * scale
    x0 = draw_rect.x0 + margin + (aw - sw) / 2
    y0 = draw_rect.y0 + margin + (ah - sh) / 2 + sh  # bottom of centred drawing
    for entity in msp:
        try:
            et = entity.dxftype()
            if et == "LINE":
                p1, p2 = entity.dxf.start, entity.dxf.end
                page.draw_line(_transform_point(p1.x, p1.y, bx, by, x0, y0, scale),
                               _transform_point(p2.x, p2.y, bx, by, x0, y0, scale),
                               color=(0, 0, 0), width=0.8)
            elif et in ("LWPOLYLINE", "POLYLINE"):
                pts = [_transform_point(p[0], p[1], bx, by, x0, y0, scale) for p in entity.get_points()]
                for i in range(len(pts) - 1):
                    page.draw_line(pts[i], pts[i + 1], color=(0, 0, 0), width=0.8)
            elif et == "CIRCLE":
                c, r = entity.dxf.center, entity.dxf.radius
                cpt = _transform_point(c.x, c.y, bx, by, x0, y0, scale)
                rs = r * scale
                pts = [fitz.Point(cpt.x + rs * math.cos(i/32*2*math.pi),
                                  cpt.y + rs * math.sin(i/32*2*math.pi)) for i in range(33)]
                for i in range(32):
                    page.draw_line(pts[i], pts[i+1], color=(0,0,0), width=0.8)
            elif et == "ARC":
                c, r = entity.dxf.center, entity.dxf.radius
                sa, ea = entity.dxf.start_angle, entity.dxf.end_angle
                cpt = _transform_point(c.x, c.y, bx, by, x0, y0, scale)
                rs = r * scale
                span = ea - sa if ea >= sa else ea - sa + 360
                pts = [fitz.Point(cpt.x + rs * math.cos(math.radians(sa + i/32*span)),
                                  cpt.y + rs * math.sin(math.radians(sa + i/32*span))) for i in range(33)]
                for i in range(32):
                    page.draw_line(pts[i], pts[i+1], color=(0,0,0), width=0.8)
            elif et == "TEXT":
                t = entity.dxf.insert
                pt = _transform_point(t.x, t.y, bx, by, x0, y0, scale)
                h = max(entity.dxf.height * scale, 5)
                page.insert_text(pt, entity.dxf.text, fontsize=h, color=(0,0,0))
            elif et == "MTEXT":
                t = entity.dxf.insert
                pt = _transform_point(t.x, t.y, bx, by, x0, y0, scale)
                txt = entity.plain_mtext() if hasattr(entity, "plain_mtext") else ""
                h = max(getattr(entity.dxf, "char_height", 2.5) * scale, 5)
                page.insert_text(pt, txt, fontsize=h, color=(0,0,0))
        except Exception:
            pass
    return scale


def fill_acro(fields: Dict[str, str], out_path: Optional[str] = None) -> str:
    """Fill HHE-200 AcroForm and draw DXF on pages 3-4. Returns output path."""
    import fitz

    src_path = PDF_PATH
    save_path = Path(out_path) if out_path else src_path.with_name("HHE-200-filled.pdf")

    doc = fitz.open(str(src_path))
    set_count = 0

    # Reverse-lookup: widget_name → logical_key
    widget_to_key: Dict[str, str] = {}
    for key, names in WIDGET_MAP.items():
        for name in names:
            if name not in widget_to_key:
                widget_to_key[name] = key

    # Fill all AcroForm widgets — page-scoped so "Owner", "SE #" etc. fill on every page
    for page in doc:
        wlist = list(page.widgets())
        if not wlist:
            continue
        groups: Dict[str, list] = {}
        for w in wlist:
            n = (w.field_name or "").strip()
            if n:
                groups.setdefault(n, []).append(w)
        for wname, ws in groups.items():
            key = widget_to_key.get(wname)
            if not key or key not in fields:
                continue
            val = fields[key]
            if val is None or (isinstance(val, str) and not val.strip()):
                continue
            val_str = str(val).strip()
            if wname in RADIO_OPTIONS:
                opt = RADIO_OPTIONS[wname]
                idx = opt.get(val_str)
                if idx is None:
                    for k, v in opt.items():
                        if k.lower() in val_str.lower() or val_str.lower() in k.lower():
                            idx = v; break
                if idx is not None and idx < len(ws):
                    # Use the widget's own on_state so PyMuPDF sets the correct export value
                    on_val = ws[idx].on_state()
                    ws[idx].field_value = on_val if on_val else "Yes"
                    ws[idx].update()
                    set_count += 1
            else:
                w = ws[0]
                if w.field_type == 2:
                    w.field_value = "Yes" if val_str.lower() in ("yes","true","x","1","on") else "Off"
                else:
                    w.field_value = val_str
                w.update(); set_count += 1

    # Keep pages 1,2,3,5 (0-indexed: 0,1,2,4) — delete 3,5,6,7
    for idx in sorted([7, 6, 5, 3], reverse=True):
        if idx < doc.page_count:
            doc.delete_page(idx)
    # After: index 0=pg1, 1=pg2, 2=pg3(site plan), 3=pg5(disposal plan)

    base     = src_path.parent
    scale_ft = float(fields.get("scale_pg3", 40))

    # ── Embed DXF drawings directly into form sections ───
    # Pages 3-4 are now generated as complete PDFs (generate_hhe200_pages34_reportlab.py)
    # and will be assembled into the final 4-page PDF by run_pipeline.py
    # No PNG embedding or overlays needed here.

    doc.save(str(save_path), incremental=False, deflate=True)
    doc.close()
    print(f"  Set {set_count} widgets")
    return str(save_path.resolve())


# ============================================================================
# Wrapper Function for Pipeline Integration
# ============================================================================

def fill_pdf_with_data(complete_data: Dict[str, str]) -> str:
    """
    Wrapper function that fills the HHE-200 PDF with complete data from the pipeline.

    Args:
        complete_data: Dictionary with form fields and drawing paths

    Returns:
        Path to the generated PDF file
    """
    try:
        # Call the main fill_acro function with the complete data
        output_path = fill_acro(complete_data)
        print(f"✓ PDF generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error filling PDF: {e}")
        raise
