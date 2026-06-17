#!/usr/bin/env python3
"""
Parse field_map.yaml and provide coordinate lookups for drawing field values on PDF.
Coordinates are in 72dpi PDF points.
"""

from typing import Dict, Tuple, Optional

# Manually extracted from field_map.yaml - maps logical field name to (page, x, y, font_size, max_length)
FIELD_COORDS: Dict[str, Tuple[int, float, float, int, int]] = {
    # PAGE 1 - Contact & Address Info
    'site_address': (1, 187, 92, 9, 40),
    'permit_number': (1, 390, 95.9, 9, 20),
    'date_issued': (1, 520, 95.9, 9, 20),
    'town': (1, 209, 106, 9, 30),
    'issuing_municipality': (1, 321, 74, 9, 30),
    'municipal_tax_map': (1, 158, 122, 9, 15),
    'lot_number': (1, 262, 122, 9, 15),
    'lpi_number': (1, 552, 122, 9, 15),
    'owner_name': (1, 162, 152, 9, 40),
    'applicant_name': (1, 200, 166, 9, 40),
    'mailing_street': (1, 140, 200, 9, 40),
    'mailing_city': (1, 94, 213, 9, 25),
    'mailing_state': (1, 206, 215, 9, 10),
    'mailing_zip': (1, 259, 215, 9, 10),
    'phone': (1, 117, 226, 9, 20),
    'email': (1, 119, 245, 9, 50),
    'owner_applicant_statement': (1, 461, 155, 9, 60),
    'property_owner_signature': (1, 155, 318, 9, 40),
    'property_owner_date': (1, 249, 318, 9, 20),
    'installer_name': (1, 52, 349, 9, 40),
    'installer_phone': (1, 190, 349, 9, 20),

    # PAGE 2 - Property & System Info
    'lot_size_sqft': (2, 131, 94, 9, 12),
    'lot_size_acres': (2, 142, 92, 9, 12),
    'shoreland_zoning': (2, 91, 110, 9, 20),
    'system_to_serve': (2, 261, 96, 9, 30),
    'design_flow_gallons': (2, 432, 95, 9, 10),
    'num_bedrooms': (2, 361, 104, 9, 5),
    'current_use': (2, 92, 157, 9, 30),
    'water_supply_type': (2, 67, 289, 9, 25),
    'disposal_field_type': (2, 270, 264, 9, 25),
    'dose_gallons': (2, 259, 346, 9, 10),
    'garbage_disposal_unit': (2, 100, 377, 9, 10),
    'evaluator_name': (2, 292, 716, 9, 40),
    'evaluator_license_number': (2, 455, 692, 9, 20),

    # PAGE 3 - Site Plan & Soil Profile
    'site_plan_scale': (3, 50, 76, 9, 20),
    'site_location_map_scale': (3, 503, 80, 9, 20),
    'oh1_organic_thickness': (3, 78, 441, 9, 10),
    'oh1_ground_surface_elevation': (3, 154, 441, 9, 10),
    'oh1_depth_to_exploration': (3, 134, 453, 9, 10),
    'oh2_organic_thickness': (3, 336, 442, 9, 10),
    'oh2_ground_surface_elevation': (3, 440, 441, 9, 10),
    'oh2_depth_to_exploration': (3, 420, 453, 9, 10),
    'deepest_restrictive_layer_hole1': (3, 52, 602, 9, 30),
    'deepest_restrictive_layer_hole2': (3, 187, 688, 9, 30),
    'water_table_depth_hole1': (3, 21, 703, 9, 10),
    'water_table_depth_hole2': (3, 468, 725, 9, 10),
    'bedrock_depth_hole1': (3, 203, 703.9, 9, 10),
    'bedrock_depth_hole2': (3, 496, 703.9, 9, 10),
    'soil_classification_hole1': (3, 52, 602, 9, 15),
    'soil_classification_hole2': (3, 187, 688, 9, 15),
    'slope_hole1': (3, 339, 564, 9, 8),
    'slope_hole2': (3, 339, 576, 9, 8),
    'evaluator_name_page3': (3, 175, 677, 9, 40),
    'evaluator_se_number': (3, 506, 676, 9, 15),
    'evaluator_date_page3': (3, 288, 701, 9, 20),
    'setback_well': (3, 450, 124.3, 9, 15),
    'setback_surface_water': (3, 450, 130, 9, 15),
    'setback_property_line': (3, 450, 136, 9, 15),

    # PAGE 4 - Cross-Section & Disposal Plan
    'scale_page5': (4, 61, 454, 9, 20),
    'depth_backfill_upslope': (4, 92, 419, 9, 10),
    'depth_backfill_downslope': (4, 54, 431, 9, 10),
    'finished_grade_elevation': (4, 511, 444, 9, 10),
    'top_of_distribution_pipe_elevation': (4, 525, 443, 9, 10),
    'bottom_of_disposal_field_elevation': (4, 497, 609, 9, 10),

    # PAGE 5 (Alternative cross-section)
    'scale_page6': (5, 61, 454, 9, 20),
    'backfill_depth_upslope_p6': (5, 92, 419, 9, 10),
    'backfill_depth_downslope_p6': (5, 54, 431, 9, 10),
    'finished_grade_elevation_p6': (5, 511, 444, 9, 10),
    'top_of_distribution_pipe_elevation_p6': (5, 525, 443, 9, 10),
    'bottom_of_disposal_field_elevation_p6': (5, 497, 609, 9, 10),
    'se_number_page6': (5, 468, 725, 9, 15),
    'se_date_page6': (5, 516, 726, 9, 20),
}


def get_page_fields(page: int) -> Dict[str, Tuple[float, float, int, int]]:
    """Get all fields for a specific page. Returns {field_name: (x, y, font_size, max_length)}"""
    result = {}
    for field_name, (p, x, y, font_size, max_length) in FIELD_COORDS.items():
        if p == page:
            result[field_name] = (x, y, font_size, max_length)
    return result


def get_field_coords(field_name: str) -> Optional[Tuple[int, float, float, int, int]]:
    """Get coordinates for a single field. Returns (page, x, y, font_size, max_length) or None"""
    return FIELD_COORDS.get(field_name)


# Map field_coordinates names to actual field names used in run_pipeline.py
FIELD_NAME_MAP = {
    'site_plan_scale': 'scale_pg3',
    'site_location_map_scale': 'scale_pg3',  # Same source
    'evaluator_se_number': 'se_number',
    'evaluator_license_number': 'se_number',
    'evaluator_date_page3': 'se_signature_date',
    'evaluator_name_page3': 'evaluator_name',
    'design_flow_gallons': 'design_flow_gpd',
    'dose_gallons': 'dose_gallons',
    'num_bedrooms': 'num_bedrooms_opt1',
    'scale_page5': 'scale_pg4',
    'scale_page6': 'scale_pg4',
    'depth_backfill_upslope': 'backfill_upslope',
    'depth_backfill_downslope': 'backfill_downslope',
    'finished_grade_elevation': 'finished_grade_elevation',
    'top_of_distribution_pipe_elevation': 'top_distribution_pipe',
    'bottom_of_disposal_field_elevation': 'bottom_disposal_field',
    'backfill_depth_upslope_p6': 'backfill_upslope',
    'backfill_depth_downslope_p6': 'backfill_downslope',
    'finished_grade_elevation_p6': 'finished_grade_elevation',
    'top_of_distribution_pipe_elevation_p6': 'top_distribution_pipe',
    'bottom_of_disposal_field_elevation_p6': 'bottom_disposal_field',
    'se_number_page6': 'se_number',
    'se_date_page6': 'se_signature_date',
}


def map_field_name(coord_field_name: str) -> str:
    """Map field_coordinates name to actual field name used in data."""
    return FIELD_NAME_MAP.get(coord_field_name, coord_field_name)


if __name__ == '__main__':
    # Test: Print all fields by page
    pages = {}
    for field_name, (page, x, y, font_size, max_len) in FIELD_COORDS.items():
        if page not in pages:
            pages[page] = []
        pages[page].append(field_name)

    for page in sorted(pages.keys()):
        print(f"\nPage {page}: {len(pages[page])} fields")
        for field in sorted(pages[page]):
            p, x, y, fs, ml = FIELD_COORDS[field]
            print(f"  {field}: ({x}, {y})")
