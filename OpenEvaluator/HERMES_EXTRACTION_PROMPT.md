---
title: Hermes Extraction Prompt for HHE-200
description: Detailed instructions for Hermes to extract data from site evaluation documents
created: 2026-05-31
updated: 2026-05-31
---

# Hermes Extraction Prompt

## Task
Extract spatial and text data from a site evaluation document and output structured JSON for HHE-200 form generation.

## Input Data

You will receive:
- **Google Sheet Row Data**: Site evaluator info, client info, property details, well info, septic system info, soil observations
- **Document Upload Link**: URL to PDF/document uploaded by site evaluator

Example row data structure:
```json
{
  "submission_id": "123-Main-St-Springfield",
  "site_evaluator_name": "John Smith",
  "site_evaluator_email": "john@example.com",
  "site_evaluator_phone": "+1-555-0123",
  "client_name": "Jane Doe",
  "client_address": "123 Main St, Springfield, IL 62701",
  "client_phone": "+1-555-0456",
  "client_email": "jane@example.com",
  "property_map_number": "26",
  "property_lot_number": "18",
  "property_county": "Maine",
  "property_township": "Turner",
  "well_type": "drilled_well",
  "well_depth_ft": 125,
  "groundwater_depth_ft": 45,
  "septic_tank_capacity": 1000,
  "septic_disposal_field_type": "Eljen GSF-B43",
  "soil_general_notes": "Well-drained loamy sand...",
  "document_upload_link": "https://drive.google.com/file/d/..."
}
```

## Extraction Steps

### Step 1: Download & Analyze Document
- Download document from the upload link
- If PDF with images: use OCR to extract text
- If sketch/hand-drawn: use computer vision to identify shapes, labels, measurements
- If mixed document: combine all sources

### Step 2: Extract Spatial Data (Coordinates)

**Property Boundaries:**
- Find lot corners (NW, NE, SE, SW) and their X,Y coordinates in feet
- Find roads and their names/directions
- Calculate total acreage if dimensions are visible

**Existing Structures:**
```
For each building visible:
- Name/label (e.g., "DWELLING", "GARAGE")
- Position: X feet east, Y feet south from NW corner
- Dimensions: width × length in feet
- Roof style (if visible)
```

**Water Supply (Well):**
```
- Location: X, Y coordinates from NW corner
- Depth: feet below surface
- Type: drilled, dug, spring, etc.
```

**Septic System:**
```
Tank:
- Location: X, Y from NW corner
- Capacity: gallons
- Type: concrete, fiberglass, etc.
- Dimensions: length × width × height (feet)

Disposal Field:
- Starting position: X, Y from NW corner
- Type/model: e.g., "Eljen GSF-B43"
- Layout: number of rows, modules per row
- Orientation: N-S or E-W
- Module spacing: feet between modules
- Row spacing: feet between rows
```

**Observation Holes (Boreholes):**
```
For each hole shown:
- Hole number: 1, 2, 3, etc.
- Location: X, Y from NW corner
- Depth: feet below surface
- Description: what was observed at each depth
```

**Elevations:**
```
- Reference point: location and height (e.g., "nail in tree at 12 inches above grade")
- Grade elevations at key points:
  - House grade elevation
  - Tank grade elevation
  - Disposal field grade elevation
- Limiting factor: depth to groundwater, clay layer, etc.
```

**Contour Lines (if present):**
```
For each contour:
- Elevation in feet
- Series of X,Y points that make the contour line
```

### Step 3: Extract Text Data (Observations)

**Soil Information:**
```
From observation holes or general notes:
- Soil color: Brown, Yellowish-Brown, Gray, etc.
- Soil texture: FSL (Fine Sandy Loam), SL, S, L, etc.
- Consistence: Friable, Firm, Loose, etc.
- Redox features: Mottled, Gleying, etc.
- Organic horizon: thickness in inches
- Limiting factors: groundwater depth, clay layer, etc.
```

**General Observations:**
```
- Overall site assessment
- Groundwater observations
- Soil drainage characteristics
- Any unusual conditions
- Site suitability for septic system
```

**Measurements & Distances:**
```
- Distance from well to proposed disposal field
- Distance from property line to structures
- Distances to surface water
- Any other relevant measurements
```

### Step 4: Validate & Reconcile

```
Cross-check extracted data with Google Sheet submission:
- Site evaluator name matches
- Client name matches
- Property details match
- Well depth approximately matches
- Tank capacity approximately matches
- Soil observations consistent with submitted notes
```

If values differ:
- Use **document values as truth** for spatial data (coordinates)
- Use **document values** for detailed observations not in sheet
- Use **sheet values** for contact info and admin data

### Step 5: Output JSON

Generate `hermes_output.json` with complete structure (see HERMES_INTEGRATION_COMPLETE.md for full schema).

## Accuracy Requirements

| Data Type | Precision | Notes |
|-----------|-----------|-------|
| Building coordinates | ±5 feet | Sketch-level OK |
| Measurements | Nearest foot | Rounding acceptable |
| Soil depths | Nearest inch | For borehole profiles |
| Elevations | Nearest 0.5 feet | For grade visualization |
| Coordinates | ±5 feet | Sketch sources OK |
| Well/tank location | ±10 feet | Sketch estimates OK |

## Handling Ambiguities

**If measurement is unclear:**
- Use nearest round number (e.g., "about 30 feet" → 30)
- Add note in extraction_quality.notes

**If coordinate can't be determined:**
- Use null or best estimate with low confidence
- Document in extraction_quality

**If soil layer is unclear:**
- Use description as-is
- Mark with lower confidence

**If document is low quality:**
- Extract what's readable
- Set confidence score appropriately (0-1.0)
- Note issues in extraction_quality.notes

## Output Format

```json
{
  "metadata": {
    "submission_id": "123-Main-St-Springfield",
    "hermes_processed_at": "2026-05-31T14:30:00Z",
    "document_analyzed": true,
    "confidence": 0.92
  },
  
  "site_evaluator": { ... },
  "client": { ... },
  "property": { ... },
  "existing_structures": [ ... ],
  "water_supply": { ... },
  "septic_system": { ... },
  "soil_observations": { ... },
  "observation_holes": [ ... ],
  "elevation_data": { ... },
  "setback_requirements": { ... },
  "designer_notes": "...",
  "contour_lines": [ ... ],
  
  "extraction_quality": {
    "spatial_data_confidence": 0.95,
    "text_data_confidence": 0.90,
    "document_clarity": "High",
    "notes": "All required fields extracted successfully"
  }
}
```

## Output Location

**File name:** `hermes_output.json`  
**Directory:** `/home/workspace/OpenEvaluator/`  
**Trigger after:** Automatically run `python3 /home/workspace/OpenEvaluator/run_pipeline_with_hermes_complete.py`

## Success Criteria

✅ hermes_output.json exists  
✅ Valid JSON format  
✅ All required top-level keys present  
✅ Spatial data: building coordinates, tank location, field position  
✅ Text data: site evaluator, client, property, soil observations  
✅ Extraction quality scores in metadata  
✅ No fake/placeholder data  
✅ All measurements in required units (feet, inches, gallons)  

## Testing

Test document: `/home/workspace/OpenEvaluator/example/26-018 PG1 (1).pdf` and related PDFs

Expected output will show:
- Property at 123 Main St, Springfield, IL (or similar)
- Building positions with coordinates
- Well and tank locations
- Soil layer observations from boreholes
- Elevation data and contours
- Complete site evaluator and client contact info
