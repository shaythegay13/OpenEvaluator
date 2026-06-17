# HHE-200 Complete Fix Plan

## PHASE 1: Extract & Map AcroForm Fields

**Goal:** Get the correct field names from the blank PDF template

### Step 1A: Extract all AcroForm field names from HHE-200-2025.pdf
- Use PyPDF or pdfrw to list every AcroForm field name
- Output: `field_names_from_pdf.json` with structure:
  ```json
  {
    "page_1": ["field1_name", "field2_name", ...],
    "page_2": [...],
    "page_3": [...],
    "page_4": [...]
  }
  ```

### Step 1B: Create proper field mapping
- Cross-reference `field_map.yaml` logical names with actual AcroForm field names
- Output: `field_mapping.json` with mapping:
  ```json
  {
    "site_address": "actual_form_field_name_from_pdf",
    "phone": "actual_form_field_name_from_pdf",
    ...
  }
  ```

### Step 1C: Update acro_fill.py
- Change to use the correct AcroForm field names
- Ensure all 55+ fields from field_map.yaml are mapped and filled

### Step 1D: Verify field filling
- Re-run pipeline
- Check output PDF has all visible fields filled

---

## PHASE 2: Fix The Three Drawings

**Problem Areas:** Our drawings don't match the example folder

### Current Issues to Fix:

#### Page 3 - Site Plan Drawing
**Missing/Wrong:**
- [ ] Grid should be 16 columns × 31 rows (not current size)
- [ ] Grid cell size should scale with site dimensions
- [ ] Scale annotation placement/format
- [ ] House placement and label positioning
- [ ] Septic tank placement and symbol
- [ ] Disposal field cluster placement
- [ ] Well location and symbol
- [ ] Setback dimensions (clearly labeled)
- [ ] Road/property boundaries
- [ ] North arrow placement
- [ ] Legend with symbols

**What Example Shows:**
- Grid-based drawing with 16×31 cells
- House in upper portion
- Tank offset from house
- Field cluster positioned below/beside tank
- Well location marked at distance
- Setbacks clearly dimensioned
- Scale: 1" = [X] ft (varies by lot size)
- All text annotations positioned clearly

#### Page 4 - Disposal Field Plan (Upper Half)
**Missing/Wrong:**
- [ ] Eljen GSF-B43 module dimensions (should be ~4' × 3.67')
- [ ] Module layout in rows (3 rows × 7 modules)
- [ ] Proper spacing between modules
- [ ] Total cluster dimension (11' × 28' for this example)
- [ ] Direction of flow/entry point
- [ ] Tank connection point shown
- [ ] Piping shown from tank to field
- [ ] Proper scale/measurements

**What Example Shows:**
- 3 rows of 7 Eljen modules
- 4'×3.67' per module
- 11' × 28' total cluster
- Clear layout showing arrangement
- Entry point from tank
- Scale reference

#### Page 4 - Cross-Section (Lower Half)
**Missing/Wrong:**
- [ ] Soil layers correctly shown (Brown → Yellowish → Olive)
- [ ] Depth markers aligned to actual soil data
- [ ] Eljen modules drawn to scale
- [ ] Pipe placement within module
- [ ] Elevation reference (ERP) shown
- [ ] Ground surface shown
- [ ] Water table depth marked
- [ ] Vertical dimensions labeled
- [ ] Horizontal scale accurate

**What Example Shows:**
- Top: Brown fine sandy loam (0-3")
- Middle: Yellowish brown fine sandy loam (3-24")
- Bottom: Olive gray fine sandy loam (24-36")
- Water table at 24" marked clearly
- Modules shown at bottom
- ERP reference point
- Vertical and horizontal scales

---

## PHASE 3: Implementation Order

1. **Extract actual field names** from blank PDF (Step 1A)
2. **Create field mapping** (Step 1B)
3. **Update acro_fill.py** with correct names (Step 1C)
4. **Test field filling** (Step 1D)
5. **Redesign site_plan_generator.py** to fix Page 3
6. **Redesign disposal_plan drawing** for Page 4 upper
7. **Redesign cross_section drawing** for Page 4 lower
8. **Run full pipeline** with test data
9. **Compare to example** - verify visual match

---

## What We Need From You

**To fix the drawings, please clarify:**
1. Looking at the example pg3_preview.png (site plan), what's the biggest difference you see?
2. Looking at the example pg4_preview.png (disposal plan & cross-section), what needs to be better?
3. Are the grid dimensions correct (16×31 for site, 16×30 for others)?
4. Should we draw the soil profile differently on the cross-section?
5. Any other visual elements missing that you see in the example?

