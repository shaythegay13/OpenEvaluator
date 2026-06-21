#!/usr/bin/env python3
"""
Simplified HHE-200 Pipeline

New architecture: Evaluator provides sketch + scales → system renders at scales → PDF

Flow:
  1. Parse intake form (sheet_parser.py)
  2. Extract scales from columns AA-AD
  3. Fill pages 1-2 with AcroForm (acro_fill.py)
  4. Generate pages 3-4 with form structure + scaled sketches (simplified generator)
  5. Assemble into 4-page PDF
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Optional
import json
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.resolve()


def run_pipeline(
    client_name: str,
    job_id: str,
    output_dir: Path,
    test_data: Optional[Dict] = None
) -> bool:
    """
    Run the complete HHE-200 generation pipeline.

    Args:
        client_name: e.g. "Marquis" or "Roberts"
        job_id: e.g. "26-018" or "26-123"
        output_dir: where to save output PDFs
        test_data: optional dict to use instead of Google Sheets

    Returns:
        True if successful, False otherwise
    """
    from sheet_parser import parse_sheet_row, RAW_ROW, ROBERTS_ROW

    # Select test data
    if test_data is None:
        if "marquis" in client_name.lower():
            test_data = RAW_ROW
        elif "roberts" in client_name.lower():
            test_data = ROBERTS_ROW
        else:
            logger.error(f"Unknown client: {client_name}")
            return False

    # Step 1: Parse intake form
    logger.info(f"Parsing {client_name} intake form...")
    fields = parse_sheet_row(test_data)

    # Step 2: Extract scales (already done in parse_sheet_row)
    logger.info("Scales extracted:")
    logger.info(f"  Page 3 site plan: {fields.get('scale_page3_inches_per_feet')}")
    logger.info(f"  Page 4 top (septic): {fields.get('scale_page4_top_inches_per_feet')}")
    logger.info(f"  Page 4 bottom vert: {fields.get('scale_page4_bottom_vertical_inches_per_feet')}")
    logger.info(f"  Page 4 bottom horiz: {fields.get('scale_page4_bottom_horizontal_inches_per_feet')}")

    # Step 3: Fill pages 1-2 with AcroForm
    logger.info("Filling pages 1-2 with AcroForm...")
    try:
        from field_adapter import adapt_sheet_fields_to_acro
        acro_fields = adapt_sheet_fields_to_acro(fields)

        # For now, just verify the fields are present
        logger.info(f"  Adapted {len(acro_fields)} fields for AcroForm")
    except Exception as e:
        logger.error(f"Error adapting fields: {e}")
        return False

    # Step 4: Fetch sketch from Google Drive
    logger.info("Fetching sketch from Google Drive...")
    sketch_url = fields.get("uploads_url")
    sketch_path = None
    if sketch_url:
        from sketch_fetcher import fetch_sketch
        sketch_path = fetch_sketch(sketch_url, output_dir / "sketches")
        if sketch_path:
            logger.info(f"  ✓ Sketch downloaded: {sketch_path}")
        else:
            logger.warning("  ⚠ Could not fetch sketch, will continue without it")
    else:
        logger.warning("  No sketch URL in form")

    # Step 5: Generate pages 3-4 with sketches [COMMENTED OUT]
    # Using filled template from acro_fill.py instead, which preserves filled soil form fields
    # logger.info("Generating pages 3-4 with sketches...")
    # try:
    #     from generate_hhe200_pages34_reportlab import generate_pages_3_4
    #
    #     page3_pdf = output_dir / f"HHE-200-{client_name}-page3.pdf"
    #     page4_pdf = output_dir / f"HHE-200-{client_name}-page4.pdf"
    #
    #     success = generate_pages_3_4(
    #         fields=fields,
    #         sketch_path=sketch_path,
    #         output_page3=page3_pdf,
    #         output_page4=page4_pdf
    #     )
    #
    #     if not success:
    #         logger.error("Failed to generate pages 3-4")
    #         return False
    #
    #     logger.info(f"  Page 3: {page3_pdf}")
    #     logger.info(f"  Page 4: {page4_pdf}")
    # except Exception as e:
    #     logger.error(f"Error generating pages 3-4: {e}", exc_info=True)
    #     return False

    # Step 6: Generate pages 1-2 with AcroForm
    logger.info("Generating pages 1-2 with AcroForm...")
    try:
        from acro_fill import fill_pdf_with_data

        pages_1_2_pdf_str = fill_pdf_with_data(acro_fields)
        pages_1_2_pdf = Path(pages_1_2_pdf_str)

        if not pages_1_2_pdf or not pages_1_2_pdf.exists():
            logger.error("Failed to generate pages 1-2")
            return False

        logger.info(f"  Pages 1-2: {pages_1_2_pdf}")
    except Exception as e:
        logger.error(f"Error generating pages 1-2: {e}", exc_info=True)
        return False

    # Step 7: Copy filled PDF as final output (already contains all 4 pages with filled soil form fields)
    logger.info("Finalizing 4-page PDF...")
    try:
        import shutil

        output_pdf = output_dir / f"HHE-200-{client_name}-{job_id}.pdf"

        # Copy the filled PDF (contains pages 1-2 AcroForm + pages 3-4 template with soil form fields)
        shutil.copy(pages_1_2_pdf, output_pdf)
        logger.info(f"  ✓ Final PDF: {output_pdf}")
    except Exception as e:
        logger.error(f"Error finalizing PDF: {e}", exc_info=True)
        return False

    logger.info(f"✓ {client_name} pipeline complete")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate HHE-200 PDFs from intake form"
    )
    parser.add_argument("--client", required=True, help="Client name (Marquis or Roberts)")
    parser.add_argument("--job", required=True, help="Job ID (26-018 or 26-123)")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(),
                        help="Output directory for PDFs")

    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    success = run_pipeline(args.client, args.job, args.output_dir)
    sys.exit(0 if success else 1)
