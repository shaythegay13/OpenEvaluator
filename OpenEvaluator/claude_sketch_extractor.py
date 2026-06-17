#!/usr/bin/env python3
"""Sketch extraction using Claude Opus 4.8 (replaces Google Cloud Vision)."""
import os, json, sys, base64, io, re
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def extract_sketch_with_claude(filepath: str) -> dict:
    """Extract structured data from sketch using Claude Opus 4.8."""
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        return {}
    
    # Convert to image
    logger.info(f"Converting {Path(filepath).name} to image...")
    try:
        if filepath.lower().endswith('.pdf'):
            pages = convert_from_path(filepath, dpi=300)
            img = pages[0]
        else:
            img = Image.open(filepath)
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return {}
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=95)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    logger.info(f"  Image: {len(img_buffer.getvalue())/1024:.0f} KB")
    
    import requests
    
    prompt = """Extract ALL visible data from this hand-drawn field sketch for a Maine HHE-200 septic evaluation form. Return ONLY valid JSON with this exact structure - fill every field you can, leave blank what you can't read:

{
  "map_lot": "",
  "road_name": "",
  "scale": "",
  "date": "",
  "soil_observations": [{"hole":, "depth":, "texture":, "color":, "limiting_factor":, "consistence":, "redox":""}],
  "gps": "",
  "well": {"type":, "distance_ft":""},
  "tank": {"capacity":, "location":""},
  "dimensions_ft": {"house_to_tank":, "tank_to_field":, "field_to_well":, "lot_frontage":, "lot_depth":, "road_frontage_ft":""},
  "distances_list": [],
  "tie_items": [{"from":, "to":, "ft":""}],
  "elevations": {"erp":, "finished_grade":, "top_pipe":, "bottom_field":, "groundwater":, "limiting_factor_depth":, "differential_ft":""},
  "field_system": {"brand":, "rows":, "modules":, "cluster_w":, "cluster_l":""},
  "buildings": [{"name":, "type":, "setback_ft":""}],
  "erp_description": "",
  "red_marks": "",
  "notes": "",
  "all_text_found": ""
}"""
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-opus-4-8",
                "max_tokens": 2000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_base64}}
                    ]
                }]
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"API error {response.status_code}: {response.text[:200]}")
            return {}
        
        text = response.json()["content"][0]["text"]
        
        # Extract JSON from response
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            # Try parsing the whole response as JSON
            try:
                data = json.loads(text)
            except:
                logger.warning("Could not parse JSON from Claude response")
                data = {"raw_text": text}
        
        data["_claude_raw"] = text
        logger.info(f"  Extracted {sum(1 for v in str(data).split(',') if ':' in v and v.split(':')[-1].strip('" '))} data points")
        return data
        
    except Exception as e:
        logger.error(f"Claude extraction failed: {e}")
        return {}


def merge_sketch_with_form(sketch_data: dict, form_fields: dict) -> dict:
    """Merge Claude's sketch extraction with Google Sheet form data.
    Maps sketch-derived data to field_adapter-recognized keys so it
    flows through to the form."""

    merged = dict(form_fields)
    
    if not sketch_data:
        return merged
    
    # Dimensions from distances_list
    dist_list = sketch_data.get("distances_list", [])
    if dist_list and len(dist_list) >= 6:
        merged["setback_tank_to_house"] = dist_list[0]
        merged["setback_well"] = dist_list[1]
        merged["lot_frontage"] = dist_list[2]
        merged["lot_depth"] = dist_list[3]
    
    # Buildings from sketch
    bldgs = sketch_data.get("buildings", [])
    for b in bldgs:
        if b.get("setback_ft"):
            merged["setback_field_to_house"] = b["setback_ft"]
    
    # Dimensions
    dims = sketch_data.get("dimensions_ft", {}) # map to field_adapter/sheet_parser keys
    dims = sketch_data.get("dimensions_ft", {})
    ht = dims.get("house_to_tank", "")
    if ht and ht not in (merged.get("setback_tank_to_house", "")):
        merged["setback_tank_to_house"] = ht
    fw = dims.get("field_to_well", "")
    if fw and fw not in (merged.get("setback_well", "")):
        merged["setback_well"] = f"{fw} ft"
    lf = dims.get("lot_frontage", "")
    if lf and not merged.get("lot_frontage_dim"):
        merged["lot_frontage_dim"] = lf
    ld = dims.get("lot_depth", "")
    if ld and not merged.get("lot_depth_dim"):
        merged["lot_depth_dim"] = ld
    
    # Well info
    well = sketch_data.get("well", {})
    if well.get("type") and not merged.get("well_type"):
        merged.setdefault('well_type', well["type"])
    if well.get("distance_ft") and not merged.get("setback_well"):
        merged["setback_well"] = f"{well['distance_ft']} ft"
    
    # Elevations - map to field_adapter keys
    elev = sketch_data.get("elevations", {})
    if elev.get("erp") and not merged.get("erp_reference_elevation"):
        merged.setdefault('erp_reference_elevation', elev["erp"])
    if elev.get("finished_grade") and not merged.get("finished_grade_elevation"):
        merged.setdefault('finished_grade_elevation', elev["finished_grade"])
    if elev.get("top_pipe") and not merged.get("top_of_distribution_pipe_elevation"):
        merged.setdefault('top_of_distribution_pipe_elevation', elev["top_pipe"])
    if elev.get("bottom_field") and not merged.get("bottom_of_disposal_field_elevation"):
        merged.setdefault('bottom_of_disposal_field_elevation', elev["bottom_field"])
    if elev.get("limiting_factor_depth") and not merged.get("limiting_factor_depth"):
        merged.setdefault('limiting_factor_depth', elev["limiting_factor_depth"])
    if elev.get("groundwater") and not merged.get("water_table_depth_hole1"):
        merged.setdefault('water_table_depth_hole1', elev["groundwater"])
    
    # Field system - map to sheet_parser keys
    fs = sketch_data.get("field_system", {})
    if fs.get("rows") and not merged.get("num_rows"):
        merged.setdefault('num_rows', fs["rows"])
    if fs.get("modules") and not merged.get("mods_per_row"):
        merged.setdefault('mods_per_row', fs["modules"])
    
    # Soil data - map to sheet_parser keys
    soil = sketch_data.get("soil_observations", [])
    if soil and len(soil) > 0:
        s = soil[0]
        if s.get("limiting_factor") and not merged.get("deepest_restrictive_layer_hole1"):
            merged["deepest_restrictive_layer_hole1"] = s["limiting_factor"]
        if s.get("depth") and not merged.get("water_table_depth_hole1"):
            merged["water_table_depth_hole1"] = s["depth"]
        if s.get("color") and not merged.get("soil_color_hole1"):
            merged["soil_color_hole1"] = s["color"]
        if s.get("texture") and not merged.get("soil_type"):
            merged["soil_type"] = s["texture"]
    
    # Road name
    if sketch_data.get("road_name") and not merged.get("road_name"):
        merged.setdefault('road_name', sketch_data["road_name"])
    
    return merged


if __name__ == "__main__":
    # Test on the sketch
    data = extract_sketch_with_claude("sketches/26-018 field worksheet - George Bouchles.pdf")
    print(json.dumps(data, indent=2) if data else "No data extracted")
