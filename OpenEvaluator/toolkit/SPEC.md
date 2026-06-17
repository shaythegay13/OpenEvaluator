---
title: OpenEvaluator Project Specification
description: Open-source toolkit for generating Maine DHHS HHE-200 subsurface wastewater disposal permit application drawings using Python and ezDXF.
created: 2024-01-15
updated: 2026-05-03
---

# OpenEvaluator Project Specification

## Overview
OpenEvaluator is an open-source toolkit for generating Maine DHHS HHE-200 subsurface wastewater disposal permit application drawings using Python and ezDXF. The system generates AutoCAD-compatible drawings from site evaluator field data.

## Purpose
Automate the production of professional HHE-200 form drawings (site plans, soil profile logs, disposal system layouts, cross-sections) from structured field data collected during site evaluations.

## Confirmed Workflow — OpenEvaluator (Hermes Pipeline)

### Trigger & Intake
1. **Site Evaluator** fills out the **Google Form** (intake questionnaire)
2. **Response** lands in **Google Sheet** as a new row
3. **Hermes** is triggered — by form submission webhook or cron check

### Processing Steps
4. **Hermes reads** the new row from Google Sheet
5. **Hermes retrieves** the uploaded sketch from **Google Drive** (`bouchlesshay@gmail.com`, uploads attachment linked from the sheet row)

6. **Hermes processes** the following sub-tasks:

   **a. Fills out the HHE-200 PDF form fields** using data from the sheet row**

   **b. Generates an AutoCAD-style drawing** from the sketch + data

   **c. Places the drawing on the correct page based on system type:**

   | System Type | Drawing Pages | Page 3+4 Variant | Notes |
   |-------------|--------------|------------------|-------|
   | **Standard system** | Pages 3 + 4 | GRID variant (hand-fill) | Site plan on p.3, cross-section on p.4 |
   | **Engineered/Alternative system** (components 7/8/9 selected) | Pages 7 + 8 | BLANK variant (for AutoCAD) | Replaces Pages 3+4 with blank templates |

   **d. Generates conditional attachments:**

   | Document | Trigger Condition |
   |---------|------------------|
   | **HHE-204** | Variance requested |
   | **GSB Soil Notes** | Referenced in submission |
   | **HHE-300A** | Pre-treatment system selected |

   **e. Assembles** all pages into one merged PDF document

7. **Hermes drafts and sends email** to Site Evaluator containing:
   - The completed **HHE-200 form** (merged PDF)
   - Each **individual page** as separate attachments
   - The completed **AutoCAD drawing**
   - Any **additional documents** (204, 300A, GSB notes)
   - A **note directing them to fill out the correction form** if anything needs to be changed

### Workflow Diagram
```
Google Form (Intake)
       │
       ▼
Google Sheet (New Row)
       │
       ▼
Hermes Triggered (Webhook / Cron)
       │
       ├──► Read Sheet Row
       ├──► Retrieve Sketch from Drive
       │
       ▼
┌──────────────────────────────────────────┐
│           HHERMES PROCESSING               │
│                                          │
│  a. Fill HHE-200 PDF form fields         │
│  b. Generate AutoCAD-style drawing       │
│                                          │
│  c. Page Selection Logic:                │
│     ├─ Standard system ──► Pages 3+4     │
│     │   (GRID variant for hand-fill)     │
│     │                                     │
│     └─ Engineered/Alt. ──► Pages 7+8    │
│         (components 7/8/9)               │
│         (BLANK variant for AutoCAD)      │
│                                          │
│  d. Conditional Attachments:             │
│     ├─ HHE-204 (if variance)            │
│     ├─ GSB Soil Notes (if referenced)   │
│     └─ HHE-300A (if pre-treatment)      │
│                                          │
│  e. Merge all pages into single PDF       │
└──────────────────────────────────────────┘
       │
       ▼
Email to Site Evaluator:
  ├─ HHE-200 merged PDF
  ├─ Individual page attachments
  ├─ AutoCAD drawing
  ├─ Additional docs (204/300A/GSB)
  └─ Correction form link
```

## Requirements

### Input Data
- Site evaluator field worksheet data (soil observations, percolation test results, GPS coordinates)
- Property boundary and feature survey data
- Elevation reference points
- Observation hole logs (minimum 2 per disposal area)
- Percolation test results
- Proposed system design parameters
- Hand-drawn sketch (scanned/uploaded via Google Form)

### Output Formats
- AutoCAD DWG format (primary)
- PDF export via ezDXF renderers
- Scalable drawings at standard engineering scales (1" = 20', 30', 40', 60')

### Form Complexity Notes
The HHE-200 form is a multi-page document requiring:

| Page | Content | Drawing Elements |
|------|---------|------------------|
| 1 | Application form, property/owner info, fee calculation | None (form fields) |
| 2 | System design parameters, soil data summary | None (form fields) |
| 3 | Site Plan + Soil Profile Description grids | Site plan, soil profile log |
| 4 | Disposal Plan + Cross-Section | Disposal system layout, cross-section |
| 7 | (Engineered/Alternative) Blank drawing area | AutoCAD drawing |
| 8 | (Engineered/Alternative) Blank drawing area | AutoCAD drawing |

**Drawing Complexity by Page:**
- Page 3: Site plan (parcel boundaries, features, observation hole locations) + 2× soil profile grids (48" depth, 6" intervals)
- Page 4: Disposal system plan (tank, distribution box, leaching area) + disposal area cross-section (vertical profile with elevation references)
- Pages 7+8: Engineered/Alternative system — blank AutoCAD templates replacing Pages 3+4

### Form Structure

#### Page 1: Permit Application
- Property address and issuing municipality
- Municipal tax map and lot numbers
- Property owner/applicant information
- Owner/applicant statement signature
- Installer information
- Type of application (First Time, Replacement, Expansion, Seasonal Conversion, Experimental)
- Disposal system components selection
- Site evaluator statement and signature
- Local Plumbing Inspector (LPI) signature areas

#### Page 2: System Design Parameters
- Property size and disposal system capacity
- Single vs. Multiple family dwelling details
- Water supply type (drilled well, dug well, private, public)
- Disposal field type and size (stone bed, stone trench, proprietary device)
- Soil data and design class
- Percolation test results
- Effluent/ejector pump specifications
- Garbage disposal unit
- Pre-treatment system details

#### Page 3: Site Plan and Soil Profile (Grid Version)
- **Site Plan Area**: Scaled drawing showing:
  - Property boundaries
  - Existing structures
  - Setback lines
  - Well locations
  - Observation hole locations (minimum 2)
  - Proposed disposal area and reserve area
  - North arrow and scale
- **Soil Profile Grids**: Two observation hole logs with columns at 0, 6, 12, 18, 24, 30, 36, 42, 48 inches
  - Texture, consistence, color, redox features per depth interval
  - Organic horizon thickness
  - Ground surface elevation
  - Depth to exploration or refusal
  - Soil classification, slope percentage
  - Limiting factor checkboxes (groundwater, restrictive layer, bedrock)
  - Profile condition

#### Page 4: Disposal Plan and Cross-Section
- **Disposal Plan Area**: Scaled drawing showing:
  - Septic tank location
  - Distribution box location
  - Leaching field/bed location
  - Elevation reference point
  - All setback dimensions
- **Cross-Section Area**: Vertical profile showing:
  - Existing grade line
  - Finished grade line
  - Top of distribution pipe
  - Bottom of disposal field
  - Depth of backfill (upslope and downslope)
  - Elevation reference point

## Drawing Outputs

### 1. Site Plan Drawing (HHE-200 Page 3)
- Property boundary with dimensions
- North arrow and scale bar
- All structures (house, existing well, other features)
- Observation hole locations with labels (OH-1, OH-2)
- Proposed disposal area boundary
- Reserve area boundary
- Setback dimension lines
- Road or street name

### 2. Soil Profile Log Drawing (HHE-200 Page 3)
- Two profile columns per observation hole
- 6-inch interval markers from 0-48"
- Layer colors based on Munsell soil colors
- Texture, consistence, color, redox annotations
- Depth to groundwater indicator
- Depth to restrictive layer or bedrock marker

### 3. Disposal System Plan Drawing (HHE-200 Page 4)
- Full system layout (tank, D-box, leaching area)
- Elevation reference point location and description
- All component dimensions
- Invert elevations at key points
- Finished grade contours

### 4. Cross-Section Drawing (HHE-200 Page 4)
- Vertical profile through disposal area
- Ground surface profile
- Proposed system components in section
- Elevation reference point (0.0 or defined datum)
- Scale: 1" = 5' vertical typically

## Technical Stack

### Core Libraries
- Python 3.10+
- ezDXF for DWG generation
- matplotlib for layout verification (optional)
- PyYAML for configuration

### Layer Conventions
| Layer Name | Description | Color (AutoCAD) |
|------------|-------------|-----------------|
| WALLS | Building outlines | White (7) |
| DIMENSIONS | All dimension lines | Cyan (4) |
| TEXT | All text annotations | White (7) |
| SITE_PLAN | Property boundaries, features | Yellow (2) |
| OBSERVATION | Observation hole markers | Green (3) |
| SOIL_PROFILE | Soil profile columns | Brown (8) |
| DISPOSAL_SYS | Disposal system components | Magenta (6) |
| CROSS_SECTION | Cross-section outlines | Red (1) |
| ELEVATIONS | Elevation markers | Cyan (4) |
| SETBACKS | Setback dimension lines | Yellow (2) |

## Integration
- CLI tool: `python -m openevaluator generate --input data.yaml --output drawing.dwg`
- Python API: `from openevaluator import DrawingGenerator; gen = DrawingGenerator(config); gen.render()`
- Web interface: Future consideration
- Hermes pipeline: Google Form → Sheet → Drive → PDF assembly → Email

## Installation
```bash
pip install ezdxf pyyaml matplotlib
git clone https://github.com/openevaluator/openevaluator.git
cd openevaluator
pip install -e .
```

## Usage
```bash
# Generate drawing from YAML config
python -m openevaluator generate --config example.yaml --output output.dwg

# Validate input data
python -m openevaluator validate --config example.yaml

# Export to PDF
python -m openevaluator export --input drawing.dwg --format pdf
```

## File Structure
```
openevaluator/
├── docs/
│   ├── requirements.md      # Detailed HHE-200 form breakdown + workflow
│   ├── drawing_spec.md      # AutoCAD drawing specifications
│   └── email_template.md    # Hermes email template
├── scripts/
│   ├── generate_drawing.py  # Main drawing generation script
│   └── hermes_flowchart.md  # Hermes pipeline flowchart
├── src/
│   └── openevaluator/
│       ├── __init__.py
│       ├── drawing.py       # Core drawing class
│       ├── layers.py        # Layer definitions
│       ├── site_plan.py     # Site plan generation
│       ├── soil_profile.py  # Soil profile generation
│       ├── disposal_plan.py # Disposal system plan
│       ├── cross_section.py # Cross-section generation
│       └── config.py        # Configuration handling
├── tests/
│   └── test_drawing.py
└── examples/
    └── sample_config.yaml
```
