"""Extract text elements with coordinates from HHE-200-2025.pdf using pdfplumber."""

import json
import pdfplumber
from pathlib import Path

PDF_PATH = "/home/workspace/OpenEvaluator/HHE-200-2025.pdf"
OUTPUT_PATH = Path("/home/workspace/OpenEvaluator/field_coordinates.json")


def extract_page_elements(page, page_num: int) -> list[dict]:
    """Extract all text elements with coordinates from a single page."""
    elements = []

    # Get page dimensions
    page_width = float(page.width)
    page_height = float(page.height)

    # Extract characters (more granular than words)
    chars = page.chars
    if not chars:
        return elements

    # Group characters by approximate position to form text blocks
    # We'll use pdfplumber's built-in物业管理
    words = page.extract_words()

    for word in words:
        elements.append({
            "text": word.get("text", ""),
            "x": round(word.get("x0", 0.0), 3),
            "y": round(word.get("top", 0.0), 3),
            "width": round(word.get("x1", 0.0) - word.get("x0", 0.0), 3),
            "height": round(word.get("bottom", 0.0) - word.get("top", 0.0), 3),
            "page_width": round(page_width, 3),
            "page_height": round(page_height, 3),
        })

    return elements


def main():
    result = {}

    with pdfplumber.open(PDF_PATH) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_key = f"page_{i}"
            elements = extract_page_elements(page, i)
            result[page_key] = elements

            unique_texts = set(el["text"] for el in elements)
            print(f"{page_key}: {len(elements)} text elements, {len(unique_texts)} unique")

    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\nSaved to {OUTPUT_PATH}")
    print(f"Total pages: {len(result)}")
    print(f"Total elements: {sum(len(v) for v in result.values())}")


if __name__ == "__main__":
    main()