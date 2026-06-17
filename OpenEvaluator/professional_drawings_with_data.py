"""Professional HHE-200 Drawing Generator using real site data from Hermes"""

import ezdxf
from typing import Dict, List, Optional
import math

class ProfessionalDrawingGeneratorWithData:
    """Generates professional CAD drawings from actual site survey data."""

    def __init__(self):
        self.dwg = None
        self.msp = None
        self.LINE_WEIGHTS = {
            'grid': 0.13,
            'thin': 0.20,
            'medium': 0.25,
            'bold': 0.38,
        }
        self.MM_PER_FOOT = 304.8  # For scaling coordinates

    def create_page3_site_plan(self, hermes_data: Dict) -> object:
        """Create Page 3: Site Plan with real property layout"""
        self.dwg = ezdxf.new('R2010')
        self.msp = self.dwg.modelspace()

        page_width = 215.9  # mm (8.5")
        page_height = 279.4  # mm (11")
        margin = 12.7  # mm (0.5")

        # Extract data from Hermes
        prop = hermes_data.get('property', {})
        structures = hermes_data.get('existing_structures', [])
        well = hermes_data.get('water_supply', {})
        obs_holes = hermes_data.get('observation_holes', [])
        contours = hermes_data.get('contour_lines', [])

        lot_corners = prop.get('lot_corners', [])
        acreage = prop.get('acreage', 1.0)

        # Calculate scale to fit property on page
        scale = self._calculate_scale_for_property(lot_corners, page_width - 2*margin, page_height - 2*margin)

        # Draw background grid
        self._draw_fine_grid(margin, margin, page_width - 2*margin, page_height - 2*margin)

        # Draw property boundary from lot corners
        if lot_corners:
            self._draw_property_boundary(lot_corners, margin, margin, scale)

        # Draw roads
        roads = prop.get('roads', [])
        if roads:
            self._draw_roads(roads, lot_corners, margin, margin, scale)

        # Draw contour lines
        if contours:
            self._draw_contour_lines(contours, lot_corners, margin, margin, scale)

        # Draw existing structures
        for struct in structures:
            self._draw_structure(struct, lot_corners, margin, margin, scale)

        # Draw well
        if well:
            self._draw_well(well, lot_corners, margin, margin, scale)

        # Draw observation holes
        for hole in obs_holes:
            self._draw_observation_hole_marker(hole, lot_corners, margin, margin, scale)

        # Draw soil profile at bottom
        self._draw_soil_profile_from_data(obs_holes, margin, page_height - margin - 40, 60, 40)

        # Add title and scale
        self._add_title_and_scale("SITE PLAN", f"Scale 1\" = {int(1/scale)}'", margin, page_height - margin - 5)

        return self.dwg

    def create_page4_disposal_and_section(self, hermes_data: Dict) -> object:
        """Create Page 4: Disposal Plan & Cross-Section"""
        self.dwg = ezdxf.new('R2010')
        self.msp = self.dwg.modelspace()

        page_width = 215.9
        page_height = 279.4
        margin = 12.7

        # Extract data
        prop = hermes_data.get('property', {})
        tank = hermes_data.get('septic_system', {}).get('tank', {})
        field = hermes_data.get('septic_system', {}).get('disposal_field', {})
        obs_holes = hermes_data.get('observation_holes', [])
        elevation = hermes_data.get('elevation_data', {})
        lot_corners = prop.get('lot_corners', [])

        scale = self._calculate_scale_for_property(lot_corners, page_width - 2*margin, page_height - 2*margin)

        # Draw background grid
        self._draw_fine_grid(margin, margin, page_width - 2*margin, page_height - 2*margin)

        # Top half: Disposal plan
        plan_height = (page_height - 2*margin) * 0.48
        self._draw_disposal_plan_layout(tank, field, lot_corners, margin, margin + plan_height + 10,
                                       page_width - 2*margin, plan_height, scale)

        # Bottom half: Cross-section
        self._draw_cross_section_from_data(obs_holes, elevation, field, margin, margin,
                                          page_width - 2*margin, plan_height - 5)

        # Add title and scale
        self._add_title_and_scale("SUBSURFACE WASTEWATER DISPOSAL PLAN", f"Scale 1\" = {int(1/scale)}'",
                                 margin, page_height - margin - 5)

        return self.dwg

    def _calculate_scale_for_property(self, lot_corners: List[Dict],
                                     max_width: float, max_height: float) -> float:
        """Calculate drawing scale to fit property on page"""
        if not lot_corners:
            return 0.01  # Default scale

        xs = [c.get('x', 0) for c in lot_corners]
        ys = [c.get('y', 0) for c in lot_corners]

        prop_width = max(xs) - min(xs)
        prop_height = max(ys) - min(ys)

        if prop_width == 0 or prop_height == 0:
            return 0.01

        # Convert feet to mm and calculate scale
        # scale = drawing_mm / real_feet
        scale_x = (max_width * 0.95) / (prop_width / 12 * 25.4)  # feet to mm conversion
        scale_y = (max_height * 0.95) / (prop_height / 12 * 25.4)

        return min(scale_x, scale_y)

    def _draw_fine_grid(self, x: float, y: float, width: float, height: float):
        """Draw fine light gray grid background"""
        grid_spacing = 2.54

        current_x = x
        while current_x <= x + width:
            self.msp.add_line((current_x, y), (current_x, y + height),
                            dxfattribs={'color': 8, 'lineweight': self.LINE_WEIGHTS['grid']})
            current_x += grid_spacing

        current_y = y
        while current_y <= y + height:
            self.msp.add_line((x, current_y), (x + width, current_y),
                            dxfattribs={'color': 8, 'lineweight': self.LINE_WEIGHTS['grid']})
            current_y += grid_spacing

    def _draw_property_boundary(self, lot_corners: List[Dict], x: float, y: float, scale: float):
        """Draw property boundary polygon"""
        if not lot_corners:
            return

        points = []
        for corner in lot_corners:
            px = x + (corner.get('x', 0) / 12 * 25.4) * scale  # feet to mm
            py = y + (corner.get('y', 0) / 12 * 25.4) * scale
            points.append((px, py))

        # Close the polygon
        if points and points[0] != points[-1]:
            points.append(points[0])

        if len(points) > 1:
            self.msp.add_lwpolyline(points, dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['bold']})

    def _draw_roads(self, roads: List[Dict], lot_corners: List[Dict], x: float, y: float, scale: float):
        """Draw roads around property"""
        # Extract property bounds
        if not lot_corners:
            return

        xs = [c.get('x', 0) for c in lot_corners]
        ys = [c.get('y', 0) for c in lot_corners]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        for road in roads:
            name = road.get('name', '')
            side = road.get('side', 'north')
            distance = road.get('distance_ft', 0)

            # Draw road line based on side
            if side == 'north':
                px1 = x + (min_x / 12 * 25.4) * scale
                py = y + ((max_y + distance) / 12 * 25.4) * scale
                px2 = x + (max_x / 12 * 25.4) * scale
                self.msp.add_line((px1, py), (px2, py), dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
            elif side == 'south':
                px1 = x + (min_x / 12 * 25.4) * scale
                py = y + ((min_y - distance) / 12 * 25.4) * scale
                px2 = x + (max_x / 12 * 25.4) * scale
                self.msp.add_line((px1, py), (px2, py), dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
            elif side == 'east':
                px = x + ((max_x + distance) / 12 * 25.4) * scale
                py1 = y + (min_y / 12 * 25.4) * scale
                py2 = y + (max_y / 12 * 25.4) * scale
                self.msp.add_line((px, py1), (px, py2), dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
            elif side == 'west':
                px = x + ((min_x - distance) / 12 * 25.4) * scale
                py1 = y + (min_y / 12 * 25.4) * scale
                py2 = y + (max_y / 12 * 25.4) * scale
                self.msp.add_line((px, py1), (px, py2), dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})

            # Label road
            label = self.msp.add_text(name, dxfattribs={'height': 2.5, 'color': 0})
            label.dxf.insert = (px1 if side in ['north', 'south'] else px,
                               py if side in ['north', 'south'] else py1)

    def _draw_contour_lines(self, contours: List[Dict], lot_corners: List[Dict],
                           x: float, y: float, scale: float):
        """Draw elevation contour lines"""
        if not lot_corners or not contours:
            return

        for contour in contours:
            elevation = contour.get('elevation_ft', 0)
            points = contour.get('points', [])

            if len(points) < 2:
                continue

            # Convert points
            converted_points = []
            for pt in points:
                px = x + (pt[0] / 12 * 25.4) * scale
                py = y + (pt[1] / 12 * 25.4) * scale
                converted_points.append((px, py))

            # Draw polyline for contour
            self.msp.add_lwpolyline(converted_points,
                                   dxfattribs={'color': 8, 'lineweight': self.LINE_WEIGHTS['thin']})

    def _draw_structure(self, struct: Dict, lot_corners: List[Dict],
                       x: float, y: float, scale: float):
        """Draw building structure"""
        name = struct.get('name', 'STRUCTURE')
        px = x + (struct.get('position_x', 0) / 12 * 25.4) * scale
        py = y + (struct.get('position_y', 0) / 12 * 25.4) * scale
        w = (struct.get('width_ft', 10) / 12 * 25.4) * scale
        h = (struct.get('length_ft', 10) / 12 * 25.4) * scale

        # Draw rectangle for building
        points = [(px, py), (px + w, py), (px + w, py + h), (px, py + h), (px, py)]
        self.msp.add_lwpolyline(points, dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})

        # Add crosshatch pattern
        self._add_diagonal_hatch(px, py, w, h)

        # Label
        label = self.msp.add_text(name, dxfattribs={'height': 1.5, 'color': 0})
        label.dxf.insert = (px + w/2, py + h/2)

    def _draw_well(self, well: Dict, lot_corners: List[Dict], x: float, y: float, scale: float):
        """Draw water supply well"""
        px = x + (well.get('position_x', 0) / 12 * 25.4) * scale
        py = y + (well.get('position_y', 0) / 12 * 25.4) * scale
        radius = 1.5  # mm

        self.msp.add_circle((px, py), radius, dxfattribs={'color': 5, 'lineweight': self.LINE_WEIGHTS['thin']})

        label = self.msp.add_text("WELL", dxfattribs={'height': 1.5, 'color': 5})
        label.dxf.insert = (px, py - 3)

    def _draw_observation_hole_marker(self, hole: Dict, lot_corners: List[Dict],
                                     x: float, y: float, scale: float):
        """Draw observation hole location marker"""
        px = x + (hole.get('position_x', 0) / 12 * 25.4) * scale
        py = y + (hole.get('position_y', 0) / 12 * 25.4) * scale
        hole_num = hole.get('hole_number', 1)

        # Draw small circle
        self.msp.add_circle((px, py), 1.0, dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']})

        label = self.msp.add_text(f"OH-{hole_num}", dxfattribs={'height': 1.0, 'color': 0})
        label.dxf.insert = (px, py + 2)

    def _draw_soil_profile_from_data(self, obs_holes: List[Dict], x: float, y: float,
                                    width: float, height: float):
        """Draw soil profile from observation hole data"""
        if not obs_holes:
            return

        title = self.msp.add_text("SOIL PROFILE", dxfattribs={'height': 2.5, 'color': 0})
        title.dxf.insert = (x, y)

        hole_width = (width - 5) / len(obs_holes)

        for i, hole in enumerate(obs_holes):
            hole_x = x + (i * (hole_width + 2))
            self._draw_single_hole_profile(hole, hole_x, y - height, hole_width, height)

    def _draw_single_hole_profile(self, hole: Dict, x: float, y: float, width: float, height: float):
        """Draw single borehole profile"""
        hole_num = hole.get('hole_number', 1)
        depth_ft = hole.get('depth_ft', 36)
        soil_layers = hole.get('soil_layers', [])

        # Draw outline
        self.msp.add_lwpolyline([(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)],
                               dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']})

        # Draw soil layers
        if soil_layers:
            layer_height_mm = height / depth_ft
            for layer in soil_layers:
                depth_start = layer.get('depth_start_in', 0) / 12
                depth_end = layer.get('depth_end_in', 12) / 12
                color = layer.get('color', 'Unknown')

                layer_y = y + (depth_start * layer_height_mm)
                layer_h = (depth_end - depth_start) * layer_height_mm

                # Simple fill
                layer_label = self.msp.add_text(color[:4], dxfattribs={'height': 1.0, 'color': 0})
                layer_label.dxf.insert = (x + width/2, layer_y + layer_h/2)

        # Label
        label = self.msp.add_text(f"Hole {hole_num}", dxfattribs={'height': 1.5, 'color': 0})
        label.dxf.insert = (x + width/2, y + height + 2)

    def _draw_disposal_plan_layout(self, tank: Dict, field: Dict, lot_corners: List[Dict],
                                  x: float, y: float, width: float, height: float, scale: float):
        """Draw disposal system plan layout"""
        title = self.msp.add_text("DISPOSAL PLAN", dxfattribs={'height': 3, 'color': 0})
        title.dxf.insert = (x, y)

        # Draw septic tank
        if tank:
            tx = x + ((tank.get('position_x', 0) / 12 * 25.4) * scale)
            ty = y - ((tank.get('position_y', 0) / 12 * 25.4) * scale)
            tw = (tank.get('dimensions', {}).get('length', 5) / 12 * 25.4) * scale
            th = (tank.get('dimensions', {}).get('width', 3) / 12 * 25.4) * scale

            self.msp.add_lwpolyline([(tx, ty), (tx + tw, ty), (tx + tw, ty + th), (tx, ty + th), (tx, ty)],
                                   dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})

            label = self.msp.add_text("SEPTIC\nTANK", dxfattribs={'height': 1.5, 'color': 0})
            label.dxf.insert = (tx + tw/2, ty + th/2)

        # Draw disposal field
        if field:
            fx = x + ((field.get('position_x', 0) / 12 * 25.4) * scale)
            fy = y - ((field.get('position_y', 0) / 12 * 25.4) * scale)
            rows = field.get('rows', 1)
            mods = field.get('modules_per_row', 1)
            mod_spacing = (field.get('module_spacing_ft', 1) / 12 * 25.4) * scale
            row_spacing = (field.get('row_spacing_ft', 2) / 12 * 25.4) * scale

            # Draw module grid
            for r in range(rows):
                for m in range(mods):
                    mx = fx + (m * mod_spacing * 2)
                    my = fy - (r * row_spacing)
                    self.msp.add_lwpolyline([(mx, my), (mx + mod_spacing, my),
                                            (mx + mod_spacing, my + mod_spacing), (mx, my + mod_spacing), (mx, my)],
                                           dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']})

            label = self.msp.add_text(f"MODULES\n{rows}x{mods}", dxfattribs={'height': 2, 'color': 0})
            label.dxf.insert = (fx + (mods * mod_spacing), fy)

    def _draw_cross_section_from_data(self, obs_holes: List[Dict], elevation: Dict, field: Dict,
                                     x: float, y: float, width: float, height: float):
        """Draw cross-section view with soil layers and elevation"""
        title = self.msp.add_text("CROSS-SECTION", dxfattribs={'height': 3, 'color': 0})
        title.dxf.insert = (x, y)

        # Get elevation data
        elevations = elevation.get('grade_elevations', [])
        limiting = elevation.get('limiting_factor', {})
        limiting_depth = limiting.get('depth_in', 24)

        if not obs_holes:
            return

        # Use first observation hole for cross-section
        hole = obs_holes[0]
        soil_layers = hole.get('soil_layers', [])
        depth_ft = hole.get('depth_ft', 36)

        # Draw ground surface line
        grade_y = y - height * 0.3
        self.msp.add_line((x, grade_y), (x + width, grade_y),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['bold']})

        label = self.msp.add_text("GRADE", dxfattribs={'height': 1.5, 'color': 0})
        label.dxf.insert = (x - 5, grade_y)

        # Draw soil layers below grade
        if soil_layers:
            layer_height = (height * 0.7) / depth_ft
            for layer in soil_layers:
                depth_start = layer.get('depth_start_in', 0) / 12
                depth_end = layer.get('depth_end_in', 12) / 12
                color = layer.get('color', 'Unknown')

                layer_y_start = grade_y - (depth_start * layer_height)
                layer_y_end = grade_y - (depth_end * layer_height)

                # Draw layer rectangle
                self.msp.add_lwpolyline([(x + 5, layer_y_start), (x + width - 5, layer_y_start),
                                        (x + width - 5, layer_y_end), (x + 5, layer_y_end), (x + 5, layer_y_start)],
                                       dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']})

                # Label layer
                label = self.msp.add_text(color, dxfattribs={'height': 1.2, 'color': 0})
                label.dxf.insert = (x + width/2, (layer_y_start + layer_y_end) / 2)

        # Draw limiting factor line
        if limiting_depth > 0:
            lim_y = grade_y - ((limiting_depth / 12) * (height * 0.7 / depth_ft))
            self.msp.add_line((x, lim_y), (x + width, lim_y),
                             dxfattribs={'color': 5, 'lineweight': self.LINE_WEIGHTS['thin']})
            label = self.msp.add_text(f"GW {limiting_depth}\"", dxfattribs={'height': 1.0, 'color': 5})
            label.dxf.insert = (x - 8, lim_y)

    def _add_diagonal_hatch(self, x: float, y: float, width: float, height: float):
        """Add diagonal hatch lines to represent existing structure"""
        spacing = 1.0  # mm
        num_lines = int((width + height) / spacing) + 2

        for i in range(num_lines):
            start_x = x - height + (i * spacing)
            start_y = y
            end_x = x + (i * spacing)
            end_y = y + height

            # Clip to rectangle bounds
            if start_x < x:
                start_y = y + (x - start_x)
                start_x = x
            if end_y > y + height:
                end_x = x + (y + height - end_y)
                end_y = y + height

            if start_x < x + width and end_x > x and start_y < y + height and end_y > y:
                self.msp.add_line((start_x, start_y), (end_x, end_y),
                                 dxfattribs={'color': 0, 'lineweight': 0.07})

    def _add_title_and_scale(self, title: str, scale: str, x: float, y: float):
        """Add title and scale notation"""
        title_text = self.msp.add_text(title, dxfattribs={'height': 3, 'color': 0})
        title_text.dxf.insert = (x, y)

        scale_text = self.msp.add_text(scale, dxfattribs={'height': 2, 'color': 0})
        scale_text.dxf.insert = (x, y - 5)


# ============================================================================
# Wrapper Function for Pipeline Integration
# ============================================================================

def generate_professional_drawings(spatial_data: Dict) -> Dict:
    """
    Wrapper function that generates professional drawings from spatial data.

    Returns a dictionary with paths to generated drawings for pages 3 and 4.
    """
    try:
        generator = ProfessionalDrawingGeneratorWithData()

        # Generate Page 3: Site Plan
        page3_path = generator.create_page3_site_plan(spatial_data)

        # Generate Page 4: Disposal Field & Cross-Section
        page4_path = generator.create_page4_disposal_and_section(spatial_data)

        return {
            'page3_path': page3_path,
            'page4_path': page4_path,
            'status': 'success'
        }
    except Exception as e:
        print(f"Error generating drawings: {e}")
        return {
            'page3_path': None,
            'page4_path': None,
            'status': 'error',
            'error': str(e)
        }
