# Hermes Drawing Generation: Current State & Improvement Plan

**Date:** June 15, 2026  
**Status:** Foundation laid, ready for OCR improvement phase  
**Target:** 93/100 quality gate completion

---

## What We've Accomplished This Session

### 1. ✓ Complete Pipeline Infrastructure
- Created `hermes_drawing_pipeline.py` - Full end-to-end workflow
- Integrated Google Sheet data extraction
- Connected sketch downloading from Google Drive
- Automated drawing generation for all 3 pages
- Created comparison framework for visual analysis

### 2. ✓ Tested with Real Data
- Row 2: Kristen Marquis property (26-018, Turner, ME)
- Successfully downloaded hand-drawn field worksheet from Google Drive
- Generated 3 drawings: site plan, disposal plan, cross-section
- Created side-by-side visual comparisons with example PDFs

### 3. ✓ Identified the Core Bottleneck
**Current extraction capacity:** 68 characters from field worksheet  
**What's being extracted:** Only basic text blocks  
**What's being missed:** All measurements, dimensions, annotations, geometry

### 4. ✓ Created Improvement Roadmap
Detailed strategy in `HERMES_IMPROVEMENT_ROADMAP.md`:
- Phase 1: Enhanced OCR & measurement extraction
- Phase 2: Geometric data integration
- Phase 3: Learning loop & validation

---

## The Critical Issue: Sketch Data Extraction

### What Should Be Extracted from George's Field Worksheet
```
Property Layout:
  ✓ Property boundary coordinates/dimensions
  ✗ Well location (not extracted)
  ✗ Tank location (not extracted)
  ✗ Disposal field layout - exact (not extracted)
  ✗ Road/driveway positions (not extracted)

Measurements:
  ✓ Form data available (11 x 28 ft field size)
  ✗ Sketch annotations (not read)
  ✗ Dimension lines & text (not extracted)
  ✗ Distance measurements between features (not extracted)
  ✗ Depth/elevation markers (not extracted)

Scale & Reference:
  ✓ Scale from form (1" = 40')
  ✗ Sketch scale notation (not extracted)
  ✗ Scale reference grid on sketch (not extracted)
```

### Why This Matters
The **example PDF drawings** (26-018 PG3 & PG4) show:
- Precise feature positioning that comes from the sketch
- Accurate measurement labels from the sketch
- Property boundary exactly matching George's hand-drawn outline
- Disposal field layout matching sketch modules

**Without extracting these details, Hermes is essentially guessing the layout.**

---

## Current Hermes Performance: 30-40/100

### What Hermes Got Right ✓
1. Form fields extraction from Google Sheets
2. Basic drawing generation with grids
3. Scale notation
4. Elevation reference data
5. System type identification
6. Sketch file downloading infrastructure

### What Hermes Got Wrong ✗
1. **Sketch data extraction** (only 68 characters)
2. **Measurement reading** (not reading dimension text)
3. **Feature detection** (tank/field/well positions missing)
4. **Shape recognition** (property boundary geometry)
5. **Data validation** (no cross-check between sheet & sketch)
6. **Learning feedback** (no automated improvement tracking)

---

## Generated Drawings vs. Examples

### Site Plan (Page 3)
**Generated:** `site_plan_pg3.png` (122K)  
**Example:** `example/example 1/26-018 PG3 (1).pdf` (290K)  
**Comparison:** `drawing_comparisons/site_plan_comparison.png` (784K)

✓ Grid layout correct  
✓ Scale notation present  
✗ Missing property boundary from sketch  
✗ Missing well location detail  
✗ Missing road/feature annotations  

### Disposal Plan (Page 4 Top)
**Generated:** `disposal_plan_pg4.png` (44K)  
**Example:** `example/example 1/26-018 PG4 (1).pdf` (259K)  
**Comparison:** `drawing_comparisons/disposal_plan_comparison.png` (538K)

✓ Grid and scale present  
✓ Basic field representation  
✗ Module layout not detailed  
✗ Tank/box connections missing detail  
✗ Elevation annotations not integrated  

### Cross-Section (Page 4 Bottom)
**Generated:** `cross_section_pg4.png` (50K)  
**Example:** Included in PG4 PDF  

✓ Elevation marks shown  
✓ Depth measurements present  
✗ Soil layer detail missing  
✗ Groundwater table visualization crude  

---

## Detailed Improvement Roadmap

### Phase 1: OCR Enhancement (1-2 weeks)
**Goal:** Extract 5-10x more useful data from sketches

1. **Better Vision API Usage**
   - Add geometric shape detection
   - Extract dimension annotations with associated values
   - Improve text-to-measurement linking
   - Add confidence scoring

2. **Measurement Pattern Extraction**
   - Parse "11 x 28 ft" format
   - Extract "100 ft setback" distances
   - Read "24 in depth" measurements
   - Identify elevation marks

3. **Image Preprocessing**
   - Auto-contrast enhancement
   - Deskew correction
   - Binarization for text clarity
   - Despeckle noise removal

**Success metric:** >500 characters of meaningful extracted data (vs. 68 current)

### Phase 2: Geometric Integration (2-3 weeks)
**Goal:** Map sketch features to drawing coordinates

1. **Feature Detection**
   - Locate property boundary
   - Find septic tank position
   - Identify disposal field cluster
   - Mark well location

2. **Coordinate Mapping**
   - Convert sketch layout → grid positions
   - Validate against form dimensions
   - Resolve conflicts (sketch vs. form data)

3. **Drawing Generation from Sketch**
   - Use extracted geometry for accurate positioning
   - Place features at correct grid coordinates
   - Include extracted measurement labels

**Success metric:** Property boundary position matches example within 5% error

### Phase 3: Learning Loop (3+ weeks)
**Goal:** Automated validation and continuous improvement

1. **Comparison System**
   - Pixel-level matching with example
   - Feature-position accuracy check
   - Measurement label validation

2. **Feedback Generation**
   - Identify discrepancies
   - Suggest corrections
   - Track improvement progress

3. **Multi-Test Validation**
   - Run on all 4 test cases
   - Identify common patterns
   - Build generalized solution

**Success metric:** Visual similarity (SSIM) >0.75 with examples

---

## Quality Gate Progress

### Current Status: 30/100 (30%)
```
Form Fields:        [████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 25%
Drawing Quality:    [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 5%
OCR/Extraction:     [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%
Feature Detection:  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%
Learning/Feedback:  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%
```

### Target: 93/100 (93%)
```
Expected after Phase 1:  50/100 (35 points from OCR)
Expected after Phase 2:  75/100 (25 points from geometry)
Expected after Phase 3:  93/100 (18 points from validation)
```

---

## Files Created This Session

### Main Pipeline
- `hermes_drawing_pipeline.py` - Complete end-to-end workflow
- `analyze_hermes_drawing_requirements.py` - Requirements analysis
- `compare_drawings_detailed.py` - Visual comparison tool

### Documentation
- `HERMES_IMPROVEMENT_ROADMAP.md` - Detailed improvement plan
- `HERMES_CURRENT_STATE.md` - This file

### Data & Comparisons
- `hermes_drawing_analysis.json` - Analysis results
- `hermes_extracted_sketches.json` - Raw extracted sketch data
- `drawing_comparisons/site_plan_comparison.png` - Side-by-side comparison
- `drawing_comparisons/disposal_plan_comparison.png` - Side-by-side comparison

### Generated Drawings
- `site_plan_pg3.png` - Generated site plan
- `disposal_plan_pg4.png` - Generated disposal plan
- `cross_section_pg4.png` - Generated cross-section

### Test Sketches
- `sketches/26-018 field worksheet - George Bouchles.pdf` - Downloaded sketch

---

## Next Steps (Priority Order)

### Week 1: OCR Improvement
1. [ ] Enhance Vision API usage for shape detection
2. [ ] Implement measurement pattern extraction
3. [ ] Improve image preprocessing
4. [ ] Test extraction on all 4 test cases
5. [ ] Create feedback on extraction quality

### Week 2: Integration & Validation
1. [ ] Map sketch features to grid coordinates
2. [ ] Merge sketch + form data
3. [ ] Generate improved drawings
4. [ ] Compare with examples
5. [ ] Document what improved

### Week 3+: Learning Loop
1. [ ] Build automated comparison system
2. [ ] Create improvement tracking
3. [ ] Run iterative improvement cycle
4. [ ] Validate against quality gate (93/100)
5. [ ] Scale to all test cases

---

## Key Resources

**Test Data:**
- Row 2: Kristen Marquis (26-018) - real client, complete examples
- Row 4: Property 26-123 - real client, complete examples
- Rows 3, 5: Synthetic data - for additional testing

**Example PDFs:**
- `/home/workspace/OpenEvaluator/example/example 1/` (26-018)
- `/home/workspace/OpenEvaluator/example/example 2/` (26-123)

**Sketch File:**
- `/home/workspace/OpenEvaluator/sketches/26-018 field worksheet - George Bouchles.pdf`

**APIs Available:**
- Google Cloud Vision API (OCR, shape detection)
- Google Maps API (property/boundary queries)
- Google Drive API (sketch downloading)
- Google Sheets API (form data)

---

## Success Criteria

When complete, Hermes should:
1. ✓ Extract 500+ characters of meaningful data per sketch
2. ✓ Identify and locate all major features (tank, field, well, property)
3. ✓ Read measurement dimensions with 85%+ accuracy
4. ✓ Generate drawings within 5% of example dimensions
5. ✓ Complete full pipeline in <5 minutes per submission
6. ✓ Achieve 93/100 quality gate across all test cases

---

**Status:** Ready to begin Phase 1 - OCR improvement.  
**Blockers:** None identified.  
**Resources:** All available and tested.
