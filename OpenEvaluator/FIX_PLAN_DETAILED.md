# HHE-200 Automation Fix Plan (Detailed)

## Current State Analysis

### What Works
- Pipeline orchestration (Google Sheets → PDF generation → Drive upload)
- AcroForm field filling: 158 fields being filled successfully
- PNG drawing insertion into PDF pages
- Basic text overlays for scale and disclaimers

### What Doesn't Work
1. **Field Visibility**: AcroForm fields are filled but not visible in final PDF
   - Reason: PNG drawings cover the form fields
   - Solution: Draw field values as text overlays using coordinates from field_map.yaml

2. **Three Drawings Are Too Simple**:
   - **Page 3 (Site Plan)**: Shows basic grid but missing lot outline, trees, setback dimensions, proper scale
   - **Page 4 Top (Disposal Plan)**: Shows simplified module layout, needs full Eljen grid (3×7)
   - **Page 4 Bottom (Cross-Section)**: Shows basic shape, missing soil layers, module details, elevation labels

## Visual Comparison

### Example vs Generated - Page 3
| Aspect | Example | Generated | Status |
|--------|---------|-----------|--------|
| Property outline | Clear boundary with dimensions | Grid-only, no boundary | ❌ Missing |
| Trees | Multiple tree symbols | Not shown | ❌ Missing |
| Setback distances | Labeled distances from tank/field | Not shown | ❌ Missing |
| House/Tank/Field | Detailed placement with dimensions | Simplified boxes | ⚠️ Too simple |
| Scale annotation | "1" = 100 ft" clearly marked | Present but basic | ⚠️ Minimal |
| Soil profile | Two columns with Brown→Yellowish→Olive layers | Empty columns | ❌ Missing |

### Example vs Generated - Page 4 (Top)
| Aspect | Example | Generated | Status |
|--------|---------|-----------|--------|
| Module layout | Grid of rectangles (3 rows × 7 cols) | Single line or simplified | ❌ Wrong |
| Dimensions | Width/spacing clearly marked | Not shown | ❌ Missing |
| Flow direction | Arrow showing wastewater flow | Not shown | ❌ Missing |
| Grid lines | Grid pattern visible | Present but wrong | ⚠️ Incorrect |

### Example vs Generated - Page 4 (Bottom)
| Aspect | Example | Generated | Status |
|--------|---------|-----------|--------|
| Soil layers | 3 distinct colored regions | Not shown | ❌ Missing |
| Modules in section | Modules drawn at correct depth | Not visible | ❌ Missing |
| Groundwater table | Horizontal line at depth | Not shown | ❌ Missing |
| Backfill regions | Distinct areas marked | Not shown | ❌ Missing |
| Elevation labels | Reference elevation, top of pipe, bottom | Minimal | ❌ Mostly missing |
| Depth dimensions | Vertical dimensions to key points | Not shown | ❌ Missing |

## Fix Plan - Three Phases

### PHASE 1: Add Coordinate-Based Text Overlays
**Goal**: Draw field values at coordinates specified in field_map.yaml

#### Step 1.1: Parse field_map.yaml and identify required fields
- Load all 55+ fields from field_map.yaml
- Group by page (1, 2, 3, 4, 5, 6)
- Create mapping of logical names → field_map coordinates

#### Step 1.2: Create overlay function for each page
- `_draw_page1_fields()`: Fill contact, owner, address, phone, email, etc.
- `_draw_page2_fields()`: Fill property, water supply, evaluator info, etc.
- `_draw_page3_fields()`: Fill scales, soil profile data, evaluator info
- `_draw_page4_fields()`: Fill elevations, scales, cross-section annotations

#### Step 1.3: Update acro_fill.py
- After inserting PNG drawings, call overlay functions
- Use fitz.insert_text() with coordinates from field_map.yaml
- Handle text wrapping for long fields (mailing address, notes)

#### Step 1.4: Test field visibility
- Run pipeline and verify all fields from field_map.yaml are visible
- Compare generated PDF to example page by page

**Effort**: 2-3 hours

---

### PHASE 2: Redesign Page 3 (Site Plan Drawing)

**Current Problems**:
- Property outline not drawn
- Trees/vegetation not shown
- Setback distances not labeled
- Scale too simplified
- Soil profile columns empty

**Target**: Match example site plan layout exactly

#### Step 2.1: Redesign site_plan_generator.py - generate_site_plan_pg3()
```python
def generate_site_plan_pg3(lot_width_ft, lot_depth_ft, house_x, house_y, tank_x, tank_y, field_x, field_y, field_w, field_h, well_x, well_y, scale_ft, setbacks):
    """
    Draw site plan with:
    1. Property boundary (rectangle)
    2. House (rectangle with label)
    3. Septic tank (circle with label)
    4. Disposal field (large rectangle with grid)
    5. Well (small circle with label)
    6. Trees (tree symbols at perimeter)
    7. Setback distances (labeled lines/dimensions)
    8. Scale notation
    9. Grid background (16×31 squares)
    
    Returns PNG buffer
    """
```

**Required Changes**:
- Calculate grid dimensions correctly (16×30 small squares per user feedback)
- Scale all elements to fit lot proportions
- Draw property boundary as outer rectangle
- Add tree symbols at corners/perimeter
- Calculate and display setback distances:
  - Well to tank (125 ft)
  - Tank to property line
  - Field to property line
  - Tank to surface water (if applicable)
- Add dimension lines with labels
- Ensure scale annotation is clear

**Effort**: 4-5 hours

---

### PHASE 3: Redesign Page 4 Drawings (Disposal Plan & Cross-Section)

#### PHASE 3A: Disposal Plan (Page 4 Top)

**Current Problem**: Simplified module layout, not matching Eljen GSF-B43 grid

**Target**: Draw proper Eljen module arrangement

```python
def generate_disposal_plan_pg4(num_modules, field_width, field_depth, flow_direction):
    """
    Draw Eljen disposal plan with:
    1. Module grid (Eljen GSF-B43: 3 rows × 7 modules standard, or custom)
    2. Each module as labeled rectangle
    3. Flow arrows showing wastewater direction
    4. Spacing/dimensions between modules
    5. Scale notation
    6. Grid background (16×30 squares)
    
    Returns PNG buffer
    """
```

**From Data**: User mentioned "The grids are 16x30 small squares"
- Each module is 2 ft × 6 ft (Eljen standard)
- Standard configuration: 3 rows × 7 modules = 42 total
- Spacing between modules: typically 0-6 inches per design

**Effort**: 3-4 hours

---

#### PHASE 3B: Cross-Section (Page 4 Bottom)

**Current Problem**: Missing soil layers, module positioning, elevation data

**Target**: Match example cross-section with all details

```python
def generate_cross_section_pg4(soil_layers, module_depth, water_table_depth, erp_elevation):
    """
    Draw cross-section with:
    1. Soil layers (colored regions for Brown/Yellowish/Olive)
    2. Modules at correct depth
    3. Backfill regions (upslope/downslope)
    4. Groundwater table line
    5. Elevation reference point (ERP)
    6. Depth dimension lines
    7. Scale notation (horizontal and vertical)
    8. Grid background (16×30 squares)
    
    Returns PNG buffer
    """
```

**Soil Layers** (from example data):
- Brown fine sandy loam: 0-3 inches
- Yellowish brown fine sandy loam: 3-24 inches
- Olive gray fine sandy loam: 24-36+ inches
- Groundwater table: 24 inches depth
- Module placement: Below groundwater table (26-28 inches typical)
- Backfill: 12 inches above module

**Elevation Labels Needed**:
- Finished grade elevation (reference point)
- Top of distribution pipe
- Top of module
- Bottom of module
- Groundwater table elevation
- All relative to ERP = 0.0

**Effort**: 4-5 hours

---

## Implementation Order

1. **Day 1 - Morning**: Phase 1 (field overlay mapping)
2. **Day 1 - Afternoon**: Phase 2 (site plan redesign)
3. **Day 2 - Morning**: Phase 3A (disposal plan)
4. **Day 2 - Afternoon**: Phase 3B (cross-section) + Testing
5. **Day 2 - Evening**: Full pipeline test, visual comparison to example, refinements

## Success Criteria

- [ ] All 55+ fields from field_map.yaml are visible in generated PDF
- [ ] Page 3 site plan matches example (property, house, tank, field, well, trees, setbacks, scale)
- [ ] Page 4 top shows proper Eljen module grid layout
- [ ] Page 4 bottom shows soil layers, modules at correct depth, all elevation labels
- [ ] Generated PDF pages compare visually identical to example/pg*_preview.png

## Key References

- **Blank template**: HHE-200-2025.pdf
- **Example output**: example/ folder (pg1_preview.png through pg4_preview.png)
- **Field coordinates**: field_map.yaml (55+ fields with x,y,page)
- **Drawing generator**: site_plan_generator.py (3 functions to redesign)
- **PDF filler**: acro_fill.py (overlay functions to implement)
- **Data source**: Google Sheet with evaluator data
- **Current output**: HHE-200-filled.pdf

