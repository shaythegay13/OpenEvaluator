#!/usr/bin/env python3
"""
Analyze what data Hermes needs to extract from sketches to generate accurate drawings.
Compare example drawings to understand the required drawing elements.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import fitz  # PyMuPDF for PDF analysis

# Example PDFs to analyze
EXAMPLE_1_DIR = Path("example/example 1")
EXAMPLE_2_DIR = Path("example/example 2")

print("\n" + "="*80)
print("HERMES DRAWING REQUIREMENTS ANALYSIS")
print("="*80)

# Analyze example 1 (26-018 Kristen Marquis property)
print("\n[EXAMPLE 1] 26-018 Kristen Marquis (Turner, ME)")
print("-" * 80)

pg3_path = EXAMPLE_1_DIR / "26-018 PG3 (1).pdf"
pg4_path = EXAMPLE_1_DIR / "26-018 PG4 (1).pdf"

if pg3_path.exists():
    print(f"\n✓ Page 3 (Site Plan): {pg3_path.name}")
    doc = fitz.open(str(pg3_path))
    page = doc[0]
    text = page.get_text()

    # Extract annotations, drawings, text
    print(f"  File size: {pg3_path.stat().st_size} bytes")
    print(f"  Text content (first 500 chars):\n{text[:500]}")

    # Look for specific elements
    elements_found = []
    if "property" in text.lower():
        elements_found.append("Property boundary")
    if "well" in text.lower():
        elements_found.append("Well location")
    if "disposal" in text.lower():
        elements_found.append("Disposal field")
    if "septic" in text.lower():
        elements_found.append("Septic tank")
    if "scale" in text.lower():
        elements_found.append("Scale notation")
    if "distance" in text.lower():
        elements_found.append("Distance measurements")

    if elements_found:
        print(f"  Key elements visible: {', '.join(elements_found)}")

    doc.close()

if pg4_path.exists():
    print(f"\n✓ Page 4 (Disposal Plan & Cross-Section): {pg4_path.name}")
    doc = fitz.open(str(pg4_path))
    page = doc[0]
    text = page.get_text()

    print(f"  File size: {pg4_path.stat().st_size} bytes")
    print(f"  Text content (first 500 chars):\n{text[:500]}")

    # Look for specific elements
    elements_found = []
    if "disposal" in text.lower():
        elements_found.append("Disposal field")
    if "tank" in text.lower():
        elements_found.append("Tank/treatment")
    if "elevation" in text.lower():
        elements_found.append("Elevation marks")
    if "feet" in text.lower():
        elements_found.append("Depth measurements")
    if "ground" in text.lower():
        elements_found.append("Ground level")

    if elements_found:
        print(f"  Key elements visible: {', '.join(elements_found)}")

    doc.close()

# Check what raw sketch data we have for row 2
print("\n" + "="*80)
print("CURRENT HERMES OUTPUT STATE")
print("="*80)

hermes_json_path = Path("hermes_output.json")
if hermes_json_path.exists():
    with open(hermes_json_path) as f:
        hermes_data = json.load(f)

    print(f"\nhermes_output.json keys: {list(hermes_data.keys())}")
    print(f"Populated fields:")
    for key, value in hermes_data.items():
        if value:
            if isinstance(value, (list, dict)):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {str(value)[:60]}")

# Required data for site plan drawing
print("\n" + "="*80)
print("REQUIRED DATA FOR ACCURATE DRAWINGS")
print("="*80)

required_site_plan = {
    "Property dimensions": ["boundary points", "acreage", "property shape"],
    "Features": ["well location", "existing septic tank", "roads/driveways", "water features"],
    "Distances/Setbacks": ["well setback from property", "building setback", "road frontage"],
    "Scale": ["drawing scale (e.g., 1\" = 40')"],
    "Annotations": ["distance markers", "direction indicators", "scale notation"],
}

required_disposal_plan = {
    "System layout": ["treatment tank position", "distribution box", "field layout"],
    "Field type": ["proprietary device dimensions", "drain lines/modules", "orientation"],
    "Connections": ["inlet/outlet pipes", "access points", "flow direction"],
    "Measurements": ["field length/width", "spacing between trenches", "depth notation"],
    "Scale": ["drawing scale"],
}

required_cross_section = {
    "Vertical profile": ["ground level (finished grade)", "water table depth", "restrictive layer depth"],
    "Elements": ["septic tank", "distribution box", "disposal field", "soil profile"],
    "Elevations": ["grade elevation", "top of tank", "bottom of tank", "disposal depth", "water table level"],
    "Measurements": ["all depth measurements", "distance from grade"],
}

print("\nSite Plan required data:")
for category, items in required_site_plan.items():
    print(f"  {category}: {', '.join(items)}")

print("\nDisposal Plan required data:")
for category, items in required_disposal_plan.items():
    print(f"  {category}: {', '.join(items)}")

print("\nCross-Section required data:")
for category, items in required_cross_section.items():
    print(f"  {category}: {', '.join(items)}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("""
1. Improve OCR/Vision API to extract:
   - Measurements and dimensions from sketches
   - Text annotations and labels
   - Geometric shapes and positions
   - Scale notations
   - Property boundaries and feature locations

2. Parse extracted data to:
   - Calculate distances and proportions
   - Determine scale from reference measurements
   - Identify feature types and positions
   - Establish elevation relationships

3. Generate drawings using:
   - Site plan generator: property bounds, features, distances
   - Disposal plan generator: tank/field layout, system type, connections
   - Cross-section generator: elevations, soil profile, depths

4. Compare with examples:
   - Overlay generated drawings with example PDFs
   - Identify discrepancies in layout, scale, positioning
   - Train Hermes to correct extracted data
""")
