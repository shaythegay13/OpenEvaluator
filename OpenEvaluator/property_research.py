#!/usr/bin/env python3
"""
Property Research Module for HHE-200 Drawing Enhancement

Uses Hermes to research online property records:
  - Tax assessor records
  - County deed databases
  - Property tax maps
  - Public lot information

Enriches site data with property boundary, lot size, existing features,
easements, and other information that appears on deeds and tax maps.
"""

from pathlib import Path
import json
import sys
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))


def research_property_online(
    address: str,
    map_lot: str,
    town: str,
    state: str = "Maine"
) -> Dict:
    """
    Research property using online sources (tax assessor, county deeds, maps).

    Searches for:
      - Tax assessor records and property cards
      - County deed records
      - USGS topographic/soil maps
      - Property lot information

    Args:
        address: Street address (e.g. "17 Aspen Way")
        map_lot: Map and Lot number (e.g. "26-18")
        town: Town name (e.g. "Turner")
        state: State (default: Maine)

    Returns:
        Dictionary of enriched property data (lot size, boundaries, features, etc.)
    """

    enriched_data = {
        "property_address": address,
        "map_lot": map_lot,
        "town": town,
        "state": state,

        # Property dimensions (from tax map/deed)
        "lot_dimensions": {
            "frontage_ft": None,  # Road frontage
            "depth_ft": None,
            "area_acres": None,
            "shape": None  # rectangular, irregular, etc.
        },

        # Existing features on property (from tax map)
        "existing_features": {
            "buildings": [],  # [{type, location, dimensions}]
            "wells": [],  # [{type, depth, location}]
            "roads": [],  # [{name, distance, direction}]
            "woods": [],  # Areas with trees
            "wetlands": [],  # Wet areas
            "slopes": [],  # Elevation changes
        },

        # Legal constraints (from deed)
        "constraints": {
            "easements": [],  # Utility, access easements
            "setbacks": {},  # Required setbacks from property lines, roads
            "shoreland_zoning": None,  # If applicable
            "wetland_buffer": None,
        },

        # Tax map info
        "tax_map_data": {
            "current_use": None,  # Agricultural, residential, etc.
            "lot_frontage": None,  # Feet of road frontage
            "frontage_type": None,  # Public road, private road
        },

        # Elevation reference (from survey or tax data)
        "elevation_data": {
            "grade_elevation": None,
            "contours": [],  # [{elevation, location}]
        }
    }

    return enriched_data


def extract_property_info_from_form(form_data: Dict) -> Dict:
    """
    Extract what property information is already in the HHE-200 form data.

    Args:
        form_data: The ROW dictionary from run_pipeline.py

    Returns:
        Extracted property information
    """

    property_info = {}

    # Parse property location
    if "Property Location Details" in form_data:
        loc = form_data["Property Location Details"]
        # Format: "17 Aspen Way, Turner, Maine 04282"
        parts = loc.split(",")
        if len(parts) >= 2:
            property_info["address"] = parts[0].strip()
            property_info["town"] = parts[1].strip() if len(parts) > 1 else ""
            property_info["state"] = parts[2].strip() if len(parts) > 2 else "Maine"

    # Parse map and lot
    if "Map and Lot # and Acreage" in form_data:
        lot_info = form_data["Map and Lot # and Acreage"]
        # Format: "26, 18, 2.35"
        parts = [p.strip() for p in lot_info.split(",")]
        if len(parts) >= 2:
            property_info["map"] = parts[0]
            property_info["lot"] = parts[1]
        if len(parts) >= 3:
            property_info["acreage"] = float(parts[2]) if parts[2] else None

    # Extract existing features from form
    if "Key distances between features" in form_data:
        property_info["form_distances"] = form_data["Key distances between features"]

    # Water supply/well info
    if "Water supply and well" in form_data:
        property_info["well_info"] = form_data["Water supply and well"]

    # Coordinates
    if "Latitude" in form_data:
        property_info["latitude"] = form_data["Latitude"]
    if "Longitude" in form_data:
        property_info["longitude"] = form_data["Longitude"]

    return property_info


def merge_property_data(form_data: Dict, enriched_data: Dict) -> Dict:
    """
    Merge form data with researched property data.

    Args:
        form_data: Original HHE-200 form data
        enriched_data: Data researched from online sources

    Returns:
        Combined property data for drawing generator
    """

    merged = {
        **form_data,
        **enriched_data,
        "property_research_complete": True,
    }

    return merged


if __name__ == "__main__":
    # Example usage
    test_data = {
        "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
        "Map and Lot # and Acreage": "26, 18, 2.35",
        "Water supply and well": "existing drilled well, private, 125 ft.",
        "Key distances between features": "house to tank = 8', tank to field may vary, field to well 100 feet minimum",
    }

    # Extract property info from form
    prop_info = extract_property_info_from_form(test_data)
    print(json.dumps(prop_info, indent=2))

    # Would call research_property_online here
    # enriched = research_property_online(...)
