#!/usr/bin/env python3
"""
HHE-200 PDF Field Mapper

Extracts X,Y coordinates and bounding boxes of all text fields and input areas
on each page of the HHE-200 PDF, so Hermes knows exactly where to place each
data point when filling the form programmatically.

Usage:
    python pdf_field_mapper.py /path/to/hhe200.pdf
    python pdf_field_mapper.py /path/to/hhe200.pdf --output ./data/fields/
    python pdf_field_mapper.py /path/to/hhe200.pdf --visualize 3

Output:
    openevaluator/data/fields/page_N.json  (one JSON file per page)
    openevaluator/data/fields/field_map_summary.json  (all pages combined)

PDF Source Note:
    The HHE-200 PDF lives in Google Drive (bouchlesshay@gmail.com). Download it
    locally first, or provide a Drive file ID to the drive-download script before
    running this mapper.

Hermes PDF Tool Integration:
    The JSON output maps directly to Hermes PDF tool calls. Each field object
    contains the coordinates Hermes needs to target:

        hermes.pdf.fill_page_field(
            page=3,
            field="property_address",
            value="123 Main St, Auburn ME 04210",
            x=72,     # points from left edge
            y=540,    # points from bottom
            width=200,
            height=18
        )

    Coordinate System:
        - x, y are the UPPER-LEFT corner of the field bounding box
        - PDF coordinate origin is the BOTTOM-LEFT corner of the page
        - pdfplumber reports y from the TOP, so this script converts to PDF space
        - Page dimensions are in PDF "points" (1 point = 1/72 inch)
"""

---
title: HHE-200 PDF Field Mapper
description: Extracts bounding box coordinates of all text fields and input areas on each page of the HHE-200 PDF for Hermes form-filling integration.
created: 2026-05-03
updated: 2026-05-03
tags: [pdf, hermes, hhe-200, field-mapping]
version: "0.1.0"
---

import argparse
import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# pdfplumber must be installed: pip install pdfplumber
try:
    import pdfplumber
    from pdfplumber.utils import get_bbox_overlap, obj_to_bbox
except ImportError:
    print("Error: pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FieldBox:
    """A detected text field / input area on a PDF page."""
    label: str            # Human-readable label (extracted from nearby text)
    x: float             # Left edge (PDF points from left)
    y: float             # Top edge (PDF points from top, converted to PDF bottom-origin)
    width: float         # Bounding box width
    height: float        # Bounding box height
    page_width: float    # Page width in points
    page_height: float   # Page height in points
    text: str            # Actual text found inside the box (if any)
    confidence: float    # Detection confidence 0.0–1.0 (AI estimated)
    field_type: str      # "input", "checkbox", "label", "section_header", "drawing_area"


@dataclass
class PageFields:
    """All fields detected on a single PDF page."""
    page_number: int
    page_width: float
    page_height: float
    fields: list


# =============================================================================
# COORDINATE CONVERSION
# =============================================================================

def pdfplumber_bbox_to_pdf_coords(bbox, page_height: float):
    """
    Convert pdfplumber bbox (top-origin y) to PDF coordinate space (bottom-origin y).

    pdfplumber bboxes: (x0, y0, x1, y1) with y measured from TOP of page
    PDF standard bboxes: (x0, y0, x1, y1) with y measured from BOTTOM of page

    Args:
        bbox: tuple (x0, y0, x1, y1) in pdfplumber (top-origin) space
        page_height: total height of the page in points

    Returns:
        dict with converted coordinates
    """
    x0, y0_top, x1, y1_top = bbox
    # Convert top-origin y to bottom-origin y
    y0_pdf = page_height - y1_top
    y1_pdf = page_height - y0_top
    return {
        "x": round(x0, 1),
        "y": round(y0_pdf, 1),       # bottom-origin, for PDF tool calls
        "top_y": round(y0_top, 1),   # top-origin, for reference
        "width": round(x1 - x0, 1),
        "height": round(y1_top - y0_top, 1),
    }


# =============================================================================
# FIELD DETECTION
# =============================================================================

def detect_fields_on_page(page) -> list[FieldBox]:
    """
    Detect all fillable fields and meaningful regions on a single PDF page.

    Detection strategy:
    1. Look for form artifacts (checkboxes, radio buttons, empty rects)
    2. Look for text near empty areas (potential input fields)
    3. Look for section headers and labels
    4. Identify drawing/attachment areas (large empty rects)

    Returns:
        List of FieldBox objects
    """
    page_width = page.width
    page_height = page.height
    fields = []

    # --- 1. Raw text extraction ---
    # Get all text with positions
    words = page.extract_words()
    chars = page.chars  # individual characters with positions

    # --- 2. Detect rectangles / paths (form boxes, input areas) ---
    rects = page.rects  # rectangular shapes
    lines = page.lines   # line segments
    curves = page.curves  # curved paths

    # --- 3. Detect likely input areas ---
    # Input areas are typically empty rectangles or areas with border lines
    # and little/no text inside them

    for rect in rects:
        bbox = rect["bbox"]
        coords = pdfplumber_bbox_to_pdf_coords(bbox, page_height)
        w, h = coords["width"], coords["height"]

        # Skip tiny decorative elements
        if w < 10 or h < 5:
            continue

        # Classify rectangle by size
        if h < 20 and w > 50:
            field_type = "input"      # Likely a text input line
        elif h < 30 and w < 30:
            field_type = "checkbox"  # Checkbox or small radio button
        else:
            field_type = "section"    # Larger area (could be drawing area)

        # Determine label from nearby text
        label = _find_nearby_label(page, bbox, words)

        # Estimate confidence based on how "empty" the box is
        confidence = _estimate_confidence(page, bbox, chars, words)

        fields.append(FieldBox(
            label=label,
            x=coords["x"],
            y=coords["y"],
            width=coords["width"],
            height=coords["height"],
            page_width=page_width,
            page_height=page_height,
            text="",
            confidence=confidence,
            field_type=field_type
        ))

    # --- 4. Detect drawing/attachment areas ---
    # Large empty regions (e.g., site plan area, cross-section area)
    drawing_areas = _detect_drawing_areas(page, page_width, page_height)
    for area in drawing_areas:
        fields.append(FieldBox(
            label=area["label"],
            x=area["x"],
            y=area["y"],
            width=area["width"],
            height=area["height"],
            page_width=page_width,
            page_height=page_height,
            text="",
            confidence=0.8,
            field_type="drawing_area"
        ))

    # --- 5. Deduplicate and sort ---
    # Remove overlapping detections, preferring higher-confidence ones
    fields = _deduplicate_fields(fields)

    return fields


def _find_nearby_label(page, bbox, words) -> str:
    """
    Find text label that likely belongs to a field.

    Looks for text immediately above or to the left of the bbox.
    """
    x0, y0_top, x1, y1_top = bbox

    # Search for words above the box (within ~30 points)
    above_words = [
        w for w in words
        if w["top"] < y0_top
        and w["top"] > y0_top - 40
        and w["x1"] > x0 - 20
        and w["x0"] < x1 + 20
    ]

    if above_words:
        above_words.sort(key=lambda w: w["top"])
        label_text = " ".join(w["text"] for w in above_words)
        return label_text.strip()

    # Fall back to words to the left
    left_words = [
        w for w in words
        if w["x1"] < x0
        and w["x1"] > x0 - 100
        and w["top"] > y0_top - 10
        and w["bottom"] < y1_top + 10
    ]

    if left_words:
        left_words.sort(key=lambda w: w["x1"], reverse=True)
        label_text = " ".join(w["text"] for w in left_words)
        return label_text.strip()

    return ""


def _estimate_confidence(page, bbox, chars, words) -> float:
    """
    Estimate detection confidence for a field box.

    High confidence = empty box with clear borders (likely an input field)
    Low confidence = box with lots of text inside (likely a section/label)
    """
    x0, y0_top, x1, y1_top = bbox

    # Count chars inside the bbox
    chars_inside = [
        c for c in chars
        if c["x0"] >= x0 and c["x1"] <= x1
        and c["top"] >= y0_top and c["bottom"] <= y1_top
    ]

    words_inside = [
        w for w in words
        if w["x0"] >= x0 and w["x1"] <= x1
        and w["top"] >= y0_top and w["bottom"] <= y1_top
    ]

    if len(chars_inside) == 0 and len(words_inside) == 0:
        return 0.9  # Empty — high confidence it's an input area

    if len(words_inside) <= 2:
        return 0.7  # Short text — could be placeholder or default value

    return 0.4  # Lots of text — probably a section/label region


def _detect_drawing_areas(page, page_width, page_height) -> list:
    """
    Detect large empty regions that are likely drawing/attachment areas.

    HHE-200 specific areas:
    - Page 3: Site plan drawing area
    - Page 4: Disposal plan and cross-section drawing areas
    - Pages 7+8: Full-page blank AutoCAD drawing areas

    These are identified as large empty rectangles with no text content.
    """
    areas = []
    rects = page.rects
    words = page.extract_words()

    # Heuristic: a drawing area is a large rect (>200pt wide, >150pt tall)
    # with no words inside it
    for rect in rects:
        bbox = rect["bbox"]
        x0, y0_top, x1, y1_top = bbox
        w, h = x1 - x0, y1_top - y0_top

        if w < 200 or h < 150:
            continue

        # Check for words inside
        words_inside = [
            w for w in words
            if w["x0"] >= x0 and w["x1"] <= x1
            and w["top"] >= y0_top and w["bottom"] <= y1_top
        ]

        if len(words_inside) > 5:
            continue  # Too much text — not a drawing area

        coords = pdfplumber_bbox_to_pdf_coords(bbox, page_height)

        # Try to label the area based on position
        label = _label_drawing_area(x0, y0_top, page_width, page_height)

        areas.append({
            "label": label,
            "x": coords["x"],
            "y": coords["y"],
            "width": coords["width"],
            "height": coords["height"],
        })

    return areas


def _label_drawing_area(x, y_top, page_width, page_height) -> str:
    """
    Assign a descriptive label to a drawing area based on its position.

    HHE-200 page layout assumptions:
    - Site plan area is typically in the upper portion of page 3
    - Cross-section area is typically in the lower portion of page 4
    """
    y_ratio = y_top / page_height

    if y_ratio < 0.3:
        return "Site Plan Drawing Area"
    elif y_ratio < 0.6:
        return "Disposal Plan Drawing Area"
    else:
        return "Cross-Section Drawing Area"


def _deduplicate_fields(fields: list[FieldBox]) -> list[FieldBox]:
    """
    Remove duplicate/overlapping field detections.

    When multiple detections overlap significantly, keep the one with
    higher confidence or larger area.
    """
    if not fields:
        return []

    # Sort by confidence descending, then by area descending
    sorted_fields = sorted(
        fields,
        key=lambda f: (f.confidence, f.width * f.height),
        reverse=True
    )

    result = []
    for candidate in sorted_fields:
        is_duplicate = False
        for existing in result:
            overlap = _bbox_overlap(candidate, existing)
            if overlap > 0.5:  # More than 50% overlap
                is_duplicate = True
                break
        if not is_duplicate:
            result.append(candidate)

    # Sort final list by position (top-to-bottom, left-to-right)
    result.sort(key=lambda f: (f.y, f.x))
    return result


def _bbox_overlap(a: FieldBox, b: FieldBox) -> float:
    """
    Calculate overlap ratio between two bounding boxes.
    Returns 0.0 (no overlap) to 1.0 (identical).
    """
    x_overlap = max(0, min(a.x + a.width, b.x + b.width) - max(a.x, b.x))
    y_overlap = max(0, min(a.y + a.height, b.y + b.height) - max(a.y, b.y))

    if x_overlap == 0 or y_overlap == 0:
        return 0.0

    overlap_area = x_overlap * y_overlap
    a_area = a.width * a.height
    b_area = b.width * b.height
    min_area = min(a_area, b_area)

    return overlap_area / min_area


# =============================================================================
# OUTPUT
# =============================================================================

def save_page_fields(output_dir: Path, page_number: int, fields: list[FieldBox]):
    """Save one page's fields to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_data = {
        "page_number": page_number,
        "page_width": fields[0].page_width if fields else 0,
        "page_height": fields[0].page_height if fields else 0,
        "fields": [
            {
                "label": f.label,
                "x": f.x,
                "y": f.y,
                "width": f.width,
                "height": f.height,
                "page_width": f.page_width,
                "page_height": f.page_height,
                "text": f.text,
                "confidence": round(f.confidence, 2),
                "field_type": f.field_type,
            }
            for f in fields
        ]
    }

    output_path = output_dir / f"page_{page_number}.json"
    with open(output_path, "w") as fp:
        json.dump(output_data, fp, indent=2)

    print(f"  Page {page_number}: {len(fields)} fields → {output_path.name}")


def save_summary(output_dir: Path, all_pages: list[PageFields]):
    """Save combined summary of all pages."""
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_pages": len(all_pages),
        "pages": [
            {
                "page_number": pf.page_number,
                "page_width": pf.page_width,
                "page_height": pf.page_height,
                "field_count": len(pf.fields),
                "fields": [
                    {
                        "label": f.label,
                        "x": f.x,
                        "y": f.y,
                        "width": f.width,
                        "height": f.height,
                        "field_type": f.field_type,
                        "confidence": round(f.confidence, 2),
                    }
                    for f in pf.fields
                ]
            }
            for pf in all_pages
        ]
    }

    output_path = output_dir / "field_map_summary.json"
    with open(output_path, "w") as fp:
        json.dump(summary, fp, indent=2)

    print(f"\nSummary saved → {output_path.name}")


# =============================================================================
# MANUAL VERIFICATION INSTRUCTIONS
# =============================================================================

MANUAL_VERIFICATION_NOTES = """
# Manual Verification Instructions

AI-assisted field detection is imperfect. Always verify and correct the output
before using it to drive Hermes PDF tool calls.

## How to Verify

1. Open the HHE-200 PDF in Adobe Acrobat Reader (free).
2. Open the corresponding `page_N.json` file.
3. For each field in the JSON:
   a. Note the x, y, width, height values.
   b. In Acrobat, use Tools > Print Production > Preflight
      or the measuring tool to confirm coordinates.
   c. Check the label against the actual form field.

## Common Detection Issues

| Issue | Fix |
|-------|-----|
| Field detected but wrong position | Adjust x/y manually in the JSON |
| Two fields merged into one | Split into two entries with separate coordinates |
| Checkbox not detected | Add manually: field_type="checkbox", use Acrobat to get exact coords |
| Label text used instead of field coords | Use the label only to identify the field, then find the adjacent input box |
| Drawing area dimensions wrong | Re-measure with Acrobat measuring tool |

## Coordinate Verification in Acrobat Reader

1. Open the PDF.
2. Go to View > Tools > Measure to activate the measuring tool.
3. Click and drag to measure from the left edge and bottom edge to the
   field's upper-left corner.
4. Record x (horizontal) and y (vertical) in points.
5. Compare to JSON values. Adjust if off by more than 2–3 points.

## Field Naming Convention

Use descriptive field names in the JSON that match the HHE-200 form sections:

    property_address    → "Property Address"
    owner_name          → "Owner/Applicant Name"
    tax_map             → "Municipal Tax Map #"
    lot_number          → "Lot #"
    disposal_field_type → "Disposal Field Type"
    soil_class          → "Soil Classification"
    percolation_rate    → "Percolation Rate"
    oh1_depth           → "OH-1 Depth to Refusal"
    ...

Consistent naming makes it easy for Hermes to map sheet row values → PDF fields.
"""


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract HHE-200 PDF field coordinates for Hermes form filling."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the HHE-200 PDF file. "
             "NOTE: Download from Google Drive first if the file is stored there. "
             "The HHE-200 PDF lives in Google Drive under "
             "bouchlesshay@gmail.com — download locally before running this script."
    )
    parser.add_argument(
        "--output", "-o",
        default="openevaluator/data/fields",
        help="Output directory for page_N.json files (default: openevaluator/data/fields)"
    )
    parser.add_argument(
        "--pages", "-p",
        help="Comma-separated page numbers to process, or 'all' (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed field info per page"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        print("\nNOTE: The HHE-200 PDF must be downloaded from Google Drive first.")
        print("Path in Drive: drive.google.com → My Drive → HHE-200 form")
        sys.exit(1)

    output_dir = Path(args.output)

    # Optional page filter
    page_filter = None
    if args.pages and args.pages.lower() != "all":
        try:
            page_filter = set(int(p) for p in args.pages.split(","))
        except ValueError:
            print(f"Error: Invalid page numbers: {args.pages}")
            sys.exit(1)

    print(f"\nProcessing: {pdf_path}")
    print(f"Output dir:  {output_dir}")
    print()

    all_pages: list[PageFields] = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF has {total_pages} pages\n")

        for i, page in enumerate(pdf.pages, start=1):
            page_num = i
            if page_filter and page_num not in page_filter:
                continue

            print(f"  Processing page {page_num}...", end=" ", flush=True)
            fields = detect_fields_on_page(page)

            if fields:
                save_page_fields(output_dir, page_num, fields)
                all_pages.append(PageFields(
                    page_number=page_num,
                    page_width=page.width,
                    page_height=page.height,
                    fields=fields
                ))
            else:
                print(f"(no fields detected)")

    if all_pages:
        save_summary(output_dir, all_pages)

    print("\n---")
    print("Manual verification REQUIRED. AI detection may miss or misplace fields.")
    print("See 'Manual Verification Instructions' in the source script comments.")
    print(f"\nVerify page coordinates in Adobe Acrobat Reader using the measuring tool.")
    print(f"Correct any inaccurate entries in: {output_dir}/page_N.json")

    # Write verification notes to file
    notes_path = output_dir / "MANUAL_VERIFICATION_NOTES.md"
    with open(notes_path, "w") as fp:
        fp.write(MANUAL_VERIFICATION_NOTES)
    print(f"Verification notes written to: {notes_path.name}")


if __name__ == "__main__":
    main()
