#!/usr/bin/env python3
"""
Convert DXF drawings to PNG using ezdxf rendering and PIL.
Used to embed drawings in HHE-200 PDF forms.
"""

import ezdxf
from PIL import Image, ImageDraw
from pathlib import Path
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def render_dxf_to_png(
    dxf_path: str,
    png_path: str,
    width: int = 1200,
    height: int = 1600,
    margin: int = 20,
    background: str = "white",
    line_color: str = "black",
    line_width: int = 1,
) -> bool:
    """
    Render DXF file to PNG image.

    Args:
        dxf_path: Path to DXF file
        png_path: Output PNG file path
        width: Output image width in pixels
        height: Output image height in pixels
        margin: Margin around drawing in pixels
        background: Background color
        line_color: Line drawing color
        line_width: Line width in pixels

    Returns:
        True if successful, False otherwise
    """
    dxf_path = Path(dxf_path)
    png_path = Path(png_path)

    if not dxf_path.exists():
        logger.error(f"DXF file not found: {dxf_path}")
        return False

    try:
        # Read DXF
        dwg = ezdxf.readfile(str(dxf_path))
        msp = dwg.modelspace()

        # Calculate bounds by scanning all entities
        all_x = []
        all_y = []
        entities_to_draw = []

        for entity in msp:
            try:
                etype = entity.dxftype()

                if etype == "LINE":
                    p1 = entity.dxf.start
                    p2 = entity.dxf.end
                    all_x.extend([p1[0], p2[0]])
                    all_y.extend([p1[1], p2[1]])
                    entities_to_draw.append(("line", p1, p2, entity))

                elif etype == "LWPOLYLINE":
                    points = list(entity.get_points("xy"))
                    for p in points:
                        all_x.append(p[0])
                        all_y.append(p[1])
                    entities_to_draw.append(("polyline", points, None, entity))

                elif etype == "CIRCLE":
                    c = entity.dxf.center
                    r = entity.dxf.radius
                    all_x.extend([c[0] - r, c[0] + r])
                    all_y.extend([c[1] - r, c[1] + r])
                    entities_to_draw.append(("circle", c, r, entity))

                elif etype == "ARC":
                    c = entity.dxf.center
                    r = entity.dxf.radius
                    all_x.extend([c[0] - r, c[0] + r])
                    all_y.extend([c[1] - r, c[1] + r])
                    entities_to_draw.append(("arc", c, r, entity))

                elif etype == "TEXT":
                    p = entity.dxf.insert
                    all_x.append(p[0])
                    all_y.append(p[1])
                    entities_to_draw.append(("text", p, entity.dxf.text, entity))

            except Exception as e:
                logger.debug(f"Skipped entity {etype}: {e}")

        if not all_x or not all_y:
            logger.warning(f"No drawable entities found in {dxf_path}")
            return False

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Add margin in DXF units
        dxf_margin = 5
        min_x -= dxf_margin
        max_x += dxf_margin
        min_y -= dxf_margin
        max_y += dxf_margin

        dxf_width = max_x - min_x or 1
        dxf_height = max_y - min_y or 1

        logger.debug(
            f"DXF bounds: X [{min_x:.1f}, {max_x:.1f}], Y [{min_y:.1f}, {max_y:.1f}]"
        )
        logger.debug(f"DXF size: {dxf_width:.1f} × {dxf_height:.1f}")

        # Calculate pixel scale (fit to canvas maintaining aspect ratio)
        scale_x = (width - 2 * margin) / dxf_width
        scale_y = (height - 2 * margin) / dxf_height
        scale = min(scale_x, scale_y)

        # Create image
        img = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(img)

        def dxf_to_pixel(x: float, y: float) -> Tuple[int, int]:
            """Convert DXF coordinates to pixel coordinates."""
            px = margin + (x - min_x) * scale
            py = height - margin - (y - min_y) * scale
            return (int(px), int(py))

        # Draw all entities
        for etype, *params in entities_to_draw:
            try:
                if etype == "line":
                    p1, p2, entity = params
                    pixel1 = dxf_to_pixel(p1[0], p1[1])
                    pixel2 = dxf_to_pixel(p2[0], p2[1])
                    draw.line([pixel1, pixel2], fill=line_color, width=line_width)

                elif etype == "polyline":
                    points, _, entity = params
                    if len(points) > 1:
                        pixels = [dxf_to_pixel(p[0], p[1]) for p in points]
                        draw.polygon(pixels, outline=line_color, fill=None)

                elif etype == "circle":
                    center, radius, entity = params
                    c_pixel = dxf_to_pixel(center[0], center[1])
                    r_pixel = int(radius * scale)
                    draw.ellipse(
                        [
                            (c_pixel[0] - r_pixel, c_pixel[1] - r_pixel),
                            (c_pixel[0] + r_pixel, c_pixel[1] + r_pixel),
                        ],
                        outline=line_color,
                        fill=None,
                    )

                elif etype == "arc":
                    center, radius, entity = params
                    c_pixel = dxf_to_pixel(center[0], center[1])
                    r_pixel = int(radius * scale)
                    draw.ellipse(
                        [
                            (c_pixel[0] - r_pixel, c_pixel[1] - r_pixel),
                            (c_pixel[0] + r_pixel, c_pixel[1] + r_pixel),
                        ],
                        outline=line_color,
                        fill=None,
                    )

                elif etype == "text":
                    p, text, entity = params
                    p_pixel = dxf_to_pixel(p[0], p[1])
                    draw.text(p_pixel, str(text), fill=line_color, font=None)

            except Exception as e:
                logger.debug(f"Draw error ({etype}): {e}")

        img.save(str(png_path))
        file_size = png_path.stat().st_size
        logger.info(f"✓ Rendered {png_path.name} ({file_size:,} bytes)")
        return True

    except Exception as e:
        logger.error(f"Rendering error: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: dxf_to_png_renderer.py <input.dxf> <output.png>")
        sys.exit(1)

    dxf_file = sys.argv[1]
    png_file = sys.argv[2]
    render_dxf_to_png(dxf_file, png_file)
