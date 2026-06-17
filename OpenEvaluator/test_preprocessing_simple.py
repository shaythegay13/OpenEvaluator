#!/usr/bin/env python3
"""
Simple test: Show preprocessing visual before/after on Row 2's sketch
"""
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from enhanced_preprocessing import preprocess_image_enhanced


def test_and_visualize():
    """Convert PDF page to image and apply preprocessing."""
    sketch_path = Path("/home/workspace/OpenEvaluator/sketches/26-018 field worksheet - George Bouchles.pdf")

    if not sketch_path.exists():
        logger.error(f"Sketch not found: {sketch_path}")
        return

    logger.info(f"\nTesting Enhanced Preprocessing")
    logger.info(f"File: {sketch_path.name}\n")

    try:
        from pdf2image import convert_from_path
        import numpy as np
        from PIL import Image

        # Convert PDF to images at 300 DPI
        logger.info("Converting PDF to images (300 DPI)...")
        pages = convert_from_path(str(sketch_path), dpi=300)
        logger.info(f"✓ Found {len(pages)} pages\n")

        if len(pages) > 0:
            page = pages[0]
            page_array = np.array(page)

            logger.info("Applying preprocessing methods...")

            # Original
            logger.info("\n1. ORIGINAL (unprocessed)")
            logger.info(f"   Size: {page_array.shape}")
            original_img = Image.fromarray(page_array)
            original_img.save("/home/workspace/OpenEvaluator/preprocessing_1_original.png")
            logger.info(f"   ✓ Saved: preprocessing_1_original.png ({original_img.size})")

            # Gentle
            logger.info("\n2. GENTLE preprocessing")
            logger.info(f"   - Deskew (auto-detect rotation)")
            logger.info(f"   - Upscale 2x")
            logger.info(f"   - Adaptive thresholding")
            logger.info(f"   - Light contrast boost (CLAHE)")
            gentle = preprocess_image_enhanced(page_array, aggressive=False, upscale=2)
            gentle_img = Image.fromarray(gentle)
            gentle_img.save("/home/workspace/OpenEvaluator/preprocessing_2_gentle.png")
            logger.info(f"   ✓ Saved: preprocessing_2_gentle.png ({gentle_img.size})")

            # Aggressive
            logger.info("\n3. AGGRESSIVE preprocessing")
            logger.info(f"   - Deskew (auto-detect rotation)")
            logger.info(f"   - Upscale 2x")
            logger.info(f"   - Strong contrast (CLAHE clipLimit=5)")
            logger.info(f"   - Stronger denoise")
            logger.info(f"   - Adaptive thresholding")
            aggressive = preprocess_image_enhanced(page_array, aggressive=True, upscale=2)
            agg_img = Image.fromarray(aggressive)
            agg_img.save("/home/workspace/OpenEvaluator/preprocessing_3_aggressive.png")
            logger.info(f"   ✓ Saved: preprocessing_3_aggressive.png ({agg_img.size})")

            logger.info(f"\n{'='*70}")
            logger.info(f"PREPROCESSING COMPARISON SAVED")
            logger.info(f"{'='*70}")
            logger.info(f"Original:     preprocessing_1_original.png ({original_img.size})")
            logger.info(f"Gentle:       preprocessing_2_gentle.png ({gentle_img.size})")
            logger.info(f"Aggressive:   preprocessing_3_aggressive.png ({agg_img.size})")
            logger.info(f"\nNext: Run these through Vision API to measure extraction improvement\n")

    except ImportError as e:
        logger.error(f"Missing: {e}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    test_and_visualize()
