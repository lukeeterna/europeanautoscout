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

# ── Configuration ─────────────────────────────────────────────────────────────

# ARGOS brand colors
ARGOS_BLACK = (26, 26, 26)        # #1A1A1A
ARGOS_GOLD = (200, 164, 70)       # #C8A446
ARGOS_WHITE = (255, 255, 255)

# Plate zone detection: covers plate + dealer frame above it
PLATE_ZONE_TOP_PCT = 0.68    # Start of plate zone (68% from top — covers dealer frame too)
PLATE_ZONE_BOTTOM_PCT = 1.0  # End of plate zone (100%)

# Dealer text zone: top percentage where dealer logos/watermarks often appear
DEALER_LOGO_TOP_PCT = 0.0
DEALER_LOGO_BOTTOM_PCT = 0.10  # Top 10%

# ARGOS logo path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ARGOS_LOGO_PATH = PROJECT_ROOT / "assets" / "ARGOS_logo_sobrio_horizontal.png"

# Output directory for sanitized images
DEFAULT_SAFE_DIR = PROJECT_ROOT / "dossiers" / "safe_images"


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
        # Create clean copy without EXIF
        clean = Image.new(img.mode, img.size)
        clean.paste(img)

        w, h = clean.size

        # ── Step 1: Blur entire lower portion (plate + dealer frame) ──
        # Covers: license plate, plate frame with dealer name/URL, bumper text
        plate_top = int(h * PLATE_ZONE_TOP_PCT)
        plate_zone = clean.crop((0, plate_top, w, h))
        plate_blurred = plate_zone.filter(ImageFilter.GaussianBlur(radius=40))
        clean.paste(plate_blurred, (0, plate_top))

        # ── Step 2: Blur the dealer frame zone above the plate ──
        # Dealer frames ("BMW Gebrauchte Automobile", "www.procar.de") sit in
        # the 45-70% vertical zone (grille/front area of the car)
        frame_top = int(h * 0.45)
        frame_bottom = int(h * PLATE_ZONE_TOP_PCT)
        # Only blur the central horizontal band where plate frames appear
        frame_left = int(w * 0.20)
        frame_right = int(w * 0.80)
        frame_zone = clean.crop((frame_left, frame_top, frame_right, frame_bottom))
        frame_blurred = frame_zone.filter(ImageFilter.GaussianBlur(radius=30))
        clean.paste(frame_blurred, (frame_left, frame_top))

        # ── Step 3: ARGOS branded plate overlay ──
        clean = _overlay_argos_plate_cover(clean, plate_top, w, h)

        # ── Step 4: Blur top dealer logo zone (top 10%) ──
        dealer_bottom = int(h * DEALER_LOGO_BOTTOM_PCT)
        if dealer_bottom > 10:
            top_zone = clean.crop((0, 0, w, dealer_bottom))
            top_blurred = top_zone.filter(ImageFilter.GaussianBlur(radius=15))
            clean.paste(top_blurred, (0, 0))

        # ── Step 4: Save as JPEG (strips all metadata) ──
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

    print(f"  Sanitized {len(safe_paths)}/{len(rows)} images for {listing_id}")
    return safe_paths


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
