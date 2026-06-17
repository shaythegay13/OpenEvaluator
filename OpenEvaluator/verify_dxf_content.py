#!/usr/bin/env python3
"""Verify DXF file content"""
import ezdxf
from pathlib import Path

dxf_path = Path('/home/workspace/OpenEvaluator/dwg_output/PG1_filled.dxf')

print(f"Reading {dxf_path.name}...")
doc = ezdxf.readfile(str(dxf_path))
msp = doc.modelspace()

print("\nTEXT ENTITIES IN DXF:\n")
text_count = 0
for entity in msp:
    if entity.dxftype() == 'TEXT':
        text_count += 1
        text_value = entity.dxf.text
        x = entity.dxf.insert[0]
        y = entity.dxf.insert[1]
        print(f"  [{x:.1f}, {y:.1f}] {text_value!r}")
        if text_count >= 20:  # Show first 20
            print("  ...")
            break

print(f"\nTotal TEXT entities: {text_count}")
