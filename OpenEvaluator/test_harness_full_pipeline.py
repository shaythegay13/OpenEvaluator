#!/usr/bin/env python3
"""
Test Harness: Read Row 2 from Google Sheet → Generate Hermes Output → Run Full Pipeline

This script:
1. Reads the test row (Row 2) from the Google Sheet
2. Downloads the document from column T
3. Generates hermes_output.json with both sheet data and document data
4. Runs the full pipeline to produce the final PDF
5. Reports success/failure with detailed logging
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

SHEET_ID = "1VHJq0vBMGrme-wmHuPooko0G5JpbfP_o1ZeozjEZ94M"
TEST_ROW = 2
TOKENS_FILE = "/home/workspace/Projects/memory-os/backend/tokens.json"
OUTPUT_DIR = Path("/home/workspace/OpenEvaluator")
HERMES_OUTPUT_FILE = OUTPUT_DIR / "hermes_output.json"
PIPELINE_SCRIPT = OUTPUT_DIR / "run_pipeline_with_hermes_complete.py"

# ============================================================================
# Step 1: Read Google Sheet Row 2
# ============================================================================

def read_google_sheet_row(sheet_id: str, row_num: int) -> Dict[str, Any]:
    """Read a single row from Google Sheet and extract all fields"""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google.api_client import discovery
        import google.auth

        logger.info(f"Reading Google Sheet Row {row_num}...")

        # Load credentials from tokens.json
        if not Path(TOKENS_FILE).exists():
            logger.error(f"tokens.json not found at {TOKENS_FILE}")
            return {}

        with open(TOKENS_FILE, 'r') as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data)

        # Build Sheets API client
        service = discovery.build('sheets', 'v4', credentials=creds)

        # Read the entire row
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"Sheet1!A{row_num}:T{row_num}"
        ).execute()

        values = result.get('values', [[]])[0]

        # Parse into dictionary
        row_data = {
            'site_evaluator_name': values[0] if len(values) > 0 else '',
            'site_evaluator_email': values[1] if len(values) > 1 else '',
            'site_evaluator_phone': values[2] if len(values) > 2 else '',
            'site_evaluator_license': values[3] if len(values) > 3 else '',
            'client_name': values[4] if len(values) > 4 else '',
            'client_address': values[5] if len(values) > 5 else '',
            'client_phone': values[6] if len(values) > 6 else '',
            'client_email': values[7] if len(values) > 7 else '',
            'property_address': values[8] if len(values) > 8 else '',
            'map_number': values[9] if len(values) > 9 else '',
            'lot_number': values[10] if len(values) > 10 else '',
            'acreage': values[11] if len(values) > 11 else '0',
            'county': values[12] if len(values) > 12 else '',
            'township': values[13] if len(values) > 13 else '',
            'section': values[14] if len(values) > 14 else '',
            'notes': values[15] if len(values) > 15 else '',
            'project_status': values[16] if len(values) > 16 else '',
            'updated_date': values[17] if len(values) > 17 else '',
            'document_link': values[18] if len(values) > 18 else '',
        }

        logger.info("✓ Sheet data read successfully")
        logger.info(f"  - Client: {row_data['client_name']} at {row_data['client_address']}")
        logger.info(f"  - Property: {row_data['property_address']} (Map {row_data['map_number']}, Lot {row_data['lot_number']})")
        logger.info(f"  - Evaluator: {row_data['site_evaluator_name']}")

        return row_data

    except Exception as e:
        logger.error(f"Failed to read Google Sheet: {e}")
        return {}

# ============================================================================
# Step 2: Download Document from Google Drive
# ============================================================================

def download_document_from_drive(document_link: str, output_path: Path) -> bool:
    """Download document from Google Drive using the shared link"""
    try:
        if not document_link:
            logger.warning("No document link provided, skipping download")
            return False

        logger.info(f"Downloading document from: {document_link[:50]}...")

        # Convert sharing link to download link
        if 'drive.google.com' in document_link:
            file_id = document_link.split('/d/')[1].split('/')[0]
            download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

            import subprocess
            result = subprocess.run(
                ['wget', '-q', '-O', str(output_path), download_url],
                capture_output=True
            )

            if result.returncode == 0 and output_path.exists():
                logger.info(f"✓ Document downloaded: {output_path}")
                return True
            else:
                logger.error(f"Failed to download document: {result.stderr.decode()}")
                return False
        else:
            logger.warning("Invalid document link format")
            return False

    except Exception as e:
        logger.error(f"Document download failed: {e}")
        return False

# ============================================================================
# Step 3: Generate Hermes Output (Combined Sheet + Document Data)
# ============================================================================

def generate_hermes_output(sheet_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate hermes_output.json from sheet data"""

    logger.info("Generating hermes_output.json from sheet data...")

    # Use the test hermes_output.json structure, but override with sheet data
    hermes_output = {
        "property": {
            "address": sheet_data.get('property_address', '17 Aspen Way, Turner, Maine 04282'),
            "map_number": sheet_data.get('map_number', '26'),
            "lot_number": sheet_data.get('lot_number', '18'),
            "acreage": float(sheet_data.get('acreage', '2.35')),
            "county": sheet_data.get('county', ''),
            "township": sheet_data.get('township', ''),
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
            "name": sheet_data.get('site_evaluator_name', ''),
            "email": sheet_data.get('site_evaluator_email', ''),
            "phone": sheet_data.get('site_evaluator_phone', ''),
            "license_number": sheet_data.get('site_evaluator_license', '')
        },
        "client": {
            "name": sheet_data.get('client_name', ''),
            "address": sheet_data.get('client_address', ''),
            "phone": sheet_data.get('client_phone', ''),
            "email": sheet_data.get('client_email', '')
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
            }
        ],
        "water_supply": {
            "type": "drilled_well",
            "position_x": 20,
            "position_y": 30,
            "depth_ft": 125
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
        }
    }

    logger.info("✓ Hermes output generated")
    return hermes_output

# ============================================================================
# Step 4: Save Hermes Output
# ============================================================================

def save_hermes_output(hermes_data: Dict[str, Any], output_file: Path) -> bool:
    """Save hermes_output.json"""
    try:
        logger.info(f"Saving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(hermes_data, f, indent=2)
        logger.info("✓ hermes_output.json saved")
        return True
    except Exception as e:
        logger.error(f"Failed to save hermes_output.json: {e}")
        return False

# ============================================================================
# Step 5: Run Pipeline
# ============================================================================

def run_pipeline() -> bool:
    """Execute the pipeline script"""
    try:
        logger.info(f"Running pipeline: {PIPELINE_SCRIPT}")

        result = subprocess.run(
            ['python3', str(PIPELINE_SCRIPT)],
            cwd=str(OUTPUT_DIR),
            capture_output=True,
            text=True
        )

        logger.info("Pipeline Output:")
        logger.info(result.stdout)

        if result.returncode == 0:
            logger.info("✓ Pipeline completed successfully")
            return True
        else:
            logger.error("Pipeline failed:")
            logger.error(result.stderr)
            return False

    except Exception as e:
        logger.error(f"Failed to run pipeline: {e}")
        return False

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Execute the full test harness"""
    logger.info("=" * 80)
    logger.info("OpenEvaluator Test Harness — Full Pipeline Test")
    logger.info("=" * 80)

    # Step 1: Read Sheet
    logger.info("\n[Step 1/4] Reading Google Sheet Row 2...")
    sheet_data = read_google_sheet_row(SHEET_ID, TEST_ROW)

    if not sheet_data.get('client_name'):
        logger.error("Failed to read sheet data")
        return 1

    # Step 2: Generate Hermes Output
    logger.info("\n[Step 2/4] Generating hermes_output.json...")
    hermes_output = generate_hermes_output(sheet_data)

    # Step 3: Save Hermes Output
    logger.info("\n[Step 3/4] Saving hermes_output.json...")
    if not save_hermes_output(hermes_output, HERMES_OUTPUT_FILE):
        return 1

    # Step 4: Run Pipeline
    logger.info("\n[Step 4/4] Running pipeline...")
    if not run_pipeline():
        return 1

    logger.info("\n" + "=" * 80)
    logger.info("✓ Test Harness Complete!")
    logger.info("=" * 80)
    logger.info("\nNext Steps:")
    logger.info("1. Check the generated PDF in /home/workspace/OpenEvaluator/")
    logger.info("2. Review pages 3-4 for CAD drawing placement")
    logger.info("3. Once working, configure Hermes to run this automatically")

    return 0

if __name__ == '__main__':
    sys.exit(main())
