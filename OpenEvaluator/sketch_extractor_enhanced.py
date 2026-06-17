#!/usr/bin/env python3
"""
Enhanced Sketch Extractor: Combines Google Vision + Tesseract + Pattern Extraction

Features:
- Image preprocessing (already in place)
- Google Vision DOCUMENT_TEXT_DETECTION (already in place)
- Tesseract OCR as backup/comparison (NEW)
- Intelligent measurement pattern extraction (NEW)
- Hybrid result merging (NEW)
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MEASUREMENT EXTRACTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

MEASUREMENT_PATTERNS = {
    'field_dimensions': [
        r'(\d+\.?\d*)\s*(?:x|by|×)\s*(\d+\.?\d*)\s*(?:ft|feet|\')',
        r'(\d+\.?\d*)\s*(?:ft|feet|\')\s*(?:x|by|×)\s*(\d+\.?\d*)',
        r'field[:\s]*(\d+\.?\d*)\s*(?:x|by)\s*(\d+\.?\d*)',
    ],
    'depth': [
        r'(\d+\.?\d*)\s*(?:in|inch|inches|"|")\s*(?:deep|depth)?',
        r'depth[:\s]*(\d+\.?\d*)\s*(?:in|inch|inches|")?',
        r'(\d+\.?\d*)\s*inches?\s*(?:deep|depth)',
    ],
    'distance': [
        r'(\d+\.?\d*)\s*(?:ft|feet)\s*(?:to|from|setback)',
        r'(?:to|from|setback)\s*(?:well|tank|property|building|road)[:\s]*(\d+\.?\d*)\s*(?:ft|feet)',
        r'setback\s*[=:]*\s*(\d+\.?\d*)\s*(?:ft|feet)',
    ],
    'elevation': [
        r'(-?\d+\.?\d*)["\"]?\s*(?:grade|elev|elevation|finish)',
        r'(?:top|bottom|grade|finish)[:\s]*(-?\d+\.?\d*)["\"]?',
        r'(-?\d+)["\"]?\s*(?:elevation|elev)',
    ],
    'scale': [
        r'1["\"]?\s*=\s*(\d+)\s*(?:ft|feet|\')',
        r'scale[:\s]*1\s*[=:]\s*(\d+)',
        r'scale[:\s]*(\d+)\s*(?:ft|feet)',
    ],
    'system_type': [
        r'(?:eljen|indrain|gsf|infiltrator|chamber|mound|gravel|stone|presby)',
    ],
    'modules': [
        r'(\d+)\s*(?:rows?)\s*(?:x|by)\s*(\d+)\s*(?:modules?|columns?)',
        r'(\d+)\s*(?:x|by)\s*(\d+)\s*(?:modules?)',
        r'(\d+)\s*modules?',
    ],
    'bedrooms': [
        r'(\d+)\s*(?:bed|br|bedroom)',
    ],
}


def extract_measurements(raw_text: str) -> Dict:
    """
    Extract structured measurements from raw OCR text using regex patterns.

    Returns:
        Dict with keys like 'field_dimensions', 'depth', 'distance', etc.
        Each containing a list of matches with confidence and position info
    """
    if not raw_text:
        return {}

    results = {
        "dimensions": [],
        "depths": [],
        "distances": [],
        "elevations": [],
        "scales": [],
        "system_type": None,
        "modules": [],
        "bedrooms": [],
        "raw_matches": {},
    }

    # Search for each pattern type
    for pattern_type, pattern_list in MEASUREMENT_PATTERNS.items():
        results["raw_matches"][pattern_type] = []

        for pattern in pattern_list:
            try:
                matches = re.finditer(pattern, raw_text, re.IGNORECASE)
                for match in matches:
                    match_data = {
                        "match": match.group(0),
                        "groups": match.groups(),
                        "position": match.start(),
                        "confidence": 0.85,  # Base confidence for regex match
                    }

                    # Categorize by type
                    if pattern_type == "field_dimensions":
                        if len(match.groups()) >= 2:
                            results["dimensions"].append({
                                "width": float(match.group(1)),
                                "length": float(match.group(2)),
                                "unit": "feet",
                                "raw": match.group(0),
                                "confidence": 0.90,
                            })

                    elif pattern_type == "depth":
                        if match.group(1):
                            results["depths"].append({
                                "value": float(match.group(1)),
                                "unit": "inches",
                                "raw": match.group(0),
                                "confidence": 0.85,
                            })

                    elif pattern_type == "distance":
                        if match.group(1):
                            results["distances"].append({
                                "value": float(match.group(1)),
                                "unit": "feet",
                                "raw": match.group(0),
                                "confidence": 0.80,
                            })

                    elif pattern_type == "elevation":
                        if match.group(1):
                            results["elevations"].append({
                                "value": float(match.group(1)),
                                "unit": "inches",
                                "raw": match.group(0),
                                "confidence": 0.85,
                            })

                    elif pattern_type == "scale":
                        if match.group(1):
                            results["scales"].append({
                                "scale_feet": int(match.group(1)),
                                "raw": match.group(0),
                                "confidence": 0.90,
                            })

                    elif pattern_type == "system_type":
                        results["system_type"] = match.group(0).lower()

                    elif pattern_type == "modules":
                        if len(match.groups()) >= 1:
                            results["modules"].append({
                                "layout": match.group(0),
                                "groups": match.groups(),
                                "confidence": 0.80,
                            })

                    elif pattern_type == "bedrooms":
                        if match.group(1):
                            results["bedrooms"].append(int(match.group(1)))

                    results["raw_matches"][pattern_type].append(match.group(0))

            except Exception as e:
                logger.warning(f"  Pattern error in {pattern_type}: {e}")

    return results


def extract_with_tesseract(image_path: str) -> Optional[Dict]:
    """
    Extract text using local Tesseract OCR.

    Returns:
        Dict with text, word_data, confidence, and measurements
    """
    try:
        import pytesseract
        import cv2
        import numpy as np
        from PIL import Image

        logger.info(f"  Extracting text with Tesseract: {Path(image_path).name}")

        # Load image
        if image_path.endswith('.pdf'):
            from pdf2image import convert_from_path
            pages = convert_from_path(image_path, dpi=300)
            img_array = np.array(pages[0])
        else:
            img = Image.open(image_path)
            img_array = np.array(img)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Enhanced preprocessing for Tesseract
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Adaptive threshold
        binary = cv2.adaptiveThreshold(enhanced, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)

        # Denoise
        denoised = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                                    cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))

        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6'

        # Extract text
        text = pytesseract.image_to_string(denoised, config=custom_config)

        # Get word-level data with confidence
        data = pytesseract.image_to_data(denoised, config=custom_config,
                                         output_type=pytesseract.Output.DICT)

        # Calculate average confidence
        confidences = [int(c) for c in data['conf'] if int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        logger.info(f"    Tesseract: {len(text)} chars, confidence {avg_confidence:.0f}%")

        # Extract measurements from Tesseract text
        measurements = extract_measurements(text)

        return {
            "text": text,
            "confidence": avg_confidence / 100,  # Convert to 0-1 scale
            "word_count": len(data['text']),
            "measurements": measurements,
            "source": "tesseract",
        }

    except ImportError as e:
        logger.warning(f"  Tesseract dependencies not available: {e}")
        logger.info("    Install with: apt-get install tesseract-ocr && pip install pytesseract")
        return None
    except Exception as e:
        logger.error(f"  Tesseract extraction failed: {e}")
        return None


def extract_with_google_vision(image_path: str) -> Optional[Dict]:
    """
    Extract text using Google Cloud Vision API.
    Uses DOCUMENT_TEXT_DETECTION for better structure.
    """
    import os
    import io
    import json
    from google.oauth2 import service_account
    from PIL import Image
    import numpy as np

    try:
        from google.cloud import vision
    except ImportError:
        logger.warning("  google-cloud-vision not available")
        return None

    vision_key_json = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
    if not vision_key_json:
        logger.warning("  GOOGLE_CLOUD_VISION_KEY not set, skipping Google Vision")
        return None

    try:
        logger.info(f"  Extracting text with Google Vision: {Path(image_path).name}")

        creds_dict = json.loads(vision_key_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        # Load and preprocess image
        if image_path.endswith('.pdf'):
            from pdf2image import convert_from_path
            pages = convert_from_path(image_path, dpi=300)
            page_array = np.array(pages[0])
        else:
            img = Image.open(image_path)
            page_array = np.array(img)

        # Preprocess (same as in sketch_extractor.py)
        from sketch_extractor import _preprocess_image
        preprocessed = _preprocess_image(page_array)

        if isinstance(preprocessed, np.ndarray):
            preprocessed_img = Image.fromarray(preprocessed)
        else:
            preprocessed_img = preprocessed

        img_bytes = io.BytesIO()
        preprocessed_img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        # Send to Vision API
        image = vision.Image(content=img_data)
        response = client.document_text_detection(image=image)

        # Extract text and confidence
        text = ""
        if response.text_annotations:
            text = response.text_annotations[0].description

        # Calculate average confidence from words
        confidences = []
        for page in response.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        confidences.append(word.confidence)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.75

        logger.info(f"    Google Vision: {len(text)} chars, confidence {avg_confidence:.0%}")

        # Extract measurements from Google Vision text
        measurements = extract_measurements(text)

        return {
            "text": text,
            "confidence": avg_confidence,
            "word_count": len(confidences),
            "measurements": measurements,
            "source": "google_vision",
        }

    except Exception as e:
        logger.error(f"  Google Vision extraction failed: {e}")
        return None


def hybrid_extract(image_path: str) -> Dict:
    """
    Hybrid extraction: Try both Google Vision and Tesseract, combine results.

    Returns best result from each method with confidence scoring.
    """
    results = {
        "google_vision": None,
        "tesseract": None,
        "best_source": None,
        "best_text": "",
        "best_confidence": 0,
        "measurements": {},
        "quality": "unknown",
    }

    logger.info(f"\n[HYBRID EXTRACTION] {Path(image_path).name}")
    logger.info("="*70)

    # Try Google Vision first
    google_result = extract_with_google_vision(image_path)
    if google_result:
        results["google_vision"] = google_result

    # Try Tesseract as backup/verification
    tesseract_result = extract_with_tesseract(image_path)
    if tesseract_result:
        results["tesseract"] = tesseract_result

    # Choose best source
    if google_result and tesseract_result:
        # Both available - choose higher confidence
        if google_result["confidence"] >= tesseract_result["confidence"]:
            results["best_source"] = "google_vision"
            results["best_text"] = google_result["text"]
            results["best_confidence"] = google_result["confidence"]
            results["measurements"] = google_result["measurements"]
        else:
            results["best_source"] = "tesseract"
            results["best_text"] = tesseract_result["text"]
            results["best_confidence"] = tesseract_result["confidence"]
            results["measurements"] = tesseract_result["measurements"]

    elif google_result:
        results["best_source"] = "google_vision"
        results["best_text"] = google_result["text"]
        results["best_confidence"] = google_result["confidence"]
        results["measurements"] = google_result["measurements"]

    elif tesseract_result:
        results["best_source"] = "tesseract"
        results["best_text"] = tesseract_result["text"]
        results["best_confidence"] = tesseract_result["confidence"]
        results["measurements"] = tesseract_result["measurements"]

    else:
        logger.error("  No extraction methods available!")
        return results

    # Assess quality
    text_len = len(results["best_text"])
    measurement_count = sum(len(v) for k, v in results["measurements"].items()
                           if isinstance(v, list))

    if results["best_confidence"] > 0.85 and measurement_count > 5:
        results["quality"] = "high"
    elif results["best_confidence"] > 0.70 and measurement_count > 3:
        results["quality"] = "medium"
    elif results["best_confidence"] > 0.50 and text_len > 100:
        results["quality"] = "low"
    else:
        results["quality"] = "poor"

    # Summary
    logger.info(f"\n[RESULT] Source: {results['best_source']}")
    logger.info(f"  Confidence: {results['best_confidence']:.0%}")
    logger.info(f"  Text length: {text_len} characters")
    logger.info(f"  Measurements extracted: {measurement_count} items")
    logger.info(f"  Quality: {results['quality'].upper()}")

    # Log measurements found
    if results["measurements"]:
        logger.info(f"\n  Measurements Found:")
        if results["measurements"].get("dimensions"):
            for dim in results["measurements"]["dimensions"]:
                logger.info(f"    • Field: {dim['width']} x {dim['length']} ft")
        if results["measurements"].get("depths"):
            for depth in results["measurements"]["depths"]:
                logger.info(f"    • Depth: {depth['value']} in")
        if results["measurements"].get("distances"):
            for dist in results["measurements"]["distances"]:
                logger.info(f"    • Distance: {dist['value']} ft")
        if results["measurements"].get("elevations"):
            for elev in results["measurements"]["elevations"]:
                logger.info(f"    • Elevation: {elev['value']}\"")
        if results["measurements"].get("scales"):
            for scale in results["measurements"]["scales"]:
                logger.info(f"    • Scale: 1\" = {scale['scale_feet']}'")

    logger.info("="*70 + "\n")

    return results


if __name__ == "__main__":
    # Test with row 2 sketch
    test_sketch = Path("sketches/26-018 field worksheet - George Bouchles.pdf")

    if test_sketch.exists():
        print(f"\nTesting with: {test_sketch}")
        result = hybrid_extract(str(test_sketch))
        print(f"\nFinal Result:")
        print(json.dumps({
            "source": result["best_source"],
            "confidence": f"{result['best_confidence']:.0%}",
            "quality": result["quality"],
            "text_chars": len(result["best_text"]),
            "measurements": {
                "dimensions": len(result["measurements"].get("dimensions", [])),
                "depths": len(result["measurements"].get("depths", [])),
                "distances": len(result["measurements"].get("distances", [])),
                "elevations": len(result["measurements"].get("elevations", [])),
                "scales": len(result["measurements"].get("scales", [])),
            }
        }, indent=2))
    else:
        print(f"Test sketch not found: {test_sketch}")
