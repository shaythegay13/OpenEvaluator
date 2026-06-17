#!/usr/bin/env python3
"""Test Claude Opus 4.8 vision using direct API call"""
import base64
import json
import os
import subprocess
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
print(f"Image base64: {len(image_b64):,} chars")

# Try to get API key from environment (user should have set ANTHROPIC_API_KEY)
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not set in environment")
    print("  To set it: export ANTHROPIC_API_KEY='sk-ant-...'")
    exit(1)

print(f"Using Anthropic API key: {api_key[:20]}...")

# Build the curl command to call Claude API
prompt = """Analyze this hand-drawn site evaluation sketch. Extract the following data and ONLY include values that are clearly visible or written on the sketch:

{
  "soil_observations": {
    "depth_measurements_inches": ["list any depth measurements"],
    "soil_colors": ["any soil colors mentioned"],
    "soil_textures": ["any soil textures"],
    "limiting_factors": "what is the limiting factor (e.g., groundwater at 24 in)"
  },
  "elevation_data": {
    "erp_description": "elevation reference point description",
    "finished_grade_inches": "if marked",
    "top_of_pipe_inches": "if marked",
    "bottom_field_inches": "if marked"
  },
  "field_layout": {
    "num_rows": "number of rows",
    "modules_per_row": "modules per row",
    "total_modules": "total if marked",
    "cluster_dimensions": "e.g. 11' x 28'",
    "module_type": "brand/model if visible"
  },
  "distances_ft": {
    "house_to_tank": "if marked",
    "tank_to_field": "if marked",
    "field_to_well": "if marked"
  },
  "key_observations": ["summary of what you see on sketch"]
}

Return ONLY JSON. Do not invent data."""

# Make the API call via curl (timeout after 60 seconds)
curl_cmd = [
    "curl", "-s", "--max-time", "120",
    "-X", "POST",
    "-H", f"Authorization: Bearer {api_key}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({
        "model": "claude-opus-4-8",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }),
    "https://api.anthropic.com/v1/messages"
]

print("\nCalling Claude Opus 4.8...")
result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=180)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    exit(1)

try:
    response = json.loads(result.stdout)
    
    if "error" in response:
        print(f"API Error: {response['error']['message']}")
        exit(1)
    
    if "content" in response and len(response["content"]) > 0:
        text_content = response["content"][0].get("text", "")
        print("\n✓ Claude Opus 4.8 extracted data:")
        print(text_content)
        
        # Try to parse as JSON
        try:
            extracted = json.loads(text_content)
            print("\n✓ Parsed JSON successfully")
            print(json.dumps(extracted, indent=2))
        except:
            print("(returned as raw text, not JSON)")
    else:
        print("No content in response")
        print(response)
        
except json.JSONDecodeError as e:
    print(f"Failed to parse response: {e}")
    print(result.stdout[:500])
