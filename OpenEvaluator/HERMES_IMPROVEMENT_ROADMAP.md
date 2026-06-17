# Hermes OCR & Drawing Generation Improvement Roadmap

## Current Status: Critical Gap Analysis

### What Hermes Is Doing Right ✓
1. **Google Sheet Integration**: Correctly extracts form field data
2. **Basic Drawing Generation**: Creates grid-based site plan, disposal plan, and cross-section
3. **Scale Notation**: Includes drawing scales
4. **Elevation Data**: Uses elevation reference data from forms

### What Hermes Is Missing (Critical) ✗

#### 1. **Sketch Data Extraction** (0/5 priority)
Currently extracting only **68 characters** from George Bouchles' hand-drawn field worksheet.

**What should be extracted:**
- Property boundary coordinates and dimensions
- Well location (coordinates + distance to property/tank)
- Existing septic tank location + condition
- Proposed disposal field layout (exact dimensions + module count)
- Road/driveway positions
- Water features (streams, ponds)
- Distance measurements (all setbacks, field length/width)
- Elevation reference marks
- Soil profile depth markers
- Restrictive layer (water table) depth

**Current limitation:** Vision API is only returning text; not extracting:
- Geometric shapes (property boundaries, tank, field outlines)
- Dimension annotations and measurement values
- Scale references in sketches
- Layout positioning relative to grid

#### 2. **Measurement Extraction** (0/5 priority)
**Missing OCR for:**
- Dimension lines and text ("11' x 28'", "100 ft setback", "24 in deep")
- Annotations and labels
- Scale notation from sketches ("Scale: 1\" = 40'")
- Depth markers for cross-sections

**Why it matters:**
The example drawings show precise measurements that come from the hand-drawn sketches. Without extracting these, Hermes is guessing dimensions from the form data only.

#### 3. **Shape Detection** (0/5 priority)
**Need to detect:**
- Property boundary outline
- Septic tank shape/position
- Disposal field cluster boundary
- Module layout (rows × columns)
- Well location marker
- Directional indicators (North arrow)

#### 4. **Drawing Generation from Sketch Data** (20% complete)
Currently generates drawings from:
- ✓ Form field values (dimensions from Google Sheet)
- ✗ Sketch-extracted geometry (not using sketch layout)
- ✗ Sketch-extracted measurements (not used)
- ✗ Sketch-extracted feature positions (not used)

Need to:
- Merge Google Sheet data + Sketch-extracted data
- Prioritize sketch data when available (more accurate)
- Validate sketch dimensions against form data
- Generate drawings that match sketch layout

#### 5. **Comparison & Learning Loop** (0% complete)
Currently comparing generated vs. example drawings as static images.

**Need to implement:**
- Feature-level comparison (tank position, field size, property boundary)
- Measurement accuracy comparison
- Visual overlay of generated vs. example
- Automated feedback on what changed/improved
- Tracking improvements across iterations

---

## Improvement Strategy: Phase 1 (Weeks 1-2)

### Priority 1A: Enhanced Vision API Usage
**Goal:** Extract 5x more useful data from sketches (target: 500+ characters of meaningful data)

```python
# Current:
- Basic OCR text extraction
- 68 characters from 1-page field worksheet

# Needed:
- Geometric shape detection (outlines, boxes, circles)
- Dimension line detection and value extraction
- Grid/ruler detection for scale reference
- Annotation text + associated geometry linking
- Confidence scoring on extracted values
```

**Implementation:**
1. Use Google Cloud Vision API's `DOCUMENT_TEXT_DETECTION` (already doing)
2. Add `FEATURE_TYPES.OBJECT_LOCALIZATION` to find shapes
3. Enhance preprocessing: contrast, dilation, skew correction
4. Post-process OCR to group related text + measurements
5. Save extracted data with coordinates for debugging

### Priority 1B: Structured Data Extraction
**Goal:** Convert raw Vision API output → structured measurement data

Create extraction rules for common patterns:
```python
patterns = {
    'dimension': r'(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)\s*x\s*(\d+(?:\.\d+)?)\s*(?:\'|ft|feet)',
    'depth': r'(\d+)\s*(?:in|inches|")\s*(?:deep|depth)',
    'distance': r'(\d+)\s*(?:ft|feet)\s*(?:to|from)',
    'elevation': r'(-?\d+)"\s*(?:elev|elevation)',
    'scale': r'1"\s*=\s*(\d+)\'',
}

# Extract matches with coordinates and confidence
extracted = {
    'measurements': [
        {'type': 'field_dimensions', 'value': '11 x 28 ft', 'confidence': 0.95},
        {'type': 'depth', 'value': '24 in', 'location': (x, y), 'confidence': 0.87},
        ...
    ],
    'annotations': [
        {'text': 'Eljen GSF-B43 Module', 'location': (x, y), 'type': 'field_type'},
        ...
    ]
}
```

### Priority 1C: Better Preprocessing
**Goal:** Improve image quality before OCR

```python
# Current: basic image loading
# Add:
- Auto-contrast enhancement
- Deskew (rotate to correct angle)
- Despeckle (remove noise)
- Binarization (threshold to pure B&W)
- Dilation/erosion for line strengthening
- Adaptive thresholding for variable lighting
```

---

## Phase 2: Geometric Data Integration (Weeks 3-4)

### Priority 2A: Feature Position Detection
**Goal:** Find property boundary, tank location, field cluster on sketch

```
Detect outlines:
- Property boundary (rectangle with corners marked)
- Septic tank (circle or square)
- Disposal field (grouped modules)
- Well (small circle + distance marker)

Extract positions:
- Relative coordinates (0-1 scale normalized)
- Pixel coordinates (for mapping to drawing grid)
- Confidence scores for each detected feature
```

### Priority 2B: Sketch Layout → Drawing Grid Mapping
**Goal:** Convert hand-drawn layout → 16×30 grid coordinates

```python
# Input: sketch with property boundary at sketch coordinates
# Output: property boundary as (x1, y1, x2, y2) in grid units

# Process:
1. Detect sketch scale reference (if present)
2. Find property boundary corners
3. Measure distances between corners
4. Calculate grid positions
5. Validate against acreage from form data
```

### Priority 2C: Data Validation & Conflict Resolution
**Goal:** When sketch data conflicts with form data, identify and prioritize

```python
# Example conflicts:
{
    'field_dimensions': {
        'form_data': '11 x 28 ft (from sheet)',
        'sketch_data': '11 x 29 ft (from sketch extraction)',
        'resolution': 'Trust sketch if extracted with high confidence'
    },
    'tank_location': {
        'form_data': 'Not specified',
        'sketch_data': '8 ft from house',
        'resolution': 'Use sketch data'
    }
}
```

---

## Phase 3: Learning Loop (Weeks 5+)

### Priority 3A: Automated Comparison System
**Goal:** Compare generated drawings pixel-by-pixel and feature-by-feature

```python
# Pixel-level comparison:
- Structural similarity index (SSIM)
- L2 distance metrics
- Feature detection matching

# Feature-level comparison:
- Property boundary position accuracy
- Tank location offset
- Field cluster positioning
- Dimension accuracy

# Output:
{
    'similarity_score': 0.75,  # 0-1, 1 = identical
    'differences': [
        {
            'type': 'property_boundary',
            'expected': (x1, y1, x2, y2),
            'actual': (x1', y1', x2', y2'),
            'error_pixels': 15
        },
        ...
    ],
    'suggestions': [
        'Field positioning differs by 20px - check extraction accuracy',
        'Tank location matches example (✓)',
        'Property boundary is 8% too small - recalibrate scale'
    ]
}
```

### Priority 3B: Iterative Improvement System
**Goal:** Track improvements across Hermes iterations

```python
# After each improvement:
comparison_score = compare_with_example(
    generated_drawing='site_plan_pg3.png',
    example_pdf='example/example 1/26-018 PG3 (1).pdf'
)

# Log progress:
history = [
    {'iteration': 1, 'score': 0.45, 'change': '+0', 'description': 'baseline'},
    {'iteration': 2, 'score': 0.58, 'change': '+0.13', 'description': 'improved OCR'},
    {'iteration': 3, 'score': 0.72, 'change': '+0.14', 'description': 'shape detection'},
    ...
]

# Visualize:
print(f"Progress toward 93/100 quality gate:")
print(f"  Current: {score} (need {0.93})")
print(f"  Progress: {iterations} iterations, {improvements} improvements")
```

### Priority 3C: Multi-Test Case Learning
**Goal:** Run improvement cycle on all 4 test cases simultaneously

```
Test cases:
- Row 2: Kristen Marquis (26-018) - real data + example
- Row 4: Property 26-123 - real data + example  
- Row 3, 5: Synthetic - learning without examples

For each iteration:
1. Improve extraction for all 4 cases
2. Generate drawings for all 4
3. Compare rows 2 & 4 against examples
4. Check that rows 3 & 5 are sensible
5. Identify common patterns/errors
6. Focus next iteration on biggest gaps
```

---

## Measurement: Success Criteria

### Quality Gate: 93/100 Completion Score
Current status: ~30/100 (mostly form fields, minimal drawing quality)

**By completing this roadmap:**
- ✓ Sketch data extraction: +15 points
- ✓ Accurate measurement extraction: +15 points
- ✓ Improved drawing generation: +20 points
- ✓ Feature positioning accuracy: +15 points
- ✓ Learning loop validation: +10 points
- **Total: 75+ points achievable**

### Specific Metrics to Track
1. **OCR Quality**: Characters extracted per sketch (target: 500+ vs. current 68)
2. **Measurement Accuracy**: % of dimension values extracted correctly (target: >85%)
3. **Feature Detection**: % of features (tank, field, property) detected (target: >80%)
4. **Drawing Similarity**: SSIM vs. example PDFs (target: >0.75 vs. current ~0.45)
5. **Time to Generate**: Minutes from submission to completed drawings (target: <5 min)

---

## Next Action Items

1. **Immediate (Today):**
   - Review Google Cloud Vision API documentation
   - Set up enhanced preprocessing pipeline
   - Test on George Bouchles' sketch

2. **This Week:**
   - Implement measurement extraction patterns
   - Create structured data output format
   - Run on all 4 test cases

3. **Next Week:**
   - Implement shape detection
   - Build feature position mapping
   - Create comparison system

4. **Following Week:**
   - Integrate sketch data into drawing generation
   - Implement learning loop
   - Track progress toward 93/100 gate

---

## References
- **Vision API Docs:** https://cloud.google.com/vision/docs
- **Example Drawings:** `example/example 1/` and `example/example 2/`
- **Current Test Data:** Google Sheet Row 2 (Kristen Marquis, 26-018)
- **Sketch File:** `sketches/26-018 field worksheet - George Bouchles.pdf`
