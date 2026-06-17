# HHE-200 Automation: Complete Learning Mechanism

## System Overview

The HHE-200 form automation now has a **comprehensive learning mechanism** that assesses ALL 4 pages and provides real feedback for Hermes to improve on both form data and drawings.

```
Google Sheet (Data Source)
    ↓
Hermes (Interprets + Completes)
    ↓
OpenClaw (Generates Site Plan + Disposal Plan)
    ↓
Form Filler (Embeds in PDF)
    ↓
Learning Assessment System
    ├─ Pages 1-2: Form Field Assessment
    └─ Pages 3-4: Drawing Comparison
    ↓
Feedback Report (for Hermes to learn from)
```

## Part 1: Form Assessment (Pages 1-2)

### What Gets Assessed
- **Page 1**: Personal info, property info, soil info (28/80 available fields evaluated)
- **Page 2**: Design info, system info, contractor info (30/50 available fields evaluated)

### How It Works
1. Generates PDF from filled form data
2. Extracts form field values from the PDF
3. Counts how many widgets were actually filled
4. Compares filled count vs. available widgets
5. Generates completion percentage

### Example Assessment
```
Page 1: 28/80 fields filled (35%)
- Found fields: client_name, address, property_size, etc.
- Missing fields: Some optional fields not in provided data

Page 2: 30/50 fields filled (60%)
- Found fields: system_type, tank_size, design_flow, etc.
- Missing fields: Some advanced design parameters
```

### Score Calculation
```
Page 1 Score = (fields_filled / total_available) * 100
Page 2 Score = (fields_filled / total_available) * 100
Form Completion = (Page1 + Page2) / 2
```

## Part 2: Drawing Assessment (Pages 3-4)

### Page 3: Site Plan

**Expected Elements:**
- Lot boundary (rectangular property outline)
- House building (residence structure)
- Septic tank (primary tank rectangle)
- Distribution box (smaller rectangle)
- Soil absorption field (with multiple rows)
- Road/access way
- Grid system (16x31 squares)
- Scale notation
- North arrow
- Dimensions and annotations

**Assessment Metrics:**
1. **Structural Completeness** - Are all required elements present?
2. **Geometric Accuracy** - Are elements in correct positions with right proportions?
3. **Detail Level** - Line count and complexity vs. pinnacle example
4. **Annotations** - Are text labels, dimensions, scale present?
5. **Grid System** - Is 16x31 grid correctly implemented?

**Scoring:**
- Base: 50 points
- Missing each element type: -15 points each
- Correct size ratio (0.8-1.2): +10 points
- Sufficient line complexity (≥70% of example): +15 points
- Has annotations: +10 points
- Final: max 100, min 0

### Page 4: Disposal Plan

**Expected Elements:**
- Septic tank (with label)
- Distribution box (with label)
- Absorption field layout
- Disposal rows (4-5 parallel)
- Field modules
- Required spacing notation
- Scale
- Dimensions
- Design notes
- Legend/symbol explanation

**Same assessment approach as Page 3**

### How Real Comparison Works

```python
1. Extract drawing from generated PDF (page 3 or 4)
2. Extract drawing from pinnacle example PDF
3. Analyze both images:
   - Count lines (structural elements)
   - Count contours (enclosed areas)
   - Detect text regions (annotations)
   - Check for grid pattern
   - Measure image dimensions
4. Compare:
   - Missing element types
   - Size ratio (should be 0.8-1.2)
   - Line count (generated vs. example)
   - Text present/missing
   - Grid present (for page 3)
5. Generate gaps list and score
```

## Part 3: Complete Assessment Report

### Structure
```
Form Assessment (Pages 1-2)
├─ Page 1 Completion: X%
├─ Page 2 Completion: Y%
└─ Form Score: (X + Y) / 2

Drawing Assessment (Pages 3-4)
├─ Page 3 (Site Plan)
│  ├─ Detected Elements: [list]
│  ├─ Missing Elements: [list]
│  ├─ Line Count: N vs M expected
│  ├─ Has Annotations: yes/no
│  └─ Score: Z/100
├─ Page 4 (Disposal Plan)
│  ├─ [same structure]
│  └─ Score: Z/100
└─ Drawing Score: average of pages 3-4

Overall Quality Score
├─ Form Contribution: 50%
├─ Drawing Contribution: 50%
└─ Final: (Form Score + Drawing Score) / 2
```

### Example Report
```
Page 1: 35% (28/80 fields)
  Gaps: Missing some optional fields

Page 2: 60% (30/50 fields)
  Gaps: Advanced design fields not provided

Page 3 Site Plan: 65/100
  Issues:
  - Missing: grid_system, north_arrow
  - Drawing lacks detail/complexity (45 vs 120 lines expected)
  - Missing text annotations/dimensions

Page 4 Disposal Plan: 72/100
  Issues:
  - Size mismatch (0.75 ratio)
  - Missing element types: spacing_notation

Overall Quality: 58/100
Status: ⚠️ Acceptable but needs improvements
```

## Part 4: Learning Feedback for Hermes

### What Hermes Learns From

**Form Gaps:**
- "Client address missing" → Ensure Google Sheet column D is populated
- "Soil type incomplete" → Need full soil profile from sheet
- "Design parameters missing" → Some Hermes outputs not matching PDF widgets

**Drawing Gaps:**
- "Missing grid system" → Site plan generator not creating 16x31 grid
- "Drawing lacks detail" → Too few lines, too simple structure
- "Missing annotations" → Text labels not being added to drawings
- "Element positioning wrong" → Coordinates need adjustment
- "Disposal rows incomplete" → Need 4-5 rows properly spaced

### Feedback Loop

```
Score < 60: Critical issues
→ Hermes should ask for:
  - Missing data in sheet
  - Clarification on soil profile
  - More complete site information

Score 60-80: Acceptable but improvable
→ Hermes iterates:
  - Refine drawing generation parameters
  - Add more detail to site plan
  - Add all required annotations
  - Fix element positioning

Score ≥ 80: Good to excellent
→ Hermes confirms:
  - All elements present
  - Proper positioning and proportions
  - Complete annotations and notes
```

## Part 5: Current Quality Gate

**Threshold: 95/100** (for production-ready documents)

This means:
- ✅ Form completion ≥ 95% (both pages)
- ✅ Drawing completion ≥ 95% (both pages)
- ✅ No critical gaps
- ✅ All annotations present
- ✅ Proper sizing and positioning

**Your Current Status:**
- Form completion: ~47% (pages 1-2)
- Drawing completion: TBD (needs real comparison against pinnacle examples)

## Part 6: How to Improve Each Component

### Improving Form Completion
1. **Check Google Sheet**: Ensure all relevant columns A-W are populated
2. **Update Hermes Prompts**: Guide it to extract more fields
3. **Expand Field Map**: Add more WIDGET_MAP entries for underutilized fields
4. **Test with Complete Data**: Use test rows with comprehensive information

### Improving Drawings
1. **Site Plan (Page 3)**:
   - Ensure 16x31 grid is generated correctly
   - Add lot boundary, house, tank, d-box, field, road
   - Include north arrow and scale
   - Add dimension annotations

2. **Disposal Plan (Page 4)**:
   - Generate proper field layout with rows
   - Label all components (tank, d-box, rows)
   - Add spacing requirements
   - Include design notes

3. **Hermes Coordination**:
   - Provide site coordinates from OpenClaw
   - Verify scaling matches HHE-200 requirements
   - Validate field dimensions and spacing

## Part 7: Integration Points

### Current Pipeline
```
run_pipeline_with_hermes_complete.py
├─ Sheet Parser: Extract data
├─ Hermes: Interpret and complete
├─ OpenClaw: Generate coordinates
├─ acro_fill.py: Fill form
├─ professional_drawings_with_data.py: Generate images
├─ Embed in PDF (form + images)
└─ hermes_quality_assessment.py: [NEW] Full assessment
    ├─ Form field extraction (pages 1-2)
    └─ drawing_comparison.py: Drawing analysis (pages 3-4)
```

### Assessment Output
- `quality_report.md`: Human-readable feedback
- `assessment_result.json`: Machine-readable scores and gaps
- `learning_feedback.txt`: Specific improvements for next iteration

## Next Steps

1. **Run Assessment**: `python run_pipeline_with_hermes_complete.py`
2. **Review Report**: Check `quality_report.md` for gaps
3. **Fix Gaps**: Either update data or adjust generation logic
4. **Iterate**: Re-run and compare scores
5. **Target**: Reach 95/100 across both form and drawings
