# HHE-200 Drawing Specifications

## Overview
This document specifies the technical requirements for generating AutoCAD-compatible drawings that accompany the HHE-200 Subsurface Wastewater Disposal System Permit Application.

## Drawing Set

| Drawing | HHE-200 Page | Contents |
|---------|--------------|----------|
| Site Plan | Page 3 | Property boundary, structures, features, observation holes |
| Soil Profile Log | Page 3 | Two observation hole vertical profiles |
| Disposal System Plan | Page 4 | Tank, D-box, leaching area layout |
| Cross-Section | Page 4 | Vertical profile through disposal area |

---

## Layer Conventions

### Standard Layer Setup

| Layer Name | Description | Color (ACI) | Linetype | Lineweight |
|------------|-------------|------------|----------|------------|
| 0 | Default layer | White | CONTINUOUS | 0.25mm |
| WALLS | Building outlines | White (7) | CONTINUOUS | 0.50mm |
| WALLS-EXIST | Existing structure outlines | White (7) | CONTINUOUS | 0.50mm |
| WALLS-PROPOSED | Proposed structure outlines | Cyan (4) | CONTINUOUS | 0.50mm |
| PROPERTY | Property boundary | Yellow (2) | CONTINUOUS | 0.70mm |
| PROPERTY-EASEMENT | Easement lines | Yellow (2) | DASHDOT | 0.50mm |
| DIMENSIONS | All dimension lines | Cyan (4) | CONTINUOUS | 0.25mm |
| DIM-ANGULAR | Angular dimensions | Cyan (4) | CONTINUOUS | 0.25mm |
| DIM-LINEAR | Linear dimensions | Cyan (4) | CONTINUOUS | 0.25mm |
| DIM-RADIAL | Radius dimensions | Cyan (4) | CONTINUOUS | 0.25mm |
| TEXT | General text annotations | White (7) | — | — |
| TEXT-ANNO | Annotation text | White (7) | — | — |
| TEXT-LABEL | Feature labels | White (7) | — | — |
| TEXT-TITLE | Drawing title text | White (7) | — | — |
| TEXT-ELEV | Elevation text | Cyan (4) | — | — |
| SITE_PLAN | Site plan features | Yellow (2) | CONTINUOUS | 0.35mm |
| FEATURES-ROAD | Road features | Yellow (2) | CONTINUOUS | 0.35mm |
| FEATURES-WELL | Well locations | Blue (5) | CONTINUOUS | 0.35mm |
| FEATURES-STRUCTURE | Structure markers | White (7) | CONTINUOUS | 0.35mm |
| OBSERVATION | Observation hole markers | Green (3) | CONTINUOUS | 0.35mm |
| OH-MARKER | OH location circles | Green (3) | CONTINUOUS | 0.35mm |
| OH-LABEL | OH number labels | Green (3) | — | — |
| SOIL_PROFILE | Soil profile columns | Brown (8) | CONTINUOUS | 0.25mm |
| SP-HEADER | Profile header row | Brown (8) | CONTINUOUS | 0.50mm |
| SP-GRID | Profile grid lines | Brown (8) | CONTINUOUS | 0.13mm |
| SP-LAYER | Soil horizon boundaries | Brown (8) | CONTINUOUS | 0.35mm |
| SP-LABEL | Soil texture/label text | Brown (8) | — | — |
| SP-REDOX | Redox feature markers | Red (1) | CONTINUOUS | 0.25mm |
| DISPOSAL_SYS | Disposal system components | Magenta (6) | CONTINUOUS | 0.50mm |
| DS-TANK | Septic tank outline | Magenta (6) | CONTINUOUS | 0.50mm |
| DS-DBOX | Distribution box | Magenta (6) | CONTINUOUS | 0.50mm |
| DS-LEACH | Leaching area boundary | Magenta (6) | CONTINUOUS | 0.50mm |
| DS-PIPE | Pipe connections | Magenta (6) | CONTINUOUS | 0.35mm |
| DS-PROPRIETARY | Proprietary device | Magenta (6) | CONTINUOUS | 0.50mm |
| CROSS_SECTION | Cross-section outlines | Red (1) | CONTINUOUS | 0.50mm |
| XS-GRADE-EXIST | Existing grade line | Red (1) | CONTINUOUS | 0.50mm |
| XS-GRADE-FIN | Finished grade line | Cyan (4) | CONTINUOUS | 0.50mm |
| XS-SYSTEM | System in section | Magenta (6) | CONTINUOUS | 0.50mm |
| XS-BACKFILL | Backfill area | Brown (8) | HATCH | — |
| ELEVATIONS | Elevation markers | Cyan (4) | CONTINUOUS | 0.35mm |
| EL-MARKER | Elevation point markers | Cyan (4) | CONTINUOUS | 0.35mm |
| EL-CALLOUT | Elevation callout text | Cyan (4) | — | — |
| EL-REFERENCE | Reference point markers | Red (1) | CONTINUOUS | 0.50mm |
| SETBACKS | Setback dimension lines | Yellow (2) | CONTINUOUS | 0.35mm |
| SB-LINE | Setback lines | Yellow (2) | CONTINUOUS | 0.35mm |
| SB-DIM | Setback dimensions | Yellow (2) | CONTINUOUS | 0.25mm |
| HATCH | Hatched areas | Various | SOLID | — |
| HATCH-SOIL | Soil pattern hatching | Brown (8) | ANSI31 | — |
| HATCH-STONE | Stone/gravel hatching | Gray (8) | ANSI37 | — |
| HATCH-ROCK | Bedrock/ledge hatching | Red (1) | ROCK | — |
| HATCH-WATER | Water / groundwater | Blue (5) | ANSI33 | — |

---

## Scale Requirements

### Standard Engineering Scales

| Scale | Use Case | Typical Drawing Size |
|-------|----------|----------------------|
| 1" = 20' | Small lots, dense development | 8.5" × 11" |
| 1" = 30' | Standard residential lot | 8.5" × 11" |
| 1" = 40' | Larger lots, rural properties | 11" × 17" |
| 1" = 60' | Large properties, commercial | 11" × 17" or larger |

### Vertical Scales (Cross-Sections)

| Scale | Use Case |
|-------|----------|
| 1" = 5' | Standard cross-section |
| 1" = 10' | Deep excavations, steep slopes |
| 1" = 2' | Detailed component sections |

### Dimension Style Settings

```
DIMSTYLE NAME: HHE200
SCALE: 1
TEXT HEIGHT: 0.08"
ARROW SIZE: 0.08"
_extension lines: 0.0625"
_extension offset: 0.0625"
TOLERANCE: None
UNITS: DECIMAL
PRECISION: 0
LEADING ZEROS: No
```

---

## Annotation Standards

### Text Styles

| Style Name | Font | Height | Width |
|------------|------|--------|-------|
| STANDARD | Arial | — | 0.7 |
| ELEVATION | Arial | — | 0.7 |
| LABEL | Arial | — | 0.7 |
| TITLE | Arial | 0.125" | 0.7 |

### Text Heights

| Element | Minimum Height | Notes |
|---------|----------------|-------|
| Drawing title | 0.125" | Bold |
| Owner/address header | 0.10" | — |
| Dimension text | 0.08" | — |
| General annotations | 0.08" | — |
| Elevation callouts | 0.10" | — |
| OH labels | 0.10" | Bold |
| Soil texture labels | 0.06" | — |
| Legend text | 0.06" | — |

### Leader/Callout Standards
- Arrow head: Closed filled
- Leader length: Minimum 0.25"
- Text attachment: Left for single-line, aligned for multi-line

---

## Site Plan Drawing Specification

### Required Elements

**Border and Header:**
- Border: 0.5" margin on all sides
- Title block in lower right: "HHE-200 SITE PLAN - SHEET 1 OF _"
- Owner name and address in title block
- Scale indicator: "SCALE: 1" = ___"
- North arrow (true or magnetic noted)
- Date and revision block

**Property Features:**
- Property boundary polyline
- Lot dimensions at each segment
- Existing structures (WALLS-EXIST layer)
- Proposed structures (WALLS-PROPOSED layer)
- Wells with W label (FEATURES-WELL layer)
- Roads with edge lines and names
- Other significant features (trees, rock outcrops, wetlands boundary)

**Disposal System Features:**
- Observation hole locations (OH-MARKER circles, OH-LABEL text)
- OH number: "OH-1", "OH-2" etc.
- Proposed disposal area boundary (DISPOSAL_SYS layer)
- Reserve area boundary (dashed line)
- Setback lines from disposal area to:
  - Property lines
  - Wells
  - Surface water
  - Other structures

**Dimensions:**
- Property line distances
- Setback distances (DIM layer)
- Structure dimensions
- OH coordinates (if required)

### Sample Layout (8.5" × 11")

```
+--------------------------------------------------+
|  OWNER: John Smith          SCALE: 1" = 30'       |
|  ADDRESS: 123 Main St       DATE: 01/15/2025     |
|  Auburn, Maine              BY: Site Evaluator    |
|                               SE#: 1234           |
|                                                  |
|                    [N]                           |
|                    /|\                          |
|                                                  |
|     +--------+                                  |
|     | HOUSE  |    OH-1                           |
|     |        |     o                             |
|     +--------+                      +---------+  |
|                    |         |     | RESERVE |  |
|                    |         |     |  AREA   |  |
|                    +--o------+     +---------+  |
|                       OH-2          +-------+   |
|                                    |DISPOSAL|   |
|                                    | FIELD  |   |
|                                    +-------+   |
|     ===========  ROAD  ===========           |
|                                                  |
|  [LEGEND]              HHE-200 SITE PLAN        |
|  o = Observation Hole                         |
+--------------------------------------------------+
```

---

## Soil Profile Log Drawing Specification

### Grid Structure

**Profile Columns:** Two observation hole columns per drawing, each with:
- Header row: "OBSERVATION HOLE #__"
- Sub-header row: "Organic Horizon Thickness: ___\""
- Depth column: 0, 6, 12, 18, 24, 30, 36, 42, 48
- Data rows per depth interval: Texture, Consistence, Color, Redox Features

**Column Width:** 3.0" per observation hole column
**Row Height:** 0.3" per depth interval
**Header Height:** 0.5" for main header, 0.25" for sub-header

### Required Elements

**Column Headers:**
- Observation hole number
- Organic horizon thickness value
- Ground surface elevation
- Test pit or Boring checkbox
- Depth to exploration or refusal

**Data Cells:**
- Texture: Abbreviated soil texture (Snd, Lm, Si, Cl, Gr, etc.)
- Consistence: Firmness (Lse, Fr, Fi, VFi, Dns)
- Color: Munsell notation (10YR 4/3, etc.)
- Redox Features: Present/Absent or specific notation

**Summary Section below grid:**
- Soil Classification text field
- Slope % field
- Limiting Factor checkboxes (Ground water, Restrictive Layer, Bedrock)
- Profile Condition notes
- Test Pit/Boring checkbox

### Color Coding for Soil Horizons

| Soil Type | Hatch Pattern | Fill Color |
|-----------|--------------|------------|
| Sand | ANSI31 | 253 (light sand) |
| Loamy Sand | ANSI31 | 254 (light tan) |
| Sandy Loam | ANSI32 | 252 (tan) |
| Loam | ANSI32 | 251 (brown-tan) |
| Silt Loam | ANSI35 | 250 (gray-brown) |
| Clay Loam | ANSI37 | 249 ( reddish-brown) |
| Clay | ANSI37 | 248 (red clay) |
| Gravel | ANSI33 | 256 (gray) |
| Bedrock | ROCK | 0 (ByBlock) |
| Fill | CROSS | 9 (light gray) |

### Sample Layout

```
+---------------------------+---------------------------+
|    OBSERVATION HOLE #1    |    OBSERVATION HOLE #2    |
| Organic Horz Thickness: 4"| Organic Horz Thickness: 3"|
| Ground Surf Elev: 245.2'  | Ground Surf Elev: 244.8'  |
| Test Pit [X]  Boring [ ]  | Test Pit [ ]  Boring [X]  |
| Depth to Refusal: 48"     | Depth to Refusal: 36"     |
+----+----------+----------+----+----------+----------+
| Dp | Texture| Consist|Color| Dp | Texture| Consist|Colr|
+----+--------+--------+------+----+--------+--------+---+
| 0  | Org    | Lse    | 2.5Y| 0  | Org    | Lse    |2.5Y|
+----+--------+--------+------+----+--------+--------+---+
| 6  | Snd    | Lse    |10YR5| 6  | Snd    | Fr     |10YR4|
+----+--------+--------+------+----+--------+--------+---+
|12  | Snd    | Fr     |10YR5| 12 | Lm     | Fr     |10YR4|
+----+--------+--------+------+----+--------+--------+---+
|18  | Lm     | Fr     |10YR4| 18 | Lm     | Fi     |10YR5|
+----+--------+--------+------+----+--------+--------+---+
|24  | SiCl   | Fi     |10YR4| 24 | SiCl   | VFi    |10YR4|
+----+--------+--------+------+----+--------+--------+---+
|30  | Cl     | VFi    | 5Y5 | 30 | Cl     | Dns    | 5Y5 |
+----+--------+--------+------+----+--------+--------+---+
|36  | Cl     | Dns    | 5Y6 | 36 | ======= BEDROCK ======| 
+----+--------+--------+------+----+--------+--------+---+
|42  | ====== BEDROCK ====== | 42 |        | | | | | | |
+----+--------+--------+------+----+--------+--------+---+
|48  |        | | | | | | | | 48 |        | | | | | | |
+----+--------+--------+------+----+--------+--------+---+
|Soil Class: Chatfield SltL |Soil Class: Lamoine CL    |
|Slope: 3%  Lim Factor: [ ]GW [X]RL [ ]BD|[ ]GW [ ]RL [X]BD|
|Signature: ____________ SE#: 1234 Date: 1/15/25       |
+---------------------------+---------------------------+
```

---

## Disposal System Plan Drawing Specification

### Required Elements

**System Components:**
- Septic tank (rectangle, labeled ST or PT with capacity)
- Distribution box (square or circle, labeled D-BOX)
- Leaching area (rectangle or custom shape per design)
- Pump chamber (if applicable, labeled PC or Pump)
- Connecting pipes (dashed lines showing inverts)

**Elevation Reference Point (ERP):**
- Physical marker location with coordinates
- Reference elevation value
- Description of location

**Construction Details:**
- All invert elevations at key points
- Pipe slopes
- Depth of cover
- Depth of backfill (upslope/downslope)

### Sample Layout

```
+--------------------------------------------------+
|  ERP: Iron rebar at NW corner of tank            |
|  Reference Elev: 0.0 = 245.50'                   |
|                                                  |
|              +-----------+                       |
|              |    ST     |  Top of Pipe: 243.2' |
|              |  1500 gal |  Bottom of Pipe:243.0'|
|              +-----------+                       |
|                  |                               |
|                  | 4" DROP                       |
|                  |                               |
|              +-----------+                       |
|              |   D-BOX   |  Invert: 242.8'       |
|              +-----------+                       |
|             / | | | | | | \                      |
|            /  | | | | | |  \                     |
|       +---------------------------+              |
|       |      LEACHING BED          | Bottom Elv: |
|       |                           |   241.5'    |
|       +---------------------------+              |
|                                                  |
|  BACKFILL: Upslope 18" / Downslope 24"          |
+--------------------------------------------------+
```

---

## Cross-Section Drawing Specification

### Required Elements

**Profile Line:**
- Cross-section station location marked on disposal plan
- Horizontal scale matches disposal plan
- Vertical scale: 1" = 5' (standard)

**Grade Lines:**
- Existing ground surface (XS-GRADE-EXIST, Red)
- Finished grade (XS-GRADE-FIN, Cyan)

**System Components in Section:**
- Tank section (XS-SYSTEM, Magenta)
- Distribution box section
- Leaching bed section
- Pipe invert line

**Elevations:**
- Reference elevation marker (EL-REFERENCE)
- Ground surface elevations at stations
- Top of pipe elevation
- Bottom of disposal area elevation
- Finished grade elevation

**Backfill:**
- Hatched area showing backfill material (XS-BACKFILL)

### Sample Layout

```
ELEVATION
|
245.5'  +------------------- EXISTING GRADE LINE
        |                   .
244.0'  |   +-----------+   .   FINISHED GRADE
        |   |    TANK   |   .
        |   |  (section)|   .
        |   +-----------+   .
243.2'  |----------- TOP OF DISTRIBUTION PIPE
        |
241.5'  |......BOTTOM OF DISPOSAL FIELD..........
        |
240.0'  +------------------- REFERENCE (0.0)

        |<------ 40' ------>|
           CROSS-SECTION A-A
```

---

## Field Worksheet vs. Final Drawing Comparison

### Form 26-018 Field Worksheet Patterns

Site evaluators typically complete hand-drawn field worksheets during site visits. The worksheets contain:

**Sketch Characteristics:**
| Element | Field Worksheet | Final Drawing |
|---------|-----------------|---------------|
| Property boundary | Approximate polygon, hand-drawn | Precise POLYLINE from survey |
| Structures | Rough rectangles with approximate dims | Precise BLOCK or POLYLINE |
| North arrow | Hand-drawn compass rose | Defined BLOCK with attribute |
| OH locations | Circles with "OH-1" text | CIRCLE + MTEXT with coordinates |
| Measurements | Short ticks with written values | DIMENSION entities |
| Soil colors | Small color patches or written Munsell | HATCH or MTEXT annotation |
| Elevations | Numbers in boxes | EL-CALLOUT MTEXT |

**Common Field Sketch Annotations:**
- "OH" with circled number
- "DWB" or "D-box" for distribution box
- "LF" or "SF" for leaching field/bed size
- Up/down arrows for grade changes
- "ERP" with circle for elevation reference
- "~" or wavy lines for estimated contours

### Translation Guide

| Field Sketch | AutoCAD Entity | Notes |
|-------------|----------------|-------|
| Hand-drawn boundary | LWPOLYLINE (close=yes) | Use precise coordinates |
| Rough rectangles | INSERT (block) | Create from survey data |
| Circle markers | CIRCLE + MTEXT | OH-1, OH-2, etc. |
| Arrow symbols | LEADER + MTEXT | Elevation callouts |
| Wavy horizon lines | LWPOLYLINE with arc segments | Soil layer boundaries |
| Color patches | HATCH or solid-filled TEXT | Based on Munsell notation |
| Tank symbol "ST" | INSERT (block with attributes) | Include capacity attribute |
| D-box symbol "D" | INSERT (block) | Standardized block |
| Pipe dashed lines | LINE with PLOTSTYLE dash | Or LAYER with linetype |
| Elevation numbers | MTEXT with frame | Match field values exactly |

---

## AutoCAD Block Definitions

### Required Blocks

**OBS_HOLE**
- Circle (radius 0.15") on layer OBSERVATION
- Attribute: OH_NUMBER (height 0.10", justify center)
- Attribute: ELEVATION (height 0.08", justify center, below number)

**TANK**
- Rectangle with label
- Attributes: CAPACITY, INVERT_ELEV, TOP_ELEV

**DIST_BOX**
- Square with D label
- Attribute: INVERT_ELEV

**LEACH_AREA**
- Rectangle with pattern
- Attributes: AREA_SQFT, BOTTOM_ELEV

**NORTH_ARROW**
- Standard compass rose block
- Attribute: NORTH_TYPE (True/Magnetic)

**ELEV_REF**
- Circle with crosshairs
- Attribute: REF_ELEV
- Attribute: DESCRIPTION

**PROFILE_MARKER**
- Small triangle with station label
- Attribute: STATION

---

## Output Requirements

### File Format
- Primary: AutoCAD DWG (version 2013 or later compatible)
- Secondary: DXF for compatibility

### Plot Settings
- Paper size: 8.5" × 11" (letter) or 11" × 17" (tabloid) as needed
- Plot style: monochrome.ctb or color_dependent.ctb
- Units: Feet and inches (engineering)

### File Naming
```
{PropertyOwner}_{Date}_{DrawingType}.dwg
Example: SmithJ_20250115_SitePlan.dwg
         SmithJ_20250115_SoilProfile.dwg
         SmithJ_20250115_DisposalPlan.dwg
         SmithJ_20250115_CrossSection.dwg
```

### Quality Checks
- [ ] All layers plot at correct lineweights
- [ ] All text is legible at plot scale
- [ ] Dimensions are accurate and complete
- [ ] Scale bar is correct
- [ ] North arrow is oriented correctly
- [ ] All elevations match field data
- [ ] Soil profile depths are accurate
- [ ] System components are correctly positioned