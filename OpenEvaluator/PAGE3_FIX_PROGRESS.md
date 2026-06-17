# Page 3 Site Plan — Fix Progress

## ✅ Priority 1: Figure Dimensions — COMPLETE

### Change Applied
- **File**: `site_plan_generator.py`, line 52
- **Before**: `FIG_PG3 = (5.76, 4.44)` → 864 × 666 px
- **After**: `FIG_PG3 = (8.50, 11.00)` → 1275 × 1650 px

### Results
| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| Width (px) | 864 | 1275 | 1275 | ✅ |
| Height (px) | 666 | 1650 | 1650 | ✅ |
| Aspect Ratio | 1.30 | 0.77 | 0.77 | ✅ |
| Cell Width (px) | 54.0 | 79.7 | 79.7 | ✅ |
| Cell Height (px) | 22.2 | 55.0 | 55.0 | ✅ |

### Visual Match
- Pixel similarity: 65.9% (indicates content differences in element sizing/positioning)
- Image dimensions: **Perfect match** ✓

---

## ⏳ Priority 2: Element Sizing — IN PROGRESS

### Elements to Verify
1. **House** — target ~2.5 × 3.0 cells (~200 × 165 px)
2. **Tank** — target ~1.2 × 1.5 cells (~95 × 83 px)
3. **Disposal field** — target ~8-10 columns wide
4. **Road band** — target ~0.4-0.6 cells wide
5. **Observation holes** — target ~0.15 × 0.15 cells (~12 × 8 px)

### Inspection Method
1. Generate site plan with test data → `site_plan_fixed_test.png`
2. Compare visually against `example/example-pg3-1.png`
3. Measure each element in the generated code
4. Adjust sizing constants in `site_plan_generator.py`

### Key Code Sections
- House sizing: ~line 350 in `site_plan_generator.py`
- Tank sizing: ~line 380
- Field layout: ~line 420
- Observation holes: ~line 470

---

## ⏳ Priority 3: Label Positioning — PENDING

- Verify label placement doesn't overlap with elements
- Check leader line angles and lengths
- Confirm text sizes are readable

---

## Next Steps

1. **Visual inspection** of `site_plan_fixed_test.png` vs. `example/example-pg3-1.png`
2. **Measure element sizes** in the generated code
3. **Adjust sizing constants** if needed
4. **Re-test and iterate** until 90%+ pixel similarity achieved

---

## Files Modified
- ✏️ `site_plan_generator.py` (line 52: FIG_PG3 constant)

## Test Outputs
- 📄 `site_plan_fixed_test.png` — Current output with fixed dimensions
- 📋 `page3_measurement_report.md` — Detailed measurement analysis
- 📋 `PAGE3_FIX_PROGRESS.md` — This progress file

