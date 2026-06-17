#!/usr/bin/env python3
"""
Maine Property Research Module - Phase 3C Enhanced + Phase 5.2 WFS Integration

Robust web scraping with:
- Retry logic (exponential backoff)
- Timeout handling
- Request throttling
- Fallback sources
- Multi-town support (no hardcoding)
- WFS (Web Feature Service) support for better boundary extraction

Sources (priority order):
1. Maine GeoLibrary WFS (Web Feature Service) - Phase 5.2
2. Maine GeoLibrary ArcGIS REST API (parcel boundaries)
3. John E. O'Donnell CAMA System (assessor records - web scraping)
4. Fallback: Cached database lookups
"""

import logging
import requests
import json
import time
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as UrlRetry

# Try to import WFS client for Phase 5.2
try:
    from maine_geolibrary_wfs import MaineGeoLibraryWFS
    HAS_WFS = True
except ImportError:
    HAS_WFS = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainePropertyResearcherV2:
    """Enhanced Maine property researcher with robust error handling and WFS support"""

    def __init__(self, timeout: int = 15, throttle_delay: float = 0.5):
        """
        Initialize researcher with configurable timeouts and throttling

        Args:
            timeout: Request timeout in seconds (default 15)
            throttle_delay: Minimum delay between requests in seconds (default 0.5)
        """
        self.timeout = timeout
        self.throttle_delay = throttle_delay
        self.last_request_time = 0

        # Initialize WFS client if available (Phase 5.2)
        self.wfs_client = None
        if HAS_WFS:
            try:
                self.wfs_client = MaineGeoLibraryWFS(timeout=timeout, throttle_delay=throttle_delay)
                logger.info("  WFS client initialized for Phase 5.2 enhanced queries")
            except Exception as e:
                logger.debug(f"  Could not initialize WFS client: {e}")

        # Configure session with automatic retries
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()

        # Retry strategy: retry on connection errors, timeouts, and specific HTTP codes
        retry_strategy = UrlRetry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        return session

    def _throttle_request(self):
        """Enforce minimum delay between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.throttle_delay:
            time.sleep(self.throttle_delay - elapsed)
        self.last_request_time = time.time()

    def research_property(self, map_num: str, lot_num: str, town: str) -> Dict:
        """
        Research a property with robust error handling and fallbacks

        Args:
            map_num: Tax map number
            lot_num: Lot number
            town: Town name (Maine) - REQUIRED

        Returns:
            Dictionary with property data and sources
        """
        logger.info(f"Researching property: {town}, Map {map_num} Lot {lot_num}")

        result = {
            "map_num": map_num,
            "lot_num": lot_num,
            "town": town,
            "property_boundary": None,
            "property_boundary_vertices": None,
            "road_information": None,
            "lot_dimensions": None,
            "ownership": None,
            "tax_data": None,
            "existing_structures": None,
            "sources": [],
            "errors": [],
            "confidence": "low",
        }

        # Step 1: Query Maine GeoLibrary (most reliable for boundaries)
        logger.info("  [1/3] Querying Maine GeoLibrary for parcel boundary...")
        boundary = self._query_maine_geolibrary(map_num, lot_num, town)
        if boundary:
            result["property_boundary"] = boundary.get("geometry")
            result["property_boundary_vertices"] = self._extract_boundary_vertices(boundary)
            result["sources"].append("Maine GeoLibrary ArcGIS REST API")
            logger.info("    ✓ Parcel boundary found")
        else:
            logger.warning("    ⚠ Could not retrieve parcel boundary")

        # Step 2: Search O'Donnell CAMA (web scraping)
        logger.info("  [2/3] Searching O'Donnell CAMA for assessor records...")
        assessor_data = self._search_odonnell_cama_v2(map_num, lot_num, town)
        if assessor_data and assessor_data.get("success"):
            result["ownership"] = assessor_data.get("ownership")
            result["tax_data"] = assessor_data.get("tax_data")
            result["lot_dimensions"] = assessor_data.get("lot_dimensions")
            result["road_information"] = assessor_data.get("road_information")
            result["existing_structures"] = assessor_data.get("structures")
            result["sources"].append("John E. O'Donnell CAMA System")
            logger.info("    ✓ Assessor records found")
        else:
            logger.warning("    ⚠ Could not retrieve assessor records")

        # Step 3: Fallback: Check property database cache
        logger.info("  [3/3] Checking property database cache...")
        from property_enrichment_engine import PropertyDatabase
        cached_data = PropertyDatabase.lookup(map_num, lot_num, town)
        if cached_data and not result["road_information"]:
            result["road_information"] = {
                "name": cached_data.get("road_name"),
                "type": cached_data.get("road_type"),
                "frontage_ft": cached_data.get("road_frontage_ft"),
            }
            result["existing_structures"] = cached_data.get("existing_structures")
            result["sources"].append("Local Property Database Cache")
            logger.info("    ✓ Cache hit")

        # Calculate confidence based on data completeness
        completeness = self._calculate_confidence(result)
        result["confidence"] = completeness

        logger.info(f"  ✓ Research complete. Sources: {len(result['sources'])}, Confidence: {completeness}")
        if result["errors"]:
            logger.warning(f"  ⚠ Warnings: {len(result['errors'])}")

        return result

    def _query_maine_geolibrary(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Query Maine GeoLibrary for parcel boundary with proper error handling

        Phase 5.2 Enhancement: Uses WFS (Web Feature Service) first for better
        boundary extraction, then falls back to REST API if WFS unavailable.

        Sources (priority):
        1. WFS - Better for complex geometries, more reliable
        2. REST API - Fallback if WFS unavailable
        """
        # Try WFS first (Phase 5.2)
        if self.wfs_client:
            try:
                logger.debug(f"  Querying WFS for parcel boundary...")
                wfs_result = self.wfs_client.query_by_map_lot(map_num, lot_num, town)
                if wfs_result:
                    logger.debug(f"    ✓ WFS query successful")
                    # Merge WFS result with consistent response structure
                    return {
                        "geometry": wfs_result.get("geometry", {}),
                        "attributes": wfs_result.get("attributes", {}),
                        "boundary_vertices": wfs_result.get("boundary_vertices"),
                        "source": "WFS",
                        "found": True,
                    }
            except Exception as e:
                logger.debug(f"    WFS query failed: {e}")

        # Fallback to REST API
        try:
            logger.debug(f"  Querying REST API for parcel boundary...")
            self._throttle_request()

            service_url = "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Organized_Towns/MapServer/0/query"

            # Try exact match first
            where_clause = f"MAP = '{map_num}' AND LOT = '{lot_num}'"

            params = {
                "where": where_clause,
                "outSR": '{"wkid":4326}',
                "outFields": "*",
                "f": "json",
                "returnGeometry": "true",
            }

            logger.debug(f"    Query: {where_clause}")

            response = self.session.get(service_url, params=params, timeout=self.timeout)

            # Handle HTTP errors
            if response.status_code != 200:
                logger.debug(f"    REST API returned status {response.status_code}")
                return None

            data = response.json()

            if "error" in data:
                logger.debug(f"    REST API error: {data['error'].get('message', 'Unknown error')}")
                return None

            if "features" in data and len(data["features"]) > 0:
                feature = data["features"][0]
                geometry = feature.get("geometry", {})
                attributes = feature.get("attributes", {})

                logger.debug(f"    ✓ REST API query successful")

                return {
                    "geometry": geometry,
                    "attributes": attributes,
                    "source": "REST_API",
                    "found": True,
                }
            else:
                logger.debug(f"    No features found in REST API")
                return None

        except requests.Timeout:
            logger.debug(f"  REST API request timeout (>{self.timeout}s)")
            return None
        except requests.ConnectionError as e:
            logger.debug(f"  REST API connection error: {e}")
            return None
        except Exception as e:
            logger.debug(f"  REST API error: {e}")
            return None

    def _search_odonnell_cama_v2(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Enhanced O'Donnell CAMA web scraping with robust error handling

        O'Donnell CAMA: https://jeodonnell.com/cama/{town}/
        """
        try:
            self._throttle_request()

            cama_base = f"https://jeodonnell.com/cama/{town.lower()}/"
            search_url = f"{cama_base}?map={map_num}&lot={lot_num}"

            logger.debug(f"  CAMA request: {search_url}")

            response = self.session.get(search_url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            # Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for property data in the page (implementation depends on CAMA structure)
            result = self._parse_cama_response(soup, map_num, lot_num, town)

            if result:
                result["success"] = True
                return result
            else:
                logger.debug(f"  CAMA: No data found for Map {map_num} Lot {lot_num}")
                return {"success": False}

        except requests.Timeout:
            logger.warning(f"  CAMA request timeout (>{self.timeout}s)")
            return {"success": False}
        except requests.ConnectionError:
            logger.warning(f"  CAMA connection error (may be down)")
            return {"success": False}
        except Exception as e:
            logger.warning(f"  CAMA scraping error: {e}")
            return {"success": False}

    def _parse_cama_response(self, soup: BeautifulSoup, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Parse HTML response from O'Donnell CAMA with multiple parsing strategies

        O'Donnell CAMA varies by town. This parser uses multiple strategies:
        1. Look for table rows with property data
        2. Look for definition lists (dt/dd elements)
        3. Look for key-value pairs in common formats
        """
        try:
            result = {
                "ownership": {},
                "tax_data": {},
                "lot_dimensions": {},
                "road_information": {},
                "structures": [],
            }

            # Strategy 1: Look for table data
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if 'owner' in label:
                            result["ownership"]["name"] = value
                        elif 'street' in label or 'road' in label or 'address' in label:
                            result["road_information"]["name"] = value
                        elif 'acre' in label or 'size' in label:
                            try:
                                result["lot_dimensions"]["area_acres"] = float(value.split()[0])
                            except (ValueError, IndexError):
                                pass

            # Strategy 2: Look for definition lists
            for dt in soup.find_all('dt'):
                label = dt.get_text(strip=True).lower()
                dd = dt.find_next('dd')
                if dd:
                    value = dd.get_text(strip=True)

                    if 'owner' in label:
                        result["ownership"]["name"] = value
                    elif 'street' in label or 'road' in label:
                        result["road_information"]["name"] = value
                    elif 'acre' in label:
                        try:
                            result["lot_dimensions"]["area_acres"] = float(value.split()[0])
                        except (ValueError, IndexError):
                            pass

            # Strategy 3: Look for paragraphs with property data
            for text_node in soup.find_all(string=True):
                text = text_node.strip()
                if not text or len(text) < 5:
                    continue

                # Look for patterns like "Owner: John Doe" or "Road: Aspen Way"
                if ':' in text:
                    try:
                        label, value = text.split(':', 1)
                        label = label.strip().lower()
                        value = value.strip()

                        if value and label:
                            if 'owner' in label:
                                result["ownership"]["name"] = value
                            elif 'street' in label or 'road' in label:
                                result["road_information"]["name"] = value
                            elif 'acre' in label:
                                try:
                                    result["lot_dimensions"]["area_acres"] = float(value.split()[0])
                                except (ValueError, IndexError):
                                    pass
                    except (ValueError, AttributeError):
                        pass

            # If we found any data, return it; otherwise return None
            found_data = any(
                v for v in result.values()
                if isinstance(v, dict) and v
            )

            return result if found_data else None

        except Exception as e:
            logger.debug(f"  CAMA parsing error: {e}")
            return None

    def _extract_boundary_vertices(self, boundary: Dict) -> Optional[List[List[float]]]:
        """Extract coordinate vertices from GIS boundary geometry"""
        try:
            geometry = boundary.get("geometry", {})

            if "rings" in geometry and len(geometry["rings"]) > 0:
                # Use the first ring (outer boundary)
                ring = geometry["rings"][0]
                # Convert from [x, y] to [[x1, y1], [x2, y2], ...]
                vertices = [[point[0], point[1]] for point in ring]
                return vertices if vertices else None
            else:
                return None

        except Exception as e:
            logger.debug(f"  Error extracting boundary vertices: {e}")
            return None

    def _calculate_confidence(self, result: Dict) -> str:
        """Calculate overall confidence in research results"""
        data_fields = [
            result.get("property_boundary"),
            result.get("ownership"),
            result.get("road_information"),
            result.get("lot_dimensions"),
        ]

        filled_fields = sum(1 for field in data_fields if field)

        if filled_fields == 4:
            return "high"
        elif filled_fields >= 2:
            return "medium"
        elif filled_fields >= 1:
            return "low"
        else:
            return "none"


def main():
    """Test the enhanced property researcher"""
    researcher = MainePropertyResearcherV2(timeout=15, throttle_delay=0.5)

    # Test with Turner property
    results = researcher.research_property(map_num="26", lot_num="18", town="Turner")

    print("\n" + "="*70)
    print("Property Research Results (Phase 3C Enhanced)")
    print("="*70)
    print(f"Property: {results['town']}, Map {results['map_num']} Lot {results['lot_num']}")
    print(f"Confidence: {results['confidence']}")
    print(f"Sources: {', '.join(results['sources'])}")

    if results["property_boundary_vertices"]:
        print(f"\n✓ Boundary vertices: {len(results['property_boundary_vertices'])} points")

    if results["road_information"]:
        print(f"\n✓ Road: {results['road_information']}")

    if results["lot_dimensions"]:
        print(f"\n✓ Dimensions: {results['lot_dimensions']}")

    if results["ownership"]:
        print(f"\n✓ Owner: {results['ownership']}")

    if results["errors"]:
        print(f"\n⚠ Warnings: {results['errors']}")

    print("\n" + "="*70 + "\n")

    # Save to JSON
    output_file = Path("property_research_results_v2.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
