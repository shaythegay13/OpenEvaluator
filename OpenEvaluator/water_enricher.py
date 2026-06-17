import json, urllib.request, urllib.parse
WETLANDS = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/Large_Wetlands/FeatureServer/1/query"
BASE = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/Maine_Parcels_Organized_Towns/FeatureServer/10/query"
NHD_WB = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/NHD_WB/FeatureServer/0/query"

from parcel_enricher import query_by_town_and_address

def find_wetlands_near(town, street, buffer_deg=0.01):
    parcels = query_by_town_and_address(town, street)
    if not parcels:
        return {"wetlands": 0}
    g = parcels[0].get("geometry", {})
    rings = g.get("rings", [])
    if not rings:
        return {"wetlands": 0}
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    env = f"{min_x-buffer_deg},{min_y-buffer_deg},{max_x+buffer_deg},{max_y+buffer_deg}"
    params = {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": "26919", "outFields": "CLASS,ACRES", "returnGeometry": "false", "f": "json"}
    qs = urllib.parse.urlencode(params)
    try:
        r = json.loads(urllib.request.urlopen(WETLANDS + "?" + qs, timeout=10).read())
        features = r.get("features", [])
        classes = []
        for f in features:
            c = f["attributes"].get("CLASS", "")
            if c and c not in classes:
                classes.append(c)
        return {"wetlands": len(features), "classes": classes}
    except:
        return {"wetlands": -1, "error": "query failed"}

def find_nearby_waterbodies(town, street, buffer_m=500):
    parcels = query_by_town_and_address(town, street)
    if not parcels:
        return {"waterbodies": 0}
    g = parcels[0].get("geometry", {})
    rings = g.get("rings", [])
    if not rings:
        return {"waterbodies": 0}
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    env = f"{cx-buffer_m},{cy-buffer_m},{cx+buffer_m},{cy+buffer_m}"
    params = {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": "26919", "outFields": "GNIS_NAME,FCODE", "returnGeometry": "false", "f": "json"}
    qs = urllib.parse.urlencode(params)
    try:
        r = json.loads(urllib.request.urlopen(NHD_WB + "?" + qs, timeout=10).read())
        features = r.get("features", [])
        names = [f["attributes"].get("GNIS_NAME","") or "Unnamed" for f in features[:10]]
        return {"waterbodies": len(features), "names": names}
    except:
        return {"waterbodies": -1, "error": "NHD query failed"}

if __name__ == "__main__":
    print(json.dumps(find_wetlands_near("Turner", "Aspen Way"), indent=2))
