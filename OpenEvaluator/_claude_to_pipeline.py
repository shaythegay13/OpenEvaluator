#!/usr/bin/env python3
"""Convert Claude output to pipeline format and run."""
import json, os, sys
sys.path.insert(0, '.')

# Load Claude output 
claude = json.load(open('claude_output.json'))

# Build pipeline-compatible structure
pipeline_data = {
    "metadata": {"source": "claude_opus_4_8", "date": "2026-06-16"},
    "site_evaluator": {"name": "", "license_number": "", "phone": "", "email": "", "company": ""},
    "client": {"name": (claude.get("map_lot") or "").split(",")[0].strip() if claude.get("map_lot") else ""},
    "property": {"address": "", "map_number": "", "lot_number": "", "acreage": 0},
    "water_supply": {"type": "", "well": {}},
    "septic_system": {"tank": {}, "disposal_field": {}},
    "soil_observations": {"soil_type": "", "groundwater_depth_in": 0},
    "observation_holes": [],
    "elevation_data": {"reference_point": {}, "limiting_factor": {}, "finished_grade_in": 0}
}

# Extract map/lot info
ml = claude.get("map_lot", "")
if ml:
    parts = ml.replace("Map", "").replace("Lot", "").split()
    for i, p in enumerate(parts):
        if p.isdigit():
            pipeline_data["property"]["map_number"] = parts[i-1] if i > 0 and not parts[i-1].isdigit() else ""
            pipeline_data["property"]["lot_number"] = p

# Elevations
elev = claude.get("elevations", {})
if elev.get("erp"):
    pipeline_data["elevation_data"]["reference_point"]["description"] = elev["erp"]
if elev.get("limiting_factor_depth"):
    pipeline_data["elevation_data"]["limiting_factor"]["depth_in"] = int(elev["limiting_factor_depth"])
    pipeline_data["soil_observations"]["groundwater_depth_in"] = int(elev["limiting_factor_depth"])

# Field system
fs = claude.get("field_system", {})
if fs.get("brand"):
    pipeline_data["septic_system"]["disposal_field"]["brand"] = fs["brand"]
if fs.get("rows"):
    pipeline_data["septic_system"]["disposal_field"]["rows"] = int(fs["rows"])
if fs.get("modules"):
    pipeline_data["septic_system"]["disposal_field"]["modules_per_row"] = int(fs["modules"])

# Tank
tank = claude.get("tank", {})
if tank.get("capacity_gallons"):
    pipeline_data["septic_system"]["tank"]["capacity_gallons"] = int(tank["capacity_gallons"])

# Well
well = claude.get("well", {})
if well.get("type"):
    pipeline_data["water_supply"]["type"] = well["type"]
    pipeline_data["water_supply"]["well"]["type"] = well["type"]

# Soil observations
soil = claude.get("soil_observations", [])
if soil and len(soil) > 0:
    s = soil[0]
    pipeline_data["soil_observations"]["soil_type"] = s.get("texture", "") + " " + s.get("color", "")
    if s.get("depth"):
        pipeline_data["soil_observations"]["depth_in"] = s["depth"]

# Save to hermes_output.json
with open('hermes_output.json', 'w') as f:
    json.dump(pipeline_data, f, indent=2)

print("hermes_output.json written with Claude data")

# Run pipeline
import run_pipeline_with_hermes_complete
