#!/usr/bin/env python3
"""
DWG/DXF Generator: Creates AutoCAD 2004-compatible DXF files with filled form data.

Outputs:
  - PG1_filled.dxf (form page 1 with field data)
  - PG2_filled.dxf (form page 2 with field data)
  - PG3_filled.dxf (form page 3 with site plan drawing + field data)
  - PG4_filled.dxf (form page 4 with disposal plan + cross-section + field data)

All files use standard AutoCAD fonts (no Carlson fonts) for AC1018 compatibility.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import ezdxf
from ezdxf.layouts import Layout
from ezdxf.entities import Text, Line, LWPolyline, Circle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "dwg_output"
RAW_TEMPLATES_DIR = Path(__file__).parent / "raw_templates"

# Standard AutoCAD 2004 fonts (no Carlson)
FONT_STANDARD = "Standard"
FONT_TEXT = "Arial"
FONT_MONO = "Monotxt"

# DXF version for AutoCAD 2004 (AC1018)
DXF_VERSION = "R2004"


def _add_text(layout: Layout, text: str, x: float, y: float, height: float = 2.5,
              font: str = FONT_TEXT) -> None:
    """Add text to DXF layout with standard font."""
    if not text or text.strip() == "":
        return

    t = layout.add_text(str(text)[:200], dxfattribs={
        "insert": (x, y),
        "height": height,
    })
    t.dxf.color = 256  # By layer


def _add_line(layout: Layout, x1: float, y1: float, x2: float, y2: float,
              color: int = 256, width: float = 0.0) -> None:
    """Add line to DXF layout."""
    line = layout.add_line((x1, y1), (x2, y2), dxfattribs={"color": color})
    if width > 0:
        line.dxf.lineweight = int(width * 100)


def _add_rect(layout: Layout, x: float, y: float, w: float, h: float,
              color: int = 256, filled: bool = False) -> None:
    """Add rectangle to DXF layout."""
    # Create as polyline (more compatible)
    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    poly = layout.add_lwpolyline(points, dxfattribs={"color": color})
    poly.close()


def create_page1_dxf(form_data: Dict[str, str], out_path: Optional[str] = None) -> str:
    """
    Create DXF for Page 1: Owner/Property Information.

    Form sections:
      - Property owner info (name, address, phone, email)
      - Property location (street, town, map, lot, acreage)
      - Site evaluator info (name, phone, email, SE#)
      - Application type (replacement, expansion, new, etc.)
      - Permit info
    """
    out_path = Path(out_path) if out_path else OUTPUT_DIR / "PG1_filled.dxf"
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Create new DXF document
    doc = ezdxf.new(DXF_VERSION)
    msp = doc.modelspace()

    logger.info(f"Creating Page 1 DXF: {out_path}")

    # Title
    _add_text(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", 10, 275, 3.5, font=FONT_STANDARD)
    _add_text(msp, "HHE-200 Application Form - Page 1 of 4", 10, 270, 2.0, font=FONT_TEXT)

    y = 260

    # Property Owner Information Section
    _add_text(msp, "PROPERTY OWNER INFORMATION", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Owner Name: {form_data.get('owner_name', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Phone: {form_data.get('owner_phone', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Email: {form_data.get('owner_email', '')}", 10, y, 2.0)
    y -= 8

    # Property Location Section
    _add_text(msp, "PROPERTY LOCATION", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Street: {form_data.get('street_name', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Town: {form_data.get('town', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Map # {form_data.get('map_number', '')}  Lot # {form_data.get('lot_number', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Acreage: {form_data.get('acreage', '')}", 10, y, 2.0)
    y -= 8

    # Site Evaluator Section
    _add_text(msp, "SITE EVALUATOR INFORMATION", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Evaluator: {form_data.get('evaluator_name', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Phone: {form_data.get('evaluator_phone', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Email: {form_data.get('evaluator_email', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"SE #: {form_data.get('se_number', '')}", 10, y, 2.0)
    y -= 8

    # Application Type Section
    _add_text(msp, "APPLICATION TYPE", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    app_type = form_data.get('type_of_app', 'Replacement')
    _add_text(msp, f"Type: {app_type}", 10, y, 2.0)
    y -= 5

    if form_data.get('system_replaced') == 'Yes':
        _add_text(msp, "[X] Replacement System", 10, y, 2.0)
    y -= 5

    if form_data.get('expansion'):
        _add_text(msp, "[X] Expansion", 10, y, 2.0)
    y -= 8

    # Signature block
    _add_text(msp, "SITE EVALUATOR SIGNATURE / INITIALS: ___________", 10, 10, 2.0)
    _add_text(msp, f"SE #: {form_data.get('se_number', '')}  Date: {form_data.get('se_signature_date', '')}", 10, 5, 2.0)

    doc.saveas(str(out_path))
    logger.info(f"✓ Page 1 DXF saved: {out_path}")
    return str(out_path)


def create_page2_dxf(form_data: Dict[str, str], out_path: Optional[str] = None) -> str:
    """
    Create DXF for Page 2: System Design Information.
    """
    out_path = Path(out_path) if out_path else OUTPUT_DIR / "PG2_filled.dxf"
    OUTPUT_DIR.mkdir(exist_ok=True)

    doc = ezdxf.new(DXF_VERSION)
    msp = doc.modelspace()

    logger.info(f"Creating Page 2 DXF: {out_path}")

    # Title
    _add_text(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", 10, 275, 3.5, font=FONT_STANDARD)
    _add_text(msp, "HHE-200 Application Form - Page 2 of 4", 10, 270, 2.0, font=FONT_TEXT)

    y = 260

    # System Design Section
    _add_text(msp, "SYSTEM DESIGN INFORMATION", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Property Size: {form_data.get('property_size', '')} acres", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Water Supply: {form_data.get('water_supply', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"System to Serve: {form_data.get('disposal_system_to_serve', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Bedrooms: {form_data.get('num_bedrooms_opt1', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Design Flow: {form_data.get('design_flow_gpd', '')} GPD", 10, y, 2.0)
    y -= 8

    # Disposal Field Section
    _add_text(msp, "DISPOSAL FIELD TYPE & SIZE", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Type: {form_data.get('disposal_field_type', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Size: {form_data.get('disposal_field_size', '')}", 10, y, 2.0)
    y -= 8

    # Soil Data Section
    _add_text(msp, "SOIL DATA", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Soil Type: {form_data.get('soil_classification_hole1', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Limiting Factor: {form_data.get('limiting_factor_depth', '')}", 10, y, 2.0)
    y -= 8

    # Signature block
    _add_text(msp, "SITE EVALUATOR SIGNATURE / INITIALS: ___________", 10, 10, 2.0)
    _add_text(msp, f"SE #: {form_data.get('se_number', '')}  Date: {form_data.get('se_signature_date', '')}", 10, 5, 2.0)

    doc.saveas(str(out_path))
    logger.info(f"✓ Page 2 DXF saved: {out_path}")
    return str(out_path)


def create_page3_dxf(form_data: Dict[str, str], drawing_data: Optional[Dict] = None,
                     out_path: Optional[str] = None) -> str:
    """
    Create DXF for Page 3: Site Plan with drawing embedded.
    """
    out_path = Path(out_path) if out_path else OUTPUT_DIR / "PG3_filled.dxf"
    OUTPUT_DIR.mkdir(exist_ok=True)

    doc = ezdxf.new(DXF_VERSION)
    msp = doc.modelspace()

    logger.info(f"Creating Page 3 DXF: {out_path}")

    # Title
    _add_text(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", 10, 275, 3.5, font=FONT_STANDARD)
    _add_text(msp, "HHE-200 Application Form - Page 3 of 4 (SITE PLAN)", 10, 270, 2.0, font=FONT_TEXT)

    y = 260
    _add_text(msp, f"Owner: {form_data.get('owner_name', '').upper()}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Address: {form_data.get('address_line', '').upper()}", 10, y, 2.0)
    y -= 8

    # Site Plan area (drawing will be embedded here)
    _add_text(msp, "SITE PLAN DRAWING", 10, y, 2.5, font=FONT_STANDARD)
    y -= 5
    _add_text(msp, f"Scale: 1\" = {form_data.get('scale_pg3', '40')}'", 10, y, 2.0)
    y -= 30

    # Placeholder for drawing (TODO: embed actual drawing geometry)
    _add_text(msp, "[SITE PLAN DRAWING AREA - See separate drawing data]", 20, y, 2.0)

    y -= 40

    # Property & Location Info
    _add_text(msp, "PROPERTY INFORMATION", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Map: {form_data.get('map_number', '')}  Lot: {form_data.get('lot_number', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Acreage: {form_data.get('acreage', '')}", 10, y, 2.0)
    y -= 8

    # Signature block
    _add_text(msp, "SITE EVALUATOR SIGNATURE / INITIALS: ___________", 10, 10, 2.0)
    _add_text(msp, f"SE #: {form_data.get('se_number', '')}  Date: {form_data.get('se_signature_date', '')}", 10, 5, 2.0)

    doc.saveas(str(out_path))
    logger.info(f"✓ Page 3 DXF saved: {out_path}")
    return str(out_path)


def create_page4_dxf(form_data: Dict[str, str], drawing_data: Optional[Dict] = None,
                     out_path: Optional[str] = None) -> str:
    """
    Create DXF for Page 4: Disposal Plan & Cross-section with drawings embedded.
    """
    out_path = Path(out_path) if out_path else OUTPUT_DIR / "PG4_filled.dxf"
    OUTPUT_DIR.mkdir(exist_ok=True)

    doc = ezdxf.new(DXF_VERSION)
    msp = doc.modelspace()

    logger.info(f"Creating Page 4 DXF: {out_path}")

    # Title
    _add_text(msp, "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION", 10, 275, 3.5, font=FONT_STANDARD)
    _add_text(msp, "HHE-200 Application Form - Page 4 of 4 (DISPOSAL PLAN & CROSS-SECTION)", 10, 270, 2.0, font=FONT_TEXT)

    y = 260
    _add_text(msp, f"Owner: {form_data.get('owner_name', '').upper()}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Address: {form_data.get('address_line', '').upper()}", 10, y, 2.0)
    y -= 8

    # Disposal Plan Section
    _add_text(msp, "DISPOSAL PLAN", 10, y, 2.5, font=FONT_STANDARD)
    y -= 5
    _add_text(msp, f"Scale: 1\" = {form_data.get('scale_pg4', '40')}'", 10, y, 2.0)
    y -= 30

    _add_text(msp, "[DISPOSAL PLAN DRAWING AREA - See separate drawing data]", 20, y, 2.0)
    y -= 40

    # Elevations Section
    _add_text(msp, "ELEVATIONS (From ERP)", 10, y, 2.5, font=FONT_STANDARD)
    y -= 8

    _add_text(msp, f"Finished Grade: {form_data.get('finished_grade_elevation', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Top of Pipe: {form_data.get('top_distribution_pipe', '')}", 10, y, 2.0)
    y -= 5
    _add_text(msp, f"Bottom of Field: {form_data.get('bottom_disposal_field', '')}", 10, y, 2.0)
    y -= 8

    # Signature block
    _add_text(msp, "SITE EVALUATOR SIGNATURE / INITIALS: ___________", 10, 10, 2.0)
    _add_text(msp, f"SE #: {form_data.get('se_number', '')}  Date: {form_data.get('se_signature_date', '')}", 10, 5, 2.0)

    doc.saveas(str(out_path))
    logger.info(f"✓ Page 4 DXF saved: {out_path}")
    return str(out_path)


def generate_all_pages(form_data: Dict[str, str], drawing_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate all 4 pages as DXF files.

    Returns:
        Dict mapping page names to output file paths
    """
    logger.info(f"\n{'='*80}")
    logger.info("DWG/DXF GENERATION: All 4 Pages")
    logger.info(f"{'='*80}")

    results = {
        'page1': create_page1_dxf(form_data),
        'page2': create_page2_dxf(form_data),
        'page3': create_page3_dxf(form_data, drawing_data),
        'page4': create_page4_dxf(form_data, drawing_data),
    }

    logger.info(f"\n✓ All pages generated in: {OUTPUT_DIR}")
    for page, path in results.items():
        logger.info(f"  {page}: {Path(path).name}")

    return results


if __name__ == "__main__":
    # Test with sample data
    test_data = {
        "owner_name": "Kristen Marquis",
        "address_line": "17 Aspen Way, Turner, Maine 04282",
        "street_name": "Aspen Way",
        "town": "Turner",
        "map_number": "26",
        "lot_number": "18",
        "acreage": "2.35",
        "evaluator_name": "George Bouchles",
        "evaluator_phone": "207-240-5567",
        "evaluator_email": "gsb@cadmasterr.com",
        "se_number": "338",
        "se_signature_date": "03/01/2026",
        "type_of_app": "Replacement",
        "system_replaced": "Yes",
        "property_size": "2.35",
        "water_supply": "Drilled Well",
        "disposal_system_to_serve": "Single Family Dwelling Unit",
        "num_bedrooms_opt1": "3",
        "design_flow_gpd": "270",
        "disposal_field_type": "Proprietary Device",
        "disposal_field_size": "11 x 28 ft",
        "soil_classification_hole1": "Fine Sandy Loam",
        "limiting_factor_depth": "24 inches (Ground Water)",
        "scale_pg3": "40",
        "scale_pg4": "40",
        "finished_grade_elevation": "0\"",
        "top_distribution_pipe": "-12\"",
        "bottom_disposal_field": "30\"",
    }

    results = generate_all_pages(test_data)
    print(f"\nTest generation complete!")
    print(f"Output files in: {OUTPUT_DIR}")
