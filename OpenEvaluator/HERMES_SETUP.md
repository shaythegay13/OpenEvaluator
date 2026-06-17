---
title: Hermes Setup & Integration Guide
description: How to configure Hermes for HHE-200 automation
created: 2026-05-31
updated: 2026-05-31
---

# Hermes Setup for HHE-200 Automation

## What Hermes Does

Hermes is your **document intelligence engine** that:
1. Monitors Google Sheet column T for new uploads
2. Downloads and analyzes the uploaded document
3. Extracts **spatial data** (coordinates, layout, measurements)
4. Extracts **text data** (observations, measurements, notes)
5. Outputs a complete JSON file
6. Triggers the OpenEvaluator pipeline

---

## Integration Architecture

```
Google Sheet Submission
├─ Form Fields (site evaluator, client, property info)
├─ Well data
├─ Septic system details
├─ Soil observations
├─ Setback requirements
└─ Document Upload Link (Column T) ← Hermes watches this
    │
    └─→ Hermes processes document
        ├─ Extracts spatial data (coordinates, building positions)
        ├─ Extracts text observations
        ├─ Combines with form submission data
        └─ Outputs: hermes_output.json
            │
            └─→ run_pipeline_with_hermes_complete.py
                ├─ Generates professional drawings (pages 3-4)
                ├─ Fills HHE-200 form (all 4 pages)
                ├─ Embeds drawings in PDF
                └─ Uploads to Google Drive
                    │
                    └─→ Client-Ready HHE-200 PDF
```

---

## Hermes Workflow

### Trigger
```
New row added to Google Sheet
     ↓
Column T (Uploads) has a document link
     ↓
Hermes event fires
```

### Processing

```python
# Hermes receives:
input = {
    "submission_id": "123-Main-St-Springfield",
    "submission_data": {
        "site_evaluator_name": "John Smith",
        "client_name": "Jane Doe",
        "client_address": "123 Main St, Springfield, IL",
        # ... all form fields ...
    },
    "document_upload_link": "https://drive.google.com/file/d/..."
}

# Hermes processes:
1. Download document from link
2. Analyze using computer vision + OCR
3. Extract building positions, tank location, field layout
4. Extract soil layer observations
5. Extract elevation data and contours
6. Validate against submission data
7. Output complete JSON

# Hermes outputs:
hermes_output.json {
    "metadata": { ... },
    "site_evaluator": { ... },
    "client": { ... },
    "property": { ... },
    "existing_structures": [ ... ],  # From document
    "water_supply": { ... },
    "septic_system": { ... },
    "soil_observations": { ... },
    "observation_holes": [ ... ],    # From document
    "elevation_data": { ... },
    "designer_notes": "..."
}
```

### Output Location

```
/home/workspace/OpenEvaluator/hermes_output.json
```

**This file MUST exist for the pipeline to run.**

---

## Required Data Extraction

### From Document Upload

Hermes extracts using the document (PDF, photos, sketch, etc.):

**Spatial Data (coordinates in feet from NW corner):**
- House position (X, Y) and dimensions
- Garage position and dimensions
- Well location (X, Y)
- Septic tank location (X, Y) and capacity
- Disposal field location (X, Y), type, modules
- Each observation hole location (X, Y), depth, soil layers
- Property corners and roads
- Elevation reference point and grade elevations
- Contour lines (if present)

**Text Data:**
- Soil texture and color descriptions
- Layer consistence (friable, firm, etc.)
- Redox features (mottled, gleying, etc.)
- Groundwater observations
- General site notes and assessments
- Limiting factors (groundwater depth, clay layer, etc.)

### Combined with Submission Data

Hermes also uses (from Google Sheet):
- Site evaluator name, email, license
- Client name, address, phone
- Property map/lot numbers, acreage
- Well type and testing info
- Septic tank capacity
- Setback requirements
- Designer notes

---

## Output Schema

See `HERMES_INTEGRATION_COMPLETE.md` for the complete JSON schema.

Key sections:
- `metadata` — Processing timestamp, confidence scores
- `site_evaluator` — Name, email, phone, license
- `client` — Name, address, contact info
- `property` — Address, map number, lot number, acreage
- `existing_structures` — Buildings with coordinates
- `water_supply` — Well type, location, depth, test results
- `septic_system` — Tank (location, capacity) + field (type, modules)
- `soil_observations` — General notes, groundwater, limiting factors
- `observation_holes` — Each hole with position, depth, soil layers
- `elevation_data` — Reference point, grade elevations, limiting factor
- `setback_requirements` — Distances, limiting factor

---

## Hermes Configuration Checklist

- [ ] Connect Hermes to Google Sheets (can read new rows)
- [ ] Hermes watches column T (Uploads) for new links
- [ ] Hermes has access to Google Drive (can download documents)
- [ ] Hermes is configured to extract spatial data (coordinates)
- [ ] Hermes is configured to extract text data (observations)
- [ ] Hermes outputs JSON to `/home/workspace/OpenEvaluator/hermes_output.json`
- [ ] Hermes can trigger external script: `python3 run_pipeline_with_hermes_complete.py`

---

## Testing Hermes Output

Before full automation, verify Hermes output with:

```bash
cd /home/workspace/OpenEvaluator

# Verify JSON exists and is valid
python3 -m json.tool hermes_output.json | head -50

# Run pipeline with Hermes output
python3 run_pipeline_with_hermes_complete.py
```

Expected output:
```
✅ Loaded hermes_output.json
   Submission ID: 123-Main-St-Springfield
   Client: Jane Doe
   Property: 123 Main St, Springfield, IL

✅ Extracted 85+ form fields
✅ Extracted spatial data for:
   - 2 building(s)
   - 1 observation hole(s)
   - 3 contour line(s)

✅ Generated drawings
   - Page 3 (Disposal Field): page3_professional.dxf
   - Page 4 (Cross-Section): page4_professional.dxf

✅ Filled HHE-200 form
   Output: HHE-200-filled.pdf

✅ Pipeline Complete
```

---

## What Happens After Hermes

Once `hermes_output.json` is written:

1. **automatic trigger** (if configured):
   ```bash
   python3 /home/workspace/OpenEvaluator/run_pipeline_with_hermes_complete.py
   ```

2. **Pipeline generates:**
   - Professional drawings (pages 3-4) from spatial data
   - Filled HHE-200 form (pages 1-4) with all data
   - Embedded drawings in the PDF
   - Ready for Google Drive upload

3. **Output PDF** includes:
   - Page 1: Site evaluator info, client info, well data
   - Page 2: Soil observations, setback analysis, notes
   - Page 3: Professional site plan with structures, tank, field
   - Page 4: Cross-section showing soil layers and elevations

---

## Troubleshooting

### "hermes_output.json not found"
- Hermes has not yet processed the upload
- Check: Is Hermes running? Has it received the document link?
- Solution: Wait for Hermes to complete, or manually trigger it

### JSON validation error
- hermes_output.json is malformed or incomplete
- Check: Hermes logs for extraction errors
- Solution: Review document quality, ensure all required fields extracted

### Missing spatial data
- Hermes couldn't extract coordinates from document
- Check: Is the document legible? Are measurements visible?
- Solution: Improve document quality, add measurements if missing

### Pipeline won't run
- Check: `python3 run_pipeline_with_hermes_complete.py`
- Error messages will indicate which step failed
- See IMPLEMENTATION_STATUS.md for current status

---

## Next Steps

1. **Connect Hermes** to Google Sheets
2. **Configure extraction** for spatial + text data
3. **Set output path** to `/home/workspace/OpenEvaluator/hermes_output.json`
4. **Set post-processing** to trigger: `python3 run_pipeline_with_hermes_complete.py`
5. **Test** with a sample document from the example folder
6. **Verify** the generated PDF matches the example outputs

---

## Questions?

Refer to:
- `HERMES_INTEGRATION_COMPLETE.md` — Full data schema
- `DRAWING_DESIGN_SPEC.md` — Page 3-4 drawing specifications
- `professional_drawings_with_data.py` — Drawing generation code
- `acro_fill.py` — Form field mapping

This is a **complete, end-to-end automation**. No manual steps after the Google Sheet submission.
