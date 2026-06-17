#!/usr/bin/env python3
"""
Sketch extraction & data combination pipeline.

Downloads hand-drawn sketches from Google Drive (column T), extracts data using Claude Opus 4.8 Vision,
queries Google Maps for property info, and combines into comprehensive HHE-200 form data.
"""
import argparse
import base64
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

# Add local python_packages to path for Vision API and dependencies
local_packages = Path(__file__).parent / "python_packages"
if local_packages.exists():
    sys.path.insert(0, str(local_packages))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main(drive_folder_id: str, address_line: str, dry_run: bool = False) -> dict:
    """
    Main extraction pipeline.
    
    Args:
        drive_folder_id: Google Drive folder ID containing sketch files (from column T)
        address_line: Property address for Maps queries
        dry_run: If True, log actions without executing
    
    Returns:
        dict with extracted sketch data and external property info
    """
    
    logger.info(f"Starting sketch extraction pipeline (dry_run={dry_run})")
    
    extracted_data = {
        "sketch_files": [],
        "sketch_text": [],
        "soil_info": {},
        "elevations": {},
        "gps_locations": {},
        "tie_items": [],
        "maps_data": {},
    }
    
    if not drive_folder_id:
        logger.warning("No Drive folder ID provided, skipping sketch extraction")
        return extracted_data
    
    # Step 1: Download sketch files from Google Drive
    logger.info(f"Step 1: Downloading sketches from Drive folder {drive_folder_id}")
    sketch_files = _download_sketches(drive_folder_id, dry_run=dry_run)
    extracted_data["sketch_files"] = sketch_files
    
    if not sketch_files:
        logger.warning("No sketch files downloaded")
        return extracted_data
    
    # Step 2: Extract text & data from sketches using Claude Opus 4.8
    logger.info(f"Step 2: Extracting data from {len(sketch_files)} sketch files using Claude Opus 4.8")
    for filepath in sketch_files:
        text_data = _extract_sketch_text_claude(filepath, dry_run=dry_run)
        if text_data:
            extracted_data["sketch_text"].append({
                "file": Path(filepath).name,
                "text": text_data,
            })
            _parse_sketch_data(text_data, extracted_data, dry_run=dry_run)
    
    # Step 3: Query Google Maps for property info
    logger.info(f"Step 3: Querying Google Maps for adjacent roads and boundaries")
    maps_results = _query_maps_api(address_line, dry_run=dry_run)
    extracted_data["maps_data"] = maps_results
    
    logger.info("✓ Sketch extraction complete")
    return extracted_data


def _download_sketches(folder_id: str, dry_run: bool = False) -> list:
    """Download sketch files from Google Drive folder OR direct file using google-api-python-client."""
    logger.info(f"  Downloading files from Drive ID {folder_id}")

    sketch_files = []
    out_dir = Path(__file__).parent / "sketches"

    if not dry_run:
        out_dir.mkdir(exist_ok=True)

        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload
            import io

            credentials = None

            # Try service account first (if properly configured)
            vision_key_json = os.environ.get("GOOGLE_CLOUD_VISION_KEY")
            if vision_key_json:
                try:
                    creds_dict = json.loads(vision_key_json)
                    if "client_email" in creds_dict and "token_uri" in creds_dict:
                        credentials = service_account.Credentials.from_service_account_info(
                            creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
                        )
                        logger.info("    Using service account credentials")
                except Exception as e:
                    logger.warning(f"    Service account credentials failed: {e}")

            # Fall back to OAuth credentials from local files
            if not credentials:
                cred_files = [
                    Path.home() / ".config" / "google_oauth_credentials.json",
                    Path.home() / ".hermes" / "google_token.json",
                ]
                for cred_file in cred_files:
                    if cred_file.exists():
                        try:
                            creds_data = json.loads(cred_file.read_text())
                            # If it's a token, try to use it directly
                            if "access_token" in creds_data:
                                credentials = Credentials.from_authorized_user_info(creds_data)
                                logger.info(f"    Using OAuth credentials from {cred_file.name}")
                                break
                            # If it's client credentials, skip (can't use without token)
                        except Exception as e:
                            logger.debug(f"    Could not load {cred_file.name}: {e}")

            if not credentials:
                logger.warning("    No valid credentials found for Drive access")
                return sketch_files

            # Build Drive service
            drive_service = build('drive', 'v3', credentials=credentials)

            # First, check if the ID is a file or folder
            file_metadata = drive_service.files().get(
                fileId=folder_id,
                fields="id,name,mimeType"
            ).execute()
            
            file_name = file_metadata.get("name", "unknown")
            mime_type = file_metadata.get("mimeType", "")
            
            # If it's a file (not a folder), download it directly
            if mime_type != "application/vnd.google-apps.folder":
                logger.info(f"    ID points to file: {file_name}")
                if "image/" in mime_type or "pdf" in mime_type.lower():
                    out_path = out_dir / file_name
                    logger.info(f"    Downloading {file_name}")
                    try:
                        request = drive_service.files().get_media(fileId=folder_id)
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                        out_path.write_bytes(fh.getvalue())
                        sketch_files.append(str(out_path))
                        logger.info(f"      ✓ Saved to {out_path}")
                    except Exception as e:
                        logger.error(f"      ✗ Download failed: {e}")
                else:
                    logger.warning(f"    File {file_name} is not an image or PDF (mime: {mime_type})")
                return sketch_files
            
            # Otherwise, it's a folder - list files inside
            logger.info(f"    ID points to folder: {file_name}")
            query = f"'{folder_id}' in parents and trashed=false"
            results = drive_service.files().list(
                q=query,
                pageSize=100,
                fields="files(id,name,mimeType)"
            ).execute()

            files_list = results.get("files", [])
            logger.info(f"    Found {len(files_list)} files in folder")

            for file_obj in files_list:
                file_id = file_obj["id"]
                file_name = file_obj["name"]
                mime = file_obj.get("mimeType", "")

                # Only download image/PDF files
                if "image/" in mime or "pdf" in mime.lower():
                    out_path = out_dir / file_name
                    logger.info(f"    Downloading {file_name}")

                    try:
                        request = drive_service.files().get_media(fileId=file_id)
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()

                        out_path.write_bytes(fh.getvalue())
                        sketch_files.append(str(out_path))
                        logger.info(f"      ✓ Saved to {out_path}")
                    except Exception as e:
                        logger.error(f"      ✗ Download failed: {e}")

        except ImportError:
            logger.error("  google-api-python-client not installed. Install with: pip install google-api-python-client")
        except Exception as e:
            logger.error(f"  Exception during download: {e}")

    else:
        logger.info(f"  [DRY RUN] Would download files from {folder_id}")

    return sketch_files


def _preprocess_image(img_array, use_enhanced: bool = True) -> object:
    """Enhance image for better OCR: deskew, contrast, denoise, adaptive threshold."""
    if use_enhanced:
        try:
            from enhanced_preprocessing import preprocess_image_enhanced
            return preprocess_image_enhanced(img_array, aggressive=True, upscale=4)
        except ImportError:
            logger.warning("    enhanced_preprocessing not available, falling back to basic")
            pass

    # Fallback: Basic preprocessing
    try:
        import cv2
        import numpy as np

        # Convert PIL Image to numpy array if needed
        if hasattr(img_array, 'tobytes'):
            img_array = np.array(img_array)

        # 1. Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # 2. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)

        # 3. Denoise
        denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=10)

        # 4. Sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]]) / 9
        sharpened = cv2.filter2D(denoised, -1, kernel)

        # 5. Adaptive thresholding (better than fixed threshold)
        binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)

        # 6. Dilation to fill gaps in handwritten text
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        logger.info(f"    Basic preprocessing: deskew-ready, contrast+denoise+adaptive-threshold+dilate")
        return dilated

    except ImportError:
        logger.warning("    opencv-python not installed, skipping image preprocessing")
        return img_array
    except Exception as e:
        logger.warning(f"    Image preprocessing failed: {e}, continuing with original")
        return img_array


def _extract_sketch_text_claude(filepath: str, dry_run: bool = False) -> str:
    """Extract text from sketch using Claude Opus 4.8 Vision API.

    For PDFs, converts pages to images first, then analyzes with Claude.
    Claude is better at understanding handwritten sketches and technical drawings.
    """
    logger.info(f"  Extracting text from {Path(filepath).name}")

    if dry_run:
        logger.info(f"    [DRY RUN] Would call Claude Opus 4.8 for OCR")
        return ""

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.error("    ANTHROPIC_API_KEY not set")
        return ""

    try:
        import io
        from PIL import Image
        import numpy as np

        # Convert PDF to images if needed
        image_data_list = []
        filepath_obj = Path(filepath)

        if filepath_obj.suffix.lower() == ".pdf":
            logger.info(f"    Converting PDF to images...")
            try:
                from pdf2image import convert_from_path

                pages = convert_from_path(filepath, dpi=300)
                logger.info(f"    Found {len(pages)} pages in PDF")

                for i, page in enumerate(pages):
                    img_bytes = io.BytesIO()
                    page.save(img_bytes, format='PNG')
                    image_data_list.append((f"page_{i+1}", img_bytes.getvalue()))
                    logger.info(f"      Converted page {i+1}")

            except ImportError as e:
                logger.error(f"    Dependencies not installed: {e}")
                return ""
            except Exception as e:
                logger.error(f"    PDF conversion failed: {e}")
                return ""
        else:
            # For regular image files, read directly
            with open(filepath, 'rb') as f:
                img_bytes = io.BytesIO(f.read())
            image_data_list = [(filepath_obj.name, img_bytes.getvalue())]

        # Call Claude Opus 4.8 on each image
        all_text = []
        for img_name, img_data in image_data_list:
            try:
                text = _call_claude_vision(
                    img_data,
                    prompt="Extract all text, numbers, labels, and handwritten notes from this sketch. Include all dimensions, measurements, and annotations. Format the output as a clear readable text document.",
                    api_key=anthropic_key,
                    model="claude-opus-4-8"
                )

                if text and len(text.strip()) > 0:
                    all_text.append(text)
                    logger.info(f"      {img_name}: {len(text)} characters extracted")
                else:
                    logger.warning(f"      {img_name}: No text extracted")

            except Exception as e:
                logger.error(f"      Claude API error on {img_name}: {e}")

        full_text = "\n---PAGE BREAK---\n".join(all_text)
        logger.info(f"    ✓ Total extracted: {len(full_text)} characters")
        return full_text

    except Exception as e:
        logger.error(f"    Extraction error: {e}")
        return ""


def _call_claude_vision(image_data: bytes, prompt: str, api_key: str, model: str = "claude-opus-4-8") -> str:
    """Call Claude Opus 4.8 with vision to extract text from image."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Encode image to base64
        img_b64 = base64.standard_b64encode(image_data).decode('utf-8')

        # Call Claude with vision
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        return response.content[0].text

    except ImportError:
        logger.error("    anthropic package not installed. Install with: pip install anthropic")
        raise
    except Exception as e:
        logger.error(f"    Claude API call failed: {e}")
        raise


def _parse_sketch_data(text: str, extracted_data: dict, dry_run: bool = False) -> None:
    """Parse extracted text to find soil, elevation, GPS, and tie item data.

    Handles various handwriting styles and formats from field sketches.
    """

    logger.info(f"    Parsing extracted text ({len(text)} characters)...")

    # Normalize text for better matching
    normalized_text = text.upper()

    # ===== SOIL INFORMATION EXTRACTION =====
    soil_patterns = [
        # Soil type at depth: "SAND @ 12 IN" or "SAND 12'"
        r"([A-Z\s]+?(?:SAND|GRAVEL|CLAY|SILT|LOAM))[,\s]+(?:@|AT|DEPTH[:\s]*)?[\s]*(\d+)[\s]*(?:IN|INCH|FT|FEET|')",
        # Simple soil types
        r"(?:SOIL|TYPE)[:\s]*([A-Z\s,\&]+?)(?=\n|DEPTH|ELEVATION|TEXTURE|$)",
        r"(?:TEXTURE|COLOR)[:\s]*([A-Z\s,\&]+?)(?=\n|$)",
    ]

    for pattern in soil_patterns:
        matches = re.finditer(pattern, normalized_text)
        for match in matches:
            soil_desc = match.group(1).strip()
            if soil_desc and len(soil_desc) > 2:
                extracted_data["soil_info"]["description"] = soil_desc
                logger.info(f"    Found soil: {soil_desc[:50]}")
                if len(match.groups()) > 1 and match.group(2):
                    extracted_data["soil_info"]["depth_inches"] = match.group(2)

    # ===== ELEVATION EXTRACTION =====
    elev_patterns = [
        # ERP or reference point elevation: "ERP 1247.5" or "REF 1247.5 FT"
        r"(?:ERP|ELEVATION\s+REFERENCE|REFERENCE\s+POINT)[:\s]*([+-]?\d+\.?\d*)\s*(?:FT|FEET)?",
        # General elevation: "ELEVATION: 1247.5" or "ELEV 1247.5"
        r"(?:ELEVATION|ELEV)[:\s]*([+-]?\d+\.?\d*)\s*(?:FT|FEET)?",
        # Finished grade or top of system
        r"(?:FINISHED\s+GRADE|GRADE|TOP\s+OF\s+TANK|TOP\s+PIPE)[:\s]*([+-]?\d+\.?\d*)",
        # Bottom elevation
        r"(?:BOTTOM|BOTTOM\s+OF\s+FIELD)[:\s]*([+-]?\d+\.?\d*)",
    ]

    for pattern in elev_patterns:
        matches = re.finditer(pattern, normalized_text)
        for match in matches:
            elev_val = match.group(1)
            if elev_val:
                extracted_data["elevations"]["value"] = elev_val
                logger.info(f"    Found elevation: {elev_val} ft")

    # ===== GPS COORDINATE EXTRACTION =====
    gps_patterns = [
        # DMS format: "44° 15' 18.56"" (with or without direction)
        r"(\d+)°\s*(\d+)'\s*([0-9.]+)\"",
        # Decimal format: "44.2551547, -70.216111"
        r"(44\.\d+)\s*,\s*(-70\.\d+)",
    ]

    for pattern in gps_patterns:
        matches = re.finditer(pattern, text)  # Use original text for GPS to preserve formatting
        for match in matches:
            gps_str = match.group(0)
            extracted_data["gps_locations"]["raw"] = gps_str
            logger.info(f"    Found GPS: {gps_str}")

    # ===== ADJACENT PROPERTY & LOT INFORMATION =====
    lot_patterns = [
        # Adjacent lot numbers: "LOT 2", "LOT 6", "LOT 7"
        r"\b(?:LOT|LOT\s*#)[\s]*(\d+)\b",
        # Tax map references: "MAP 26 LOT 18"
        r"(?:TAX\s+MAP|MAP)[\s]*(\d+)\s*(?:LOT|LOT\s*#)[\s]*(\d+)",
    ]

    adjacent_lots = []
    for pattern in lot_patterns:
        matches = re.finditer(pattern, normalized_text)
        for match in matches:
            if len(match.groups()) == 1:
                lot_num = match.group(1)
            else:
                lot_num = match.group(2)
            if lot_num and lot_num not in adjacent_lots:
                adjacent_lots.append(lot_num)

    if adjacent_lots:
        extracted_data["property_info"] = extracted_data.get("property_info", {})
        extracted_data["property_info"]["adjacent_lots"] = adjacent_lots
        logger.info(f"    Found adjacent lots: {', '.join(adjacent_lots)}")

    # ===== STREET NAME EXTRACTION =====
    street_patterns = [
        # Street references: "ASPEN WAY", "OAK'S ROAD", "MAIN STREET"
        r"\b([A-Z][A-Z\s&']+?)(?:\s+(?:ROAD|STREET|WAY|DRIVE|AVENUE|AVENUE|LANE|PATH|TRAIL|CIRCLE))\b",
        # Simple street names preceded by "Street:" or "Road:"
        r"(?:STREET|ROAD|WAY)[:\s]*([A-Z][A-Z\s&']+?)(?=\n|$|\d)",
    ]

    adjacent_streets = []
    for pattern in street_patterns:
        matches = re.finditer(pattern, normalized_text)
        for match in matches:
            street = match.group(1 if len(match.groups()) == 1 else 1).strip()
            if street and len(street) > 2 and street not in adjacent_streets:
                adjacent_streets.append(street)

    if adjacent_streets:
        extracted_data["property_info"] = extracted_data.get("property_info", {})
        extracted_data["property_info"]["adjacent_streets"] = adjacent_streets
        logger.info(f"    Found adjacent streets: {', '.join(adjacent_streets)}")

    # ===== TIE ITEM EXTRACTION (Property corners, wells, trees, etc.) =====
    tie_patterns = [
        # Standard format: "NW CORNER TO SE CORNER: 145 FT"
        r"([A-Z\s\&]+?(?:CORNER|WELL|TREE|BUILDING|HOUSE|MARKER))[:\s]*TO[:\s]*([A-Z\s\&]+?(?:CORNER|WELL|TREE|BUILDING|HOUSE|MARKER|SYSTEM|TANK|FIELD))[:\s]*(\d+)\s*(?:FT|FEET|')?",
        # Alternative format: "DISTANCE FROM NW CORNER TO TANK: 95'"
        r"(?:DISTANCE|FROM)\s+([A-Z\s\&]+?)(?:TO|TOWARD)[:\s]*([A-Z\s\&]+?)[:\s]*(\d+)\s*(?:FT|FEET|')?",
        # Compact format: "NW COR - TANK = 145'"
        r"([A-Z\s\&]+?)[\s\-]+(?:TO|=)[\s]*([A-Z\s\&]+?)[:\s]*(\d+)'",
    ]

    for pattern in tie_patterns:
        matches = re.finditer(pattern, normalized_text)
        for match in matches:
            if len(match.groups()) >= 3:
                from_item = match.group(1).strip()
                to_item = match.group(2).strip()
                distance = match.group(3)

                # Filter out noise
                if from_item and to_item and distance and len(from_item) > 2 and len(to_item) > 2:
                    extracted_data["tie_items"].append({
                        "from": from_item,
                        "to": to_item,
                        "distance_ft": distance,
                    })
                    logger.info(f"    Found tie item: {from_item} → {to_item} = {distance}'")


def _query_maps_api(address_line: str, dry_run: bool = False) -> dict:
    """Query Google Maps for adjacent roads and property boundary info."""
    logger.info(f"  Querying Google Maps for {address_line}")
    
    maps_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not maps_key:
        logger.warning("    GOOGLE_MAPS_API_KEY not set, skipping Maps queries")
        return {}
    
    if dry_run:
        logger.info(f"    [DRY RUN] Would query Maps API for roads/boundaries")
        return {}
    
    maps_results = {
        "address": address_line,
        "adjacent_roads": [],
        "coordinates": {},
    }
    
    try:
        import googlemaps
        
        client = googlemaps.Client(key=maps_key)
        
        # Geocode address to get coordinates
        geocode_result = client.geocode(address=address_line)
        if geocode_result:
            loc = geocode_result[0]["geometry"]["location"]
            maps_results["coordinates"] = {
                "lat": loc["lat"],
                "lng": loc["lng"],
            }
            logger.info(f"    ✓ Found coordinates: {loc['lat']}, {loc['lng']}")
            
            # Query nearby roads using Reverse Geocode
            reverse_result = client.reverse_geocode(
                latlng=(loc["lat"], loc["lng"]),
                result_type="route"
            )
            
            for result in reverse_result:
                road_name = result.get("formatted_address", "")
                if road_name and "road" in road_name.lower() or "street" in road_name.lower():
                    maps_results["adjacent_roads"].append(road_name)
            
            if maps_results["adjacent_roads"]:
                logger.info(f"    ✓ Found {len(maps_results['adjacent_roads'])} adjacent roads")
        
        return maps_results
    
    except ImportError:
        logger.warning("    googlemaps not installed, skipping Maps queries")
        return maps_results
    except Exception as e:
        logger.error(f"    Maps API error: {e}")
        return maps_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract sketch data and property info")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID from column T")
    parser.add_argument("--address", required=True, help="Property address for Maps queries")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    parser.add_argument("--output", help="Output JSON file for extracted data")
    
    args = parser.parse_args()
    
    result = main(args.folder_id, args.address, dry_run=args.dry_run)
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"✓ Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    sys.exit(0)
