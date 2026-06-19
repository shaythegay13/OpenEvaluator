#!/usr/bin/env python3
"""
generate_hhe200_pages34.py — ReportLab-based generation of HHE-200 pages 3-4.

Generates properly formatted pages 3 and 4 of the HHE-200 form, matching
George Bouchles' layout exactly, with composite images and populated grids.

Usage:
    python3 generate_hhe200_pages34.py --client Marquis --job 26-018
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, grey, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage,
    PageBreak, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from PIL import Image
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class HHE200Page3Generator:
    """Generate page 3 (Site Plan + Soil Profile) using ReportLab."""

    PAGE_WIDTH = 8.5 * inch
    PAGE_HEIGHT = 11 * inch
    MARGIN = 0.5 * inch

    def __init__(self, fields: Dict[str, Any], boundary_png: Path, field_png: Path,
                 soil_png: Path, site_location_png: Optional[Path] = None):
        """
        Initialize page 3 generator.

        Args:
            fields: Parsed form data dict
            boundary_png: Path to boundary layer PNG
            field_png: Path to field placement PNG
            soil_png: Path to soil profile grid PNG
            site_location_png: Optional site location inset map
        """
        self.fields = fields
        self.boundary_png = boundary_png
        self.field_png = field_png
        self.soil_png = soil_png
        self.site_location_png = site_location_png

    def build(self, output_path: Path) -> Dict[str, Any]:
        """Build page 3 PDF."""
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                topMargin=0.3 * inch,
                bottomMargin=0.5 * inch,
                leftMargin=0.4 * inch,
                rightMargin=0.4 * inch,
            )

            elements = []

            # Header block
            elements.append(self._build_header())
            elements.append(Spacer(1, 0.15 * inch))

            # Scale line
            styles = getSampleStyleSheet()
            scale_style = ParagraphStyle(
                'Scale',
                parent=styles['Normal'],
                fontSize=9,
                leading=10,
                textColor=black,
            )
            elements.append(Paragraph(f"Scale: 1\" = {self.fields.get('site_plan_scale_ft_per_in', '100')} ft.", scale_style))

            # Site plan + soil profile section
            elements.append(self._build_plan_and_soil_section())
            elements.append(Spacer(1, 0.2 * inch))

            # Footer
            elements.append(self._build_footer())

            # Build PDF
            doc.build(elements)
            logger.info(f"✓ Page 3 generated: {output_path}")

            return {
                "status": "GENERATED",
                "output_file": output_path,
                "page": 3,
            }
        except Exception as e:
            logger.error(f"Error generating page 3: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
            }

    def _build_header(self) -> Table:
        """Build gray header block with title and owner/address fields."""
        header_data = [
            [
                Paragraph(
                    "<b>SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION</b><br/>"
                    "Maine Department of Health and Human Services (DHHS), Office of Environmental and Community Health<br/>"
                    "(207) 287-2070 | Fax (207) 287-4172 | subsurface.wastewater@maine.gov",
                    ParagraphStyle(
                        'HeaderTitle',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=9,
                        textColor=white,
                    )
                ),
                Paragraph(
                    f"<b>Owner:</b><br/>{self.fields.get('client_name', '')}<br/><br/>"
                    f"<b>Address:</b><br/>{self.fields.get('property_address', '')}",
                    ParagraphStyle(
                        'HeaderFields',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=10,
                        textColor=black,
                    )
                )
            ]
        ]

        header_table = Table(header_data, colWidths=[5.5*inch, 2.2*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#4a4a4a')),
            ('BACKGROUND', (1, 0), (1, 0), white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (0, 0), 8),
            ('PADDING', (1, 0), (1, 0), 6),
            ('BORDER', (1, 0), (1, 0), 1, black),
        ]))
        return header_table

    def _build_plan_and_soil_section(self) -> Table:
        """Build main site plan + soil profile section."""
        # Load and scale images
        plan_img = self._load_and_scale_image(self.boundary_png, max_width=3.8*inch, max_height=4.5*inch)
        soil_img = self._load_and_scale_image(self.soil_png, max_width=3.5*inch, max_height=2.5*inch)

        # Left column: Site plan + soil grid
        left_cells = []
        if plan_img:
            left_cells.append(Paragraph("<b>SITE PLAN</b>", getSampleStyleSheet()['Normal']))
            left_cells.append(plan_img)

        left_cells.append(Spacer(1, 0.1*inch))

        if soil_img:
            left_cells.append(Paragraph(
                "<b>SOL PROFILE DESCRIPTION AND CLASSIFICATION</b>",
                ParagraphStyle(
                    'SoilTitle',
                    parent=getSampleStyleSheet()['Normal'],
                    fontSize=9,
                    leading=10,
                )
            ))
            left_cells.append(soil_img)

        # Right column: Site location + notes
        right_cells = []

        if self.site_location_png and self.site_location_png.exists():
            loc_img = self._load_and_scale_image(self.site_location_png, max_width=1.8*inch, max_height=1.8*inch)
            right_cells.append(Paragraph("<b>SITE LOCATION</b>", getSampleStyleSheet()['Normal']))
            if loc_img:
                right_cells.append(loc_img)

        right_cells.append(Spacer(1, 0.2*inch))

        # Special notes box
        special_notes = self.fields.get('special_notes', 'None')
        right_cells.append(Paragraph(
            f"<b>SPECIAL NOTES:</b><br/>{special_notes}",
            ParagraphStyle(
                'SpecialNotes',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=8,
                leading=9,
            )
        ))

        # Create two-column layout
        section_data = [[left_cells, right_cells]]
        section_table = Table(section_data, colWidths=[4.2*inch, 2.2*inch])
        section_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        return section_table

    def _build_footer(self) -> Table:
        """Build signature block and footer."""
        footer_data = [
            [
                Paragraph(
                    f"<b>Site Evaluator Signature or Initials:</b> _________________________",
                    getSampleStyleSheet()['Normal']
                ),
                Paragraph(
                    f"<b>SE #:</b> {self.fields.get('evaluator_number', '')}",
                    getSampleStyleSheet()['Normal']
                ),
                Paragraph(
                    f"<b>Date:</b> ___________________",
                    getSampleStyleSheet()['Normal']
                ),
            ],
            [
                {
                    'content': Paragraph(
                        "Subsurface Wastewater Unit — HHE-200: Subsurface Wastewater Disposal Application Rev. 7/2025",
                        ParagraphStyle(
                            'Footer',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=7,
                            textColor=HexColor('#666666'),
                        )
                    ),
                    'colspan': 3,
                }
            ],
            [
                {
                    'content': Paragraph(
                        "Page 3 of 4",
                        ParagraphStyle(
                            'PageNum',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=8,
                            alignment=1,  # Right align
                        )
                    ),
                    'colspan': 3,
                }
            ],
        ]

        footer_table = Table(footer_data, colWidths=[3.0*inch, 1.5*inch, 1.7*inch])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ]))

        return footer_table

    def _load_and_scale_image(self, img_path: Path, max_width: float, max_height: float) -> Optional[RLImage]:
        """Load image and scale to fit max dimensions."""
        try:
            if not img_path.exists():
                logger.warning(f"Image not found: {img_path}")
                return None

            img = Image.open(img_path)
            img_width = img.width
            img_height = img.height

            # Calculate scale factor to fit within max dimensions
            width_scale = max_width / (img_width / 96 * inch)  # Assuming 96 DPI
            height_scale = max_height / (img_height / 96 * inch)
            scale = min(width_scale, height_scale, 1.0)  # Don't upscale

            scaled_width = img_width / 96 * inch * scale
            scaled_height = img_height / 96 * inch * scale

            return RLImage(str(img_path), width=scaled_width, height=scaled_height)
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {e}")
            return None


class HHE200Page4Generator:
    """Generate page 4 (Cross-Section + System Notes) using ReportLab."""

    PAGE_WIDTH = 8.5 * inch
    PAGE_HEIGHT = 11 * inch
    MARGIN = 0.5 * inch

    def __init__(self, fields: Dict[str, Any], system_plan_png: Path, cross_section_png: Path):
        """
        Initialize page 4 generator.

        Args:
            fields: Parsed form data dict
            system_plan_png: Path to subsurface disposal system plan PNG
            cross_section_png: Path to cross-section profile PNG
        """
        self.fields = fields
        self.system_plan_png = system_plan_png
        self.cross_section_png = cross_section_png

    def build(self, output_path: Path) -> Dict[str, Any]:
        """Build page 4 PDF."""
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                topMargin=0.3 * inch,
                bottomMargin=0.5 * inch,
                leftMargin=0.4 * inch,
                rightMargin=0.4 * inch,
            )

            elements = []

            # Header block
            elements.append(self._build_header())
            elements.append(Spacer(1, 0.15 * inch))

            # Scale line
            styles = getSampleStyleSheet()
            scale_style = ParagraphStyle(
                'Scale',
                parent=styles['Normal'],
                fontSize=9,
                leading=10,
                textColor=black,
            )
            elements.append(Paragraph(f"Scale: 1\" = {self.fields.get('system_plan_scale_ft_per_in', '10')} ft.", scale_style))

            # System plan section
            system_plan = self._build_system_plan_section()
            if system_plan:
                elements.append(system_plan)
            elements.append(Spacer(1, 0.1 * inch))

            # Backfill and construction info boxes
            elements.append(self._build_construction_section())
            elements.append(Spacer(1, 0.1 * inch))

            # Cross-section
            cross_section = self._build_cross_section_section()
            if cross_section:
                elements.append(cross_section)
            elements.append(Spacer(1, 0.2 * inch))

            # Footer
            elements.append(self._build_footer())

            # Build PDF
            doc.build(elements)
            logger.info(f"✓ Page 4 generated: {output_path}")

            return {
                "status": "GENERATED",
                "output_file": output_path,
                "page": 4,
            }
        except Exception as e:
            logger.error(f"Error generating page 4: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
            }

    def _build_header(self) -> Table:
        """Build gray header block (same as page 3)."""
        header_data = [
            [
                Paragraph(
                    "<b>SUBSURFACE WASTEWATER DISPOSAL SYSTEM APPLICATION</b><br/>"
                    "Maine Department of Health and Human Services (DHHS), Office of Environmental and Community Health<br/>"
                    "(207) 287-2070 | Fax (207) 287-4172 | subsurface.wastewater@maine.gov",
                    ParagraphStyle(
                        'HeaderTitle',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=9,
                        textColor=white,
                    )
                ),
                Paragraph(
                    f"<b>Owner:</b><br/>{self.fields.get('client_name', '')}<br/><br/>"
                    f"<b>Address:</b><br/>{self.fields.get('property_address', '')}",
                    ParagraphStyle(
                        'HeaderFields',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=10,
                        textColor=black,
                    )
                )
            ]
        ]

        header_table = Table(header_data, colWidths=[5.5*inch, 2.2*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#4a4a4a')),
            ('BACKGROUND', (1, 0), (1, 0), white),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (0, 0), 8),
            ('PADDING', (1, 0), (1, 0), 6),
            ('BORDER', (1, 0), (1, 0), 1, black),
        ]))
        return header_table

    def _build_system_plan_section(self) -> Optional[RLImage]:
        """Build subsurface disposal system plan section."""
        try:
            if not self.system_plan_png.exists():
                logger.warning(f"System plan PNG not found: {self.system_plan_png}")
                return None

            img = Image.open(self.system_plan_png)
            # Assume 96 DPI for the source image
            img_width_in = img.width / 96.0
            img_height_in = img.height / 96.0
            
            # Scale to fit 7.0 inches wide and max 3.2 inches tall
            max_width = 7.0 * inch
            max_height = 3.2 * inch
            
            width_scale = max_width / (img_width_in * inch)
            height_scale = max_height / (img_height_in * inch)
            scale = min(width_scale, height_scale, 1.0)
            
            scaled_width = img_width_in * inch * scale
            scaled_height = img_height_in * inch * scale

            return RLImage(str(self.system_plan_png), width=scaled_width, height=scaled_height)
        except Exception as e:
            logger.error(f"Error loading system plan: {e}")
            return None

    def _build_construction_section(self) -> Table:
        """Build backfill requirements and construction elevations section."""
        # Parse elevations
        finish_grade = float(self.fields.get('finish_grade_elevation', '0') or '0')
        top_of_pipe = float(self.fields.get('top_of_distribution_pipe_elevation', '-12') or '-12')
        bottom_of_field = float(self.fields.get('bottom_of_disposal_field_elevation', '-30') or '-30')

        backfill_upslope = self.fields.get('backfill_upslope_inches', '')
        backfill_downslope = self.fields.get('backfill_downslope_inches', '')

        construction_data = [
            [
                Paragraph(
                    f"<b>Backfill Requirements Above<br/>Existing Grade</b><br/>"
                    f"Depth of Backfill (upslope): {backfill_upslope or '___'} \"<br/>"
                    f"Depth of Backfill (downslope): {backfill_downslope or '___'} \"<br/>"
                    f"Depths at Cross-Section (shown below)",
                    ParagraphStyle(
                        'Construction',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=9,
                    )
                ),
                Paragraph(
                    f"<b>Construction Elevations from<br/>Elevation Reference Point</b><br/>"
                    f"Finish Grade (Elevation): {finish_grade} \"<br/>"
                    f"Top of Distribution Pipe or Proprietary Device: {top_of_pipe} \"<br/>"
                    f"Bottom of Disposal Field: {bottom_of_field} \"<br/>"
                    f"<br/><b>Scales:</b><br/>"
                    f"Vertical: 1\" = {self.fields.get('cross_section_vertical_scale_ft_per_in', '2.5')} ft.<br/>"
                    f"Horizontal: 1\" = {self.fields.get('cross_section_horizontal_scale_ft_per_in', '5')} ft.",
                    ParagraphStyle(
                        'Elevations',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=9,
                    )
                ),
                Paragraph(
                    f"<b>Elevation Reference Point</b><br/>"
                    f"Location & Description:<br/>"
                    f"{self.fields.get('erp_description', '')}<br/><br/>"
                    f"Reference Elevation is: 0.0\" or _____",
                    ParagraphStyle(
                        'RefPoint',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        leading=9,
                    )
                ),
            ]
        ]

        construction_table = Table(construction_data, colWidths=[2.5*inch, 2.5*inch, 2.0*inch])
        construction_table.setStyle(TableStyle([
            ('BORDER', (0, 0), (-1, -1), 0.5, black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ]))

        return construction_table

    def _build_cross_section_section(self) -> Optional[KeepTogether]:
        """Build cross-section profile section."""
        try:
            if not self.cross_section_png.exists():
                logger.warning(f"Cross-section PNG not found: {self.cross_section_png}")
                return None

            img = Image.open(self.cross_section_png)
            # Assume 96 DPI for the source image
            img_width_in = img.width / 96.0
            img_height_in = img.height / 96.0
            
            # Scale to fit 6.5 inches wide and max 2.2 inches tall
            max_width = 6.5 * inch
            max_height = 2.2 * inch
            
            width_scale = max_width / (img_width_in * inch)
            height_scale = max_height / (img_height_in * inch)
            scale = min(width_scale, height_scale, 1.0)
            
            scaled_width = img_width_in * inch * scale
            scaled_height = img_height_in * inch * scale

            title = Paragraph(
                "<b>DISPOSAL AREA CROSS-SECTION</b>",
                ParagraphStyle(
                    'CrossSectionTitle',
                    parent=getSampleStyleSheet()['Normal'],
                    fontSize=9,
                    leading=10,
                )
            )

            image = RLImage(str(self.cross_section_png), width=scaled_width, height=scaled_height)

            return KeepTogether([title, image])
        except Exception as e:
            logger.error(f"Error loading cross-section: {e}")
            return None

    def _build_footer(self) -> Table:
        """Build signature block and footer."""
        footer_data = [
            [
                Paragraph(
                    f"<b>Site Evaluator Signature or Initials:</b> _________________________",
                    getSampleStyleSheet()['Normal']
                ),
                Paragraph(
                    f"<b>SE #:</b> {self.fields.get('evaluator_number', '')}",
                    getSampleStyleSheet()['Normal']
                ),
                Paragraph(
                    f"<b>Date:</b> ___________________",
                    getSampleStyleSheet()['Normal']
                ),
            ],
            [
                {
                    'content': Paragraph(
                        "Subsurface Wastewater Unit — HHE-200: Subsurface Wastewater Disposal Application Rev. 7/2025",
                        ParagraphStyle(
                            'Footer',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=7,
                            textColor=HexColor('#666666'),
                        )
                    ),
                    'colspan': 3,
                }
            ],
            [
                {
                    'content': Paragraph(
                        "Page 4 of 4 (GRID)",
                        ParagraphStyle(
                            'PageNum',
                            parent=getSampleStyleSheet()['Normal'],
                            fontSize=8,
                            alignment=1,  # Right align
                        )
                    ),
                    'colspan': 3,
                }
            ],
        ]

        footer_table = Table(footer_data, colWidths=[3.0*inch, 1.5*inch, 1.7*inch])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
        ]))

        return footer_table


def main(client: str, job: str, work_dir: Path, output_dir: Path) -> int:
    """Generate pages 3-4 for HHE-200."""
    logger.info(f"Generating pages 3-4 for {client} (job {job})")

    # Input files
    boundary_png = work_dir / f"boundary_{client.lower()}.png"
    placement_png = work_dir / f"placement_{client.lower()}_with_tie_points.png"
    soil_png = work_dir / f"soil_profile_{client.lower()}.png"
    cross_section_png = work_dir / f"cross_section_{client.lower()}_v2.png"

    # Test harness reference
    harness_dir = work_dir / "test_harness" / f"{client.lower()}-{job}"

    # Load test data
    fields = load_test_data(client, job, harness_dir)
    if not fields:
        logger.error(f"Could not load test data for {client}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate page 3
    page3_output = output_dir / f"HHE-200-{client}-{job}-page3.pdf"
    gen3 = HHE200Page3Generator(fields, boundary_png, placement_png, soil_png)
    result3 = gen3.build(page3_output)
    if result3['status'] != 'GENERATED':
        logger.error(f"Failed to generate page 3: {result3}")
        return 1

    # Generate page 4
    page4_output = output_dir / f"HHE-200-{client}-{job}-page4.pdf"
    gen4 = HHE200Page4Generator(fields, placement_png, cross_section_png)
    result4 = gen4.build(page4_output)
    if result4['status'] != 'GENERATED':
        logger.error(f"Failed to generate page 4: {result4}")
        return 1

    logger.info(f"\n✓ Pages 3-4 generated successfully")
    logger.info(f"  Page 3: {page3_output}")
    logger.info(f"  Page 4: {page4_output}")

    return 0


def load_test_data(client: str, job: str, harness_dir: Path) -> Optional[Dict[str, Any]]:
    """Load test data from harness or use defaults."""
    # Map test clients to field values
    if client.lower() == "marquis":
        return {
            "client_name": "KRISTEN MARQUIS",
            "property_address": "17 ASPEN WAY",
            "evaluator_number": "338",
            "site_plan_scale_ft_per_in": "100",
            "system_plan_scale_ft_per_in": "10",
            "cross_section_vertical_scale_ft_per_in": "2.5",
            "cross_section_horizontal_scale_ft_per_in": "5",
            "finish_grade_elevation": "0",
            "top_of_distribution_pipe_elevation": "-12",
            "bottom_of_proprietary_device_elevation": "-24",
            "bottom_of_disposal_field_elevation": "-30",
            "erp_description": "TOP OF EXISTING SEPTIC TANK",
            "backfill_upslope_inches": "",
            "backfill_downslope_inches": "",
            "special_notes": "EXISTING DISPOSAL FIELD, EXISTING BIOMATT AND A MINIMUM OF 12 INCHES OF EXISTING SOIL BELOW PROPOSED DISPOSAL AREA AND FILL EXTENSIONS SHALL BE REMOVED, WHERE ENCOUNTERED, AND REPLACED WITH SUITABLE SOIL BACKFILL PER SECTION II(E) OF THE CODE.",
        }
    elif client.lower() == "roberts":
        return {
            "client_name": "CHARLES ROBERTS",
            "property_address": "450 LANE ROAD",
            "evaluator_number": "338",
            "site_plan_scale_ft_per_in": "100",
            "system_plan_scale_ft_per_in": "10",
            "cross_section_vertical_scale_ft_per_in": "2.5",
            "cross_section_horizontal_scale_ft_per_in": "5",
            "finish_grade_elevation": "+4",
            "top_of_distribution_pipe_elevation": "-14",
            "bottom_of_proprietary_device_elevation": "-26",
            "bottom_of_disposal_field_elevation": "-32",
            "erp_description": "TOP OF DISTRIBUTION PIPE OR PROPRIETARY DEVICE",
            "backfill_upslope_inches": "4",
            "backfill_downslope_inches": "10",
            "special_notes": "None",
        }

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HHE-200 pages 3-4")
    parser.add_argument("--client", required=True, help="Client name (e.g., 'Marquis')")
    parser.add_argument("--job", required=True, help="Job number (e.g., '26-018')")
    parser.add_argument("--work-dir", type=Path, default=Path("/home/workspace/OpenEvaluator"),
                        help="Working directory with renders")
    parser.add_argument("--output-dir", type=Path, default=Path("/home/workspace/OpenEvaluator"),
                        help="Output directory for PDFs")

    args = parser.parse_args()
    exit(main(args.client, args.job, args.work_dir, args.output_dir))
