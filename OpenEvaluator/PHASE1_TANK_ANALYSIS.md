# Phase 1: Tank & System Components — Code Analysis & Fixes

## Current Implementation Issues

### Issue 1: Tank Rendering
**Lines 545-563 in site_plan_generator.py**

Current code:
```python
tw_g = max(0.8, 10.0 / ft_per_cell)  # Tank width (grid units)
td_g = max(0.5, 6.0 / ft_per_cell)   # Tank depth (grid units)

_rect(ax, tank_x, tank_y, tw_g, td_g, ec=C_BLACK, lw=1.8, fc="#f8f8f8")
_txt(ax, f"PROP. {tank_cap} GAL SEPTIC TANK", ...)
```

**Problems:**
1. Tank is just a plain rectangle with no fill pattern or internal details
2. Missing "INSPECT & REPAIR" label clarity
3. No visual distinction between tank compartments
4. Label positioning may be unclear

**Required Fixes:**
1. Add tank fill pattern (diagonal hatch or dots) for visual distinction
2. Add inlet/outlet pipe labels with clear positioning
3. Increase tank visual prominence
4. Better label spacing

---

### Issue 2: Distribution Box (D-Box) Rendering
**Lines 564-569**

Current code:
```python
_rect(ax, dbox_x, dby, dbs, dbs, ec=C_BLACK, lw=1.8, fc="#f0f0f0")
_txt(ax, "DIST. BOX", cx, dby - 0.12, size=4.8, ha="center", va="top")
```

**Problems:**
1. D-box is too small visually (only 0.35-0.5 grid units)
2. Missing inlet/outlet pipe connections from tank
3. No label for outgoing distribution piping
4. Inadequate spacing between tank and D-box

**Required Fixes:**
1. Increase D-box size proportionally (currently too small)
2. Add visual inlet from tank
3. Add outlet labels to field distribution lines
4. Add "4\" DIA" pipe label clarity

---

### Issue 3: Pipe Connections & Labels
**Lines 548-562, 566-568**

Current code shows pipes but missing:
1. Clear inlet/outlet marking on tank
2. Distribution box inlet/outlet distinction
3. Pipe type labels ("4\" DIA NON-PERF." vs "4\" DIA PERF.")
4. Proper line styles (solid vs dashed)

---

### Issue 4: Setback Table Oversizing (BOTTOM Region - 118% excess)
**Lines 605-637**

Current code:
```python
row_h = 0.62          # Row height = 0.62 grid units
tbl_h = len(rows_data) * row_h + 0.45  # Total height
```

**Calculation:**
- 5 data rows × 0.62 = 3.1 units
- Header = 0.45 units
- Total ≈ 3.55 grid units (too tall!)

**Problems:**
1. Row height is too large (0.62 should be ~0.45)
2. Table takes up too much vertical space
3. Contributes to BOTTOM region having 118% excess content

**Required Fixes:**
1. Reduce `row_h` from 0.62 to 0.45
2. Reduce table header height from 0.45 to 0.35
3. Reduce font sizes from 4.3 to 4.0
4. Reduce overall table padding

---

## Implementation Plan

### Step 1: Enhance Tank Rendering
**File:** site_plan_generator.py, lines 545-563

Changes:
1. Add tank fill pattern (diagonal hatch)
2. Improve tank label positioning
3. Add inlet/outlet pipe indicators
4. Better spacing

### Step 2: Fix D-Box Sizing & Details
**File:** site_plan_generator.py, lines 564-569

Changes:
1. Increase D-box visibility
2. Add clear inlet from tank
3. Add outlet distribution label
4. Better spacing

### Step 3: Enhance Pipe Labels
**File:** site_plan_generator.py, lines 548-570

Changes:
1. Add inlet/outlet clarity markers
2. Improve pipe type labels
3. Better visual hierarchy

### Step 4: Reduce Setback Table Size
**File:** site_plan_generator.py, line 605-637

Changes:
1. Reduce `row_h` from 0.62 to 0.45
2. Reduce header height from 0.45 to 0.35
3. Reduce font sizes
4. Tighten padding

---

## Success Criteria

**Target Measurements After Fixes:**
- TOP region: 151,440 → 140,000+ pixels (achieve 92%+ of example)
- BOTTOM region: 214,692 → 110,000-120,000 pixels (achieve 90%+ of example)
- Overall pixel similarity: 85%+ with example

---

## Execution Order

1. **First:** Fix setback table sizing (BOTTOM) — quick win to reduce excess content
2. **Second:** Enhance tank/D-box rendering (TOP) — add missing visual details
3. **Third:** Test and verify measurements
4. **Fourth:** Final adjustments if needed

