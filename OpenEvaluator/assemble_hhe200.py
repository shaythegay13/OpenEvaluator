#!/usr/bin/env python3
"""
Assemble a complete 4-page HHE-200 PDF from:
- Pages 1-2: AcroForm fills (from acro_fill.py)
- Page 3: Composite site plan (boundary + field + soil grid)
- Page 4: Cross-section elevation profile

Usage: python3 assemble_hhe200.py --client "Marquis" --job "26-018" --output-dir /path/to/output
"""
import argparse
import logging
from pathlib import Path
from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PyPDF2.generic import IndirectObject, NameObject
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def png_to_pdf(png_path: Path) -> BytesIO:
    """Convert PNG image to PDF bytes."""
    img = Image.open(png_path)
    
    # Convert RGBA to RGB if needed
    if img.mode == 'RGBA':
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3])
        img = rgb_img
    
    # Create PDF
    pdf_buffer = BytesIO()
    
    # Calculate page size to fit image at its natural DPI
    # Assume 300 DPI for rendered images
    dpi = 300
    width_inches = img.width / dpi
    height_inches = img.height / dpi
    page_size = (width_inches * inch, height_inches * inch)
    
    c = canvas.Canvas(pdf_buffer, pagesize=page_size)
    c.drawImage(png_path, 0, 0, width=page_size[0], height=page_size[1])
    c.save()
    
    pdf_buffer.seek(0)
    return pdf_buffer

def composite_page3(placement_png: Path, soil_png: Path) -> Path:
    """Composite page 3 from plan view and soil profile."""
    logger.info(f"Compositing page 3 from {placement_png.name} and {soil_png.name}")
    
    placement = Image.open(placement_png)
    soil = Image.open(soil_png)
    
    # Crop placement to 1800px height (reasonable for one page section)
    placement_height = 1800
    placement_cropped = placement.crop((0, 0, placement.width, placement_height))
    
    # Scale soil to match placement width
    soil_scaled = soil.resize(
        (placement_cropped.width, int(soil.height * placement_cropped.width / soil.width)),
        Image.Resampling.LANCZOS
    )
    
    # Composite: placement (top) + soil (bottom)
    composite_height = placement_cropped.height + soil_scaled.height
    composite = Image.new('RGB', (placement_cropped.width, composite_height), 'white')
    composite.paste(placement_cropped, (0, 0))
    composite.paste(soil_scaled, (0, placement_cropped.height))
    
    output_path = placement_png.parent / f"page3_{placement_png.stem.replace('placement_', '')}_composite.png"
    composite.save(output_path)
    logger.info(f"✓ Composite page 3: {output_path.name}")
    
    return output_path

def merge_pdfs(pages_1_2: Path, page3_pdf: BytesIO, page4_pdf: BytesIO, output_path: Path) -> None:
    """Merge all 4 pages into a single PDF, preserving AcroForm fields."""
    logger.info(f"Merging 4 pages into {output_path.name}")

    # Start with pages 1-2 as the base (contains AcroForm)
    reader_1_2 = PdfReader(pages_1_2)
    writer = PdfWriter()

    # Add only pages 1-2 from the filled PDF (which may have more pages)
    for page_num in range(min(2, len(reader_1_2.pages))):
        writer.add_page(reader_1_2.pages[page_num])

    # Manually copy AcroForm from source to writer
    # This must happen AFTER pages are added
    if "/AcroForm" in reader_1_2.trailer["/Root"]:
        # Get the AcroForm from source
        source_acroform = reader_1_2.trailer["/Root"]["/AcroForm"]

        # Add it to the writer's root using NameObject for the key
        writer._root_object[NameObject("/AcroForm")] = source_acroform

    # Add page 3 (rendered site plan)
    page3_reader = PdfReader(page3_pdf)
    writer.add_page(page3_reader.pages[0])

    # Add page 4 (cross-section)
    page4_reader = PdfReader(page4_pdf)
    writer.add_page(page4_reader.pages[0])

    # Write output
    with open(output_path, 'wb') as f:
        writer.write(f)

    logger.info(f"✓ Final PDF: {output_path}")

def main(client: str, job: str, work_dir: Path, output_dir: Path):
    """Assemble complete HHE-200 PDF."""
    
    # Find input files
    placement_png = work_dir / f"placement_{client.lower()}_with_tie_points.png"
    soil_png = work_dir / f"soil_profile_{client.lower()}.png"
    cross_section_png = work_dir / f"cross_section_{client.lower()}_v2.png"
    pages_1_2_pdf = work_dir / "HHE-200-filled.pdf"  # Assume this exists
    
    # Verify inputs exist
    if not pages_1_2_pdf.exists():
        logger.error(f"Pages 1-2 PDF not found: {pages_1_2_pdf}")
        return 1
    if not placement_png.exists():
        logger.error(f"Placement PNG not found: {placement_png}")
        return 1
    if not soil_png.exists():
        logger.error(f"Soil profile PNG not found: {soil_png}")
        return 1
    if not cross_section_png.exists():
        logger.error(f"Cross-section PNG not found: {cross_section_png}")
        return 1
    
    logger.info(f"Inputs verified:")
    logger.info(f"  Pages 1-2: {pages_1_2_pdf.name}")
    logger.info(f"  Page 3 plan: {placement_png.name}")
    logger.info(f"  Page 3 soil: {soil_png.name}")
    logger.info(f"  Page 4: {cross_section_png.name}")
    
    # Composite page 3
    page3_composite_png = composite_page3(placement_png, soil_png)
    
    # Convert pages 3-4 to PDF
    logger.info("Converting page 3 (composite) to PDF...")
    page3_pdf = png_to_pdf(page3_composite_png)
    
    logger.info("Converting page 4 (cross-section) to PDF...")
    page4_pdf = png_to_pdf(cross_section_png)
    
    # Merge all pages
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"HHE-200-{client}-{job}.pdf"
    merge_pdfs(pages_1_2_pdf, page3_pdf, page4_pdf, output_path)
    
    logger.info(f"\n✓ Assembly complete!")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Pages: 4 (1-2: AcroForm, 3: Site plan, 4: Cross-section)")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble HHE-200 PDF from components")
    parser.add_argument("--client", required=True, help="Client name (e.g., 'Marquis')")
    parser.add_argument("--job", required=True, help="Job number (e.g., '26-018')")
    parser.add_argument("--work-dir", type=Path, default=Path("/home/workspace/OpenEvaluator"),
                        help="Working directory with PNG renders")
    parser.add_argument("--output-dir", type=Path, default=Path("/home/workspace/OpenEvaluator"),
                        help="Output directory for final PDF")
    
    args = parser.parse_args()
    sys.exit(main(args.client, args.job, args.work_dir, args.output_dir))
