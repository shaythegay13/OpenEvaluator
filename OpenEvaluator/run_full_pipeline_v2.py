#!/usr/bin/env python3
"""
Complete OpenEvaluator Pipeline v2
- Uses Hermes data (no fallback to test data)
- Generates dense grid drawings (16x30 = 480+ lines per page)
- Fills HHE-200 form with all data
- Produces high-quality PDF output for testing

Run: python3 run_full_pipeline_v2.py
"""

import json
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_hermes_data():
    """Load hermes_output.json"""
    path = Path('hermes_output.json')
    if not path.exists():
        logger.error("❌ hermes_output.json not found")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    logger.info(f"✅ Loaded hermes_output.json")
    logger.info(f"   Client: {data.get('client', {}).get('name')}")
    logger.info(f"   Property: {data.get('property', {}).get('address')}")

    return data


def generate_drawings(hermes_data):
    """Generate site plan and disposal plan drawings"""
    logger.info("\n[STEP 1] Generating professional CAD drawings...")

    try:
        from simple_dense_drawings import generate_simple_drawings

        result = generate_simple_drawings(hermes_data)

        if result['status'] != 'success':
            logger.error(f"❌ Drawing generation failed: {result.get('error')}")
            return None

        logger.info(f"✅ Generated DXF drawings")
        logger.info(f"   Page 3: {result['page3_path']}")
        logger.info(f"   Page 4: {result['page4_path']}")

        # Convert DXF to PNG for PDF embedding
        logger.info("\n[STEP 2] Converting DXF to PNG...")
        dxf_to_png_convert(result['page3_path'], 'site_plan_pg3.png')
        dxf_to_png_convert(result['page4_path'], 'disposal_plan_pg4.png')

        return result

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def dxf_to_png_convert(dxf_path, png_name):
    """Convert DXF to PNG"""
    try:
        import ezdxf
        from PIL import Image, ImageDraw

        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Determine dimensions based on content
        if 'site_plan' in png_name:
            width, height = 864, 666
        else:
            width, height = 1256, 636

        # Get bounds
        try:
            extents = msp.get_bounding_box()
            if extents:
                min_x, min_y, min_z = extents[0]
                max_x, max_y, max_z = extents[1]
            else:
                min_x, min_y = 0, 0
                max_x, max_y = 220, 280
        except:
            min_x, min_y = 0, 0
            max_x, max_y = 220, 280

        # Create image
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # Calculate scale
        model_width = max_x - min_x or 1
        model_height = max_y - min_y or 1
        scale_x = width / model_width * 0.95
        scale_y = height / model_height * 0.95
        scale = min(scale_x, scale_y)

        # Draw entities
        for entity in msp:
            try:
                if entity.dxftype() == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    x1 = (start[0] - min_x) * scale + 10
                    y1 = height - (start[1] - min_y) * scale - 10
                    x2 = (end[0] - min_x) * scale + 10
                    y2 = height - (end[1] - min_y) * scale - 10
                    draw.line([(x1, y1), (x2, y2)], fill='black', width=1)

                elif entity.dxftype() == 'LWPOLYLINE':
                    points = entity.get_points()
                    if len(points) > 1:
                        for i in range(len(points) - 1):
                            x1 = (points[i][0] - min_x) * scale + 10
                            y1 = height - (points[i][1] - min_y) * scale - 10
                            x2 = (points[i + 1][0] - min_x) * scale + 10
                            y2 = height - (points[i + 1][1] - min_y) * scale - 10
                            draw.line([(x1, y1), (x2, y2)], fill='black', width=1)

                elif entity.dxftype() == 'CIRCLE':
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    cx = (center[0] - min_x) * scale + 10
                    cy = height - (center[1] - min_y) * scale - 10
                    r = radius * scale
                    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline='black', width=1)
            except:
                pass

        img.save(png_name)
        logger.info(f"   ✓ {png_name}")

    except Exception as e:
        logger.error(f"   ✗ Error converting {dxf_path}: {e}")


def fill_form(hermes_data):
    """Fill HHE-200 form with Hermes data"""
    logger.info("\n[STEP 3] Filling HHE-200 form...")

    try:
        from acro_fill import fill_pdf_with_data

        # Extract comprehensive form data from Hermes
        prop = hermes_data.get('property', {})
        se = hermes_data.get('site_evaluator', {})
        client = hermes_data.get('client', {})
        tank = hermes_data.get('septic_system', {}).get('tank', {})
        field = hermes_data.get('septic_system', {}).get('disposal_field', {})
        soil = hermes_data.get('soil_observations', {})
        well = hermes_data.get('water_supply', {})
        obs_holes = hermes_data.get('observation_holes', [])

        # Parse address
        address_parts = (client.get('address', '') or '').split()
        street_num = address_parts[0] if address_parts else ''
        street_name = ' '.join(address_parts[1:3]) if len(address_parts) > 2 else ' '.join(address_parts[1:])

        form_data = {
            # Client/Owner info
            "owner_name": client.get('name', ''),
            "owner_phone": client.get('phone', ''),
            "owner_email": client.get('email', ''),
            "applicant_name": client.get('name', ''),
            "street_number": street_num,
            "street_name": street_name,
            "town": prop.get('township', ''),
            "mailing_city": prop.get('township', ''),

            # Property info
            "map_number": prop.get('map_number', ''),
            "lot_number": prop.get('lot_number', ''),

            # Evaluator info
            "evaluator_name": se.get('name', ''),
            "evaluator_phone": se.get('phone', ''),
            "se_number": se.get('license_number', ''),

            # Well/Water supply
            "well_type": well.get('type', ''),
            "well_depth": str(well.get('depth_ft', '')),
            "groundwater_depth": str(well.get('depth_to_water_ft', '')),
            "well_tested": "Yes" if well.get('water_tested') else "No",

            # Tank info
            "tank_capacity": str(tank.get('capacity_gallons', '')),
            "tank_type": tank.get('tank_type', ''),
            "tank_cap_gal": str(tank.get('capacity_gallons', '')),
            "treatment_tanks": str(tank.get('capacity_gallons', '')),

            # Disposal field
            "disposal_field_type": field.get('type', ''),
            "disposal_field_modules": str(field.get('total_modules', '')),
            "non_eng_field_check": "On",

            # Soil observations
            "soil_general_notes": soil.get('general_notes', ''),
            "soil_texture": soil.get('texture_description', ''),
            "organic_horizon": str(soil.get('organic_horizon_thickness_in', '')),
            "groundwater_limiting_factor": soil.get('limiting_factors', ''),

            # Setback
            "estimated_setback": str(hermes_data.get('setback_requirements', {}).get('estimated_setback_ft', '')),

            # Designer notes
            "designer_notes": hermes_data.get('designer_notes', ''),
        }

        # Add observation hole data
        for i, hole in enumerate(obs_holes[:3]):  # Max 3 holes
            idx = i + 1
            form_data.update({
                f'oh{idx}_depth': str(hole.get('depth_ft', '')),
                f'oh{idx}_limiting_factor': hole.get('observations', ''),
            })

            # Add soil layers
            soil_layers = hole.get('soil_layers', [])
            for j, layer in enumerate(soil_layers[:6]):  # Max 6 layers
                form_data.update({
                    f'oh{idx}_layer{j+1}_depth': str(layer.get('depth_in', '')),
                    f'oh{idx}_layer{j+1}_texture': layer.get('texture', ''),
                    f'oh{idx}_layer{j+1}_color': layer.get('color', ''),
                })

        output_pdf = fill_pdf_with_data(form_data)
        logger.info(f"✅ Filled HHE-200 form")
        logger.info(f"   Output: {output_pdf}")

        return output_pdf

    except Exception as e:
        logger.error(f"❌ Error filling form: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_assessment(output_pdf):
    """Run quality assessment"""
    logger.info("\n[STEP 4] Running quality assessment...")

    try:
        from comprehensive_assessment import generate_quality_report

        example_dir = Path("/home/workspace/OpenEvaluator/example")
        example_pdfs = list(example_dir.glob("26-018 PG*.pdf"))

        report = generate_quality_report(Path(output_pdf), example_pdfs)

        logger.info(f"\n✅ Assessment Complete")
        logger.info(f"   Overall Score: {report.get('overall_score', 0)}/100")
        logger.info(f"   Status: {report.get('status')}")

        return report

    except Exception as e:
        logger.error(f"❌ Assessment error: {e}")
        return None


def main():
    logger.info("=" * 70)
    logger.info("OpenEvaluator - Complete Pipeline v2")
    logger.info("=" * 70)

    # Load Hermes data
    hermes_data = load_hermes_data()

    # Generate drawings
    drawings = generate_drawings(hermes_data)
    if not drawings:
        sys.exit(1)

    # Fill form
    output_pdf = fill_form(hermes_data)
    if not output_pdf:
        sys.exit(1)

    # Assessment
    report = run_assessment(output_pdf)

    logger.info("\n" + "=" * 70)
    logger.info("Pipeline Complete")
    logger.info("=" * 70)
    logger.info(f"Output PDF: {output_pdf}")
    logger.info(f"Quality Score: {report.get('overall_score', 0)}/100" if report else "Assessment failed")


if __name__ == '__main__':
    main()
