#!/usr/bin/env python3
"""
Test Harness: Read Row 2 → Generate Hermes Output → Run Pipeline

Simpler version that uses pre-loaded data and generates hermes_output.json
"""

import json
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("/home/workspace/OpenEvaluator")
HERMES_OUTPUT_FILE = OUTPUT_DIR / "hermes_output.json"
PIPELINE_SCRIPT = OUTPUT_DIR / "run_pipeline_with_hermes_complete.py"

def generate_hermes_output():
    """Generate hermes_output.json with test data from Row 2"""

    # This is the test data for Row 2 (26-018 Turner property)
    hermes_output = {
        "metadata": {
            "submission_id": "26-018-2026-05-31",
            "submission_date": "2026-05-31",
            "document_type": "HHE-200",
            "version": "2025"
        },
        "property": {
            "address": "17 Aspen Way, Turner, Maine 04282",
            "map_number": "26",
            "lot_number": "18",
            "acreage": 2.35,
            "county": "Androscoggin",
            "township": "Turner",
            "lot_corners": [
                {"label": "NW", "x": 0, "y": 0},
                {"label": "NE", "x": 200, "y": 0},
                {"label": "SE", "x": 200, "y": 150},
                {"label": "SW", "x": 0, "y": 150}
            ],
            "roads": [
                {"name": "ASPEN", "side": "north", "distance_ft": 25},
                {"name": "161", "side": "east", "distance_ft": 0}
            ]
        },
        "site_evaluator": {
            "name": "George Bouchles",
            "email": "george.bouchles@example.com",
            "phone": "207-555-0123",
            "license_number": "LS-12345"
        },
        "client": {
            "name": "Smith Family Trust",
            "address": "17 Aspen Way, Turner, Maine 04282",
            "phone": "207-555-0456",
            "email": "smith.family@example.com"
        },
        "existing_structures": [
            {
                "name": "DWELLING",
                "type": "house",
                "position_x": 50,
                "position_y": 40,
                "width_ft": 30,
                "length_ft": 40,
                "roof_style": "gable"
            },
            {
                "name": "GARAGE",
                "type": "garage",
                "position_x": 85,
                "position_y": 50,
                "width_ft": 20,
                "length_ft": 24
            },
            {
                "name": "DECK",
                "type": "deck",
                "position_x": 60,
                "position_y": 85,
                "width_ft": 15,
                "length_ft": 12
            }
        ],
        "water_supply": {
            "type": "drilled_well",
            "position_x": 20,
            "position_y": 30,
            "depth_ft": 125,
            "depth_to_water_ft": 45,
            "water_tested": True,
            "test_date": "2026-05-15",
            "test_results": "Passed - Suitable for use"
        },
        "soil_observations": {
            "general_notes": "Well-drained FSL soil suitable for septic system. Groundwater observed at 24 inches in test hole 1.",
            "groundwater_depth_in": 24,
            "limiting_factors": "Groundwater depth is the limiting factor for septic system design.",
            "organic_horizon_thickness_in": 2,
            "texture_description": "Fine Sandy Loam (FSL) throughout profile"
        },
        "septic_system": {
            "tank": {
                "position_x": 120,
                "position_y": 80,
                "capacity_gallons": 1000,
                "dimensions": {
                    "length": 5,
                    "width": 3,
                    "height": 4,
                    "unit": "feet"
                }
            },
            "disposal_field": {
                "position_x": 140,
                "position_y": 50,
                "type": "Eljen GSF-B43",
                "orientation": "N-S",
                "rows": 3,
                "modules_per_row": 7,
                "total_modules": 21,
                "module_spacing_ft": 1.5,
                "row_spacing_ft": 3.5
            }
        },
        "observation_holes": [
            {
                "hole_number": 1,
                "position_x": 130,
                "position_y": 70,
                "depth_ft": 36,
                "organic_horizon_thickness_in": 2,
                "ground_surface_elevation": 0,
                "soil_layers": [
                    {
                        "depth_start_in": 0,
                        "depth_end_in": 3,
                        "color": "Brown",
                        "texture": "FSL",
                        "consistence": "Friable",
                        "redox_features": ""
                    },
                    {
                        "depth_start_in": 3,
                        "depth_end_in": 24,
                        "color": "Yellowish Brown",
                        "texture": "FSL",
                        "consistence": "Friable",
                        "redox_features": ""
                    },
                    {
                        "depth_start_in": 24,
                        "depth_end_in": 36,
                        "color": "Olive Gray",
                        "texture": "FSL",
                        "consistence": "Friable",
                        "redox_features": "Mottled"
                    }
                ]
            },
            {
                "hole_number": 2,
                "position_x": 160,
                "position_y": 70,
                "depth_ft": 36,
                "organic_horizon_thickness_in": 2,
                "ground_surface_elevation": -2,
                "soil_layers": [
                    {
                        "depth_start_in": 0,
                        "depth_end_in": 4,
                        "color": "Brown",
                        "texture": "FSL",
                        "consistence": "Friable",
                        "redox_features": ""
                    },
                    {
                        "depth_start_in": 4,
                        "depth_end_in": 24,
                        "color": "Brown",
                        "texture": "SL",
                        "consistence": "Friable",
                        "redox_features": ""
                    },
                    {
                        "depth_start_in": 24,
                        "depth_end_in": 36,
                        "color": "Gray",
                        "texture": "SL",
                        "consistence": "Friable",
                        "redox_features": "Mottled"
                    }
                ]
            }
        ],
        "elevation_data": {
            "reference_point": {
                "description": "Nail in 6\" maple tree",
                "position_x": 45,
                "position_y": 35,
                "height_above_grade_in": 12
            },
            "grade_elevations": [
                {"location": "house", "elevation_ft": 120.0},
                {"location": "tank", "elevation_ft": 119.5},
                {"location": "field", "elevation_ft": 119.0}
            ],
            "limiting_factor": {
                "type": "groundwater",
                "depth_in": 24,
                "location": "observed in hole 1"
            }
        },
        "contour_lines": [
            {
                "elevation_ft": 120,
                "points": [[0,0], [50,5], [100,10], [150,8], [200,5]]
            },
            {
                "elevation_ft": 119,
                "points": [[0,50], [50,55], [100,60], [150,58], [200,55]]
            },
            {
                "elevation_ft": 118,
                "points": [[0,100], [50,105], [100,110], [150,108], [200,105]]
            }
        ],
        "setback_requirements": {
            "well_setback_ft": 75,
            "property_line_setback_ft": 10,
            "road_setback_ft": 50,
            "water_body_setback_ft": 100,
            "dwelling_setback_ft": 30,
            "estimated_setback_ft": 75,
            "setback_limiting_factor": "Property line setback"
        },
        "designer_notes": "Septic system designed per Maine HHE-200 standards. All setback requirements met. Groundwater at 24 inches depth. System designed for 4-bedroom dwelling."
    }

    return hermes_output

def main():
    logger.info("=" * 80)
    logger.info("OpenEvaluator Test Harness — Full Pipeline Execution")
    logger.info("=" * 80)

    # Generate Hermes Output
    logger.info("\n[Step 1/2] Generating hermes_output.json...")
    hermes_output = generate_hermes_output()

    try:
        with open(HERMES_OUTPUT_FILE, 'w') as f:
            json.dump(hermes_output, f, indent=2)
        logger.info(f"✓ Saved: {HERMES_OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to save hermes_output.json: {e}")
        return 1

    # Run Pipeline
    logger.info("\n[Step 2/2] Running full pipeline...")
    logger.info(f"Pipeline: {PIPELINE_SCRIPT}")
    logger.info("-" * 80)

    try:
        result = subprocess.run(
            ['python3', str(PIPELINE_SCRIPT)],
            cwd=str(OUTPUT_DIR),
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            logger.info("-" * 80)
            logger.info("✓ Pipeline completed successfully!")
            logger.info("\n" + "=" * 80)
            logger.info("TEST COMPLETE")
            logger.info("=" * 80)
            logger.info("\nCheck the output:")
            logger.info("1. HHE-200-filled.pdf — The completed form")
            logger.info("2. disposal_plan_pg4.png — Site plan on page 4")
            logger.info("3. cross_section_pg4.png — Cross section on page 4")
            return 0
        else:
            logger.error("Pipeline failed")
            return 1

    except Exception as e:
        logger.error(f"Failed to run pipeline: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
