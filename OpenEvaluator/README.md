# OpenEvaluator — Maine DHHS HHE-200 Permit Application Toolkit

This is the **active working project** for generating Maine DHHS HHE-200 subsurface wastewater disposal permit application drawings from Google Form submissions.

## Project Structure

```
OpenEvaluator/
├── toolkit/                    ← open-source spec + Hermes pipeline docs
│   ├── SPEC.md                 ← project specification
│   ├── docs/                   ← setup guides, email templates, drawing spec
│   │   ├── gcp-setup.md       ← OAuth 2.0 setup for Hermes
│   │   ├── requirements.md    ← HHE-200 form field reference
│   │   ├── drawing_spec.md    ← AutoCAD drawing standards
│   │   └── email_template.md ← Hermes email output template
│   └── scripts/
│       ├── generate_drawing.py   ← standalone drawing CLI
│       ├── pdf_field_mapper.py  ← PDF coordinate extraction
│       └── hermes_flowchart.md   ← pipeline flowchart
│
├── examples/                  ← A+ reference examples (filled by George Bouchles)
│   ├── 26-018 PG1 (1).pdf     ← filled page 1 (property info + signature)
│   ├── 26-018 PG2 (1).pdf    ← filled page 2 (system design table)
│   ├── 26-018 PG3 (1).pdf    ← filled page 3 (site plan + soil profile)
│   └── 26-018 PG4 (1).pdf    ← filled page 4 (disposal plan + cross-section)
│
├── reference/                 ← blank source forms
│   ├── HHE-200-2025-1.pdf through HHE-200-2025-8.pdf
│   └── HHE-204-blank.pdf
│
├── HHE-200-2025.pdf          ← source form (master blank)
├── HHE-200-filled.pdf         ← output from fill_form.py (with test values)
├── site_plan.dxf             ← output from site_plan_generator.py
├── field_map.yaml            ← field coordinates extracted via OCR from examples/
├── fill_form.py              ← fills PDF using field_map.yaml
├── sheet_parser.py           ← parses Google Sheet row → field dict
├── site_plan_generator.py    ← generates ezDXF site plan drawing
├── run_pipeline.py           ← orchestrator: parse → fill → draw → upload
├── extract_coordinates.py    ← extracts PDF text coordinates
└── run_parser.py             ← parse sheet row → fill PDF → verify
```

## Hermes Pipeline (Google Form → Permit Package)

```
Google Form (Site Evaluator submission)
       │
       ▼
Google Sheet ("Form Responses 1")
       │
       ▼
Hermes triggered (webhook or cron)
       │
       ├── Read new row from sheet
       ├── Retrieve sketch from Drive (bouchlesshay@gmail.com)
       │
       ▼
┌─────────────────────────────────────────────┐
│  OpenEvaluator Processing                    │
│                                              │
│  1. sheet_parser.py → field dict             │
│  2. fill_form.py → HHE-200-filled.pdf        │
│  3. site_plan_generator.py → site_plan.dxf  │
│  4. Upload both to Drive folder (column S)   │
└─────────────────────────────────────────────┘
       │
       ▼
Email drafted + sent to Site Evaluator
  ├─ HHE-200 merged PDF
  ├─ Individual page attachments
  ├─ AutoCAD drawing (DXF)
  └─ Conditional docs (HHE-204, GSB Notes) if triggered
```

## Running the Pipeline

```bash
# Full pipeline (fills PDF + generates DXF + uploads to Drive)
python run_pipeline.py

# Test the sheet parser only
python run_parser.py

# Fill the PDF only
python -c "
import yaml, json
from sheet_parser import build_field_dict
from fill_form import fill_form
fields = build_field_dict()
fill_form(fields, 'test_output.pdf')
"

# Generate site plan only
python site_plan_generator.py
```

## GCP Setup (for Drive/Sheets/Gmail access)

See `toolkit/docs/gcp-setup.md` for OAuth 2.0 setup instructions.

Required credential paths:
- `~/.config/google_oauth_credentials.json` — OAuth client ID/secret
- `~/.config/google_token_store.json` — access/refresh tokens

Legacy Hermes files under `~/.hermes/` are still accepted by `live_run_pipeline.py` as a fallback, but the `.config` paths above are the documented setup.

## Sheet Data

Spreadsheet: `1ebjhzBSaH9zrJBORxKTkM56ukKV2IlNJ-3r1wJslNBc`
Sheet: `"Form Responses 1"`, row 2+ (first data row after headers)

Column mapping (from sheet_parser.py):
- A: Timestamp
- B: Client name, Phone number, and Address
- C: Property Location Details
- D: Map and Lot # and Acreage
- E: Site Evaluator's Information
- F: Application Type
- G: Use and bedrooms/flow
- H: Seasonal use
- I: Shoreland zoning
- J: Water supply and well
- K: Soil summary at disposal area
- L: Limiting factor
- M: Disposal system type
- N: Septic tank setup
- O: Design flow override
- P: Planned field size and layout (if known)
- Q: Key distances between features
- R: Elevation reference point (ERP) and elevations (if known)
- S: Uploads (Google Drive folder link)

## Key Scripts

| Script | Purpose |
|--------|---------|
| `sheet_parser.py` | Parse sheet row → flat field dict matching field_map.yaml |
| `fill_form.py` | Fill HHE-200 PDF fields using field_map.yaml coordinates |
| `site_plan_generator.py` | Generate ezDXF site plan drawing |
| `run_pipeline.py` | Orchestrate full pipeline + Drive upload |
| `extract_coordinates.py` | Extract text coordinates from PDF pages |
| `field_map.yaml` | Canonical field → PDF coordinate mapping |

---
For the open-source toolkit specification, see `toolkit/`.
