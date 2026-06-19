#!/usr/bin/env python3
"""
claude_sketch_extractor.py — Extract bearing directions from field sketches.

Analyzes hand-drawn septic field sketches using Claude's vision API to:
1. Identify the disposal field rectangle
2. Locate tie-point objects (trees, poles, sheds, etc.) labeled on the sketch
3. Determine the compass bearing from the field to each tie point
4. Return bearing_a_degrees and bearing_b_degrees for the placement solver

The solver uses these bearings to locate tie points around the pin anchor
and trilaterate the field position deterministically.
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BearingResult:
    """Result from sketch bearing extraction."""
    bearing_a_degrees: Optional[float]
    bearing_b_degrees: Optional[float]
    tie_point_a_object: Optional[str]
    tie_point_b_object: Optional[str]
    tie_point_a_corner: Optional[str]
    tie_point_b_corner: Optional[str]
    confidence: str  # "high", "medium", "low"
    notes: str


def corner_to_bearing(corner: str) -> float:
    """Convert field corner label (NE/NW/SE/SW) to bearing in degrees."""
    corner_map = {
        "NE": 45.0,
        "SE": 135.0,
        "SW": 225.0,
        "NW": 315.0,
        "northeast": 45.0,
        "southeast": 135.0,
        "southwest": 225.0,
        "northwest": 315.0,
    }
    corner_upper = corner.strip().upper()
    return corner_map.get(corner_upper, None)


def extract_directions_from_form_data(
    tie_point_a_object: str,
    tie_point_a_corner: str,
    tie_point_b_object: str,
    tie_point_b_corner: str
) -> BearingResult:
    """
    Extract bearing directions from form tie-point data.
    Infers bearings from the labeled field corners.

    Args:
        tie_point_a_object: Name of first tie point (e.g., "maple tree")
        tie_point_a_corner: Which corner it measures to (NE/NW/SE/SW)
        tie_point_b_object: Name of second tie point
        tie_point_b_corner: Which corner it measures to

    Returns:
        BearingResult with inferred bearings
    """
    bearing_a = corner_to_bearing(tie_point_a_corner)
    bearing_b = corner_to_bearing(tie_point_b_corner)

    return BearingResult(
        bearing_a_degrees=bearing_a,
        bearing_b_degrees=bearing_b,
        tie_point_a_object=tie_point_a_object,
        tie_point_b_object=tie_point_b_object,
        tie_point_a_corner=tie_point_a_corner,
        tie_point_b_corner=tie_point_b_corner,
        confidence="high" if (bearing_a is not None and bearing_b is not None) else "medium",
        notes=f"Bearings inferred from corner labels: {tie_point_a_corner}→{bearing_a}°, {tie_point_b_corner}→{bearing_b}°"
    )


def extract_directions_from_sketch(sketch_path: str) -> BearingResult:
    """
    Extract bearing directions from a field sketch image.

    Args:
        sketch_path: Path to sketch image (PNG/JPG) or PDF worksheet

    Returns:
        BearingResult with bearing_a_degrees, bearing_b_degrees, and metadata
    """

    sketch_path = Path(sketch_path)
    if not sketch_path.exists():
        logger.error(f"Sketch file not found: {sketch_path}")
        return BearingResult(None, None, None, None, None, None, "error", f"File not found: {sketch_path}")

    # Convert PDF to image if needed
    image_path = sketch_path
    if sketch_path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(str(sketch_path), dpi=200, first_page=1, last_page=1)
            image_path = sketch_path.parent / f"{sketch_path.stem}_page1.png"
            pages[0].save(str(image_path), "PNG")
            logger.info(f"Converted PDF to image: {image_path}")
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return BearingResult(None, None, None, None, None, None, "error", f"PDF conversion failed: {e}")

    # Read image and encode as base64
    try:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        logger.info(f"Loaded sketch image: {image_path.name} ({len(image_data) / 1024:.0f} KB base64)")
    except Exception as e:
        logger.error(f"Failed to read image: {e}")
        return BearingResult(None, None, None, None, None, None, "error", f"Image read failed: {e}")

    # Call Claude API to extract bearing data
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set in environment")
        return BearingResult(None, None, None, None, None, None, "error", "API key not configured")

    prompt = """You are analyzing a hand-drawn field sketch for a Maine septic system evaluation.

TASK: Extract the compass bearing (0-359°) from the DISPOSAL FIELD RECTANGLE to each of the two tie points.

KEY ASSUMPTION: All field sketches follow standard surveying/drafting convention where NORTH IS UP on the page.

STEPS:
1. Identify the FIELD RECTANGLE on the sketch (the 11'×28' disposal field, usually clearly drawn/labeled as a rectangle)
2. Find the CENTER of this rectangle
3. Identify the TWO TIE POINTS (labeled objects like "shed", "tree", "pole", "building corner", "house", "garage", etc.)
   - Look for measurement lines from field corners to these objects
   - Identify which field corner each tie point measures to: NE (top-right), NW (top-left), SE (bottom-right), SW (bottom-left)
4. For EACH tie point, calculate the compass bearing FROM THE FIELD CENTER TO THAT OBJECT:
   - If object is above the field center = North direction = bearing close to 0° or 360°
   - If object is to the right = East = bearing close to 90°
   - If object is below = South = bearing close to 180°
   - If object is to the left = West = bearing close to 270°
   - Estimate the angle based on position: NE=45°, SE=135°, SW=225°, NW=315°
   - Be precise: if it's 30° from north toward east, use 30°, not 45°
5. Extract the object names and corner references from any labels visible on the sketch

RETURN ONLY VALID JSON with this exact structure (no markdown, no code blocks):

{
  "tie_point_a_object": "<name of first tie point, e.g. 'maple tree' or 'shed'>",
  "tie_point_a_corner": "<which field corner it ties to: NE/NW/SE/SW>",
  "bearing_a_degrees": <compass bearing from field center to tie point A as a number 0-359, or null if impossible to determine>,
  "tie_point_b_object": "<name of second tie point, e.g. 'oak tree' or 'telephone pole'>",
  "tie_point_b_corner": "<which field corner it ties to: NE/NW/SE/SW>",
  "bearing_b_degrees": <compass bearing from field center to tie point B as a number 0-359, or null if impossible to determine>,
  "confidence": "<'high', 'medium', or 'low' based on sketch clarity, object positioning, and label legibility>",
  "notes": "<brief explanation of what you identified, the position of each tie point relative to the field, and any uncertainties>"
}

IMPORTANT:
- Return bearing as a NUMBER (0-359), not a compass direction string
- Both bearings are FROM the field center outward to the tie point
- If you cannot reliably estimate bearing based on position, set to null
- Be specific about which corner each tie point ties to (look for labels or measurement lines)
- Assume North is up; use the visual position on the page to infer bearing"""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )

        response_text = message.content[0].text
        logger.info(f"Claude response received ({len(response_text)} chars)")

        # Parse JSON from response
        try:
            # Try to extract JSON from markdown code block
            if "```" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                else:
                    json_str = response_text
            else:
                json_str = response_text

            data = json.loads(json_str)
            logger.info(f"✓ Parsed bearing data: A={data.get('bearing_a_degrees')}°, B={data.get('bearing_b_degrees')}°")

            return BearingResult(
                bearing_a_degrees=data.get("bearing_a_degrees"),
                bearing_b_degrees=data.get("bearing_b_degrees"),
                tie_point_a_object=data.get("tie_point_a_object"),
                tie_point_b_object=data.get("tie_point_b_object"),
                tie_point_a_corner=data.get("tie_point_a_corner"),
                tie_point_b_corner=data.get("tie_point_b_corner"),
                confidence=data.get("confidence", "unknown"),
                notes=data.get("notes", "")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return BearingResult(None, None, None, None, None, None, "error", f"JSON parse failed: {e}")

    except Exception as e:
        logger.error(f"API call failed: {e}")
        return BearingResult(None, None, None, None, None, None, "error", f"API call failed: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 claude_sketch_extractor.py <sketch_image_or_pdf_path>")
        sys.exit(1)

    sketch_path = sys.argv[1]
    result = extract_directions_from_sketch(sketch_path)

    print("\n" + "=" * 60)
    print("BEARING EXTRACTION RESULT")
    print("=" * 60)
    print(f"Tie Point A: {result.tie_point_a_object}")
    print(f"  Corner: {result.tie_point_a_corner}")
    print(f"  Bearing: {result.bearing_a_degrees}°" if result.bearing_a_degrees is not None else "  Bearing: (not extracted)")
    print()
    print(f"Tie Point B: {result.tie_point_b_object}")
    print(f"  Corner: {result.tie_point_b_corner}")
    print(f"  Bearing: {result.bearing_b_degrees}°" if result.bearing_b_degrees is not None else "  Bearing: (not extracted)")
    print()
    print(f"Confidence: {result.confidence}")
    print(f"Notes: {result.notes}")
    print("=" * 60)
