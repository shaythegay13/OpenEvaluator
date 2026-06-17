#!/usr/bin/env python3
"""
O'Donnell CAMA System Web Scraper for Turner, Maine

Extracts property data from the John E. O'Donnell CAMA system web interface.
CAMA = Computer Assisted Mass Appraisal System

Data extracted:
- Owner name and address
- Property description
- Lot dimensions and acreage
- Assessed values
- Road/frontage information
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ODonnellCAMA:
    """Scrape property data from O'Donnell CAMA system - supports all Maine towns"""

    def __init__(self, town: str = "Turner"):
        """
        Initialize CAMA scraper for a specific Maine town

        Args:
            town: Maine town name (e.g., "Turner", "Auburn", "Portland")
                 Used to construct the CAMA URL dynamically
        """
        self.town = town.lower()
        self.base_url = f"https://jeodonnell.com/cama/{self.town}/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_property(self, map_num: str, lot_num: str) -> Optional[Dict]:
        """
        Search for property in O'Donnell CAMA system

        Args:
            map_num: Tax map number (e.g., "26")
            lot_num: Lot number (e.g., "18")

        Returns:
            Dictionary with property data or None if not found
        """
        try:
            # First, get the search form to understand the interface
            logger.info(f"Accessing O'Donnell CAMA system for Turner...")
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()

            # Parse the HTML to find search form and method
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try direct URL search (common pattern: ?account=MAPLOT or similar)
            # Common CAMA URL patterns for parcel search
            search_urls = [
                f"{self.base_url}?map={map_num}&lot={lot_num}",
                f"{self.base_url}?account={map_num}-{lot_num}",
                f"{self.base_url}?parcel={map_num}{lot_num}",
            ]

            for search_url in search_urls:
                logger.debug(f"  Trying: {search_url}")
                try:
                    search_response = self.session.get(search_url, timeout=10)
                    if search_response.status_code == 200:
                        logger.info(f"  ✓ Found property page")
                        return self._parse_property_data(search_response.content, map_num, lot_num)
                except Exception as e:
                    logger.debug(f"    Failed: {e}")
                    continue

            logger.warning(f"  Could not find property through direct URL search")
            return None

        except Exception as e:
            logger.error(f"  Error accessing O'Donnell CAMA: {e}")
            return None

    def _parse_property_data(self, html_content: bytes, map_num: str, lot_num: str) -> Dict:
        """Parse HTML response to extract property data"""
        soup = BeautifulSoup(html_content, 'html.parser')

        data = {
            "map_num": map_num,
            "lot_num": lot_num,
            "owner_name": None,
            "property_address": None,
            "property_description": None,
            "lot_dimensions": {},
            "acreage": None,
            "road_frontage": None,
            "assessed_value": None,
            "tax_class": None,
        }

        # Common property data locations in CAMA systems
        # Try multiple patterns as HTML structure can vary

        try:
            # Look for property owner information
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for i, row in enumerate(rows):
                    cols = row.find_all(['td', 'th'])
                    for j, col in enumerate(cols):
                        text = col.get_text(strip=True).lower()

                        # Owner name
                        if 'owner' in text and j + 1 < len(cols):
                            owner = cols[j + 1].get_text(strip=True)
                            if owner and len(owner) > 2:
                                data["owner_name"] = owner
                                logger.debug(f"    Owner: {owner}")

                        # Property address
                        if 'address' in text and j + 1 < len(cols):
                            addr = cols[j + 1].get_text(strip=True)
                            if addr:
                                data["property_address"] = addr
                                logger.debug(f"    Address: {addr}")

                        # Lot dimensions
                        if 'lot' in text and 'dimension' in text and j + 1 < len(cols):
                            dims = cols[j + 1].get_text(strip=True)
                            if dims:
                                data["lot_dimensions"]["dimensions"] = dims
                                logger.debug(f"    Lot dimensions: {dims}")

                        # Acreage
                        if 'acreage' in text or 'acres' in text:
                            if j + 1 < len(cols):
                                acreage = cols[j + 1].get_text(strip=True)
                                if acreage:
                                    data["acreage"] = acreage
                                    logger.debug(f"    Acreage: {acreage}")

                        # Road frontage
                        if 'frontage' in text or 'road' in text:
                            if j + 1 < len(cols):
                                frontage = cols[j + 1].get_text(strip=True)
                                if frontage:
                                    data["road_frontage"] = frontage
                                    logger.debug(f"    Frontage: {frontage}")

            # Extract all text and look for patterns
            all_text = soup.get_text()

            # Look for common patterns
            # Acreage pattern: "2.35 acres" or "2.35 ac"
            acreage_match = re.search(r'([\d.]+)\s*(?:acre|ac)', all_text, re.IGNORECASE)
            if acreage_match and not data["acreage"]:
                data["acreage"] = acreage_match.group(1)
                logger.debug(f"    Acreage (from text): {acreage_match.group(1)}")

            # Frontage pattern: "150 ft" or "150 feet"
            frontage_match = re.search(r'([\d.]+)\s*(?:ft|feet|front)', all_text, re.IGNORECASE)
            if frontage_match and not data["road_frontage"]:
                data["road_frontage"] = frontage_match.group(1)
                logger.debug(f"    Frontage (from text): {frontage_match.group(1)}")

            return data

        except Exception as e:
            logger.error(f"  Error parsing property data: {e}")
            return data


class ManualPropertyResearch:
    """Fallback: Manual research data for testing"""

    # Known properties in Turner that we have data for
    KNOWN_PROPERTIES = {
        ("26", "18"): {
            "map_num": "26",
            "lot_num": "18",
            "property_address": "17 Aspen Way, Turner, ME 04282",
            "owner_name": "George Bouchles",
            "acreage": "2.35",
            "road_frontage": "100+",
            "property_description": "Residential property with septic system",
            "lot_dimensions": {
                "area_acres": 2.35,
                "frontage_approx": "100+ feet",
            },
        }
    }

    @classmethod
    def get_property(cls, map_num: str, lot_num: str) -> Optional[Dict]:
        """Get manually-researched property data"""
        key = (map_num, lot_num)
        if key in cls.KNOWN_PROPERTIES:
            logger.info(f"  Using cached research data for Map {map_num} Lot {lot_num}")
            return cls.KNOWN_PROPERTIES[key]
        return None


def main():
    """Test the O'Donnell CAMA scraper"""
    scraper = ODonnellCAMA()

    # Try to scrape
    result = scraper.search_property("26", "18")

    if result:
        print("\n✓ Scraped property data:")
        for key, val in result.items():
            if val:
                print(f"  {key}: {val}")
    else:
        print("\n✗ Could not scrape property data")
        print("\nUsing manual fallback data:")
        manual_result = ManualPropertyResearch.get_property("26", "18")
        if manual_result:
            for key, val in manual_result.items():
                if val:
                    print(f"  {key}: {val}")


if __name__ == "__main__":
    main()
