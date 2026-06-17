#!/usr/bin/env python3
"""Convert DXF files to SVG for browser previewing."""
from pathlib import Path
import subprocess, sys, tempfile

def dxf_to_svg(dxf_path)
    cmd = ["python3", "-m", "ezdxf", "draw", str(dxf_path), "--format=svg"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "dxf_output/PG3.dxf"
    svg = dxf_to_svg(path)
    out = Path(path).with_suffix(".svg")
    out.write_text(svg)
    print(f"Saved SVG to {out}")