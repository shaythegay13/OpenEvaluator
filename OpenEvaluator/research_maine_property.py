#!/usr/bin/env python3
"""
Maine Property Research Module

Research property information from online sources:
  - Maine tax assessor records
  - County deeds and property records
  - Property GIS/tax maps
  - Municipal zoning regulations

Returns enriched property data for drawing generator.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def research_maine_property(
    address: str,
    town: str,
    map_lot: str = "",
    state: str = "Maine"
) -> Dict:
    """
    Research a Maine property online for deed/tax map information.

    This should be called by Hermes or similar to search:
      1. Maine tax assessor online records
      2. County deed records
      3. GIS property boundary data
      4. Local zoning/setback requirements

    Args:
        address: Street address (e.g., "17 Aspen Way")
        town: Town name (e.g., "Turner")
        map_lot: Map and Lot (e.g., "26-18")
        state: State (default: Maine)

    Returns:
        Dictionary with property data to feed into drawing generator
    """

    property_data = {
        "address": address,
        "town": town,
        "map_lot": map_lot,
        "state": state,

        # Property boundary - from tax map/deed (needed for realistic site plan)
        "property_boundary": {
            "vertices": [],  # [(x, y), ...] - actual lot boundary coordinates
            "shape": "unknown",  # polygon shape
            "area_acres": None,
            "perimeter_ft": None,
        },

        # Road information - from county/town records
        "road_information": {
            "name": None,  # "Aspen Way", "Route 2", etc.
            "type": None,  # "public", "private", "town"
            "distance_ft": None,  # distance from house to road
            "direction": None,  # "North", "South", etc.
        },

        # Existing structures - from property records/GIS
        "existing_structures": [
            # {
            #     "type": "dwelling",  # dwelling, garage, deck, shed, well, etc.
            #     "x": 50,  # coordinates relative to property boundary
            #     "y": 100,
            #     "width": 30,
            #     "depth": 40,
            #     "annotation": "SINGLE FAMILY DWELLING"
            # }
        ],

        # Lot information - from deed/tax map
        "lot_info": {
            "lot_number": None,
            "frontage_ft": None,  # road frontage
            "depth_ft": None,
            "subdivision": None,
        },

        # Zoning and setbacks - from municipal records
        "zoning": {
            "zone": None,  # "residential", "agricultural", etc.
            "setback_road": None,  # required distance from road
            "setback_property_line": None,  # required distance from lot line
            "setback_well": None,  # required distance from well
            "min_lot_size": None,
        },

        # Natural features - from GIS/maps
        "natural_features": {
            "wetlands": [],  # [{type, location, size}]
            "water_bodies": [],
            "wooded_areas": [],
            "slopes": None,  # terrain type
            "elevation": None,
        },

        # Research status
        "research_sources": [],  # Track which sources were checked
        "data_complete": False,
    }

    logger.info(f"Property research template for {address}, {town}, ME")
    logger.info("To complete research, check these sources:")
    logger.info("  1. Maine tax assessor (likely town-specific online)")
    logger.info("  2. County deed records or Maine Secretary of State")
    logger.info("  3. County GIS/property mapping system")
    logger.info("  4. Municipal zoning ordinances")
    logger.info(f"  5. For {map_lot}: Map & Lot records from town")

    return property_data


def get_search_queries_for_property(
    address: str,
    town: str,
    map_lot: str = "",
    state: str = "Maine"
) -> Dict[str, str]:
    """
    Generate search queries to find property information online.

    Uses map and lot number as primary lookup key, with address as fallback.
    These queries can be used by Hermes or similar to search various sources.
    """
    queries = {
        "map_lot_maine_assessor": f'map {map_lot} {town} Maine tax assessor property',
        "town_gis": f'{town} Maine GIS property map lot {map_lot}',
        "maine_assessor": f'"{address}" {town} Maine tax assessor property record',
        "county_deed": f'"{address}" "{town}" Maine deed property record',
        "zoning": f'{town} Maine zoning ordinances setback requirements residential',
    }
    return queries


def parse_property_research_results(
    research_results: Dict[str, str],
    form_data: Dict
) -> Dict:
    """
    Parse research results and merge with form data to create enriched property info.

    This would be called after Hermes researches the property.

    Args:
        research_results: Dictionary of search results for each query
        form_data: Original HHE-200 form data

    Returns:
        Enriched property data ready for drawing generator
    """

    enriched = research_maine_property(
        address=form_data.get("Property Location Details", "").split(",")[0].strip(),
        town=form_data.get("Property Location Details", "").split(",")[1].strip() if "," in form_data.get("Property Location Details", "") else "",
        map_lot=form_data.get("Map and Lot # and Acreage", "").split(",")[0:2],
    )

    # Would parse research_results and populate enriched data
    # For now, this is a placeholder showing the expected flow

    return enriched


if __name__ == "__main__":
    # Example
    form_data = {
        "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
        "Map and Lot # and Acreage": "26, 18, 2.35",
    }

    # Get research queries
    queries = get_search_queries_for_property(
        "17 Aspen Way", "Turner", "Maine"
    )
    print("Research queries needed:")
    for key, query in queries.items():
        print(f"  {key}: {query}")

    # Create template
    template = research_maine_property("17 Aspen Way", "Turner", "26-18")
    print(f"\nProperty data template:\n{json.dumps(template, indent=2)}")
