---
title: Hermes Learning Guide - HHE-200 Multi-Example Comparison Framework
description: Framework for Hermes to identify and learn from document/drawing generation faults by comparing against multiple pinnacle examples
created: 2026-06-14
updated: 2026-06-14
---

# Hermes Learning Guide: HHE-200 Generator Improvement Framework

**Date:** June 14, 2026  
**Purpose:** Enable Hermes to systematically identify faults in HHE-200 document and drawing generation by comparing against multiple pinnacle examples

---

## Overview

You now have **4 generated test PDFs** ready to compare against **2 pinnacle example sets**. This multi-example approach gives you richer learning signals:

- **Row 2 (26-018):** Live data - your dad's actual client work
- **Row 3:** Synthetic test 1 - baseline reference
- **Row 4:** Synthetic test 2 - baseline reference  
- **Row 5:** Live data - another real property

Each generated PDF should be compared to both example folders to identify patterns in how your generation diverges from professional quality.

---

## Comparison Matrix

```
Generated PDF  vs  Example 1 (26-018)  +  Example 2 (26-123)
                        ↓                        ↓
                   7 comparison items      4 comparison items
                   (Form + extras)         (Form pages only)
```

**Total evaluation scope:** 8 comparison pairs (4 generated × 2 examples)

---

## What to Evaluate for Each Comparison

### Pages 1-2: Form Fields & Data Accuracy

**What to check:**
- [ ] Owner name is populated and correctly formatted
- [ ] Property address is complete and correctly positioned
- [ ] Tax map number and lot number present
- [ ] Acreage value filled in
- [ ] Soil information populated from sketch extraction
- [ ] Groundwater depth and limiting factors recorded
- [ ] System type correctly identified
- [ ] Tank capacity shown
- [ ] Field sizing and layout specifications filled
- [ ] Signature blocks included
- [ ] Date fields present

**Scoring criteria:**
- **Excellent (90-100%):** All fields populated correctly, formatting matches example
- **Good (75-89%):** Most fields correct, minor formatting differences
- **Fair (60-74%):** Basic structure present, several fields missing or incorrect
- **Needs Work (<60%):** Many fields missing or data is wrong

**What Hermes should learn:**
- Which form fields are consistently populated?
- Which fields are frequently blank or wrong?
- Do certain properties cause more field errors?
- Is the issue with data extraction or form filling?

---

### Page 3: Site Plan Drawing Quality

**Visual elements to compare:**

**Structure & Layout:**
- [ ] Property boundary drawn with corner markings (X marks)
- [ ] House positioned correctly relative to boundaries
- [ ] Septic tank placed in correct location
- [ ] Disposal field area delineated
- [ ] Observation holes (OH-1, OH-2, etc.) marked and numbered
- [ ] Well location shown if present
- [ ] Trees or other reference markers drawn

**Annotations & Dimensions:**
- [ ] Distance callouts present (e.g., "8' house to tank")
- [ ] Street name labeled (e.g., "ASPEN WAY")
- [ ] Adjacent lot numbers shown (LOT 6, LOT 8, etc.)
- [ ] Adjacent street names included
- [ ] Scale notation present (e.g., "1\" = 40'")
- [ ] North arrow shows correct orientation
- [ ] Grid background with appropriate density

**Professional Quality:**
- [ ] Line weights consistent (solid vs. dashed appropriately)
- [ ] Fill patterns used correctly (field hatching, etc.)
- [ ] Text size and font consistent
- [ ] Dimensions clearly readable
- [ ] Overall appearance professional and clean

**Scoring criteria:**
- **Excellent (90-100%):** Nearly indistinguishable from example, all elements present, professional quality
- **Good (75-89%):** All major elements present, minor detail differences
- **Fair (60-74%):** Basic structure correct, missing some annotations or detail
- **Needs Work (<60%):** Major elements missing or incorrectly sized/positioned

**What Hermes should learn:**
- Are elements consistently sized correctly?
- Are annotations/callouts being generated?
- Is the professional appearance matching?
- Which specific elements are most often wrong?
- Does accuracy differ between property types?

---

### Page 4: Disposal Plan & Cross-Section

**Top Section - Tank & Distribution System:**
- [ ] Septic tank drawn with correct dimensions
- [ ] Tank labeled (capacity in gallons)
- [ ] Distribution box (D-box) shown if applicable
- [ ] Connection pipes from tank to D-box drawn
- [ ] D-box to field distribution pipes shown
- [ ] House position shown relative to tank
- [ ] All components properly proportioned

**Middle Section - Disposal Field:**
- [ ] Field modules drawn in correct arrangement (rows × modules)
- [ ] Module dimensions shown
- [ ] Row spacing accurate
- [ ] Module spacing/sizing proportional
- [ ] Trenches or distribution lines shown
- [ ] Perforated vs. solid pipe differentiated if applicable
- [ ] Fill materials indicated

**Bottom Section - Cross-Section:**
- [ ] Soil layers shown with correct depths
- [ ] Soil type labels present
- [ ] Groundwater level marked
- [ ] Elevation references shown
- [ ] Device or module depth shown
- [ ] Backfill requirements indicated
- [ ] Scale appropriate for detail

**Quality Elements:**
- [ ] Tank/D-box sizing proportionally correct
- [ ] Field module proportions match example
- [ ] Cross-section shows proper soil stratification
- [ ] Dimension strings clear and readable
- [ ] Leader lines point to correct features
- [ ] Professional appearance and polish

**Scoring criteria:**
- **Excellent (90-100%):** All elements present, sizing/spacing accurate, professional presentation
- **Good (75-89%):** Major elements correct, minor spacing/sizing differences acceptable
- **Fair (60-74%):** Basic layout correct, notable differences in sizing or missing details
- **Needs Work (<60%):** Significant layout or sizing errors, poor quality presentation

**What Hermes should learn:**
- Is sizing calculation algorithm correct?
- Are elements positioned proportionally?
- Are dimension callouts being generated?
- Is cross-section detail showing properly?
- Which properties generate the most accurate drawings?

---

## Scoring Process

### Step 1: Extract Differences for Each Comparison

For **Row 2 vs Example 1**, create a list like:

```
PAGE 1-2: Form Fields
✓ Owner name: "Kristen Marquis" - CORRECT
✓ Property address: "17 Aspen Way, Turner, Maine 04282" - CORRECT
✗ Soil depth field: BLANK - should show "36 inches"
✓ Tank capacity: "1000 gallons" - CORRECT
~ Field layout: Shows "3x7 modules" - Example shows "3x7 GSF-B43" - MINOR DIFFERENCE

PAGE 3: Site Plan
✓ Property boundary marked with corner Xs - CORRECT
✓ House labeled "EXISTING HOUSE" - CORRECT  
✓ Tank positioned 8' from house - CORRECT
✗ Adjacent lot numbers: MISSING - should show "LOT 6, LOT 8"
~ Grid density: Appears slightly finer than example - MINOR
```

### Step 2: Score Each Page

Assign a score per page:

```
Row 2 vs Example 1:
  Page 1: GOOD (82%) - Most fields correct, minor formatting differences
  Page 2: GOOD (80%) - Form fields mostly complete
  Page 3: FAIR (71%) - Site plan layout correct but missing adjacent property labels
  Page 4: GOOD (78%) - Disposal plan structure correct, some sizing differences
  OVERALL: FAIR (77%)

Row 2 vs Example 2:
  Page 1: FAIR (68%) - Some field differences due to different property
  Page 2: FAIR (70%) - Form layout similar but content differs
  Page 3: FAIR (65%) - Site plan structure different property type
  Page 4: FAIR (67%) - Different disposal system layout
  OVERALL: FAIR (67%)
```

### Step 3: Identify Patterns Across All Comparisons

After scoring all 8 pairs, look for patterns:

```
CONSISTENT PATTERNS (appear in most/all comparisons):
  • Page 3 site plans: Missing adjacent property labels (HIGH PRIORITY)
  • Page 4 cross-section: Soil layer details sometimes unclear (MEDIUM PRIORITY)
  • Form fields: Some optional fields consistently blank (DEPENDS ON DATA)

PROPERTY-SPECIFIC PATTERNS:
  • Row 2 (26-018): Field modules calculated correctly
  • Row 5 (Unknown): Check if pattern matches or differs

BIGGEST QUALITY GAPS:
  • Missing annotation callouts on drawings
  • Some dimension strings not being generated
  • Color fills or hatching patterns inconsistent
```

### Step 4: Prioritize Improvements

Based on frequency × impact:

```
TIER 1 (Do First - Appears in ALL/MOST comparisons):
  1. Generate adjacent property labels on site plans
  2. Improve soil layer visualization on cross-sections
  3. Add missing dimension callouts to drawings

TIER 2 (Do Next - Appears in MOST comparisons):
  1. Consistent professional line weights
  2. Complete all optional form fields when data available
  3. Better proportioning of field modules

TIER 3 (Do Later - Appears in SOME comparisons):
  1. Edge cases for specific property types
  2. Styling polish and professional appearance
  3. Advanced annotation features
```

---

## Expected Outputs Location

All test data and comparison materials are in:

```
/home/workspace/OpenEvaluator/test_results/20260614_190036/
├── row_2/
│   ├── HHE-200-row2.pdf
│   ├── row2_page3_*.png
│   ├── row2_page4_*.png
│   └── hermes_row2.json
├── row_3/
├── row_4/
└── row_5/

/home/workspace/OpenEvaluator/example/
├── example 1/
│   ├── 26-018 PG1 (1).pdf
│   ├── 26-018 PG2 (1).pdf
│   ├── 26-018 PG3 (1).pdf
│   └── 26-018 PG4 (1).pdf
└── example 2/
    ├── 26-123 PG1.pdf
    ├── 26-123 PG2.pdf
    ├── 26-123 PG3.pdf
    └── 26-123 PG4.pdf
```

---

## Quick Reference: What Each Example Shows

### Example 1: 26-018 (Kristen Marquis, 17 Aspen Way)

- **Property Type:** Replacement system on existing property
- **System Type:** Eljen-in Drain with 3×7 GSF-B43 modules
- **Tank:** 1,000 gallons
- **Soil:** Brown sandy loam, groundwater at 24 inches
- **Layout:** Standard suburban property with adjacent lots
- **Drawing Quality:** Professional CAD rendering
- **Complexity:** Moderate (typical residential)

**Use this to understand:** Standard form layout, typical site plan and disposal field arrangement, professional drawing standards

### Example 2: 26-123

- **Property Type:** [Determine from your examples]
- **System Type:** [Determine from examples]
- **Unique Features:** [Note differences from Example 1]

**Use this to understand:** How layouts differ for different property types, verify that generation adapts to varied scenarios

---

## Next Steps for Hermes

1. **Open all 8 comparison pairs** (4 generated PDFs vs 2 examples)
2. **Create a comparison worksheet** documenting differences per page
3. **Score each comparison** using the framework above
4. **Identify top 3 issues** appearing most frequently
5. **Implement fixes** in the generator code
6. **Re-run test suite** to verify improvements
7. **Re-score** and confirm changes are working
8. **Iterate** until pages reach "Good" or "Excellent" status

---

## Success Criteria

**When to stop iterating:**
- ✅ Pages 1-2: All form fields populated correctly (90%+)
- ✅ Page 3: Site plan visually accurate with all callouts (85%+)
- ✅ Page 4: Disposal plan and cross-section professional quality (85%+)
- ✅ Overall: Generated PDFs look professional and complete

---

## Key Insight for Learning

**Why compare to BOTH examples:**

Each example shows what "good" looks like for different properties. By comparing your generated output to both:
- You see patterns that work across properties (design principles)
- You identify property-specific variations (data handling)
- You learn what professional quality actually means (multiple reference points)
- You can improve more systematically (patterns vs. single case)

This multi-example approach helps you build better generalizations than comparing to just one example.

---

**Document prepared:** June 14, 2026 19:09 UTC  
**Ready for Hermes to begin detailed comparison and learning**
