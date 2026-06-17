#!/usr/bin/env python3
"""
Simplified drawing generator focused on dense grid + basic elements
- Creates 16x30 grid (480+ lines per page)
- Draws septic system layout with proper spacing
"""

import ezdxf
from typing import Dict
from pathlib import Path


class SimpleDenseDrawingGenerator:
    """Generate detailed CAD drawings from spatial data."""

    def create_page3_site_plan(self, hermes_data: Dict) -> str:
        """Create Page 3: Site Plan with dense grid"""
        dwg = ezdxf.new('R2010')
        msp = dwg.modelspace()

        # Page dimensions (mm): 8.5" x 11" - 0.5" margins
        x_min, y_min = 10, 10
        x_max, y_max = 210, 270

        # Draw 16x30 grid (480 lines!)
        self._draw_grid(msp, x_min, y_min, x_max, y_max, 16, 30)

        # Draw property boundary
        self._draw_boundary(msp, x_min, y_min, x_max, y_max)

        # Draw elements
        self._draw_septic_tank(msp, x_min, x_max, y_min, y_max)
        self._draw_well(msp, x_min, x_max, y_min, y_max)
        self._draw_observation_holes(msp, hermes_data, x_min, x_max, y_min, y_max)

        # Save as DXF
        path = Path("/tmp/site_plan_pg3.dxf")
        dwg.saveas(str(path))
        return str(path)

    def create_page4_disposal_plan(self, hermes_data: Dict) -> str:
        """Create Page 4: Disposal Plan with cross-section"""
        dwg = ezdxf.new('R2010')
        msp = dwg.modelspace()

        x_min, y_min = 10, 10
        x_max, y_max = 210, 270

        # Top half: Disposal plan with grid
        y_mid = (y_min + y_max) / 2
        self._draw_grid(msp, x_min, y_min, x_max, y_mid, 16, 15)

        # Draw disposal field layout
        self._draw_disposal_field_detail(msp, x_min, x_max, y_min, y_mid)

        # Bottom half: Cross-section (no grid, but with profile lines)
        self._draw_cross_section(msp, hermes_data, x_min, x_max, y_mid, y_max)

        # Save as DXF
        path = Path("/tmp/disposal_plan_pg4.dxf")
        dwg.saveas(str(path))
        return str(path)

    def _draw_grid(self, msp, x_min: float, y_min: float, x_max: float, y_max: float, cols: int, rows: int):
        """Draw rectangular grid with cols x rows cells"""
        width = x_max - x_min
        height = y_max - y_min
        col_width = width / cols
        row_height = height / rows

        # Vertical lines
        for i in range(cols + 1):
            x = x_min + i * col_width
            msp.add_line((x, y_min), (x, y_max), dxfattribs={'color': 8, 'lineweight': 0.13})

        # Horizontal lines
        for j in range(rows + 1):
            y = y_min + j * row_height
            msp.add_line((x_min, y), (x_max, y), dxfattribs={'color': 8, 'lineweight': 0.13})

    def _draw_boundary(self, msp, x_min: float, y_min: float, x_max: float, y_max: float):
        """Draw property boundary"""
        margin = 15
        msp.add_lwpolyline(
            [(x_min + margin, y_min + margin),
             (x_max - margin, y_min + margin),
             (x_max - margin, y_max - margin),
             (x_min + margin, y_max - margin),
             (x_min + margin, y_min + margin)],
            dxfattribs={'color': 1, 'lineweight': 0.35}
        )

    def _draw_septic_tank(self, msp, x_min: float, x_max: float, y_min: float, y_max: float):
        """Draw septic tank"""
        cx = x_min + (x_max - x_min) * 0.35
        cy = y_min + (y_max - y_min) * 0.5
        w, h = 15, 10

        msp.add_lwpolyline(
            [(cx - w/2, cy - h/2),
             (cx + w/2, cy - h/2),
             (cx + w/2, cy + h/2),
             (cx - w/2, cy + h/2),
             (cx - w/2, cy - h/2)],
            dxfattribs={'color': 1, 'lineweight': 0.35}
        )
        msp.add_line((cx, cy - h/2), (cx, cy + h/2), dxfattribs={'color': 1, 'lineweight': 0.2})

    def _draw_well(self, msp, x_min: float, x_max: float, y_min: float, y_max: float):
        """Draw water well"""
        wx = x_min + (x_max - x_min) * 0.7
        wy = y_min + (y_max - y_min) * 0.3

        msp.add_circle((wx, wy), 3, dxfattribs={'color': 3})
        msp.add_line((wx - 5, wy), (wx + 5, wy), dxfattribs={'color': 3})
        msp.add_line((wx, wy - 5), (wx, wy + 5), dxfattribs={'color': 3})

    def _draw_observation_holes(self, msp, hermes_data: Dict, x_min: float, x_max: float, y_min: float, y_max: float):
        """Draw observation holes"""
        obs_holes = hermes_data.get('observation_holes', []) or []

        for i, hole in enumerate(obs_holes):
            px = x_min + (x_max - x_min) * (0.3 + i * 0.2)
            py = y_min + (y_max - y_min) * 0.7
            msp.add_circle((px, py), 2, dxfattribs={'color': 5})

    def _draw_disposal_field_detail(self, msp, x_min: float, x_max: float, y_min: float, y_max: float):
        """Draw disposal field with modules"""
        cx = x_min + (x_max - x_min) * 0.5
        cy = y_min + (y_max - y_min) * 0.5
        modules = 3

        module_width = 30
        field_length = 40
        start_x = cx - (modules * module_width / 2)

        for i in range(modules):
            mod_x = start_x + i * module_width
            msp.add_lwpolyline(
                [(mod_x, cy - field_length/2),
                 (mod_x + module_width * 0.9, cy - field_length/2),
                 (mod_x + module_width * 0.9, cy + field_length/2),
                 (mod_x, cy + field_length/2),
                 (mod_x, cy - field_length/2)],
                dxfattribs={'color': 2, 'lineweight': 0.25}
            )

            # Internal spacing lines
            for row in range(5):
                y_row = cy - field_length/2 + (row + 1) * (field_length / 6)
                msp.add_line((mod_x, y_row), (mod_x + module_width * 0.9, y_row),
                            dxfattribs={'color': 2, 'lineweight': 0.15})

    def _draw_cross_section(self, msp, hermes_data: Dict, x_min: float, x_max: float, y_min: float, y_max: float):
        """Draw cross-section profile"""
        obs_holes = hermes_data.get('observation_holes', []) or []

        # Base line
        cy = y_min + (y_max - y_min) * 0.7
        msp.add_line((x_min, cy), (x_max, cy), dxfattribs={'color': 0, 'lineweight': 0.35})

        # Draw soil columns
        if obs_holes:
            col_width = (x_max - x_min) / (len(obs_holes) + 1)
            for i, hole in enumerate(obs_holes):
                cx = x_min + (i + 1) * col_width
                depth_mm = min(30, hole.get('depth_ft', 5) * 5)

                msp.add_lwpolyline(
                    [(cx - 3, cy), (cx + 3, cy),
                     (cx + 3, cy - depth_mm), (cx - 3, cy - depth_mm),
                     (cx - 3, cy)],
                    dxfattribs={'color': 5, 'lineweight': 0.3}
                )

                # Hatching for soil
                spacing = depth_mm / 4
                for j in range(1, int(depth_mm / spacing) + 1):
                    y_hatch = cy - j * spacing
                    msp.add_line((cx - 3, y_hatch), (cx + 3, y_hatch),
                               dxfattribs={'color': 5, 'lineweight': 0.15})


def generate_simple_drawings(spatial_data: Dict) -> Dict:
    """Main entry point"""
    try:
        gen = SimpleDenseDrawingGenerator()

        page3 = gen.create_page3_site_plan(spatial_data)
        page4 = gen.create_page4_disposal_plan(spatial_data)

        return {
            'page3_path': page3,
            'page4_path': page4,
            'status': 'success'
        }
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'page3_path': None,
            'page4_path': None,
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    import json

    with open('hermes_output.json') as f:
        data = json.load(f)

    result = generate_simple_drawings(data)
    print(f"Generated: {result['status']}")
    if result['status'] == 'success':
        print(f"  Page 3: {result['page3_path']}")
        print(f"  Page 4: {result['page4_path']}")
