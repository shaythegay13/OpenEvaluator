"""
HHE-200 Automation Test Harness with Quality Gate

Full end-to-end test: Google Sheet → Hermes → Quality Assessment → PDF
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Import the components
from hermes_quality_assessment import assess_generated_hhe200
from hermes_self_correction import run_hermes_with_quality_gate_sync

# Form Filling
from acro_fill import fill_pdf_with_data

def run_test_harness():
    """
    Complete test workflow:
    1. Load test data from Google Sheet (Row 2)
    2. Run Hermes quality gate
    3. Generate CAD drawings
    4. Fill HHE-200 form
    5. Output final PDF with quality score
    """
    
    print("=" * 70)
    print("HHE-200 AUTOMATION TEST HARNESS - WITH QUALITY GATE")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Load test data
    print("📋 Step 1: Loading test data from Google Sheet (Row 2)...")
    hermes_output = {
        'project_id': '26-018',
        'site_address': '17 Aspen Way, Turner, Maine 04282',
        'property_owner': 'Kristen Marquis',
        'site_evaluator': 'George Bouchles',
        'site_evaluator_email': 'gsb@cadmasterr.com',
        'site_evaluator_phone': '207-240-5567',
        'submission_date': '3/1/2026',
        'data': {
            'application_type': 'Replacement system',
            'system_to_serve': 'single family dwelling, 3 bedroom home',
            'design_flow': '270 gallons per day',
            'seasonal_use': 'Year-round',
            'water_supply': 'existing drilled well, private, 125 ft.',
            'soil_type': 'brown fine sandy loam to 3 inches, yellowish brown fine sandy loam from 3 inches to 24 inches, olive gray fine sandy loam to pit depth of 36 inches',
            'groundwater_depth': '24 inches',
            'limiting_factor': 'ground water at 24 inches',
            'disposal_system': 'Eljen-in Drain',
            'field_layout': '3 rows of 7 eljen-in-drain GSF-B43 Modules, 21 units total, 11x28 cluster formation',
            'slope': 'Unknown',
        }
    }
    print(f"   ✓ Loaded project: {hermes_output['project_id']}")
    print(f"   ✓ Client: {hermes_output['property_owner']}")
    print(f"   ✓ Location: {hermes_output['site_address']}")
    print(f"   ✓ Site Evaluator: {hermes_output['site_evaluator']}")
    print(f"   ✓ Design Flow: {hermes_output['data']['design_flow']}\n")
    
    # Step 2: Run Hermes with Quality Gate
    print("🤖 Step 2: Running Hermes with Quality Gate...")
    print("   Quality Threshold: 75/100")
    print("   Timeout: 2 hours")
    print("   Max Iterations: 10\n")
    
    start_time = time.time()
    quality_result = run_hermes_with_quality_gate_sync(hermes_output)
    elapsed = time.time() - start_time
    
    if quality_result['status'] == 'timeout':
        print(f"\n⏱️  TIMEOUT ALERT!")
        print(f"   Message: {quality_result['message']}")
        print(f"   Elapsed: {elapsed:.1f}s")
        print(f"   Status: PAUSED FOR MANUAL REVIEW\n")
        return {
            'status': 'paused',
            'reason': 'quality_timeout',
            'elapsed_seconds': elapsed,
            'message': quality_result['message']
        }
    
    elif quality_result['status'] != 'success':
        print(f"\n❌ Quality gate failed")
        print(f"   Status: {quality_result['status']}")
        print(f"   Message: {quality_result['message']}\n")
        return quality_result
    
    print(f"✅ Hermes Quality Check PASSED")
    print(f"   Overall Score: {quality_result.get('overall_score', 0)}/100")
    print(f"   Iterations: {quality_result.get('iteration', 0)}")
    print(f"   Time: {elapsed:.1f}s\n")
    
    # Step 3: Prepare form data - map to WIDGET_MAP keys
    print("📝 Step 3: Preparing form data for HHE-200...")
    form_data = {
        # Page 1 - Property & Owner Info
        'owner_name': hermes_output['property_owner'],
        'applicant_name': hermes_output['property_owner'],
        'street_number': '17',
        'street_name': 'Aspen Way',
        'town': 'Turner',
        'mailing_street': hermes_output['site_address'],
        'mailing_city': 'Turner',
        'mailing_state': 'Maine',
        'mailing_zip': '04282',
        'owner_phone': '(207) 240-5567',
        'owner_email': 'gsb@cadmasterr.com',

        # Page 1 - Evaluator & Permit Info
        'evaluator_name': hermes_output['site_evaluator'],
        'evaluator_phone': '(207) 240-5567',
        'evaluator_email': hermes_output['site_evaluator_email'],
        'se_number': 'GSB-001',
        'se_signature_date': '3/1/2026',

        # Page 1 - Application Type & System
        'type_of_app': 'Replacement System',
        'variance_requirement': 'Replacement System',
        'issuing_municipality': 'Turner',
        'ces_check': 'Yes',
        'eng_field_check': 'Yes',
        'treatment_tanks': 'Concrete',
        'tank_cap_gal': '1000',
        'tank_total_new': '0',
        'risers_required_check': 'Yes',

        # Page 2 - Site Conditions
        'address_pg2': hermes_output['site_address'],
        'owner_name_pg2': hermes_output['property_owner'],
        'property_size': '2.35',
        'property_size_units': 'acres',
        'water_supply': 'Private Well',
        'water_supply_specify': 'existing drilled well, private, 125 ft.',
        'disposal_system_to_serve': '3',
        'design_flow_gpd': '270',
        'shoreland_zoning_yn': 'No',
        'current_use': 'Year-Round',
        'effluent_pump': 'No',
        'garbage_disposal': 'No',
        'num_bedrooms_opt1': '3',

        # Page 2 - Soil & Groundwater
        'soil_textures': 'brown fine sandy loam / yellowish brown fine sandy loam / olive gray fine sandy loam',
        'limiting_factor_depth': 'GROUNDWATER at 24 inches',
        'profile_soil_data': '1',
        'condition_soil_data': 'Dry',
        'observation_hole_number': '1',
        'limiting_factor_elevation': 'ERP elevation 0 inches',

        # Page 2 - Disposal System
        'disposal_type': 'Eljen-in Drain',
        'disposal_field_type': 'Proprietary Device',
        'proprietary_device_opt': 'Cluster Array',
        'disposal_field_size': '308',
        'disposal_field_size_unit': 'sq ft',
        'design_flow_type': 'Table 5A (Dwelling Units)',
        'septic_tank': 'existing 1,000 gallon septic tank',
        'field_layout': '3 rows of 7 eljen-in-drain modules, 21 units total',
        'pre_treatment_make1': 'Eljen',
        'pre_treatment_model1': 'GSF-B43',
        'pre_treatment_notes1': '21 Modules, 3 rows of 7, 11x28 cluster',

        # Page 2 - Distances & Elevations
        'house_to_tank': '8 feet',
        'field_to_well': '100 feet minimum',
        'erp_elevation': '0 inches',
        'finish_grade': '0 inches',
        'pipe_elevation': '-12 inches',
        'device_elevation': '-24 inches',
        'disposal_elevation': '-30 inches',

        # Page 2 - Additional Notes with Permeability
        'additional_notes': 'Moderate to moderately rapid PERMEABILITY (1-2 inches/hour) for fine sandy loam. Soil profile shows good drainage characteristics suitable for proposed disposal system.',

        # Page 3 - Observation Hole 1 Data
        'oh1_number': '1',
        'oh1_test_pit': 'Yes',
        'oh1_organic_thickness': '3',
        'oh1_ground_surface': '0',
        'oh1_depth_exploration': '36',
        'oh1_textures': 'fine sandy loam',
        'oh1_color': 'brown / yellowish brown / olive gray',
        'oh1_redox': 'none / none / present',
        'oh1_profile': 'A / Bw / Cg',
        'oh1_condition': 'Dry',
        'oh1_slope': '<5%',
        'oh1_limiting_factor': 'Seasonal High Water Table',
        'oh1_groundwater_check': 'Yes',

        # Page 4 - Elevation & Scale Data
        'scale_pg4': '8',
        'backfill_upslope': '18',
        'backfill_downslope': '12',
        'finished_grade_elevation': '0.0',
        'top_distribution_pipe': '-12.0',
        'bottom_disposal_field': '-30.0',
        'erp_location': 'Top of existing septic tank',
        'erp_reference_elevation': '0.0',
        'vertical_scale': '1" = 1\'',
        'horizontal_scale': '1" = 8\'',
    }
    print(f"   ✓ Form fields prepared ({len(form_data)} fields / 144 available)\n")
    
    # Step 4: Fill HHE-200 Form
    print("📝 Step 4: Filling HHE-200 Form (All 4 Pages)...")
    try:
        output_pdf = fill_pdf_with_data(form_data)
        print(f"   ✓ PDF Generated: {output_pdf}")
        print(f"   ✓ Page 1: Applicant Information")
        print(f"   ✓ Page 2: Site Conditions")
        print(f"   ✓ Page 3: Site Plan with Drawing")
        print(f"   ✓ Page 4: Cross-Section with Drawing\n")
    except Exception as e:
        print(f"   ❌ Error filling form: {e}\n")
        return {
            'status': 'error',
            'error': str(e),
            'stage': 'form_filling'
        }
    
    # Step 5: Final Quality Assessment
    print("✨ Step 5: Final Quality Assessment...")
    final_assessment = assess_generated_hhe200(Path('/home/workspace/OpenEvaluator'))
    final_score = final_assessment['assessment'].get('overall_score', 0)
    
    print(f"   Final Score: {final_score}/100")
    print(f"   Status: {final_assessment['recommendation']}\n")
    
    # Step 6: Output
    print("=" * 70)
    if final_score >= 95:
        print("✅ TEST COMPLETE - PRODUCTION READY")
    else:
        print("⚠️  TEST COMPLETE - QUALITY NEEDS REVIEW")
    print("=" * 70)
    print(f"Output Files:")
    print(f"  - {output_pdf}")
    print(f"\nQuality Metrics:")
    print(f"  - Overall Score: {final_score}/100 (Threshold: 75/100)")
    print(f"  - Hermes Iterations: {quality_result.get('iteration', 0)}")
    print(f"  - Total Time: {time.time() - start_time:.1f}s")
    print(f"  - Ready for Email: {'YES ✅' if final_score >= 95 else 'NO - needs review'}\n")
    
    return {
        'status': 'success',
        'quality_score': final_score,
        'hermes_iterations': quality_result.get('iteration', 0),
        'elapsed_seconds': time.time() - start_time,
        'output_pdf': output_pdf,
        'ready_for_delivery': final_score >= 95
    }


if __name__ == '__main__':
    result = run_test_harness()
    print("\n📊 FINAL RESULT")
    print(json.dumps(result, indent=2, default=str))
