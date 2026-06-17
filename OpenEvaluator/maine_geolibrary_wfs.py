#!/usr/bin/env python3
"""
Maine GeoLibrary WFS Client - Phase 5.2

Web Feature Service (WFS) integration for Maine parcel queries.
WFS provides more reliable geographic data queries than REST APIs.

WFS Endpoints:
- Maine GeoLibrary WFS: https://gis.maine.gov/arcgis/services/mrs/WFS/...
- Service: Maine_Parcels_Organized_Towns

Features:
- Query by MAP and LOT (tax identifiers)
- Query by location (coordinates)
- Extract boundary coordinates as vertex list
- Comprehensive error handling
- Automatic fallback to REST API
"""

import logging
import requests
import json
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MaineGeoLibraryWFS:
    """Query Maine GeoLibrary using Web Feature Service (WFS) protocol"""

    def __init__(self, timeout: int = 15, throttle_delay: float = 0.5):
        """
        Initialize WFS client

        Args:
            timeout: Request timeout in seconds (default 15)
            throttle_delay: Minimum delay between requests in seconds (default 0.5)
        """
        self.timeout = timeout
        self.throttle_delay = throttle_delay
        self.last_request_time = 0

        # Maine GeoLibrary WFS endpoints
        self.wfs_url = "https://gis.maine.gov/arcgis/services/mrs/Maine_Parcels_Organized_Towns/MapServer/WFSServer"

        # Fallback to REST API if WFS fails
        self.rest_url = "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Organized_Towns/MapServer/0/query"

        # Session with retries
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        from urllib3.util.retry import Retry as UrlRetry
        from requests.adapters import HTTPAdapter

        session = requests.Session()

        retry_strategy = UrlRetry(
            total=3,
            backoff_factor=1,
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

    def query_by_map_lot(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Query Maine GeoLibrary for parcel by MAP and LOT

        Args:
            map_num: Tax map number
            lot_num: Lot number
            town: Town name (for context/logging)

        Returns:
            Dictionary with parcel geometry, attributes, and boundary vertices
            or None if not found
        """
        logger.info(f"Querying WFS for {town} Map {map_num} Lot {lot_num}")

        # Try WFS first
        result = self._query_wfs_by_map_lot(map_num, lot_num, town)
        if result:
            logger.info(f"  ✓ WFS query successful")
            return result

        # Fallback to REST API
        logger.info(f"  ⚠ WFS failed, falling back to REST API")
        result = self._query_rest_api_by_map_lot(map_num, lot_num, town)
        if result:
            logger.info(f"  ✓ REST API query successful")
            return result

        logger.warning(f"  ✗ Could not find parcel in either WFS or REST API")
        return None

    def _query_wfs_by_map_lot(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Query Maine GeoLibrary WFS by MAP and LOT

        WFS Request: GetFeature with CQL_FILTER for Map/Lot

        NOTE: As of 2026-06-17, Maine GeoLibrary WFS service may be unavailable.
        Falls back to REST API automatically when WFS fails.
        """
        try:
            self._throttle_request()

            # WFS GetFeature request with CQL filter
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "Maine_Parcels_Organized_Towns",
                "CQL_FILTER": f"MAP = '{map_num}' AND LOT = '{lot_num}'",
                "outputFormat": "application/json",
                "srsName": "EPSG:4326",
            }

            url = f"{self.wfs_url}?{urlencode(params)}"
            logger.debug(f"  WFS request: {url[:100]}...")

            response = self.session.get(url, timeout=self.timeout)

            # Check for HTTP errors (404, 500, etc.)
            if response.status_code != 200:
                logger.debug(f"  WFS HTTP {response.status_code}")
                return None

            data = response.json()

            # Check for WFS-specific errors
            if "error" in data or "ows:ExceptionReport" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.debug(f"  WFS error: {error_msg}")
                return None

            # Extract features
            if "features" in data and len(data["features"]) > 0:
                feature = data["features"][0]
                geometry = feature.get("geometry", {})
                attributes = feature.get("properties", {})

                # Extract boundary coordinates
                boundary_vertices = self._extract_boundary_vertices(geometry)

                return {
                    "source": "WFS",
                    "geometry": geometry,
                    "attributes": attributes,
                    "boundary_vertices": boundary_vertices,
                    "type": geometry.get("type"),
                    "found": True,
                }
            else:
                logger.debug(f"  WFS: No features found")
                return None

        except requests.Timeout:
            logger.debug(f"  WFS request timeout")
            return None
        except requests.ConnectionError as e:
            logger.debug(f"  WFS connection error: {e}")
            return None
        except json.JSONDecodeError:
            logger.debug(f"  WFS invalid JSON response")
            return None
        except Exception as e:
            logger.debug(f"  WFS query error: {e}")
            return None

    def _query_rest_api_by_map_lot(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Fallback: Query Maine GeoLibrary REST API by MAP and LOT

        Used if WFS is unavailable
        """
        try:
            self._throttle_request()

            params = {
                "where": f"MAP = '{map_num}' AND LOT = '{lot_num}'",
                "outSR": '{"wkid":4326}',
                "outFields": "*",
                "f": "json",
                "returnGeometry": "true",
            }

            logger.debug(f"  REST API fallback request")

            response = self.session.get(self.rest_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                logger.debug(f"  REST API error: {data['error'].get('message')}")
                return None

            if "features" in data and len(data["features"]) > 0:
                feature = data["features"][0]
                geometry = feature.get("geometry", {})
                attributes = feature.get("attributes", {})

                # Extract boundary coordinates
                boundary_vertices = self._extract_boundary_vertices(geometry)

                return {
                    "source": "REST_API",
                    "geometry": geometry,
                    "attributes": attributes,
                    "boundary_vertices": boundary_vertices,
                    "type": geometry.get("type"),
                    "found": True,
                }
            else:
                logger.debug(f"  REST API: No features found")
                return None

        except Exception as e:
            logger.debug(f"  REST API error: {e}")
            return None

    def _extract_boundary_vertices(self, geometry: Dict) -> Optional[List[Tuple[float, float]]]:
        """
        Extract boundary coordinates from geometry object

        Supports:
        - Polygon: exterior ring only
        - MultiPolygon: largest polygon
        - Point: None (point geometry)

        Returns: List of (longitude, latitude) tuples
        """
        try:
            geom_type = geometry.get("type", "").lower()

            if geom_type == "polygon":
                coords = geometry.get("coordinates", [])
                if coords and len(coords) > 0:
                    # First array is exterior ring
                    return [(lon, lat) for lon, lat in coords[0]]

            elif geom_type == "multipolygon":
                coords = geometry.get("coordinates", [])
                if coords and len(coords) > 0:
                    # Find largest polygon (usually the main parcel boundary)
                    largest_polygon = max(coords, key=lambda p: len(p[0]) if p else 0)
                    if largest_polygon:
                        return [(lon, lat) for lon, lat in largest_polygon[0]]

            elif geom_type == "point":
                logger.debug(f"  Point geometry - no boundary vertices")
                return None

            return None

        except Exception as e:
            logger.debug(f"  Error extracting boundary vertices: {e}")
            return None

    def get_parcel_attributes(self, map_num: str, lot_num: str, town: str) -> Optional[Dict]:
        """
        Get parcel attributes (owner, acreage, etc.)

        Returns dictionary with:
        - MAP: Tax map number
        - LOT: Lot number
        - ACRES: Acreage
        - OWNER: Owner name (if available)
        - ADDRESS: Property address (if available)
        """
        result = self.query_by_map_lot(map_num, lot_num, town)
        if not result:
            return None

        attributes = result.get("attributes", {})

        return {
            "map": attributes.get("MAP"),
            "lot": attributes.get("LOT"),
            "acres": attributes.get("ACRES"),
            "owner": attributes.get("OWNER"),
            "address": attributes.get("ADDRESS"),
            "town": attributes.get("TOWN"),
            "all_attributes": attributes,
        }

    def normalize_boundary_for_drawing(
        self,
        vertices: Optional[List[Tuple[float, float]]],
        target_width: float = 1000.0,
        target_height: float = 800.0
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Normalize boundary coordinates for drawing (scale + translate to fit canvas)

        Args:
            vertices: List of (longitude, latitude) coordinates
            target_width: Canvas width in pixels
            target_height: Canvas height in pixels

        Returns:
            List of (x, y) pixel coordinates normalized to canvas
        """
        if not vertices or len(vertices) < 3:
            return None

        try:
            # Find bounds
            lons = [v[0] for v in vertices]
            lats = [v[1] for v in vertices]

            min_lon, max_lon = min(lons), max(lons)
            min_lat, max_lat = min(lats), max(lats)

            # Calculate scale to fit in canvas with padding
            padding = 0.05
            width_degrees = max_lon - min_lon or 0.001
            height_degrees = max_lat - min_lat or 0.001

            # Aspect ratio compensation (latitude degrees are smaller than longitude)
            lat_correction = 0.7  # Approximate latitude/longitude ratio in pixels

            scale_x = (target_width * (1 - 2 * padding)) / width_degrees
            scale_y = (target_height * (1 - 2 * padding)) / (height_degrees * lat_correction)

            # Use smaller scale to maintain aspect ratio
            scale = min(scale_x, scale_y)

            # Translate to center
            center_lon = (min_lon + max_lon) / 2
            center_lat = (min_lat + max_lat) / 2

            canvas_center_x = target_width / 2
            canvas_center_y = target_height / 2

            # Normalize coordinates
            normalized = []
            for lon, lat in vertices:
                x = canvas_center_x + (lon - center_lon) * scale
                y = canvas_center_y - (lat - center_lat) * scale * lat_correction
                normalized.append((round(x, 2), round(y, 2)))

            logger.debug(f"  Normalized {len(vertices)} boundary vertices to canvas coordinates")
            return normalized

        except Exception as e:
            logger.error(f"  Error normalizing boundary: {e}")
            return None


def main():
    """Test WFS client"""
    wfs = MaineGeoLibraryWFS()

    # Test case: Turner Map 26 Lot 18
    print("\n" + "=" * 60)
    print("Maine GeoLibrary WFS Test")
    print("=" * 60)

    result = wfs.query_by_map_lot("26", "18", "Turner")

    if result:
        print(f"\n✓ Query successful (source: {result.get('source')})")
        print(f"  Type: {result.get('type')}")

        attrs = result.get("attributes", {})
        print(f"\nParcel Attributes:")
        for key in ["MAP", "LOT", "ACRES", "OWNER", "ADDRESS"]:
            if key in attrs:
                print(f"  {key}: {attrs[key]}")

        vertices = result.get("boundary_vertices")
        if vertices:
            print(f"\nBoundary Vertices: {len(vertices)} points")
            print(f"  First 3 points: {vertices[:3]}")

            # Test normalization
            normalized = wfs.normalize_boundary_for_drawing(vertices)
            if normalized:
                print(f"\nNormalized to canvas (1000×800):")
                print(f"  First 3 points: {normalized[:3]}")
        else:
            print("\nNo boundary vertices found")
    else:
        print("\n✗ Query failed")


if __name__ == "__main__":
    main()
