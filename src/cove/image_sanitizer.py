"""
image_sanitizer.py — ARGOS Image Processing Pipeline
CoVe 2026 | Enterprise Grade

Sanitizes vehicle images for dealer dossiers:
  1. Crops/blurs license plate area (bottom 18% of frontal images)
  2. Overlays ARGOS branded plate cover over plate zone
  3. Strips EXIF metadata (no source leaks)
  4. Detects dealer watermarks/frames in images

BUSINESS RULE: The dealer must NOT be able to identify the EU seller
from the dossier. Source identity is revealed ONLY after fee payment.

Usage:
  from src.cove.image_sanitizer import sanitize_image, sanitize_all_images

  # Single image
  safe_path = sanitize_image("raw_photo.jpg", output_dir="dossiers/safe/")

  # All images for a listing
  safe_paths = sanitize_all_images(listing_id, db_path, output_dir)
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# EasyOCR — lazy loaded (heavy model, 95MB)
_EASYOCR_READER = None

def _get_ocr_reader():
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        try:
            import easyocr
            _EASYOCR_READER = easyocr.Reader(['de', 'en'], gpu=False, verbose=False)
        except ImportError:
            pass
    return _EASYOCR_READER

# ── Configuration ─────────────────────────────────────────────────────────────

# ARGOS brand colors
ARGOS_BLACK = (26, 26, 26)        # #1A1A1A
ARGOS_GOLD = (200, 164, 70)       # #C8A446
ARGOS_WHITE = (255, 255, 255)

# Plate zone: ONLY the license plate area (small strip at bottom)
# EU plates are ~520x110mm, typically in bottom 10-15% of image
PLATE_ZONE_TOP_PCT = 0.88    # Start of plate strip (88% from top)
PLATE_ZONE_BOTTOM_PCT = 1.0  # End (100%)

# Plate frame text: thin band just above the plate where dealer name sits
PLATE_FRAME_TOP_PCT = 0.82   # Dealer frame starts here
PLATE_FRAME_BOTTOM_PCT = 0.88 # Ends where plate starts

# Top dealer watermark zone — many EU portals/dealers place large logos on top 15-20%
DEALER_LOGO_TOP_PCT = 0.0
DEALER_LOGO_BOTTOM_PCT = 0.18  # Top 18% — covers most dealer watermarks

# ARGOS logo path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ARGOS_LOGO_PATH = PROJECT_ROOT / "assets" / "ARGOS_logo_sobrio_horizontal.png"

# Output directory for sanitized images
DEFAULT_SAFE_DIR = PROJECT_ROOT / "dossiers" / "safe_images"

# Minimum file size — images below this are thumbnails (useless in PDF)
MIN_IMAGE_BYTES = 30 * 1024  # 30 KB


def sanitize_image(
    image_path: str,
    output_dir: str = None,
    listing_id: str = None,
    image_index: int = 0,
) -> Optional[str]:
    """
    Sanitize a single vehicle image:
    1. Strip EXIF metadata
    2. Blur bottom plate zone
    3. Overlay ARGOS branded plate cover
    4. Blur top dealer logo zone (if detected)

    Returns: path to sanitized image, or None on failure.
    """
    if not PILLOW_AVAILABLE:
        print("ERROR: Pillow not installed. pip install Pillow")
        return None

    if not os.path.exists(image_path):
        print(f"  SKIP: image not found: {image_path}")
        return None

    # Skip thumbnails — too small to be useful in a dossier
    file_size = os.path.getsize(image_path)
    if file_size < MIN_IMAGE_BYTES:
        print(f"  SKIP thumbnail: {os.path.basename(image_path)} ({file_size // 1024} KB < {MIN_IMAGE_BYTES // 1024} KB)")
        return None

    # Output setup
    if output_dir is None:
        output_dir = str(DEFAULT_SAFE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    # Output filename
    if listing_id:
        safe_name = f"argos_{listing_id}_{image_index:02d}.jpg"
    else:
        base = Path(image_path).stem
        safe_name = f"argos_safe_{base}.jpg"
    safe_path = os.path.join(output_dir, safe_name)

    try:
        # Open and strip EXIF
        img = Image.open(image_path)
        clean = Image.new(img.mode, img.size)
        clean.paste(img)
        w, h = clean.size

        # ══════════════════════════════════════════════════════════
        # STEP 1: Detect license plates via OpenCV (contour + HSV)
        # ══════════════════════════════════════════════════════════
        plate_rects = []
        if CV2_AVAILABLE:
            plate_rects = _detect_plates_cv2(image_path)

        # ══════════════════════════════════════════════════════════
        # STEP 2: Detect dealer text via EasyOCR
        # ══════════════════════════════════════════════════════════
        text_rects = []
        reader = _get_ocr_reader()
        if reader:
            try:
                results = reader.readtext(image_path, detail=1)
                for bbox_pts, text_str, conf in results:
                    if conf > 0.3:
                        xs = [int(p[0]) for p in bbox_pts]
                        ys = [int(p[1]) for p in bbox_pts]
                        text_rects.append((min(xs), min(ys), max(xs), max(ys), text_str))
            except Exception as e:
                print(f"  [OCR] EasyOCR error: {e}")

        # ══════════════════════════════════════════════════════════
        # STEP 3: Cover plates with ARGOS branded bar
        # ══════════════════════════════════════════════════════════
        draw = ImageDraw.Draw(clean)

        if plate_rects:
            for px, py, pw, ph in plate_rects:
                # Draw ARGOS branded plate cover
                draw.rectangle([(px, py), (px + pw, py + ph)], fill=ARGOS_BLACK)
                # Add ARGOS text centered on plate
                try:
                    pfont_size = max(8, int(ph * 0.45))
                    try:
                        pfont = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", pfont_size)
                    except OSError:
                        try:
                            pfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", pfont_size)
                        except OSError:
                            pfont = ImageFont.load_default()
                except Exception:
                    pfont = ImageFont.load_default()
                ptext = "ARGOS"
                pbb = draw.textbbox((0, 0), ptext, font=pfont)
                ptw, pth = pbb[2] - pbb[0], pbb[3] - pbb[1]
                draw.text((px + (pw - ptw) // 2, py + (ph - pth) // 2), ptext, fill=ARGOS_GOLD, font=pfont)
        else:
            # Fallback: no plate detected — add ARGOS bar at bottom 10%
            bar_top = int(h * 0.90)
            draw.rectangle([(int(w * 0.20), bar_top), (int(w * 0.80), h)], fill=ARGOS_BLACK)
            try:
                fs = max(10, int((h - bar_top) * 0.40))
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fs)
                except OSError:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
                    except OSError:
                        font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            text = "ARGOS AUTOMOTIVE"
            bb = draw.textbbox((0, 0), text, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            draw.text(((w - tw) // 2, bar_top + ((h - bar_top - th) // 2)), text, fill=ARGOS_GOLD, font=font)

        # ══════════════════════════════════════════════════════════
        # STEP 4: Cover dealer text with black rectangles
        # ══════════════════════════════════════════════════════════
        # Blackout any detected text that looks like dealer info
        # (not car spec text like "xDrive" or "Automatik")
        # Blackout detected text that could identify the seller
        # Keep only pure car spec words (engine, transmission codes)
        _keep_words = {'xdrive', 'sdrive', 'quattro', 'tfsi', 'tdi', 'cdi',
                       'diesel', 'benzin', 'hybrid', 'electric',
                       'automatik', 'automatic', 'schaltung',
                       'argos', 'automotive'}
        has_bottom_text = False
        for tx1, ty1, tx2, ty2, ttext in text_rects:
            words_lower = ttext.lower().strip().split()
            # Skip if it's pure car spec terminology
            if all(w in _keep_words or len(w) <= 2 or w.replace('.', '').isdigit() for w in words_lower):
                continue
            # Skip tiny text (noise)
            if (tx2 - tx1) < 20 or (ty2 - ty1) < 6:
                continue
            # Track if text found in bottom 20% (dealer banner zone)
            if ty1 > h * 0.80:
                has_bottom_text = True
            # Cover with black + padding
            pad = 5
            draw.rectangle([(tx1 - pad, ty1 - pad), (tx2 + pad, ty2 + pad)], fill=ARGOS_BLACK)

        # If any dealer text detected in bottom 20%, blackout the entire bottom strip
        # This catches logos and small text that OCR might miss
        if has_bottom_text:
            bot_bar = int(h * 0.82)
            draw.rectangle([(0, bot_bar), (w, h)], fill=ARGOS_BLACK)
            # Add ARGOS branding on the bottom bar
            try:
                bfs = max(10, int((h - bot_bar) * 0.30))
                try:
                    bfont = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", bfs)
                except OSError:
                    try:
                        bfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", bfs)
                    except OSError:
                        bfont = ImageFont.load_default()
            except Exception:
                bfont = ImageFont.load_default()
            btext = "ARGOS AUTOMOTIVE"
            bbb = draw.textbbox((0, 0), btext, font=bfont)
            btw = bbb[2] - bbb[0]
            bth = bbb[3] - bbb[1]
            draw.text(((w - btw) // 2, bot_bar + ((h - bot_bar - bth) // 2)),
                      btext, fill=ARGOS_GOLD, font=bfont)

        # ── Step 5: Save as JPEG (strips all metadata) ──
        if clean.mode == 'RGBA':
            clean = clean.convert('RGB')
        clean.save(safe_path, 'JPEG', quality=90)

        size_kb = os.path.getsize(safe_path) / 1024
        print(f"  SANITIZED: {safe_name} ({size_kb:.0f} KB)")
        return safe_path

    except Exception as e:
        print(f"  ERROR sanitizing {image_path}: {e}")
        return None


def _overlay_argos_plate_cover(img: Image.Image, plate_top: int, w: int, h: int) -> Image.Image:
    """
    Overlay a branded ARGOS plate cover bar on the plate zone.
    Dark bar with ARGOS text + gold accent.
    """
    draw = ImageDraw.Draw(img)

    # Plate cover bar dimensions
    bar_height = h - plate_top
    bar_y_center = plate_top + bar_height // 2

    # Draw semi-transparent dark bar across bottom
    # Pillow doesn't support alpha on non-RGBA, so we just draw a solid bar
    # slightly above the very bottom to look intentional
    bar_top = plate_top + int(bar_height * 0.15)
    bar_bottom = h - int(bar_height * 0.15)

    # Dark bar
    draw.rectangle(
        [(w * 0.15, bar_top), (w * 0.85, bar_bottom)],
        fill=ARGOS_BLACK
    )

    # Gold accent lines
    draw.line(
        [(w * 0.15, bar_top), (w * 0.85, bar_top)],
        fill=ARGOS_GOLD, width=2
    )
    draw.line(
        [(w * 0.15, bar_bottom), (w * 0.85, bar_bottom)],
        fill=ARGOS_GOLD, width=2
    )

    # ARGOS text in plate cover
    text = "ARGOS AUTOMOTIVE"
    try:
        # Try to use a reasonable font size
        font_size = max(14, int(bar_height * 0.35))
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (w - text_w) // 2
    text_y = (bar_top + bar_bottom - text_h) // 2

    draw.text((text_x, text_y), text, fill=ARGOS_GOLD, font=font)

    return img


def sanitize_all_images(
    listing_id: str,
    db_path: str = None,
    output_dir: str = None,
    download_first: bool = True,
) -> List[str]:
    """
    Sanitize all images for a listing:
    1. Get image URLs from vehicle_images table
    2. Download if needed
    3. Sanitize each image
    4. Return list of safe image paths
    """
    if db_path is None:
        db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")

    if output_dir is None:
        output_dir = str(DEFAULT_SAFE_DIR)
    os.makedirs(output_dir, exist_ok=True)

    try:
        import duckdb
        db = duckdb.connect(db_path, read_only=True)
        rows = db.execute(
            "SELECT image_url, local_path FROM vehicle_images WHERE listing_id = ? ORDER BY rowid",
            [listing_id]
        ).fetchall()
        db.close()
    except Exception as e:
        print(f"  ERROR reading images from DB: {e}")
        return []

    if not rows:
        print(f"  No images found for listing {listing_id}")
        return []

    # ── Dedup URLs: AS24 stores same photo in 10 resolutions ──
    # Keep only highest resolution per unique image UUID
    import re as _re
    unique_images = {}
    for url, local_path in rows:
        if not url:
            continue
        # Extract base UUID from URL (before resolution suffix like /1280x960.webp)
        base = _re.sub(r'/\d+x\d+\.(jpg|webp|png)$', '', url.split('?')[0])
        # Parse resolution
        res_match = _re.search(r'/(\d+)x(\d+)\.(jpg|webp|png)$', url)
        res = int(res_match.group(1)) * int(res_match.group(2)) if res_match else 0
        # Prefer jpg over webp at same resolution, prefer highest resolution
        if base not in unique_images or res > unique_images[base][2]:
            unique_images[base] = (url, local_path, res)

    deduped_rows = [(v[0], v[1]) for v in unique_images.values()]
    if len(deduped_rows) < len(rows):
        print(f"  URL dedup: {len(rows)} → {len(deduped_rows)} unique images")
    rows = deduped_rows

    safe_paths = []
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    for i, (url, local_path) in enumerate(rows):
        # Determine source path
        src_path = None

        # Try local path first
        if local_path and os.path.exists(local_path):
            src_path = local_path
        elif download_first and url:
            # Download from URL
            src_path = _download_image(url, raw_dir, listing_id, i)

        if src_path and os.path.exists(src_path):
            safe = sanitize_image(src_path, output_dir, listing_id, i)
            if safe:
                safe_paths.append(safe)

    # Dedup disabled — perceptual hash too aggressive on studio photos
    # where all images share the same background after banner crop.
    # TODO: implement content-aware dedup (detect car angle, not background)

    print(f"  Sanitized {len(safe_paths)}/{len(rows)} images for {listing_id}")
    return safe_paths


def _detect_plates_cv2(image_path: str) -> List[Tuple[int, int, int, int]]:
    """
    Detect EU license plates using OpenCV contour + HSV color detection.
    EU plates: white rectangle, aspect ratio ~4.7:1.
    Returns list of (x, y, w, h) bounding rectangles.
    """
    if not CV2_AVAILABLE:
        return []
    try:
        img = cv2.imread(image_path)
        if img is None:
            return []
        h_img, w_img = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # White color range — EU plates are white with blue left band
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([255, 60, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Morphological ops to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            img_area = w_img * h_img

            # EU plate constraints:
            # - Aspect ratio 3.5-6.0 (standard is ~4.7)
            # - Area between 0.2% and 5% of image
            # - Width between 5% and 30% of image width
            if (3.0 < aspect_ratio < 6.5
                    and 0.002 < area / img_area < 0.05
                    and 0.05 < w / w_img < 0.35):
                plates.append((x, y, w, h))

        # Remove overlapping detections — keep largest
        plates.sort(key=lambda p: p[2] * p[3], reverse=True)
        filtered = []
        for p in plates:
            overlap = False
            for f in filtered:
                # Check if centers are close
                cx1, cy1 = p[0] + p[2]//2, p[1] + p[3]//2
                cx2, cy2 = f[0] + f[2]//2, f[1] + f[3]//2
                if abs(cx1 - cx2) < p[2] and abs(cy1 - cy2) < p[3]:
                    overlap = True
                    break
            if not overlap:
                filtered.append(p)

        return filtered[:3]  # Max 3 plates (front, rear, side)
    except Exception as e:
        print(f"  [CV2] Plate detection error: {e}")
        return []


def _perceptual_hash(image_path: str) -> Optional[str]:
    """Compute a simple perceptual hash: resize to 8x8 grayscale, threshold to binary."""
    try:
        img = Image.open(image_path).convert('L').resize((8, 8), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        return bits
    except Exception:
        return None


def _perceptual_hash_16(image_path: str) -> Optional[str]:
    """Higher resolution perceptual hash (16x16=256 bits) for better discrimination."""
    try:
        img = Image.open(image_path).convert('L').resize((16, 16), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        return bits
    except Exception:
        return None


def _hamming_distance(h1: str, h2: str) -> int:
    """Count differing bits between two hashes."""
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def _dedup_images(image_paths: List[str], threshold: int = 2) -> List[str]:
    """
    Remove near-duplicate images using perceptual hashing.
    threshold: max hamming distance to consider duplicate (lower = stricter).
    2 out of 64 bits = ~3% — only truly identical photos removed.

    Uses 16x16 hash for better discrimination between different car angles.
    """
    if not PILLOW_AVAILABLE:
        return image_paths

    hashes = []
    unique = []
    for path in image_paths:
        h = _perceptual_hash_16(path)
        if h is None:
            unique.append(path)
            continue
        is_dup = False
        for existing_h in hashes:
            if _hamming_distance(h, existing_h) <= threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(path)
            hashes.append(h)
    return unique


def _download_image(url: str, output_dir: str, listing_id: str, index: int) -> Optional[str]:
    """Download image from URL to local path."""
    try:
        import requests
        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        resp.raise_for_status()

        ext = '.jpg'
        if 'webp' in url or 'webp' in resp.headers.get('content-type', ''):
            ext = '.webp'
        elif 'png' in url:
            ext = '.png'

        filename = f"raw_{listing_id}_{index:02d}{ext}"
        path = os.path.join(output_dir, filename)

        with open(path, 'wb') as f:
            f.write(resp.content)

        # Convert webp to jpg for compatibility
        if ext == '.webp' and PILLOW_AVAILABLE:
            img = Image.open(path)
            jpg_path = path.replace('.webp', '.jpg')
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(jpg_path, 'JPEG', quality=92)
            os.remove(path)
            return jpg_path

        return path
    except Exception as e:
        print(f"  ERROR downloading {url}: {e}")
        return None


def check_image_sufficient(listing_id: str, db_path: str = None, min_photos: int = 4) -> dict:
    """
    Check if a listing has enough photos for a complete dossier.

    Returns dict:
      sufficient: bool
      photo_count: int
      min_required: int
      missing_views: list of str (e.g. ["interior", "rear", "engine"])
    """
    if db_path is None:
        db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")

    try:
        import duckdb
        db = duckdb.connect(db_path, read_only=True)
        count = db.execute(
            "SELECT COUNT(*) FROM vehicle_images WHERE listing_id = ?",
            [listing_id]
        ).fetchone()[0]
        db.close()
    except Exception:
        count = 0

    # Ideal views for a complete dossier
    ideal_views = ["front", "rear", "side_left", "side_right", "interior_front", "interior_rear", "dashboard", "engine"]

    sufficient = count >= min_photos
    missing_count = max(0, min_photos - count)

    return {
        "sufficient": sufficient,
        "photo_count": count,
        "min_required": min_photos,
        "missing_count": missing_count,
        "ideal_views": ideal_views,
        "message": f"{count} foto disponibili" if sufficient else f"Solo {count} foto — servono almeno {min_photos} per un dossier completo"
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 src/cove/image_sanitizer.py <listing_id>           # Sanitize all images")
        print("  python3 src/cove/image_sanitizer.py --file <image_path>    # Sanitize single file")
        print("  python3 src/cove/image_sanitizer.py --check <listing_id>   # Check photo sufficiency")
        sys.exit(1)

    if sys.argv[1] == "--file" and len(sys.argv) >= 3:
        result = sanitize_image(sys.argv[2])
        if result:
            print(f"\nSanitized: {result}")
        else:
            print("\nFailed to sanitize image")
            sys.exit(1)
    elif sys.argv[1] == "--check" and len(sys.argv) >= 3:
        info = check_image_sufficient(sys.argv[2])
        print(f"\nPhoto check for {sys.argv[2]}:")
        print(f"  Photos: {info['photo_count']}")
        print(f"  Sufficient: {info['sufficient']}")
        print(f"  {info['message']}")
        if not info['sufficient']:
            print(f"\n  Ideal views needed:")
            for v in info['ideal_views']:
                print(f"    - {v}")
    else:
        listing_id = sys.argv[1]
        results = sanitize_all_images(listing_id)
        print(f"\nSanitized {len(results)} images for {listing_id}")
        for p in results:
            print(f"  {p}")
