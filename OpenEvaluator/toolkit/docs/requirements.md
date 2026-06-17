---
title: HHE-200 Form Structure and Requirements
description: Detailed breakdown of the Maine DHHS HHE-200 subsurface wastewater disposal permit application form, including page layouts, field specifications, and drawing requirements.
created: 2024-01-15
updated: 2026-05-03
---

# HHE-200 Form Structure and Requirements

## Form Overview
The HHE-200: Subsurface Wastewater Disposal System Permit Application (Rev. 7/2025) is a multi-page Maine DHHS form used to permit septic system installations. AutoCAD drawings are submitted as attachments to specific pages depending on system type.

## Workflow Specification (Hermes Pipeline)

### End-to-End Flow

```
Step 1: Site Evaluator fills out Google Form (intake)
         │
         ▼
Step 2: Response lands in Google Sheet as new row
         │
         ▼
Step 3: Hermes triggered (form webhook or cron)
         │
         ▼
Step 4: Hermes reads new row from Google Sheet
         │
         ▼
Step 5: Hermes retrieves uploaded sketch from Drive (bouchlesshay@gmail.com, uploads attachment)
         │
         ▼
Step 6: Hermes processes:
         │
         ├─ a. Fills out HHE-200 PDF form fields using sheet row data
         │
         ├─ b. Generates AutoCAD-style drawing from sketch + data
         │
         ├─ c. Places drawing on correct page based on system type:
         │       │
         │       ├─ STANDARD SYSTEM ──► Pages 3 + 4
         │       │   Page 3: Site Plan + Soil Profile (GRID variant — hand-fill)
         │       │   Page 4: Disposal Plan + Cross-Section
         │       │
         │       └─ ENGINEERED/ALTERNATIVE (components 7/8/9) ──► Pages 7 + 8
         │           Page 7: Disposal plan (BLANK variant — for AutoCAD)
         │           Page 8: Cross-section (BLANK variant — for AutoCAD)
         │           (Replaces Pages 3+4)
         │
         ├─ d. Generates conditional attachments:
         │       │
         │       ├─ HHE-204  ── if variance requested
         │       ├─ GSB Soil Notes ── if referenced
         │       └─ HHE-300A ── if pre-treatment system selected
         │
         └─ e. Assembles all pages into one merged PDF document
         │
         ▼
Step 7: Hermes drafts and sends email to Site Evaluator with:
         ├─ Completed HHE-200 form (merged PDF)
         ├─ Each individual page as separate attachments
         ├─ Completed AutoCAD drawing
         ├─ Additional documents (204, 300A, GSB notes as applicable)
         └─ Note directing them to fill out correction form if anything needs changes
```

### Page Selection Logic

| System Type | Drawing Pages | Variant | Description |
|-------------|---------------|---------|-------------|
| **Standard** | Pages 3 + 4 | GRID | Grid-based templates for hand-filled site plans |
| **Engineered/Alternative** (components 7, 8, or 9 selected) | Pages 7 + 8 | BLANK | Blank AutoCAD templates for professional drawings |

**Engineered/Alternative System Triggers:**
- Component 7: Proprietary Device
- Component 8: Advanced Pre-Treatment
- Component 9: Alternative System Design

### Conditional Document Triggers

| Document | Condition |
|----------|-----------|
| HHE-204 | Variance requested in application |
| GSB Soil Notes | Soil notes referenced in submission |
| HHE-300A | Pre-treatment system with maintenance contract |

---

## Page 1: Permit Application

### Property Information
| Field | Description | Required |
|-------|-------------|----------|
| Property Address | Street address of the site | Yes |
| Issuing Municipality | City/Town/Plantation | Yes |
| Municipal Tax Map # | Tax map reference | Yes |
| Lot # | Lot number on tax map | Yes |
| Permit # / Date Issued | For replacement permits | Conditional |

### Property Owner/Applicant
| Field | Description |
|-------|-------------|
| Owner Name | Last, First |
| Applicant Name | If different from owner |
| Mailing Address | Street, City, State, Zip |
| Phone | Contact number |
| Email | Contact email |

### Application Type
- First Time System
- Replacement System (with year installed and type replaced)
- Expansion (<25% Minor or >25% Major)
- Seasonal Conversion Permit
- Experimental System

### Disposal System Components
| Category | Options |
|----------|---------|
| Treatment Tanks | Concrete (Regular/Low Profile/H-20), Plastic, External Grease Interceptor, Other |
| Disposal Fields | Stone Bed, Stone Trench, Proprietary Device, Cluster Array, Linear |
| Pumps | Effluent/Ejector Pump (capacity in gallons) |
| Pre-Treatment | Pre-Treatment Tank, Pre-Treatment Component (with make/model) |

### Variance Requirements
- No Rule Variance
- First Time System (LPI Only or State Required)
- Replacement System
- Minimum Lot Size
- Seasonal Conversion
- Other as specified

### Signatures
- Property Owner/Applicant signature
- Site Evaluator Statement with SE# and date
- Local Plumbing Inspector (LPI) signature areas

---

## Page 2: System Design Parameters

### Property and Use Details
| Field | Description |
|-------|-------------|
| Property Size | Square feet or acres |
| Disposal System to Serve | Single Family, Multiple Family, Accessory Dwelling, Other |
| Number of Bedrooms | For residential calculations |
| Current Use | Seasonal, Year-Round, Undeveloped, Commercial |
| Shoreland Zoning | Yes/No |
| Design Flow | Gallons per day |

### Water Supply Type
- Drilled Well
- Dug/Point Well
- Private
- Public
- Other (specify)

### Disposal Field Details
| Field | Description |
|-------|-------------|
| Disposal Field Type | Stone Bed, Stone Trench, Proprietary Device, Other |
| Field Size | Square feet or linear feet |
| Configuration | Cluster Array or Linear, Regular or Load |

### Soil Data
| Field | Description |
|-------|-------------|
| Soil Data Required | Yes/No/Maybe |
| At Observation Hole # | Reference to OH number |
| Limiting Factor Depth | Depth to limiting factor |
| Limiting Factor Elevation | Elevation of limiting factor |
| Profile Condition | Soil profile condition notes |

### System Components
| Component | Details |
|-----------|---------|
| Garbage Disposal Unit | Yes/No, Size if yes |
| Multi-compartment Tank | Number of tanks |
| Tanks in Series | Configuration |
| Increase Tank Capacity | If applicable |
| Filter on Tank Outlet | If applicable |

### Pre-Treatment Systems
| Field | Description |
|-------|-------------|
| Make | Manufacturer |
| Model | Model number |
| Notes | Additional details |
| Maintenance Contract | HHE-300A required (Yes/No) |

---

## Page 3: Site Plan and Soil Profile (Grid Version)

### Site Plan Area
The site plan is a scaled drawing requiring:

**Property Features:**
- Property boundaries with dimensions
- Existing structures (house, garage, etc.)
- Wells (existing and proposed)
- Roads or streets
- North arrow (true or magnetic)
- Scale indicator (e.g., 1" = 30')

**Disposal System Features:**
- Observation hole locations (labeled OH-1, OH-2, etc.)
- Proposed disposal area boundary
- Reserve area boundary
- Setback dimension lines to property lines
- Building setback lines

**Required Distances:**
- Distance from disposal area to property lines
- Distance from disposal area to wells
- Distance from disposal area to surface water
- Distance from disposal area to other structures

### Soil Profile Description Grid
Two observation holes per page, each with:

| Column | Description |
|--------|-------------|
| Organic Horizon Thickness | Depth of organic layer at surface |
| Ground Surface Elevation | Elevation at hole location |
| Depth to Exploration or Refusal | Total depth excavated |
| 0-48" at 6" intervals | Readings at each 6" depth increment |

**Per Depth Interval (0-48"):**
| Sub-column | Description |
|-----------|-------------|
| Texture | Soil texture (sand, loam, clay, etc.) |
| Consistence | Soil consistence (loose, firm, dense, etc.) |
| Color | Munsell color notation |
| Redox Features | Redoximorphic features present |

**Summary Fields per Observation Hole:**
| Field | Options |
|-------|---------|
| Soil Classification | Per NRCS classification |
| Slope | Percentage |
| Limiting Factor | Checkbox: Groundwater, Restrictive Layer, or Bedrock |
| Profile Condition | Notes on condition |
| Test Pit/Boring | Checkbox for excavation type |

---

## Page 4: Disposal Plan and Cross-Section

### Disposal Plan Area
Scaled drawing showing:

**System Components:**
- Septic tank location and dimensions
- Distribution box location
- Leaching field/bed location and dimensions
- Pump chamber location (if applicable)
- Connection pipes between components

**Elevation Information:**
- Elevation reference point (ERP) location and description
- Reference elevation value (0.0 or defined datum)

**Construction Details:**
- Depth of backfill (upslope)
- Depth of backfill (downslope)
- Finished grade elevation
- Top of distribution pipe elevation
- Bottom of disposal field elevation
- Construction elevations from reference point

### Cross-Section Area
Vertical profile drawing showing:

**Vertical Scale:** Typically 1" = 5' (larger than horizontal scale)

**Profile Elements:**
- Existing ground surface line
- Finished grade line
- Elevation reference point marker
- Top of distribution pipe or proprietary device
- Bottom of disposal field
- Depth markers at regular intervals

**Annotation Requirements:**
- Reference elevation (0.0 or specific value)
- Location and description of reference point
- Depths at cross-section location

---

## Pages 7+8: Engineered/Alternative Systems

For engineered or alternative systems (when components 7, 8, or 9 are selected):

- **Page 7**: Blank AutoCAD template for disposal plan drawing
- **Page 8**: Blank AutoCAD template for cross-section drawing

These pages replace the standard Pages 3+4 for:
- Proprietary devices
- Advanced pre-treatment systems
- Alternative system designs requiring engineering review

---

## Drawing Requirements Summary

### Site Plan Drawing (Page 3 Attachment)
| Requirement | Specification |
|-------------|---------------|
| Scale | Minimum 1" = 30' (or larger) |
| Format | AutoCAD DWG or PDF |
| Orientation | Portrait or landscape as needed |
| Elements | Property boundary, structures, wells, OH locations, disposal area, setbacks |

### Soil Profile Log Drawing (Page 3 Attachment)
| Requirement | Specification |
|-------------|---------------|
| Scale | 1" = 5' vertical for profile columns |
| Format | Match site plan format |
| Elements | Two observation hole profiles, 0-48" depth, annotation columns |

### Disposal System Plan Drawing (Page 4 or 7 Attachment)
| Requirement | Specification |
|-------------|---------------|
| Scale | Match site plan scale |
| Format | AutoCAD DWG or PDF |
| Elements | Tank, D-box, leaching area, pipes, elevation reference |

### Cross-Section Drawing (Page 4 or 8 Attachment)
| Requirement | Specification |
|-------------|---------------|
| Scale | 1" = 5' vertical (standard) |
| Horizontal Scale | Match disposal plan |
| Elements | Existing grade, finished grade, system components in section, elevations |

---

## Site Evaluator Sketch Analysis

### Field Worksheet Patterns (Form 26-018 Style)

Site evaluators typically complete field worksheets during site visits. These worksheets show distinctive patterns:

**Common Field Sketch Elements:**
1. **Rough Property Boundary** - Hand-drawn polygon approximating lot shape
2. **Structure Placement** - Simple rectangles for buildings with approximate dimensions
3. **Compass Rose** - Hand-drawn north arrow, occasionally labeled T (true) or M (magnetic)
4. **Observation Hole Markers** - Circles or squares with OH-1, OH-2 labels
5. **Gradient Shading** - Cross-hatching or stippling to indicate slope direction
6. **Measurement Ticks** - Short lines indicating measured distances

**Soil Profile Log Patterns:**
1. **Column Format** - Two vertical columns per observation hole
2. **Ruler Markings** - 6" interval marks along column edges
3. **Layer Transitions** - Wavy lines between soil horizons
4. **Color Swatches** - Small colored patches indicating Munsell colors (or written notations)
5. **Annotation Style** - Abbreviated text (Snd, Lm, Cl, Fr, Ds) for soil textures

**Disposal System Sketches:**
1. **Tank Symbol** - Rectangle with "ST" or "PT" label
2. **D-Box Symbol** - Small square or circle with "D" or "DB" label
3. **Leaching Area** - Rectangle with stone trench or bed pattern
4. **Pipe Lines** - Dashed lines connecting components
5. **Elevation Callouts** - Numbers in circles or boxes with up/down arrows

### Sketch-to-Drawing Translation

| Field Sketch Element | AutoCAD Translation |
|---------------------|---------------------|
| Hand-drawn boundary | POLYLINE with precise coordinates |
| Rough structure rectangles | BLOCK references or POLYLINEs |
| Circle OH markers | CIRCLE with label MTEXT |
| Cross-hatch slope indicators | HATCH patterns with gradient |
| Measurement ticks | DIMENSION entities |
| Wavy soil horizon lines | LWPOLYLINE with spline fit |
| Color swatches | HATCH with solid fill or text annotation |
| Tank/DB symbols | BLOCK library with attributes |
| Pipe connections | LINE or LWPOLYLINE entities |
| Elevation callouts | LEADER + MTEXT |

---

## Data Requirements for Drawing Generation

### Required Fields per Drawing Type

**Site Plan:**
- Property corner coordinates
- Structure locations and dimensions
- Well locations
- Observation hole coordinates (from GPS)
- Proposed disposal area boundary
- Reserve area boundary
- Scale and north reference

**Soil Profile:**
- Observation hole numbers
- Organic horizon thickness
- Ground surface elevation per hole
- Depth to refusal per hole
- Soil classification per horizon
- Texture, consistence, color, redox per 6" interval
- Slope percentage
- Limiting factor type and depth

**Disposal Plan:**
- Tank location and dimensions
- D-box location
- Leaching area location and dimensions
- Pipe invert elevations
- Elevation reference point location
- Reference elevation value

**Cross-Section:**
- Cross-section station location
- Ground surface elevations along line
- System component depths
- Reference elevation
- All construction elevations

---

## GCP Setup for Hermes

Hermes uses OAuth 2.0 (not service account) for full Gmail, Drive, and Sheets access.

### Credentials and Token Storage

| File | Path | Purpose |
|------|------|---------|
| Credentials | `~/.config/google_oauth_credentials.json` | OAuth 2.0 client ID/secr |
| Token store | `~/.config/google_token_store.json` | Access/refresh tokens |

### Required OAuth Scopes

```
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/spreadsheets.readonly
https://www.googleapis.com/auth/drive.readonly
```

### Setup Steps

1. **Enable GCP APIs** — Enable Gmail API, Google Sheets API, and Google Drive API in the GCP console.
2. **Create OAuth 2.0 credentials** — In GCP → APIs & Services → Credentials, create an OAuth 2.0 Client ID (Desktop app or Other). Download the JSON and place it at `~/.config/google_oauth_credentials.json`.
3. **Run initial auth** — Use the Hermes auth initialization command to trigger the OAuth consent flow and store the resulting tokens at `~/.config/google_token_store.json`.
4. **Verify** — Confirm tokens are persisted and that Hermes can read from Drive/Sheets and send via Gmail.

### Reference

- NousResearch hermes-agent `google-workspace` skill — OAuth 2.0 flow implementation
- Hermes config keys: `google_workspace_credentials_path`, `google_workspace_token_path`
