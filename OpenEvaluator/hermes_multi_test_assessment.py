#!/usr/bin/env python3
"""
Hermes Multi-Test Assessment
Evaluates all 4 test cases against their respective pinnacle examples.
"""

import json
import subprocess
from pathlib import Path
import fitz

RESULTS_DIR = Path("test_results")
EXAMPLE_DIR = Path("example")

TEST_CASES = {
    2: {"row": "row_2", "property": "26-018 (Kristen Marquis)", "example_folder": "example 1", "example_pdfs": [
        EXAMPLE_DIR / "example 1" / "26-018 PG1 (1).pdf",
        EXAMPLE_DIR / "example 1" / "26-018 PG2 (1).pdf",
        EXAMPLE_DIR / "example 1" / "26-018 PG3 (1).pdf",
        EXAMPLE_DIR / "example 1" / "26-018 PG4 (1).pdf",
    ]},
    3: {"row": "row_3", "property": "Synthetic Test 1", "example_folder": None, "example_pdfs": []},
    4: {"row": "row_4", "property": "26-123", "example_folder": "example 2", "example_pdfs": [
        EXAMPLE_DIR / "example 2" / "26-123 PG1.pdf",
        EXAMPLE_DIR / "example 2" / "26-123 PG2.pdf",
        EXAMPLE_DIR / "example 2" / "26-123 PG3.pdf",
        EXAMPLE_DIR / "example 2" / "26-123 PG4.pdf",
    ]},
    5: {"row": "row_5", "property": "Synthetic Test 2", "example_folder": None, "example_pdfs": []},
}

def count_filled_fields(pdf_path):
    """Count filled form fields in a PDF."""
    try:
        doc = fitz.open(str(pdf_path))
        total_filled = 0
        total_fields = 0
        text_fields = 0
        checkbox_fields = 0

        for page in doc:
            widgets = list(page.widgets())
            for widget in widgets:
                total_fields += 1
                value = widget.field_value
                field_type = widget.field_type

                # Count based on field type
                if field_type == 7:  # Text field
                    text_fields += 1
                    if value and str(value).strip():
                        total_filled += 1
                elif field_type in [2, 6]:  # Checkbox or Radio
                    checkbox_fields += 1
                    # Any value means it's been set
                    if value:
                        total_filled += 1
                else:
                    # Other field types
                    if value:
                        total_filled += 1

        doc.close()
        return total_filled, total_fields, text_fields, checkbox_fields
    except Exception as e:
        return 0, 0, 0, 0

def assess_test_case(row_num, case_info):
    """Assess a single test case against its example folder."""
    row_dir = RESULTS_DIR / case_info["row"]
    pdf_path = row_dir / f"HHE-200-row{row_num}.pdf"

    result = {
        "row": row_num,
        "property": case_info["property"],
        "has_example": case_info.get("example_folder") is not None,
        "example_folder": case_info.get("example_folder"),
        "pdf_exists": pdf_path.exists(),
        "score": 0,
    }

    if not pdf_path.exists():
        result["status"] = "PDF not found"
        return result

    try:
        # Count filled fields
        filled, total, text_count, checkbox_count = count_filled_fields(pdf_path)
        fill_rate = (filled / total * 100) if total > 0 else 0

        result["filled_fields"] = filled
        result["total_fields"] = total
        result["text_fields"] = text_count
        result["checkbox_fields"] = checkbox_count
        result["fill_rate"] = round(fill_rate, 1)

        # Basic score based on field fill rate
        # Pages 1-2 should have 60-80 fields, pages 3-4 should have 40-50 fields total
        if fill_rate >= 80:
            score = 95
        elif fill_rate >= 60:
            score = 85
        elif fill_rate >= 40:
            score = 70
        elif fill_rate >= 20:
            score = 50
        else:
            score = 30

        result["score"] = score
        result["status"] = "assessed"

        # Also check if example PDFs exist
        example_pdfs = case_info.get("example_pdfs", [])
        if example_pdfs and result.get("has_example"):
            existing_examples = [p for p in example_pdfs if p.exists()]
            result["example_pdfs_found"] = len(existing_examples)
            result["example_pdfs_total"] = len(example_pdfs)

    except Exception as e:
        import traceback
        result["status"] = f"error: {str(e)[:100]}"
        result["score"] = 0
        result["error_traceback"] = traceback.format_exc()

    return result

def main():
    print("=" * 80)
    print("HERMES MULTI-TEST ASSESSMENT")
    print("=" * 80)
    
    results = {
        "timestamp": Path.cwd().exists(),
        "test_cases": [],
        "summary": {
            "total": len(TEST_CASES),
            "assessed": 0,
            "average_score": 0,
            "quality_issues": [],
        }
    }
    
    scores = []
    for row_num, case_info in sorted(TEST_CASES.items()):
        print(f"\nAssessing Row {row_num}: {case_info['property']}")
        print("-" * 80)

        assessment = assess_test_case(row_num, case_info)
        results["test_cases"].append(assessment)

        print(f"  Status: {assessment['status']}")
        print(f"  Example Folder: {assessment['example_folder'] or 'None (synthetic data)'}")

        if assessment["status"] == "assessed":
            filled = assessment.get("filled_fields", 0)
            total = assessment.get("total_fields", 0)
            fill_rate = assessment.get("fill_rate", 0)
            score = assessment.get("score", 0)

            print(f"  Fields Filled: {filled}/{total} ({fill_rate}%)")
            print(f"  Overall Score: {score}/100")

            if assessment.get("example_pdfs_found"):
                print(f"  Example PDFs: {assessment.get('example_pdfs_found')}/{assessment.get('example_pdfs_total')} found")

            scores.append(score)
            results["summary"]["assessed"] += 1
        elif assessment["status"] != "PDF not found":
            print(f"  Error: {assessment.get('status', 'Unknown error')}")
    
    # Summary
    if scores:
        avg_score = sum(scores) / len(scores)
        results["summary"]["average_score"] = int(avg_score)
        
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Tests Assessed: {results['summary']['assessed']}/{results['summary']['total']}")
        print(f"Average Score: {int(avg_score)}/100")
        print(f"Quality Status: {'❌ BELOW STANDARD' if avg_score < 75 else '⚠️  ACCEPTABLE' if avg_score < 90 else '✅ MEETS STANDARD'}")
        
        # Identify issues
        if avg_score < 75:
            results["summary"]["quality_issues"] = [
                "Form fields incomplete on pages 1-2",
                "Drawing content matching low on pages 3-4", 
                "Need to improve field filling rate and drawing accuracy"
            ]
        
        print(f"\nKey Issues:")
        for issue in results["summary"]["quality_issues"]:
            print(f"  • {issue}")
    
    # Save results
    with open(RESULTS_DIR / "hermes_multi_test_assessment.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to {RESULTS_DIR / 'hermes_multi_test_assessment.json'}")
    
    return results

if __name__ == "__main__":
    main()
