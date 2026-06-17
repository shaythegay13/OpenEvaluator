---
title: Complete Hermes Integration for HHE-200
description: Full data flow from Google Sheet submission to professional HHE-200 PDF
created: 2026-05-31
updated: 2026-05-31
---

# Hermes Integration — Complete Data Flow

## Overview
Hermes receives **all submission data** (form fields + document analysis) and outputs a **complete JSON** with everything needed to fill the HHE-200 PDF.

---

## Input to Hermes

### From Google Sheet (All Columns)

```json
{
  "submission_id": "123-Main-St-Springfield",
  "submission_date": "2026-05-31",
  
  "site_evaluator": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "license_number": "SE-12345"
  },
  
  "client": {
    "name": "Jane Doe",
    "address": "123 Main St, Springfield, IL 62701",
    "phone": "+1-555-0456",
    "email": "jane@example.com"
  },
  
  "property": {
    "map_number": "26",
    "lot_number": "18",
    "parcel_id": "26-18",
    "county": "Maine",
    "township": "Turner"
  },
  
  "well_information": {
    "type": "drilled_well",
    "depth_ft": 125,
    "depth_to_water_ft": 45,
    "water_tested": true,
    "test_date": "2026-05-15",
    "test_results": "Bacteria present"
  },
  
  "septic_system": {
    "tank_capacity_gallons": 1000,
    "tank_type": "concrete",
    "tank_age_years": 15,
    "disposal_field_type": "Eljen GSF-B43",
    "disposal_field_size_modules": 21,
    "last_pumped": "2024-03-01"
  },
  
  "soil_observations": {
    "general_notes": "Well-drained loamy sand with some gravel...",
    "groundwater_depth_in": 24,
    "limiting_factors": "Seasonal groundwater at 24 inches",
    "organic_horizon_thickness_in": 2,
    "texture_description": "Fine sandy loam to sandy loam"
  },
  
  "observation_holes": [
    {
      "hole_number": 1,
      "location_description": "Southeast of tank",
      "depth_ft": 36,
      "observations": "Dark brown loam, friable...",
      "layer_data": [
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
    "grade_at_house_ft": 120.0,
    "grade_at_tank_ft": 119.5,
    "grade_at_field_ft": 119.0,
    "reference_point_description": "Nail in 6\" maple tree"
  },
  
  "setback_requirements": {
    "distance_from_well_ft": 50,
    "distance_from_property_line_ft": 10,
    "distance_from_surface_water_ft": 100
  },
  
  "estimated_setback_ft": 50,
  "designer_notes": "Site suitable for standard septic system...",
  
  "document_upload_link": "https://drive.google.com/file/d/..."
}
```

---

## Hermes Processing

Hermes must:

1. **Download & analyze the uploaded document** (PDF, sketch, photos, etc.)
2. **Extract spatial data** (buildings, tank, field, boreholes, elevations)
3. **Extract text data** (observations, notes, measurements)
4. **Validate against submission data** (cross-check with Google Sheet values)
5. **Output complete JSON** with both spatial + text data

---

## Output from Hermes

**File**: `hermes_output.json`  
**Location**: Same directory as `run_pipeline_with_hermes.py`  
**Schema**:

```json
{
  "metadata": {
    "submission_id": "123-Main-St-Springfield",
    "hermes_processed_at": "2026-05-31T14:30:00Z",
    "document_analyzed": true,
    "confidence": 0.95
  },

  "site_evaluator": {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "license_number": "SE-12345"
  },

  "client": {
    "name": "Jane Doe",
    "address": "123 Main St, Springfield, IL 62701",
    "phone": "+1-555-0456",
    "email": "jane@example.com"
  },

  "property": {
    "address": "123 Main St, Springfield, IL 62701",
    "map_number": "26",
    "lot_number": "18",
    "acreage": 2.35,
    "county": "Maine",
    "township": "Turner",
    "lot_corners": [
      {"label": "NW", "x": 0, "y": 0},
      {"label": "NE", "x": 200, "y": 0},
      {"label": "SE", "x": 200, "y": 150},
      {"label": "SW", "x": 0, "y": 150}
    ],
    "roads": [
      {"name": "ASPEN", "side": "north", "distance_ft": 25}
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
      "roof_style": "gable",
      "distance_from_field_ft": 45
    },
    {
      "name": "GARAGE",
      "type": "garage",
      "position_x": 70,
      "position_y": 50,
      "width_ft": 20,
      "length_ft": 22
    }
  ],

  "water_supply": {
    "type": "drilled_well",
    "position_x": 20,
    "position_y": 30,
    "depth_ft": 125,
    "depth_to_water_ft": 45,
    "water_tested": true,
    "test_date": "2026-05-15",
    "test_results": "Bacteria present"
  },

  "septic_system": {
    "tank": {
      "position_x": 120,
      "position_y": 80,
      "capacity_gallons": 1000,
      "tank_type": "concrete",
      "tank_age_years": 15,
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
      "row_spacing_ft": 3.5,
      "total_modules": 21,
      "last_pumped": "2024-03-01"
    }
  },

  "soil_observations": {
    "general_notes": "Well-drained loamy sand with some gravel. Suitable for septic system.",
    "groundwater_depth_in": 24,
    "limiting_factors": "Seasonal groundwater at 24 inches",
    "organic_horizon_thickness_in": 2,
    "texture_description": "Fine sandy loam to sandy loam",
    "percolation_rate": "30-60 min/inch",
    "seasonal_saturation": "observed at 24 inches"
  },

  "observation_holes": [
    {
      "hole_number": 1,
      "position_x": 130,
      "position_y": 70,
      "location_description": "Southeast of tank",
      "depth_ft": 36,
      "organic_horizon_thickness_in": 2,
      "ground_surface_elevation": 0,
      "observations": "Dark brown loam, friable consistency...",
      "soil_layers": [
        {
          "depth_start_in": 0,
          "depth_end_in": 3,
          "color": "Brown",
          "texture": "FSL",
          "consistence": "Friable",
          "redox_features": ""
        },
        {
          "depth_start_in": 3,
          "depth_end_in": 12,
          "color": "Brown",
          "texture": "SL",
          "consistence": "Friable",
          "redox_features": ""
        },
        {
          "depth_start_in": 12,
          "depth_end_in": 24,
          "color": "Yellowish-Brown",
          "texture": "S",
          "consistence": "Loose",
          "redox_features": "Mottled"
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
      {"location": "tank", "elevation_ft": 119.5},
      {"location": "field", "elevation_ft": 119.0}
    ],
    "limiting_factor": {
      "type": "groundwater",
      "depth_in": 24,
      "location": "observed in hole 1"
    }
  },

  "setback_requirements": {
    "distance_from_well_ft": 50,
    "distance_from_property_line_ft": 10,
    "distance_from_surface_water_ft": 100,
    "estimated_setback_ft": 50,
    "setback_limiting_factor": "Well location"
  },

  "designer_notes": "Site is suitable for standard septic system. Well exceeds setback requirements. Seasonal groundwater limits shallow disposal.",

  "contour_lines": [
    {
      "elevation_ft": 120,
      "points": [[0,0], [50,5], [100,10]]
    }
  ],

  "extraction_quality": {
    "spatial_data_confidence": 0.95,
    "text_data_confidence": 0.90,
    "document_clarity": "High",
    "notes": "All required fields extracted successfully"
  }
}
```

---

## Data Flow Diagram

```
Google Sheet Row
       ↓
  [All columns] + [Document Link]
       ↓
   Hermes
   ├─ Downloads document
   ├─ Extracts spatial data (coordinates, layout)
   ├─ Extracts text data (observations, measurements)
   ├─ Cross-validates with sheet data
   └─ Outputs hermes_output.json
       ↓
  run_pipeline_with_hermes.py
  ├─ Reads hermes_output.json
  ├─ Generates professional drawings (pages 3-4)
  ├─ Fills HHE-200 form (all 4 pages)
  ├─ Embeds drawings into PDF
  └─ Uploads to Google Drive
       ↓
   Professional HHE-200 PDF
```

---

## Key Points

### ✅ Complete Data Package
- **From Sheet**: All form fields (evaluator, client, property, soil, setback, notes)
- **From Document**: Spatial data (coordinates, measurements, observations)
- **Output**: Everything needed to fill HHE-200 + generate drawings

### ✅ No Fallback
- Hermes **MUST** provide hermes_output.json
- Pipeline **REFUSES** to run without it
- No fake documents produced

### ✅ Coordinated Workflow
- Hermes processes document → outputs JSON
- Pipeline reads JSON → fills PDF
- No intermediate steps or manual data re-entry

---

## Triggering

After Hermes outputs `hermes_output.json`:

```bash
python3 /path/to/OpenEvaluator/run_pipeline_with_hermes.py
```

This will generate the complete HHE-200 PDF with:
- All form fields filled from submission data
- Professional site plan drawings (pages 3-4)
- Soil profiles from observation holes
- Property layout and structures
- Elevation contours

---

## Questions

If any data structure needs adjustment, update both:
1. This HERMES_INTEGRATION_COMPLETE.md
2. professional_drawings_with_data.py (for spatial rendering)
3. acro_fill.py (for form field mapping)
