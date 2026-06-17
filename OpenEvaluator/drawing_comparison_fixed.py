"""
Drawing Comparison - Fixed to extract images directly from PDF
"""

import logging
from pathlib import Path
from typing import Dict, List
import fitz
import json

logger = logging.getLogger(__name__)

class DrawingComparatorFixed:
    """Compare drawings by extracting directly from PDF."""
    
    def __init__(self, example_dir: Path, output_dir: Path):
        self.example_pdf_dir = example_dir
        self.output_dir = output_dir
    
    def extract_page_images(self, pdf_path: Path, page_num: int) -> List[Path]:
        """Extract images from PDF page directly using fitz."""
        try:
            doc = fitz.open(str(pdf_path))
            page = doc[page_num - 1]
            images = page.get_images()
            
            extracted_paths = []
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # Skip tiny images (likely noise)
                if pix.width < 100 or pix.height < 100:
                    logger.debug(f"Skipping tiny image {pix.width}x{pix.height}")
                    continue
                
                # Save image
                out_path = self.output_dir / f"page{page_num}_img{img_index}.png"
                pix.save(str(out_path))
                extracted_paths.append(out_path)
                logger.info(f"Extracted image {pix.width}x{pix.height} → {out_path.name}")
            
            doc.close()
            return extracted_paths
        except Exception as e:
            logger.error(f"Failed to extract images: {e}")
            return []
    
    def quick_analyze(self, image_path: Path) -> Dict:
        """Quick analysis of image using CV."""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(str(image_path))
            if img is None:
                return {'error': 'Failed to load', 'width': 0, 'height': 0}
            
            height, width = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            return {
                'width': width,
                'height': height,
                'line_count': len(lines) if lines is not None else 0,
                'contour_count': len(contours),
                'has_content': len(lines) > 10 if lines is not None else False
            }
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_pages(self, generated_pdf: Path) -> Dict:
        """Analyze both pages."""
        result = {}
        
        # Page 3
        print("\n📄 Extracting Page 3 images...")
        page3_imgs = self.extract_page_images(generated_pdf, 3)
        if page3_imgs:
            analysis = self.quick_analyze(page3_imgs[0])
            result['page_3'] = {
                'found': True,
                'image_path': str(page3_imgs[0]),
                'analysis': analysis,
                'has_drawing': analysis.get('has_content', False)
            }
        else:
            result['page_3'] = {'found': False, 'images': 0}
        
        # Page 4
        print("📄 Extracting Page 4 images...")
        page4_imgs = self.extract_page_images(generated_pdf, 4)
        if page4_imgs:
            analysis = self.quick_analyze(page4_imgs[0])
            result['page_4'] = {
                'found': True,
                'image_path': str(page4_imgs[0]),
                'analysis': analysis,
                'has_drawing': analysis.get('has_content', False)
            }
        else:
            result['page_4'] = {'found': False, 'images': 0}
        
        return result

# Run it
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    comparator = DrawingComparatorFixed(
        Path('/home/workspace/OpenEvaluator/example'),
        Path('/home/workspace/OpenEvaluator')
    )
    
    result = comparator.analyze_pages(Path('/home/workspace/OpenEvaluator/HHE-200-filled.pdf'))
    print("\n" + "="*70)
    print("EXTRACTED DRAWING ANALYSIS")
    print("="*70)
    print(json.dumps(result, indent=2))
