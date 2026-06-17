#!/usr/bin/env python3
"""
Detailed visual comparison of generated drawings vs. example PDFs.
Creates side-by-side previews and identifies differences.
"""
import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).parent))

try:
    import cv2
    import numpy as np
    import fitz  # PyMuPDF
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install opencv-python pillow pymupdf")
    sys.exit(1)

OUTPUT_DIR = Path('drawing_comparisons')
OUTPUT_DIR.mkdir(exist_ok=True)

def pdf_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 150) -> np.ndarray:
    """Convert PDF page to image array"""
    try:
        doc = fitz.open(str(pdf_path))
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        doc.close()
        return img_data
    except Exception as e:
        print(f"  Error converting {pdf_path}: {e}")
        return None

def png_to_image(png_path: Path) -> np.ndarray:
    """Load PNG as image array"""
    try:
        return cv2.imread(str(png_path))
    except Exception as e:
        print(f"  Error loading {png_path}: {e}")
        return None

def resize_to_match(img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Resize images to match for comparison"""
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # Resize to smaller dimension to fit side-by-side
    target_h = min(h1, h2)
    target_w = min(w1, w2)

    img1_resized = cv2.resize(img1, (target_w, target_h))
    img2_resized = cv2.resize(img2, (target_w, target_h))

    return img1_resized, img2_resized

def create_side_by_side(img1: np.ndarray, img2: np.ndarray, label1: str, label2: str, output_path: Path):
    """Create side-by-side comparison image"""
    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB) if len(img1.shape) == 3 else cv2.cvtColor(cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB) if len(img2.shape) == 3 else cv2.cvtColor(cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2RGB)

    img1_pil = Image.fromarray(img1_rgb)
    img2_pil = Image.fromarray(img2_rgb)

    # Create side-by-side
    total_w = img1_pil.width + img2_pil.width + 40
    total_h = max(img1_pil.height, img2_pil.height) + 80

    result = Image.new('RGB', (total_w, total_h), color='white')

    # Add labels
    draw = ImageDraw.Draw(result)

    # Try to use a basic font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()

    draw.text((20, 10), label1, fill='black', font=font)
    draw.text((img1_pil.width + 40, 10), label2, fill='black', font=font)

    # Paste images
    result.paste(img1_pil, (20, 60))
    result.paste(img2_pil, (img1_pil.width + 40, 60))

    result.save(str(output_path))
    return output_path

def compare_site_plan():
    """Compare site plan (page 3)"""
    print("\n[COMPARING SITE PLANS]")
    print("-" * 80)

    generated_path = Path('site_plan_pg3.png')
    example_path = Path('example/example 1/26-018 PG3 (1).pdf')

    if not generated_path.exists():
        print(f"✗ Generated site plan not found: {generated_path}")
        return False

    if not example_path.exists():
        print(f"✗ Example PDF not found: {example_path}")
        return False

    print(f"Generated: {generated_path}")
    print(f"Example:   {example_path}")

    # Load images
    print("  Loading images...")
    gen_img = png_to_image(generated_path)
    ex_img = pdf_to_image(example_path, dpi=150)

    if gen_img is None or ex_img is None:
        print("  ✗ Failed to load images")
        return False

    print(f"  Generated size: {gen_img.shape}")
    print(f"  Example size:   {ex_img.shape}")

    # Create comparison
    print("  Creating comparison...")
    try:
        gen_resized, ex_resized = resize_to_match(gen_img, ex_img)
        output = create_side_by_side(gen_resized, ex_resized, "GENERATED", "EXAMPLE", OUTPUT_DIR / "site_plan_comparison.png")
        print(f"  ✓ Comparison saved: {output}")
    except Exception as e:
        print(f"  ✗ Failed to create comparison: {e}")
        return False

    return True

def compare_disposal_plan():
    """Compare disposal plan (page 4 top)"""
    print("\n[COMPARING DISPOSAL PLANS]")
    print("-" * 80)

    generated_path = Path('disposal_plan_pg4.png')
    example_path = Path('example/example 1/26-018 PG4 (1).pdf')

    if not generated_path.exists():
        print(f"✗ Generated disposal plan not found: {generated_path}")
        return False

    if not example_path.exists():
        print(f"✗ Example PDF not found: {example_path}")
        return False

    print(f"Generated: {generated_path}")
    print(f"Example:   {example_path}")

    # Load images
    print("  Loading images...")
    gen_img = png_to_image(generated_path)
    ex_img = pdf_to_image(example_path, page_num=0, dpi=150)  # Page 4 is index 3, but start with 0

    if gen_img is None or ex_img is None:
        print("  ✗ Failed to load images")
        return False

    print(f"  Generated size: {gen_img.shape}")
    print(f"  Example size:   {ex_img.shape}")

    # Create comparison
    print("  Creating comparison...")
    try:
        gen_resized, ex_resized = resize_to_match(gen_img, ex_img)
        output = create_side_by_side(gen_resized, ex_resized, "GENERATED", "EXAMPLE", OUTPUT_DIR / "disposal_plan_comparison.png")
        print(f"  ✓ Comparison saved: {output}")
    except Exception as e:
        print(f"  ✗ Failed to create comparison: {e}")
        return False

    return True

def main():
    print("\n" + "="*80)
    print("DETAILED DRAWING COMPARISON")
    print("="*80)
    print("Comparing Hermes-generated drawings with example PDFs")

    success = True
    success = compare_site_plan() and success
    success = compare_disposal_plan() and success

    print("\n" + "="*80)
    if success:
        print("✓ COMPARISON COMPLETE")
        print(f"Comparisons saved to: {OUTPUT_DIR}/")
    else:
        print("✗ SOME COMPARISONS FAILED")
    print("="*80)

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
