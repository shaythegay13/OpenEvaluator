#!/usr/bin/env python3
"""
Integrate professional drawings into HHE-200 PDF workflow.

Uses professional_drawings.py enriched with property data researched online.
Workflow:
  1. Extract property identifiers (address, map, lot) from form
  2. Research property boundary, road, structures, zoning online
  3. Merge research results with form data
  4. Generate professional drawings with real property information
  5. Embed in PDF
"""

from pathlib import Path
import sys
import json
import logging

sys.path.insert(0, str(Path(__file__).parent))
from professional_drawings import ProfessionalDrawingGenerator
from dxf_to_png_renderer import render_dxf_to_png
from property_enrichment_engine import PropertyEnrichmentEngine, format_enrichment_results
from enrich_property_data import (
    extract_property_identifiers,
    create_research_request,
    generate_hermes_task,
    merge_research_results,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_professional_drawings(
    site_data: dict,
    system_data: dict,
    output_dir: str = ".",
    enriched_property_data: dict = None,
) -> tuple:
    """
    Generate professional drawings with enriched property data.

    Workflow:
      1. Extract property identifiers (map, lot, address, town)
      2. Log research requirements if property data not provided
      3. Accept enriched property data if available
      4. Pass merged data to professional_drawings.py
      5. Generate and save DXF files

    Args:
        site_data: Site information from HHE-200 form
        system_data: System design information
        output_dir: Output directory for DXF files
        enriched_property_data: Optional - researched property data to merge

    Returns:
        Tuple of (pg3_dxf_path, locus_dxf_path, pg4_dxf_path, xsect_dxf_path)
    """

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Merge all data
    merged_data = {**site_data, **system_data}

    # Extract property identifiers from form
    identifiers = extract_property_identifiers(merged_data)
    logger.info(f"Property: {identifiers.get('address', '?')}, {identifiers.get('town', '?')}")
    logger.info(f"Map {identifiers.get('map', '?')} Lot {identifiers.get('lot', '?')}")

    # Phase 2: Attempt to enrich property data automatically
    enrichment_engine = PropertyEnrichmentEngine()
    enrichment_results = enrichment_engine.enrich_property(merged_data)

    if enrichment_results.get("status") == "found":
        logger.info("✓ Property enrichment successful")
        property_data = enrichment_results.get("property_data", {})
        merged_data.update(property_data)
        logger.info(f"  Source: {enrichment_results.get('source')}")
        logger.info(f"  Confidence: {enrichment_results.get('confidence')}")

        if enrichment_results.get("used_for_drawings"):
            logger.info("  ✓ Data will be used in drawings")
    else:
        logger.warning(f"⚠ Property enrichment status: {enrichment_results.get('status')}")
        if enrichment_results.get("errors"):
            for error in enrichment_results["errors"]:
                logger.warning(f"    {error}")

    # Check if we have enriched property data from parameter
    if enriched_property_data:
        logger.info("✓ Using provided enriched property data for drawings")
        merged_data.update(enriched_property_data)

    # Generate drawings using professional drawing generator
    logger.info("Generating professional drawings…")

    gen = ProfessionalDrawingGenerator()

    # Page 3: Site Plan
    logger.info("  Page 3: Site Plan (with property boundary)")
    dwg3 = gen.create_page3_site_plan(merged_data)
    dxf3_path = out_dir / "PG3.dxf"
    gen.save(str(dxf3_path))
    logger.info(f"    ✓ {dxf3_path.name}")

    # Page 4: Disposal Plan & Cross-Section
    logger.info("  Page 4: Disposal Plan & Cross-Section")
    gen2 = ProfessionalDrawingGenerator()
    dwg4 = gen2.create_page4_disposal_and_section(merged_data)
    dxf4_path = out_dir / "PG4.dxf"
    gen2.save(str(dxf4_path))
    logger.info(f"    ✓ {dxf4_path.name}")

    # Convert DXF files to PNG for embedding in PDF
    logger.info("Converting DXF drawings to PNG…")

    png3_path = out_dir / "site_plan_pg3.png"
    locus_path = out_dir / "locus_map.png"
    png4_path = out_dir / "disposal_plan_pg4.png"
    xsect_path = out_dir / "cross_section_pg4.png"

    render_dxf_to_png(str(dxf3_path), str(png3_path), width=600, height=800)
    render_dxf_to_png(str(dxf3_path), str(locus_path), width=300, height=400)  # Locus map from same DXF
    render_dxf_to_png(str(dxf4_path), str(png4_path), width=800, height=900)
    render_dxf_to_png(str(dxf4_path), str(xsect_path), width=800, height=600)  # Cross-section from same DXF

    logger.info("  ✓ PNG rendering complete")

    return (
        str(png3_path.resolve()),
        str(locus_path.resolve()),
        str(png4_path.resolve()),
        str(xsect_path.resolve()),
    )


if __name__ == "__main__":
    # Example test without enriched data
    test_site_data = {
        "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
        "Map and Lot # and Acreage": "26, 18, 2.35",
    }
    test_system_data = {
        "tank_size": 1000,
        "disposal_field": "3 rows x 7 modules",
    }

    # Example with enriched property data
    enriched = {
        "property_boundary": {
            "vertices": [
                [100, 100],
                [300, 100],
                [350, 250],
                [100, 250],
            ]  # Example coordinates
        },
        "road": {
            "name": "Aspen Way",
            "type": "public",
            "distance_ft": 50,
        },
    }

    paths = generate_professional_drawings(
        test_site_data, test_system_data, enriched_property_data=enriched
    )
    print(f"Generated DXF files:")
    for i, path in enumerate(paths):
        print(f"  {i+1}. {Path(path).name}")
