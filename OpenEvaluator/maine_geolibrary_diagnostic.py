#!/usr/bin/env python3
"""
Maine GeoLibrary Diagnostic Tool

Helps identify:
1. Available WFS endpoints
2. Layer/feature type names
3. Available fields in each layer
4. Sample queries to test
"""

import requests
import json
import logging
from typing import Dict, List
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MaineGeoLibraryDiagnostic:
    """Diagnostic tool for Maine GeoLibrary exploration"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def test_rest_api_endpoint(self) -> bool:
        """Test if REST API endpoint is accessible"""
        print("\n" + "=" * 60)
        print("Testing REST API Endpoint")
        print("=" * 60)

        rest_url = "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Organized_Towns/MapServer"

        try:
            response = self.session.get(f"{rest_url}?f=json", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ REST API endpoint is accessible")
                print(f"  Service name: {data.get('name', 'N/A')}")
                print(f"  Layers: {[l.get('name') for l in data.get('layers', [])]}")
                return True
            else:
                print(f"✗ REST API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ REST API error: {e}")
            return False

    def test_wfs_getcapabilities(self) -> Dict:
        """Test WFS GetCapabilities request"""
        print("\n" + "=" * 60)
        print("Testing WFS GetCapabilities")
        print("=" * 60)

        # Try multiple WFS endpoint patterns
        wfs_patterns = [
            "https://gis.maine.gov/arcgis/services/mrs/Maine_Parcels_Organized_Towns/MapServer/WFSServer",
            "https://gis.maine.gov/arcgis/services/mrs/WFS/MapServer/WFSServer",
            "https://gis.maine.gov/geoserver/wfs",
        ]

        for wfs_url in wfs_patterns:
            try:
                print(f"\nTrying: {wfs_url}")
                params = {
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetCapabilities",
                }

                response = self.session.get(f"{wfs_url}?{urlencode(params)}", timeout=self.timeout)

                if response.status_code == 200:
                    print(f"✓ WFS endpoint is accessible")

                    # Check if response is valid XML
                    if "wfs:" in response.text or "FeatureType" in response.text:
                        print(f"  Response contains WFS feature types")

                        # Extract feature type names
                        import xml.etree.ElementTree as ET
                        try:
                            root = ET.fromstring(response.text)
                            # Look for FeatureType elements
                            for elem in root.iter():
                                if "FeatureType" in elem.tag or "Name" in elem.tag:
                                    if elem.text and elem.text.strip():
                                        print(f"    - {elem.text.strip()}")
                        except:
                            pass

                        return {"endpoint": wfs_url, "accessible": True}
                    else:
                        print(f"  Response doesn't contain WFS feature types")

            except Exception as e:
                print(f"  Error: {e}")

        return {"accessible": False}

    def test_rest_api_query_sample(self) -> None:
        """Test a sample REST API query to understand response structure"""
        print("\n" + "=" * 60)
        print("Testing REST API Query (Sample)")
        print("=" * 60)

        rest_url = "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Organized_Towns/MapServer/0/query"

        # Try a simple query with no where clause to get first feature
        params = {
            "where": "1=1",  # Get any feature
            "outFields": "*",
            "f": "json",
            "returnGeometry": "true",
            "resultRecordCount": "1",
        }

        try:
            print(f"Query URL: {rest_url}")
            response = self.session.get(rest_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                if "features" in data and len(data["features"]) > 0:
                    feature = data["features"][0]
                    attributes = feature.get("attributes", {})

                    print(f"✓ Sample feature retrieved")
                    print(f"\nAvailable attributes:")
                    for key in sorted(attributes.keys()):
                        value = attributes[key]
                        if isinstance(value, (int, float)):
                            print(f"  {key}: {value}")
                        else:
                            value_str = str(value)[:50]
                            print(f"  {key}: {value_str}")
                else:
                    print(f"✗ No features returned")

            else:
                print(f"✗ Query returned status {response.status_code}")
                print(f"  Response: {response.text[:200]}")

        except Exception as e:
            print(f"✗ Query error: {e}")

    def test_specific_property_lookup(self, map_num: str, lot_num: str) -> None:
        """Test looking up a specific property"""
        print("\n" + "=" * 60)
        print(f"Testing Property Lookup: Map {map_num} Lot {lot_num}")
        print("=" * 60)

        rest_url = "https://gis.maine.gov/arcgis/rest/services/mrs/Maine_Parcels_Organized_Towns/MapServer/0/query"

        # Try different field name combinations
        queries = [
            f"MAP = '{map_num}' AND LOT = '{lot_num}'",
            f"map = '{map_num}' AND lot = '{lot_num}'",
            f"Map = '{map_num}' AND Lot = '{lot_num}'",
        ]

        for where_clause in queries:
            try:
                print(f"\nTrying: {where_clause}")
                params = {
                    "where": where_clause,
                    "outFields": "*",
                    "f": "json",
                    "returnGeometry": "true",
                }

                response = self.session.get(rest_url, params=params, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()

                    if "features" in data:
                        if len(data["features"]) > 0:
                            print(f"✓ Found {len(data['features'])} feature(s)")

                            feature = data["features"][0]
                            attrs = feature.get("attributes", {})
                            print(f"  Property found:")
                            for key in ["MAP", "LOT", "ACRES", "OWNER"]:
                                if key in attrs:
                                    print(f"    {key}: {attrs[key]}")
                            return
                        else:
                            print(f"  No features found with this query")
                    else:
                        print(f"  Error: {data}")
                else:
                    print(f"  Status {response.status_code}")

            except Exception as e:
                print(f"  Error: {e}")

        print(f"\n✗ Could not find property with any query variation")


def main():
    """Run diagnostics"""
    print("\nMAINE GEOLIBRARY DIAGNOSTIC TOOL")
    print("=" * 60)

    diag = MaineGeoLibraryDiagnostic()

    # Run tests
    diag.test_rest_api_endpoint()
    diag.test_wfs_getcapabilities()
    diag.test_rest_api_query_sample()
    diag.test_specific_property_lookup("26", "18")

    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
