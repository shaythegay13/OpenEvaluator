#!/usr/bin/env python3
"""Test Claude Opus 4.8 on hand-drawn sketch for HHE-200 data extraction."""
import os, json, sys, base64, io
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

SKETCH_FILE = "sketches/26-018 field worksheet - George Bouchles.pdf"
OUTPUT_FILE = "claude_extraction_results.json"

# Step 1: Convert PDF to high-res image
print(f"Converting {SKETCH_FILE} to image...")
pages = convert_from_path(SKETCH_FILE, dpi=300)
img = pages[0]

# Step 2: Save as JPEG for API
img_buffer = io.BytesIO()
img.save(img_buffer, format='JPEG', quality=95)
img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
print(f"  Image size: {len(img_buffer.getvalue()) / 1024:.0f} KB")

# Step 3: Send to Claude Opus 4.8
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    sys.exit(1)

print("Sending to Claude Opus 4.8...")
import requests

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
                {
                    "type": "text",
                    "text": """Extract ALL visible text and data from this hand-drawn field sketch for an HHE-200 septic system evaluation form. Return the data in this exact JSON format:

{
  "gps_coordinates": {"lat_dms": "", "lng_dms": ""},
  "property_information": {
    "map": "",
    "lot": "",
    "road_name": "",
    "adjacent_lots": []
  },
  "soil_observations": [
    {
      "hole_number": 1,
      "depth_range_in": "",
      "texture": "",
      "color": "",
      "consistence": "",
      "redox_features": "",
      "limiting_factor": "",
      "slope": ""
    }
  ],
  "tank_info": {"capacity_gallons": "", "location": ""},
  "well_info": {"type": "", "location": "", "depth_ft": ""},
  "dimensions_ft": {
    "house_to_tank": "",
    "tank_to_field": "",
    "field_to_well": "",
    "field_to_property_line": "",
    "lot_frontage": "",
    "lot_depth": ""
  },
  "elevations": {
    "erp_elevation_ft": "",
    "finished_grade_in": "",
    "top_of_pipe_in": "",
    "bottom_of_field_in": "",
    "limiting_factor_depth_in": "",
    "groundwater_depth_in": ""
  },
  "field_layout": {
    "brand": "",
    "num_rows": "",
    "modules_per_row": "",
    "total_modules": "",
    "cluster_width_ft": "",
    "cluster_length_ft": ""
  },
  "tie_items": [
    {"from": "", "to": "", "distance_ft": ""}
  ],
  "all_visible_text": ""
}

Fill in every field you can find on the sketch. For fields not visible, leave as empty string."""
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_base64
                    }
                }
            ]
        }]
    }
)

if response.status_code != 200:
    print(f"ERROR {response.status_code}: {response.text}")
    sys.exit(1)

result = response.json()
text_content = result.get("content", [{}])[0].get("text", "")

# Save raw response
with open(OUTPUT_FILE, "w") as f:
    f.write(text_content)

print(f"\n=== CLAUDE'S EXTRACTION ({len(text_content)} chars) ===")
# Try to parse as JSON
try:
    data = json.loads(text_content)
    print(json.dumps(data, indent=2))
except json.JSONDecodeError:
    print(text_content)

# Count filled fields
try:
    data = json.loads(text_content)
    filled = sum(1 for v in str(data).split(",") if ":" in v and '"' not in v.split(":")[-1])
    print(f"\nFilled fields: {filled}")
except:
    pass

print(f"\nResults saved to {OUTPUT_FILE}")
