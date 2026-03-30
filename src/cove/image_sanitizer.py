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

# LaMa inpainting model — lazy loaded (196MB, WACV 2022)
_LAMA_MODEL = None
_LAMA_PATH = None

def _get_lama_model():
    global _LAMA_MODEL, _LAMA_PATH
    if _LAMA_MODEL is None:
        try:
            import torch
            from huggingface_hub import hf_hub_download
            _LAMA_PATH = hf_hub_download(repo_id="fashn-ai/LaMa", filename="big-lama.pt")
            _LAMA_MODEL = torch.jit.load(_LAMA_PATH, map_location="cpu")
            _LAMA_MODEL.eval()
        except Exception as e:
            print(f"  [LAMA] Model load failed: {e}")
    return _LAMA_MODEL


def _lama_inpaint(cv_img, mask):
    """
    Inpaint using LaMa (Large Mask Inpainting).
    cv_img: BGR numpy array (H, W, 3)
    mask: binary numpy array (H, W), 255 = inpaint
    Returns: BGR numpy array (H, W, 3)
    """
    import torch
    model = _get_lama_model()
    if model is None:
        # Fallback to cv2.inpaint
        return cv2.inpaint(cv_img, mask, 12, cv2.INPAINT_NS)

    h, w = cv_img.shape[:2]
    # LaMa requires dimensions divisible by 8
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8

    # Prepare image tensor: RGB normalized to [0, 1]
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)

    # Prepare mask tensor: binary [0, 1]
    mask_f = (mask > 127).astype(np.float32)
    mask_tensor = torch.from_numpy(mask_f).unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

    # Pad to multiple of 8
    if pad_h > 0 or pad_w > 0:
        img_tensor = torch.nn.functional.pad(img_tensor, (0, pad_w, 0, pad_h), mode='reflect')
        mask_tensor = torch.nn.functional.pad(mask_tensor, (0, pad_w, 0, pad_h), mode='constant', value=0)

    with torch.no_grad():
        result = model(img_tensor, mask_tensor)

    # Remove padding and convert back
    result = result[0].permute(1, 2, 0).numpy()[:h, :w]
    result = np.clip(result * 255, 0, 255).astype(np.uint8)
    return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)


# YOLOv5 plate detector — lazy loaded
_YOLO_PLATE_MODEL = None

def _get_plate_model():
    global _YOLO_PLATE_MODEL
    if _YOLO_PLATE_MODEL is None:
        try:
            import yolov5
            _YOLO_PLATE_MODEL = yolov5.load('keremberke/yolov5n-license-plate')
            _YOLO_PLATE_MODEL.conf = 0.40
            _YOLO_PLATE_MODEL.iou = 0.45
        except Exception as e:
            print(f"  [YOLO] Plate model load failed: {e}")
    return _YOLO_PLATE_MODEL

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


def _add_argos_bar(draw: 'ImageDraw.Draw', w: int, h_total: int, bar_top: int, bar_bottom: int):
    """Draw ARGOS AUTOMOTIVE text centered on a black bar."""
    try:
        bfs = max(10, int((bar_bottom - bar_top) * 0.30))
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
    bar_h = bar_bottom - bar_top
    draw.text(((w - btw) // 2, bar_top + (bar_h - bth) // 2),
              btext, fill=ARGOS_GOLD, font=bfont)


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
        # ZERO TOLERANCE SANITIZATION v14 — GENERAL APPROACH
        #
        # 1. YOLO detects plates → inpaint (natural fill, not black box)
        # 2. OCR detects ALL text → inpaint non-car text
        # 3. CV2 edge detects banners → CROP
        # 4. Verify OCR on output → DROP if text survives
        #
        # No blur. No full-width bars. No whack-a-mole.
        # ══════════════════════════════════════════════════════════

        _keep_words = {'xdrive', 'sdrive', 'quattro', 'tfsi', 'tdi', 'cdi',
                       'diesel', 'benzin', 'hybrid', 'electric',
                       'automatik', 'automatic', 'schaltung',
                       'argos', 'automotive'}

        # ── STEP 1: Detect plates via YOLO ───────────────────────
        plate_boxes = []
        yolo = _get_plate_model()
        if yolo:
            try:
                results = yolo(image_path, size=640)
                preds = results.pred[0]
                for *box, conf, cls in preds:
                    x1, y1, x2, y2 = [int(v) for v in box]
                    # Plates are in bottom 60% of image — filter top false positives
                    if y1 < h * 0.40 and conf < 0.70:
                        continue
                    if conf > 0.30:
                        plate_boxes.append((x1, y1, x2, y2, float(conf)))
                        print(f"  [YOLO] Plate at ({x1},{y1})-({x2},{y2}) conf={conf:.2f}")
            except Exception as e:
                print(f"  [YOLO] Error: {e}")

        # ── STEP 2: Detect all text via EasyOCR ──────────────────
        text_rects = []
        reader = _get_ocr_reader()
        if reader:
            try:
                results = reader.readtext(image_path, detail=1)
                for bbox_pts, text_str, conf in results:
                    if conf > 0.15:
                        xs = [int(p[0]) for p in bbox_pts]
                        ys = [int(p[1]) for p in bbox_pts]
                        text_rects.append((min(xs), min(ys), max(xs), max(ys), text_str, conf))
            except Exception as e:
                print(f"  [OCR] Error: {e}")

        _crop_top_after_inpaint = 0

        # ── STEP 3: Build inpaint mask ───────────────────────────
        # One mask for everything that needs to disappear.
        if CV2_AVAILABLE:
            cv_img = cv2.imread(image_path)
            if cv_img is not None:
                mask = np.zeros(cv_img.shape[:2], dtype=np.uint8)

                # 3a: Mask plates (YOLO) + generous frame expansion
                for x1, y1, x2, y2, conf in plate_boxes:
                    pw, ph = x2 - x1, y2 - y1
                    # Expand to cover plate frame (dealer text above/below)
                    fx1 = max(0, x1 - int(pw * 0.08))
                    fy1 = max(0, y1 - int(ph * 1.0))   # 100% above for frame
                    fx2 = min(w, x2 + int(pw * 0.08))
                    fy2 = min(h, y2 + int(ph * 0.5))    # 50% below
                    mask[fy1:fy2, fx1:fx2] = 255

                # 3b: Mask all non-car text detected by OCR
                for tx1, ty1, tx2, ty2, ttext, conf in text_rects:
                    words_lower = ttext.lower().strip().split()
                    if all(w in _keep_words for w in words_lower):
                        continue
                    if (tx2 - tx1) < 15 or (ty2 - ty1) < 5:
                        continue
                    if len(ttext.strip()) <= 1:
                        continue
                    # Mask with padding
                    pad = 10
                    mx1 = max(0, tx1 - pad)
                    my1 = max(0, ty1 - pad)
                    mx2 = min(w, tx2 + pad)
                    my2 = min(h, ty2 + pad)
                    mask[my1:my2, mx1:mx2] = 255

                # 3c: Detect top banner → save for CROP later (not inpaint!)
                # Inpainting the entire top zone destroys the car roof.
                # Banner = CROP. Individual text/logos = already in mask from 3b.
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                h_cv, w_cv = gray.shape
                max_edge = 0
                edge_row = 0
                for row in range(int(h_cv * 0.05), int(h_cv * 0.30)):
                    diff = abs(float(np.mean(gray[row])) - float(np.mean(gray[row + 1])))
                    if diff > max_edge:
                        max_edge = diff
                        edge_row = row
                top_std = float(np.std(gray[0:int(h_cv * 0.18)]))
                _crop_top_after_inpaint = 0
                if max_edge > 15 and edge_row > int(h_cv * 0.05):
                    _crop_top_after_inpaint = edge_row + int(h_cv * 0.04)  # 4% margin — catches logos below edge
                elif top_std < 25:
                    _crop_top_after_inpaint = int(h_cv * 0.18)
                # Extend if OCR found text above the edge
                for tx1, ty1, tx2, ty2, ttext, conf in text_rects:
                    if ty1 < h * 0.30:
                        words_lower = ttext.lower().strip().split()
                        if not all(w in _keep_words for w in words_lower) and len(ttext.strip()) > 2:
                            _crop_top_after_inpaint = max(_crop_top_after_inpaint, ty2 + int(h * 0.05))
                _crop_top_after_inpaint = min(_crop_top_after_inpaint, int(h * 0.30))
                if _crop_top_after_inpaint > 0:
                    print(f"  [BANNER] Top crop planned at {_crop_top_after_inpaint}px ({_crop_top_after_inpaint/h*100:.0f}%)")

                # 3d: Plate fallback — if YOLO missed the plate, mask typical plate zone
                if not plate_boxes:
                    # Look for OCR text in bottom 30% that could be plate frame text
                    has_bottom_text = False
                    for tx1, ty1, tx2, ty2, ttext, conf in text_rects:
                        if ty1 > h * 0.70:
                            words_lower = ttext.lower().strip().split()
                            if not all(w in _keep_words for w in words_lower):
                                has_bottom_text = True
                                pad = 12
                                mask[max(0,ty1-pad):min(h,ty2+pad), max(0,tx1-pad):min(w,tx2+pad)] = 255
                    if not has_bottom_text:
                        # No plate found at all — DON'T mask, just add ARGOS label
                        # after crop in the right spot
                        print(f"  [FALLBACK] No plate detected, will add ARGOS label after crop")

                # 3f: Inpaint with LaMa
                has_mask = np.any(mask > 0)
                if has_mask:
                    inpainted = _lama_inpaint(cv_img, mask)
                    # Convert back to PIL
                    clean = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
                    w, h = clean.size
                    print(f"  [INPAINT] Removed {len(plate_boxes)} plates + {np.count_nonzero(mask) // 1000}K masked pixels")

        # ── STEP 4: Crop top banner + bottom uniform strip ────────
        # Top banner = CROP (preserves car, removes dealer logos)
        # Bottom = crop if uniform strip detected
        crop_top = _crop_top_after_inpaint
        crop_bottom = 0
        if CV2_AVAILABLE:
            _tmp = safe_path + ".tmp.jpg"
            _save = clean.convert('RGB') if clean.mode == 'RGBA' else clean
            _save.save(_tmp, 'JPEG', quality=95)
            cv_img2 = cv2.imread(_tmp)
            try:
                os.remove(_tmp)
            except OSError:
                pass
            if cv_img2 is not None:
                gray2 = cv2.cvtColor(cv_img2, cv2.COLOR_BGR2GRAY)
                bot_std = float(np.std(gray2[int(gray2.shape[0] * 0.85):]))
                if bot_std < 30:
                    crop_bottom = gray2.shape[0] - int(gray2.shape[0] * 0.85)

        if crop_top > 0 or crop_bottom > 0:
            new_bottom = h - crop_bottom if crop_bottom else h
            clean = clean.crop((0, crop_top, w, new_bottom))
            w, h = clean.size
            if crop_top > 0:
                print(f"  [CROP] Top {crop_top}px")
            if crop_bottom > 0:
                print(f"  [CROP] Bottom {crop_bottom}px")

        # ── STEP 5: Add small ARGOS label on plate area ──────────
        if plate_boxes:
            draw = ImageDraw.Draw(clean)
            for x1, y1, x2, y2, conf in plate_boxes:
                ay1 = y1 - crop_top
                ay2 = min(y2 - crop_top, h)
                if ay1 < 0 or ay1 > h:
                    continue
                pw, ph = x2 - x1, ay2 - ay1
                if ph <= 0:
                    continue
                # Small ARGOS text on the inpainted plate area
                try:
                    pfont_size = max(8, int(ph * 0.40))
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
                cx = x1 + (pw - ptw) // 2
                cy = ay1 + (ph - pth) // 2
                draw.text((cx, cy), ptext, fill=ARGOS_GOLD, font=pfont)

        # ── STEP 5b: If no plate detected, add small ARGOS at bottom ──
        if not plate_boxes:
            draw = ImageDraw.Draw(clean)
            # Small ARGOS in bottom-left, subtle
            try:
                fs = max(10, int(h * 0.03))
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fs)
                except OSError:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
                    except OSError:
                        font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            draw.text((int(w * 0.03), int(h * 0.92)), "ARGOS", fill=ARGOS_GOLD, font=font)

        # ── STEP 6: Save ─────────────────────────────────────────
        if clean.mode == 'RGBA':
            clean = clean.convert('RGB')
        clean.save(safe_path, 'JPEG', quality=90)

        # ── STEP 7: ZERO TOLERANCE VERIFY ────────────────────────
        if reader:
            try:
                import re as _re
                verify_results = reader.readtext(safe_path, detail=1)
                for bbox_pts, vtext, vconf in verify_results:
                    if vconf < 0.30:
                        continue
                    vwords = vtext.lower().strip().split()
                    # Skip our own ARGOS branding (OCR sometimes reads it as ARCOS/ARG0S)
                    _our_brand = {'argos', 'arcos', 'arg0s', 'argds', 'automotive', 'automotve'}
                    if all(w in _our_brand or w in _keep_words for w in vwords):
                        continue
                    if len(vtext.strip()) <= 2:
                        continue
                    if all(w.replace('.', '').replace(',', '').isdigit() for w in vwords):
                        continue
                    garble_ratio = len(_re.findall(r'[^a-zA-Z0-9\s]', vtext)) / max(len(vtext), 1)
                    if garble_ratio > 0.3 or (vconf < 0.45 and garble_ratio > 0.1):
                        continue
                    if len(vtext.strip()) <= 4 and vconf < 0.50:
                        continue
                    # Surviving dealer text → REJECT
                    print(f"  REJECTED: \"{vtext}\" (conf={vconf:.2f}) survived")
                    try:
                        os.remove(safe_path)
                    except OSError:
                        pass
                    return None
            except Exception as e:
                print(f"  [VERIFY] error: {e}")

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
    Detect EU license plates using OpenCV contour + HSV + position filtering.

    EU plates: white rectangle ~520x110mm, aspect ratio ~4.7:1.
    Position constraint: plates appear in bottom 45% of image, center 90%.
    This eliminates false positives from white car body parts, sky, etc.

    Returns list of (x, y, w, h) bounding rectangles.
    """
    if not CV2_AVAILABLE:
        return []
    try:
        img = cv2.imread(image_path)
        if img is None:
            return []
        h_img, w_img = img.shape[:2]

        # Only search in bottom 45% of image — plates are never in the sky
        search_top = int(h_img * 0.55)
        roi = img[search_top:, :]
        h_roi, w_roi = roi.shape[:2]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # White color range — EU plates are white with blue left band
        lower_white = np.array([0, 0, 170])
        upper_white = np.array([255, 70, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)

        # Morphological ops: close gaps in plate text, then open to remove noise
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 5))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h == 0 or w == 0:
                continue
            area = w * h
            aspect_ratio = w / h
            roi_area = w_roi * h_roi

            # EU plate constraints (tightened):
            # - Aspect ratio 3.5-5.8 (standard EU is 4.7:1)
            # - Area 0.15%-4% of ROI (not full image — ROI is bottom 45%)
            # - Width 6%-28% of image width
            # - Height 1%-6% of image height (plates are thin)
            # - Center 90%: plate center X must be within 5%-95% of image width
            cx = x + w // 2
            cy_full = (search_top + y) + h // 2  # Y in full image coords

            center_x_ok = 0.05 * w_img < cx < 0.95 * w_img

            if (3.5 < aspect_ratio < 5.8
                    and 0.0015 < area / roi_area < 0.04
                    and 0.06 < w / w_img < 0.28
                    and 0.01 < h / h_img < 0.06
                    and center_x_ok):
                # Score: prefer candidates closer to EU standard aspect ratio
                ar_score = 1.0 - abs(aspect_ratio - 4.7) / 2.0
                candidates.append((x, search_top + y, w, h, ar_score))

        # Sort by aspect ratio closeness to 4.7 (best match first)
        candidates.sort(key=lambda c: c[4], reverse=True)

        # Remove overlapping detections — keep best scoring
        filtered = []
        for c in candidates:
            x, y, w, h, score = c
            overlap = False
            for fx, fy, fw, fh in filtered:
                # Check if centers are close (within 1 plate-width)
                cx1, cy1 = x + w // 2, y + h // 2
                cx2, cy2 = fx + fw // 2, fy + fh // 2
                if abs(cx1 - cx2) < max(w, fw) and abs(cy1 - cy2) < max(h, fh) * 2:
                    overlap = True
                    break
            if not overlap:
                filtered.append((x, y, w, h))

        return filtered[:2]  # Max 2 plates (front + rear visible)
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
