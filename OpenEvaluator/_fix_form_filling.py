import sys, json, os, re
sys.path.insert(0, '.')
from sheet_parser import parse_sheet_row, RAW_ROW
from field_adapter import adapt_sheet_fields_to_acro
from acro_fill import fill_acro

# 1. Parse Google Sheet row
fields = parse_sheet_row(RAW_ROW)
print(f"Sheet fields: {len(fields)}")

# 2. Read Claude sketch data if available
claude_path = 'claude_output.json'
claude_data = {}
if os.path.exists(claude_path):
    with open(claude_path) as f:
        claude_data = json.load(f)
    print(f"Claude keys: {list(claude_data.keys())}")
    
    # Merge Claude dimensions and soil into sheet fields
    dims = claude_data.get('dimensions_ft', {})
    if dims.get('field_to_well'): fields['setback_well'] = f"{dims['field_to_well']} ft"
    
    elev = claude_data.get('elevations', {})
    if elev.get('finished_grade'): fields['finished_grade_elevation_p6'] = elev['finished_grade']
    if elev.get('top_pipe'): fields['top_of_distribution_pipe_elevation_p6'] = elev['top_pipe']
    if elev.get('bottom_field'): fields['bottom_of_disposal_field_elevation_p6'] = elev['bottom_field']
    
    soil = claude_data.get('soil_observations', [])
    if soil and len(soil) > 0:
        s = soil[0]
        if s.get('texture'): fields['soil_type'] = s['texture']
        if s.get('color'): fields['soil_color_hole1'] = s['color']
    
    fs = claude_data.get('field_system', {})
    if fs.get('rows'): fields['num_rows'] = fs['rows']
    if fs.get('modules'): fields['mods_per_row'] = fs['modules']

# 3. Adapt to acro_fill format
adapted = adapt_sheet_fields_to_acro(fields)
non_empty = {k:v for k,v in adapted.items() if v}
print(f"Adapted: {len(non_empty)} non-empty fields")

# 4. Get GPS for coordinates
maps_key = os.environ.get('GOOGLE_MAPS_API_KEY')
if maps_key:
    try:
        import googlemaps
        gmaps = googlemaps.Client(key=maps_key)
        geo = gmaps.geocode('17 Aspen Way, Turner, Maine 04282')
        if geo:
            lat = geo[0]['geometry']['location']['lat']
            lng = geo[0]['geometry']['location']['lng']
            adapted['latitude_deg'] = str(int(abs(lat)))
            adapted['latitude_min'] = str(int((abs(lat) - int(abs(lat))) * 60))
            adapted['latitude_sec'] = str(round(((abs(lat)%1*60)%1)*60, 1))
            adapted['longitude_deg'] = str(int(abs(lng)))
            adapted['longitude_min'] = str(int((abs(lng) - int(abs(lng))) * 60))
            adapted['longitude_sec'] = str(round(((abs(lng)%1*60)%1)*60, 1))
            print(f"GPS: {lat}, {lng}")
    except Exception as e:
        print(f"Maps error: {e}")

# 5. Fill form
result = fill_acro(adapted, 'HHE-200-filled.pdf')
print(f"Form: {result}")

# 6. Score
import pikepdf
doc = pikepdf.open('HHE-200-filled.pdf')
filled = 0
total = 0
for page in doc.pages:
    annots = page.get('/Annots')
    if annots:
        for ref in annots:
            w = doc.get_object(ref)
            if '/T' in w:
                total += 1
                if '/V' in w:
                    v = str(w['/V'])
                    if v and v != '/Off' and v != '':
                        filled += 1
doc.close()
print(f"Score: {filled}/{total} = {filled*100//total}%")
