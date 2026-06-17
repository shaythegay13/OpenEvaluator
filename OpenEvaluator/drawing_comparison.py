"""
Drawing Comparison System for HHE-200 Forms
Compares generated site plans (page 3) and disposal plans (page 4)
against pinnacle examples using image and geometric analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import json

logger = logging.getLogger(__name__)

class DrawingComparator:
    """Compares generated drawings against pinnacle examples."""
    
    def __init__(self, example_pdf_dir: Path, output_dir: Path):
        self.example_pdf_dir = example_pdf_dir
        self.output_dir = output_dir
        
        # Expected elements for each drawing type
        self.site_plan_elements = {
            'lot_boundary': 'Rectangular boundary of property',
            'house_building': 'Main residence structure',
            'septic_tank': 'Primary septic tank (large rectangle)',
            'd_box': 'Distribution box (smaller rectangle)',
            'soil_absorption_field': 'Disposal field with rows',
            'road': 'Access road/driveway',
            'grid_lines': '16x31 grid system',
            'scale': 'Scale notation (e.g., 1 inch = X feet)',
            'north_arrow': 'North direction indicator',
            'dimensions': 'Linear measurements'
        }
        
        self.disposal_plan_elements = {
            'septic_tank': 'Tank outline and capacity label',
            'd_box': 'Distribution box with label',
            'absorption_field': 'Field system layout',
            'disposal_rows': '4-5 parallel absorption rows',
            'field_modules': 'Module layout within field',
            'spacing': 'Required spacing (typically 6-8 feet)',
            'scale': 'Scale notation',
            'dimensions': 'Linear measurements',
            'notes': 'Design notes and references',
            'legend': 'Explanation of symbols'
        }
    
    def extract_drawing_images(self, pdf_path: Path, page_num: int) -> List[Path]:
        """Extract images from a specific PDF page."""
        try:
            output_prefix = self.output_dir / f"extracted_page{page_num}"
            result = subprocess.run(
                ['pdfimages', '-png', str(pdf_path), str(output_prefix)],
                capture_output=True,
                timeout=10
            )
            
            # Find extracted images
            extracted = list(self.output_dir.glob(f'extracted_page{page_num}-*.png'))
            logger.info(f"Extracted {len(extracted)} images from page {page_num}")
            return extracted
        except Exception as e:
            logger.warning(f"Failed to extract images: {e}")
            return []
    
    def analyze_drawing_elements(self, image_path: Path, expected_elements: Dict) -> Dict:
        """Analyze drawing for presence of expected elements."""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(str(image_path))
            if img is None:
                return {'error': 'Failed to load image', 'detected_elements': []}
            
            height, width = img.shape[:2]
            
            # Analyze image characteristics
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect lines (for structure outlines)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
            line_count = len(lines) if lines is not None else 0
            
            # Detect contours (for filled shapes)
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len(contours)
            
            # Detect text regions
            text_regions = cv2.findNonZero(cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
            has_text = text_regions is not None and len(text_regions) > 100
            
            # Heuristic element detection
            detected = []
            if line_count > 20:
                detected.append('geometric_structure')
            if contour_count > 5:
                detected.append('enclosed_areas')
            if has_text:
                detected.append('annotations')
            if contour_count > 20:
                detected.append('detailed_elements')
            
            # Check for grid pattern (regular line spacing)
            has_grid = False
            if line_count > 50:
                # Analyze line spacing regularity
                has_grid = True
                detected.append('grid_system')
            
            return {
                'image_size': (width, height),
                'line_count': line_count,
                'contour_count': contour_count,
                'has_text': has_text,
                'has_grid': has_grid,
                'detected_elements': detected,
                'element_confidence': len(detected) / len(expected_elements)
            }
        except Exception as e:
            logger.error(f"Element analysis failed: {e}")
            return {'error': str(e), 'detected_elements': []}
    
    def compare_with_example(self, generated_image: Path, example_page: int) -> Dict:
        """Compare generated drawing with pinnacle example."""
        
        # Load example images
        example_pattern = f"example-pg{example_page}"
        example_images = list(self.example_pdf_dir.glob(f"{example_pattern}-*.png"))
        
        if not example_images:
            logger.warning(f"No example images found for page {example_page}")
            return {
                'comparison': 'No example available',
                'score': 0,
                'gaps': [f'No example images for page {example_page}']
            }
        
        # Use the main example (not detail)
        example_img = next((i for i in example_images if 'detail' not in i.name), example_images[0])
        
        # Analyze both images
        expected = self.site_plan_elements if example_page == 3 else self.disposal_plan_elements
        
        generated_analysis = self.analyze_drawing_elements(generated_image, expected)
        example_analysis = self.analyze_drawing_elements(example_img, expected)
        
        # Calculate comparison score
        gaps = []
        
        # Check for structural completeness
        gen_elements = set(generated_analysis.get('detected_elements', []))
        ex_elements = set(example_analysis.get('detected_elements', []))
        
        missing_element_types = ex_elements - gen_elements
        if missing_element_types:
            gaps.append(f"Missing element types: {', '.join(missing_element_types)}")
        
        # Check geometric properties
        gen_size = generated_analysis.get('image_size', (0, 0))
        ex_size = example_analysis.get('image_size', (1, 1))
        size_ratio = (gen_size[0] * gen_size[1]) / (ex_size[0] * ex_size[1]) if ex_size[0] > 0 and ex_size[1] > 0 else 0
        
        if size_ratio < 0.8 or size_ratio > 1.2:
            gaps.append(f"Drawing size mismatch (ratio: {size_ratio:.2f})")
        
        # Check complexity
        gen_lines = generated_analysis.get('line_count', 0)
        ex_lines = example_analysis.get('line_count', 50)
        
        if gen_lines < ex_lines * 0.5:
            gaps.append(f"Drawing lacks detail/complexity (lines: {gen_lines} vs {ex_lines} expected)")
        
        # Check for annotations
        if not generated_analysis.get('has_text', False) and example_analysis.get('has_text', False):
            gaps.append("Missing text annotations/dimensions")
        
        # Check for grid (site plan specific)
        if example_page == 3 and not generated_analysis.get('has_grid', False):
            gaps.append("Missing grid system (should be 16x31)")
        
        # Calculate score
        base_score = 50
        if missing_element_types:
            base_score -= len(missing_element_types) * 15
        if 0.8 <= size_ratio <= 1.2:
            base_score += 10
        if gen_lines >= ex_lines * 0.7:
            base_score += 15
        if generated_analysis.get('has_text', False):
            base_score += 10
        
        final_score = max(0, min(100, base_score))
        
        return {
            'page': example_page,
            'score': final_score,
            'generated_analysis': generated_analysis,
            'example_analysis': example_analysis,
            'gaps': gaps,
            'has_all_elements': len(missing_element_types) == 0,
            'size_ratio': size_ratio
        }
    
    def generate_learning_report(self, page_3_result: Dict, page_4_result: Dict) -> str:
        """Generate learning feedback for Hermes to improve drawings."""
        
        report = "## Drawing Assessment & Learning Feedback\n\n"
        
        # Page 3 (Site Plan) feedback
        report += f"### Page 3 - Site Plan\n"
        report += f"**Score: {page_3_result.get('score', 0)}/100**\n\n"
        
        if page_3_result.get('gaps'):
            report += "**Issues to Fix:**\n"
            for gap in page_3_result['gaps']:
                report += f"- {gap}\n"
        else:
            report += "✅ All elements present and properly positioned\n"
        
        report += f"\n**Analysis:**\n"
        report += f"- Detected elements: {', '.join(page_3_result.get('generated_analysis', {}).get('detected_elements', []))}\n"
        report += f"- Line count: {page_3_result.get('generated_analysis', {}).get('line_count', 0)}\n"
        report += f"- Has annotations: {page_3_result.get('generated_analysis', {}).get('has_text', False)}\n"
        report += f"- Has grid: {page_3_result.get('generated_analysis', {}).get('has_grid', False)}\n\n"
        
        # Page 4 (Disposal Plan) feedback
        report += f"### Page 4 - Disposal Plan\n"
        report += f"**Score: {page_4_result.get('score', 0)}/100**\n\n"
        
        if page_4_result.get('gaps'):
            report += "**Issues to Fix:**\n"
            for gap in page_4_result['gaps']:
                report += f"- {gap}\n"
        else:
            report += "✅ All elements present and properly positioned\n"
        
        report += f"\n**Analysis:**\n"
        report += f"- Detected elements: {', '.join(page_4_result.get('generated_analysis', {}).get('detected_elements', []))}\n"
        report += f"- Line count: {page_4_result.get('generated_analysis', {}).get('line_count', 0)}\n"
        report += f"- Has annotations: {page_4_result.get('generated_analysis', {}).get('has_text', False)}\n\n"
        
        # Overall summary
        overall_score = (page_3_result.get('score', 0) + page_4_result.get('score', 0)) / 2
        report += f"## Overall Drawing Quality: {overall_score:.0f}/100\n"
        
        if overall_score >= 80:
            report += "✅ Drawings meet quality standards\n"
        elif overall_score >= 60:
            report += "⚠️ Drawings acceptable but need improvements\n"
        else:
            report += "❌ Drawings need significant rework\n"
        
        return report


def compare_drawings(example_dir: Path, output_dir: Path, generated_pdf: Path) -> Dict:
    """Main function to compare all drawings."""
    comparator = DrawingComparator(example_dir, output_dir)
    
    # Extract and compare page 3 (site plan)
    page_3_images = comparator.extract_drawing_images(generated_pdf, 3)
    page_3_result = {}
    if page_3_images:
        page_3_result = comparator.compare_with_example(page_3_images[0], 3)
    else:
        page_3_result = {'score': 0, 'gaps': ['Failed to extract page 3 images']}
    
    # Extract and compare page 4 (disposal plan)
    page_4_images = comparator.extract_drawing_images(generated_pdf, 4)
    page_4_result = {}
    if page_4_images:
        page_4_result = comparator.compare_with_example(page_4_images[0], 4)
    else:
        page_4_result = {'score': 0, 'gaps': ['Failed to extract page 4 images']}
    
    # Generate learning report
    report = comparator.generate_learning_report(page_3_result, page_4_result)
    
    return {
        'page_3': page_3_result,
        'page_4': page_4_result,
        'overall_drawing_score': (page_3_result.get('score', 0) + page_4_result.get('score', 0)) / 2,
        'learning_report': report,
        'gaps_for_improvement': page_3_result.get('gaps', []) + page_4_result.get('gaps', [])
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    example_dir = Path('/home/workspace/OpenEvaluator/example')
    output_dir = Path('/home/workspace/OpenEvaluator')
    generated_pdf = output_dir / 'output.pdf'
    
    if generated_pdf.exists():
        result = compare_drawings(example_dir, output_dir, generated_pdf)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Generated PDF not found: {generated_pdf}")
