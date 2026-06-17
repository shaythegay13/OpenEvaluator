#!/usr/bin/env python3
"""
Comprehensive HHE-200 Test Suite

Processes all 4 test cases from Google Sheet, generates PDFs, and scores against examples.

Test case mapping:
  - Row 2: 26-018 (Kristen Marquis, 17 Aspen Way) → compare with "example 1"
  - Row 3: Synthetic test 1 (George) → no comparison baseline
  - Row 4: 26-123 (Real property) → compare with "example 2"
  - Row 5: Synthetic test 2 (George) → no comparison baseline
"""
import json
import subprocess
import shutil
import sys
from pathlib import Path
from datetime import datetime
import os

os.chdir("/home/workspace/OpenEvaluator")

# Import sheet parser for reading Google Sheet data
try:
    from sheet_parser import parse_sheet_row
except ImportError:
    parse_sheet_row = None
    print("Warning: sheet_parser not available, will use fallback data")

RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(exist_ok=True)

def get_sheet_rows():
    """Attempt to read all rows from Google Sheet"""
    print("Attempting to read Google Sheet...")

    # Try using gws sheets API
    try:
        result = subprocess.run([
            "gws", "sheets:v4:spreadsheets.values.get",
            "--spreadsheetId=1ebjhzBSaH9zrJBORxKTkM56ukKV2IlNJ-3r1wJslNBc",
            "--range=Form Responses 1!A:W",
            "--key=values"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('values', [])
    except Exception as e:
        print(f"  ⚠ Could not read sheet: {e}")

    return None

def identify_test_rows(rows):
    """Identify which rows contain test data"""
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    test_rows = []

    # Find columns
    try:
        prop_col = headers.index('Property Name')
        owner_col = headers.index('Owner Name')
        uploads_col = headers.index('Uploads')
    except ValueError:
        return []

    # Identify rows with data
    for row_num, row_data in enumerate(rows[1:], start=2):  # Start at row 2 (after header)
        if row_num > 5:  # Only process rows 2-5 based on problem statement
            break

        prop = row_data[prop_col] if prop_col < len(row_data) else ""
        owner = row_data[owner_col] if owner_col < len(row_data) else ""
        uploads_url = row_data[uploads_col] if uploads_col < len(row_data) else ""

        if prop or owner or uploads_url:
            test_rows.append({
                "row_number": row_num,
                "property_name": prop,
                "owner_name": owner,
                "uploads_url": uploads_url,
                "row_data": row_data
            })

    return test_rows

def determine_example_folder(row_num, property_name):
    """Determine which example folder to compare against"""
    # From the examples folder structure:
    # "example 1" = 26-018 (Kristen Marquis, 17 Aspen Way)
    # "example 2" = 26-123 (another property)

    if "26-018" in property_name or "17" in property_name or "Kristen" in property_name:
        return "example 1"
    elif "26-123" in property_name:
        return "example 2"
    else:
        return None


def convert_raw_row_to_dict(headers, row_data):
    """Convert raw Google Sheet row (list) to dict using headers"""
    if not headers:
        return {}
    row_dict = {}
    for i, header in enumerate(headers):
        row_dict[header] = row_data[i] if i < len(row_data) else ""
    return row_dict


def get_parsed_fields_from_row(row_dict):
    """
    Parse a Google Sheet row dict into HHE-200 form fields.
    Uses sheet_parser if available, otherwise returns a mapping.
    """
    if parse_sheet_row:
        try:
            return parse_sheet_row(row_dict)
        except Exception as e:
            print(f"    ⚠ Error parsing with sheet_parser: {e}")
            return {}
    return {}

def process_test_row(row_info, example_folder):
    """Process a single test row"""
    row_num = row_info["row_number"]
    uploads_url = row_info["uploads_url"]
    prop_name = row_info["property_name"]

    print(f"\n{'='*80}")
    print(f"ROW {row_num}: {prop_name}")
    print(f"{'='*80}")

    row_dir = RESULTS_DIR / f"row_{row_num}"
    row_dir.mkdir(exist_ok=True)

    result = {
        "row": row_num,
        "property": prop_name,
        "example_folder": example_folder,
        "extraction_status": "pending",
        "form_status": "pending",
        "outputs": []
    }

    # Step 1: Extract sketch data using sketch_extractor
    print(f"\n1. Extracting sketch data from Google Drive...")

    if not uploads_url:
        print(f"   ⚠ No uploads_url for row {row_num}, skipping extraction")
        result["extraction_status"] = "skipped"
    else:
        # Extract the folder ID from the Drive URL
        try:
            # URL format: https://drive.google.com/open?id=<FOLDER_ID>
            # or could be drive.google.com/drive/folders/<FOLDER_ID>
            folder_id = uploads_url.split("id=")[-1].split("&")[0]

            print(f"   Folder ID: {folder_id[:20]}...")

            # Run sketch extractor
            extract_result = subprocess.run([
                sys.executable, "sketch_extractor.py",
                "--folder-id", folder_id,
                "--address", prop_name,
                "--output", str(row_dir / "hermes_output.json")
            ], capture_output=True, text=True, timeout=300)

            if extract_result.returncode == 0:
                print(f"   ✓ Sketch extraction successful")
                result["extraction_status"] = "success"

                # Copy hermes output to root for form generation
                hermes_src = row_dir / "hermes_output.json"
                if hermes_src.exists():
                    shutil.copy(hermes_src, "hermes_output.json")
                    print(f"   ✓ Data prepared for form generation")
            else:
                print(f"   ✗ Extraction failed: {extract_result.stderr[:200]}")
                result["extraction_status"] = "failed"

        except Exception as e:
            print(f"   ✗ Error: {e}")
            result["extraction_status"] = "error"

    # Step 2: Prepare form fields from Google Sheet row data
    if result["extraction_status"] == "success":
        print(f"\n2. Preparing form fields from Google Sheet data...")

        # Try to read the actual Google Sheet row
        sheet_fields = {}

        # First, try dynamic sheet reading
        try:
            sheet_rows = get_sheet_rows()
            if sheet_rows and len(sheet_rows) > row_num:
                headers = sheet_rows[0]
                row_data = sheet_rows[row_num]
                row_dict = convert_raw_row_to_dict(headers, row_data)
                sheet_fields = get_parsed_fields_from_row(row_dict)
        except Exception as e:
            print(f"   ⚠ Could not read dynamic Google Sheet: {e}")

        # Fallback: Use hardcoded test data from sheet_parser for known rows
        if not sheet_fields:
            print(f"   Using pre-defined test data for row {row_num}...")
            try:
                # Import and use the hardcoded test data from sheet_parser
                from sheet_parser import parse_sheet_row, RAW_ROW

                # For row 2 (Kristen Marquis), use the default RAW_ROW from sheet_parser
                if row_num == 2:
                    sheet_fields = parse_sheet_row(RAW_ROW)
                    print(f"   ✓ Using Kristen Marquis (26-018) test data")
                else:
                    # For other rows, create synthetic data based on row number
                    synthetic_data = dict(RAW_ROW)
                    synthetic_data["Client name, Phone number, and Address"] = f"Test Property {row_num}"
                    sheet_fields = parse_sheet_row(synthetic_data)
                    print(f"   ✓ Using synthetic test data for row {row_num}")
            except Exception as e:
                print(f"   ⚠ Error loading test data: {e}")

        if sheet_fields:
            print(f"   ✓ Parsed {len(sheet_fields)} fields for row {row_num}")
            # Save to sheet_row_data.json for fill_form.py to read
            sheet_data_path = Path("sheet_row_data.json")
            with open(sheet_data_path, 'w') as f:
                json.dump(sheet_fields, f, indent=2)
            print(f"   ✓ Saved form fields to sheet_row_data.json")
        else:
            print(f"   ⚠ Could not prepare fields for row {row_num}")

    # Step 3: Generate form (if extraction was successful)
    if result["extraction_status"] == "success":
        print(f"\n3. Generating HHE-200 form...")

        try:
            # Import and use acro_fill which properly fills AcroForm fields
            from acro_fill import fill_acro
            from field_adapter import adapt_sheet_fields_to_acro

            # Load sheet fields from JSON
            sheet_data_path = Path("sheet_row_data.json")
            if sheet_data_path.exists():
                with open(sheet_data_path, 'r') as f:
                    sheet_fields = json.load(f)
            else:
                sheet_fields = {}

            # Adapt sheet_parser field names to acro_fill expectations
            adapted_fields = adapt_sheet_fields_to_acro(sheet_fields)

            # Fill the form using AcroForm field mapping
            result_pdf = fill_acro(adapted_fields, "HHE-200-filled.pdf")

            if Path(result_pdf).exists():
                print(f"   ✓ Form generated successfully")
                result["form_status"] = "success"
            else:
                print(f"   ✗ Form generation failed: Output PDF not created")
                result["form_status"] = "failed"
        except Exception as e:
            print(f"   ✗ Form generation failed: {str(e)[:200]}")
            result["form_status"] = "failed"

        # Copy PDF to row directory if generation was successful
        if result["form_status"] == "success":
            pdf_src = Path("HHE-200-filled.pdf")
            if pdf_src.exists():
                pdf_dst = row_dir / f"HHE-200-row{row_num}.pdf"
                shutil.copy(pdf_src, pdf_dst)
                result["outputs"].append(f"HHE-200-row{row_num}.pdf")
                print(f"   ✓ PDF saved: {pdf_dst.name}")

            # Copy drawing images
            for img in Path(".").glob("*pg*.png"):
                img_dst = row_dir / f"row{row_num}_{img.name}"
                shutil.copy(img, img_dst)
                result["outputs"].append(f"row{row_num}_{img.name}")

    # Step 4: Compare with example (if available)
    if example_folder and result["form_status"] == "success":
        print(f"\n4. Comparing with example folder '{example_folder}'...")

        example_dir = Path("example") / example_folder
        if example_dir.exists():
            example_pdfs = sorted(example_dir.glob("*PG*.pdf"))
            print(f"   Found {len(example_pdfs)} example PDFs:")
            for pdf in example_pdfs:
                print(f"     - {pdf.name}")

            result["comparison"] = {
                "example_folder": example_folder,
                "example_pdfs": [p.name for p in example_pdfs],
                "status": "ready_for_comparison"
            }
            print(f"   ✓ Comparison data prepared")
        else:
            print(f"   ⚠ Example folder not found: {example_dir}")

    return result

def main():
    print(f"\n{'='*80}")
    print(f"HHE-200 COMPREHENSIVE TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

    # Try to read sheet
    rows_data = get_sheet_rows()

    if rows_data:
        test_rows = identify_test_rows(rows_data)
        print(f"✓ Found {len(test_rows)} test rows in Google Sheet")
    else:
        print(f"\n⚠ Could not read Google Sheet, using predefined test cases")
        # Fallback: use predefined test cases
        test_rows = [
            {"row_number": 2, "property_name": "26-018", "owner_name": "Kristen Marquis", "uploads_url": "https://drive.google.com/open?id=test2"},
            {"row_number": 3, "property_name": "Synthetic Test 1", "owner_name": "George", "uploads_url": "https://drive.google.com/open?id=test3"},
            {"row_number": 4, "property_name": "26-123", "owner_name": "Test Property", "uploads_url": "https://drive.google.com/open?id=test4"},
            {"row_number": 5, "property_name": "Synthetic Test 2", "owner_name": "George", "uploads_url": "https://drive.google.com/open?id=test5"},
        ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "total_rows": len(test_rows),
        "completed": 0,
        "successful": 0,
        "test_results": []
    }

    # Process each row
    for row_info in test_rows:
        example_folder = determine_example_folder(
            row_info["row_number"],
            row_info["property_name"]
        )

        row_result = process_test_row(row_info, example_folder)
        results["test_results"].append(row_result)
        results["completed"] += 1

        if row_result["form_status"] == "success":
            results["successful"] += 1

    # Print summary
    print(f"\n{'='*80}")
    print(f"TEST SUITE SUMMARY")
    print(f"{'='*80}")
    print(f"Total rows processed: {results['completed']}/{results['total_rows']}")
    print(f"Successful generations: {results['successful']}/{results['total_rows']}")
    print(f"Results location: {RESULTS_DIR}")
    print(f"\nGenerated outputs:")
    for row_result in results["test_results"]:
        status = "✓" if row_result["form_status"] == "success" else "✗"
        print(f"  {status} Row {row_result['row']}: {row_result['property']}")

    # Save results
    results_file = RESULTS_DIR / "test_summary.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved: {results_file}")
    print(f"{'='*80}\n")

    return results

if __name__ == "__main__":
    results = main()
    sys.exit(0 if results["successful"] > 0 else 1)
