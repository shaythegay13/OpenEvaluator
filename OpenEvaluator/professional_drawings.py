"""Professional HHE-200 Drawing Generator using ezdxf"""

import ezdxf
from typing import Dict, List, Optional
import math

class ProfessionalDrawingGenerator:
    def __init__(self):
        self.dwg = None
        self.msp = None
        self.LINE_WEIGHTS = {
            'grid': 0.13,
            'thin': 0.20,
            'medium': 0.25,
            'bold': 0.38,
        }

    def create_page3_site_plan(self, site_data: Dict):
        """Create professional Page 3: Site Plan"""
        self.dwg = ezdxf.new('R2010')
        self.msp = self.dwg.modelspace()
        
        page_width = 215.9
        page_height = 279.4
        margin = 12.7
        
        self._draw_fine_grid(margin, margin, page_width - 2*margin, page_height - 2*margin)
        
        plan_height = (page_height - 2*margin) * 0.65
        self._draw_site_plan_area(site_data, margin, margin, page_width - 2*margin, plan_height)
        
        soil_y = margin + plan_height + 5
        self._draw_soil_profile(site_data, margin, soil_y, 60, 60)
        
        locus_x = page_width - 2*margin - 50
        self._draw_locus_map(site_data, locus_x, margin + plan_height - 40, 50, 40)
        
        self._add_title_and_scale("SITE PLAN", "1\" = 100'", margin, page_height - margin - 5)
        
        return self.dwg

    def create_page4_disposal_and_section(self, system_data: Dict):
        """Create professional Page 4: Disposal Plan & Cross-Section"""
        self.dwg = ezdxf.new('R2010')
        self.msp = self.dwg.modelspace()
        
        page_width = 215.9
        page_height = 279.4
        margin = 12.7
        
        self._draw_fine_grid(margin, margin, page_width - 2*margin, page_height - 2*margin)
        
        plan_height = (page_height - 2*margin) * 0.48
        self._draw_disposal_plan(system_data, margin, margin + plan_height + 10, 
                                page_width - 2*margin, plan_height)
        
        self._draw_cross_section(system_data, margin, margin, 
                                page_width - 2*margin, plan_height - 5)
        
        self._add_title_and_scale("SUBSURFACE WASTEWATER DISPOSAL PLAN", "1\" = 50'", 
                                 margin, page_height - margin - 5)
        
        return self.dwg

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

    def _draw_site_plan_area(self, site_data: Dict, x: float, y: float,
                            width: float, height: float):
        """Draw the main site plan with property boundary and structures"""

        # Try to draw real property boundary if available, otherwise generic
        boundary_vertices = site_data.get('property_boundary_vertices', None)
        if boundary_vertices and len(boundary_vertices) > 2:
            self._draw_property_boundary_polygon(boundary_vertices, x, y, width, height)
        else:
            # Draw generic property boundary (main lot outline)
            self.msp.add_lwpolyline(
                [(x + 10, y + 10), (x + width - 10, y + 10),
                 (x + width - 10, y + height - 10), (x + 10, y + height - 10), (x + 10, y + 10)],
                dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['bold']}
            )

        # Add road name if available from property research
        road_name = site_data.get('road_name', '')
        road_type = site_data.get('road_type', 'Public')
        if road_name:
            road_text = f"ROAD: {road_name} ({road_type})"
            road_label = self.msp.add_text(road_text,
                                          dxfattribs={'height': 3.2, 'color': 1})
            road_label.dxf.insert = (x + 12, y + 8)

            # Draw road edge indicator line
            self.msp.add_line((x + 12, y + 6), (x + width - 12, y + 6),
                            dxfattribs={'color': 5, 'lineweight': self.LINE_WEIGHTS['medium'],
                                      'linetype': 'DASHED'})

        # Draw existing structures from property data if available
        structures_data = site_data.get('existing_structures', [])
        if structures_data:
            self._draw_property_structures(structures_data, x, y, width, height)
        else:
            # Fallback: draw generic structures for demo
            self._draw_generic_structures(x, y)

        self._draw_north_arrow(x + width - 20, y + height - 15)

    def _draw_property_structures(self, structures: List[Dict], x: float, y: float,
                                 width: float, height: float):
        """Draw actual property structures from researched data"""
        # Dwelling in upper-left area
        dwellings = [s for s in structures if s.get('type') == 'Dwelling']
        if dwellings:
            self._draw_hatched_rectangle(x + 15, y + 35, 18, 24,
                                        pattern='existing', label='DWELLING')

        # Garage offset from dwelling
        garages = [s for s in structures if s.get('type') == 'Garage']
        if garages:
            self._draw_hatched_rectangle(x + 40, y + 40, 12, 10,
                                        pattern='existing', label='GARAGE')

        # Shed or other structures
        sheds = [s for s in structures if s.get('type') in ('Shed', 'Outbuilding')]
        if sheds:
            self._draw_hatched_rectangle(x + 60, y + 45, 8, 8,
                                        pattern='existing', label='SHED')

        # Well location if researched (marked with circle)
        wells = [s for s in structures if s.get('type') == 'Well']
        if wells:
            well_x, well_y = x + 75, y + 50
            self.msp.add_circle((well_x, well_y), 2, dxfattribs={'color': 0})
            well_label = self.msp.add_text("WELL", dxfattribs={'height': 2, 'color': 0})
            well_label.dxf.insert = (well_x - 3, well_y - 3)

    def _draw_property_boundary_polygon(self, vertices: List[List[float]], x: float, y: float,
                                       width: float, height: float):
        """Draw property boundary from actual coordinates if available"""
        if not vertices or len(vertices) < 2:
            return

        # Find min/max to normalize vertices to drawing area
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)

        range_x = max_x - min_x or 1
        range_y = max_y - min_y or 1

        # Scale and translate vertices to fit in drawing area
        plan_width = width - 20
        plan_height = height - 20
        scale_x = plan_width / range_x
        scale_y = plan_height / range_y
        scale = min(scale_x, scale_y) * 0.9  # Leave margin

        scaled_vertices = []
        for v in vertices:
            norm_x = (v[0] - min_x) / range_x
            norm_y = (v[1] - min_y) / range_y
            draw_x = x + 10 + plan_width * norm_x
            draw_y = y + 10 + plan_height * norm_y
            scaled_vertices.append((draw_x, draw_y))

        # Close polygon
        if scaled_vertices[0] != scaled_vertices[-1]:
            scaled_vertices.append(scaled_vertices[0])

        # Draw boundary polygon with bold line
        self.msp.add_lwpolyline(
            scaled_vertices,
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['bold']}
        )

    def _draw_generic_structures(self, x: float, y: float):
        """Draw generic structures for demo purposes"""
        structures = [
            {"name": "DWELLING", "x": x + 20, "y": y + 30, "w": 15, "h": 20},
            {"name": "GARAGE", "x": x + 50, "y": y + 35, "w": 12, "h": 10},
        ]

        for struct in structures:
            self._draw_hatched_rectangle(struct["x"], struct["y"], struct["w"], struct["h"],
                                        pattern='existing', label=struct["name"])

    def _draw_soil_profile(self, site_data: Dict, x: float, y: float, 
                          width: float, height: float):
        """Draw soil profile section"""
        
        title = self.msp.add_text("SOIL PROFILE", dxfattribs={'height': 3, 'color': 0})
        title.dxf.insert = (x, y)
        
        hole_width = (width - 5) / 2
        
        self._draw_observation_hole(x, y - height + 10, hole_width, height - 10, 
                                   "Obs Hole A", site_data.get('soil_profile', []))
        
        self._draw_observation_hole(x + hole_width + 5, y - height + 10, hole_width, height - 10,
                                   "Obs Hole B", site_data.get('soil_profile', []))

    def _draw_observation_hole(self, x: float, y: float, width: float, height: float,
                              hole_label: str, soil_layers: List[Dict]):
        """Draw observation hole"""
        
        self.msp.add_lwpolyline(
            [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)],
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']}
        )
        
        depth_increment = height / 6
        for i in range(7):
            depth_ft = i * 8
            depth_y = y + (i * depth_increment)
            label = self.msp.add_text(str(depth_ft), dxfattribs={'height': 2, 'color': 0})
            label.dxf.insert = (x - 3, depth_y)
        
        if soil_layers:
            layer_height = height / len(soil_layers)
            for i, layer in enumerate(soil_layers):
                layer_y = y + (i * layer_height)
                layer_name = layer.get('type', 'UNKNOWN')
                
                self._draw_hatched_rectangle(x + 1, layer_y, width - 2, layer_height,
                                           pattern=layer_name.lower())
                
                label = self.msp.add_text(layer_name, dxfattribs={'height': 2, 'color': 0})
                label.dxf.insert = (x + width/2, layer_y + layer_height/2)
        
        label = self.msp.add_text(hole_label, dxfattribs={'height': 2.5, 'color': 0})
        label.dxf.insert = (x + width/2, y + height + 2)

    def _draw_disposal_plan(self, system_data: Dict, x: float, y: float,
                           width: float, height: float):
        """Draw disposal plan"""

        title = self.msp.add_text("DISPOSAL PLAN", dxfattribs={'height': 4, 'color': 0})
        title.dxf.insert = (x, y + height - 3)

        # Priority 2 Fix: Larger tank for better visibility
        tank_x = x + 10
        tank_y = y + height - 45
        tank_w = 25
        tank_h = 20

        self.msp.add_lwpolyline(
            [(tank_x, tank_y), (tank_x + tank_w, tank_y),
             (tank_x + tank_w, tank_y + tank_h), (tank_x, tank_y + tank_h), (tank_x, tank_y)],
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']}
        )

        for i in range(1, 3):
            baffle_x = tank_x + (i * tank_w / 3)
            self.msp.add_line((baffle_x, tank_y), (baffle_x, tank_y + tank_h),
                             dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin'],
                                        'linetype': 'DASHED'})

        label = self.msp.add_text("SEPTIC\nTANK", dxfattribs={'height': 2.8, 'color': 0})
        label.dxf.insert = (tank_x + tank_w/2, tank_y + tank_h/2)

        # Priority 2 Fix: Larger distributor
        dist_x = tank_x + tank_w + 10
        dist_y = tank_y + tank_h/2 - 5
        dist_w = 12
        dist_h = 10

        self.msp.add_lwpolyline(
            [(dist_x, dist_y), (dist_x + dist_w, dist_y),
             (dist_x + dist_w, dist_y + dist_h), (dist_x, dist_y + dist_h), (dist_x, dist_y)],
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']}
        )

        self.msp.add_line((tank_x + tank_w, tank_y + tank_h/2),
                         (dist_x, dist_y + dist_h/2),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']})

        # Priority 1 Fix: Larger field modules with wider layout
        modules_x = dist_x + dist_w + 10
        modules_y = tank_y
        module_size = 6
        cols, rows = 6, 3

        for row in range(rows):
            for col in range(cols):
                mx = modules_x + (col * module_size)
                my = modules_y + (row * module_size)
                self.msp.add_lwpolyline(
                    [(mx, my), (mx + module_size, my),
                     (mx + module_size, my + module_size), (mx, my + module_size), (mx, my)],
                    dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']}
                )

        label = self.msp.add_text("ELJEN\nMODULES", dxfattribs={'height': 2.2, 'color': 0})
        label.dxf.insert = (modules_x + (cols * module_size)/2,
                            modules_y + (rows * module_size)/2)

    def _draw_cross_section(self, system_data: Dict, x: float, y: float,
                           width: float, height: float):
        """Draw cross-section"""
        
        title = self.msp.add_text("CROSS-SECTION", dxfattribs={'height': 4, 'color': 0})
        title.dxf.insert = (x, y + height)
        
        grade_y = y + height - 30
        self.msp.add_line((x + 5, grade_y), (x + width - 5, grade_y),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['bold']})
        
        label = self.msp.add_text("EL 120'", dxfattribs={'height': 2, 'color': 0})
        label.dxf.insert = (x + 2, grade_y)
        
        soil_layers = system_data.get('soil_profile', [])
        if soil_layers:
            layer_height = (grade_y - y - 5) / len(soil_layers)
            for i, layer in enumerate(soil_layers):
                layer_y = grade_y - ((i + 1) * layer_height)
                layer_name = layer.get('type', 'UNKNOWN')
                
                self._draw_hatched_rectangle(x + 5, layer_y, width - 10, layer_height,
                                           pattern=layer_name.lower())
                
                label = self.msp.add_text(layer_name, dxfattribs={'height': 2, 'color': 0})
                label.dxf.insert = (x + width/2, layer_y + layer_height/2)
        
        tank_x = x + width - 40
        tank_y = grade_y - 15
        tank_w = 20
        tank_h = 10
        
        self.msp.add_lwpolyline(
            [(tank_x, tank_y), (tank_x + tank_w, tank_y),
             (tank_x + tank_w, tank_y + tank_h), (tank_x, tank_y + tank_h), (tank_x, tank_y)],
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']}
        )

    def _draw_hatched_rectangle(self, x: float, y: float, width: float, height: float,
                               pattern: str = 'default', label: Optional[str] = None):
        """Draw rectangle with hatching"""
        
        patterns_map = {
            'existing': 45, 'brown': 0, 'sand': 45, 'fine': 45,
            'silt': 0, 'peat': 45, 'loam': 45, 'gray': 0,
        }
        
        angle = patterns_map.get(pattern, 45)
        spacing = 0.3
        
        self.msp.add_lwpolyline(
            [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)],
            dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['thin']}
        )
        
        if angle == 0:
            for offset in [i * spacing for i in range(int(height / spacing) + 1)]:
                line_y = y + offset
                if line_y < y + height:
                    self.msp.add_line((x, line_y), (x + width, line_y),
                                    dxfattribs={'color': 0, 'lineweight': 0.07})
        else:
            extent = width + height
            for offset in [i * spacing for i in range(int(extent / spacing) + 1)]:
                x1 = x + offset
                y1 = y
                x2 = x1 - height
                y2 = y + height
                
                if x2 < x + width and x1 > x:
                    self.msp.add_line((max(x1, x), y), (min(x2 + width, x + width), y + height),
                                    dxfattribs={'color': 0, 'lineweight': 0.07})
        
        if label:
            label_text = self.msp.add_text(label, dxfattribs={'height': 2.5, 'color': 0})
            label_text.dxf.insert = (x + width/2, y + height/2)

    def _draw_locus_map(self, site_data: Dict, x: float, y: float, width: float, height: float):
        """Draw locus map"""
        self.msp.add_lwpolyline(
            [(x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y)],
            dxfattribs={'color': 8, 'lineweight': self.LINE_WEIGHTS['thin']}
        )
        label = self.msp.add_text("LOCUS", dxfattribs={'height': 2, 'color': 0})
        label.dxf.insert = (x + width/2, y + height/2)

    def _draw_north_arrow(self, x: float, y: float):
        """Draw north arrow"""
        size = 3
        self.msp.add_line((x, y), (x, y + size),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
        self.msp.add_line((x, y + size), (x - size/3, y + size/2),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
        self.msp.add_line((x, y + size), (x + size/3, y + size/2),
                         dxfattribs={'color': 0, 'lineweight': self.LINE_WEIGHTS['medium']})
        label = self.msp.add_text("N", dxfattribs={'height': 1.5, 'color': 0})
        label.dxf.insert = (x, y + size + 1)

    def _add_title_and_scale(self, title: str, scale: str, x: float, y: float):
        """Add title and scale"""
        title_text = self.msp.add_text(title, dxfattribs={'height': 3.5, 'color': 0})
        title_text.dxf.insert = (x, y)
        
        scale_text = self.msp.add_text(f"Scale: {scale}", dxfattribs={'height': 2, 'color': 0})
        scale_text.dxf.insert = (x, y - 4)

    def save(self, filename: str):
        """Save drawing"""
        if self.dwg:
            self.dwg.saveas(filename)
            print(f"✅ Saved: {filename}")

if __name__ == "__main__":
    site_data = {
        'soil_profile': [
            {'type': 'BROWN', 'depth_start': 0, 'depth_end': 8},
            {'type': 'FINE', 'depth_start': 8, 'depth_end': 16},
            {'type': 'SAND', 'depth_start': 16, 'depth_end': 24},
            {'type': 'LOAM', 'depth_start': 24, 'depth_end': 32},
            {'type': 'GRAY', 'depth_start': 32, 'depth_end': 48},
        ]
    }
    
    gen = ProfessionalDrawingGenerator()
    dwg3 = gen.create_page3_site_plan(site_data)
    gen.save('page3_professional.dxf')
    
    gen = ProfessionalDrawingGenerator()
    dwg4 = gen.create_page4_disposal_and_section(site_data)
    gen.save('page4_professional.dxf')
    
    print("✅ All professional drawings generated!")
