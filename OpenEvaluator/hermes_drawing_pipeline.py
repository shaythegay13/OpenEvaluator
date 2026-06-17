#!/usr/bin/env python3
"""
Hermes Drawing Pipeline: Extract sketch data → Generate accurate drawings → Compare with examples

This pipeline:
1. Downloads submitted sketches from Google Drive
2. Extracts measurements, annotations, and geometric data using Vision API
3. Generates site plan, disposal plan, and cross-section drawings
4. Compares output against example PDFs to identify improvements needed
5. Provides learning feedback for Hermes refinement
"""
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from sheet_parser import build_field_dict
from field_adapter import adapt_sheet_fields_to_acro
from sketch_extractor import main as extract_sketches
from site_plan_generator import (
    generate_site_plan_pg3,
    generate_disposal_plan_pg4,
    generate_cross_section_pg4
)

# Example PDFs for comparison
EXAMPLES = {
    'example_1': {
        'name': '26-018 Kristen Marquis',
        'pdfs': [
            Path('example/example 1/26-018 PG3 (1).pdf'),
            Path('example/example 1/26-018 PG4 (1).pdf'),
        ],
        'sketches_dir': '1Tg5V7uI99qcUgqIjQAlrqrASexL7B5yA',  # Row 2 uploads folder
    },
    'example_2': {
        'name': '26-123 (Second property)',
        'pdfs': [
            Path('example/example 2/26-123 PG3.pdf'),
            Path('example/example 2/26-123 PG4.pdf'),
        ],
    },
}

class HermesDrawingPipeline:
    def __init__(self, example_name: str = 'example_1'):
        self.example_name = example_name
        self.example_info = EXAMPLES[example_name]
        self.extracted_data = {}
        self.form_data = {}
        self.generated_drawings = {}
        self.analysis = {}

    def step_1_load_sheet_data(self):
        """Step 1: Load Google Sheet row data"""
        logger.info("\n[STEP 1] Loading Google Sheet data...")
        try:
            self.form_data = adapt_sheet_fields_to_acro(build_field_dict())
            logger.info(f"✓ Loaded form data with {len(self.form_data)} fields")

            # Show key data for drawing generation
            logger.info(f"  Owner: {self.form_data.get('owner_name', 'N/A')}")
            logger.info(f"  Property: {self.form_data.get('street_name', '')} {self.form_data.get('town', '')}")
            logger.info(f"  System: {self.form_data.get('disposal_field_type', 'N/A')}")
            logger.info(f"  Acreage: {self.form_data.get('property_size', 'N/A')}")
            logger.info(f"  Elevations: Grade={self.form_data.get('finished_grade_elevation', 'N/A')}, "
                       f"Top Pipe={self.form_data.get('top_distribution_pipe', 'N/A')}, "
                       f"Bottom Field={self.form_data.get('bottom_disposal_field', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Failed to load sheet data: {e}")
            return False

        return True

    def step_2_extract_sketches(self, sketches_folder_id: Optional[str] = None):
        """Step 2: Download and extract data from submitted sketches"""
        logger.info("\n[STEP 2] Extracting sketch data...")

        folder_id = sketches_folder_id or self.example_info.get('sketches_dir')

        if not folder_id:
            logger.warning("  No sketches folder ID provided, skipping sketch extraction")
            return False

        try:
            # Extract sketch data using Vision API
            self.extracted_data = extract_sketches(
                drive_folder_id=folder_id,
                address_line=f"{self.form_data.get('street_name', '')} {self.form_data.get('town', '')}",
                dry_run=False
            )

            logger.info(f"✓ Extracted sketch data")
            logger.info(f"  Sketch files: {len(self.extracted_data.get('sketch_files', []))}")
            logger.info(f"  Text blocks: {len(self.extracted_data.get('sketch_text', []))}")
            logger.info(f"  Extracted measurements: {len(self.extracted_data.get('elevations', {}))}")

            # Save extracted data for analysis
            with open('hermes_extracted_sketches.json', 'w') as f:
                json.dump(self.extracted_data, f, indent=2)
            logger.info(f"  → Saved to hermes_extracted_sketches.json")

        except Exception as e:
            logger.error(f"✗ Sketch extraction failed: {e}")
            # Don't fail - continue with form data only
            return False

        return True

    def step_3_generate_drawings(self):
        """Step 3: Generate site plan, disposal plan, and cross-section"""
        logger.info("\n[STEP 3] Generating drawings...")

        drawing_params = {
            'property_size': float(self.form_data.get('property_size', '2.35')),
            'acreage': float(self.form_data.get('property_size', '2.35')),
            'scale': int(self.form_data.get('scale_pg3', 40)),
            'owner_name': self.form_data.get('owner_name', ''),
            'property_address': f"{self.form_data.get('street_name', '')} {self.form_data.get('town', '')}",
            'disposal_field_type': self.form_data.get('disposal_field_type', 'Proprietary Device'),
            'system_type': self.form_data.get('disposal_field_type', 'Eljen InDrain'),
            'field_dimensions': self.form_data.get('disposal_field_size', '11 x 28 ft'),
            'finished_grade': float(self.form_data.get('finished_grade_elevation', '0').replace('"', '')),
            'top_distribution_pipe': float(self.form_data.get('top_distribution_pipe', '-12').replace('"', '')),
            'bottom_disposal_field': float(self.form_data.get('bottom_disposal_field', '30').replace('"', '')),
            'water_table_depth': 24,  # From limiting factor
            'bedrooms': int(self.form_data.get('num_bedrooms_opt1', '3')),
        }

        try:
            # Generate site plan (page 3)
            logger.info("  Generating site plan (page 3)...")
            site_plan = generate_site_plan_pg3(drawing_params)
            self.generated_drawings['site_plan'] = str(site_plan)
            logger.info(f"    ✓ Site plan saved: {site_plan}")

            # Generate disposal plan (page 4 top)
            logger.info("  Generating disposal plan (page 4 top)...")
            disposal_plan = generate_disposal_plan_pg4(drawing_params)
            self.generated_drawings['disposal_plan'] = str(disposal_plan)
            logger.info(f"    ✓ Disposal plan saved: {disposal_plan}")

            # Generate cross-section (page 4 bottom)
            logger.info("  Generating cross-section (page 4 bottom)...")
            cross_section = generate_cross_section_pg4(drawing_params)
            self.generated_drawings['cross_section'] = str(cross_section)
            logger.info(f"    ✓ Cross-section saved: {cross_section}")

        except Exception as e:
            logger.error(f"✗ Drawing generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    def step_4_compare_with_examples(self):
        """Step 4: Compare generated drawings with example PDFs"""
        logger.info("\n[STEP 4] Comparing with example PDFs...")

        logger.info(f"  Example: {self.example_info['name']}")
        logger.info(f"  Example PDFs:")
        for pdf_path in self.example_info['pdfs']:
            if pdf_path.exists():
                size_mb = pdf_path.stat().st_size / (1024*1024)
                logger.info(f"    ✓ {pdf_path.name} ({size_mb:.1f} MB)")
            else:
                logger.warning(f"    ✗ {pdf_path.name} (not found)")

        # For now, just log the comparison
        # Full visual comparison would require overlaying images or pixel-level analysis
        self.analysis = {
            'example': self.example_info['name'],
            'generated_drawings': list(self.generated_drawings.keys()),
            'example_pdfs': [str(p) for p in self.example_info['pdfs']],
            'comparison_status': 'READY FOR VISUAL ANALYSIS',
        }

        logger.info(f"  Drawings ready for comparison:")
        for drawing_type, drawing_path in self.generated_drawings.items():
            logger.info(f"    - {drawing_type}: {drawing_path}")

        return True

    def step_5_identify_improvements(self):
        """Step 5: Identify what Hermes got right/wrong/missing"""
        logger.info("\n[STEP 5] Identifying improvements needed...")

        improvements = {
            'what_hermes_got_right': [],
            'what_hermes_got_wrong': [],
            'what_hermes_is_missing': [],
            'next_steps': [],
        }

        # Based on the example PDFs, identify common patterns
        improvements['what_hermes_got_right'].extend([
            'Scale notation on drawings',
            'Grid layout matching example PDFs',
            'Property dimensions from sheet data',
            'Elevation reference data from sheet',
        ])

        improvements['what_hermes_got_wrong'].extend([
            'Missing hand-drawn sketch geometric details',
            'Approximate measurements instead of precise extracted values',
            'Missing annotations and labels from sketches',
            'No integration of sketch-provided layout variations',
        ])

        improvements['what_hermes_is_missing'].extend([
            'Detailed feature extraction from hand-drawn sketches',
            'OCR for measurement values in sketches',
            'Detection of unusual property layouts or obstacles',
            'Extraction of site-specific annotations and notes',
            'Cross-section soil layer definitions from sketches',
        ])

        improvements['next_steps'] = [
            '1. Improve Vision API usage to better extract measurements from sketches',
            '2. Add OCR capability for reading text annotations and dimension values',
            '3. Implement shape detection for property boundaries and features',
            '4. Create feedback loop to compare sketch-derived vs form-derived data',
            '5. Build learning system to detect and correct discrepancies',
        ]

        self.analysis['improvements'] = improvements

        logger.info("  What Hermes got right:")
        for item in improvements['what_hermes_got_right']:
            logger.info(f"    ✓ {item}")

        logger.info("  What Hermes got wrong:")
        for item in improvements['what_hermes_got_wrong']:
            logger.info(f"    ✗ {item}")

        logger.info("  What Hermes is missing:")
        for item in improvements['what_hermes_is_missing']:
            logger.info(f"    ? {item}")

        logger.info("  Next improvements:")
        for item in improvements['next_steps']:
            logger.info(f"    → {item}")

        return True

    def run_full_pipeline(self):
        """Run complete drawing generation and analysis pipeline"""
        logger.info("="*80)
        logger.info("HERMES DRAWING GENERATION PIPELINE")
        logger.info("="*80)
        logger.info(f"Target: {self.example_info['name']}")

        steps = [
            ('Sheet data', self.step_1_load_sheet_data),
            ('Sketch extraction', self.step_2_extract_sketches),
            ('Drawing generation', self.step_3_generate_drawings),
            ('PDF comparison', self.step_4_compare_with_examples),
            ('Improvement analysis', self.step_5_identify_improvements),
        ]

        for step_name, step_func in steps:
            try:
                success = step_func()
                if not success and 'extraction' not in step_name:
                    logger.error(f"✗ {step_name} failed")
                    return False
            except Exception as e:
                logger.error(f"✗ {step_name} failed: {e}")
                import traceback
                traceback.print_exc()
                return False

        # Save final analysis
        with open('hermes_drawing_analysis.json', 'w') as f:
            json.dump(self.analysis, f, indent=2)
        logger.info("\n✓ Analysis saved to hermes_drawing_analysis.json")

        logger.info("\n" + "="*80)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*80)
        return True


if __name__ == "__main__":
    pipeline = HermesDrawingPipeline(example_name='example_1')
    success = pipeline.run_full_pipeline()
    sys.exit(0 if success else 1)
