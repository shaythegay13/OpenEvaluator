# Page 3 Site Plan — Measurement Comparison Report

## Summary
**Status: 50% → 20% (REGRESSION)** — Aspect ratio is inverted and cells are too small

---

## Pinnacle Example (example-pg3-1.png)
| Metric | Value | Notes |
|--------|-------|-------|
| Dimensions | 1275 × 1650 px | Portrait orientation (tall) |
| Aspect Ratio | **0.77** | Width/Height; portrait-biased |
| Grid | 16 cols × 30 rows | Fixed grid structure |
| Cell Width | 79.7 px | 1275 ÷ 16 |
| Cell Height | 55.0 px | 1650 ÷ 30 |
| Cell Ratio | 1.45 | Width/Height per cell |

---

## Current Output (site_plan_current_test.png)
| Metric | Value | Notes |
|--------|-------|-------|
| Dimensions | 864 × 666 px | Landscape orientation (wide) |
| Aspect Ratio | **1.30** | Width/Height; landscape-biased |
| Grid | 16 cols × 30 rows | Same logical grid |
| Cell Width | 54.0 px | 864 ÷ 16 |
| Cell Height | 22.2 px | 666 ÷ 30 |
| Cell Ratio | 2.43 | Width/Height per cell |

---

## Errors Identified

### 1. **Aspect Ratio Mismatch** ⚠️ CRITICAL
- **Expected**: 0.77 (portrait/tall)
- **Actual**: 1.30 (landscape/wide)
- **Error**: 69% wider than expected
- **Fix**: Increase height, reduce width

### 2. **Cell Height Too Small** ⚠️ CRITICAL
- **Expected**: 55.0 px
- **Actual**: 22.2 px
- **Error**: 2.47× too small (60% of target)
- **Scale factor needed**: 2.47×

### 3. **Cell Width Too Small** ⚠️
- **Expected**: 79.7 px
- **Actual**: 54.0 px
- **Error**: 1.48× too small (68% of target)
- **Scale factor needed**: 1.48×

---

## Root Cause

The figure dimensions in `generate_site_plan_pg3()` are set too small.

**Current code location**: `site_plan_generator.py:240-260`

### Current Figure Setup (WRONG):
```python
fig_w, fig_h = _fig(fig_w=8.0, fig_h=6.0, n_cols=16, n_rows=30)
```
- Results in 864 × 666 px at 108 DPI default

### Target Figure Setup (CORRECT):
```python
# Need: 1275 × 1650 px
# At matplotlib default 100 DPI:
# 1275 px ÷ 100 DPI = 12.75 inches width
# 1650 px ÷ 100 DPI = 16.5 inches height
fig_w, fig_h = _fig(fig_w=12.75, fig_h=16.5, n_cols=16, n_rows=30)
```

---

## Required Fixes (Priority Order)

### Priority 1: Fix Figure Dimensions
**File**: `site_plan_generator.py`
**Function**: `generate_site_plan_pg3()`
**Change**: Update `_fig()` call to produce 1275 × 1650 px output

**Before**:
```python
fig_w, fig_h = _fig(fig_w=8.0, fig_h=6.0, n_cols=16, n_rows=30)
```

**After**:
```python
# Target: ~1275 × 1650 px (0.77 aspect ratio, 16×30 grid)
# Using 100 DPI baseline: inches = pixels ÷ 100
fig_w, fig_h = _fig(fig_w=12.75, fig_h=16.5, n_cols=16, n_rows=30)
```

### Priority 2: Verify Element Sizing
Once figure dimensions are correct, check:
- House size proportions (should be ~2.5 × 3.0 cells)
- Tank size (should be ~1.2 × 1.5 cells)
- Disposal field layout (should span ~8-10 cols)
- Road band width (should be ~0.4-0.6 cells)

### Priority 3: Label Positioning
- Verify labels don't overlap with elements
- Check leader line angles and lengths
- Confirm text sizes are readable

---

## Testing Procedure

1. **Modify figure dimensions** in `generate_site_plan_pg3()`
2. **Re-run generator** with test data
3. **Measure output** (should be ~1275 × 1650 px)
4. **Visual comparison** against `example/example-pg3-1.png`
5. **Iterative refinement** for element sizing and positioning

---

## Expected Outcome

After fix:
- ✅ Aspect ratio: 0.77 (portrait)
- ✅ Cell size: ~80 × 55 px
- ✅ Total size: ~1275 × 1650 px
- ✅ Grid visible with correct proportions
- ✅ Elements positioned correctly relative to grid

---

**Next Step**: Apply Priority 1 fix and re-test.
