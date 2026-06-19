---
title: Test Harness — Pinnacle Examples
description: Two complete input→output pairs for validating the HHE-200 placement solver and rendering pipeline
created: 2026-06-19
updated: 2026-06-19
---

# Test Harness: Two Real Pinnacle Examples

These are the ground-truth input→output pairs used to validate the FormRunner/OpenEvaluator rebuild. Grade the solver against these two sites only — they are the proof that placement and rendering work correctly.

## Marquis (26-018) — Irregular Hexagon Lot

**Site**: Kristen Marquis, 17 Aspen Way, Turner, Maine

**Input**:
- `26-018_field_worksheet_George_Bouchles.pdf` — Field sketch (pencil on graph paper) with dimensions and tie-outs

**Answer Key** (George's finished site plan):
- `26-018 PG1 (1).pdf` — Page 1 (header/site info)
- `26-018 PG2 (1).pdf` — Page 2 (form fields)
- `26-018 PG3 (1).pdf` — Page 3 (plan view with boundary, field placement, soil grid)
- `26-018 PG4 (1).pdf` — Page 4 (cross-section and soil profile)

**Validation Criteria**:
- Field shape: 11×28 cluster, 3 rows of 7 GSF-B43 modules
- Field placement: Match position + rotation within a few feet of the finished plan
- Lot boundary: Irregular hexagon (LOT 7/8/6), ~118 vertices from GeoLibrary
- All setbacks passing (well ≥100', building ≥20', property line ≥10')

---

## Roberts (26-123) — Rectangular Lot with Structures

**Site**: Charles Roberts, 450 Lane Road, Maine

**Input**:
- Grid-paper worksheet (IMG_6862) with frontage dimensions and tie-outs

**Answer Key** (George's finished site plan):
- `26-123 PG1.pdf` — Page 1
- `26-123 PG2.pdf` — Page 2
- `26-123 PG3.pdf` — Page 3 (plan view)
- `26-123 PG4.pdf` — Page 4 (cross-section)

**Validation Criteria**:
- Lot dimensions: 88'/29'/96'/40' frontage (rectangular)
- Field placement: Match George's sketch tie-outs and setbacks
- Existing structures: Garage and mobile home on lot
- Cross-section: Backfill upslope/downslope (4'/10') at stated scales (V:1"=2.5', H:1"=5')

---

## How to Use

1. **Test parcel enricher** — Does it return the real boundary rings and corners for Marquis (irregular hexagon, ~118 vertices)?
2. **Test placement solver** — Does it place the field within a few feet of George's finished plan?
3. **Test rendering** — Do pages 1–4 render correctly with proper boundary, soil layers, cross-section?
4. **Test assembly** — Does the 4-page PDF match the answer key (George's finished plan)?

Pass criteria: Both sites `SOLVED`, field placement within tolerance, all 4 pages rendering correctly.
