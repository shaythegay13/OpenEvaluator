#!/usr/bin/env python3
"""
Page 3 Deep-Dive: Reverse-engineer example measurements to determine correct scaling.

Goal: Understand what scale, sizing constants, and parameters produce the 
target fill percentages observed in the pinnacle example.

Approach:
1. Extract pixel measurements from example PDF
2. Calculate implied ft_per_cell and scale from element sizes
3. Work backwards to required max_ft and scale adjustments
"""

import json
import math
from pathlib import Path

# Target fill percentages (from hermes analysis)
TARGET = {
    "ROAD_BAND": 0.232,
    "HOUSE": 0.219,
    "TANK": 0.280,
    "FIELD": 0.196,
}

# Current fill percentages (with bug fix applied)
CURRENT = {
    "ROAD_BAND": 0.053,
    "HOUSE": 0.097,
    "TANK": 0.148,
    "FIELD": 0.380,
}

# System parameters (defaults)
DEFAULTS = {
    "acreage": 2.35,
    "tank_to_house": 8.0,
    "field_to_house": 20.0,
    "cluster_l": 28.0,
    "cluster_w": 11.0,
}

# Grid and figure settings (after fix)
GRID = {
    "n_cols": 16,
    "n_rows": 30,
    "fig_w": 8.5,
    "fig_h": 11.0,
}

STANDARD_SCALES = [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200]

def calculate_system_span():
    """Calculate vertical system span from defaults."""
    sys_vert = (
        DEFAULTS["tank_to_house"] +
        DEFAULTS["field_to_house"] +
        DEFAULTS["cluster_l"]
    )
    return sys_vert  # Should be 56.0 ft

def analyze_scale_logic():
    """Analyze how scale is currently calculated."""
    sys_vert = calculate_system_span()
    
    # Current scale calculation
    target_ftpc = sys_vert / 7.0  # 56 / 7 = 8.0
    max_ft_system = target_ftpc * (GRID["n_cols"] - 2)  # 8.0 * 14 = 112 ft
    
    # Which scale gets selected?
    cells_per_inch = GRID["n_cols"] / GRID["fig_w"]  # 16 / 8.5 = 1.88
    usable_cells = GRID["n_cols"] - 2  # 14
    
    print("=" * 70)
    print("CURRENT SCALE CALCULATION ANALYSIS")
    print("=" * 70)
    print(f"\nSystem vertical span: {sys_vert} ft")
    print(f"Target ft/cell (system fills 7 rows): {target_ftpc:.2f}")
    print(f"Max ft that system should span: {max_ft_system:.1f}")
    print(f"\nCells per inch: {cells_per_inch:.2f}")
    print(f"Usable cells: {usable_cells}")
    
    print(f"\nScale selection:")
    for s in STANDARD_SCALES:
        ft_per_cell = s / cells_per_inch
        max_ft_fits = ft_per_cell * usable_cells
        fits = "✓ SELECTED" if max_ft_fits >= max_ft_system else "✗ too small"
        print(f"  Scale {s:3d}': {ft_per_cell:5.2f} ft/cell → max {max_ft_fits:6.1f} ft {fits}")
    
    # Find actual selection
    for s in STANDARD_SCALES:
        ft_per_cell = s / cells_per_inch
        if ft_per_cell * usable_cells >= max_ft_system:
            print(f"\n→ SELECTED: 1'{s}\" scale = {ft_per_cell:.2f} ft/cell")
            return ft_per_cell, s
    
    s = STANDARD_SCALES[-1]
    ft_per_cell = s / cells_per_inch
    print(f"\n→ FALLBACK: 1'{s}\" scale = {ft_per_cell:.2f} ft/cell")
    return ft_per_cell, s

def estimate_required_scale():
    """Estimate what scale would produce target percentages."""
    print("\n" + "=" * 70)
    print("TARGET SCALE ANALYSIS")
    print("=" * 70)
    
    # Key insight: Tank fill ratio indicates scale
    # Example: TANK is 28.0% at example scale
    # Current: TANK is 14.8% at our scale
    # This suggests our scale is ~2x too large (too many ft/cell)
    
    # If TANK should be 28% but is 14.8%, multiply ft_per_cell by ratio:
    scale_ratio = CURRENT["TANK"] / TARGET["TANK"]
    print(f"\nTank fill ratio analysis:")
    print(f"  Target: {TARGET['TANK']:.1%}")
    print(f"  Current: {CURRENT['TANK']:.1%}")
    print(f"  Ratio: {scale_ratio:.2f}")
    print(f"  → Suggest ft_per_cell should be ~{scale_ratio:.2f}x larger")
    
    # Current ft_per_cell is likely around 5-6 ft/cell
    # If we need 2x the size, we need 2.5-3 ft/cell
    # That corresponds to a smaller scale (like 10' or 15' instead of 20-30')
    
    print(f"\nImplication:")
    print(f"  If current scale = ~25-30 ft/scale")
    print(f"  And we need ~2x smaller ft/cell")
    print(f"  Then target scale ≈ 10-15 ft/scale")

def element_sizing_analysis():
    """Analyze element sizing logic from code."""
    print("\n" + "=" * 70)
    print("ELEMENT SIZING ANALYSIS")
    print("=" * 70)
    
    lot_w_ft = math.sqrt(DEFAULTS["acreage"] * 43560)
    
    print(f"\nLot width (from {DEFAULTS['acreage']} acres): {lot_w_ft:.1f} ft")
    
    # House sizing (from code)
    house_ft_w = max(36.0, lot_w_ft * 0.12)
    house_ft_h = max(28.0, lot_w_ft * 0.09)
    print(f"\nHouse:")
    print(f"  Width: {house_ft_w:.1f} ft")
    print(f"  Height: {house_ft_h:.1f} ft")
    
    # These are in feet. To appear correct, they need to be scaled correctly
    # If ft_per_cell is too large, the house will appear too small
    
    print(f"\nKey insight:")
    print(f"  Element dimensions (house, tank, field) are calculated in feet")
    print(f"  Their visual size depends on ft_per_cell scale")
    print(f"  → Smaller ft_per_cell = larger visual size")
    print(f"  → Larger ft_per_cell = smaller visual size")

def calculate_required_max_ft():
    """Calculate what max_ft would produce target scale."""
    print("\n" + "=" * 70)
    print("REQUIRED ADJUSTMENT CALCULATION")
    print("=" * 70)
    
    cells_per_inch = GRID["n_cols"] / GRID["fig_w"]
    usable_cells = GRID["n_cols"] - 2
    
    # Current: max_ft produces a large scale (like 25-30 ft)
    # Current ft_per_cell ≈ scale / cells_per_inch
    # If scale=25: ft_per_cell = 25 / 1.88 ≈ 13.3 ft/cell
    # If scale=20: ft_per_cell = 20 / 1.88 ≈ 10.6 ft/cell
    # If scale=15: ft_per_cell = 15 / 1.88 ≈ 8.0 ft/cell
    # If scale=10: ft_per_cell = 10 / 1.88 ≈ 5.3 ft/cell
    
    print(f"\nScale to ft_per_cell conversion:")
    print(f"  Cells per inch: {cells_per_inch:.2f}")
    for s in [5, 10, 15, 20, 25, 30]:
        ftpc = s / cells_per_inch
        max_ft_fits = ftpc * usable_cells
        print(f"  Scale {s:2d}' → {ftpc:5.2f} ft/cell → max {max_ft_fits:6.1f} ft")
    
    print(f"\nTo produce target fill percentages:")
    print(f"  We likely need scale ≈ 10-15 (ft_per_cell ≈ 5-8)")
    print(f"  Currently getting scale ≈ 20-30 (ft_per_cell ≈ 10-16)")
    print(f"  → Need to reduce max_ft by ~50-60%")
    
    sys_vert = calculate_system_span()
    print(f"\nCurrent max_ft calculation:")
    print(f"  sys_vert = {sys_vert} ft")
    print(f"  target_ftpc = sys_vert / 7.0 = {sys_vert / 7.0:.1f}")
    print(f"  max_ft_system = {sys_vert / 7.0 * (GRID['n_cols'] - 2):.1f} ft")
    
    # To get smaller ft_per_cell, we need smaller max_ft
    # If we want scale=15 instead of scale=25+
    # We need max_ft ≈ 112 ft (current) down to ~70-80 ft
    
    print(f"\nSuggested adjustment:")
    print(f"  Reduce 'target_ftpc = sys_vert / 7.0' ")
    print(f"  To 'target_ftpc = sys_vert / 5.5' or '/5.0'")
    print(f"  This would target filling 5-5.5 rows instead of 7")
    print(f"  Result: larger system elements, smaller overall scale")

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║ PAGE 3 DEEP-DIVE: REVERSE-ENGINEERING CORRECT SCALE & SIZING ║")
    print("╚" + "=" * 68 + "╝")
    
    # Run analyses
    analyze_scale_logic()
    estimate_required_scale()
    element_sizing_analysis()
    calculate_required_max_ft()
    
    print("\n" + "=" * 70)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 70)
    print("""
The issue is that `max_ft` calculation targets filling 7 grid rows,
which results in a scale that's too large (too many feet/cell).

This makes all elements appear too small because:
- House fills 9.7% instead of 21.9% (56% too small)
- Tank fills 14.8% instead of 28.0% (47% too small)
- Field is oversized (because it scales differently)

RECOMMENDATION:
1. Reduce target rows from 7 → 5.5 or 5.0
2. This will reduce max_ft proportionally
3. Smaller max_ft → smaller scale selected → smaller ft_per_cell → larger elements
4. Should bring TANK to 25-28% and HOUSE to 20-22%

NEXT STEP: Test adjustment with target_ftpc = sys_vert / 5.5
    """)
    print("=" * 70)
