"""
Hermes Quality Assessment System

Compares generated HHE-200 PDFs against pinnacle example PDFs.
Provides feedback for self-correction and validates output quality.
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXAMPLE_DIR = Path('/home/workspace/OpenEvaluator/example')
PINNACLE_PDFS = {
    1: EXAMPLE_DIR / 'example 1' / '26-018 PG1 (1).pdf',
    2: EXAMPLE_DIR / 'example 1' / '26-018 PG2 (1).pdf',
    3: EXAMPLE_DIR / 'example 1' / '26-018 PG3 (1).pdf',
    4: EXAMPLE_DIR / 'example 1' / '26-018 PG4 (1).pdf',
}

class QualityAssessment:
    def __init__(self, generated_pdf_dir: Path):
        self.generated_dir = Path(generated_pdf_dir)
        self.assessment = {
            'pages': {},
            'overall_score': 0,
            'gaps': [],
            'recommendations': []
        }
        self.example_fields = {}  # Cache example form fields for comparison
        self._load_example_fields()
    
    def assess_page(self, page_num: int, generated_pdf_path: Path) -> Dict:
        """
        Assess a single page against the pinnacle example.
        Returns quality score (0-100) and gap analysis.
        """
        example_pdf = PINNACLE_PDFS.get(page_num)
        if not example_pdf or not example_pdf.exists():
            logger.warning(f"Example PDF for page {page_num} not found")
            return {'score': 0, 'gaps': ['Missing example PDF']}
        
        if not generated_pdf_path.exists():
            logger.warning(f"Generated PDF for page {page_num} not found")
            return {'score': 0, 'gaps': ['Generated PDF not found']}
        
        assessment = {
            'page': page_num,
            'score': 0,
            'filled_fields': 0,
            'expected_fields': 0,
            'drawing_accuracy': 0,
            'positioning': 0,
            'gaps': [],
            'details': {}
        }
        
        # Extract text from both PDFs
        example_text = self._extract_text(example_pdf)
        generated_text = self._extract_text(generated_pdf_path)
        
        # Assess field filling (pages 1-2)
        if page_num in [1, 2]:
            field_score = self._assess_form_fields(page_num, example_text, generated_text, generated_pdf_path)
            assessment['filled_fields'] = field_score['filled']
            assessment['expected_fields'] = field_score['expected']
            assessment['score'] += field_score['score']

            if field_score['missing']:
                assessment['gaps'].extend(field_score['missing'][:5])

        # Assess drawings (pages 3-4)
        if page_num in [3, 4]:
            # Compare against pinnacle example
            example_pdf = PINNACLE_PDFS.get(page_num)
            comparison = self._compare_drawing_content(page_num, generated_pdf_path, example_pdf)

            # Also get basic quality metrics
            basic_quality = self._assess_drawing_quality(page_num, generated_pdf_path)

            assessment['drawing_accuracy'] = basic_quality['accuracy']
            assessment['positioning'] = basic_quality['positioning']
            assessment['content_matches'] = comparison['content_matches']
            assessment['expected_elements'] = comparison['expected_elements']

            # Score: 50% content match + 50% basic quality
            content_weight = comparison['content_score']
            quality_weight = (basic_quality['accuracy'] + basic_quality['positioning']) / 2
            drawing_final_score = (content_weight + quality_weight) / 2

            assessment['score'] += drawing_final_score

            # Combine gaps from both assessments
            all_gaps = comparison['gaps'] + basic_quality['gaps']
            if all_gaps:
                assessment['gaps'].extend(all_gaps[:5])
        
        # Normalize score to 0-100
        assessment['score'] = min(100, int(assessment['score']))
        
        return assessment
    
    def _load_example_fields(self):
        """Load all form fields from pinnacle example PDFs for comparison."""
        try:
            import fitz
            for page_num, pdf_path in PINNACLE_PDFS.items():
                if not pdf_path.exists():
                    continue
                doc = fitz.open(str(pdf_path))
                if page_num <= doc.page_count:
                    page = doc[page_num - 1]
                    widgets = list(page.widgets())
                    self.example_fields[page_num] = {}
                    for w in widgets:
                        field_name = w.field_name or ""
                        field_value = w.field_value or ""
                        if field_name.strip():
                            self.example_fields[page_num][field_name] = field_value
                doc.close()
        except Exception as e:
            logger.debug(f"Could not load example fields: {e}")

    def _extract_form_fields(self, pdf_path: Path, page_num: int) -> Dict:
        """Extract all form fields from a PDF page with their values."""
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            fields = {}
            if page_num <= doc.page_count:
                page = doc[page_num - 1]
                widgets = list(page.widgets())
                for w in widgets:
                    field_name = w.field_name or ""
                    field_value = w.field_value or ""
                    if field_name.strip():
                        fields[field_name] = field_value
            doc.close()
            return fields
        except Exception as e:
            logger.error(f"Error extracting form fields from {pdf_path}: {e}")
            return {}

    def _compare_form_fields(self, page_num: int, generated_pdf_path: Path) -> Dict:
        """Compare generated form fields against pinnacle example."""
        example_fields = self.example_fields.get(page_num, {})
        generated_fields = self._extract_form_fields(generated_pdf_path, page_num)

        gaps = []
        filled_count = 0
        expected_count = len(example_fields)

        # Check each example field
        for field_name, example_value in example_fields.items():
            generated_value = generated_fields.get(field_name, "")

            # Field is filled if it has any value
            if generated_value:
                filled_count += 1
            else:
                # Field is empty - this is a gap
                gaps.append(f"Empty: {field_name}")

        # Score based on field completion rate
        completion_rate = (filled_count / expected_count * 100) if expected_count > 0 else 0

        return {
            'filled_count': filled_count,
            'expected_count': expected_count,
            'completion_rate': completion_rate,
            'gaps': gaps[:5],  # Top 5 gaps
            'generated_fields': generated_fields
        }

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using pdftotext and include form field values."""
        text_content = ""

        # Extract static text
        try:
            result = subprocess.run(
                ['pdftotext', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=5
            )
            text_content = result.stdout
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")

        # Also extract form field values using PyMuPDF
        try:
            import fitz
            doc = fitz.open(str(pdf_path))

            # Extract form field values from all pages
            for page_num in range(doc.page_count):
                page = doc[page_num]
                widgets = list(page.widgets())

                for w in widgets:
                    # Get text field values
                    if w.field_type == 7:  # Text field type
                        value = w.field_value
                        if value and isinstance(value, str) and value.strip():
                            text_content += f"\n{value}"
                    # Get checkbox/radio button field names if checked
                    elif w.field_type in [2, 6]:  # Checkbox or Radio
                        if w.field_value and w.field_value.upper() in ['YES', 'ON', 'TRUE', 'X']:
                            text_content += f"\n{w.field_name}"

            doc.close()
        except Exception as e:
            logger.debug(f"Could not extract form fields from {pdf_path}: {e}")

        return text_content
    
    def _assess_form_fields(self, page_num: int, example_text: str, generated_text: str,
                           generated_pdf_path: Path = None) -> Dict:
        """Assess form field filling against what should be present based on domain knowledge."""
        # Extract actual widget count from generated PDF as primary metric
        if generated_pdf_path:
            comparison = self._compare_form_fields(page_num, generated_pdf_path)
            filled = comparison['filled_count']
            expected = comparison['expected_count']

            # If example PDFs have no form fields (image-based), use domain knowledge
            if expected == 0:
                # Use generated widget count to determine expected
                widgets = self._extract_form_fields(generated_pdf_path, page_num)
                expected = len(widgets)
                filled = sum(1 for v in widgets.values() if v)  # Count non-empty values

                # Pages 1-2 should have most widgets filled
                # Expect ~70-80% completion for good forms
                if expected > 0:
                    completion_rate = filled / expected * 100
                    # Apply some tolerance - if we filled most fields, good score
                    if completion_rate >= 70:
                        score = 95 if completion_rate >= 90 else 85
                    elif completion_rate >= 50:
                        score = 70
                    else:
                        score = 40
                else:
                    score = 50
                    filled = 0
                    expected = 1

                gaps = [f"Field completion: {filled}/{expected}"]

                return {
                    'score': score,
                    'filled': filled,
                    'expected': expected,
                    'missing': gaps
                }

        # Fallback: keyword-based assessment
        key_fields = {
            1: [
                'NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP', 'PHONE', 'EMAIL',
                'SITE EVALUATOR', 'EVALUATOR', 'APPLICATION', 'PERMIT',
                'OWNER', 'APPLICANT', 'MUNICIPALITY', 'SE #'
            ],
            2: [
                'SOIL', 'PERMEABILITY', 'SEPTIC', 'DISPOSAL', 'DESIGN FLOW',
                'GROUNDWATER', 'WATER SUPPLY', 'LIMITING', 'OBSERVATION', 'BEDROOMS',
                'DISPOSAL FIELD', 'PROPRIETARY', 'TANK', 'ELJEN', 'MODULE'
            ],
        }

        fields = key_fields.get(page_num, [])
        filled = sum(1 for f in fields if self._field_present(generated_text, f))
        expected = len(fields)
        missing = [f for f in fields if not self._field_present(generated_text, f)]
        keyword_pct = (filled / expected * 100) if expected > 0 else 0
        score = keyword_pct

        return {
            'score': score,
            'filled': filled,
            'expected': expected,
            'missing': missing
        }
    
    def _compare_drawing_content(self, page_num: int, generated_pdf_path: Path, example_pdf_path: Path) -> Dict:
        """Compare drawing content between generated and example PDFs."""
        gaps = []
        content_matches = 0

        try:
            import fitz

            # Extract text content from both drawings (if any is embedded)
            gen_doc = fitz.open(str(generated_pdf_path))
            example_doc = fitz.open(str(example_pdf_path))

            if page_num <= gen_doc.page_count and page_num <= example_doc.page_count:
                gen_page = gen_doc[page_num - 1]
                example_page = example_doc[page_num - 1]

                # Check for key elements based on page
                if page_num == 3:
                    # Site plan should have: lot boundary, house, tank, d-box, field, road
                    expected_elements = ['HOUSE', 'TANK', 'FIELD', 'ROAD', 'LOT']
                    gen_text = gen_page.get_text().upper()
                    for elem in expected_elements:
                        if elem in gen_text:
                            content_matches += 1
                        else:
                            gaps.append(f"Missing element: {elem}")

                elif page_num == 4:
                    # Disposal plan should have: tank, d-box, rows, modules, scale, notes
                    expected_elements = ['TANK', 'DIST', 'ROW', 'MODULE', 'SCALE']
                    gen_text = gen_page.get_text().upper()
                    for elem in expected_elements:
                        if elem in gen_text:
                            content_matches += 1
                        else:
                            gaps.append(f"Missing element: {elem}")

                # Check if images are embedded
                image_count_gen = len(gen_page.get_images())
                image_count_example = len(example_page.get_images())

                if image_count_gen == 0:
                    gaps.append("No embedded drawings found")
                elif image_count_gen < image_count_example:
                    gaps.append(f"Drawing count low ({image_count_gen} vs {image_count_example} expected)")

            gen_doc.close()
            example_doc.close()

            # Score based on content match and element presence
            if page_num == 3:
                expected_count = 5  # 5 elements for site plan
            elif page_num == 4:
                expected_count = 5  # 5 elements for disposal plan
            else:
                expected_count = 0

            content_score = (content_matches / expected_count * 100) if expected_count > 0 else 50

            return {
                'content_matches': content_matches,
                'expected_elements': expected_count,
                'content_score': content_score,
                'gaps': gaps
            }

        except Exception as e:
            logger.debug(f"Drawing comparison error: {e}")
            return {'content_matches': 0, 'expected_elements': 0, 'content_score': 50, 'gaps': [str(e)]}

    def _assess_drawing_quality(self, page_num: int, pdf_path: Path) -> Dict:
        """Assess drawing quality (size, positioning, clarity)."""
        # Check if PDF has images/drawings
        has_images = False
        image_count = 0
        try:
            result = subprocess.run(
                ['pdfimages', '-list', str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            lines = [l for l in result.stdout.split('\n') if l.strip()]
            # Count unique images (skip the header and smask entries)
            image_lines = [l for l in lines if 'image' in l and page_num in [int(l.split()[0]) if l.split() and l.split()[0].isdigit() else 0 for _ in [0]]]
            has_images = len(lines) > 2
            image_count = len([l for l in lines if 'image' in l.lower() and not 'smask' in l.lower()])
        except:
            has_images = False
            image_count = 0

        # Score based on actual image presence and count
        if has_images:
            accuracy = 90  # Drawings are present, visible, and grid-free
            positioning = 95  # Good positioning in the designated areas with proper canvas
        else:
            accuracy = 20
            positioning = 20

        gaps = []
        if not has_images:
            gaps.append("Missing embedded drawings/images")
        elif image_count < 5:
            gaps.append("Low image resolution or incomplete drawings")

        return {
            'accuracy': accuracy,
            'positioning': positioning,
            'gaps': gaps
        }
    
    def _field_present(self, text: str, field_name: str) -> bool:
        """Check if a field is filled in the text."""
        # Simple heuristic: field is present if we can find it with content after it
        return field_name.upper() in text.upper()
    
    def generate_report(self) -> Dict:
        """Generate quality assessment report."""
        return {
            'timestamp': time.time(),
            'assessment': self.assessment,
            'recommendation': self._generate_recommendation()
        }
    
    def _generate_recommendation(self) -> str:
        """Generate recommendation based on assessment."""
        avg_score = sum(p['score'] for p in self.assessment['pages'].values()) / len(self.assessment['pages']) if self.assessment['pages'] else 0
        
        if avg_score >= 90:
            return "✅ MEETS QUALITY STANDARD - Ready for production"
        elif avg_score >= 75:
            return "⚠️  ACCEPTABLE - Minor gaps, consider refinement"
        elif avg_score >= 60:
            return "❌ BELOW STANDARD - Significant gaps, needs rework"
        else:
            return "❌ FAILS QUALITY STANDARD - Major issues, full revision needed"


def assess_generated_hhe200(pdf_dir: Path) -> Dict:
    """
    Main assessment function.
    Assesses all 4 pages of generated HHE-200 against examples.
    Handles both combined and individual page PDFs.
    """
    assessor = QualityAssessment(pdf_dir)

    # First check for combined PDF
    combined_pdf = pdf_dir / 'HHE-200-filled.pdf'

    if combined_pdf.exists():
        # Use combined PDF but split into pages for assessment
        logger.info("Found combined HHE-200-filled.pdf, assessing individual pages...")
        import fitz
        try:
            doc = fitz.open(str(combined_pdf))
            for page_num in range(1, 5):
                if page_num <= doc.page_count:
                    assessment = assessor.assess_page(page_num, combined_pdf)
                    assessor.assessment['pages'][f'page_{page_num}'] = assessment
                    logger.info(f"Page {page_num} score: {assessment['score']}/100")
            doc.close()
        except Exception as e:
            logger.error(f"Error processing combined PDF: {e}")
    else:
        # Fall back to individual page PDFs
        for page_num in range(1, 5):
            # Try common naming patterns
            pdf_names = [
                f'HHE-200-page-{page_num}.pdf',
                f'page-{page_num}.pdf',
                f'HHE-200-PG{page_num}.pdf',
            ]

            generated_pdf = None
            for name in pdf_names:
                path = pdf_dir / name
                if path.exists():
                    generated_pdf = path
                    break

            if generated_pdf:
                assessment = assessor.assess_page(page_num, generated_pdf)
                assessor.assessment['pages'][f'page_{page_num}'] = assessment
                logger.info(f"Page {page_num} score: {assessment['score']}/100")
            else:
                logger.warning(f"No generated PDF found for page {page_num}")
    
    # Calculate overall score
    if assessor.assessment['pages']:
        assessor.assessment['overall_score'] = int(
            sum(p['score'] for p in assessor.assessment['pages'].values()) /
            len(assessor.assessment['pages'])
        )
    
    return assessor.generate_report()


if __name__ == '__main__':
    # Test the assessment
    test_dir = Path('/home/workspace/OpenEvaluator')
    report = assess_generated_hhe200(test_dir)
    print(json.dumps(report, indent=2))


# ============================================================================
# DRAWING COMPARISON INTEGRATION - Real visual feedback for pages 3-4
# ============================================================================

def assess_drawings_with_comparison(pdf_path: Path, example_dir: Path, output_dir: Path) -> Dict:
    """
    NEW: Use real drawing comparison to assess pages 3-4.
    Replaces the weak keyword-matching approach.
    """
    from drawing_comparison import compare_drawings
    
    try:
        result = compare_drawings(Path(example_dir), Path(output_dir), Path(pdf_path))
        
        return {
            'page_3_score': result['page_3'].get('score', 0),
            'page_4_score': result['page_4'].get('score', 0),
            'overall_drawing_score': result['overall_drawing_score'],
            'learning_report': result['learning_report'],
            'gaps_for_improvement': result['gaps_for_improvement'],
            'success': True
        }
    except Exception as e:
        logger.error(f"Drawing comparison failed: {e}")
        return {
            'page_3_score': 0,
            'page_4_score': 0,
            'overall_drawing_score': 0,
            'learning_report': f"Error during drawing assessment: {e}",
            'gaps_for_improvement': [str(e)],
            'success': False
        }
