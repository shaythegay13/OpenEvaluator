import json, urllib.request, urllib.parse
from parcel_enricher import query_by_town_and_address

ROAD_URL = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/Addresses/FeatureServer/1/query"
KNOWN_CLASSES = {"I": "Interstate", "R": "State Route", "SR": "State Route", "L": "Local", "C": "Collector", "P": "Private", "M": "Major", "A": "Arterial"}

def get_road_info(town: str) -> dict:
    """Get road name and class for town."""
    params = {"where": f"TOWN='{town}'", "outFields": "STREETNAME,SUFFIX,RDCLASS,RDNAME", "f": "json", "resultRecordCount": "200"}
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(ROAD_URL + "?" + qs, timeout=10) as r:
        data = json.loads(r.read())
    roads = list(set(f["attributes"].get("RDNAME", f["attributes"].get("STREETNAME", "") or "") for f in data.get("features", []) if f["attributes"].get("RDNAME") or f["attributes"].get("STREETNAME")))
    return {"town": town, "roads": roads, "count": len(roads)}

def query_roads_by_town(town: str) -> list:
    """Query all roads in a town from E911 road network."""
    params = {"where": f"TOWN='{town}'", "outFields": "STREETNAME,SUFFIX,RDCLASS", "f": "json", "resultRecordCount": "500"}
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(ROAD_URL + "?" + qs, timeout=10) as r:
        data = json.loads(r.read())
    return data.get("features", [])
