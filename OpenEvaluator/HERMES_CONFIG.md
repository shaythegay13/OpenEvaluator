---
title: Hermes Configuration for HHE-200 Pipeline
description: Setup instructions for Hermes to process Google Sheet submissions
created: 2026-05-31
updated: 2026-05-31
---

# Hermes Configuration

## Quick Start

Hermes needs to:
1. **Watch** Google Sheet for new rows (or specifically Row 2 for testing)
2. **Download** document from column T
3. **Extract** spatial + text data using HERMES_EXTRACTION_PROMPT.md
4. **Output** JSON to `/home/workspace/OpenEvaluator/hermes_output.json`
5. **Trigger** the pipeline script

---

## Configuration Steps

### Step 1: Connect to Google Sheet

Hermes needs access to:
- **Sheet ID**: `1VHJq0vBMGrme-wmHuPooko0G5JpbfP_o1ZeozjEZ94M`
- **Watch Column T** for document upload links
- **Read all columns** (A-T) for submission data

In your Zo Hermes configuration:
```
Sheet URL: https://docs.google.com/spreadsheets/d/1VHJq0vBMGrme-wmHuPooko0G5JpbfP_o1ZeozjEZ94M/edit
Trigger: New row added
Watch: Column T (Uploads)
Read: All columns (A-T)
```

### Step 2: Set Extraction Instructions

Use the extraction prompt:

**File**: `HERMES_EXTRACTION_PROMPT.md`  
**Location**: `/home/workspace/OpenEvaluator/HERMES_EXTRACTION_PROMPT.md`

This file contains detailed instructions on what to extract from:
- Document (spatial data: coordinates, layout, measurements)
- Form submission data (text fields: names, addresses, observations)

Hermes should read this prompt and follow it for every extraction.

### Step 3: Configure Output

**Output file:**
```
/home/workspace/OpenEvaluator/hermes_output.json
```

**Schema**: See `HERMES_INTEGRATION_COMPLETE.md`

Example output structure:
```json
{
  "metadata": { ... },
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
  "extraction_quality": { ... }
}
```

### Step 4: Configure Post-Processing

After Hermes outputs JSON, automatically run:

```bash
python3 /home/workspace/OpenEvaluator/run_pipeline_with_hermes_complete.py
```

This will:
- Verify hermes_output.json exists
- Extract form fields
- Generate professional drawings
- Fill HHE-200 PDF
- Upload to Google Drive (when enabled)

---

## Testing Hermes

### Test Data Location

**Google Sheet**: Row 2  
**Property**: 123 Main St, Springfield, IL (example)  
**Document Upload**: Column T, Row 2  
**Test Documents**: `/home/workspace/OpenEvaluator/example/26-018 PG*.pdf`

### Manual Test (Before Automation)

1. **Trigger Hermes manually** on Row 2:
   ```
   Input: Row 2 data + document link in column T
   ```

2. **Verify output:**
   ```bash
   ls -l /home/workspace/OpenEvaluator/hermes_output.json
   python3 -m json.tool /home/workspace/OpenEvaluator/hermes_output.json | head -50
   ```

3. **Check quality:**
   ```json
   {
     "metadata": {
       "submission_id": "123-Main-St-...",
       "confidence": 0.90+,
       "extraction_quality": {
         "spatial_data_confidence": 0.90+,
         "document_clarity": "High"
       }
     }
   }
   ```

4. **Run pipeline:**
   ```bash
   python3 /home/workspace/OpenEvaluator/run_pipeline_with_hermes_complete.py
   ```

### Expected Test Output

```
✅ Loaded hermes_output.json
   Submission ID: 123-Main-St-Springfield
   Client: Jane Doe
   Property: 123 Main St, Springfield, IL

✅ Extracted 85+ form fields
✅ Generated professional drawings
✅ Filled HHE-200 form (4 pages)
✅ Output: HHE-200-filled.pdf
```

---

## Hermes Configuration Checklist

- [ ] Hermes connected to Google Sheet
- [ ] Can read column T (Uploads)
- [ ] Can access Google Drive (download documents)
- [ ] Has HERMES_EXTRACTION_PROMPT.md as instructions
- [ ] Outputs to `/home/workspace/OpenEvaluator/hermes_output.json`
- [ ] Configured to run post-processing script
- [ ] Manual test passes (Row 2)
- [ ] Automatic trigger works
- [ ] End-to-end pipeline produces HHE-200 PDF

---

## Troubleshooting

### Hermes Can't Read Google Sheet
- **Check**: Google Sheet sharing permissions
- **Fix**: Ensure Hermes has read access to the sheet

### Document Download Fails
- **Check**: Column T has valid Google Drive links
- **Check**: Document sharing permissions
- **Fix**: Re-upload document or update link

### hermes_output.json Not Created
- **Check**: Hermes logs for extraction errors
- **Check**: Is the document readable/analyzable?
- **Fix**: Improve document quality or add annotations

### JSON Validation Error
- **Check**: JSON syntax (use `python3 -m json.tool`)
- **Check**: All required fields present
- **Fix**: Review Hermes extraction logs

### Pipeline Won't Run
- **Check**: hermes_output.json exists and is valid
- **Check**: Python dependencies installed
- **Run**: `python3 run_pipeline_with_hermes_complete.py` manually to see error

---

## What Happens When Hermes Runs

### Input
```
From Google Sheet Row 2:
- Site evaluator: John Smith, john@example.com
- Client: Jane Doe, 123 Main St, Springfield, IL
- Property: Map 26, Lot 18
- Well: Drilled, 125 feet deep
- Septic: 1000 gal tank, Eljen field
- Document link: https://drive.google.com/file/d/...
```

### Processing
```
Hermes downloads document
├─ Extracts building coordinates (X, Y)
├─ Extracts tank location and dimensions
├─ Extracts well location and depth
├─ Extracts disposal field layout
├─ Extracts soil layer observations
├─ Extracts elevation data
└─ Outputs hermes_output.json
```

### Output
```json
{
  "property": {
    "address": "123 Main St, Springfield, IL",
    "map_number": "26",
    "lot_number": "18"
  },
  "existing_structures": [
    {
      "name": "DWELLING",
      "position_x": 50,
      "position_y": 40,
      "width_ft": 30,
      "length_ft": 40
    }
  ],
  "water_supply": {
    "position_x": 20,
    "position_y": 30,
    "depth_ft": 125
  },
  "septic_system": {
    "tank": {
      "position_x": 120,
      "position_y": 80,
      "capacity_gallons": 1000
    },
    "disposal_field": {
      "position_x": 140,
      "position_y": 50,
      "type": "Eljen GSF-B43"
    }
  },
  "observation_holes": [ ... ],
  "elevation_data": { ... }
}
```

### Result
```
✅ HHE-200-filled.pdf generated
   - Page 1: Contact info, well data
   - Page 2: Soil observations, setback analysis
   - Page 3: Professional site plan (auto-drawn)
   - Page 4: Cross-section with soil layers (auto-drawn)
```

---

## Files Referenced

- `HERMES_EXTRACTION_PROMPT.md` — Detailed extraction instructions
- `HERMES_INTEGRATION_COMPLETE.md` — Full data schema and format
- `run_pipeline_with_hermes_complete.py` — Pipeline that processes output
- `professional_drawings_with_data.py` — Drawing generation
- `acro_fill.py` — PDF form filling
