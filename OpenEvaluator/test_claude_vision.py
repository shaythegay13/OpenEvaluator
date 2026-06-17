#!/usr/bin/env python3
"""Test Claude Opus 4.8 on sketch - save image first, then ask Claude."""
import os, json, sys, base64, io
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

# 1. Convert and save sketch as high quality JPEG
sketch_file = "/home/workspace/OpenEvaluator/sketches/26-018 field worksheet - George Bouchles.pdf"
pages = convert_from_path(sketch_file, dpi=400)
img_path = "/home/workspace/OpenEvaluator/sketches/sketch_for_claude.jpg"
pages[0].save(img_path, format='JPEG', quality=98)
img_size = Path(img_path).stat().st_size
print(f"Saved sketch as JPEG: {img_size/1024:.0f} KB")

# 2. Call Claude via Zo/ask API - pass image path as context
import httpx
resp = httpx.post(
    "https://api.zo.computer/zo/ask",
    headers={
        "authorization": os.environ["ZO_CLIENT_IDENTITY_TOKEN"],
        "content-type": "application/json"
    },
    json={
        "input": f"""You are reading a hand-drawn site evaluation sketch at {img_path}.

Read the image file at that path. It's a professional site evaluator's hand-drawn field worksheet for a septic system.

Extract EVERYTHING you can read:
1. ALL measurements and dimensions (numbers with ft, in, ' symbols)
2. ALL labels (house, tank, well, field, road, etc.)
3. ALL soil information (colors, textures, depths)
4. ALL GPS coordinates or survey data
5. ALL distances between features
6. Property lines, lot numbers, adjacent roads
7. Elevation reference points (ERP)
8. ANY text visible anywhere on the sketch

Be extremely thorough. Read every corner, every annotation, every number.""",
        "model_name": "claude-opus-4-8"
    },
    timeout=300
)
data = resp.json()
output = data.get("output", "")
print(f"\nCharacters extracted: {len(output)}")
print("="*60)
print(output[:3000])
if len(output) > 3000:
    print(f"\n... ({len(output)-3000} more chars truncated)")
