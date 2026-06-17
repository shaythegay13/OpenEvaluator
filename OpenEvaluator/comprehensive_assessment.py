#!/usr/bin/env python3
"""
Comprehensive HHE-200 assessment comparing current output against example PDFs.
Analyzes all 4 pages with detailed quality report and learning feedback.
"""

import fitz  # PyMuPDF
import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime


def extract_page_images(pdf_path, page_num):
    """Extract images from a specific PDF page."""
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            return []

        page = doc[page_num]
        image_list = page.get_images()
        images = []

        for img_index in image_list:
            xref = img_index[0]
            pix = fitz.Pixmap(doc, xref)

            # Skip very small images (noise/artifacts)
            if pix.width < 100 or pix.height < 100:
                continue

            # Convert to numpy array for OpenCV
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 3:  # RGB
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                elif pix.n == 2:  # GRAY + alpha
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            else:  # CMYK
                pix = fitz.Pixmap(fitz.csRGB, pix)
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

            images.append({
                'array': img_array,
                'dimensions': (pix.width, pix.height),
                'size_kb': len(pix.samples) / 1024
            })

        doc.close()
        return images
    except Exception as e:
        print(f"Error extracting from {pdf_path} page {page_num}: {e}")
        return []


def analyze_drawing(img_array):
    """Analyze a drawing image for quality metrics."""
    if img_array is None:
        return None

    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_array

    # Edge detection
    edges = cv2.Canny(gray, 50, 150)

    # Line detection
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
    line_count = len(lines) if lines is not None else 0

    # Contour detection
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Calculate contour statistics
    contour_areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 50]
    avg_contour_area = np.mean(contour_areas) if contour_areas else 0
    max_contour_area = np.max(contour_areas) if contour_areas else 0

    # Text detection (look for dark regions that could be text/annotations)
    text_regions = cv2.countNonZero(cv2.inRange(gray, 0, 100))

    return {
        'line_count': line_count,
        'contour_count': len(contours),
        'significant_contours': len(contour_areas),
        'avg_contour_area': float(avg_contour_area),
        'max_contour_area': float(max_contour_area),
        'text_pixels': text_regions,
        'has_content': line_count > 5 or len(contour_areas) > 10,
        'complexity_score': min(100, (line_count * 2 + len(contour_areas) // 5))
    }


def compare_drawings(current_img, example_img):
    """Compare two drawings and return similarity metrics."""
    if current_img is None or example_img is None:
        return {'similarity': 0, 'notes': 'Missing image data'}

    # Resize to same dimensions for comparison
    h_current = current_img['array'].shape[0]
    w_current = current_img['array'].shape[1]

    example_array = cv2.resize(example_img['array'], (w_current, h_current))
    current_array = current_img['array']

    # Analyze both
    current_analysis = analyze_drawing(current_array)
    example_analysis = analyze_drawing(example_array)

    if not current_analysis or not example_analysis:
        return {'similarity': 0, 'notes': 'Analysis failed'}

    # Compare line counts (example is pinnacle)
    line_ratio = current_analysis['line_count'] / max(1, example_analysis['line_count'])
    line_ratio = min(1.0, line_ratio)  # Cap at 1.0

    # Compare contour complexity
    contour_ratio = current_analysis['significant_contours'] / max(1, example_analysis['significant_contours'])
    contour_ratio = min(1.0, contour_ratio)

    # Compare text/annotations
    text_ratio = current_analysis['text_pixels'] / max(1, example_analysis['text_pixels'])
    text_ratio = min(1.0, text_ratio)

    # Calculate overall similarity
    similarity = int((line_ratio + contour_ratio + text_ratio) / 3 * 100)

    return {
        'similarity': similarity,
        'current_analysis': current_analysis,
        'example_analysis': example_analysis,
        'line_ratio': float(line_ratio),
        'contour_ratio': float(contour_ratio),
        'text_ratio': float(text_ratio),
        'details': f"Current: {current_analysis['line_count']} lines, {current_analysis['significant_contours']} shapes | "
                  f"Example: {example_analysis['line_count']} lines, {example_analysis['significant_contours']} shapes"
    }


def assess_form_completion(pdf_path):
    """Count form field completion (pages 1-2)."""
    try:
        doc = fitz.open(pdf_path)

        page1 = doc[0]
        page2 = doc[1]

        # Count text on pages (rough indicator of form completion)
        page1_text = page1.get_text()
        page2_text = page2.get_text()

        # More sophisticated: look for filled form fields
        page1_blocks = page1.get_text("blocks")
        page2_blocks = page2.get_text("blocks")

        # Count non-empty text blocks
        filled_1 = sum(1 for block in page1_blocks if len(block[4].strip()) > 2)
        filled_2 = sum(1 for block in page2_blocks if len(block[4].strip()) > 2)

        doc.close()

        return {
            'page1_filled_blocks': filled_1,
            'page2_filled_blocks': filled_2,
            'total_filled': filled_1 + filled_2,
            'estimate_percent': min(100, int((filled_1 + filled_2) / 4))  # Very rough estimate
        }
    except Exception as e:
        print(f"Error assessing form: {e}")
        return {'error': str(e)}


def generate_quality_report(current_pdf, example_pdfs):
    """Generate comprehensive quality report."""
    print(f"\n{'='*70}")
    print(f"COMPREHENSIVE HHE-200 QUALITY ASSESSMENT")
    print(f"Generated: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    report = {
        'timestamp': datetime.now().isoformat(),
        'current_pdf': str(current_pdf),
        'pages': {}
    }

    # PAGES 1-2: Form Completion Assessment
    print("PAGES 1-2: FORM COMPLETION")
    print("-" * 70)
    form_assessment = assess_form_completion(current_pdf)
    report['form_assessment'] = form_assessment
    print(f"  Page 1 filled blocks: {form_assessment.get('page1_filled_blocks', 'N/A')}")
    print(f"  Page 2 filled blocks: {form_assessment.get('page2_filled_blocks', 'N/A')}")
    print(f"  Estimated completion: {form_assessment.get('estimate_percent', 0)}%")

    # PAGES 3-4: Drawing Assessment
    print("\nPAGES 3-4: DRAWING ASSESSMENT")
    print("-" * 70)

    for page_num, page_label in [(2, "Page 3 (Site Plan)"), (3, "Page 4 (Disposal Plan)")]:
        print(f"\n{page_label}:")

        # Get example PDF for this page
        page_name = f"PG{page_num + 1}"
        example_pdf = None
        for pdf in example_pdfs:
            if page_name in pdf.name:
                example_pdf = pdf
                break

        if example_pdf is None:
            print(f"  ⚠️  Example PDF for {page_label} not found")
            continue

        # Extract images
        current_images = extract_page_images(current_pdf, page_num)
        example_images = extract_page_images(example_pdf, 0)  # Example is single page

        if not current_images:
            print(f"  ❌ No drawing found in current output")
            report['pages'][page_label] = {'score': 0, 'reason': 'No drawing found'}
            continue

        if not example_images:
            print(f"  ⚠️  Could not extract example drawing for comparison")
            continue

        # Compare
        current_img = current_images[0]
        example_img = example_images[0]

        comparison = compare_drawings(current_img, example_img)
        similarity = comparison['similarity']

        print(f"  Dimensions: {current_img['dimensions']}")
        print(f"  Similarity to example: {similarity}/100")
        if 'details' in comparison:
            print(f"  {comparison['details']}")

        report['pages'][page_label] = {
            'score': similarity,
            'dimensions': current_img['dimensions'],
            'comparison': comparison
        }

    # OVERALL QUALITY SCORE
    print("\n" + "="*70)
    print("OVERALL QUALITY ASSESSMENT")
    print("="*70)

    page3_score = report['pages'].get('Page 3 (Site Plan)', {}).get('score', 0)
    page4_score = report['pages'].get('Page 4 (Disposal Plan)', {}).get('score', 0)
    form_score = form_assessment.get('estimate_percent', 0)

    # Weighted scoring: form 40%, page3 30%, page4 30%
    overall_score = int(form_score * 0.4 + page3_score * 0.3 + page4_score * 0.3)

    print(f"\n  Form completion (Pages 1-2): {form_score}/100 (40% weight)")
    print(f"  Site plan quality (Page 3):  {page3_score}/100 (30% weight)")
    print(f"  Disposal plan quality (Page 4): {page4_score}/100 (30% weight)")
    print(f"\n  OVERALL QUALITY SCORE: {overall_score}/100")

    if overall_score >= 95:
        status = "✅ PRODUCTION READY"
    elif overall_score >= 80:
        status = "⚠️  NEEDS ITERATION"
    else:
        status = "❌ SIGNIFICANT IMPROVEMENTS NEEDED"

    print(f"  Status: {status}")

    report['overall_score'] = overall_score
    report['status'] = status

    # Learning Feedback
    print("\n" + "="*70)
    print("LEARNING FEEDBACK FOR HERMES")
    print("="*70)

    gaps = []

    if form_score < 70:
        gaps.append(f"• Form completion too low ({form_score}%): Hermes should fill more data fields from available sheet data")

    if page3_score < 70:
        gaps.append("• Site plan drawings lack detail: Missing grid system, proper annotations, scaling, or spatial layout")

    if page4_score < 70:
        gaps.append("• Disposal plan drawings incomplete: Missing field rows, spacing, modules, or system configuration")

    if not gaps:
        gaps.append("• Minor refinements needed to reach 95/100 threshold")

    print("\nPriority improvements for next iteration:")
    for gap in gaps:
        print(gap)

    report['learning_feedback'] = gaps

    # Save report
    report_file = Path(current_pdf).parent / "quality_assessment.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Full report saved to: {report_file}")
    print("="*70 + "\n")

    return report


if __name__ == "__main__":
    current_pdf = Path("/home/workspace/OpenEvaluator/HHE-200-filled.pdf")
    example_dir = Path("/home/workspace/OpenEvaluator/example")

    example_pdfs = list(example_dir.glob("26-018 PG*.pdf"))

    report = generate_quality_report(current_pdf, example_pdfs)

    # Print JSON for programmatic access
    print("\n📊 MACHINE-READABLE REPORT:")
    print(json.dumps(report, indent=2))
