---
title: Site Plan Generator
description: Generate a proper scaled DXF site plan from property field worksheet geometry for HHE-200 applications
created: 2026-05-04
updated: 2026-05-04
tags: [cad, dxf, site-plan, septic, engineering]
version: 1.0.0
---

# generate_site_plan.py

Generate a proper AutoCAD DXF site plan from property geometry extracted from the field worksheet.

## Geometry extracted from 26-018_field_worksheet_George_Bouchles.pdf

```
Property: 17 Aspen Way, Turner, Maine (map/lot 26-018)
Property dimensions: ~185 ft wide × ~220 ft deep (from scan annotations)
House: rectangle ~55 ft wide × 28.5 ft deep, labeled
Garage (GAR): rectangle ~16.5 ft wide, labeled
Bearing callout: 3-33-29 (southwest of property, presumably road frontage bearing)
Drive: labeled, connects house to road frontage
ST: road/street on south side
Septic tank (ST): south of house, labeled
Planned disposal field: north/northeast of house, 3 rows × 7 modules (Eljen-in-drain)
Well: existing drilled well, private, 125 ft from worksheet data
Setbacks: well-to-field ≥100 ft, surface water 75 ft, property line 10 ft
Ground water: 24 inches (limiting factor)
Scale note on scan: 1 inch ≈ 20 ft (field sketch scale)
```

## Layer structure

| Layer | Color (ACI) | Contents |
|-------|-------------|----------|
| PROPERTY | 3 (green) | Property boundary polygon |
| STRUCTURE | 1 (red) | House, garage outlines |
| SEPTIC | 4 (blue) | Septic tank rectangle |
| DISPOSAL | 2 (yellow) | Eljen-in-drain cluster, fill zones |
| WELL | 5 (cyan) | Well circle + label |
| DIM | 7 (white/black) | Dimension lines + text |
| SETBACK | 8 (gray) | Setback limit lines + distance labels |
| TEXT | 7 (white/black) | Labels, north arrow, scale bar |
| NORTH | 7 (white/black) | North arrow |

## Output

`site_plan.dxf` — model space at 1 unit = 1 foot, properly layered DXF R2010.