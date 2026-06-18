import json
import urllib.request
import urllib.parse
import re
from typing import Optional, Dict, Any

BASE = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/Maine_Parcels_Organized_Towns/FeatureServer/10/query"

def query_by_town_and_address(town: str, street: str) -> list:
    """Find parcels matching town and street name."""
    where = f"TOWN='{town.replace(chr(39), chr(39)+chr(39))}' AND PROP_LOC LIKE '%{street.upper().strip()}%'"
    params = {"where": where, "outFields": "MAP_BK_LOT,PROP_LOC,TOWN,COUNTY,STATE_ID,Shape__Area,Shape__Length,GEOCODE", "returnGeometry": "true", "f": "json"}
    qs = urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(BASE + "?" + qs, timeout=10) as r:
            return json.loads(r.read()).get("features", [])
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_parcel_dimensions(town: str, address: str, acres: Optional[float] = None) -> Dict[str, Any]:
    """Get parcel boundary rings and corner/pin coordinates from Maine GeoLibrary."""
    # Extract street name from address (e.g., "17 Aspen Way" → "Aspen Way")
    # GeoLibrary stores PROP_LOC as "00XXX STREET NAME", so we need to search by street name only
    import re
    street_match = re.search(r'([A-Za-z\s]+(?:Way|Road|Street|Lane|Drive|Court|Avenue|Terrace))', address, re.IGNORECASE)
    search_address = street_match.group(0) if street_match else address

    features = query_by_town_and_address(town, search_address)
    if not features:
        return {}
    # Score parcels by acreage match to find the right one
    scored = []
    for f in features:
        a = f["attributes"]
        area_ac = round(a["Shape__Area"] * 0.000247105, 2)
        score = 0
        if acres and abs(area_ac - acres) < 0.5:
            score += 10 - abs(area_ac - acres) * 10
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    a = best["attributes"]
    g = best.get("geometry", {})
    rings = g.get("rings", [])
    if not rings:
        return {"found": True, "error": "no geometry"}

    # Extract corner/pin coordinates from exterior ring (first ring)
    exterior_ring = rings[0]
    corners = exterior_ring

    # Compute bounding box dimensions for backward compatibility
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    w_m = max(xs) - min(xs)
    d_m = max(ys) - min(ys)

    return {
        "found": True,
        "map_bk_lot": a["MAP_BK_LOT"],
        "prop_loc": a["PROP_LOC"],
        "rings": rings,
        "corners": corners,
        "width_ft": round(w_m * 3.28084),
        "depth_ft": round(d_m * 3.28084),
        "area_sqm": round(a["Shape__Area"], 1),
        "area_ac": round(a["Shape__Area"] * 0.000247105, 2),
        "parcels_nearby": len(features)
    }
