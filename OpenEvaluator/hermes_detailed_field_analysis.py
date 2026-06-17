#!/usr/bin/env python3
"""
Detailed field analysis - identifies exactly which fields are populated and which are empty.
"""

import fitz
from pathlib import Path

def analyze_pdf_fields(pdf_path):
    """Extract all form fields and their values from a PDF."""
    doc = fitz.open(str(pdf_path))
    
    results = {}
    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_key = f"page_{page_num + 1}"
        results[page_key] = {
            "page_num": page_num + 1,
            "filled_fields": [],
            "empty_fields": [],
            "total_fields": 0,
        }
        
        widgets = list(page.widgets())
        results[page_key]["total_fields"] = len(widgets)
        
        for widget in widgets:
            field_name = widget.field_name or "UNNAMED"
            field_value = widget.field_value or ""
            
            if field_value and str(field_value).strip():
                results[page_key]["filled_fields"].append({
                    "name": field_name,
                    "value": str(field_value)[:50]
                })
            else:
                results[page_key]["empty_fields"].append(field_name)
    
    doc.close()
    return results

def main():
    pdf_path = Path("test_results/row_2/HHE-200-row2.pdf")
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return
    
    print("=" * 80)
    print(f"DETAILED FIELD ANALYSIS: {pdf_path.name}")
    print("=" * 80)
    
    results = analyze_pdf_fields(pdf_path)
    
    for page_key, page_data in sorted(results.items()):
        page_num = page_data["page_num"]
        filled = len(page_data["filled_fields"])
        empty = len(page_data["empty_fields"])
        total = page_data["total_fields"]
        
        print(f"\nPage {page_num}: {filled} filled, {empty} empty, {total} total")
        print("-" * 80)
        
        if page_data["filled_fields"]:
            print(f"✓ FILLED FIELDS ({len(page_data['filled_fields'])}):")
            for field in page_data["filled_fields"][:10]:
                print(f"    {field['name']}: {field['value']}")
            if len(page_data["filled_fields"]) > 10:
                print(f"    ... and {len(page_data['filled_fields']) - 10} more")
        
        if page_data["empty_fields"]:
            print(f"\n✗ EMPTY FIELDS ({len(page_data['empty_fields'])}):")
            for field_name in page_data["empty_fields"][:10]:
                print(f"    {field_name}")
            if len(page_data["empty_fields"]) > 10:
                print(f"    ... and {len(page_data['empty_fields']) - 10} more")
    
    # Save detailed analysis
    import json
    with open("test_results/hermes_field_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed analysis saved to test_results/hermes_field_analysis.json")

if __name__ == "__main__":
    main()
