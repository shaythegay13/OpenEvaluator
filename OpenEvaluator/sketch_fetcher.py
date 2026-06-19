#!/usr/bin/env python3
"""
Sketch Fetcher — Download sketches from Google Drive URLs

Extracts file ID from Google Drive URLs and downloads sketches for rendering.
"""

import re
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def extract_drive_file_id(url: str) -> Optional[str]:
    """
    Extract Google Drive file ID from various URL formats.

    Supported formats:
    - https://drive.google.com/open?id=XXX
    - https://drive.google.com/file/d/XXX/view
    - https://drive.google.com/file/d/XXX/view?usp=sharing
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # Format: /open?id=XXX
    if "drive.google.com/open" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "id" in params and params["id"]:
            return params["id"][0]

    # Format: /file/d/XXX/view
    if "drive.google.com/file/d/" in url:
        match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
        if match:
            return match.group(1)

    # Raw ID (if someone just passes the ID)
    if re.match(r'^[a-zA-Z0-9-_]+$', url) and len(url) > 20:
        return url

    logger.warning(f"Could not extract Drive file ID from: {url}")
    return None


def pdf_to_image(pdf_path: Path) -> Optional[Path]:
    """Convert a PDF to a PNG image (first page)."""
    try:
        from pdf2image import convert_from_path

        logger.info(f"Converting PDF to image: {pdf_path}")
        images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=150)

        if images:
            output_path = pdf_path.with_suffix(".png")
            images[0].save(str(output_path), "PNG")
            logger.info(f"✓ Converted to PNG: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to convert PDF: {e}")

    return None


def fetch_sketch_from_drive(url: str, output_dir: Path) -> Optional[Path]:
    """
    Download a sketch image from Google Drive via direct HTTP.

    Args:
        url: Google Drive URL
        output_dir: Where to save the downloaded image

    Returns:
        Path to downloaded image, or None if fetch failed
    """
    file_id = extract_drive_file_id(url)
    if not file_id:
        logger.error(f"Could not extract file ID from URL: {url}")
        return None

    logger.info(f"Fetching Google Drive file: {file_id}")

    try:
        import requests

        # Direct download URL for Google Drive files
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        response = requests.get(download_url, timeout=15, allow_redirects=True)

        if response.status_code == 200:
            # Detect file type from content and magic bytes
            content = response.content
            content_type = response.headers.get("content-type", "").lower()

            # Detect PDF (PDF files start with %PDF)
            if content.startswith(b"%PDF") or "pdf" in content_type:
                output_path = output_dir / f"sketch_{file_id}.pdf"
                logger.info(f"Downloaded as PDF: {output_path}")
            elif b"\x89PNG" in content[:10] or "png" in content_type:
                output_path = output_dir / f"sketch_{file_id}.png"
                logger.info(f"Downloaded as PNG")
            elif b"\xff\xd8\xff" in content[:10] or "jpeg" in content_type or "jpg" in content_type:
                output_path = output_dir / f"sketch_{file_id}.jpg"
                logger.info(f"Downloaded as JPEG")
            else:
                # Default to PNG
                output_path = output_dir / f"sketch_{file_id}.png"
                logger.info(f"Downloaded (format unknown, treating as PNG)")

            output_path.write_bytes(response.content)
            logger.info(f"✓ Downloaded: {output_path} ({len(content)} bytes)")

            # Convert PDF to PNG if needed
            if output_path.suffix == ".pdf":
                png_path = pdf_to_image(output_path)
                if png_path:
                    return png_path
                else:
                    logger.warning(f"Could not convert PDF to image, but returning PDF path")
                    return output_path

            return output_path
        else:
            logger.error(f"HTTP request failed with status {response.status_code}")
    except Exception as e:
        logger.error(f"Could not download sketch: {e}")

    return None


def fetch_sketch(url: str, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Main entry point: fetch a sketch and return its local path.

    Args:
        url: Google Drive URL or file ID
        output_dir: Optional directory to save in. Defaults to /tmp

    Returns:
        Path to downloaded image, or None if failed
    """
    if not url:
        logger.warning("No sketch URL provided")
        return None

    if output_dir is None:
        output_dir = Path("/tmp/hhe200_sketches")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching sketch from: {url}")
    return fetch_sketch_from_drive(url, output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch sketch from Google Drive")
    parser.add_argument("url", help="Google Drive URL")
    parser.add_argument("--output", type=Path, help="Output directory")
    args = parser.parse_args()

    result = fetch_sketch(args.url, args.output)
    if result:
        print(f"✓ Sketch saved to: {result}")
    else:
        print("✗ Failed to fetch sketch")
        exit(1)
