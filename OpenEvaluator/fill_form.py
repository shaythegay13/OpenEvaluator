#!/usr/bin/env python3
"""
fill_form.py — Fill HHE-200-2025.pdf with field → value mappings.

Reads actual Google Sheet row data from sheet_row_data.json (set by comprehensive_test_runner)
Falls back to hardcoded test values only if sheet_row_data.json is not present.

Usage:
    # Programmatically:
    from fill_form import fill_form
    fields = { ... }
    fill_form(fields, "/path/to/output.pdf")

    # Command line (reads from sheet_row_data.json):
    python3 fill_form.py
"""

from __future__ import annotations

import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Optional

import fitz  # pymupdf

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PDF_PATH   = SCRIPT_DIR / "HHE-200-2025.pdf"
MAP_PATH   = SCRIPT_DIR / "field_map.yaml"


# ── helpers ────────────────────────────────────────────────────────────────
def _load_map() -> Dict:
    """Load field_map.yaml, resolving path relative to this script."""
    if not MAP_PATH.exists():
        raise FileNotFoundError(
            f"field_map.yaml not found at {MAP_PATH}. "
            "Create it with the coordinate mappings first."
        )
    with open(MAP_PATH, "r") as fh:
        return yaml.safe_load(fh)


def _truncate(value: str, max_len: int) -> str:
    """Clamp value to max_length characters."""
    return str(value)[:max_len]


# ── core fill function ─────────────────────────────────────────────────────
def fill_form(
    fields: Dict[str, str],
    output_path: Optional[str] = None,
    pdf_path: Optional[str] = None,
    map_path: Optional[str] = None,
) -> str:
    """
    Fill the HHE-200-2025 PDF with the provided field → value mappings.

    Args:
        fields:      Dictionary of field_name (key in field_map.yaml) → value
        output_path: Path to write the filled PDF.
                     Defaults to <pdf_path>/../HHE-200-filled.pdf
        pdf_path:    Override source PDF path.
        map_path:    Override field_map.yaml path.

    Returns:
        Absolute path to the saved output file.

    Raises:
        FileNotFoundError: PDF source or field_map.yaml not found.
        ValueError:       A field name in `fields` is not in field_map.yaml.
    """
    pdf_path = Path(pdf_path) if pdf_path else PDF_PATH
    map_path = Path(map_path) if map_path else MAP_PATH
    if output_path:
        out_path = Path(output_path)
    else:
        out_path = pdf_path.parent / "HHE-200-filled.pdf"

    if not pdf_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {pdf_path}")

    field_map = _load_map()

    # Filter out fields that aren't in the field_map (instead of erroring)
    # This allows sheet_parser to return extra metadata that we don't need
    unknown = set(fields.keys()) - set(field_map.keys())
    if unknown:
        print(f"⚠ Ignoring {len(unknown)} unknown fields not in field_map.yaml")
        # Remove unknown fields
        fields = {k: v for k, v in fields.items() if k in field_map.keys()}

    doc = fitz.open(str(pdf_path))

    for field_name, value in fields.items():
        if not value and value != 0:
            continue  # skip empty fields

        entry = field_map[field_name]
        page_num = int(entry["page"])       # 1-indexed in YAML
        x        = float(entry["x"])
        y        = float(entry["y"])
        fontsize = float(entry.get("font_size", 9))
        max_len  = int(entry.get("max_length", 200))

        value_str = _truncate(value, max_len)

        # pymupdf uses 0-indexed pages
        page = doc[page_num - 1]

        # Write text at the coordinate
        page.insert_text(
            (x, y),
            value_str,
            fontsize=fontsize,
            fontname="helv",   # Helvetica (built-in, reliable)
            color=(0, 0, 0),
        )

    doc.save(str(out_path), garbage=4, deflate=True)
    doc.close()

    return str(out_path.resolve())


# ── Default test fields (used as fallback) ─────────────────────────────────
def _get_default_test_fields() -> Dict[str, str]:
    """Hardcoded test values as fallback"""
    return {
        # Page 1 – Header / Property Info
        "site_address":     "123 Maple Ridge Road",
        "town":             "Portland",
        "permit_number":    "HHE-2025-12345",
        "date_issued":      "06/15/2025",
        "municipal_tax_map": "Map 12",
        "lot_number":       "Lot 7A",
        "lpi_number":       "LPI-99999",
        "owner_name":       "Smith, Jane",
        "applicant_name":   "Doe, Jane",
        # Mailing address components (page 1)
        "mailing_street":   "456 Oak Avenue",
        "mailing_city":     "Portland",
        "mailing_state":    "ME",
        "mailing_zip":      "04101",
        "phone":            "(207) 555-0100",
        "email":            "jane.doe@example.com",
        # Owner/Applicant Statement
        "owner_applicant_statement": "I certify the information is correct.",
        # Installer info
        "installer_name":   "ABC Septic Services LLC",
        "installer_phone": "(207) 555-0199",
        # Owner signature
        "property_owner_signature": "Jane Doe",
        "property_owner_date":     "06/15/2025",

        # Page 2 – Property / System Details
        "lot_size_sqft":    "43,560",
        "lot_size_acres":   "1.0",
        "shoreland_zoning": "Shoreland Zone",
        "system_to_serve":  "Single Family Dwelling",
        "design_flow_gallons": "450",
        "num_bedrooms":     "3",
        "current_use":      "Year-Round",
        "water_supply_type": "Private Well",
        "disposal_field_type": "Stone Trench",
        "dose_gallons":     "N/A",
        "garbage_disposal_unit": "No",
        "gps_margin_of_error": "30' +/-",
        "evaluator_name":   "John Smith",
        "evaluator_license_number": "SE-54321",

        # Page 3 – Soil Profile & Site Plan
        "site_plan_scale":            "40",
        "oh1_organic_thickness":      "6",
        "oh1_ground_surface_elevation": "182.5",
        "oh1_depth_to_exploration":   "60",
        "oh2_organic_thickness":     "4",
        "oh2_ground_surface_elevation": "181.0",
        "oh2_depth_to_exploration":  "60",
        # Deepest restrictive layer
        "deepest_restrictive_layer_hole1": "Sandy Loam",
        "deepest_restrictive_layer_hole2": "Clay",
        # Water table
        "water_table_depth_hole1":    "36",
        "water_table_depth_hole2":    "42",
        # Bedrock
        "bedrock_depth_hole1":        "72",
        "bedrock_depth_hole2":        "68",
        # Soil classification / slope
        "soil_classification_hole1":  "Sandy Loam",
        "soil_classification_hole2":  "Clay",
        "slope_hole1":                "5",
        "slope_hole2":                "8",
        # SE signature block
        "evaluator_name_page3":       "John Smith",
        "evaluator_se_number":        "SE-54321",
        "evaluator_date_page3":       "06/15/2025",

        # Page 4 – Grid Soil Profile (mirror fields)
        "water_table_depth_p4_hole1": "36",
        "water_table_depth_p4_hole2": "42",
        "deepest_restrictive_layer_p4_hole1": "Sandy Loam",
        "deepest_restrictive_layer_p4_hole2": "Clay",
        "bedrock_depth_p4_hole1":     "72",
        "bedrock_depth_p4_hole2":     "68",
        "soil_classification_p4_hole1": "Sandy Loam",
        "soil_classification_p4_hole2": "Clay",
        "slope_p4_hole1":             "5",
        "slope_p4_hole2":             "8",

        # Page 5 – Disposal Area Cross-Section
        "scale_page5":                "20",
        "depth_backfill_upslope":    "12",
        "depth_backfill_downslope":   "8",
        "finished_grade_elevation":  "185.0",
        "top_of_distribution_pipe_elevation": "174.0",
        "bottom_of_disposal_field_elevation": "172.0",

        # Page 6 – Site Plan (detail)
        "scale_page6":                "40",
        "backfill_depth_upslope_p6": "12",
        "backfill_depth_downslope_p6": "8",
        "finished_grade_elevation_p6": "185.0",
        "top_of_distribution_pipe_elevation_p6": "174.0",
        "bottom_of_disposal_field_elevation_p6": "172.0",
        "se_number_page6":            "SE-54321",
        "se_date_page6":             "06/15/2025",

        # Setbacks
        "setback_well":              "100 ft",
        "setback_surface_water":    "75 ft",
        "setback_property_line":    "10 ft",
    }


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Try to load actual Google Sheet row data (set by comprehensive_test_runner)
    sheet_data_file = Path(__file__).parent / "sheet_row_data.json"

    if sheet_data_file.exists():
        print(f"✓ Loading actual Google Sheet row data from {sheet_data_file.name}")
        try:
            with open(sheet_data_file, 'r') as f:
                sheet_fields = json.load(f)
            test_fields = sheet_fields
            print(f"  - Owner: {test_fields.get('owner_name', 'N/A')}")
            print(f"  - Property: {test_fields.get('site_address', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"✗ Error reading sheet data: {e}")
            print("  Falling back to hardcoded test values")
            test_fields = _get_default_test_fields()
    else:
        print("  (No sheet_row_data.json found, using hardcoded test values)")
        test_fields = _get_default_test_fields()

    print("Filling HHE-200-2025.pdf…")
    try:
        out = fill_form(test_fields)
        print(f"✓  Saved filled PDF → {out}")
    except Exception as exc:
        print(f"✗  ERROR: {exc}")
        sys.exit(1)