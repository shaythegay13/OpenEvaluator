#!/usr/bin/env python3
"""
Property Data Enrichment for HHE-200 Drawings

Enriches submission data with property information researched online
using map and lot number as primary lookup.

This module orchestrates:
  1. Extraction of address, map, lot from form data
  2. Online research (via Hermes or web search) for property details
  3. Parsing results into drawing-ready format
  4. Merging with original form data
"""

import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_property_identifiers(form_data: Dict) -> Dict:
    """
    Extract property location identifiers from HHE-200 form data.

    Returns:
        Dictionary with address, town, map, lot, acreage
    """
    identifiers = {}

    # Parse property location
    if "Property Location Details" in form_data:
        loc = form_data["Property Location Details"]
        parts = [p.strip() for p in loc.split(",")]
        if len(parts) >= 1:
            identifiers["address"] = parts[0]
        if len(parts) >= 2:
            identifiers["town"] = parts[1]
        if len(parts) >= 3:
            identifiers["state"] = parts[2] if "Maine" not in parts[2] else "Maine"

    # Parse map and lot
    if "Map and Lot # and Acreage" in form_data:
        lot_data = form_data["Map and Lot # and Acreage"]
        parts = [p.strip() for p in lot_data.split(",")]
        if len(parts) >= 1:
            identifiers["map"] = parts[0]
        if len(parts) >= 2:
            identifiers["lot"] = parts[1]
        if len(parts) >= 3:
            try:
                identifiers["acreage"] = float(parts[2])
            except ValueError:
                identifiers["acreage"] = None

    return identifiers


def create_research_request(identifiers: Dict) -> Dict:
    """
    Create a structured research request for property information.

    This is what Hermes (or other research tool) needs to find:
      - Property boundary coordinates
      - Road information (name, distance, direction)
      - Existing structures and their locations
      - Lot dimensions and divisions
      - Zoning and setback requirements
      - Natural features (wetlands, water bodies, woods)
    """

    map_lot_str = f"Map {identifiers.get('map', '?')} Lot {identifiers.get('lot', '?')}"

    research_request = {
        "property_id": f"{map_lot_str}, {identifiers.get('town', 'Unknown')}, Maine",
        "map": identifiers.get("map"),
        "lot": identifiers.get("lot"),
        "town": identifiers.get("town"),
        "address": identifiers.get("address"),
        "acreage": identifiers.get("acreage"),

        "research_needed": {
            "property_boundary": {
                "description": "Property boundary polygon coordinates (vertices)",
                "source": "Tax assessor, county GIS, or deed description",
                "importance": "HIGH - Required for realistic site plan",
                "search_query": f'"{map_lot_str}" {identifiers.get("town")} Maine property boundary GIS',
            },
            "road_information": {
                "description": "Road name, type (public/private), distance from house",
                "source": "Tax map, deed, or local assessor",
                "importance": "HIGH - Needed to label and position road",
                "search_query": f'"{identifiers.get("address")}" {identifiers.get("town")} Maine road frontage',
            },
            "lot_dimensions": {
                "description": "Frontage feet, depth feet, lot shape",
                "source": "Deed, tax map, assessor record",
                "importance": "MEDIUM - For accurate lot representation",
                "search_query": f'{map_lot_str} {identifiers.get("town")} Maine lot dimensions',
            },
            "existing_structures": {
                "description": "Location and size of dwelling, garage, other buildings",
                "source": "Tax assessor property card, if publicly available",
                "importance": "MEDIUM - For accurate structure placement",
                "search_query": f'{map_lot_str} {identifiers.get("town")} Maine property structures buildings',
            },
            "zoning_and_setbacks": {
                "description": "Zone type, required setbacks (road, property line, well)",
                "source": "Municipal zoning ordinances",
                "importance": "MEDIUM - For setback visualization",
                "search_query": f'{identifiers.get("town")} Maine zoning ordinances residential setback requirements',
            },
            "natural_features": {
                "description": "Wetlands, water bodies, wooded areas, terrain",
                "source": "USGS maps, GIS, property records",
                "importance": "LOW - For context",
                "search_query": f'{identifiers.get("town")} Maine GIS wetlands {map_lot_str}',
            },
        },

        "next_steps": [
            "1. Hermes searches for each item in 'research_needed'",
            "2. Extract and structure findings into property_data format",
            "3. Merge with form_data and pass to professional_drawings.py",
            "4. Generator creates drawings with real property information",
        ],
    }

    return research_request


def merge_research_results(
    form_data: Dict,
    research_results: Dict
) -> Dict:
    """
    Merge researched property data with original form data.

    Args:
        form_data: Original HHE-200 submission
        research_results: Results from property research

    Returns:
        Enriched data ready for drawing generator
    """

    enriched = {
        **form_data,
        **research_results,
        "property_research_complete": True,
        "property_research_sources": research_results.get("sources", []),
    }

    return enriched


def generate_hermes_task(identifiers: Dict) -> str:
    """
    Generate a Hermes task description to research the property.

    Returns a formatted task that Hermes (or similar agent) can execute.
    """

    task = f"""
TASK: Research Maine Property {identifiers.get('map')}-{identifiers.get('lot')}

PROPERTY DETAILS:
- Address: {identifiers.get('address', 'Unknown')}
- Town: {identifiers.get('town', 'Unknown')}
- Map & Lot: {identifiers.get('map', '?')}-{identifiers.get('lot', '?')}
- Acreage: {identifiers.get('acreage', 'Unknown')}

RESEARCH OBJECTIVES (in priority order):

1. PROPERTY BOUNDARY COORDINATES (HIGH PRIORITY)
   Search: "{identifiers.get('map')}-{identifiers.get('lot')}" {identifiers.get('town')} Maine GIS property tax map
   What to find: Lot boundary vertices/coordinates, property polygon shape
   Where to look: County GIS, town assessor online mapping, property deed

2. ROAD INFORMATION (HIGH PRIORITY)
   Search: "{identifiers.get('address')}" {identifiers.get('town')} Maine road
   What to find: Road name, whether public/private, distance from main structure
   Where to look: Deed, tax map, Google Maps, town records

3. LOT DIMENSIONS (MEDIUM PRIORITY)
   Search: "{identifiers.get('map')}-{identifiers.get('lot')}" {identifiers.get('town')} Maine lot dimensions
   What to find: Road frontage (feet), lot depth, shape description
   Where to look: Tax assessor, deed, property record

4. ZONING & SETBACKS (MEDIUM PRIORITY)
   Search: {identifiers.get('town')} Maine zoning ordinances residential setback
   What to find: Minimum setbacks from road, property lines, wells (in feet)
   Where to look: Town zoning ordinance, municipal regulations

5. EXISTING STRUCTURES (OPTIONAL)
   Search: {identifiers.get('map')}-{identifiers.get('lot')} {identifiers.get('town')} Maine property structures
   What to find: If available: dwelling location, garage, other buildings on property
   Where to look: Tax assessor property card, property records

DELIVERABLE:
Return structured data in this format:
{{
  "property_boundary": {{"vertices": [[x1,y1], [x2,y2], ...]}},
  "road": {{"name": "Road Name", "type": "public/private", "distance_ft": 50}},
  "lot": {{"frontage_ft": 200, "depth_ft": 300}},
  "zoning": {{"setback_road_ft": 50, "setback_line_ft": 30, "setback_well_ft": 100}},
  "sources": ["source1", "source2", ...]
}}
"""
    return task.strip()


if __name__ == "__main__":
    # Example usage
    test_form_data = {
        "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
        "Map and Lot # and Acreage": "26, 18, 2.35",
        "Client name, Phone number, and Address": "Kristen Marquis, empty, empty",
    }

    # Extract identifiers
    identifiers = extract_property_identifiers(test_form_data)
    print("Extracted Property Identifiers:")
    print(json.dumps(identifiers, indent=2))

    # Create research request
    research_request = create_research_request(identifiers)
    print("\nResearch Request:")
    print(json.dumps(research_request, indent=2))

    # Generate Hermes task
    hermes_task = generate_hermes_task(identifiers)
    print("\nHermes Task:")
    print(hermes_task)
