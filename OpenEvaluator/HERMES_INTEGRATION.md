# Hermes Integration Guide

## Overview
Hermes analyzes site evaluator uploads (documents, sketches, photos) and extracts structured survey data. This data feeds OpenEvaluator to generate professional HHE-200 PDFs.

## Integration Points

### 1. Hermes Input
- **Trigger**: New entry in Google Sheet column T (Uploads)
- **Input**: URL/file link to site evaluator's uploaded document
- **Task**: Analyze document and extract site information

### 2. Hermes Processing
Hermes must extract and parse:

#### Property Information
- Lot corners/boundaries (coordinates in feet from property corner)
- Road names and positions
- Property acreage
- Address, map number, lot number

#### Building/Structure Positions
- Existing house location (X, Y feet from NW corner)
- Dimensions (width, length in feet)
- Garage location and dimensions
- Deck/other structures location and dimensions
- Building orientation/direction

#### Water Supply
- Well/water supply location (X, Y)
- Type (drilled, dug, spring)
- Depth

#### Septic System
**Tank:**
- Position (X, Y from NW corner)
- Capacity (gallons)
- Dimensions (length, width, height in feet)

**Disposal Field:**
- Starting position (X, Y)
- Type (Eljen, drip, traditional, etc.)
- Number of rows and modules per row
- Module spacing and row spacing
- Orientation (N-S or E-W)

#### Soil Information (from observation holes)
For each borehole/observation hole:
- Location (X, Y coordinates)
- Depth (feet)
- Soil layers with:
  - Depth range (inches from surface)
  - Color (Brown, Gray, Yellowish-Brown, etc.)
  - Texture (FSL, SL, S, L, LS, etc.)
  - Consistence (Friable, Firm, etc.)
  - Redox features (Mottled, Gleying, etc.)
- Organic horizon thickness
- Ground surface elevation (relative to reference point)

#### Elevation Data
- Reference point description and location
- Reference point height above grade
- Grade elevations at key points (house, tank, field)
- Limiting factor type and depth (groundwater, restrictive layer)

#### Contour Lines (optional but valuable)
- Elevation (feet)
- Series of points defining contour path

### 3. Hermes Output

**File**: `hermes_output.json`
**Location**: Same directory as run_pipeline_with_hermes.py
**Format**: JSON matching this schema:

```json
{
  "property": {
    "address": "17 Aspen Way, Turner, Maine 04282",
    "map_number": "26",
    "lot_number": "18",
    "acreage": 2.35,
    "lot_corners": [
      {"label": "NW", "x": 0, "y": 0},
      {"label": "NE", "x": 200, "y": 0},
      {"label": "SE", "x": 200, "y": 150},
      {"label": "SW", "x": 0, "y": 150}
    ],
    "roads": [
      {"name": "ASPEN", "side": "north", "distance_ft": 25},
      {"name": "161", "side": "east", "distance_ft": 0}
    ]
  },
  
  "existing_structures": [
    {
      "name": "DWELLING",
      "type": "house",
      "position_x": 50,
      "position_y": 40,
      "width_ft": 30,
      "length_ft": 40,
      "roof_style": "gable"
    }
  ],
  
  "water_supply": {
    "type": "drilled_well",
    "position_x": 20,
    "position_y": 30,
    "depth_ft": 125
  },
  
  "septic_system": {
    "tank": {
      "position_x": 120,
      "position_y": 80,
      "capacity_gallons": 1000,
      "dimensions": {
        "length": 5,
        "width": 3,
        "height": 4,
        "unit": "feet"
      }
    },
    "disposal_field": {
      "position_x": 140,
      "position_y": 50,
      "type": "Eljen GSF-B43",
      "orientation": "N-S",
      "rows": 3,
      "modules_per_row": 7,
      "module_spacing_ft": 1.5,
      "row_spacing_ft": 3.5
    }
  },
  
  "observation_holes": [
    {
      "hole_number": 1,
      "position_x": 130,
      "position_y": 70,
      "depth_ft": 36,
      "organic_horizon_thickness_in": 2,
      "ground_surface_elevation": 0,
      "soil_layers": [
        {
          "depth_start_in": 0,
          "depth_end_in": 3,
          "color": "Brown",
          "texture": "FSL",
          "consistence": "Friable",
          "redox_features": ""
        }
      ]
    }
  ],
  
  "elevation_data": {
    "reference_point": {
      "description": "Nail in 6\" maple tree",
      "position_x": 45,
      "position_y": 35,
      "height_above_grade_in": 12
    },
    "grade_elevations": [
      {"location": "house", "elevation_ft": 120.0},
      {"location": "tank", "elevation_ft": 119.5}
    ],
    "limiting_factor": {
      "type": "groundwater",
      "depth_in": 24,
      "location": "observed in hole 1"
    }
  },
  
  "contour_lines": [
    {
      "elevation_ft": 120,
      "points": [[0,0], [50,5], [100,10]]
    }
  ]
}
```

## Coordinate System

**All coordinates in feet from Northwest (NW) corner of property:**
- Origin (0, 0) = NW corner
- X increases going East
- Y increases going South
- Example: Position (50, 40) = 50 feet East, 40 feet South of NW corner

## Data Accuracy Requirements

| Data | Precision | Rationale |
|------|-----------|-----------|
| Building positions | ±5 feet | Sketch-level accuracy acceptable |
| Measurements | Nearest foot | Rounding acceptable |
| Soil depths | Nearest inch | For borehole profiles |
| Elevations | Nearest 0.5 feet | For grade/GW visualization |
| Coordinates | ±5 feet | Sketch sources acceptable |

## Triggering OpenEvaluator

### Automatic (Recommended)
After Hermes outputs `hermes_output.json`, trigger:
```bash
python3 /path/to/OpenEvaluator/run_pipeline_with_hermes.py
```

This will:
1. Verify hermes_output.json exists
2. Validate required fields
3. Generate professional drawings from real data
4. Fill HHE-200 PDF
5. Upload to Google Drive

### Safety
- Script **REQUIRES** hermes_output.json
- **WILL NOT** generate fake documents
- **WILL EXIT** if required data is missing
- No fallback to test data

## Troubleshooting

### "hermes_output.json not found"
- Hermes has not yet processed the upload
- Pipeline is running before Hermes completes
- Solution: Ensure Hermes runs first, outputs JSON file

### JSON validation error
- hermes_output.json is malformed
- Missing required top-level keys
- Solution: Check JSON syntax, ensure all required keys present

### Missing required fields
- Some data couldn't be extracted from upload
- Solution: Hermes should output `null` for missing fields, not omit them

## Future Enhancements

1. **Confidence scores** - Add confidence_score (0-1.0) for extracted fields
2. **Extraction notes** - Add notes field for ambiguities or extraction issues
3. **Multiple holes** - Support 2+ observation holes with cross-section averaging
4. **Photo integration** - Embed site photos in PDF (if available)
5. **Sketches** - Overlay extracted sketch outlines on generated drawings

## Questions?

This integration assumes Hermes can analyze:
- Hand-drawn site plans
- Scanned survey documents
- Photos with measurements
- PDF reports with tables/data
- Mixed document formats

If you need to adjust data structure or add fields, update this schema and professional_drawings_with_data.py accordingly.
