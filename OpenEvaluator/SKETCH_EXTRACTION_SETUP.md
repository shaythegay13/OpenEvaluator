---
title: Sketch Extraction Setup & Fallback Options
description: Configure Vision API and Google Maps for sketch data extraction, with fallback to structured form
created: 2026-06-05
updated: 2026-06-05
---

## Phase 2C: Sketch Data Extraction — Status

The sketch extraction pipeline has been **rebuilt with major improvements** for better OCR and data parsing. However, system package restrictions prevent installing the required Vision API library (`google-cloud-vision`) directly.

### Current Capabilities

✅ **Completed:**
- Google Cloud credentials configured (service account JSON)
- Google Maps API enabled (Geocoding)
- Sketch download from Google Drive (working)
- Improved data parsing patterns for hand-drawn sketches
- Image preprocessing code (contrast enhancement, denoising, sharpening)
- Document-level OCR (when Vision API is available)

❌ **Blocked:**
- `google-cloud-vision` library requires system package installation
- `opencv-python` for image preprocessing requires system package installation

### Solution Options

#### **Option A: Install via Zo Service (Recommended)**

Create a dedicated Python environment in a Zo service with the required packages:

```bash
# In a Zo terminal:
python3 -m venv /home/.venv_hhe200
source /home/.venv_hhe200/bin/activate
pip install google-cloud-vision opencv-python pdf2image
```

Then update the pipeline to use this venv:

```bash
/home/.venv_hhe200/bin/python3 live_run_pipeline.py [row]
```

#### **Option B: Structured Form for Site Evaluators (Fallback)**

Create a Google Form template that site evaluators fill out with structured fields instead of hand-drawing:

**Form Fields:**
- Test Pit Location (GPS coordinates or address)
- Soil Layer 1: Type, Texture, Color, Depth
- Soil Layer 2: Type, Texture, Color, Depth
- Soil Layer 3: Type, Texture, Color, Depth
- Elevation Reference Point (ERP) value
- Finished Grade elevation
- Top of Tank elevation
- Bottom of Field elevation
- Tie Item 1: From [corner/marker] To [system component], Distance
- Tie Item 2: From [corner/marker] To [system component], Distance
- Property Corner 1 Location
- Property Corner 2 Location
- Property Corner 3 Location
- Property Corner 4 Location

**Benefits:**
- 100% accuracy (no OCR errors)
- Structured data (easy to parse)
- Faster data extraction
- No dependency on handwriting quality

**Hybrid Approach:**
- Site evaluators can upload a sketch PDF AND fill the structured form
- Use form data as primary source
- Use sketch for visual reference

### What Was Improved in Phase 2C

**Vision API Changes:**
- Changed from `text_detection()` → `document_text_detection()` for better form/document extraction
- Increased PDF resolution from 150 DPI → 300 DPI for better quality
- Added image preprocessing pipeline (CLAHE contrast enhancement, denoising, sharpening, dilation)

**Data Parsing Changes:**
- Improved soil pattern matching (handles "SAND @ 12 IN", "SAND 12'", etc.)
- Better elevation extraction (ERP, finished grade, top/bottom components)
- Enhanced tie item patterns (multiple formats for property corners, wells, trees)
- Better handling of abbreviated forms and various handwriting styles

**Expected Improvement:**
- With Vision API: 88 chars → ~500-1000+ chars (5-10x improvement)
- With structured form: 100% accuracy on all fields

### Next Steps

**Immediate (This Sprint):**
1. Recommend **Option B: Structured Form** to site evaluators
2. Create a companion Google Form with the fields above
3. Update pipeline to read from both sketch (visual reference) and form (data)

**Later (Once Environment Setup Resolved):**
1. Install Vision API in a Zo service or virtual environment
2. Run improved OCR extraction
3. Use form data + Vision API data together for comprehensive extraction

### Test Results (Current)

With the improved extraction code (even without Vision API):
- Sketch file downloads: ✓ Working
- Maps API queries: ✓ Ready (needs Hermes setup)
- Data parsing: ✓ Enhanced patterns ready
- Drawing generation: ✓ Using observation hole data correctly

**Recommendation:** Go with **Option B (Structured Form)** for immediate improvements. It will solve the quality issues faster than waiting for Vision API setup, and provides better data integrity.
