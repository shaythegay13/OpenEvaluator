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
        """Overlay a PNG image on the canvas."""
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            return

        try:
            # Open image to get dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size

            # Calculate scaling to fit in the box while maintaining aspect ratio
            scale_x = width / img_width
            scale_y = height / img_height
            scale = min(scale_x, scale_y)

            scaled_width = img_width * scale
            scaled_height = img_height * scale

            # Center in the box
            offset_x = x + (width - scaled_width) / 2
            offset_y = y - height + (height - scaled_height) / 2

            c.drawImage(str(image_path), offset_x, offset_y,
                       width=scaled_width, height=scaled_height, preserveAspectRatio=True)
        except Exception as e:
            logger.warning(f"Failed to overlay image {image_path}: {e}")

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
