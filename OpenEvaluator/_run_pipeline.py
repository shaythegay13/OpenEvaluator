#!/usr/bin/env python3
import json, sys, os, re
sys.path.insert(0, '.')

from sheet_parser import parse_sheet_row, RAW_ROW

# Parse form
fields = parse_sheet_row(RAW_ROW)

# Build drawing data
drawing_data = {
    'owner_name': fields.get('owner_name', '').upper(),
    'address_line': fields.get('site_address', '') + ', ' + fields.get('town', '') + ', ME ' + fields.get('mailing_zip', ''),
    'road_name': 'ROAD',
    'town': fields.get('town', '').upper(),
    'tax_map': fields.get('map_number', ''),
    'lot_number': fields.get('lot_number', ''),
    'acreage': float(fields.get('acreage', 1)),
    'tank_cap': '1000',
    'se_number': fields.get('lpi_number', ''),
    'se_date': '03/01/2026',
    'evaluator_name': fields.get('evaluator_name', '').upper(),
    'num_rows': 3, 'mods_per_row': 7, 'mod_len': 4.0, 'mod_wid': 3.67,
    'cluster_w': 11.0, 'cluster_l': 28.0, 'brand': 'Eljen',
    'scale_pg3': 80, 'field_to_well': 100,
    'field_to_house': 40, 'tank_to_house': 8.0,
    'finished_grade_elevation': '0"',
    'top_of_distribution_pipe_elevation': '-12"',
    'bottom_of_disposal_field_elevation': '30"',
    'limiting_factor': 24,
}

# Parse planned field size
fl = fields.get('planned_field_size', '')
m = re.search(r'(\d+)\s+rows', fl, re.I)
if m: drawing_data['num_rows'] = int(m.group(1))
m = re.search(r'of\s+(\d+)\s+\w+.*[Mm]odul', fl)
if m: drawing_data['mods_per_row'] = int(m.group(1))
m = re.search(r'(\d+\.?\d*)\s*(?:ft)?\s*[xX]\s*(\d+\.?\d*)', fl)
if m:
    drawing_data['cluster_w'] = float(m.group(1))
    drawing_data['cluster_l'] = float(m.group(2))

# Generate DXF
from dxf_generator import generate_all_dxf
results = generate_all_dxf(drawing_data)
print(json.dumps(results, indent=2))
