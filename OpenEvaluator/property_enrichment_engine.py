#!/usr/bin/env python3
"""
Property Enrichment Engine - Phase 2 Production Implementation

Enriches HHE-200 form submissions with property data from multiple sources:
1. Cached/manual research (fallback for known properties)
2. Form-submitted data (deed/tax map documents - future)
3. Online sources (Maine GeoLibrary, O'Donnell CAMA - attempted)
4. User input (manual entry for properties not found)

Strategy:
- Primary source: Cached research database (most reliable)
- Secondary: Online queries (when available)
- Fallback: None (property enrichment optional)
"""

import logging
import json
from typing import Dict, Optional
from pathlib import Path
import sys

# Try to import enhanced researcher for Phase 3C
try:
    from maine_property_research_v2 import MainePropertyResearcherV2
    HAS_ENHANCED_RESEARCH = True
except ImportError:
    HAS_ENHANCED_RESEARCH = False
    logger = logging.getLogger(__name__)

# Try to import persistent database manager
try:
    from property_database_manager import PropertyDatabaseManager
    HAS_DB_MANAGER = True
except ImportError:
    HAS_DB_MANAGER = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyDatabase:
    """Property database - uses persistent storage if available, falls back to in-memory"""

    _manager = None  # Cached database manager instance

    @classmethod
    def _get_manager(cls) -> "PropertyDatabaseManager":
        """Get or create the database manager instance"""
        if cls._manager is None and HAS_DB_MANAGER:
            cls._manager = PropertyDatabaseManager()
        return cls._manager

    @classmethod
    def lookup(cls, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """Look up property in database. Town is required (no default)."""
        # Try persistent database first
        if HAS_DB_MANAGER:
            manager = cls._get_manager()
            if manager:
                data = manager.get_property(town, map_num, lot_num)
                if data:
                    logger.info(f"  ✓ Found in property database: {town} Map {map_num} Lot {lot_num}")
                    return data.copy()

        logger.debug(f"  No properties cached for {town} Map {map_num} Lot {lot_num}")
        return None

    @classmethod
    def add_property(cls, map_num: str, lot_num: str, town: str, data: Dict) -> None:
        """Add property to database. Town is required (no default)."""
        if HAS_DB_MANAGER:
            manager = cls._get_manager()
            if manager:
                manager.add_property(town, map_num, lot_num, data)
                logger.info(f"  ✓ Added to property database: {town} Map {map_num} Lot {lot_num}")

        key = (map_num, lot_num)
        cls.MAINE_PROPERTIES[town][key] = data
        logger.info(f"  ✓ Added to property database: {town} Map {map_num} Lot {lot_num}")


class PropertyEnrichmentEngine:
    """Main enrichment engine - orchestrates multiple data sources"""

    def __init__(self):
        self.sources_tried = []
        self.errors = []

    def enrich_property(self, form_data: Dict) -> Dict:
        """
        Enrich form submission with property data

        Input form_data should contain:
        - "Map and Lot # and Acreage": "26, 18, 2.35"
        - "Property Location Details": "17 Aspen Way, Turner, Maine 04282"

        Returns:
        {
            "map": "26",
            "lot": "18",
            "town": "Turner",
            "property_data": {...},
            "source": "Property Database",
            "confidence": "high",
            "used_for_drawings": True/False,
        }
        """
        # Extract identifiers from form
        identifiers = self._extract_identifiers(form_data)

        if not identifiers:
            logger.warning("Could not extract Map/Lot from form data")
            return {
                "status": "no_identifiers",
                "map": None,
                "lot": None,
                "property_data": None,
                "errors": self.errors,
            }

        map_num = identifiers["map"]
        lot_num = identifiers["lot"]
        town = identifiers["town"]

        logger.info(f"Enriching property: {town} Map {map_num} Lot {lot_num}")

        # Try sources in order
        self.sources_tried = []
        self.errors = []

        # Source 1: Property Database (cached research)
        logger.info("  [1/3] Checking property database...")
        property_data = PropertyDatabase.lookup(map_num, lot_num, town)
        if property_data:
            self.sources_tried.append("Property Database")
            return {
                "status": "found",
                "map": map_num,
                "lot": lot_num,
                "town": town,
                "property_data": property_data,
                "source": "Property Database",
                "confidence": property_data.get("confidence", "medium"),
                "used_for_drawings": True,
                "errors": self.errors,
            }

        # Source 2: Online queries (Maine GeoLibrary, O'Donnell CAMA, etc.)
        logger.info("  [2/3] Querying online sources...")
        online_data = self._query_online_sources(map_num, lot_num, town)
        if online_data:
            self.sources_tried.append("Online Sources")
            return {
                "status": "found",
                "map": map_num,
                "lot": lot_num,
                "town": town,
                "property_data": online_data,
                "source": "Online Sources",
                "confidence": "low",  # Online sources are less reliable
                "used_for_drawings": False,  # Don't use unless verified
                "errors": self.errors,
            }

        # Source 3: Form-provided data (future: extracted from uploaded documents)
        logger.info("  [3/3] Checking form data for enrichment info...")
        form_enrichment = self._extract_form_enrichment(form_data)
        if form_enrichment:
            self.sources_tried.append("Form Data")
            return {
                "status": "partial",
                "map": map_num,
                "lot": lot_num,
                "town": town,
                "property_data": form_enrichment,
                "source": "Form Data",
                "confidence": "medium",
                "used_for_drawings": False,  # Partial data only
                "errors": self.errors,
            }

        # No data found
        self.errors.append(
            f"Property not found in any source. Manual research needed."
        )
        return {
            "status": "not_found",
            "map": map_num,
            "lot": lot_num,
            "town": town,
            "property_data": None,
            "source": None,
            "confidence": None,
            "used_for_drawings": False,
            "errors": self.errors,
        }

    def _extract_identifiers(self, form_data: Dict) -> Optional[Dict]:
        """Extract Map, Lot, and Town from form data"""
        try:
            # Parse "Map and Lot # and Acreage" field: "26, 18, 2.35"
            map_lot_str = form_data.get("Map and Lot # and Acreage", "")
            if not map_lot_str:
                return None

            parts = [p.strip() for p in map_lot_str.split(",")]
            if len(parts) < 2:
                return None

            map_num = parts[0]
            lot_num = parts[1]
            acreage = parts[2] if len(parts) > 2 else None

            # Parse town from property location (e.g., "17 Aspen Way, Turner, Maine 04282")
            location = form_data.get("Property Location Details", "")
            town = self._extract_town_from_location(location)

            if not town:
                logger.warning(f"Could not extract town from location: {location}")
                return None

            return {
                "map": map_num,
                "lot": lot_num,
                "town": town,
                "acreage": acreage,
            }
        except Exception as e:
            logger.error(f"Error extracting identifiers: {e}")
            return None

    def _extract_town_from_location(self, location: str) -> Optional[str]:
        """
        Extract Maine town name from property location string

        Examples:
        - "17 Aspen Way, Turner, Maine 04282" -> "Turner"
        - "123 Main Street, Portland, ME 04101" -> "Portland"
        - "456 Road, Augusta, Maine" -> "Augusta"
        """
        if not location:
            return None

        # Split by comma and look for town between address and state/zip
        parts = [p.strip() for p in location.split(",")]

        # Format: address, town, state/zip
        # or: address, town (no state/zip)
        if len(parts) >= 2:
            # Town is typically the second-to-last part before state/zip
            # or the last part if only address and town provided
            potential_town = parts[-2] if len(parts) >= 3 else parts[-1]

            # Filter out state abbreviations/names and zip codes
            if potential_town.upper() not in ["ME", "MAINE", "MAINE."]:
                # Remove 'Maine' or 'Maine.' suffix if present
                potential_town = potential_town.replace("Maine.", "").replace("Maine", "").strip()

                # Check if it looks like a town name (not a zip code)
                if potential_town and not potential_town.isdigit():
                    return potential_town

        return None

    def _extract_form_enrichment(self, form_data: Dict) -> Optional[Dict]:
        """Extract property data from form fields"""
        try:
            data = {}

            # Location
            location = form_data.get("Property Location Details", "")
            if location:
                data["address"] = location

            # Acreage
            map_lot = form_data.get("Map and Lot # and Acreage", "")
            if "," in map_lot:
                parts = map_lot.split(",")
                if len(parts) > 2:
                    try:
                        data["acreage"] = float(parts[2].strip())
                    except ValueError:
                        pass

            # Soil data (implies site research was done)
            soil = form_data.get("Soil summary at disposal area", "")
            if soil:
                data["soil_profile"] = soil

            if data:
                return data
            return None
        except Exception as e:
            logger.error(f"Error extracting form enrichment: {e}")
            return None

    def _query_online_sources(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """Query online sources using Phase 3C enhanced researcher"""
        if not HAS_ENHANCED_RESEARCH:
            logger.debug("  Enhanced research module not available (phase 3C)")
            return None

        try:
            researcher = MainePropertyResearcherV2(timeout=15, throttle_delay=0.5)
            research_result = researcher.research_property(map_num, lot_num, town)

            if research_result:
                # Convert research results to enrichment format
                enriched = {
                    "road_name": research_result.get("road_information", {}).get("name"),
                    "road_type": research_result.get("road_information", {}).get("type"),
                    "road_frontage_ft": research_result.get("road_information", {}).get("frontage_ft"),
                    "property_boundary_vertices": research_result.get("property_boundary_vertices"),
                    "existing_structures": research_result.get("existing_structures"),
                    "owner": research_result.get("ownership", {}).get("name"),
                    "acreage": research_result.get("lot_dimensions", {}).get("area_acres"),
                }

                # Filter out None values
                enriched = {k: v for k, v in enriched.items() if v is not None}

                if enriched:
                    logger.info(f"    ✓ Online research found {len(enriched)} fields")
                    return enriched
                else:
                    logger.debug("    No enrichment data found from online sources")
                    return None
            else:
                return None

        except Exception as e:
            logger.warning(f"  Error querying online sources: {e}")
            return None


def format_enrichment_results(results: Dict) -> str:
    """Format enrichment results for display"""
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"Property Enrichment Results")
    output.append(f"{'='*60}")

    status = results.get("status", "unknown")
    output.append(f"Status: {status.upper()}")

    map_num = results.get("map")
    lot_num = results.get("lot")
    town = results.get("town")

    if map_num and lot_num:
        output.append(f"Property: {town}, Map {map_num} Lot {lot_num}")

    source = results.get("source")
    if source:
        output.append(f"Source: {source}")
        output.append(f"Confidence: {results.get('confidence', 'unknown').upper()}")

    used = results.get("used_for_drawings", False)
    output.append(f"Used for Drawings: {'YES ✓' if used else 'NO'}")

    prop_data = results.get("property_data", {})
    if prop_data:
        output.append(f"\nEnriched Data:")
        for key in ["address", "owner", "acreage", "road_name", "property_description"]:
            val = prop_data.get(key)
            if val:
                output.append(f"  {key}: {val}")

    errors = results.get("errors", [])
    if errors:
        output.append(f"\nNotes:")
        for err in errors:
            output.append(f"  ⚠ {err}")

    output.append(f"\n{'='*60}\n")
    return "\n".join(output)


def main():
    """Test the enrichment engine"""
    engine = PropertyEnrichmentEngine()

    # Test with form data matching the pipeline test case
    test_form = {
        "Map and Lot # and Acreage": "26, 18, 2.35",
        "Property Location Details": "17 Aspen Way, Turner, Maine 04282",
        "Soil summary at disposal area": "brown fine sandy loam to 3 inches, ...",
    }

    results = engine.enrich_property(test_form)

    print(format_enrichment_results(results))

    # Save results
    output_file = Path("enrichment_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
