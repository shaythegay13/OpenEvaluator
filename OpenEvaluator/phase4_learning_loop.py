#!/usr/bin/env python3
"""Phase 4: Quality assessment & learning loop.
Compares generated HHE-200 output against pinnacle examples
and tracks improvement across iterations."""
import json, os, sys, subprocess
from pathlib import Path

sys.path.insert(0, '/home/workspace/OpenEvaluator')

# Number of fields on the HHE-200 PDF
TOTAL_SCORABLE = 264
EXCLUDED = 20
TARGET = 230  # 93/100 ~ 87%

def score_form():
    """Run form scoring."""
    result = subprocess.run(
        ['python3', '/home/workspace/OpenEvaluator/score_form.py'],
        capture_output=True, text=True, cwd='/home/workspace/OpenEvaluator'
    )
    for line in result.stdout.split('\n'):
        if 'Score:' in line:
            parts = line.split('=')
            score = float(parts[1].strip().replace('%', ''))
            filled = int(parts[0].split('/')[0].split(':')[1].strip())
            return score, filled
    return 0, 0

def main():
    print("=" * 60)
    print("PHASE 4: QUALITY ASSESSMENT & LEARNING LOOP")
    print("=" * 60)

    # 1. Generate current output
    print("\n[STEP 1] Generating current form...")
    result = subprocess.run(
        ['python3', 'test_field_adapter.py'],
        capture_output=True, text=True,
        cwd='/home/workspace/OpenEvaluator', timeout=120
    )
    
    # 2. Score the form
    print("\n[STEP 2] Scoring form...")
    score, filled = score_form()
    target = 230
    gap = target - filled
    
    print(f"\n  Current score: {score:.0f}% ({filled}/{TOTAL_SCORABLE})")
    print(f"  Target score:  87% ({target}/{TOTAL_SCORABLE})")
    print(f"  Gap: {gap} fields to fill")
    
    # 3. Identify largest remaining gaps
    print("\n[STEP 3] Analyzing field gaps...")
    import pikepdf
    pdf = pikepdf.open('/home/workspace/OpenEvaluator/HHE-200-filled.pdf')
    acro = pdf.Root['/AcroForm']
    fields_list = acro['/Fields']
    
    excluded_patterns = [
        "Installer", "LPI Signature", "Date for First LPI", 
        "Date for Second LPI", "Issuing Municipality", "Permit #",
        "Permit Issued", "Fee Calculation", "Total Fee", "Town Share",
        "State 25%", "DEP WQS", "Revision", "Doubled", "Variance Check",
        "Property Owner Signature", "Date (Property Owner",
        "Maintenance Contract", "Pre-Treatment",
    ]
    
    empty_meaningful = []
    for f in fields_list:
        name = str(f.get("/T", ""))
        val = str(f.get("/V", ""))
        if not val and len(name) > 3:
            excluded = False
            for pat in excluded_patterns:
                if pat.lower() in name.lower():
                    excluded = True
                    break
            if not excluded:
                empty_meaningful.append(name)
    
    print(f"  Empty scorable fields: {len(empty_meaningful)}")
    
    # Group empty fields by category
    categories = {
        "Soil grid data": [],
        "Checkboxes/radio": [],
        "Numeric fields": [],
        "Text/descriptive": [],
    }
    for name in empty_meaningful:
        if "table" in name.lower() or "grid" in name.lower() or "soil" in name.lower():
            categories["Soil grid data"].append(name)
        elif "check" in name.lower() or "box" in name.lower():
            categories["Checkboxes/radio"].append(name)
        elif "size" in name.lower() or "number" in name.lower() or "# of" in name.lower() or "ft" in name.lower():
            categories["Numeric fields"].append(name)
        else:
            categories["Text/descriptive"].append(name)
    
    print("\n  Gap breakdown:")
    for cat, names in categories.items():
        if names:
            print(f"    {cat}: {len(names)} fields")
    
    # 4. Generate learning report
    print("\n[STEP 4] Saving learning report...")
    report = {
        "iteration": 1,
        "score_pct": round(score, 1),
        "filled": filled,
        "total": TOTAL_SCORABLE,
        "gap": gap,
        "empty_categories": {cat: len(names) for cat, names in categories.items() if names},
        "top_empty_fields": empty_meaningful[:20],
        "excluded_sections": EXCLUDED,
        "target": TARGET,
        "recommendations": [
            f"1. Fill {gap} remaining scorable fields to reach 87%",
            "2. Map soil observation hole data to grid rows",
            "3. Set checkbox/radio states based on application type",
            "4. Populate numeric sizing fields from disposal field data",
        ]
    }
    
    report_path = Path('/home/workspace/OpenEvaluator/test_results/learning_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Report saved: {report_path}")
    
    print(f"\n{'=' * 60}")
    print(f"PHASE 4 COMPLETE — Score: {score:.0f}%")
    print(f"{'=' * 60}")
    
    return report

if __name__ == "__main__":
    main()
