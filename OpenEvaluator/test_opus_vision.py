#!/usr/bin/env python3
"""Test Claude Opus 4.8 vision on sketch image"""
import base64
import json
import os
from pathlib import Path

# Read the sketch image
sketch_path = Path("sketches/sketch_for_claude.jpg")
if not sketch_path.exists():
    print(f"Error: {sketch_path} not found")
    exit(1)

with open(sketch_path, "rb") as f:
    image_bytes = f.read()
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

print(f"Loaded sketch: {sketch_path.name} ({len(image_bytes):,} bytes)")

# Use the Zo API token
zo_token = os.environ.get("ZO_CLIENT_IDENTITY_TOKEN")
if not zo_token:
    print("Error: ZO_CLIENT_IDENTITY_TOKEN not set")
    exit(1)

# Call Zo /zo/ask with Claude Opus 4.8 (BYOK model)
import requests

prompt = """Analyze this hand-drawn sketch and extract the following data in JSON format:

{
  "soil_observations": {
    "depth_measurements": [depths in inches],
    "soil_colors": ["colors observed"],
    "soil_textures": ["textures observed"],
    "limiting_factors": ["any mentioned"]
  },
  "elevation_data": {
    "erp_description": "elevation reference point description",
    "erp_height_inches": number,
    "finished_grade": number,
    "top_of_pipe": number,
    "bottom_field": number
  },
  "field_layout": {
    "num_rows": number,
    "modules_per_row": number,
    "total_modules": number,
    "cluster_dimensions": "e.g. 11' x 28'",
    "module_type": "brand/model if visible"
  },
  "distances": {
    "house_to_tank_ft": number,
    "tank_to_field_ft": number,
    "field_to_well_ft": number
  },
  "observations": ["key observations and notes"]
}

Extract ONLY data that is clearly visible or written on the sketch. Do not hallucinate values."""

response = requests.post(
    "https://api.zo.computer/zo/ask",
    headers={
        "authorization": zo_token,
        "content-type": "application/json"
    },
    json={
        "input": prompt,
        "model_name": "byok:87228cf1-a844-4837-a472-c65fd4122867",
        "files": [
            {
                "data": image_b64,
                "mime_type": "image/jpeg",
                "filename": "sketch.jpg"
            }
        ]
    },
    timeout=120
)

print(f"\nResponse status: {response.status_code}")
result = response.json()

if "output" in result:
    print("\n✓ Claude Opus 4.8 extracted:")
    print(result["output"][:1500])
else:
    print("Error:", result)
