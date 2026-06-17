#!/usr/bin/env python3
"""
Multi-Example Comparison Framework

Compares each of the 4 generated test cases against BOTH pinnacle examples.
This gives Hermes multiple reference points to identify its own faults in
document and drawing generation.

Strategy:
  - Each generated PDF (rows 2-5) is compared to example 1 AND example 2
  - Hermes can identify patterns across multiple perfect outputs
  - Better learning signal for improvement areas
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime
import os

os.chdir("/home/workspace/OpenEvaluator")

# Test cases: all 4 rows
TEST_CASES = [
    {"row": 2, "name": "26-018 (Kristen Marquis - Live Data)", "is_live": True},
    {"row": 3, "name": "Synthetic Test 1 (George)", "is_live": False},
    {"row": 4, "name": "Synthetic Test 2 (George)", "is_live": False},
    {"row": 5, "name": "Unknown (Live Data)", "is_live": True},
]

# Both examples for comparison
EXAMPLES = [
    {"folder": "example 1", "pages": ["PG1", "PG2", "PG3", "PG4"], "prefix": "26-018"},
    {"folder": "example 2", "pages": ["PG1", "PG2", "PG3", "PG4"], "prefix": "26-123"},
]

def get_example_pages(example_folder):
    """Get all PDF pages from example folder"""
    example_dir = Path("example") / example_folder
    if not example_dir.exists():
        return []

    pdfs = sorted(example_dir.glob("*.pdf"))
    return pdfs

def get_generated_pdf(row_num):
    """Get generated PDF for a row"""
    # Find latest test results
    results_dir = Path("test_results")
    if not results_dir.exists():
        return None

    latest = sorted(results_dir.iterdir())[-1]
    pdf = latest / f"row_{row_num}" / f"HHE-200-row{row_num}.pdf"

    return pdf if pdf.exists() else None

def compare_generated_to_examples(row_num, generated_pdf):
    """Compare a generated PDF to both examples"""
    comparison = {
        "row": row_num,
        "generated_pdf": str(generated_pdf),
        "vs_examples": []
    }

    for example in EXAMPLES:
        example_folder = example["folder"]
        example_pages = get_example_pages(example_folder)

        example_info = {
            "example_folder": example_folder,
            "example_pages": [str(p) for p in example_pages],
            "page_count": len(example_pages),
            "comparison_status": "ready" if len(example_pages) > 0 else "example_not_found"
        }

        comparison["vs_examples"].append(example_info)

    return comparison

def main():
    print(f"\n{'='*80}")
    print(f"MULTI-EXAMPLE COMPARISON FRAMEWORK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    print("📊 Comparison Strategy:")
    print("  • All 4 generated test cases compared to BOTH pinnacle examples")
    print("  • Provides multiple reference points for Hermes learning")
    print("  • Helps identify common fault patterns across document/drawing generation\n")

    all_comparisons = {
        "timestamp": datetime.now().isoformat(),
        "strategy": "multi_example_learning",
        "comparisons": []
    }

    # Process each test case
    for test_case in TEST_CASES:
        row = test_case["row"]
        name = test_case["name"]
        is_live = test_case["is_live"]

        print(f"\n{'─'*80}")
        print(f"Row {row}: {name}")
        if is_live:
            print(f"  ⭐ LIVE DATA (pinnacle examples available)")
        else:
            print(f"  🔷 Synthetic data (baseline testing)")
        print(f"{'─'*80}")

        # Get generated PDF
        gen_pdf = get_generated_pdf(row)
        if not gen_pdf:
            print(f"  ✗ Generated PDF not found")
            continue

        print(f"  Generated: {gen_pdf.name}")

        # Compare to both examples
        comparison = compare_generated_to_examples(row, str(gen_pdf))

        for ex_comp in comparison["vs_examples"]:
            example = ex_comp["example_folder"]
            page_count = ex_comp["page_count"]

            if page_count > 0:
                print(f"\n  vs {example}:")
                print(f"    Pages to compare: {page_count}")
                for page in ex_comp["example_pages"]:
                    print(f"      • {Path(page).name}")
                print(f"    Status: ✅ Ready for comparison")
            else:
                print(f"\n  vs {example}: ⚠️ Example folder not found")

        all_comparisons["comparisons"].append(comparison)

    # Print summary
    print(f"\n{'='*80}")
    print(f"COMPARISON FRAMEWORK SUMMARY")
    print(f"{'='*80}\n")

    total_comparisons = len(all_comparisons["comparisons"]) * len(EXAMPLES)
    print(f"Total comparisons to evaluate: {total_comparisons}")
    print(f"  • 4 generated PDFs × 2 example folders = 8 comparison pairs\n")

    print("Comparison Matrix:")
    print("\n  Row | Type | vs Example 1 | vs Example 2")
    print("  ─────────────────────────────────────────")
    for comp in all_comparisons["comparisons"]:
        row = comp["row"]
        test_case = next((tc for tc in TEST_CASES if tc["row"] == row), {})
        type_label = "Live" if test_case.get("is_live") else "Syn"

        status1 = "✅" if comp["vs_examples"][0]["page_count"] > 0 else "❌"
        status2 = "✅" if comp["vs_examples"][1]["page_count"] > 0 else "❌"

        print(f"  {row}  | {type_label}  | {status1}             | {status2}")

    print(f"\n{'='*80}")
    print(f"EVALUATION FOCUS AREAS")
    print(f"{'='*80}\n")

    print("""For each generated PDF vs each example, evaluate:

1. **Pages 1-2: Form Field Accuracy**
   - Field population completeness
   - Data accuracy (owner, address, property info, soil data, system specs)
   - Formatting and alignment
   - Font consistency

   Learning from both examples:
     • Example 1 shows format for property 26-018
     • Example 2 shows format for property 26-123
     • Hermes should identify which fields are consistently populated correctly

2. **Page 3: Site Plan Drawing Quality**
   - Property boundary and corner markings
   - House, tank, field positioning
   - Observation hole placement and labeling
   - Distance callouts and annotations
   - Scale notation and grid
   - Adjacent property labeling

   Learning from both examples:
     • Both examples show professional site plan layouts
     • Hermes can identify sizing patterns, annotation styles, element spacing
     • Spot differences in detail level, label placement, dimension precision

3. **Page 4: Disposal Plan & Cross-Section**
   - Tank/D-box positioning and sizing
   - Field module arrangement and dimensions
   - Cross-section soil layer detail
   - Elevation reference markings
   - Dimension strings and callouts

   Learning from both examples:
     • Both show professional disposal system layouts
     • Can identify consistent patterns across different properties
     • Spot areas where generated drawings diverge from professional standard

4. **Overall Professional Quality**
   - Visual polish and presentation
   - Line weights and styles consistency
   - Color fills and patterns
   - Text clarity and hierarchy
   - Professional appearance overall
""")

    print(f"\n{'='*80}")
    print(f"SCORING APPROACH FOR HERMES LEARNING")
    print(f"{'='*80}\n")

    print("""For each generated PDF vs example pair:

1. **Extract & Catalog Differences**
   Example format:
     Row 2 vs Example 1:
       ✓ Page 1: Owner name correct, address correct
       ✗ Page 1: Soil depth field empty
       ✓ Page 3: Site plan layout matches overall structure
       ~ Page 3: Tank sizing off by ~2%
       ✗ Page 4: Field module rows incorrect (showing 2, should be 3)

2. **Score Each Page**
   Excellent (90-100%): Near-perfect match with example
   Good (75-89%): Strong match, minor differences
   Fair (60-74%): Basic structure correct, notable differences
   Needs Work (<60%): Significant divergence from example

3. **Identify Patterns**
   After comparing all 4 generated PDFs to both examples:
     • Which issues appear consistently? → High priority
     • Which only appear in certain properties? → May be data-specific
     • What's the biggest quality gap? → Where to start improvements

4. **Prioritize Improvements**
   Based on frequency and impact:
     Tier 1: Issues in ALL comparisons (pages, drawing elements, styling)
     Tier 2: Issues in MOST comparisons (common fault patterns)
     Tier 3: Issues in SOME comparisons (edge cases, property-specific)
""")

    # Save comparison framework
    framework_file = Path("test_results") / "multi_example_framework.json"
    framework_file.parent.mkdir(exist_ok=True)

    with open(framework_file, "w") as f:
        json.dump(all_comparisons, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Framework saved: {framework_file}\n")

if __name__ == "__main__":
    main()
