#!/usr/bin/env python3
"""Generate comprehensive WIDGET_MAP covering ALL widgets on pages 1-2."""
from pathlib import Path

# Every unique widget field_name on pages 1-2
# (RAD) radio — set first widget in group
# (CHK) checkbox — set "Yes" to check, "Off" to uncheck
# (TXT) text — set the value
# Key format: logical_key: [widget_field_name1, widget_field_name2, ...]

WIDGET_MAP = {
    # ═══════════════════════════════════════
    # PAGE 1: Applicant / Site / Fee / Tank
    # ═══════════════════════════════════════

    # --- Site / Applicant Info ---
    "street_number":           ["Street #"],
    "street_name":             ["Street Name"],
    "town":                    ["City/ Town/ Plantation"],
    "map_number":              ["Map #"],
    "lot_number":              ["Lot #"],
    "owner_name":              ["Owner Name"],
    "applicant_name":          ["Applicant Name"],
    "mailing_street":          ["Street (Mailing Address)"],
    "mailing_city":            ["City (Mailing Address)"],
    "mailing_state":           ["State (Mailing Address)"],
    "mailing_zip":             ["Zip Code (Mailing Address)"],
    "owner_phone":             ["Owner/ Applicant Phone Number"],
    "owner_email":             ["Owner/ Applicant Email"],
    "property_owner_signature_date": ["Date (Property Owner Signature)"],

    # --- Installer ---
    "installer_name":          ["Installer Name"],
    "installer_phone":         ["Installer Phone #"],
    "installer_email":         ["Installer Email"],

    # --- Municipality / Permit ---
    "issuing_municipality":    ["Issuing Municipality or Territory"],
    "permit_number":           ["Permit #"],
    "permit_issued_date":      ["Permit Issued Date"],
    "lpi_number":              ["LPI #"],
    "lpi_inspection1_date":    ["Date for First LPI Inspection"],
    "lpi_inspection2_date":    ["Date for Second LPI Inspection"],

    # --- Fee ---
    "fee_area":                ["Fee Calculation Area"],
    "total_fee":               ["Total Fee"],
    "town_share":              ["Town Share"],
    "state_25_pct":            ["State 25%"],
    "dep_wqs":                 ["DEP WQS"],

    # --- Checkboxes (top section) ---
    "revision_check":          ["Revision Check Box"],
    "doubled_fee_check":       ["Doubled Fee Check Box"],
    "variance_check":          ["Variance Check Box"],
    "seasonal_conversion_check": ["Seasonal Conversion Check Box"],

    # --- Application Info ---
    "type_of_app":             ["Type of Application"],
    "system_replaced":         ["Type of System Replaced"],
    "year_installed":          ["Year Installed"],

    # --- Radio: Expansion ---
    "expansion":               ["Expansion"],

    # --- Radio: Variance Requirement ---
    "variance_requirement":    ["Variance Requirement"],

    # --- Radio: First Time System ---
    "first_time_system":       ["First Time System Requirement"],

    # --- Radio: Replacement Variance ---
    "replacement_variance":    ["Replacement Variance Requirement"],

    # --- Radio: Treatment Tanks ---
    "treatment_tanks":         ["Treatment Tanks"],

    # --- Checkboxes: Treatment Tank ---
    "tank_regular_check":      ["Regular Check Box (Treatment Tank)"],
    "tank_low_profile_check":  ["Low Profile Check Box (Treatment Tank)"],
    "tank_h20_check":          ["H-20 Check Box (Treatment Tank)"],
    "tank_capacity":           ["Capacity (Treatment Tank)"],
    "tank_specify_other":      ["Specify Other Tank (Treatment Tank)"],
    "tank_cap_gal":            ["Tank Capacity (Treatment Tank)"],
    "tank_total_new":          ["Total # of New Tanks (Treatment Tank)"],
    "tank_notes":              ["Notes (Treatment Tank)"],

    # --- Checkboxes: Risers / Systems ---
    "risers_required_check":   ["Risers Required Checkbox"],
    "cnes_check":              ["Complete Non-Engineered System Check Box"],
    "cnes_total_tanks":        ["Specify Total Number of New Tanks (CNES)"],
    "primitive_limited_check": ["Primitive/ Limited System Check Box"],
    "primitive_limited_type":  ["Specify Type (Primitive/ Limited System)"],
    "alt_toilet_check":        ["Alternative Toilet Check Box"],
    "alt_toilet_type":         ["Specify Type (Alt Toilet)"],
    "non_eng_tank_check":      ["Non-Engineered Treatment Tank Check Box"],
    "non_eng_tank_number":     ["Specify # of New Tanks (Non-Engineered Disposal Field)"],
    "holding_tank_check":      ["Holding Tank Check Box"],
    "non_eng_field_check":     ["Non-Engineered Disposal Field Check Box"],
    "ces_check":               ["Complete Engineered System Check Box"],
    "ces_tanks":               ["# of New Disposal Tanks"],
    "ces_new_tanks":           ["# of New Tanks (CES)"],
    "ces_pumps":               ["# of Pumps (CES)"],
    "eng_tank_check":          ["Engineered Tank Check Box"],
    "eng_tank_number":         ["Specify # of New Tanks (Engineered Tank)"],
    "eng_field_check":         ["Engineered Field Check Box"],
    "misc_components_check":   ["Misc. Components Check Box"],
    "misc_components_specify": ["Specify (Misc. Components)"],
    "pre_treatment_tank_check":["Pre-Treatment Tank Check Box"],
    "pre_treatment_comp_check":["Pre-Treatment Component Check Box"],

    # --- Site Evaluator ---
    "evaluator_name":          ["Site Evaluator Name"],
    "evaluator_phone":         ["Site Evaluator Phone #"],
    "se_number":               ["SE #"],
    "se_signature_date":       ["Date of Site Evaluator Signature"],
    "evaluator_email":         ["Site Evaluator Email"],

    # ═══════════════════════════════════════
    # PAGE 2: Property / Soils / Pre-Treatment
    # ═══════════════════════════════════════

    # --- Property ---
    "owner_name_pg2":          ["Owner"],
    "address_pg2":             ["Address"],
    "property_size":           ["Property Size"],
    "property_size_units":     ["property size measurement"],

    # --- Shoreland / Current Use ---
    "shoreland_zoning_yn":     ["SLZ y/n"],
    "current_use":             ["Current Use"],

    # --- GPS ---
    "latitude_deg":            ["Latitude (degrees)"],
    "latitude_min":            ["Latitude (minutes)"],
    "latitude_sec":            ["Latitude (seconds)"],
    "longitude_deg":           ["Longitude (degrees)"],
    "longitude_min":           ["Longitude (minutes)"],
    "longitude_sec":           ["Longitude (seconds)"],
    "gps_margin_error":        ["GPS margin of error"],

    # --- Water Supply ---
    "water_supply":            ["Type of Water Supply"],
    "water_supply_specify":    ["specify box (type of water supply)"],

    # --- Effluent/Ejector Pump ---
    "effluent_pump":           ["Effluent/Ejector Pump"],
    "dose_engineered":         ["Dose (Engineered Systems)"],

    # --- GDU ---
    "gdu_ynm":                 ["GDU Y/N/M"],
    "gdu_if_yes":              ["GDU if yes"],
    "gdu_tanks":               ["# of Tanks (garbage disposal unit)"],

    # --- Disposal System ---
    "disposal_system_type":    ["Disposal System to Serve"],
    "num_bedrooms_opt1":       ["# of bedrooms for option 1 (disposal system to serve)"],
    "num_bedrooms_opt2":       ["# of bedrooms for option 2 (disposal system to serve)"],
    "num_bedrooms_opt3":       ["# of bedrooms for option 3 (disposal system to serve)"],
    "disposal_system_other":   ["specify for other (disposal system to serve)"],

    # --- Disposal Field ---
    "disposal_field_type":     ["Disposal Field Type & Size"],
    "proprietary_device":      ["Proprietary Device Options"],
    "field_type_other":        ["specify for other (disposal field type and size)"],
    "field_size":              ["size (disposal field type and size)"],
    "field_size_measurement":  ["Disposal Field Size Measurement"],

    # --- Design Flow ---
    "design_flow_gpd":         ["gallons per day (design flow)"],
    "design_flow_type":        ["Design Flow"],
    "design_flow_calc":        ["show calculations for 'other facilities' (design flow)"],

    # --- Soil Data ---
    "profile_soil_data":       ["profile (soil data & design class)"],
    "condition_soil":          ["condition (soil data & design class)"],
    "observation_hole":        ["observation hole # (soil data & design class)"],
    "limiting_factor_depth":   ["limiting factor depth (soil data & design class)"],
    "limiting_factor_elev":    ["limiting factor elevation (soil data & design class)"],

    # --- Pre-Treatment ---
    "pre_treatment_make1":     ["make #1 (pre-treatment)"],
    "pre_treatment_model1":    ["model #1 (pre-treatment)"],
    "pre_treatment_notes1":    ["Notes #1 (pre-treatment)"],
    "pre_treatment_maint1":    ["Maintenance Contract #1 (pre-treatment)"],
    "pre_treatment_make2":     ["make #2 (pre-treatment)"],
    "pre_treatment_model2":    ["model #2 (pre-treatment)"],
    "pre_treatment_notes2":    ["Notes #2 (pre-treatment)"],
    "pre_treatment_maint2":    ["Maintenance Contract #2 (pre-treatment)"],

    # --- Additional ---
    "additional_notes":        ["Additional Notes"],

    # --- Page 2 Signature ---
    "se_number_pg2":           ["SE #"],
    "se_signature_date_pg2":   ["Date of SE signature/ initial (pg2)"],
}

# Generate the acro_fill.py file
lines = []
lines.append('#!/usr/bin/env python3')
lines.append('"""Fill HHE-200 AcroForm widgets by setting field values directly."""')
lines.append('from pathlib import Path')
lines.append('from typing import Dict, List, Optional')
lines.append('')
lines.append('PDF_PATH = Path(__file__).parent / "HHE-200-2025.pdf"')
lines.append('')
lines.append('WIDGET_MAP: Dict[str, List[str]] = {')

for key, names in WIDGET_MAP.items():
    names_str = ', '.join(f'"{n}"' for n in names)
    lines.append(f'    "{key}": [{names_str}],')

lines.append('}')
lines.append('')
lines.append('''
def fill_acro(fields: Dict[str, str], out_path: Optional[str] = None) -> str:
    """Fill HHE-200 AcroForm widgets. Sets only the first widget per unique field_name (handles radio groups)."""
    import fitz

    pdf_path = Path(out_path) if out_path else PDF_PATH
    src_path = PDF_PATH
    save_path = Path(out_path) if out_path else Path(fitz.open(str(src_path)).name)

    doc = fitz.open(str(src_path))
    set_count = 0
    seen_widget_fields = set()

    for page in doc:
        for w in page.widgets():
            n = (w.field_name or "").strip()
            if not n or n in seen_widget_fields:
                continue
            seen_widget_fields.add(n)

            # Find logical key in WIDGET_MAP that maps to this widget name
            logical = None
            for log_name, widget_names in WIDGET_MAP.items():
                if n in widget_names and log_name in fields:
                    logical = log_name
                    break
            if not logical or logical not in fields:
                continue

            val = fields[logical]
            if not val and val != 0:
                continue

            ft = w.field_type
            if ft == 2:  # Checkbox
                w.field_value = "Yes" if str(val).lower() in ("yes", "true", "x", "1", "on") else "Off"
            elif ft == 5:  # Radio - set value directly
                w.field_value = str(val)
            else:  # Text (7) or signature (6) or other
                w.field_value = str(val)
            w.update()
            set_count += 1

    total_pages = doc.page_count
    doc.save(str(save_path), incremental=False, deflate=True)
    doc.close()

    # Trim blank trailing pages
    doc2 = fitz.open(str(save_path))
    if doc2.page_count > total_pages:
        for pi in range(doc2.page_count - 1, total_pages - 1, -1):
            doc2.delete_page(pi)
    elif doc2.page_count > 2:
        for pi in range(doc2.page_count - 1, 1, -1):
            has_content = False
            for w in doc2[pi].widgets():
                if w.field_value and str(w.field_value).strip() not in ("", "Off", "0"):
                    has_content = True
                    break
            if not has_content:
                doc2.delete_page(pi)
    doc2.save(str(save_path), incremental=False, deflate=True)
    doc2.close()

    print(f'  Set {set_count} widgets')
    return str(save_path.resolve())
''')

target = Path("/home/workspace/OpenEvaluator/acro_fill.py")
target.write_text("\n".join(lines) + "\n")
print(f"Wrote {len(lines)} lines -> {target}")
print(f"WIDGET_MAP entries: {len(WIDGET_MAP)}")
