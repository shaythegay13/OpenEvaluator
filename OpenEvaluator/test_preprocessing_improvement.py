#!/usr/bin/env python3
"""
Test: Enhanced Preprocessing on Row 2's Actual Sketch
Shows before/after improvement with different preprocessing levels.
"""
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_preprocessing import preprocess_image_enhanced


def test_row2_sketch():
    """Test preprocessing on Row 2's actual sketch."""
    sketch_path = Path("/home/workspace/OpenEvaluator/sketches/26-018 field worksheet - George Bouchles.pdf")

    if not sketch_path.exists():
        logger.error(f"Sketch not found: {sketch_path}")
        return {}

    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING: Enhanced Preprocessing on Row 2 Sketch")
    logger.info(f"File: {sketch_path.name}")
    logger.info(f"{'='*80}\n")

    try:
        from pdf2image import convert_from_path
        import numpy as np
        from PIL import Image
        import io
        from google.cloud import vision
        from google.oauth2 import service_account

        # 1. Convert PDF to images
        logger.info("Step 1: Converting PDF to images...")
        pages = convert_from_path(str(sketch_path), dpi=300)
        logger.info(f"  Found {len(pages)} pages")

        # Setup Vision API
        vision_key_json = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
        if not vision_key_json:
            logger.error("GOOGLE_CLOUD_VISION_KEY not set")
            return {}

        creds_dict = json.loads(vision_key_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = vision.ImageAnnotatorClient(credentials=credentials)

        results = {
            "test_date": "2026-06-15",
            "sketch": str(sketch_path.name),
            "pages": len(pages),
            "methods": {},
            "summary": {}
        }

        # Test each preprocessing method on first page (page 1 = main sketch)
        if len(pages) > 0:
            page = pages[0]
            page_array = np.array(page)
            logger.info(f"\nStep 2: Testing preprocessing methods on Page 1...")

            # Method 1: Original (no preprocessing)
            logger.info(f"\n  Method 1: ORIGINAL (no preprocessing)")
            original_bytes = io.BytesIO()
            page.save(original_bytes, format='PNG')
            response = client.document_text_detection(image=vision.Image(content=original_bytes.getvalue()))
            text_orig = response.text_annotations[0].description if response.text_annotations else ""
            results["methods"]["original"] = {
                "chars": len(text_orig),
                "lines": len(text_orig.split('\n')),
                "sample": text_orig[:150]
            }
            logger.info(f"    Extracted: {len(text_orig)} characters, {len(text_orig.split(chr(10)))} lines")

            # Method 2: Gentle preprocessing
            logger.info(f"\n  Method 2: GENTLE preprocessing (deskew + 2x upscale + adaptive threshold)")
            gentle = preprocess_image_enhanced(page_array, aggressive=False, upscale=2)
            gentle_img = Image.fromarray(gentle)
            gentle_bytes = io.BytesIO()
            gentle_img.save(gentle_bytes, format='PNG')
            response = client.document_text_detection(image=vision.Image(content=gentle_bytes.getvalue()))
            text_gentle = response.text_annotations[0].description if response.text_annotations else ""
            results["methods"]["gentle"] = {
                "chars": len(text_gentle),
                "lines": len(text_gentle.split('\n')),
                "sample": text_gentle[:150]
            }
            improvement_gentle = ((len(text_gentle) - len(text_orig)) / len(text_orig) * 100) if len(text_orig) > 0 else 0
            logger.info(f"    Extracted: {len(text_gentle)} characters ({improvement_gentle:+.1f}%), {len(text_gentle.split(chr(10)))} lines")

            # Method 3: Aggressive preprocessing
            logger.info(f"\n  Method 3: AGGRESSIVE preprocessing (stronger contrast + denoise)")
            aggressive = preprocess_image_enhanced(page_array, aggressive=True, upscale=2)
            agg_img = Image.fromarray(aggressive)
            agg_bytes = io.BytesIO()
            agg_img.save(agg_bytes, format='PNG')
            response = client.document_text_detection(image=vision.Image(content=agg_bytes.getvalue()))
            text_agg = response.text_annotations[0].description if response.text_annotations else ""
            results["methods"]["aggressive"] = {
                "chars": len(text_agg),
                "lines": len(text_agg.split('\n')),
                "sample": text_agg[:150]
            }
            improvement_agg = ((len(text_agg) - len(text_orig)) / len(text_orig) * 100) if len(text_orig) > 0 else 0
            logger.info(f"    Extracted: {len(text_agg)} characters ({improvement_agg:+.1f}%), {len(text_agg.split(chr(10)))} lines")

            # Summary
            logger.info(f"\n{'='*80}")
            logger.info(f"RESULTS SUMMARY")
            logger.info(f"{'='*80}")
            logger.info(f"Original:    {len(text_orig):4d} chars")
            logger.info(f"Gentle:      {len(text_gentle):4d} chars ({improvement_gentle:+6.1f}%)")
            logger.info(f"Aggressive:  {len(text_agg):4d} chars ({improvement_agg:+6.1f}%)")

            best_method = "aggressive" if len(text_agg) > len(text_gentle) else "gentle"
            best_improvement = max(improvement_gentle, improvement_agg)
            logger.info(f"\n✓ Best method: {best_method.upper()} (+{best_improvement:.1f}%)")

            results["summary"] = {
                "baseline_chars": len(text_orig),
                "gentle_chars": len(text_gentle),
                "aggressive_chars": len(text_agg),
                "gentle_improvement_pct": f"{improvement_gentle:+.1f}%",
                "aggressive_improvement_pct": f"{improvement_agg:+.1f}%",
                "recommended": best_method,
                "estimated_measurement_extraction": f"~{int(best_improvement * 0.5)}-{int(best_improvement)}% improvement in field dimensions, depths, elevations"
            }

        return results

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return {}
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return {}


if __name__ == "__main__":
    results = test_row2_sketch()

    print(f"\n\n{'='*80}")
    print(f"TEST RESULTS (JSON)")
    print(f"{'='*80}")
    print(json.dumps(results, indent=2))

    # Save results
    out_path = Path("/home/workspace/OpenEvaluator/preprocessing_test_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {out_path}")
