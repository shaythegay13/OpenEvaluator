# HHE-200 Automation - Implementation Status

**Last Updated**: 2026-05-31  
**Status**: Phase 1 (Coordinate-Based Text Overlays) - COMPLETE  
**Status**: Phase 2 (Drawing Redesign) - IN PROGRESS

## Phase 1: Coordinate-Based Text Overlays ✅ COMPLETE

### What Was Done
1. Created `field_coordinates.py` module
   - Extracts coordinates from field_map.yaml for 55+ fields
   - Maps logical field names to actual data field names used in run_pipeline.py
   - Provides lookup functions for page-specific fields

2. Updated `acro_fill.py`
   - Enhanced `_draw_page3_overlays()` to draw field values at specified coordinates
   - Enhanced `_draw_page4_overlays()` to draw field values at specified coordinates
   - Added debug output to verify field overlay drawing

3. Test Results
   - Page 3: Successfully drawing 6 field overlays
   - Page 4: Successfully drawing 6 field overlays
   - Fields being drawn: scale, evaluator name, SE number, signature date, backfill depths, elevations

### Current Limitations
- Only fields with mapped data are being drawn (41 fields in field_coordinates have no data mapping)
- Soil profile observation hole data needs to be extracted and added to fields dict
- Some field coordinates may need fine-tuning based on visual comparison with example

---

## Phase 2: Drawing Redesign - IN PROGRESS

### Current Drawing Code Analysis

The site_plan_generator.py actually contains very comprehensive drawing code:

#### Page 3 (Site Plan)
**Current Implementation** includes:
- Grid-based layout (16×31 cells)
- Road band at bottom
- Lot boundary with tax map/lot number labels
- Adjacent lot indicators
- House with label
- Septic tank with capacity label
- Distribution box
- Disposal field with module grid (3 rows × 7 cols)
- Setback dimension lines (field-to-house, field-to-well)
- Well with label
- Wooded area with tree symbols
- Observation holes (OH-1, OH-2)
- North arrow and scale notation
- Header with owner name and address

**Visual Comparison to Example**: 
- ✅ All major elements present
- ⚠️ Elements may be at slightly different scales/positions
- ⚠️ Grid dimensions user mentioned as "16×30" but code uses 16×31 for page 3

#### Page 4 Top (Disposal Plan)
**Current Implementation** includes:
- Grid-based layout (16×30 cells)
- Septic tank with label
- Distribution box
- Distribution laterals to each row
- Perforated pipe through modules
- Individual module grid (color-coded rows)
- Row labels (ROW 1, ROW 2, ROW 3)
- Module type label with dimensions
- Cluster border with dashed line
- Width/height dimensions
- Setback notes (field-to-well, field-to-house, tank-to-house)
- Total module count
- North arrow and scale

**Visual Comparison to Example**:
- ✅ Module layout structure correct
- ✅ Dimensions shown
- ⚠️ Module appearance/style may differ from example

#### Page 4 Bottom (Cross-Section)
**Current Implementation** includes:
- Existing grade line
- Fill mound polygon
- Finished grade (ERP) dashed line
- ERP marker with nail symbol
- Module cross-sections (7 modules shown)
- Pipe dots inside modules
- Anti-siltation fabric line
- Bottom of disposal field line
- SHWT (Seasonally High Water Table) dashed line
- Vertical dimension annotations
- Elevation reference point table
- Scale notation (vertical 1"=1', horizontal variable)

**Visual Comparison to Example**:
- ⚠️ Soil layers not shown with distinct colors (BROWN, YELLOWISH, OLIVE GRAY)
- ⚠️ Module positioning relative to soil layers may be different
- ⚠️ Elevation labels positioning may differ

### Known Issues to Address

1. **Grid Dimensions**
   - User stated: "The grids are 16x30 small squares"
   - Current code: ROWS_PG3 = 31, ROWS_PG4 = 30
   - Action: Verify if page 3 should be 16×30 instead of 16×31

2. **Soil Layer Colors**
   - Cross-section needs visual soil layers: BROWN → YELLOWISH → OLIVE GRAY
   - Currently using white/gray backgrounds only
   - Action: Add colored rectangles/polygons for each soil layer

3. **Scale and Proportions**
   - Drawings may be rendering at incorrect scale
   - Action: Test with known dimensions and compare to example

4. **Text Positioning**
   - Some text labels may overlap or be in wrong positions
   - Action: Visual comparison and coordinate adjustments

---

## Field Mapping Status

### Mapped Fields (working):
✅ Page 3:
- site_plan_scale (→ scale_pg3): "40" ✓
- site_location_map_scale (→ scale_pg3): "40" ✓
- evaluator_name_page3 (→ evaluator_name): "GEORGE BOUCHLES" ✓
- evaluator_se_number (→ se_number): "338" ✓
- evaluator_date_page3 (→ se_signature_date): "03/01/2026" ✓

✅ Page 4:
- scale_page5 (→ scale_pg4): value present ✓
- depth_backfill_upslope (→ backfill_upslope): "12" ✓
- depth_backfill_downslope (→ backfill_downslope): "12" ✓
- finished_grade_elevation (→ finished_grade_elevation): "0.0\"" ✓
- top_of_distribution_pipe_elevation (→ top_distribution_pipe): "1.0\"" ✓
- bottom_of_disposal_field_elevation (→ bottom_disposal_field): "2.5\"" ✓

### Unmapped Fields (need data):
❌ Soil profile observation hole data
❌ Soil layer texture/color info
❌ Limiting factor depths
❌ Setback distances (well, surface water, property line)
❌ Lot size (acres/sqft)
❌ Water table depth

---

## Next Steps

### Immediate (Phase 2):
1. **Fix Grid Dimensions** 
   - Change ROWS_PG3 from 31 to 30 if confirmed by user
   - Verify all drawing proportions remain correct

2. **Add Soil Layer Visualization**
   - Create colored regions in cross-section for:
     - Brown fine sandy loam (0-3")
     - Yellowish brown fine sandy loam (3-24")
     - Olive gray fine sandy loam (24-36"+)
   - Add texture labels or patterns

3. **Verify Scale and Proportions**
   - Run pipeline with test data
   - Visual comparison to examples
   - Adjust element sizes/positions as needed

4. **Complete Field Extraction**
   - Extract observation hole data from ROW in run_pipeline.py
   - Calculate soil layer colors and depths
   - Add to fields dict for overlay drawing

### Testing:
- Run full pipeline: `python3 run_pipeline.py`
- Compare generated PDF pages to example/ folder
- Verify all 55+ field coordinates have data values

### Success Criteria:
- Generated PDF pages 3 & 4 visually match example pages
- All fields with data are drawn at correct coordinates
- Soil layer colors visible in cross-section
- Grid dimensions correct (16×30)
- Module layouts match examples exactly

