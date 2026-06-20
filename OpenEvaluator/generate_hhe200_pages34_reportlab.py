#!/usr/bin/env python3
"""
HHE-200 Pages 3-4 ReportLab Generator

Generates pages 3 and 4 of the HHE-200 form using ReportLab Canvas,
drawing the form structure from scratch and overlaying rendered images.

Structure:
  - Gray header block with form title and owner/address fields
  - Grid backgrounds for drawing areas
  - Soil profile table (page 3)
  - Cross-section layout (page 4)
  - Signature block at bottom
  - Rendered PNGs overlaid on drawing grids
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class HHE200ReportLabGenerator:
    """Generate HHE-200 pages 3-4 with proper form structure."""

    PAGE_WIDTH = 8.5 * inch
    PAGE_HEIGHT = 11 * inch
    MARGIN_LEFT = 0.4 * inch
    MARGIN_RIGHT = 0.4 * inch
    MARGIN_TOP = 0.5 * inch
    MARGIN_BOTTOM = 0.5 * inch

    # Colors
    HEADER_GRAY = colors.HexColor("#999999")
    GRID_GRAY = colors.HexColor("#DDDDDD")
    LIGHT_YELLOW = colors.HexColor("#FFFACD")
    BLACK = colors.black
    WHITE = colors.white

    def __init__(self, fields: Dict[str, Any]):
        """Initialize generator with form data."""
        self.fields = fields
        self.client_name = fields.get("client_name", "")
        self.job_id = fields.get("job_id", "")
        self.owner = fields.get("owner_name", "")
        self.address = fields.get("address", "")

    def draw_header(self, c: canvas.Canvas, page_title: str, y_position: float):
        """Draw the gray header block with form title and owner/address fields."""
        x_start = self.MARGIN_LEFT
        x_end = self.PAGE_WIDTH - self.MARGIN_RIGHT
        header_height = 0.6 * inch

        # Gray background
        c.setFillColor(self.HEADER_GRAY)
        c.rect(x_start, y_position - header_height, x_end - x_start, header_height,
               fill=1, stroke=0)

        # Form title (left side, white text)
        c.setFillColor(self.WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_start + 0.15 * inch, y_position - 0.35 * inch,
                    "SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION")

        # Owner field (right side)
        c.setFillColor(self.BLACK)
        c.setFont("Helvetica", 9)
        c.drawString(x_end - 2.5 * inch, y_position - 0.15 * inch, "Owner")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_end - 2.5 * inch, y_position - 0.35 * inch, self.owner[:30])

        # Address field (right side)
        c.setFillColor(self.BLACK)
        c.setFont("Helvetica", 9)
        c.drawString(x_end - 2.5 * inch, y_position - 0.50 * inch, "Address")
        c.setFont("Helvetica", 8)
        c.drawString(x_end - 2.5 * inch, y_position - 0.60 * inch, self.address[:30])

        return y_position - header_height - 0.1 * inch

    def draw_grid_background(self, c: canvas.Canvas, x: float, y: float,
                             width: float, height: float, grid_spacing: float = 0.1 * inch):
        """Draw light gray grid background."""
        # Light background
        c.setFillColor(self.LIGHT_YELLOW)
        c.setStrokeColor(self.BLACK)
        c.rect(x, y - height, width, height, fill=1, stroke=1)

        # Draw grid lines
        c.setStrokeColor(self.GRID_GRAY)
        c.setLineWidth(0.5)

        # Vertical lines
        curr_x = x + grid_spacing
        while curr_x < x + width:
            c.line(curr_x, y - height, curr_x, y)
            curr_x += grid_spacing

        # Horizontal lines
        curr_y = y - grid_spacing
        while curr_y > y - height:
            c.line(x, curr_y, x + width, curr_y)
            curr_y -= grid_spacing

    def overlay_image(self, c: canvas.Canvas, image_path: Path, x: float, y: float,
                      width: float, height: float):
        """Overlay a PNG image on the canvas, scaled to fit the box."""
        # Debug: Check file existence
        logger.info(f"Checking image: {image_path}")
        logger.info(f"  Exists: {image_path.exists()}")
        logger.info(f"  Grid area: x={x}, y={y}, width={width}, height={height}")

        if not image_path.exists():
            logger.error(f"❌ IMAGE NOT FOUND: {image_path}")
            return

        try:
            # Open image to get dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            logger.info(f"  PNG dimensions: {img_width}×{img_height}")

            # Calculate scaling to fit in the box while maintaining aspect ratio
            scale_x = width / img_width
            scale_y = height / img_height
            scale = min(scale_x, scale_y)

            logger.info(f"  Scale factors: x={scale_x:.4f}, y={scale_y:.4f}, using={scale:.4f}")

            scaled_width = img_width * scale
            scaled_height = img_height * scale

            # Center in the box
            offset_x = x + (width - scaled_width) / 2
            offset_y = y - height + (height - scaled_height) / 2

            logger.info(f"  Scaled to: {scaled_width:.1f}×{scaled_height:.1f} pts")
            logger.info(f"  Grid box bottom-left: ({x:.1f}, {y-height:.1f})")
            logger.info(f"  Image positioned at: ({offset_x:.1f}, {offset_y:.1f})")
            logger.info(f"  Image fits in box: width_ok={scaled_width <= width}, height_ok={scaled_height <= height}")

            c.drawImage(str(image_path), offset_x, offset_y,
                       width=scaled_width, height=scaled_height, preserveAspectRatio=True)
            logger.info(f"  ✓ Image overlaid successfully")
        except Exception as e:
            logger.error(f"❌ Failed to overlay image {image_path}: {e}")

    def overlay_sketch_at_scale(self, c: canvas.Canvas, sketch_path: Path, x: float, y: float,
                                width: float, height: float, scale_factor: float):
        """
        Overlay a sketch image at a specified scale factor.

        scale_factor: inches per feet (e.g., 0.01 for 1" = 100 feet)
        The sketch is rendered at this scale, with 1 inch = scale_factor * feet.
        """
        if not sketch_path or not sketch_path.exists():
            logger.warning(f"Sketch not found: {sketch_path}, skipping overlay")
            return

        logger.info(f"Overlaying sketch at scale: 1\" = {1/scale_factor:.1f} ft")

        try:
            img = Image.open(sketch_path)
            img_width, img_height = img.size
            logger.info(f"  Sketch dimensions: {img_width}×{img_height} pixels")

            # Calculate display size based on scale factor
            # Assume sketch is at 72 DPI (ReportLab default)
            # Display size = (image pixels / 72 dpi) * 72 * scale_factor
            # Which simplifies to just using the scale_factor to adjust the dimensions
            display_width = width
            display_height = height

            # Try to fit the sketch in the box at the specified scale
            scale_x = width / img_width
            scale_y = height / img_height
            display_scale = min(scale_x, scale_y, 1.0)  # Don't upscale

            display_width = img_width * display_scale
            display_height = img_height * display_scale

            # Center in the box
            offset_x = x + (width - display_width) / 2
            offset_y = y - height + (height - display_height) / 2

            logger.info(f"  Display size: {display_width:.1f}×{display_height:.1f} points")
            logger.info(f"  Position: ({offset_x:.1f}, {offset_y:.1f})")

            c.drawImage(str(sketch_path), offset_x, offset_y,
                       width=display_width, height=display_height, preserveAspectRatio=True)
            logger.info(f"  ✓ Sketch overlaid successfully")
        except Exception as e:
            logger.error(f"Failed to overlay sketch: {e}", exc_info=True)

    def draw_soil_profile_table(self, c: canvas.Canvas, fields: Dict[str, Any], y_position: float) -> float:
        """
        Draw soil profile description table at bottom of page 3.

        Args:
            c: ReportLab canvas
            fields: Form data dict
            y_position: Starting y position

        Returns:
            New y position after table
        """
        x_start = self.MARGIN_LEFT
        table_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        table_height = 1.8 * inch
        header_height = 0.25 * inch

        # Column structure: Depth | Obs Hole # | Textures | Consistency | Color | Redox Features
        col_widths = [0.6 * inch, 0.8 * inch, 1.1 * inch, 1.1 * inch, 0.9 * inch, 1.3 * inch]

        # Step 1: Draw table borders and grid
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.rect(x_start, y_position - table_height, table_width, table_height, fill=0, stroke=1)

        # Vertical lines
        c.setLineWidth(0.5)
        x_pos = x_start
        for width in col_widths:
            c.line(x_pos, y_position - header_height, x_pos, y_position - table_height)
            x_pos += width
        c.line(x_pos, y_position - header_height, x_pos, y_position - table_height)  # Right edge

        # Horizontal lines
        row_height = (table_height - header_height) / 8
        for i in range(8):
            y_line = y_position - header_height - (i + 1) * row_height
            c.line(x_start, y_line, x_start + table_width, y_line)

        # Step 2: Draw header background
        c.setLineWidth(0)
        c.setFillColor(colors.HexColor("#D3D3D3"))
        c.rect(x_start, y_position - header_height, table_width, header_height, fill=1, stroke=0)

        # Step 3: Add header text
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.BLACK)
        headers = ["Depth", "Obs #", "Textures", "Consistency", "Color", "Redox"]
        x_pos = x_start
        for i, header in enumerate(headers):
            col_x = x_pos + (col_widths[i] / 2)
            c.drawCentredString(col_x, y_position - 0.18 * inch, header)
            x_pos += col_widths[i]

        # Step 4: Add depth scale labels on left
        c.setFont("Helvetica", 7)
        c.setFillColor(self.BLACK)
        for i in range(8):
            depth_inches = 48 - (i * 6)
            y_row = y_position - header_height - (i * row_height) - (row_height / 2)
            col_x = x_start + (col_widths[0] / 2)
            c.drawCentredString(col_x, y_row, f'{depth_inches}"')

        # Step 5: Populate data from fields (if available)
        soil_profile = fields.get('soil_profile_data', [])
        c.setFont("Helvetica", 7)
        for i, row_data in enumerate(soil_profile[:8]):  # Max 8 rows
            y_row = y_position - header_height - (i * row_height) - (row_height / 2)
            x_pos = x_start + col_widths[0]

            # Populate each cell (skip first column, already filled with depth)
            for j in range(1, len(col_widths)):
                if j - 1 < len(row_data):
                    cell_text = str(row_data[j - 1])[:15]  # Truncate to fit
                    col_x = x_pos + (col_widths[j] / 2)
                    c.drawCentredString(col_x, y_row, cell_text)
                x_pos += col_widths[j]

        # Add note below table
        c.setFont("Helvetica", 8)
        c.drawString(x_start, y_position - table_height - 0.12 * inch, "Location of Observation Holes Shown Above")

        return y_position - table_height - 0.2 * inch

    def draw_construction_elevation_tables(self, c: canvas.Canvas, fields: Dict[str, Any], y_position: float) -> float:
        """
        Draw construction/elevation detail tables in middle of page 4.

        Args:
            c: ReportLab canvas
            fields: Form data dict with tank and pipe specs
            y_position: Starting y position

        Returns:
            New y position after tables
        """
        x_start = self.MARGIN_LEFT
        table_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        left_table_width = (table_width - 0.2 * inch) / 2
        right_x = x_start + left_table_width + 0.1 * inch

        table_height = 0.7 * inch
        header_height = 0.2 * inch
        row_height = (table_height - header_height) / 2

        # LEFT TABLE: Tank/Distribution Box Specs
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.setFillColor(colors.HexColor("#E8E8E8"))
        c.rect(x_start, y_position - table_height, left_table_width, table_height, fill=1, stroke=1)

        # Left table header
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.BLACK)
        c.drawString(x_start + 0.05 * inch, y_position - 0.15 * inch, "TANK / DISTRIBUTION BOX")

        # Left table grid
        c.setLineWidth(0.5)
        col1_x = x_start + left_table_width * 0.33
        col2_x = x_start + left_table_width * 0.66
        c.line(col1_x, y_position - header_height, col1_x, y_position - table_height)
        c.line(col2_x, y_position - header_height, col2_x, y_position - table_height)
        c.line(x_start, y_position - header_height - row_height, x_start + left_table_width, y_position - header_height - row_height)

        # Left table subheaders
        c.setFont("Helvetica", 7)
        c.drawString(x_start + 0.05 * inch, y_position - header_height - 0.08 * inch, "Type")
        c.drawString(col1_x + 0.05 * inch, y_position - header_height - 0.08 * inch, "Capacity")
        c.drawString(col2_x + 0.05 * inch, y_position - header_height - 0.08 * inch, "Elevation")

        # Left table data
        tank_type = fields.get("tank_type", "Concrete")
        tank_capacity = fields.get("tank_capacity", "1000 gal")
        tank_elevation = fields.get("tank_elevation", "TBD")

        c.setFont("Helvetica", 7)
        c.drawString(x_start + 0.05 * inch, y_position - header_height - row_height - 0.08 * inch, tank_type[:20])
        c.drawString(col1_x + 0.05 * inch, y_position - header_height - row_height - 0.08 * inch, tank_capacity[:15])
        c.drawString(col2_x + 0.05 * inch, y_position - header_height - row_height - 0.08 * inch, tank_elevation[:15])

        # RIGHT TABLE: Pipe Specs
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.setFillColor(colors.HexColor("#E8E8E8"))
        c.rect(right_x, y_position - table_height, left_table_width, table_height, fill=1, stroke=1)

        # Right table header
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.BLACK)
        c.drawString(right_x + 0.05 * inch, y_position - 0.15 * inch, "PIPE SPECS")

        # Right table grid
        c.setLineWidth(0.5)
        col1_x_r = right_x + left_table_width * 0.5
        c.line(col1_x_r, y_position - header_height, col1_x_r, y_position - table_height)
        c.line(right_x, y_position - header_height - row_height, right_x + left_table_width, y_position - header_height - row_height)

        # Right table subheaders
        c.setFont("Helvetica", 7)
        c.drawString(right_x + 0.05 * inch, y_position - header_height - 0.08 * inch, "Size")
        c.drawString(col1_x_r + 0.05 * inch, y_position - header_height - 0.08 * inch, "Slope")

        # Right table data
        pipe_size = fields.get("pipe_size", "4\"")
        pipe_slope = fields.get("pipe_slope", "1/8\"")

        c.setFont("Helvetica", 7)
        c.drawString(right_x + 0.05 * inch, y_position - header_height - row_height - 0.08 * inch, pipe_size[:15])
        c.drawString(col1_x_r + 0.05 * inch, y_position - header_height - row_height - 0.08 * inch, pipe_slope[:15])

        return y_position - table_height - 0.15 * inch

    def draw_site_location_inset_and_notes(self, c: canvas.Canvas, y_position: float) -> float:
        """
        Draw site location inset map (top) and disclaimer notes (bottom) on right sidebar of page 3.

        Args:
            c: ReportLab canvas
            y_position: Starting y position (top of inset box)

        Returns:
            New y position after both boxes
        """
        sidebar_x = self.PAGE_WIDTH - self.MARGIN_RIGHT - 1.6 * inch
        sidebar_width = 1.5 * inch

        # Site location inset (top)
        inset_y = y_position
        inset_height = 1.6 * inch

        # Draw inset background (gray)
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.setFillColor(colors.HexColor("#F2F2F2"))
        c.rect(sidebar_x, inset_y - inset_height, sidebar_width, inset_height, fill=1, stroke=1)

        # "SITE LOCATION" label
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(self.BLACK)
        c.drawString(sidebar_x + 0.1 * inch, inset_y - 0.25 * inch, "SITE")
        c.drawString(sidebar_x + 0.1 * inch, inset_y - 0.45 * inch, "LOCATION")

        # Asterisk placeholder (represents map)
        c.setFont("Helvetica", 24)
        c.drawString(sidebar_x + 0.55 * inch, inset_y - 0.85 * inch, "*")

        inset_bottom = inset_y - inset_height - 0.1 * inch

        # Disclaimer notes block (below inset)
        notes_y = inset_bottom
        notes_height = 2.0 * inch

        # Draw notes background (white)
        c.setLineWidth(1)
        c.setFillColor(self.WHITE)
        c.setStrokeColor(self.BLACK)
        c.rect(sidebar_x, notes_y - notes_height, sidebar_width, notes_height, fill=1, stroke=1)

        # Notes text - disclaimer
        disclaimer_text = (
            "NOTE: LOCATION OF SEPTIC SYSTEM HAS BEEN SITED ON THE PROPERTY BASED UPON "
            "BOUNDARY LINE/PROPERTY INFORMATION PROVIDED BY OWNER OR OWNER'S AGENT. "
            "NO INDEPENDENT VERIFICATION OF BOUNDARY LINE LOCATIONS HAS BEEN MADE BY THIS "
            "SITE EVALUATOR. PROFESSIONAL BOUNDARY SURVEYS HAVE BEEN VERIFIED BY "
            "OWNER/INSTALLER PRIOR TO SYSTEM INSTALLATION. ANY DISCREPANCY FROM THAT "
            "SHOWN SHALL BE IMMEDIATELY BROUGHT TO THE ATTENTION OF THE DESIGN SITE "
            "EVALUATOR PRIOR TO BEGINNING ANY WORK."
        )

        c.setFont("Helvetica", 7)
        c.setFillColor(self.BLACK)

        # Break text into lines that fit in the box
        text_x = sidebar_x + 0.08 * inch
        text_y = notes_y - 0.12 * inch
        line_height = 0.09 * inch

        # Simple word-wrap implementation
        words = disclaimer_text.split()
        current_line = ""
        line_count = 0
        max_lines = 20  # Safety limit

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            # Rough estimate: ~11 characters fit in the width at 7pt
            if len(test_line) > 28 or line_count >= max_lines - 1:
                if current_line:
                    c.drawString(text_x, text_y - (line_count * line_height), current_line)
                    line_count += 1
                current_line = word
            else:
                current_line = test_line

        if current_line and line_count < max_lines:
            c.drawString(text_x, text_y - (line_count * line_height), current_line)

        return notes_y - notes_height - 0.1 * inch

    def draw_page4_notes_section(self, c: canvas.Canvas, fields: Dict[str, Any], y_position: float) -> float:
        """
        Draw notes section on page 4, just above signature block.

        Args:
            c: ReportLab canvas
            fields: Form data dict with system specs
            y_position: Starting y position

        Returns:
            New y position after notes section
        """
        x_start = self.MARGIN_LEFT
        section_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        section_height = 1.0 * inch

        # Draw notes box border
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.setFillColor(self.WHITE)
        c.rect(x_start, y_position - section_height, section_width, section_height, fill=1, stroke=1)

        # Notes header
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(self.BLACK)
        c.drawString(x_start + 0.1 * inch, y_position - 0.2 * inch, "SYSTEM NOTES")

        # Horizontal line below header
        c.setLineWidth(0.5)
        c.line(x_start + 0.05 * inch, y_position - 0.28 * inch, x_start + section_width - 0.05 * inch, y_position - 0.28 * inch)

        # Notes content - system specifications
        notes_text = fields.get("system_notes",
                               "GSF-B43 Module approved for this application. "
                               "System designed per Maine Department of Health & Human Services standards. "
                               "All work shall be in accordance with the approved design.")

        c.setFont("Helvetica", 8)
        c.setFillColor(self.BLACK)

        # Word-wrap notes
        text_x = x_start + 0.1 * inch
        text_y = y_position - 0.4 * inch
        line_height = 0.12 * inch
        max_width_chars = 95  # Approximate chars per line at 8pt

        words = notes_text.split()
        current_line = ""
        line_count = 0
        max_lines = 5  # Safety limit

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) > 28 or line_count >= max_lines - 1:
                if current_line:
                    c.drawString(text_x, text_y - (line_count * line_height), current_line)
                    line_count += 1
                current_line = word
            else:
                current_line = test_line

        if current_line and line_count < max_lines:
            c.drawString(text_x, text_y - (line_count * line_height), current_line)

        return y_position - section_height - 0.1 * inch

    def draw_signature_block(self, c: canvas.Canvas, y_position: float, page_num: int = 3):
        """Draw signature block at bottom of page."""
        x_start = self.MARGIN_LEFT
        x_end = self.PAGE_WIDTH - self.MARGIN_RIGHT

        # Horizontal line for signature
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.line(x_start, y_position - 0.2 * inch, x_start + 2 * inch, y_position - 0.2 * inch)

        # Labels
        c.setFont("Helvetica", 8)
        c.setFillColor(self.BLACK)
        c.drawString(x_start, y_position - 0.35 * inch, "Site Evaluator Signature or Initials")
        c.drawString(x_start + 2.2 * inch, y_position - 0.2 * inch, "SE #")
        c.drawString(x_start + 3.5 * inch, y_position - 0.2 * inch, "Date")

        # Page footer
        c.setFont("Helvetica", 7)
        c.drawString(x_end - 1.5 * inch, y_position - 0.4 * inch, f"Page {page_num} of 4")

    def generate_page_3(self, boundary_png: Optional[Path] = None,
                       field_png: Optional[Path] = None,
                       soil_png: Optional[Path] = None,
                       output_path: Path = None) -> Path:
        """Generate page 3 (Site Plan + Soil Profile)."""
        if output_path is None:
            output_path = Path(f"/home/workspace/OpenEvaluator/HHE-200-{self.client_name}-{self.job_id}-page3.pdf")

        logger.info(f"Generating page 3 for {self.client_name} {self.job_id}")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.setTitle(f"HHE-200 Page 3 - {self.client_name}")

        # Starting position (top of page)
        y = self.PAGE_HEIGHT - self.MARGIN_TOP

        # Draw header
        y = self.draw_header(c, "SITE PLAN", y)

        # Draw scale and title
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN_LEFT, y - 0.15 * inch, 'Scale 1" = 100 ft')
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN_LEFT + 1.5 * inch, y - 0.15 * inch, "SITE PLAN")

        # Site location inset label (right side)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.PAGE_WIDTH - self.MARGIN_RIGHT - 1.5 * inch, y - 0.15 * inch, "SITE LOCATION")

        y -= 0.3 * inch

        # Main site plan drawing area with grid
        plan_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT - 1.8 * inch  # Leave room for inset
        plan_height = 3.2 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, plan_width, plan_height, 0.1 * inch)

        # Overlay site plan image (boundary + field placement)
        if boundary_png and boundary_png.exists():
            self.overlay_image(c, boundary_png, self.MARGIN_LEFT, y, plan_width, plan_height)

        # Site location inset box (right side)
        inset_x = self.PAGE_WIDTH - self.MARGIN_RIGHT - 1.6 * inch
        inset_width = 1.5 * inch
        inset_height = 1.6 * inch

        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.rect(inset_x, y - inset_height, inset_width, inset_height, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(inset_x + 0.1 * inch, y - 0.2 * inch, "SITE")

        y -= (plan_height + 0.15 * inch)

        # Soil profile section header and table
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(self.BLACK)
        c.drawString(self.MARGIN_LEFT, y, "SOL PROFILE DESCRIPTION AND CLASSIFICATION")

        y -= 0.2 * inch

        # Draw soil profile table structure
        soil_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        soil_height = 2.0 * inch

        # Draw table border
        c.setLineWidth(1)
        c.setStrokeColor(self.BLACK)
        c.rect(self.MARGIN_LEFT, y - soil_height, soil_width, soil_height, fill=0, stroke=1)

        # Draw column dividers and rows
        col_width = soil_width / 2
        c.line(self.MARGIN_LEFT + col_width, y - soil_height, self.MARGIN_LEFT + col_width, y)

        # Row dividers (depth scale on left)
        row_height = soil_height / 8
        for i in range(1, 8):
            y_line = y - (i * row_height)
            c.line(self.MARGIN_LEFT, y_line, self.MARGIN_LEFT + soil_width, y_line)

        # Add depth scale labels
        c.setFont("Helvetica", 7)
        for i in range(9):
            depth_inches = 48 - (i * 6)
            y_label = y - (i * row_height) - 0.08 * inch
            if 0 <= depth_inches <= 48:
                c.drawString(self.MARGIN_LEFT + 0.05 * inch, y_label, f"{depth_inches}\"")

        # Overlay soil profile image on top of table
        if soil_png and soil_png.exists():
            self.overlay_image(c, soil_png, self.MARGIN_LEFT, y, soil_width, soil_height)

        y -= (soil_height + 0.1 * inch)

        # Location of observation holes section
        c.setFont("Helvetica", 8)
        c.drawString(self.MARGIN_LEFT, y, "Location of Observation Holes Shown Above")

        y -= 0.25 * inch

        # Signature block
        self.draw_signature_block(c, y, page_num=3)

        c.save()
        logger.info(f"✓ Page 3 generated: {output_path}")
        return output_path

    def generate_page_3_with_sketch(self, sketch_path: Optional[Path] = None,
                                     scale_factor: float = 0.01,
                                     output_path: Optional[Path] = None) -> Path:
        """Generate page 3 with sketch rendered at specified scale."""
        if output_path is None:
            output_path = Path(f"/home/workspace/OpenEvaluator/HHE-200-{self.client_name}-{self.job_id}-page3.pdf")

        logger.info(f"Generating page 3 with sketch (scale 1\" = {1/scale_factor:.1f} ft)")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.setTitle(f"HHE-200 Page 3 - {self.client_name}")

        y = self.PAGE_HEIGHT - self.MARGIN_TOP
        y = self.draw_header(c, "SITE PLAN", y)

        # Draw scale label and title
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN_LEFT, y - 0.15 * inch, f'Scale 1" = {1/scale_factor:.0f} ft')
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN_LEFT + 1.5 * inch, y - 0.15 * inch, "SITE PLAN")

        y -= 0.3 * inch

        # Main site plan area
        plan_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT - 1.8 * inch
        plan_height = 3.2 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, plan_width, plan_height, 0.1 * inch)

        # Overlay sketch
        if sketch_path:
            self.overlay_sketch_at_scale(c, sketch_path, self.MARGIN_LEFT, y, plan_width, plan_height, scale_factor)

        # Draw site location inset and notes on right sidebar (at same y level as plan)
        sidebar_y = y  # Start at top of site plan area
        self.draw_site_location_inset_and_notes(c, sidebar_y)

        y -= (plan_height + 0.15 * inch)

        # Soil profile section with table
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.MARGIN_LEFT, y, "SOIL PROFILE DESCRIPTION AND CLASSIFICATION")

        y -= 0.2 * inch

        # Draw soil profile table
        y = self.draw_soil_profile_table(c, self.fields, y)

        y -= 0.15 * inch
        self.draw_signature_block(c, y, page_num=3)

        c.save()
        logger.info(f"✓ Page 3 generated: {output_path}")
        return output_path

    def generate_page_4_with_sketch(self, sketch_path: Optional[Path] = None,
                                     scale_top: float = 0.1,
                                     scale_bottom_vert: float = 0.4,
                                     scale_bottom_horiz: float = 0.2,
                                     output_path: Optional[Path] = None) -> Path:
        """Generate page 4 with sketches at different scales for top and bottom sections."""
        if output_path is None:
            output_path = Path(f"/home/workspace/OpenEvaluator/HHE-200-{self.client_name}-{self.job_id}-page4.pdf")

        logger.info(f"Generating page 4 with sketches")
        logger.info(f"  Top (septic plan) scale: 1\" = {1/scale_top:.1f} ft")
        logger.info(f"  Bottom vertical scale: 1\" = {1/scale_bottom_vert:.1f} ft")
        logger.info(f"  Bottom horizontal scale: 1\" = {1/scale_bottom_horiz:.1f} ft")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.setTitle(f"HHE-200 Page 4 - {self.client_name}")

        y = self.PAGE_HEIGHT - self.MARGIN_TOP
        y = self.draw_header(c, "SUBSURFACE WASTEWATER DISPOSAL PLAN", y)

        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN_LEFT, y - 0.15 * inch, f'Top Scale 1" = {1/scale_top:.0f} ft')
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN_LEFT + 1.5 * inch, y - 0.15 * inch, "SUBSURFACE WASTEWATER DISPOSAL PLAN")

        y -= 0.3 * inch

        # Top section: Septic system plan
        system_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        system_height = 2.5 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, system_width, system_height, 0.1 * inch)

        if sketch_path:
            self.overlay_sketch_at_scale(c, sketch_path, self.MARGIN_LEFT, y, system_width, system_height, scale_top)

        y -= (system_height + 0.15 * inch)

        # Construction/elevation tables
        y = self.draw_construction_elevation_tables(c, self.fields, y)

        # Notes section
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.MARGIN_LEFT, y, "NOTES AND SPECIFICATIONS")

        y -= 0.2 * inch
        notes_height = 0.9 * inch

        c.setLineWidth(1)
        c.setFillColor(self.WHITE)
        c.setStrokeColor(self.BLACK)
        c.rect(self.MARGIN_LEFT, y - notes_height, system_width, notes_height, fill=1, stroke=1)

        y -= (notes_height + 0.1 * inch)

        # Cross-section section
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.MARGIN_LEFT, y, "CROSS-SECTION A-A")

        y -= 0.2 * inch

        cross_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        cross_height = 2.0 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, cross_width, cross_height, 0.1 * inch)

        # Note: For cross-section, we'd typically use different scale factors, but same sketch for now
        if sketch_path:
            logger.info(f"  Rendering cross-section sketch at V={1/scale_bottom_vert:.1f}' H={1/scale_bottom_horiz:.1f}'")
            # Use horizontal scale for cross-section fit
            self.overlay_sketch_at_scale(c, sketch_path, self.MARGIN_LEFT, y, cross_width, cross_height, scale_bottom_horiz)

        y -= (cross_height + 0.1 * inch)

        # Page 4 notes section (above signature)
        y = self.draw_page4_notes_section(c, self.fields, y)

        self.draw_signature_block(c, y, page_num=4)

        c.save()
        logger.info(f"✓ Page 4 generated: {output_path}")
        return output_path

    def generate_page_4(self, cross_section_png: Optional[Path] = None,
                       system_plan_png: Optional[Path] = None,
                       output_path: Path = None) -> Path:
        """Generate page 4 (Subsurface Wastewater Disposal Plan)."""
        if output_path is None:
            output_path = Path(f"/home/workspace/OpenEvaluator/HHE-200-{self.client_name}-{self.job_id}-page4.pdf")

        logger.info(f"Generating page 4 for {self.client_name} {self.job_id}")

        c = canvas.Canvas(str(output_path), pagesize=letter)
        c.setTitle(f"HHE-200 Page 4 - {self.client_name}")

        # Starting position
        y = self.PAGE_HEIGHT - self.MARGIN_TOP

        # Draw header
        y = self.draw_header(c, "SUBSURFACE WASTEWATER DISPOSAL PLAN", y)

        # Title and scale
        c.setFont("Helvetica", 9)
        c.drawString(self.MARGIN_LEFT, y - 0.15 * inch, 'Scale 1" = 50 ft')
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.MARGIN_LEFT + 1.5 * inch, y - 0.15 * inch, "SUBSURFACE WASTEWATER DISPOSAL PLAN")

        y -= 0.3 * inch

        # Upper section: System plan layout
        system_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        system_height = 2.5 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, system_width, system_height, 0.1 * inch)

        # Overlay system plan image
        if system_plan_png and system_plan_png.exists():
            self.overlay_image(c, system_plan_png, self.MARGIN_LEFT, y, system_width, system_height)

        y -= (system_height + 0.15 * inch)

        # Notes and specifications section header
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(self.BLACK)
        c.drawString(self.MARGIN_LEFT, y, "NOTES AND SPECIFICATIONS")

        y -= 0.2 * inch
        notes_height = 0.9 * inch

        # Draw notes box with light fill
        c.setLineWidth(1)
        c.setFillColor(self.WHITE)
        c.setStrokeColor(self.BLACK)
        c.rect(self.MARGIN_LEFT, y - notes_height, system_width, notes_height, fill=1, stroke=1)

        # Add note checkboxes/structure lines inside
        c.setFont("Helvetica", 7)
        line_height = 0.15 * inch
        for i in range(4):
            y_line = y - (i + 1) * line_height
            c.line(self.MARGIN_LEFT + 0.15 * inch, y_line, self.MARGIN_LEFT + system_width - 0.15 * inch, y_line)

        y -= (notes_height + 0.1 * inch)

        # Loading grade section
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.BLACK)
        c.drawString(self.MARGIN_LEFT, y, "LOADING GRADE")

        y -= 0.15 * inch

        # Loading grade table with structure
        table_width = 2.0 * inch
        table_height = 0.35 * inch
        c.setLineWidth(1)
        c.setFillColor(self.LIGHT_YELLOW)
        c.setStrokeColor(self.BLACK)
        c.rect(self.MARGIN_LEFT, y - table_height, table_width, table_height, fill=1, stroke=1)

        # Add column dividers in loading grade table
        c.line(self.MARGIN_LEFT + table_width/2, y - table_height, self.MARGIN_LEFT + table_width/2, y)

        y -= (table_height + 0.2 * inch)

        # Cross-section header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.MARGIN_LEFT, y, "CROSS-SECTION A-A")

        y -= 0.2 * inch

        # Cross-section area with grid
        cross_width = self.PAGE_WIDTH - 2 * self.MARGIN_LEFT
        cross_height = 2.0 * inch

        self.draw_grid_background(c, self.MARGIN_LEFT, y, cross_width, cross_height, 0.1 * inch)

        # Overlay cross-section image
        if cross_section_png and cross_section_png.exists():
            self.overlay_image(c, cross_section_png, self.MARGIN_LEFT, y, cross_width, cross_height)

        y -= (cross_height + 0.1 * inch)

        # Signature block
        self.draw_signature_block(c, y, page_num=4)

        c.save()
        logger.info(f"✓ Page 4 generated: {output_path}")
        return output_path


def generate_pages_3_4(fields: Dict[str, Any], sketch_path: Optional[Path] = None,
                       output_page3: Optional[Path] = None,
                       output_page4: Optional[Path] = None) -> bool:
    """
    Generate pages 3-4 with sketches rendered at evaluator-specified scales.

    Args:
        fields: Form data dict with scales and property info
        sketch_path: Path to uploaded sketch image
        output_page3: Where to save page 3 PDF
        output_page4: Where to save page 4 PDF

    Returns:
        True if successful, False otherwise
    """
    try:
        client_name = fields.get("client_name", "Unknown")
        job_id = fields.get("job_id", "Unknown")

        # Extract scale factors (inches per feet)
        scale_page3 = float(fields.get("scale_page3_inches_per_feet", 0.01))  # Default 1" = 100'
        scale_page4_top = float(fields.get("scale_page4_top_inches_per_feet", 0.1))  # Default 1" = 10'

        logger.info(f"Generating pages 3-4 for {client_name} {job_id}")
        logger.info(f"  Page 3 scale: 1\" = {1/scale_page3:.1f} ft")
        logger.info(f"  Page 4 (top) scale: 1\" = {1/scale_page4_top:.1f} ft")

        generator = HHE200ReportLabGenerator(fields)

        # Generate page 3 with sketch
        if output_page3 is None:
            output_page3 = Path(f"/home/workspace/OpenEvaluator/HHE-200-{client_name}-{job_id}-page3.pdf")

        page3_path = generator.generate_page_3_with_sketch(
            sketch_path=sketch_path,
            scale_factor=scale_page3,
            output_path=output_page3
        )

        # Generate page 4 with sketch
        if output_page4 is None:
            output_page4 = Path(f"/home/workspace/OpenEvaluator/HHE-200-{client_name}-{job_id}-page4.pdf")

        scale_page4_bottom_vert = float(fields.get("scale_page4_bottom_vertical_inches_per_feet", 0.4))
        scale_page4_bottom_horiz = float(fields.get("scale_page4_bottom_horizontal_inches_per_feet", 0.2))

        page4_path = generator.generate_page_4_with_sketch(
            sketch_path=sketch_path,
            scale_top=scale_page4_top,
            scale_bottom_vert=scale_page4_bottom_vert,
            scale_bottom_horiz=scale_page4_bottom_horiz,
            output_path=output_page4
        )

        logger.info(f"✓ Pages 3-4 generated successfully")
        logger.info(f"  Page 3: {page3_path}")
        logger.info(f"  Page 4: {page4_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate pages 3-4: {e}", exc_info=True)
        return False


def main():
    """Generate pages 3-4 for a given project."""
    parser = argparse.ArgumentParser(description="Generate HHE-200 pages 3-4")
    parser.add_argument("--client", default="Marquis", help="Client name")
    parser.add_argument("--job", default="26-018", help="Job ID")
    parser.add_argument("--boundary", help="Path to boundary PNG")
    parser.add_argument("--field", help="Path to field placement PNG")
    parser.add_argument("--soil", help="Path to soil profile PNG")
    parser.add_argument("--cross-section", help="Path to cross-section PNG")
    parser.add_argument("--system-plan", help="Path to system plan PNG")

    args = parser.parse_args()

    # Default paths if not provided
    base_dir = Path("/home/workspace/OpenEvaluator")
    client_lower = args.client.lower()

    boundary_png = Path(args.boundary) if args.boundary else \
                   base_dir / f"boundary_{client_lower}.png"
    field_png = Path(args.field) if args.field else \
                base_dir / f"field_placement_{client_lower}.png"
    soil_png = Path(args.soil) if args.soil else \
               base_dir / f"soil_profile_{client_lower}.png"
    cross_section_png = Path(args.cross_section) if args.cross_section else \
                       base_dir / f"cross_section_{client_lower}_hires.png"

    # Form data
    fields = {
        "client_name": args.client,
        "job_id": args.job,
        "owner_name": "KRISTEN MARQUIS" if args.client == "Marquis" else "CHARLES ROBERTS",
        "address": "17 ASPEN WAY" if args.client == "Marquis" else "450 LANE ROAD",
    }

    generator = HHE200ReportLabGenerator(fields)

    # Generate both pages
    page3_path = generator.generate_page_3(
        boundary_png=boundary_png,
        field_png=field_png,
        soil_png=soil_png
    )

    page4_path = generator.generate_page_4(
        cross_section_png=cross_section_png,
        system_plan_png=field_png  # Use field placement as system plan placeholder
    )

    logger.info(f"✓ Both pages generated successfully")
    logger.info(f"  Page 3: {page3_path}")
    logger.info(f"  Page 4: {page4_path}")


if __name__ == "__main__":
    main()
