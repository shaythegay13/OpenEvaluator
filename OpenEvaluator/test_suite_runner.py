#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for HHE-200 Generator

Processes all 4 test cases from Google Sheet:
  - Rows 2-3: Synthetic test data (from George)
  - Rows 4-5: Real example data (with pinnacle PDFs in examples folder)

Generates PDFs for each and scores against pinnacle examples.
"""
import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

os.chdir("/home/workspace/OpenEvaluator")

RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(exist_ok=True)

# Test case mappings (row_number -> example_folder_name)
TEST_CASES = {
    2: None,  # Synthetic test 1 (George)
    3: None,  # Synthetic test 2 (George)
    4: "example 1",  # Real example 26-018 (Kristen Marquis)
    5: "example 2",  # Real example 26-123
}

def run_command(cmd, description=""):
    """Run a command and return result"""
    print(f"\n  {'→' if description else '  '} {description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/home/workspace/OpenEvaluator"
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)

def extract_sketch_data(row_number):
    """Extract sketch data for a specific row using Hermes"""
    print(f"\n{'='*80}")
    print(f"PROCESSING ROW {row_number}")
    print(f"{'='*80}")

    # Create row-specific output directory
    row_dir = RESULTS_DIR / f"row_{row_number}"
    row_dir.mkdir(exist_ok=True)

    print(f"\nStep 1: Extract sketch data using Hermes")

    # Run the sketch extractor for this specific row
    # The sketch_extractor.py extracts data from the drawing file in column T
    cmd = [
        sys.executable, "sketch_extractor.py",
        "--row", str(row_number),
        "--output-dir", str(row_dir)
    ]

    success, output = run_command(cmd, "Running sketch extractor")

    if not success:
        print(f"\n  ✗ Sketch extraction failed: {output[:200]}")
        return False

    print(f"  ✓ Sketch extraction complete")

    # Check if hermes_output.json was created
    hermes_file = row_dir / "hermes_output.json"
    if not hermes_file.exists():
        print(f"  ✗ hermes_output.json not found")
        return False

    # Copy hermes_output.json to root for pipeline
    shutil.copy(hermes_file, "hermes_output.json")
    print(f"  ✓ hermes_output.json created")

    return True

def run_fill_form():
    """Fill the PDF form using hermes data"""
    print(f"\nStep 2: Generate HHE-200 form")

    cmd = [sys.executable, "fill_form.py"]
    success, output = run_command(cmd, "Filling PDF form")

    if not success:
        print(f"  ✗ Form generation failed: {output[:200]}")
        return False

    print(f"  ✓ Form generated")
    return True

def collect_outputs(row_number):
    """Collect generated PDFs and images"""
    print(f"\nStep 3: Collect outputs")

    row_dir = RESULTS_DIR / f"row_{row_number}"
    row_dir.mkdir(exist_ok=True)

    # Copy generated PDF
    pdf_file = Path("HHE-200-filled.pdf")
    if pdf_file.exists():
        dest = row_dir / "HHE-200-filled.pdf"
        shutil.copy(pdf_file, dest)
        print(f"  ✓ PDF copied to {dest.name}")

    # Copy generated images
    for img_file in Path(".").glob("*pg*.png"):
        dest = row_dir / img_file.name
        shutil.copy(img_file, dest)
        print(f"  ✓ Image copied to {img_file.name}")

    return True

def score_against_examples(row_number, example_folder):
    """Score generated PDFs against example PDFs"""
    if not example_folder:
        print(f"\nStep 4: Scoring")
        print(f"  (No example folder configured for Row {row_number} - skipping comparison)")
        return None

    print(f"\nStep 4: Score against example folder: {example_folder}")

    row_dir = RESULTS_DIR / f"row_{row_number}"
    example_dir = Path("example") / example_folder

    # Compare Page 1-4 PDFs
    pages_to_compare = [1, 2, 3, 4]
    scores = {}

    for page in pages_to_compare:
        gen_pdf = row_dir / "HHE-200-filled.pdf"
        example_pdf = list(example_dir.glob(f"*PG{page}*.pdf"))

        if not example_pdf:
            print(f"  ? Page {page}: No example PDF found")
            continue

        example_pdf = example_pdf[0]

        if not gen_pdf.exists():
            print(f"  ✗ Page {page}: Generated PDF not found")
            continue

        # For now, just check file existence
        # TODO: Implement actual PDF comparison (visual similarity, field comparison, etc.)
        print(f"  ✓ Page {page}: Generated vs {example_pdf.name}")
        scores[f"page_{page}"] = "generated"

    return scores

def main():
    """Run test suite"""
    print(f"\n{'='*80}")
    print(f"HHE-200 COMPREHENSIVE TEST SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "total_rows": len(TEST_CASES),
        "rows_processed": 0,
        "rows_successful": 0,
        "results_by_row": {}
    }

    for row_number, example_folder in TEST_CASES.items():
        row_results = {
            "row": row_number,
            "example_folder": example_folder,
            "extraction": False,
            "form_generation": False,
            "outputs_collected": False,
            "score": None
        }

        # Step 1: Extract sketch data
        if extract_sketch_data(row_number):
            row_results["extraction"] = True
        else:
            print(f"✗ Row {row_number} failed at extraction")
            results_summary["results_by_row"][f"row_{row_number}"] = row_results
            continue

        # Step 2: Generate form
        if run_fill_form():
            row_results["form_generation"] = True
        else:
            print(f"✗ Row {row_number} failed at form generation")
            results_summary["results_by_row"][f"row_{row_number}"] = row_results
            continue

        # Step 3: Collect outputs
        if collect_outputs(row_number):
            row_results["outputs_collected"] = True

        # Step 4: Score against examples
        score = score_against_examples(row_number, example_folder)
        row_results["score"] = score

        # Count successes
        results_summary["rows_processed"] += 1
        if row_results["extraction"] and row_results["form_generation"]:
            results_summary["rows_successful"] += 1

        results_summary["results_by_row"][f"row_{row_number}"] = row_results

        print(f"\n✓ Row {row_number} complete")

    # Print summary
    print(f"\n{'='*80}")
    print(f"TEST SUITE SUMMARY")
    print(f"{'='*80}")
    print(f"Rows processed: {results_summary['rows_processed']}/{results_summary['total_rows']}")
    print(f"Rows successful: {results_summary['rows_successful']}/{results_summary['total_rows']}")
    print(f"Results saved to: {RESULTS_DIR}")

    # Save results to JSON
    results_file = RESULTS_DIR / "summary.json"
    with open(results_file, "w") as f:
        json.dump(results_summary, f, indent=2)
    print(f"Results JSON: {results_file}")

    return results_summary

if __name__ == "__main__":
    summary = main()
    sys.exit(0 if summary["rows_successful"] == summary["total_rows"] else 1)
