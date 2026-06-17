#!/usr/bin/env python3
"""
run_parser.py — Parse the Google Sheet row and fill the HHE-200 PDF.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Add OpenEvaluator to path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from sheet_parser import build_field_dict, OUTPUT_PDF
from fill_form import fill_form

def main():
    print("Step 1 — Parsing Google Sheet row…")
    fields = build_field_dict()

    print(f"\n{'='*60}")
    print(f"Parsed field dictionary — {len(fields)} fields")
    print(f"{'='*60}")
    for k, v in fields.items():
        if v:  # only show non-empty
            print(f"  {k:<45} = {v!r}")
    print()

    print("Step 2 — Filling HHE-200-filled.pdf…")
    out_path = fill_form(fields, output_path=str(OUTPUT_PDF))
    print(f"  ✓  Saved → {out_path}")

    print("\nStep 3 — Verifying with pdfplumber (pages 1–2)…")
    try:
        import pdfplumber
        with pdfplumber.open(out_path) as pdf:
            for page_num in [0, 1]:  # 0-indexed
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                print(f"\n{'='*60}")
                print(f"PAGE {page_num + 1} — ALL TEXT FOUND")
                print(f"{'='*60}")
                if text.strip():
                    print(text)
                else:
                    print("(no text extracted — may be image-based)")
                # Also show words
                words = page.extract_words()
                if words:
                    print("\nWords extracted:")
                    for w in words:
                        print(f"  [{w['x0']:.1f}, {w['top']:.1f}] {w['text']!r}")
    except ImportError:
        print("  pdfplumber not installed — skipping verification")
        print("  Install with: pip install pdfplumber")

if __name__ == "__main__":
    main()