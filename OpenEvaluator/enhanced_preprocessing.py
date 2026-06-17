#!/usr/bin/env python3
"""
Enhanced Image Preprocessing for Hand-Drawn Sketches
Adds: deskewing, upscaling, adaptive thresholding, and level controls
"""
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def preprocess_image_enhanced(img_array, aggressive: bool = False, upscale: int = 2) -> object:
    """
    Enhanced image preprocessing with deskew + upscale + adaptive options.

    Args:
        img_array: Input image (PIL Image or numpy array)
        aggressive: If True, use aggressive preprocessing; if False, gentle
        upscale: Upscaling factor (1 = no upscale, 2 = 2x, 3 = 3x)

    Returns:
        Preprocessed numpy array ready for Vision API
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image

        # Convert PIL Image to numpy array if needed
        if hasattr(img_array, 'tobytes'):
            img_array = np.array(img_array)

        # 1. UPSCALING (before preprocessing - makes small text clearer)
        if upscale > 1:
            h, w = img_array.shape[:2]
            new_h, new_w = h * upscale, w * upscale
            img_array = cv2.resize(img_array, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logger.info(f"    Upscaled: {h}×{w} → {new_h}×{new_w}")

        # 2. DESKEWING (fixes rotated sketches - critical for hand-drawn)
        img_array = _deskew_image(img_array)

        # 3. GRAYSCALE conversion
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        if aggressive:
            # AGGRESSIVE PATH (for low-quality or faint sketches)
            logger.info(f"    Using AGGRESSIVE preprocessing...")

            # 4a. CLAHE with higher clip limit (more aggressive contrast)
            clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(6, 6))
            contrast_enhanced = clahe.apply(gray)

            # 5a. Strong denoise
            denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=12, templateWindowSize=7, searchWindowSize=21)

            # 6a. Morphological opening (remove noise)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            opened = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel, iterations=1)

            # 7a. Aggressive sharpening
            kernel = np.array([[-2, -1,  0],
                              [-1,  1,  1],
                              [ 0,  1,  2]]) / 4
            sharpened = cv2.filter2D(opened, -1, kernel)

            # 8a. Adaptive thresholding (better for varying lighting)
            binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)

            # 9a. Strong dilation to fill gaps
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            processed = cv2.dilate(binary, kernel, iterations=2)

        else:
            # GENTLE PATH (for good quality sketches - preserves detail)
            logger.info(f"    Using GENTLE preprocessing...")

            # 4b. CLAHE with moderate clip limit
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            contrast_enhanced = clahe.apply(gray)

            # 5b. Moderate denoise
            denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=10, templateWindowSize=7, searchWindowSize=21)

            # 6b. Gentle sharpening
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]]) / 9
            sharpened = cv2.filter2D(denoised, -1, kernel)

            # 7b. Adaptive thresholding (preserves more detail than OTSU)
            binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)

            # 8b. Light dilation to fill small gaps
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            processed = cv2.dilate(binary, kernel, iterations=1)

        logger.info(f"    ✓ Enhanced preprocessing complete")
        return processed

    except ImportError as e:
        logger.warning(f"    opencv-python not installed: {e}")
        return img_array
    except Exception as e:
        logger.warning(f"    Enhanced preprocessing failed: {e}, continuing with original")
        return img_array


def _deskew_image(img_array) -> object:
    """
    Deskew image by detecting text orientation.
    Critical for hand-drawn sketches that may be rotated.
    """
    try:
        import cv2
        import numpy as np

        h, w = img_array.shape[:2]

        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Find contours to detect text orientation
        edges = cv2.Canny(gray, 100, 200)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)

        if lines is None or len(lines) == 0:
            logger.info(f"    No rotation detected")
            return img_array

        # Extract angles from detected lines
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            angles.append(angle)

        # Use median angle (more robust than mean)
        median_angle = np.median(angles) if angles else 0

        # Only correct if angle is significant (> 0.5 degrees)
        if abs(median_angle) > 0.5:
            # Rotation matrix
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            deskewed = cv2.warpAffine(img_array, M, (w, h),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REFLECT)
            logger.info(f"    Deskewed by {median_angle:.1f}°")
            return deskewed
        else:
            logger.info(f"    No significant rotation detected")
            return img_array

    except Exception as e:
        logger.warning(f"    Deskewing failed: {e}, continuing with original")
        return img_array


def compare_preprocessing(filepath: str) -> dict:
    """
    Compare original vs. enhanced preprocessing on a real image.
    Returns before/after metrics.
    """
    try:
        from PIL import Image
        import numpy as np
        import io
        from google.cloud import vision
        from google.oauth2 import service_account
        import os
        import json

        logger.info(f"Comparing preprocessing on {Path(filepath).name}...")

        # Load image
        logger.info(f"  Opening {filepath}...")
        
        # Handle PDF: convert first page to image
        if filepath.lower().endswith('.pdf'):
            from pdf2image import convert_from_path
            pages = convert_from_path(filepath, dpi=200)
            if pages:
                img = pages[0]
            else:
                logger.error("    PDF conversion returned no pages")
                return {}
        else:
            img = Image.open(filepath)
        img_array = np.array(img)

        # Setup Vision API
        vision_key_json = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
        if not vision_key_json:
            logger.error("GOOGLE_CLOUD_VISION_KEY not set")
            return {}

        creds_dict = json.loads(vision_key_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        results = {
            "original": {},
            "gentle": {},
            "aggressive": {},
        }

        # Test 1: Original (unprocessed)
        logger.info("  Testing: ORIGINAL (no preprocessing)")
        original_bytes = io.BytesIO()
        img.save(original_bytes, format='PNG')
        response = client.document_text_detection(image=vision.Image(content=original_bytes.getvalue()))
        text_orig = response.text_annotations[0].description if response.text_annotations else ""
        results["original"]["chars"] = len(text_orig)
        results["original"]["text_sample"] = text_orig[:100]
        logger.info(f"    Extracted: {len(text_orig)} characters")

        # Test 2: Gentle preprocessing
        logger.info("  Testing: GENTLE preprocessing")
        gentle = preprocess_image_enhanced(img_array, aggressive=False, upscale=2)
        gentle_img = Image.fromarray(gentle)
        gentle_bytes = io.BytesIO()
        gentle_img.save(gentle_bytes, format='PNG')
        response = client.document_text_detection(image=vision.Image(content=gentle_bytes.getvalue()))
        text_gentle = response.text_annotations[0].description if response.text_annotations else ""
        results["gentle"]["chars"] = len(text_gentle)
        results["gentle"]["text_sample"] = text_gentle[:100]
        logger.info(f"    Extracted: {len(text_gentle)} characters")

        # Test 3: Aggressive preprocessing
        logger.info("  Testing: AGGRESSIVE preprocessing")
        aggressive = preprocess_image_enhanced(img_array, aggressive=True, upscale=2)
        agg_img = Image.fromarray(aggressive)
        agg_bytes = io.BytesIO()
        agg_img.save(agg_bytes, format='PNG')
        response = client.document_text_detection(image=vision.Image(content=agg_bytes.getvalue()))
        text_agg = response.text_annotations[0].description if response.text_annotations else ""
        results["aggressive"]["chars"] = len(text_agg)
        results["aggressive"]["text_sample"] = text_agg[:100]
        logger.info(f"    Extracted: {len(text_agg)} characters")

        # Calculate improvements
        baseline = len(text_orig)
        improvement_gentle = ((len(text_gentle) - baseline) / baseline * 100) if baseline > 0 else 0
        improvement_agg = ((len(text_agg) - baseline) / baseline * 100) if baseline > 0 else 0

        results["summary"] = {
            "baseline_chars": baseline,
            "gentle_improvement_pct": f"+{improvement_gentle:.1f}%",
            "aggressive_improvement_pct": f"+{improvement_agg:.1f}%",
            "recommendation": "aggressive" if improvement_agg > improvement_gentle else "gentle"
        }

        logger.info(f"\n✓ COMPARISON RESULTS:")
        logger.info(f"  Original:    {baseline} chars")
        logger.info(f"  Gentle:      {len(text_gentle)} chars ({improvement_gentle:+.1f}%)")
        logger.info(f"  Aggressive:  {len(text_agg)} chars ({improvement_agg:+.1f}%)")
        logger.info(f"  Recommended: {results['summary']['recommendation']}")

        return results

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        return {}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced preprocessing for sketches")
    parser.add_argument("--test-compare", help="Compare preprocessing on an image")
    args = parser.parse_args()

    if args.test_compare:
        results = compare_preprocessing(args.test_compare)
        import json
        print(json.dumps(results, indent=2))
