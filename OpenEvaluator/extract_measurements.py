#!/usr/bin/env python3
"""
Extract visual measurements from example PNGs and compare with generated outputs.
This will help us identify exact sizing/positioning discrepancies.
"""
import json
from pathlib import Path
from PIL import Image
import numpy as np

def get_image_dimensions(img_path):
    """Get image pixel dimensions."""
    try:
        img = Image.open(img_path)
        return img.size  # (width, height)
    except Exception as e:
        return None

def analyze_example_proportions():
    """Analyze the pinnacle example to extract key proportions."""
    examples = {
        "pg3_1": Path("example/example-pg3-1.png"),
        "pg3_detail": Path("example/example-pg3-detail-1.png"),
        "pg3_preview": Path("example/pg3_preview.png"),
    }
    
    results = {}
    for name, path in examples.items():
        if path.exists():
            dims = get_image_dimensions(path)
            results[name] = {
                "path": str(path),
                "dimensions": dims,
                "aspect_ratio": dims[0] / dims[1] if dims else None
            }
    
    return results

def estimate_element_positions(img_path, grid_cols=16, grid_rows=30):
    """
    Try to estimate element positions by analyzing the image.
    For now, just get dimensions. Visual inspection will handle positioning.
    """
    try:
        img = Image.open(img_path)
        img_array = np.array(img)
        
        # Get dimensions
        height, width = img_array.shape[:2]
        
        # Estimate grid cell size
        cell_w = width / grid_cols
        cell_h = height / grid_rows
        
        return {
            "image_size": (width, height),
            "cell_width_px": cell_w,
            "cell_height_px": cell_h,
            "estimated_grid": {
                "cols": grid_cols,
                "rows": grid_rows,
                "cell_w": cell_w,
                "cell_h": cell_h
            }
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 70)
    print("SITE PLAN (PAGE 3) MEASUREMENT ANALYSIS")
    print("=" * 70)
    
    # Analyze examples
    examples = analyze_example_proportions()
    
    print("\n1. PINNACLE EXAMPLE DIMENSIONS:")
    print("-" * 70)
    for name, info in examples.items():
        print(f"\n{name}:")
        print(f"  Path: {info['path']}")
        print(f"  Dimensions: {info['dimensions']} pixels")
        print(f"  Aspect Ratio: {info['aspect_ratio']:.2f}" if info['aspect_ratio'] else "  Aspect Ratio: N/A")
        
        # Analyze grid proportions
        if info['dimensions']:
            analysis = estimate_element_positions(info['path'])
            if 'image_size' in analysis:
                print(f"  Estimated Grid Cell: {analysis['estimated_grid']['cell_w']:.1f} x {analysis['estimated_grid']['cell_h']:.1f} px")
    
    print("\n" + "=" * 70)
    print("2. NEXT STEPS:")
    print("-" * 70)
    print("□ Generate current site plan from test data")
    print("□ Measure current output dimensions")
    print("□ Identify scale factor differences")
    print("□ Create side-by-side pixel-by-pixel comparison")
    print("□ Extract specific element measurements (house, tank, field)")
    print("=" * 70)

if __name__ == "__main__":
    main()
