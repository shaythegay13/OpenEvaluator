#!/usr/bin/env python3
"""
DXF to PDF Converter
Converts AutoCAD DXF files to PDF for viewing final form output.
"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def convert_dxf_to_pdf(dxf_path: str, pdf_path: Optional[str] = None, timeout: int = 30) -> str:
    """
    Convert DXF file to PDF using LibreOffice.

    Args:
        dxf_path: Path to DXF file
        pdf_path: Output PDF path (default: same name, .pdf extension)
        timeout: Conversion timeout in seconds

    Returns:
        Path to generated PDF
    """
    dxf_path = Path(dxf_path)

    if not dxf_path.exists():
        raise FileNotFoundError(f"DXF file not found: {dxf_path}")

    pdf_path = Path(pdf_path) if pdf_path else dxf_path.with_suffix(".pdf")

    logger.info(f"Converting: {dxf_path.name} → {pdf_path.name}")

    try:
        # Use LibreOffice headless mode to convert
        # --convert-to format[:export_filter_options]
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(pdf_path.parent),
            str(dxf_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode != 0:
            logger.error(f"Conversion failed: {result.stderr}")
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

        # LibreOffice outputs to same name with .pdf extension
        libreoffice_output = dxf_path.with_suffix(".pdf")

        if libreoffice_output.exists() and libreoffice_output != pdf_path:
            libreoffice_output.rename(pdf_path)

        if not pdf_path.exists():
            raise RuntimeError(f"PDF not created at {pdf_path}")

        file_size = pdf_path.stat().st_size
        logger.info(f"✓ Converted successfully: {pdf_path.name} ({file_size:,} bytes)")

        return str(pdf_path)

    except subprocess.TimeoutExpired:
        logger.error(f"Conversion timeout after {timeout}s")
        raise
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise


def merge_pdfs(pdf_paths: List[str], output_path: str) -> str:
    """
    Merge multiple PDF files into one using PyPDF2.

    Args:
        pdf_paths: List of PDF file paths to merge (in order)
        output_path: Path to output merged PDF

    Returns:
        Path to merged PDF
    """
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        logger.warning("PyPDF2 not available, skipping merge. Install with: pip install PyPDF2")
        return pdf_paths[0] if pdf_paths else None

    logger.info(f"Merging {len(pdf_paths)} PDFs...")

    try:
        merger = PdfMerger()

        for pdf_path in pdf_paths:
            if Path(pdf_path).exists():
                logger.info(f"  Adding: {Path(pdf_path).name}")
                merger.append(str(pdf_path))

        merger.write(str(output_path))
        merger.close()

        file_size = Path(output_path).stat().st_size
        logger.info(f"✓ Merged successfully: {Path(output_path).name} ({file_size:,} bytes)")

        return str(output_path)

    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise


def convert_hhe200_dxf_to_pdf(dxf_folder: str = "./dwg_output") -> dict:
    """
    Convert all 4 HHE-200 DXF pages to PDF and merge into single document.

    Args:
        dxf_folder: Folder containing PG1.dxf, PG2.dxf, PG3.dxf, PG4.dxf

    Returns:
        dict with results
    """
    dxf_folder = Path(dxf_folder)

    if not dxf_folder.exists():
        logger.error(f"DXF folder not found: {dxf_folder}")
        return {}

    logger.info(f"\n{'='*70}")
    logger.info(f"HHE-200 DXF to PDF Conversion")
    logger.info(f"{'='*70}\n")

    results = {
        "folder": str(dxf_folder),
        "pages": {},
        "merged_pdf": None
    }

    # Convert each page
    page_pdfs = []
    for page_num in [1, 2, 3, 4]:
        dxf_file = dxf_folder / f"PG{page_num}_filled.dxf"

        if not dxf_file.exists():
            logger.warning(f"  Page {page_num}: DXF not found, skipping")
            results["pages"][f"page_{page_num}"] = {"status": "not_found"}
            continue

        try:
            pdf_file = dxf_folder / f"PG{page_num}_filled.pdf"
            pdf_path = convert_dxf_to_pdf(str(dxf_file), str(pdf_file))
            page_pdfs.append(pdf_path)
            results["pages"][f"page_{page_num}"] = {
                "status": "success",
                "dxf": str(dxf_file),
                "pdf": pdf_path,
                "size_bytes": Path(pdf_path).stat().st_size
            }
        except Exception as e:
            logger.error(f"  Page {page_num}: {e}")
            results["pages"][f"page_{page_num}"] = {"status": "failed", "error": str(e)}

    # Merge PDFs if all pages successful
    if len(page_pdfs) == 4:
        try:
            merged_path = dxf_folder / "HHE-200-FINAL.pdf"
            merged_pdf = merge_pdfs(page_pdfs, str(merged_path))
            results["merged_pdf"] = {
                "status": "success",
                "path": merged_pdf,
                "size_bytes": Path(merged_pdf).stat().st_size
            }
            logger.info(f"\n✓ FINAL OUTPUT: {merged_path}")
        except Exception as e:
            logger.warning(f"Merge failed: {e}")
            results["merged_pdf"] = {"status": "failed", "error": str(e)}
    else:
        logger.warning(f"Not all pages converted ({len(page_pdfs)}/4), skipping merge")

    return results


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Convert DXF to PDF")
    parser.add_argument("--dxf-folder", default="./dwg_output", help="Folder containing DXF files")
    parser.add_argument("--dxf-file", help="Single DXF file to convert")
    args = parser.parse_args()

    if args.dxf_file:
        # Convert single file
        try:
            pdf_path = convert_dxf_to_pdf(args.dxf_file)
            print(f"\n✓ Converted to: {pdf_path}")
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
    else:
        # Convert all HHE-200 pages
        results = convert_hhe200_dxf_to_pdf(args.dxf_folder)
        print(f"\n{json.dumps(results, indent=2)}")

        if results.get("merged_pdf", {}).get("status") == "success":
            print(f"\n✓ SUCCESS: View final output at: {results['merged_pdf']['path']}")
            sys.exit(0)
        else:
            sys.exit(1)
