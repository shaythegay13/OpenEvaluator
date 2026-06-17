#!/usr/bin/env python3
"""
HHE-200 Drawing Generator for Maine Subsurface Wastewater Disposal Permits

This script generates AutoCAD-compatible drawings (DWG) for the HHE-200
Subsurface Wastewater Disposal System Permit Application using ezDXF.

Usage:
    python generate_drawing.py --config config.yaml --output drawing.dwg
    python generate_drawing.py --site-plan data.yaml site_plan.dwg
    python generate_drawing.py --soil-profile data.yaml soil_profile.dwg
    python generate_drawing.py --disposal-plan data.yaml disposal_plan.dwg
    python generate_drawing.py --cross-section data.yaml cross_section.dwg

Input data format (YAML):
    owner:
      name: "John Smith"
      address: "123 Main Street"
      city: "Auburn"
      state: "ME"
      zip: "04210"

    property:
      tax_map: "Map 12"
      lot: "Lot 45"
      boundaries: [[x1, y1], [x2, y2], ...]  # in feet

    observation_holes:
      - id: "OH-1"
        coordinates: [x, y]  # GPS coordinates
        ground_surface_elev: 245.2
        depth_to_refusal: 48
        test_pit: true
        organic_horizon: 4
        soil_data:
          - depth: 0
            texture: "Org"
            consistence: "Lse"
            color: "2.5Y"
            redox: ""
          - depth: 6
            texture: "Snd"
            consistence: "Lse"
            color: "10YR 5/3"
            redox: ""
          ... (continues at 6" intervals to 48")
        classification: "Chatfield Silt Loam"
        slope: 3
        limiting_factor: "restrictive_layer"
        profile_condition: "Good"

    disposal_system:
      tank:
        location: [x, y]
        type: "concrete"
        capacity: 1500
        invert_elev: 243.2
      distribution_box:
        location: [x, y]
        invert_elev: 242.8
      leaching_area:
        location: [x, y]
        dimensions: [width, length]
        bottom_elev: 241.5
        type: "stone_trench"
      backfill_upslope: 18
      backfill_downslope: 24

    elevation_reference:
      location: [x, y]
      description: "Iron rebar at NW corner of tank"
      reference_elev: 0.0
      actual_elev: 245.50

    scale: "1\" = 30'"
    north_type: "True"
"""

import argparse
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

try:
    import ezdxf
    from ezdxf.document import Drawing
    from ezdxf.enums import TextEntityAlignment
    from ezdxf import const
except ImportError:
    print("Error: ezdxf is required. Install with: pip install ezdxf")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(1)


# =============================================================================
# LAYER DEFINITIONS
# =============================================================================

@dataclass
class LayerDef:
    """Layer definition with AutoCAD properties."""
    name: str
    color: int  # ACI color number
    linetype: str = "CONTINUOUS"
    lineweight: float = 0.25

# Standard AutoCAD Color Index (ACI)
ACI_WHITE = 7
ACI_YELLOW = 2
ACI_MAGENTA = 6
ACI_RED = 1
ACI_GREEN = 3
ACI_CYAN = 4
ACI_BLUE = 5
ACI_BROWN = 8
ACI_GRAY = 9

LAYERS = {
    # Core layers
    "0": LayerDef("0", ACI_WHITE, "CONTINUOUS", 0.25),
    
    # Walls/Structures
    "WALLS": LayerDef("WALLS", ACI_WHITE, "CONTINUOUS", 0.50),
    "WALLS-EXIST": LayerDef("WALLS-EXIST", ACI_WHITE, "CONTINUOUS", 0.50),
    "WALLS-PROPOSED": LayerDef("WALLS-PROPOSED", ACI_CYAN, "CONTINUOUS", 0.50),
    
    # Property
    "PROPERTY": LayerDef("PROPERTY", ACI_YELLOW, "CONTINUOUS", 0.70),
    "PROPERTY-EASEMENT": LayerDef("PROPERTY-EASEMENT", ACI_YELLOW, "DASHDOT", 0.50),
    
    # Dimensions
    "DIMENSIONS": LayerDef("DIMENSIONS", ACI_CYAN, "CONTINUOUS", 0.25),
    "DIM-LINEAR": LayerDef("DIM-LINEAR", ACI_CYAN, "CONTINUOUS", 0.25),
    
    # Text
    "TEXT": LayerDef("TEXT", ACI_WHITE, "CONTINUOUS", 0.0),
    "TEXT-ANNO": LayerDef("TEXT-ANNO", ACI_WHITE, "CONTINUOUS", 0.0),
    "TEXT-LABEL": LayerDef("TEXT-LABEL", ACI_WHITE, "CONTINUOUS", 0.0),
    "TEXT-TITLE": LayerDef("TEXT-TITLE", ACI_WHITE, "CONTINUOUS", 0.0),
    "TEXT-ELEV": LayerDef("TEXT-ELEV", ACI_CYAN, "CONTINUOUS", 0.0),
    
    # Site Plan
    "SITE_PLAN": LayerDef("SITE_PLAN", ACI_YELLOW, "CONTINUOUS", 0.35),
    "FEATURES-ROAD": LayerDef("FEATURES-ROAD", ACI_YELLOW, "CONTINUOUS", 0.35),
    "FEATURES-WELL": LayerDef("FEATURES-WELL", ACI_BLUE, "CONTINUOUS", 0.35),
    "FEATURES-STRUCTURE": LayerDef("FEATURES-STRUCTURE", ACI_WHITE, "CONTINUOUS", 0.35),
    
    # Observation Holes
    "OBSERVATION": LayerDef("OBSERVATION", ACI_GREEN, "CONTINUOUS", 0.35),
    "OH-MARKER": LayerDef("OH-MARKER", ACI_GREEN, "CONTINUOUS", 0.35),
    "OH-LABEL": LayerDef("OH-LABEL", ACI_GREEN, "CONTINUOUS", 0.0),
    
    # Soil Profile
    "SOIL_PROFILE": LayerDef("SOIL_PROFILE", ACI_BROWN, "CONTINUOUS", 0.25),
    "SP-HEADER": LayerDef("SP-HEADER", ACI_BROWN, "CONTINUOUS", 0.50),
    "SP-GRID": LayerDef("SP-GRID", ACI_BROWN, "CONTINUOUS", 0.13),
    "SP-LAYER": LayerDef("SP-LAYER", ACI_BROWN, "CONTINUOUS", 0.35),
    "SP-LABEL": LayerDef("SP-LABEL", ACI_BROWN, "CONTINUOUS", 0.0),
    "SP-REDOX": LayerDef("SP-REDOX", ACI_RED, "CONTINUOUS", 0.25),
    
    # Disposal System
    "DISPOSAL_SYS": LayerDef("DISPOSAL_SYS", ACI_MAGENTA, "CONTINUOUS", 0.50),
    "DS-TANK": LayerDef("DS-TANK", ACI_MAGENTA, "CONTINUOUS", 0.50),
    "DS-DBOX": LayerDef("DS-DBOX", ACI_MAGENTA, "CONTINUOUS", 0.50),
    "DS-LEACH": LayerDef("DS-LEACH", ACI_MAGENTA, "CONTINUOUS", 0.50),
    "DS-PIPE": LayerDef("DS-PIPE", ACI_MAGENTA, "CONTINUOUS", 0.35),
    
    # Cross-Section
    "CROSS_SECTION": LayerDef("CROSS_SECTION", ACI_RED, "CONTINUOUS", 0.50),
    "XS-GRADE-EXIST": LayerDef("XS-GRADE-EXIST", ACI_RED, "CONTINUOUS", 0.50),
    "XS-GRADE-FIN": LayerDef("XS-GRADE-FIN", ACI_CYAN, "CONTINUOUS", 0.50),
    "XS-SYSTEM": LayerDef("XS-SYSTEM", ACI_MAGENTA, "CONTINUOUS", 0.50),
    
    # Elevations
    "ELEVATIONS": LayerDef("ELEVATIONS", ACI_CYAN, "CONTINUOUS", 0.35),
    "EL-MARKER": LayerDef("EL-MARKER", ACI_CYAN, "CONTINUOUS", 0.35),
    "EL-CALLOUT": LayerDef("EL-CALLOUT", ACI_CYAN, "CONTINUOUS", 0.0),
    "EL-REFERENCE": LayerDef("EL-REFERENCE", ACI_RED, "CONTINUOUS", 0.50),
    
    # Setbacks
    "SETBACKS": LayerDef("SETBACKS", ACI_YELLOW, "CONTINUOUS", 0.35),
    "SB-LINE": LayerDef("SB-LINE", ACI_YELLOW, "CONTINUOUS", 0.35),
    "SB-DIM": LayerDef("SB-DIM", ACI_YELLOW, "CONTINUOUS", 0.25),
    
    # Hatching
    "HATCH": LayerDef("HATCH", ACI_BROWN, "SOLID", 0.0),
    "HATCH-SOIL": LayerDef("HATCH-SOIL", ACI_BROWN, "ANSI31", 0.0),
    "HATCH-STONE": LayerDef("HATCH-STONE", ACI_GRAY, "ANSI37", 0.0),
    "HATCH-ROCK": LayerDef("HATCH-ROCK", ACI_RED, "ROCK", 0.0),
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SoilInterval:
    """Soil data for a single depth interval."""
    depth: int  # 0, 6, 12, 18, 24, 30, 36, 42, 48
    texture: str
    consistence: str
    color: str
    redox: str = ""


@dataclass
class ObservationHole:
    """Observation hole data."""
    id: str
    coordinates: Tuple[float, float]
    ground_surface_elev: float
    depth_to_refusal: int
    test_pit: bool = True
    organic_horizon: float = 0
    soil_data: List[SoilInterval] = field(default_factory=list)
    classification: str = ""
    slope: float = 0
    limiting_factor: str = ""  # "groundwater", "restrictive_layer", "bedrock"
    profile_condition: str = ""


@dataclass
class Tank:
    """Septic tank data."""
    location: Tuple[float, float]
    type: str = "concrete"
    capacity: int = 1500
    invert_elev: float = 0
    dimensions: Tuple[float, float] = (5, 10)  # width, length


@dataclass
class DistributionBox:
    """Distribution box data."""
    location: Tuple[float, float]
    invert_elev: float = 0


@dataclass
class LeachingArea:
    """Leaching area data."""
    location: Tuple[float, float]
    dimensions: Tuple[float, float] = (20, 30)
    bottom_elev: float = 0
    type: str = "stone_trench"


@dataclass
class DisposalSystem:
    """Complete disposal system data."""
    tank: Tank = field(default_factory=Tank)
    distribution_box: DistributionBox = field(default_factory=DistributionBox)
    leaching_area: LeachingArea = field(default_factory=LeachingArea)
    backfill_upslope: float = 0
    backfill_downslope: float = 0


@dataclass
class ElevationReference:
    """Elevation reference point data."""
    location: Tuple[float, float]
    description: str = ""
    reference_elev: float = 0.0
    actual_elev: float = 0.0


@dataclass
class SiteData:
    """Complete site data for drawing generation."""
    owner_name: str = ""
    owner_address: str = ""
    property_tax_map: str = ""
    property_lot: str = ""
    property_boundaries: List[Tuple[float, float]] = field(default_factory=list)
    observation_holes: List[ObservationHole] = field(default_factory=list)
    disposal_system: DisposalSystem = field(default_factory=DisposalSystem)
    elevation_reference: ElevationReference = field(default_factory=ElevationReference)
    scale: str = '1" = 30\''
    north_type: str = "True"


# =============================================================================
# DRAWING GENERATOR
# =============================================================================

class DrawingGenerator:
    """Generates HHE-200 compliant AutoCAD drawings."""
    
    def __init__(self, site_data: SiteData):
        self.site_data = site_data
        self.doc: Optional[Drawing] = None
        self.modelspace = None
        self._setup_linetypes()
    
    def _setup_linetypes(self):
        """Register custom linetypes."""
        # Note: In ezDXF, linetypes are defined in the document's linetype table
        pass
    
    def create_drawing(self) -> Drawing:
        """Create a new AutoCAD drawing."""
        self.doc = ezdxf.new('R2013')  # AutoCAD 2013 format
        self.doc.header.setup_unit_settings(
           insunits=1  # Feet
        )
        
        # Setup dimension styles
        self._setup_dimension_styles()
        
        # Create layers
        self._create_layers()
        
        # Get modelspace
        self.modelspace = self.doc.modelspace()
        
        return self.doc
    
    def _setup_dimension_styles(self):
        """Setup HHE-200 compliant dimension styles."""
        if self.doc is None:
            return
        
        dim_style = self.doc.dimstyles.new("HHE200")
        dim_style.dimsz = 0.08  # Arrow and text size
        dim_style.dtxt = 0.08  # Text height
        dim_style.dgap = 0.0625  # Extension line offset
        dim_style.dle = 0.0625  # Extension line extension
        dim_style.dunit = const.METRIC  # Use decimal for feet
        dim_style.dimadec = 0  # No decimal places
        dim_style.dimzin = 0  # Suppress leading zeros
    
    def _create_layers(self):
        """Create all required layers in the drawing."""
        if self.doc is None:
            return
        
        for layer_key, layer_def in LAYERS.items():
            if layer_key != "0":  # Skip default layer
                try:
                    self.doc.layers.add(
                        name=layer_def.name,
                        color=layer_def.color,
                        linetype=layer_def.linetype,
                        lineweight=layer_def.lineweight
                    )
                except Exception:
                    pass  # Layer may already exist
    
    def set_layer(self, layer_name: str):
        """Set the current layer for subsequent entities."""
        if self.modelspace is not None:
            self.modelspace.layer = layer_name
    
    def add_text(self, text: str, location: Tuple[float, float], 
                 height: float = 0.08, layer: str = "TEXT",
                 alignment: str = "LEFT") -> None:
        """Add text to the drawing.
        
        SITE_EVALUATOR DATA INJECTION POINT:
            Replace 'text' parameter with site_data.observation_holes[i].id
            or other field values from the SiteData object.
        """
        if self.modelspace is None:
            return
        
        self.modelspace.add_text(
            text,
            dxfattribs={
                'layer': layer,
                'height': height
            }
        ).set_placement(location, align=TextEntityAlignment[alignment])
    
    def add_mtext(self, text: str, location: Tuple[float, float],
                  width: float = 2.0, height: float = 0.08,
                  layer: str = "TEXT") -> None:
        """Add multi-line text to the drawing."""
        if self.modelspace is None:
            return
        
        mtext = self.modelspace.add_mtext(
            text,
            dxfattribs={'layer': layer}
        )
        mtext.set_location(location, relative_base=True)
    
    def add_circle(self, center: Tuple[float, float], radius: float,
                   layer: str = "OH-MARKER") -> None:
        """Add a circle to the drawing."""
        if self.modelspace is None:
            return
        
        self.modelspace.add_circle(
            center,
            radius,
            dxfattribs={'layer': layer}
        )
    
    def add_rectangle(self, corner: Tuple[float, float],
                      width: float, height: float,
                      layer: str = "WALLS") -> None:
        """Add a rectangle (polyline) to the drawing."""
        if self.modelspace is None:
            return
        
        points = [
            corner,
            (corner[0] + width, corner[1]),
            (corner[0] + width, corner[1] + height),
            (corner[0], corner[1] + height),
            corner
        ]
        
        self.modelspace.add_lwpolyline(
            points,
            close=True,
            dxfattribs={'layer': layer}
        )
    
    def add_polyline(self, points: List[Tuple[float, float]],
                     layer: str = "PROPERTY", close: bool = False) -> None:
        """Add a polyline to the drawing.
        
        SITE_EVALUATOR DATA INJECTION POINT:
            Points should come from site_data.property_boundaries
        """
        if self.modelspace is None:
            return
        
        self.modelspace.add_lwpolyline(
            points,
            close=close,
            dxfattribs={'layer': layer}
        )
    
    def add_line(self, start: Tuple[float, float], 
                 end: Tuple[float, float],
                 layer: str = "DS-PIPE") -> None:
        """Add a line to the drawing."""
        if self.modelspace is None:
            return
        
        self.modelspace.add_line(
            start,
            end,
            dxfattribs={'layer': layer}
        )
    
    def add_leader(self, points: List[Tuple[float, float]],
                   text: str, layer: str = "EL-CALLOUT") -> None:
        """Add a leader with text annotation.
        
        SITE_EVALUATOR DATA INJECTION POINT:
            Text should come from site_data.elevation_reference fields
            or disposal_system component elevations.
        """
        if self.modelspace is None:
            return
        
        # Add leader line
        self.modelspace.add_leader(
            points,
            dxfattribs={'layer': layer}
        )
        
        # Add text at end of leader
        if points:
            self.add_text(text, points[-1], height=0.08, layer=layer)
    
    def add_dimension_linear(self, start: Tuple[float, float],
                             end: Tuple[float, float],
                             offset: float = 0.5,
                             layer: str = "DIMENSIONS") -> None:
        """Add a linear dimension."""
        if self.modelspace is None:
            return
        
        self.modelspace.add_linear_dim(
            base=(0, 0),
            p1=start,
            p2=end,
            offset=offset,
            dimstyle="HHE200",
            dxfattribs={'layer': layer}
        )


# =============================================================================
# SITE PLAN GENERATION
# =============================================================================

def generate_site_plan(generator: DrawingGenerator, site_data: SiteData) -> None:
    """Generate the site plan drawing (HHE-200 Page 3 attachment).
    
    SITE_EVALUATOR DATA INJECTION POINTS:
    - site_data.property_boundaries -> property boundary polyline
    - site_data.observation_holes[i].coordinates -> OH marker locations
    - site_data.observation_holes[i].id -> OH labels (OH-1, OH-2)
    - site_data.disposal_system -> disposal area boundary
    - site_data.elevation_reference -> ERP location
    """
    
    if generator.modelspace is None:
        return
    
    # Add title block
    generator.add_text(
        "HHE-200 SITE PLAN",
        (0.5, 10.5),
        height=0.125,
        layer="TEXT-TITLE"
    )
    generator.add_text(
        f"Owner: {site_data.owner_name}",
        (0.5, 10.2),
        height=0.08,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Address: {site_data.owner_address}",
        (0.5, 10.0),
        height=0.08,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Scale: {site_data.scale}",
        (7.0, 10.5),
        height=0.08,
        layer="TEXT-LABEL"
    )
    
    # Add north arrow
    generator.add_text(
        "N",
        (4.25, 9.5),
        height=0.15,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"({site_data.north_type})",
        (4.25, 9.3),
        height=0.06,
        layer="TEXT-LABEL"
    )
    
    # Draw property boundary
    # SITE_EVALUATOR DATA INJECTION POINT: 
    # Replace with: site_data.property_boundaries
    sample_boundary = [
        (1, 1), (8, 1), (8, 8), (5, 9), (1, 8), (1, 1)
    ]
    generator.add_polyline(sample_boundary, layer="PROPERTY", close=True)
    
    # Draw structures (sample house)
    # SITE_EVALUATOR DATA INJECTION POINT:
    # Replace with actual structure data from site survey
    generator.add_rectangle((2, 6), 3, 2, layer="WALLS-EXIST")
    generator.add_text("HOUSE", (3.5, 7.2), height=0.06, layer="TEXT-LABEL")
    
    # Draw observation holes
    # SITE_EVALUATOR DATA INJECTION POINT:
    # Replace with loop over site_data.observation_holes
    for i, oh in enumerate(site_data.observation_holes):
        generator.add_circle(oh.coordinates, 0.15, layer="OH-MARKER")
        generator.add_text(
            oh.id,
            (oh.coordinates[0] - 0.1, oh.coordinates[1] - 0.2),
            height=0.08,
            layer="OH-LABEL"
        )
        # Add elevation annotation
        generator.add_text(
            f"Elev: {oh.ground_surface_elev}'",
            (oh.coordinates[0] - 0.3, oh.coordinates[1] - 0.35),
            height=0.06,
            layer="TEXT-ELEV"
        )
    
    # Draw disposal area boundary (sample)
    # SITE_EVALUATOR DATA INJECTION POINT:
    # Replace with disposal system boundary from site_data.disposal_system
    generator.add_rectangle((5, 2), 2.5, 3, layer="DS-LEACH")
    generator.add_text("DISPOSAL AREA", (5.5, 2.3), height=0.06, layer="TEXT-LABEL")
    
    # Draw reserve area (dashed)
    generator.add_rectangle((5, 0.5), 3, 1.3, layer="DS-LEACH")
    generator.add_text("RESERVE AREA", (5.25, 1.0), height=0.06, layer="TEXT-LABEL")
    
    # Add setback dimensions
    # SITE_EVALUATOR DATA INJECTION POINT:
    # Calculate actual setback distances from site_data
    generator.add_dimension_linear((1, 8), (1, 5.5), offset=0.3, layer="DIM-LINEAR")
    generator.add_text("Setback to Property Line", (0.2, 6.5), height=0.05, layer="TEXT-ANNO")
    
    # Add elevation reference point
    if site_data.elevation_reference.location:
        generator.add_circle(site_data.elevation_reference.location, 0.1, layer="EL-REFERENCE")
        generator.add_text(
            f"ERP: {site_data.elevation_reference.reference_elev}",
            (site_data.elevation_reference.location[0] + 0.15,
             site_data.elevation_reference.location[1]),
            height=0.06,
            layer="EL-CALLOUT"
        )


# =============================================================================
# SOIL PROFILE LOG GENERATION
# =============================================================================

def generate_soil_profile(generator: DrawingGenerator, site_data: SiteData) -> None:
    """Generate the soil profile log drawing (HHE-200 Page 3 attachment).
    
    SITE_EVALUATOR DATA INJECTION POINTS:
    - site_data.observation_holes[i].id -> Observation Hole number
    - site_data.observation_holes[i].organic_horizon -> Organic Horizon Thickness
    - site_data.observation_holes[i].ground_surface_elev -> Ground Surface Elevation
    - site_data.observation_holes[i].test_pit -> Test Pit or Boring checkbox
    - site_data.observation_holes[i].depth_to_refusal -> Depth to Exploration or Refusal
    - site_data.observation_holes[i].soil_data -> Texture, Consistence, Color, Redox per interval
    - site_data.observation_holes[i].classification -> Soil Classification
    - site_data.observation_holes[i].slope -> Slope percentage
    - site_data.observation_holes[i].limiting_factor -> Limiting Factor checkboxes
    - site_data.observation_holes[i].profile_condition -> Profile Condition notes
    """
    
    if generator.modelspace is None:
        return
    
    # Drawing parameters
    col_width = 3.0
    row_height = 0.3
    start_x = 0.5
    start_y = 8.0
    header_height = 0.5
    
    for col_idx, oh in enumerate(site_data.observation_holes[:2]):  # Max 2 OH per page
        col_x = start_x + (col_idx * (col_width + 0.5))
        
        # Draw header
        header_text = f"OBSERVATION HOLE #{oh.id}"
        generator.add_text(
            header_text,
            (col_x + col_width/2, start_y),
            height=0.1,
            layer="SP-HEADER"
        )
        
        # Add sub-header info
        # SITE_EVALUATOR DATA INJECTION POINT:
        generator.add_text(
            f"Organic Horz Thickness: {oh.organic_horizon}\"",
            (col_x, start_y - 0.2),
            height=0.06,
            layer="SP-LABEL"
        )
        generator.add_text(
            f"Ground Surf Elev: {oh.ground_surface_elev}'",
            (col_x, start_y - 0.35),
            height=0.06,
            layer="SP-LABEL"
        )
        generator.add_text(
            f"Test Pit [{'X' if oh.test_pit else ' '}]  Boring [{'X' if not oh.test_pit else ' '}]",
            (col_x, start_y - 0.5),
            height=0.06,
            layer="SP-LABEL"
        )
        generator.add_text(
            f"Depth to Refusal: {oh.depth_to_refusal}\"",
            (col_x, start_y - 0.65),
            height=0.06,
            layer="SP-LABEL"
        )
        
        # Draw grid
        grid_y = start_y - 1.0
        generator.add_line(
            (col_x, grid_y),
            (col_x + col_width, grid_y),
            layer="SP-GRID"
        )
        
        # Column headers
        col_headers = ["Depth", "Texture", "Consist", "Color", "Redox"]
        col_widths = [0.5, 0.7, 0.7, 0.8, 0.3]
        curr_x = col_x
        for i, header in enumerate(col_headers):
            generator.add_text(
                header,
                (curr_x + col_widths[i]/2, grid_y - 0.15),
                height=0.05,
                layer="SP-HEADER"
            )
            curr_x += col_widths[i]
        
        # Draw depth rows
        # SITE_EVALUATOR DATA INJECTION POINT:
        # Replace with loop over oh.soil_data
        depths = [0, 6, 12, 18, 24, 30, 36, 42, 48]
        for row_idx, depth in enumerate(depths):
            row_y = grid_y - 0.25 - (row_idx * row_height)
            
            # Find soil data for this depth
            soil_interval = None
            for sd in oh.soil_data:
                if sd.depth == depth:
                    soil_interval = sd
                    break
            
            curr_x = col_x
            
            # Depth
            generator.add_text(
                str(depth),
                (curr_x + 0.25, row_y),
                height=0.05,
                layer="SP-LABEL"
            )
            curr_x += col_widths[0]
            
            # Texture
            texture = soil_interval.texture if soil_interval else ""
            generator.add_text(
                texture,
                (curr_x + col_widths[1]/2, row_y),
                height=0.05,
                layer="SP-LABEL"
            )
            curr_x += col_widths[1]
            
            # Consistence
            consistence = soil_interval.consistence if soil_interval else ""
            generator.add_text(
                consistence,
                (curr_x + col_widths[2]/2, row_y),
                height=0.05,
                layer="SP-LABEL"
            )
            curr_x += col_widths[2]
            
            # Color
            color = soil_interval.color if soil_interval else ""
            generator.add_text(
                color,
                (curr_x + col_widths[3]/2, row_y),
                height=0.05,
                layer="SP-LABEL"
            )
            curr_x += col_widths[3]
            
            # Redox
            redox = soil_interval.redox if soil_interval else ""
            generator.add_text(
                redox,
                (curr_x + col_widths[4]/2, row_y),
                height=0.05,
                layer="SP-REDOX"
            )
            
            # Draw horizontal grid line
            generator.add_line(
                (col_x, row_y - 0.08),
                (col_x + col_width, row_y - 0.08),
                layer="SP-GRID"
            )
        
        # Summary section
        summary_y = grid_y - 0.25 - (len(depths) * row_height) - 0.3
        
        # Soil Classification
        generator.add_text(
            f"Soil Class: {oh.classification}",
            (col_x, summary_y),
            height=0.06,
            layer="SP-LABEL"
        )
        
        # Slope and Limiting Factor
        limiting = oh.limiting_factor.replace("_", " ").title()
        generator.add_text(
            f"Slope: {oh.slope}%  Lim Factor: [ ]GW [X]RL [ ]BD",
            (col_x, summary_y - 0.2),
            height=0.06,
            layer="SP-LABEL"
        )
        
        # Profile Condition
        generator.add_text(
            f"Profile Condition: {oh.profile_condition}",
            (col_x, summary_y - 0.4),
            height=0.06,
            layer="SP-LABEL"
        )


# =============================================================================
# DISPOSAL SYSTEM PLAN GENERATION
# =============================================================================

def generate_disposal_plan(generator: DrawingGenerator, site_data: SiteData) -> None:
    """Generate the disposal system plan drawing (HHE-200 Page 4 attachment).
    
    SITE_EVALUATOR DATA INJECTION POINTS:
    - site_data.disposal_system.tank -> Tank location, type, capacity, invert_elev
    - site_data.disposal_system.distribution_box -> D-box location, invert_elev
    - site_data.disposal_system.leaching_area -> Leaching area location, dimensions, bottom_elev
    - site_data.disposal_system.backfill_upslope/downslope -> Backfill depths
    - site_data.elevation_reference -> ERP location, description, reference_elev
    """
    
    if generator.modelspace is None:
        return
    
    # Add title
    generator.add_text(
        "HHE-200 DISPOSAL SYSTEM PLAN",
        (0.5, 10.5),
        height=0.125,
        layer="TEXT-TITLE"
    )
    generator.add_text(
        f"Owner: {site_data.owner_name}",
        (0.5, 10.2),
        height=0.08,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Scale: {site_data.scale}",
        (7.0, 10.5),
        height=0.08,
        layer="TEXT-LABEL"
    )
    
    # Elevation Reference Point
    # SITE_EVALUATOR DATA INJECTION POINT:
    erp = site_data.elevation_reference
    generator.add_text(
        f"ERP: {erp.description}",
        (0.5, 9.8),
        height=0.06,
        layer="EL-CALLOUT"
    )
    generator.add_text(
        f"Reference Elev: {erp.reference_elev} = {erp.actual_elev}'",
        (0.5, 9.6),
        height=0.06,
        layer="EL-CALLOUT"
    )
    generator.add_circle(erp.location, 0.1, layer="EL-REFERENCE")
    
    # Draw septic tank
    # SITE_EVALUATOR DATA INJECTION POINT:
    tank = site_data.disposal_system.tank
    tank_w, tank_l = tank.dimensions
    generator.add_rectangle(
        tank.location,
        tank_w,
        tank_l,
        layer="DS-TANK"
    )
    generator.add_text(
        f"ST\n{tank.capacity} gal",
        (tank.location[0] + tank_w/2, tank.location[1] + tank_l/2),
        height=0.08,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Top of Pipe: {tank.invert_elev}'",
        (tank.location[0], tank.location[1] - 0.2),
        height=0.05,
        layer="EL-CALLOUT"
    )
    
    # Draw distribution box
    dbox = site_data.disposal_system.distribution_box
    generator.add_rectangle(
        dbox.location,
        1.5,  # D-box size
        1.5,
        layer="DS-DBOX"
    )
    generator.add_text(
        "D-BOX",
        (dbox.location[0] + 0.75, dbox.location[1] + 0.75),
        height=0.06,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Invert: {dbox.invert_elev}'",
        (dbox.location[0], dbox.location[1] - 0.2),
        height=0.05,
        layer="EL-CALLOUT"
    )
    
    # Connect tank to D-box
    tank_center = (
        tank.location[0] + tank_w/2,
        tank.location[1] + tank_l/2
    )
    generator.add_line(
        (tank.location[0] + tank_w, tank_center[1]),
        (dbox.location[0], dbox.location[1] + 0.75),
        layer="DS-PIPE"
    )
    
    # Draw leaching area
    leach = site_data.disposal_system.leaching_area
    generator.add_rectangle(
        leach.location,
        leach.dimensions[0],
        leach.dimensions[1],
        layer="DS-LEACH"
    )
    generator.add_text(
        "LEACHING BED",
        (leach.location[0] + leach.dimensions[0]/2, 
         leach.location[1] + leach.dimensions[1]/2),
        height=0.08,
        layer="TEXT-LABEL"
    )
    generator.add_text(
        f"Bottom Elev: {leach.bottom_elev}'",
        (leach.location[0], leach.location[1] - 0.2),
        height=0.05,
        layer="EL-CALLOUT"
    )
    
    # Connect D-box to leaching area
    generator.add_line(
        (dbox.location[0] + 0.75, dbox.location[1]),
        (leach.location[0] + leach.dimensions[0]/2, leach.location[1] + leach.dimensions[1]),
        layer="DS-PIPE"
    )
    
    # Backfill information
    bs = site_data.disposal_system
    generator.add_text(
        f"BACKFILL: Upslope {bs.backfill_upslope}\" / Downslope {bs.backfill_downslope}\"",
        (0.5, 0.5),
        height=0.08,
        layer="TEXT-LABEL"
    )


# =============================================================================
# CROSS-SECTION GENERATION
# =============================================================================

def generate_cross_section(generator: DrawingGenerator, site_data: SiteData) -> None:
    """Generate the disposal area cross-section drawing (HHE-200 Page 4 attachment).
    
    SITE_EVALUATOR DATA INJECTION POINTS:
    - site_data.disposal_system.leaching_area.bottom_elev -> Bottom of disposal field
    - site_data.disposal_system.tank.invert_elev -> Top of distribution pipe
    - site_data.disposal_system.backfill_upslope/downslope -> Backfill depths
    - site_data.elevation_reference.reference_elev -> Reference elevation
    - site_data.elevation_reference.actual_elev -> Actual elevation of reference
    """
    
    if generator.modelspace is None:
        return
    
    # Add title
    generator.add_text(
        "DISPOSAL AREA CROSS-SECTION",
        (0.5, 10.5),
        height=0.125,
        layer="TEXT-TITLE"
    )
    generator.add_text(
        f"Reference Elev: {site_data.elevation_reference.reference_elev} = {site_data.elevation_reference.actual_elev}'",
        (0.5, 10.2),
        height=0.08,
        layer="EL-CALLOUT"
    )
    
    # Cross-section parameters
    horizontal_scale = 1  # 1 unit = 1 foot (same as site plan)
    vertical_scale = 5    # 1 unit = 5 feet
    section_start_x = 1.0
    section_y = 5.0
    section_length = 40  # feet
    
    # Calculate elevations
    ref_elev = site_data.elevation_reference.reference_elev
    actual_ref = site_data.elevation_reference.actual_elev
    
    # Convert elevations to drawing coordinates (assuming vertical scale 1" = 5')
    elev_to_y = lambda e: section_y - ((actual_ref - e) / 5) * vertical_scale
    
    # Draw existing grade line
    exist_grade_points = [
        (section_start_x, elev_to_y(actual_ref)),  # Start at reference
        (section_start_x + section_length, elev_to_y(actual_ref - 2))  # Slight slope
    ]
    generator.add_line(
        exist_grade_points[0],
        exist_grade_points[1],
        layer="XS-GRADE-EXIST"
    )
    generator.add_text(
        "EXISTING GRADE",
        (section_start_x + 0.1, elev_to_y(actual_ref) + 0.1),
        height=0.05,
        layer="TEXT-LABEL"
    )
    
    # Calculate finished grade (after backfill)
    backfill_up = site_data.disposal_system.backfill_upslope
    backfill_down = site_data.disposal_system.backfill_downslope
    avg_backfill = (backfill_up + backfill_down) / 24  # Convert inches to feet, approximate
    
    finished_elev = actual_ref - avg_backfill
    fin_grade_y = elev_to_y(finished_elev)
    
    # Draw finished grade line
    generator.add_line(
        (section_start_x, fin_grade_y),
        (section_start_x + section_length, fin_grade_y - 1),
        layer="XS-GRADE-FIN"
    )
    generator.add_text(
        "FINISHED GRADE",
        (section_start_x + 0.1, fin_grade_y + 0.1),
        height=0.05,
        layer="TEXT-LABEL"
    )
    
    # Draw tank in section
    tank_elev = site_data.disposal_system.tank.invert_elev
    tank_top_elev = tank_elev + 1  # Approximate tank height
    tank_x = section_start_x + 5
    
    generator.add_rectangle(
        (tank_x, elev_to_y(tank_top_elev)),
        4,  # Tank width in section
        elev_to_y(tank_elev) - elev_to_y(tank_top_elev),
        layer="XS-SYSTEM"
    )
    generator.add_text(
        "TANK",
        (tank_x + 2, elev_to_y((tank_elev + tank_top_elev)/2)),
        height=0.08,
        layer="TEXT-LABEL"
    )
    
    # Draw top of pipe
    pipe_elev = site_data.disposal_system.tank.invert_elev
    pipe_y = elev_to_y(pipe_elev)
    generator.add_line(
        (tank_x + 4, pipe_y),
        (tank_x + 8, pipe_y),
        layer="XS-SYSTEM"
    )
    generator.add_text(
        f"Top of Pipe: {pipe_elev}'",
        (tank_x + 8.1, pipe_y),
        height=0.05,
        layer="EL-CALLOUT"
    )
    
    # Draw leaching area bottom
    leach_bottom = site_data.disposal_system.leaching_area.bottom_elev
    leach_y = elev_to_y(leach_bottom)
    
    generator.add_line(
        (section_start_x + 10, leach_y),
        (section_start_x + section_length - 5, leach_y - 0.5),
        layer="XS-SYSTEM"
    )
    generator.add_text(
        f"Bottom of Disposal Field: {leach_bottom}'",
        (section_start_x + section_length - 4, leach_y - 0.2),
        height=0.05,
        layer="EL-CALLOUT"
    )
    
    # Draw elevation scale
    for elev in [actual_ref, actual_ref - 5, actual_ref - 10, actual_ref - 15]:
        y = elev_to_y(elev)
        generator.add_line(
            (section_start_x + section_length + 1, y),
            (section_start_x + section_length + 2, y),
            layer="EL-MARKER"
        )
        generator.add_text(
            f"{elev:.1f}'",
            (section_start_x + section_length + 2.1, y),
            height=0.05,
            layer="EL-CALLOUT"
        )
    
    # Vertical scale note
    generator.add_text(
        "Vertical Scale: 1\" = 5'",
        (0.5, 0.5),
        height=0.08,
        layer="TEXT-LABEL"
    )


# =============================================================================
# MAIN DRAWING GENERATION
# =============================================================================

def generate_full_drawing(site_data: SiteData) -> Drawing:
    """Generate a complete HHE-200 drawing set."""
    generator = DrawingGenerator(site_data)
    doc = generator.create_drawing()
    
    # Generate all components
    generate_site_plan(generator, site_data)
    generate_soil_profile(generator, site_data)
    generate_disposal_plan(generator, site_data)
    generate_cross_section(generator, site_data)
    
    return doc


def load_site_data(config_path: str) -> SiteData:
    """Load site data from a YAML configuration file.
    
    SITE_EVALUATOR DATA INJECTION POINT:
        This is where field worksheet data would be loaded and parsed.
        The YAML file would contain data collected during the site visit.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Parse owner info
    owner = config.get('owner', {})
    
    # Parse observation holes
    observation_holes = []
    for oh_data in config.get('observation_holes', []):
        soil_intervals = []
        for interval in oh_data.get('soil_data', []):
            soil_intervals.append(SoilInterval(
                depth=interval['depth'],
                texture=interval.get('texture', ''),
                consistence=interval.get('consistence', ''),
                color=interval.get('color', ''),
                redox=interval.get('redox', '')
            ))
        
        observation_holes.append(ObservationHole(
            id=oh_data['id'],
            coordinates=tuple(oh_data['coordinates']),
            ground_surface_elev=oh_data['ground_surface_elev'],
            depth_to_refusal=oh_data['depth_to_refusal'],
            test_pit=oh_data.get('test_pit', True),
            organic_horizon=oh_data.get('organic_horizon', 0),
            soil_data=soil_intervals,
            classification=oh_data.get('classification', ''),
            slope=oh_data.get('slope', 0),
            limiting_factor=oh_data.get('limiting_factor', ''),
            profile_condition=oh_data.get('profile_condition', '')
        ))
    
    # Parse disposal system
    ds_config = config.get('disposal_system', {})
    disposal_system = DisposalSystem(
        tank=Tank(
            location=tuple(ds_config.get('tank', {}).get('location', (0, 0))),
            type=ds_config.get('tank', {}).get('type', 'concrete'),
            capacity=ds_config.get('tank', {}).get('capacity', 1500),
            invert_elev=ds_config.get('tank', {}).get('invert_elev', 0),
            dimensions=tuple(ds_config.get('tank', {}).get('dimensions', (5, 10)))
        ),
        distribution_box=DistributionBox(
            location=tuple(ds_config.get('distribution_box', {}).get('location', (0, 0))),
            invert_elev=ds_config.get('distribution_box', {}).get('invert_elev', 0)
        ),
        leaching_area=LeachingArea(
            location=tuple(ds_config.get('leaching_area', {}).get('location', (0, 0))),
            dimensions=tuple(ds_config.get('leaching_area', {}).get('dimensions', (20, 30))),
            bottom_elev=ds_config.get('leaching_area', {}).get('bottom_elev', 0),
            type=ds_config.get('leaching_area', {}).get('type', 'stone_trench')
        ),
        backfill_upslope=ds_config.get('backfill_upslope', 0),
        backfill_downslope=ds_config.get('backfill_downslope', 0)
    )
    
    # Parse elevation reference
    erp_config = config.get('elevation_reference', {})
    elevation_reference = ElevationReference(
        location=tuple(erp_config.get('location', (0, 0))),
        description=erp_config.get('description', ''),
        reference_elev=erp_config.get('reference_elev', 0.0),
        actual_elev=erp_config.get('actual_elev', 0.0)
    )
    
    # Parse property boundaries
    boundaries = [tuple(p) for p in config.get('property', {}).get('boundaries', [])]
    
    return SiteData(
        owner_name=owner.get('name', ''),
        owner_address=owner.get('address', ''),
        property_tax_map=config.get('property', {}).get('tax_map', ''),
        property_lot=config.get('property', {}).get('lot', ''),
        property_boundaries=boundaries,
        observation_holes=observation_holes,
        disposal_system=disposal_system,
        elevation_reference=elevation_reference,
        scale=config.get('scale', '1" = 30\''),
        north_type=config.get('north_type', 'True')
    )


def create_sample_data() -> SiteData:
    """Create sample site data for testing."""
    # Sample soil data at 6" intervals
    sample_soil = [
        SoilInterval(0, "Org", "Lse", "2.5Y"),
        SoilInterval(6, "Snd", "Lse", "10YR 5/3"),
        SoilInterval(12, "Snd", "Fr", "10YR 5/3"),
        SoilInterval(18, "Lm", "Fr", "10YR 4/3"),
        SoilInterval(24, "SiCl", "Fi", "10YR 4/4"),
        SoilInterval(30, "Cl", "VFi", "5Y 5/2"),
        SoilInterval(36, "Cl", "Dns", "5Y 6/2"),
        SoilInterval(42, "Cl", "Dns", "5Y 6/3"),
        SoilInterval(48, "======", "BEDROCK", "======"),
    ]
    
    return SiteData(
        owner_name="John Smith",
        owner_address="123 Main Street, Auburn, ME 04210",
        property_tax_map="Map 12",
        property_lot="Lot 45",
        property_boundaries=[(1, 1), (8, 1), (8, 8), (5, 9), (1, 8), (1, 1)],
        observation_holes=[
            ObservationHole(
                id="OH-1",
                coordinates=(3.5, 4),
                ground_surface_elev=245.2,
                depth_to_refusal=48,
                test_pit=True,
                organic_horizon=4,
                soil_data=sample_soil,
                classification="Chatfield Silt Loam",
                slope=3,
                limiting_factor="restrictive_layer",
                profile_condition="Good"
            ),
            ObservationHole(
                id="OH-2",
                coordinates=(6, 3),
                ground_surface_elev=244.8,
                depth_to_refusal=36,
                test_pit=False,
                organic_horizon=3,
                soil_data=sample_soil[:6],  # Shorter profile
                classification="Lamoine Clay Loam",
                slope=4,
                limiting_factor="bedrock",
                profile_condition="Fair"
            ),
        ],
        disposal_system=DisposalSystem(
            tank=Tank(
                location=(4, 5.5),
                type="concrete",
                capacity=1500,
                invert_elev=243.2,
                dimensions=(5, 10)
            ),
            distribution_box=DistributionBox(
                location=(4.5, 4),
                invert_elev=242.8
            ),
            leaching_area=LeachingArea(
                location=(5, 1.5),
                dimensions=(10, 15),
                bottom_elev=241.5,
                type="stone_trench"
            ),
            backfill_upslope=18,
            backfill_downslope=24
        ),
        elevation_reference=ElevationReference(
            location=(3.5, 5.5),
            description="Iron rebar at NW corner of tank",
            reference_elev=0.0,
            actual_elev=245.50
        ),
        scale='1" = 30\'',
        north_type="True"
    )


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate HHE-200 AutoCAD drawings from site data"
    )
    parser.add_argument(
        '--config', '-c',
        help='YAML configuration file with site data'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output DWG file path'
    )
    parser.add_argument(
        '--drawing-type', '-t',
        choices=['full', 'site-plan', 'soil-profile', 'disposal-plan', 'cross-section'],
        default='full',
        help='Type of drawing to generate'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Generate sample drawing with test data'
    )
    
    args = parser.parse_args()
    
    # Load or create site data
    if args.config:
        site_data = load_site_data(args.config)
    elif args.sample:
        site_data = create_sample_data()
    else:
        print("Error: Either --config or --sample required")
        parser.print_help()
        sys.exit(1)
    
    # Generate drawing
    generator = DrawingGenerator(site_data)
    doc = generator.create_drawing()
    
    # Generate requested drawing type
    if args.drawing_type == 'full':
        generate_site_plan(generator, site_data)
        generate_soil_profile(generator, site_data)
        generate_disposal_plan(generator, site_data)
        generate_cross_section(generator, site_data)
    elif args.drawing_type == 'site-plan':
        generate_site_plan(generator, site_data)
    elif args.drawing_type == 'soil-profile':
        generate_soil_profile(generator, site_data)
    elif args.drawing_type == 'disposal-plan':
        generate_disposal_plan(generator, site_data)
    elif args.drawing_type == 'cross-section':
        generate_cross_section(generator, site_data)
    
    # Save drawing
    output_path = args.output or "hhe200_drawing.dwg"
    doc.saveas(output_path)
    print(f"Drawing saved to: {output_path}")


if __name__ == "__main__":
    main()