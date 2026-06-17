---
title: HHE-200 Pages 3 & 4 Drawing Specification
description: Complete visual and technical specification derived from analyzing example PDFs
created: 2026-05-31
updated: 2026-05-31
---

# HHE-200 Drawing Design Specification

## Executive Summary

After analyzing the example Pages 3 and 4, the key issue is **scale, proportion, visual hierarchy, and professional CAD drawing conventions**. The current system generates technically correct content but lacks the visual polish and engineering standards of real examples.

---

## PAGE 3: SITE PLAN

### Overall Layout
- **Grid Background**: Fine light gray grid (~0.1" spacing at print)
- **Scale Notation**: "Scale: 1" = 100'" prominently displayed
- **Content**: Property boundary, lots, roads, existing structures, soil profile

### Key Visual Elements

**1. Property Boundary & Lots**
- Thick black solid lines (0.015" stroke)
- Clear lot labels: LOT 1, LOT 2, LOT 6
- Dimensions marked outside with leader lines

**2. Existing Structures** 
- Diagonal crosshatching (45°, ~0.02" spacing)
- Labels: EXISTING DECK, POOL, GARAGE, DWELLING
- Clearly differentiated from undeveloped areas

**3. Site Plan Detail**
- Roads labeled with name/direction
- Tree symbols (circles with crossing lines)
- Driveway shown with parallel lines
- Clear north arrow or compass

**4. Soil Profile Section (Bottom Left)**
- Vertical scale: 0-48 feet
- Two observation holes (Obs Hole A & B)
- Soil types with distinct hatching patterns
- Depth labels every 8 feet
- Soil type: BROWN, FINE, PEAT, SAND, LOAM, SILT, GRAY

**5. Locus Map (Top Right)**
- Grayscale reference map
- Shows surrounding context
- "SITE" labeled clearly

### Soil Type Hatching Patterns
- **BROWN/TOP**: Solid light fill
- **SAND**: Coarse diagonal crosshatch (45°)
- **FINE SAND**: Fine diagonal lines (45°)
- **SILT**: Horizontal parallel lines
- **PEAT**: Dotted/stipple pattern
- **LOAM**: Medium dots
- **GRAY Clay**: Fine dots

### Typography
- Main title "SITE PLAN": ~12pt bold
- Soil labels: ~8pt inside zones
- Dimension text: ~7pt with leaders
- Notes: ~6-7pt

---

## PAGE 4: DISPOSAL PLAN & CROSS-SECTION

### Upper Section: Disposal Plan (~50% of page)

**Scale**: 1" = 20' to 1" = 50'

**Components**:

**1. Septic Tank**
- Rectangular shape with thin lines
- Dimensions labeled (6' × 8')
- Inlet/outlet marked with arrows
- Internal baffles shown as dashed lines

**2. Distribution Box**
- Connected to tank with line
- Internal compartments visible
- Flow arrows showing direction

**3. Eljen Module System**
- Grid of rectangles (~3×5 modules)
- Each module ~2-3 ft squares
- Total system ~20 ft × 30 ft
- Grid lines thin (0.01" stroke)
- "Eljen Module" label

**4. Distribution Piping**
- Thin lines with flow arrows
- Labeled for each function
- Equal distribution marked

**5. Elevation Information**
- Ground elevation line shown
- System depth below grade marked
- Top of module elevation noted

### Lower Section: Cross-Section View (~45% of page)

**1. Existing Grade**
- Ground surface line (curved/straight)
- Elevation marked (e.g., "EL 120'")

**2. Septic Tank in Profile**
- Rectangular outline
- Inlet/outlet pipes shown
- Depth measurements from grade
- Clear dimension lines

**3. Soil Layers in Cross-Section**
- Horizontal stratification clearly shown
- ~1-3 inches tall per layer in drawing
- Soil type labels inside
- Hatching matches plan view
- Depth to each layer marked

**4. Module System Profile**
- Side view of modules
- Individual modules outlined
- Gravel/sand layers shown
- Support structure indicated

**5. Key Dimensions**
- Vertical: Grade to system bottom
- Horizontal: Module spacing
- Depth to restrictive layer
- Fill height marked

### Typography
- Section title: ~12pt bold
- Component labels: ~8pt
- Dimension text: ~7pt with leaders
- Notes: ~6pt

---

## CRITICAL LINE WEIGHTS & STYLES

| Purpose | Weight | Style | Color |
|---------|--------|-------|-------|
| Grid Background | 0.005" | Solid | Light Gray |
| Property Boundary | 0.015" | Solid | Black |
| Lot Lines | 0.008" | Solid | Black |
| System Piping | 0.010" | Solid | Black |
| Underground | 0.008" | Dashed | Black |
| Dimension Lines | 0.005" | Solid | Black |
| Text Leaders | 0.005" | Solid | Black |

---

## KEY DIFFERENCES FROM CURRENT OUTPUT

1. **Grid is missing or too coarse** → Should be fine and light gray
2. **Scale is wrong** → Elements not proportional to 1" = 100'
3. **Line quality inconsistent** → Should be crisp and thin
4. **Hatching patterns too coarse or missing** → Must clearly show soil types
5. **Text positioning poor** → Labels should follow professional standards
6. **Overall layout scattered** → Should fill space professionally

---

## IMPLEMENTATION STRATEGY

**Tools**: Use **ezdxf** library to generate vector drawings, then embed in PDF

**Approach**:
1. Create vector-based drawing (not raster)
2. Control all line weights precisely
3. Apply hatching patterns programmatically
4. Position text accurately with leader lines
5. Generate high-quality output for professional use
