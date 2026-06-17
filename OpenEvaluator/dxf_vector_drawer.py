#!/usr/bin/env python3
"""
Parse DXF file and draw geometries as vector graphics on PDF pages.
Maintains AutoCAD-style technical drawing appearance.
"""

from pathlib import Path
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


def _calculate_bounds(msp):
    """Calculate bounding box of all DXF entities."""
    min_x, min_y, max_x, max_y = None, None, None, None
    
    for entity in msp:
        try:
            entity_type = entity.dxftype()
            coords = []
            
            if entity_type == 'LINE':
                p1, p2 = entity.dxf.start, entity.dxf.end
                coords = [(p1.x, p1.y), (p2.x, p2.y)]
            
            elif entity_type in ('LWPOLYLINE', 'POLYLINE'):
                coords = [(p[0], p[1]) for p in entity.get_points()]
            
            elif entity_type == 'CIRCLE':
                c = entity.dxf.center
                r = entity.dxf.radius
                coords = [(c.x - r, c.y - r), (c.x + r, c.y + r)]
            
            elif entity_type == 'ARC':
                c = entity.dxf.center
                r = entity.dxf.radius
                coords = [(c.x - r, c.y - r), (c.x + r, c.y + r)]
            
            elif entity_type in ('TEXT', 'MTEXT'):
                t = entity.dxf.insert
                coords = [(t.x, t.y)]
            
            # Update bounds
            for x, y in coords:
                if min_x is None:
                    min_x, min_y, max_x, max_y = x, y, x, y
                else:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
        
        except Exception as e:
            logger.debug(f"Error processing {entity.dxftype()}: {e}")
    
    return min_x, min_y, max_x, max_y


def draw_dxf_on_pdf(pdf_path: str, dxf_path: str, page_indices: List[int]) -> None:
    """
    Parse DXF file and draw all geometries as vector graphics on specified PDF pages.
    
    Args:
        pdf_path: Path to PDF file
        dxf_path: Path to DXF file
        page_indices: List of 0-indexed page numbers to draw on (e.g., [2, 3] for pages 3-4)
    """
    try:
        import fitz
        import ezdxf
    except ImportError as e:
        logger.error(f"Missing required library: {e}")
        raise
    
    dxf_file = Path(dxf_path)
    if not dxf_file.exists():
        raise FileNotFoundError(f"DXF file not found: {dxf_path}")
    
    # Load DXF
    dwg = ezdxf.readfile(str(dxf_file))
    msp = dwg.modelspace()
    
    # Calculate bounds
    min_x, min_y, max_x, max_y = _calculate_bounds(msp)
    
    if min_x is None or max_x <= min_x or max_y <= min_y:
        logger.warning("DXF has no valid geometry bounds")
        return
    
    logger.info(f"DXF bounds: ({min_x:.2f}, {min_y:.2f}) → ({max_x:.2f}, {max_y:.2f})")
    
    # Open PDF
    doc = fitz.open(pdf_path)
    
    for page_idx in page_indices:
        if page_idx < 0 or page_idx >= doc.page_count:
            continue
        
        page = doc[page_idx]
        page_rect = page.rect
        
        # Calculate scaling: fit DXF to page with margins
        margin = 30
        page_width = page_rect.width - (2 * margin)
        page_height = page_rect.height - (2 * margin)
        
        dxf_width = max_x - min_x
        dxf_height = max_y - min_y
        
        scale_x = page_width / dxf_width
        scale_y = page_height / dxf_height
        scale = min(scale_x, scale_y)
        
        logger.info(f"Drawing on page {page_idx + 1}: scale={scale:.2f}")
        
        # Draw each entity
        for entity in msp:
            _draw_entity(page, entity, min_x, min_y, margin, scale, page_rect.height)
    
    doc.save(pdf_path, incremental=True)
    doc.close()
    logger.info(f"Drew DXF geometries on pages {[p+1 for p in page_indices]}")


def _draw_entity(page, entity, min_x: float, min_y: float, margin: float, scale: float, page_height: float):
    """Draw a single DXF entity on the PDF page."""
    import fitz
    
    try:
        entity_type = entity.dxftype()
        
        if entity_type == 'LINE':
            p1 = entity.dxf.start
            p2 = entity.dxf.end
            pt1 = _transform_point(p1.x, p1.y, min_x, min_y, margin, scale, page_height)
            pt2 = _transform_point(p2.x, p2.y, min_x, min_y, margin, scale, page_height)
            page.draw_line(pt1, pt2, color=(0, 0, 0), width=1.0)
        
        elif entity_type == 'LWPOLYLINE':
            points = []
            for point in entity.get_points():
                pt = _transform_point(point[0], point[1], min_x, min_y, margin, scale, page_height)
                points.append(pt)
            if len(points) > 1:
                for i in range(len(points) - 1):
                    page.draw_line(points[i], points[i + 1], color=(0, 0, 0), width=1.0)
        
        elif entity_type == 'POLYLINE':
            points = []
            for vertex in entity.get_points():
                pt = _transform_point(vertex[0], vertex[1], min_x, min_y, margin, scale, page_height)
                points.append(pt)
            if len(points) > 1:
                for i in range(len(points) - 1):
                    page.draw_line(points[i], points[i + 1], color=(0, 0, 0), width=1.0)
        
        elif entity_type == 'CIRCLE':
            c = entity.dxf.center
            r = entity.dxf.radius
            center = _transform_point(c.x, c.y, min_x, min_y, margin, scale, page_height)
            r_scaled = r * scale
            # Draw circle as 32 arc segments
            import math
            points = []
            for i in range(33):
                angle = (i / 32) * 2 * math.pi
                x = center.x + r_scaled * math.cos(angle)
                y = center.y + r_scaled * math.sin(angle)
                points.append(fitz.Point(x, y))
            for i in range(len(points) - 1):
                page.draw_line(points[i], points[i + 1], color=(0, 0, 0), width=1.0)
        
        elif entity_type == 'ARC':
            c = entity.dxf.center
            r = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            center = _transform_point(c.x, c.y, min_x, min_y, margin, scale, page_height)
            r_scaled = r * scale
            # Draw arc as 32 segments
            import math
            angle_range = end_angle - start_angle
            if angle_range < 0:
                angle_range += 360
            points = []
            for i in range(33):
                angle_deg = start_angle + (i / 32) * angle_range
                angle_rad = math.radians(angle_deg)
                x = center.x + r_scaled * math.cos(angle_rad)
                y = center.y + r_scaled * math.sin(angle_rad)
                points.append(fitz.Point(x, y))
            for i in range(len(points) - 1):
                page.draw_line(points[i], points[i + 1], color=(0, 0, 0), width=1.0)
        
        elif entity_type == 'TEXT':
            t = entity.dxf.insert
            pt = _transform_point(t.x, t.y, min_x, min_y, margin, scale, page_height)
            text = entity.dxf.text
            height = entity.dxf.height * scale
            page.insert_text(pt, text, fontsize=max(height, 6), color=(0, 0, 0))
        
        elif entity_type == 'MTEXT':
            t = entity.dxf.insert
            pt = _transform_point(t.x, t.y, min_x, min_y, margin, scale, page_height)
            text = entity.text
            height = entity.dxf.char_height * scale
            page.insert_text(pt, text, fontsize=max(height, 6), color=(0, 0, 0))
    
    except Exception as e:
        logger.debug(f"Skipped entity {entity.dxftype()}: {e}")


def _transform_point(x: float, y: float, min_x: float, min_y: float, 
                     margin: float, scale: float, page_height: float):
    """Transform DXF coordinates to PDF page coordinates."""
    import fitz
    
    # Scale and translate to PDF space
    px = (x - min_x) * scale + margin
    # Flip Y (DXF origin bottom-left, PDF origin top-left)
    py = page_height - ((y - min_y) * scale + margin)
    
    return fitz.Point(px, py)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 dxf_vector_drawer.py <pdf_path> <dxf_path> [page_indices]")
        print("Example: python3 dxf_vector_drawer.py form.pdf site_plan.dxf 2,3")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    dxf_path = sys.argv[2]
    pages = [2, 3]  # Default to pages 3-4 (0-indexed)
    
    if len(sys.argv) > 3:
        pages = [int(p) for p in sys.argv[3].split(",")]
    
    draw_dxf_on_pdf(pdf_path, dxf_path, pages)
    print(f"✓ Drew DXF on pages {[p+1 for p in pages]}")
