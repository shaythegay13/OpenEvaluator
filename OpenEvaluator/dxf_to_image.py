#!/usr/bin/env python3
"""Convert DXF file to PNG image for PDF embedding."""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def dxf_to_image(
    dxf_path: str,
    output_path: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    dpi: int = 150
) -> str:
    """
    Convert DXF file to PNG image.
    
    Args:
        dxf_path: Path to DXF file
        output_path: Output PNG path (defaults to same name, .png extension)
        width: Image width in pixels
        height: Image height in pixels
        dpi: Resolution in DPI
    
    Returns:
        Path to generated PNG file
    """
    try:
        import ezdxf
        from PIL import Image, ImageDraw
    except ImportError as e:
        logger.error(f"Missing required library: {e}")
        raise

    dxf_file = Path(dxf_path)
    if not dxf_file.exists():
        raise FileNotFoundError(f"DXF file not found: {dxf_path}")

    output_file = Path(output_path) if output_path else dxf_file.with_suffix(".png")

    try:
        # Load DXF document
        dwg = ezdxf.readfile(str(dxf_file))
        logger.info(f"Loaded DXF: {dxf_file}")
        
        # Get the modelspace (where drawings are)
        msp = dwg.modelspace()
        
        # Create blank image
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Get all entities and their bounds
        entities = list(msp)
        if not entities:
            logger.warning(f"No entities found in DXF {dxf_file}")
            image.save(str(output_file))
            return str(output_file.resolve())
        
        # Calculate bounds of all entities
        min_x, min_y, max_x, max_y = None, None, None, None

        for entity in entities:
            x_min, y_min, x_max, y_max = None, None, None, None

            # Try to get bbox first
            try:
                bounds = entity.bbox()
                if bounds:
                    ext = bounds.extmin, bounds.extmax
                    x_min, y_min = ext[0].x, ext[0].y
                    x_max, y_max = ext[1].x, ext[1].y
            except:
                pass

            # If bbox failed, handle manually based on entity type
            if x_min is None:
                if entity.dxftype() == 'LINE':
                    p1 = entity.dxf.start
                    p2 = entity.dxf.end
                    x_min, x_max = min(p1.x, p2.x), max(p1.x, p2.x)
                    y_min, y_max = min(p1.y, p2.y), max(p1.y, p2.y)
                elif entity.dxftype() == 'LWPOLYLINE':
                    points = list(entity.get_points())
                    if points:
                        x_min = min(p[0] for p in points)
                        x_max = max(p[0] for p in points)
                        y_min = min(p[1] for p in points)
                        y_max = max(p[1] for p in points)
                elif entity.dxftype() == 'CIRCLE':
                    c = entity.dxf.center
                    r = entity.dxf.radius
                    x_min, x_max = c.x - r, c.x + r
                    y_min, y_max = c.y - r, c.y + r
                elif entity.dxftype() == 'TEXT':
                    t = entity.dxf.insert
                    x_min, x_max = t.x, t.x + 10
                    y_min, y_max = t.y, t.y + 5
                else:
                    continue

            if x_min is not None:
                if min_x is None:
                    min_x, min_y, max_x, max_y = x_min, y_min, x_max, y_max
                else:
                    min_x = min(min_x, x_min)
                    min_y = min(min_y, y_min)
                    max_x = max(max_x, x_max)
                    max_y = max(max_y, y_max)
        
        # If we found bounds, draw entities using the bounds to scale
        if min_x is not None and max_x > min_x and max_y > min_y:
            logger.info(f"Drawing bounds: x=[{min_x:.1f}, {max_x:.1f}], y=[{min_y:.1f}, {max_y:.1f}]")
            # Calculate scaling
            dxf_width = max_x - min_x
            dxf_height = max_y - min_y
            scale_x = (width * 0.95) / dxf_width
            scale_y = (height * 0.95) / dxf_height
            scale = min(scale_x, scale_y)
            
            # Draw each entity
            for entity in entities:
                try:
                    if entity.dxftype() == 'LINE':
                        p1 = entity.dxf.start
                        p2 = entity.dxf.end
                        x1 = (p1.x - min_x) * scale + 20
                        y1 = height - ((p1.y - min_y) * scale + 20)
                        x2 = (p2.x - min_x) * scale + 20
                        y2 = height - ((p2.y - min_y) * scale + 20)
                        draw.line([(x1, y1), (x2, y2)], fill='black', width=2)
                    
                    elif entity.dxftype() == 'LWPOLYLINE':
                        points = []
                        for point in entity.get_points():
                            x = (point[0] - min_x) * scale + 20
                            y = height - ((point[1] - min_y) * scale + 20)
                            points.append((x, y))
                        if len(points) > 1:
                            draw.polygon(points, outline='black')
                    
                    elif entity.dxftype() == 'CIRCLE':
                        c = entity.dxf.center
                        r = entity.dxf.radius
                        cx = (c.x - min_x) * scale + 20
                        cy = height - ((c.y - min_y) * scale + 20)
                        r_scaled = r * scale
                        draw.ellipse(
                            [(cx - r_scaled, cy - r_scaled), (cx + r_scaled, cy + r_scaled)],
                            outline='black'
                        )
                    
                    elif entity.dxftype() == 'ARC':
                        # Simplified arc handling
                        c = entity.dxf.center
                        r = entity.dxf.radius
                        cx = (c.x - min_x) * scale + 20
                        cy = height - ((c.y - min_y) * scale + 20)
                        r_scaled = r * scale
                        draw.ellipse(
                            [(cx - r_scaled, cy - r_scaled), (cx + r_scaled, cy + r_scaled)],
                            outline='black'
                        )
                    
                    elif entity.dxftype() == 'TEXT':
                        t = entity.dxf.insert
                        x = (t.x - min_x) * scale + 20
                        y = height - ((t.y - min_y) * scale + 20)
                        text = entity.dxf.text
                        draw.text((x, y), text, fill='black')
                
                except Exception as e:
                    logger.debug(f"Skipped entity {entity.dxftype()}: {e}")
        
        image.save(str(output_file))
        logger.info(f"DXF converted to PNG: {output_file}")
        return str(output_file.resolve())
    
    except Exception as e:
        logger.error(f"Failed to convert DXF: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 dxf_to_image.py <dxf_file> [output_png]")
        sys.exit(1)
    
    dxf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = dxf_to_image(dxf_path, output_path)
    print(f"✓ Saved: {result}")
