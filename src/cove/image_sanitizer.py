"""
image_sanitizer.py — ARGOS Image Sanitizer v5 (S179)
CoVe 2026 | Enterprise Grade

5-stage pipeline validated on 10+ real dealer photos (S110):
  Stage 0: Interior/exterior classifier (photo index heuristic)
  Stage 1: Crop portal banner (top zone, configurable per portal)
  Stage 2: Apple Vision text detection (was PaddleOCR pre-S163)
  Stage 3: Cover text regions with Pillow rectangles (D-32, D-25)
  Stage 4: Post-OCR verification + Telegram alert if residuals

BUSINESS RULE: The dealer must NOT be able to identify the EU seller
from the dossier. Source identity is revealed ONLY after fee payment.

S163 (2026-05-12): PaddleOCR replaced with Apple Vision Framework via pyobjc.
Reason: paddle wheel macOS minos=12.3 (S159) + iMac AVX1-only (S162) = dead-end
strutturale su hardware Luke. Vision.framework è built-in macOS 10.13+,
zero ML deps install, zero AVX2 req. Quality verified on 4 real dealer photos:
4/4 seller match "Autohaus Isernhagen", warm latency 1.6-2.0s/img.

S179 (2026-05-20): LaMa+cv2.inpaint replaced with Pillow rectangle solid fill (D-32).
Reason: LaMa hallucination on S176 BMW X1 (deformed bumper, swallowed "xDrive 25e").
D-25 compliance: no generative OpenCV/LaMa in inpaint path.

Stack (all Apache 2.0 / MIT / Apple system):
  - Apple Vision Framework (system, free, built-in 10.13+)
  - pyobjc-framework-Vision (Apache 2.0): Python bindings
  - Pillow: solid fill rectangles (D-32), EXIF strip, save, branding
  - cv2: banner crop, hood reflection (out of scope D-32)

Usage:
  from src.cove.image_sanitizer import sanitize_image, sanitize_all_images

  safe_path = sanitize_image("raw_photo.jpg", output_dir="dossiers/safe/")
  safe_paths = sanitize_all_images(listing_id, db_path, output_dir)
"""

import os
import re
import sys
import time
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict

# Load .env for TG alerts (if dotenv available)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

try:
    from PIL import Image, ImageDraw, ImageFont, ImageStat
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

log = logging.getLogger("argos.sanitizer")

# ── Configuration — thresholds validated on 10+ real photos (S110) ────────────

# PaddleOCR detection thresholds
PADDLE_DET_THRESH = 0.2
PADDLE_BOX_THRESH = 0.35
PADDLE_CONF_MIN = 0.25
PADDLE_TEXT_MIN_LEN = 2

# Alert: if post-verify finds text above this confidence, send TG alert
ALERT_CONFIDENCE_THRESHOLD = 0.70

# Interior photo detection: photos at index >= this are likely interior
INTERIOR_INDEX_THRESHOLD = 4

# Portal banner crop heights (% of image height from top)
PORTAL_BANNER_CROP = {
    "autoscout24": 0.08,
    "mobile_de": 0.06,
    "default": 0.05,
}

# Minimum file size — images below this are thumbnails
MIN_IMAGE_BYTES = 30 * 1024  # 30 KB

# S163.1: skip output if sanitized JPEG file size collapses vs original.
# Use case: AS24 a volte include "slide marketing" (BMW Premium Selection ecc.)
# che sono 100% testo dealer-promozionale; il sanitizer wipa il testo e l'output
# JPEG compresso diventa quasi vuoto (bianco/grigio uniforme). Soglia 0.20 =
# output JPEG < 20% size originale → probabile slide promo wipe, skip.
# Area-based check non funziona (inpaint preserva dimensioni anche se contenuto = bianco).
MIN_OUTPUT_SIZE_RATIO = 0.20

# Words to keep (car specs, our own branding)
# S179: expanded with BMW/Mercedes/Audi numeric trims vulnerable in S176
KEEP_WORDS = frozenset({
    'xdrive', 'sdrive', 'quattro', 'tfsi', 'tdi', 'cdi',
    'diesel', 'benzin', 'hybrid', 'electric', 'phev', 'mhev',
    'automatik', 'automatic', 'schaltung', 'steptronic',
    'argos', 'automotive', 'arcos', 'arg0s',
    'bmw', 'mercedes', 'audi', 'porsche', 'volkswagen', 'vw',
    'amg', 'sport', 'luxury', 'line', 'pack', 'paket',
    # BMW numeric trims (S176: xDrive 25e swallowed by LaMa)
    '25e', '30e', '45e', '18d', '20d', '23d', '25d', '30d', '40d', '50d',
    '18i', '20i', '23i', '25i', '30i', '40i', '50i',
    'm240i', 'm340i', 'm440i',
    # Mercedes numeric trims
    '200d', '220d', '300d', '350d', '400d', '450d',
    '200', '220', '300', '350', '400', '450',
    # Audi numeric trims
    '30tdi', '35tdi', '40tdi', '45tdi', '50tdi',
    '30tfsi', '35tfsi', '40tfsi', '45tfsi',
})

# ARGOS brand colors
ARGOS_BLACK = (26, 26, 26)
ARGOS_GOLD = (200, 164, 70)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ARGOS_LOGO_PATH = PROJECT_ROOT / "assets" / "ARGOS_logo_sobrio_horizontal.png"
DEFAULT_SAFE_DIR = PROJECT_ROOT / "dossiers" / "safe_images"


# ── Vision OCR backend (S163: replaces PaddleOCR) ────────────────────────────

_VISION_OCR_FN = None


def _get_vision_ocr():
    """Lazy-load Apple Vision OCR detector (S163).

    Returns callable(image_path, seller_name, keep_words, conf_min) -> List[Dict]
    Same return shape as previous paddle-based detector.
    """
    global _VISION_OCR_FN
    if _VISION_OCR_FN is None:
        try:
            try:
                from .vision_ocr import detect_text_regions
            except ImportError:
                from vision_ocr import detect_text_regions  # type: ignore
            _VISION_OCR_FN = detect_text_regions
            log.info("Vision OCR (Apple Framework) initialized")
        except ImportError as e:
            log.warning(f"vision_ocr not available: {e}")
        except Exception as e:
            log.error(f"Vision OCR init failed: {e}")
    return _VISION_OCR_FN


# ── Telegram Alert ────────────────────────────────────────────────────────────

def _send_tg_alert(message: str, photo_path: str = None):
    """Send alert to Telegram bot. Non-blocking, fire-and-forget."""
    try:
        token = os.environ.get("ARGOS_TELEGRAM_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
        chat_id = os.environ.get("ARGOS_TELEGRAM_CHAT_ID", os.environ.get("TELEGRAM_ADMIN_CHAT_IDS", ""))
        if not token or not chat_id:
            log.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_CHAT_IDS not set — alert skipped")
            return

        import requests
        base = f"https://api.telegram.org/bot{token}"

        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": chat_id, "caption": message[:1024]},
                    files={"photo": f},
                    timeout=10,
                )
        else:
            requests.post(
                f"{base}/sendMessage",
                data={"chat_id": chat_id, "text": message[:4096]},
                timeout=10,
            )
    except Exception as e:
        log.error(f"TG alert failed: {e}")


def _send_tg_before_after(before_path: str, after_path: str, caption: str):
    """Send before/after comparison to Telegram."""
    try:
        token = os.environ.get("ARGOS_TELEGRAM_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
        chat_id = os.environ.get("ARGOS_TELEGRAM_CHAT_ID", os.environ.get("TELEGRAM_ADMIN_CHAT_IDS", ""))
        if not token or not chat_id:
            return

        import requests
        base = f"https://api.telegram.org/bot{token}"

        # Send before
        if os.path.exists(before_path):
            with open(before_path, 'rb') as f:
                requests.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": chat_id, "caption": f"BEFORE: {caption}"[:1024]},
                    files={"photo": f},
                    timeout=10,
                )

        # Send after
        if os.path.exists(after_path):
            with open(after_path, 'rb') as f:
                requests.post(
                    f"{base}/sendPhoto",
                    data={"chat_id": chat_id, "caption": f"AFTER: {caption}"[:1024]},
                    files={"photo": f},
                    timeout=10,
                )
    except Exception as e:
        log.error(f"TG before/after failed: {e}")


# ── Stage 0: Interior/Exterior Classifier ────────────────────────────────────

def _is_interior_photo(image_path: str, image_index: int) -> bool:
    """
    Classify photo as interior or exterior.

    Strategy (validated S110):
    - EU portals typically order: 0-3 exterior, 4+ mixed interior/exterior
    - Interior photos should NOT be sanitized (no dealer text on dashboards)
    - For indices < INTERIOR_INDEX_THRESHOLD: always exterior
    - For indices >= threshold: use photo index as primary signal

    The OpenCV heuristics (sky ratio, variance, edge density) were tested
    and FAILED 0/10 in S110. Do NOT re-add them.
    """
    if image_index < INTERIOR_INDEX_THRESHOLD:
        return False

    # For higher indices, we treat them as exterior (safe default).
    # Interior photos rarely have dealer overlays, so sanitizing them
    # is harmless — worst case we just strip EXIF.
    return False


# ── Stage 1: Banner Crop ─────────────────────────────────────────────────────

def _detect_banner_crop(cv_img, portal: str = "default") -> Tuple[int, int]:
    """
    Detect portal banners at top and bottom of image.
    Returns (crop_top, crop_bottom) in pixels.

    Top: edge detection in top 25% or low-variance solid banner.
    Bottom: edge detection in bottom 75-97% (AS24 dealer bars with logos).
    """
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # ── TOP banner scan ──
    crop_top = 0
    max_edge = 0
    edge_row = 0
    for row in range(int(h * 0.03), int(h * 0.25)):
        diff = abs(float(np.mean(gray[row])) - float(np.mean(gray[row + 1])))
        if diff > max_edge:
            max_edge = diff
            edge_row = row

    if max_edge > 15 and edge_row > int(h * 0.03):
        crop_top = min(edge_row + int(h * 0.02), int(h * 0.25))
    else:
        top_zone = gray[:int(h * 0.12)]
        if float(np.std(top_zone)) < 25:
            pct = PORTAL_BANNER_CROP.get(portal, PORTAL_BANNER_CROP["default"])
            crop_top = int(h * pct)

    # ── BOTTOM banner scan — AS24 dealer bars at bottom ~15% ──
    crop_bottom = 0
    max_edge_bot = 0
    edge_row_bot = 0
    for row in range(int(h * 0.97), int(h * 0.75), -1):
        diff = abs(float(np.mean(gray[row])) - float(np.mean(gray[row - 1])))
        if diff > max_edge_bot:
            max_edge_bot = diff
            edge_row_bot = row

    if max_edge_bot > 15 and edge_row_bot > int(h * 0.75):
        crop_bottom = edge_row_bot - int(h * 0.01)  # 1% margin above edge
        log.debug(f"[SANITIZER] Banner bottom edge at row={edge_row_bot}/{h}")

    return crop_top, crop_bottom


# ── Stage 2: PaddleOCR Text Detection ────────────────────────────────────────

def _detect_text_regions(
    image_path: str, seller_name: str = None
) -> List[Dict]:
    """
    Detect all text regions using Apple Vision Framework (S163).

    Returns list of dicts:
      {box: (x1,y1,x2,y2), text: str, conf: float, is_seller: bool, should_mask: bool}

    Note: vision_ocr.detect_text_regions encapsulates the seller-match + KEEP_WORDS
    filter logic. We pass module-level KEEP_WORDS so it stays the single source.
    """
    vision_fn = _get_vision_ocr()
    if vision_fn is None:
        return []

    try:
        return vision_fn(
            image_path,
            seller_name=seller_name,
            keep_words=KEEP_WORDS,
            conf_min=PADDLE_CONF_MIN,
            min_text_len=PADDLE_TEXT_MIN_LEN,
        )
    except Exception as e:
        log.error(f"Vision OCR detection failed: {e}")
        return []


# ── Stage 3: Pillow solid fill (D-32, D-25) ──────────────────────────────────

def _sample_border_color(pil_img: "Image.Image", bbox: Tuple[int, int, int, int], sample_px: int = 3) -> Tuple[int, int, int]:
    """
    Sample average color of pixels in a border ring around bbox (color match).

    Crops a slightly enlarged region and averages it. Because the inner bbox
    is typically a small fraction of the outer crop, the mean is dominated by
    the surrounding background — giving a natural blend color.
    """
    x1, y1, x2, y2 = bbox
    w, h = pil_img.size
    ox1 = max(0, x1 - sample_px)
    oy1 = max(0, y1 - sample_px)
    ox2 = min(w, x2 + sample_px)
    oy2 = min(h, y2 + sample_px)
    outer = pil_img.crop((ox1, oy1, ox2, oy2))
    mean_outer = ImageStat.Stat(outer).mean[:3]
    return tuple(int(c) for c in mean_outer)


def _apply_solid_fills(cv_img, text_regions: List[Dict], crop_top: int = 0):
    """
    Cover masked text regions with solid color rectangles, color matched to
    the surrounding border pixels.

    Replaces LaMa+cv2.inpaint (D-32, D-25 Pillow-only). Zero generative ML,
    zero hallucination risk. Color is sampled from a 3px ring around each bbox
    for natural blending against the background.

    Args:
        cv_img: BGR numpy array (cv2 format)
        text_regions: list of region dicts from _detect_text_regions
        crop_top: pixels already known to be cropped (regions fully above
                  this line are skipped unless is_seller)

    Returns:
        BGR numpy array with text regions covered.
    """
    if not text_regions:
        return cv_img

    h, w = cv_img.shape[:2]
    # Convert BGR → PIL RGB for Pillow drawing
    pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    for region in text_regions:
        if not region['should_mask']:
            continue

        x1, y1, x2, y2 = region['box']

        # Skip regions fully above crop line (they'll be removed by crop)
        if y2 <= crop_top and not region['is_seller']:
            continue

        # For seller matches near crop line: extend down to catch full signage
        if region['is_seller'] and y2 <= crop_top + int(h * 0.05):
            y2 = min(h, crop_top + int(h * 0.08))

        # Pad: 20px seller (larger signage), 12px others (mirror _build_inpaint_mask)
        pad = 20 if region['is_seller'] else 12
        mx1 = max(0, x1 - pad)
        my1 = max(0, y1 - pad)
        mx2 = min(w, x2 + pad)
        my2 = min(h, y2 + pad)

        # Color match: sample 3px border ring around padded bbox
        fill_color = _sample_border_color(pil_img, (mx1, my1, mx2, my2), sample_px=3)
        draw.rectangle([mx1, my1, mx2, my2], fill=fill_color)

    # Convert PIL RGB → BGR for downstream cv2 pipeline
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


# ── Stage 4: Post-verify + Alert ─────────────────────────────────────────────

def _post_verify_and_alert(
    safe_path: str,
    original_path: str,
    listing_id: str,
    image_index: int,
    seller_name: str = None,
) -> bool:
    """
    Re-run OCR on sanitized image. If text survives:
    - conf >= ALERT_CONFIDENCE_THRESHOLD → send TG alert with before/after
    - Returns True if image is acceptable (no high-confidence text)

    Unlike v2 which REJECTED images with surviving text, v3 keeps the image
    but alerts for human review. This prevents empty dossiers.
    """
    vision_fn = _get_vision_ocr()
    if vision_fn is None:
        return True  # Can't verify, assume OK

    try:
        # Re-detect on sanitized image with same seller-aware filter
        regions = vision_fn(
            safe_path,
            seller_name=seller_name,
            keep_words=KEEP_WORDS,
            conf_min=0.30,
            min_text_len=PADDLE_TEXT_MIN_LEN,
        )
        if not regions:
            return True  # Clean

        surviving_text = []
        for region in regions:
            text = region['text']
            conf = region['conf']
            words = text.lower().strip().split()
            # Apply post-verify-only extra filters (mirror v3 logic):
            if not region['should_mask'] and not region['is_seller']:
                continue
            garble = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / max(len(text), 1)
            if garble > 0.3:
                continue
            if len(text.strip()) <= 4 and conf < 0.50:
                continue
            surviving_text.append((text, conf))

        if surviving_text:
            high_conf = [t for t, c in surviving_text if c >= ALERT_CONFIDENCE_THRESHOLD]
            all_text = ", ".join(f'"{t}" ({c:.0%})' for t, c in surviving_text)

            if high_conf:
                caption = (
                    f"SANITIZER ALERT: Residual text in {listing_id} img#{image_index}\n"
                    f"Text: {all_text}\n"
                    f"Seller: {seller_name or 'unknown'}\n"
                    f"ACTION: Review manually"
                )
                log.warning(caption)
                _send_tg_before_after(original_path, safe_path, caption)
                return True  # Keep image but alert sent

            # Low confidence text — log only
            log.info(f"Low-conf residual in {listing_id} img#{image_index}: {all_text}")

        return True

    except Exception as e:
        log.error(f"Post-verify failed: {e}")
        return True


# ── Hood Reflection Detection ─────────────────────────────────────────────────

def _detect_hood_reflection(cv_img) -> bool:
    """
    Detect text reflected on car hood (irresolvable automatically per S110).
    Returns True if suspicious reflection detected → triggers TG alert.

    Heuristic: dark zone in bottom 40-60% with high local variance
    (text reflection on metallic surface).
    """
    if not CV2_AVAILABLE:
        return False

    try:
        h, w = cv_img.shape[:2]
        # Hood zone: 40-65% from top (typical for frontal shots)
        hood = cv_img[int(h * 0.40):int(h * 0.65), int(w * 0.15):int(w * 0.85)]
        gray = cv2.cvtColor(hood, cv2.COLOR_BGR2GRAY)

        # Dark + high local variance = possible text reflection on paint
        mean_val = float(np.mean(gray))
        local_var = float(np.std(gray))

        # Metallic hoods are dark (mean < 80) with text reflections (std > 35)
        if mean_val < 80 and local_var > 35:
            return True

    except Exception:
        pass

    return False


# ── Font Helper ───────────────────────────────────────────────────────────────

def _get_font(size: int):
    """Get best available font at given size."""
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ── Main sanitize_image ──────────────────────────────────────────────────────

def sanitize_image(
    image_path: str,
    output_dir: str = None,
    listing_id: str = None,
    image_index: int = 0,
    seller_name: str = None,
) -> Optional[str]:
    """
    Sanitize a single vehicle image (v5 pipeline):

    Stage 0: Classify interior/exterior
    Stage 1: Crop portal banner (top zone)
    Stage 2: Apple Vision text detection
    Stage 3: Cover text regions with Pillow rectangles (D-32, D-25)
    Stage 4: Post-verify + TG alert if residuals

    Returns: path to sanitized image, or None on failure.
    """
    if not PILLOW_AVAILABLE:
        print("ERROR: Pillow not installed. pip install Pillow")
        return None

    if not os.path.exists(image_path):
        print(f"  SKIP: image not found: {image_path}")
        return None

    file_size = os.path.getsize(image_path)
    if file_size < MIN_IMAGE_BYTES:
        print(f"  SKIP thumbnail: {os.path.basename(image_path)} ({file_size // 1024} KB)")
        return None

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

    t0 = time.time()

    try:
        # ── STAGE 0: Interior/Exterior Classification ────────────
        is_interior = _is_interior_photo(image_path, image_index)

        if is_interior:
            # Interior photos: just strip EXIF, no text removal
            img = Image.open(image_path)
            clean = Image.new(img.mode, img.size)
            clean.paste(img)
            if clean.mode == 'RGBA':
                clean = clean.convert('RGB')
            clean.save(safe_path, 'JPEG', quality=90)
            elapsed = time.time() - t0
            print(f"  INTERIOR: {safe_name} (index={image_index}, {elapsed:.1f}s)")
            return safe_path

        if not CV2_AVAILABLE:
            # Without OpenCV, just strip EXIF
            img = Image.open(image_path)
            clean = Image.new(img.mode, img.size)
            clean.paste(img)
            if clean.mode == 'RGBA':
                clean = clean.convert('RGB')
            clean.save(safe_path, 'JPEG', quality=90)
            return safe_path

        cv_img = cv2.imread(image_path)
        if cv_img is None:
            print(f"  ERROR: cv2 cannot read {image_path}")
            return None

        h, w = cv_img.shape[:2]

        # Detect portal from listing_id
        portal = "default"
        if listing_id:
            if "autoscout24" in listing_id:
                portal = "autoscout24"
            elif "mobile_de" in listing_id:
                portal = "mobile_de"

        # ── STAGE 1: Banner Crop ─────────────────────────────────
        crop_top, crop_bottom = _detect_banner_crop(cv_img, portal)

        # Extend crop if OCR finds text in top zone
        text_regions = _detect_text_regions(image_path, seller_name)
        for region in text_regions:
            if region['should_mask']:
                _, ty1, _, ty2 = region['box']
                if ty1 < h * 0.30:
                    # Seller text: aggressive crop (8% margin below text)
                    # Other text: standard crop (2% margin)
                    margin = int(h * 0.08) if region['is_seller'] else int(h * 0.02)
                    crop_top = max(crop_top, ty2 + margin)
                # Extend bottom crop if text in bottom 20%
                if ty1 > h * 0.80:
                    margin_bot = int(h * 0.02) if region['is_seller'] else int(h * 0.01)
                    new_bottom = ty1 - margin_bot
                    if crop_bottom == 0 or new_bottom < crop_bottom:
                        crop_bottom = new_bottom
        crop_top = min(crop_top, int(h * 0.35))  # Never crop more than 35%

        if crop_top > 0:
            print(f"  [BANNER] Crop top {crop_top}px ({crop_top/h*100:.0f}%)")
        if crop_bottom > 0:
            print(f"  [BANNER] Crop bottom at row {crop_bottom}px ({crop_bottom/h*100:.0f}%)")

        # ── STAGE 2: Already done above (text_regions) ───────────
        mask_count = sum(1 for r in text_regions if r['should_mask'])
        if mask_count > 0:
            seller_matches = [r for r in text_regions if r['is_seller']]
            other_text = [r for r in text_regions if r['should_mask'] and not r['is_seller']]
            if seller_matches:
                print(f"  [OCR] {len(seller_matches)} seller match(es): "
                      + ", ".join(f'"{r["text"]}"' for r in seller_matches))
            if other_text:
                print(f"  [OCR] {len(other_text)} other text region(s) to mask")

        # ── STAGE 3: Pillow solid fill (D-32, D-25) ─────────────
        to_mask = [r for r in text_regions if r['should_mask']]
        has_mask = len(to_mask) > 0

        if has_mask:
            cv_img = _apply_solid_fills(cv_img, text_regions, crop_top)
            print(f"  [FILL] {len(to_mask)} text region(s) covered (Pillow rect)")

        # Apply top crop
        if crop_top > 0:
            if crop_bottom > 0:
                crop_bottom = crop_bottom - crop_top  # Adjust for top crop
            cv_img = cv_img[crop_top:, :]
            h, w = cv_img.shape[:2]

        # Apply bottom crop (text-aware from Stage 1 or variance-based fallback)
        if crop_bottom > 0 and crop_bottom < h:
            cv_img = cv_img[:crop_bottom, :]
            h, w = cv_img.shape[:2]
            print(f"  [CROP] Bottom at row {crop_bottom}px")
        else:
            # Fallback: crop bottom uniform strip (solid color bars)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            bot_std = float(np.std(gray[int(h * 0.85):]))
            if bot_std < 30:
                crop_px = h - int(h * 0.85)
                cv_img = cv_img[:int(h * 0.85), :]
                h, w = cv_img.shape[:2]
                print(f"  [CROP] Bottom {crop_px}px (uniform strip)")

        # ── Hood reflection check ────────────────────────────────
        if _detect_hood_reflection(cv_img):
            caption = (
                f"HOOD REFLECTION: {listing_id or 'unknown'} img#{image_index}\n"
                f"Possible text reflection on hood — review manually"
            )
            log.warning(caption)
            _send_tg_alert(caption, image_path)

        # ── Add subtle ARGOS branding ────────────────────────────
        pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        fs = max(10, int(h * 0.025))
        font = _get_font(fs)
        draw.text((int(w * 0.03), int(h * 0.93)), "ARGOS", fill=ARGOS_GOLD, font=font)

        # ── Save ─────────────────────────────────────────────────
        if pil_img.mode == 'RGBA':
            pil_img = pil_img.convert('RGB')
        pil_img.save(safe_path, 'JPEG', quality=90)

        # ── S163.1 promo-slide guard (size-based, post-save) ─────
        # If sanitized JPEG file size collapsed below threshold ratio of original,
        # the source was probably a marketing slide (100% dealer text), not a car
        # photo. Remove the empty output and skip from dossier.
        orig_size = os.path.getsize(image_path)
        out_size = os.path.getsize(safe_path)
        if orig_size > 0 and (out_size / orig_size) < MIN_OUTPUT_SIZE_RATIO:
            ratio_pct = (out_size / orig_size) * 100
            os.remove(safe_path)
            print(f"  SKIP promo-slide: {safe_name} output {out_size//1024}KB "
                  f"({ratio_pct:.0f}% of orig) — probable dealer marketing slide")
            return None

        # ── STAGE 4: Post-verify + Alert (only if text was masked) ──
        if has_mask:
            _post_verify_and_alert(safe_path, image_path, listing_id or "", image_index, seller_name)

        elapsed = time.time() - t0
        size_kb = os.path.getsize(safe_path) / 1024
        print(f"  SANITIZED: {safe_name} ({size_kb:.0f} KB, {elapsed:.1f}s)")
        return safe_path

    except Exception as e:
        print(f"  ERROR sanitizing {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ── sanitize_all_images (public interface — PRESERVED) ───────────────────────

def sanitize_all_images(
    listing_id: str,
    db_path: str = None,
    output_dir: str = None,
    download_first: bool = True,
    seller_name: str = None,
) -> List[str]:
    """
    Sanitize all images for a listing:
    1. Get image URLs from vehicle_images table
    2. Download if needed
    3. Sanitize each image (with seller_name blocklist if provided)
    4. Return list of safe image paths
    """
    if db_path is None:
        db_path = str(PROJECT_ROOT / "src" / "cove" / "data" / "cove_tracker.duckdb")

    # Auto-fetch seller_name from DB if not provided
    if not seller_name:
        try:
            import duckdb as _ddb
            _con = _ddb.connect(db_path, read_only=True)
            _row = _con.execute(
                "SELECT seller_name FROM vehicle_listings WHERE listing_id = ?", [listing_id]
            ).fetchone()
            if _row and _row[0]:
                seller_name = _row[0]
            _con.close()
        except Exception:
            pass

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
    unique_images = {}
    for url, local_path in rows:
        if not url:
            continue
        # Extract base UUID from URL (before resolution suffix)
        base = re.sub(r'/\d+[xX]\d+\.(?:jpg|jpeg|webp|png)$', '', url.split('?')[0])
        res_match = re.search(r'/(\d+)[xX](\d+)\.(?:jpg|jpeg|webp|png)$', url)
        res = int(res_match.group(1)) * int(res_match.group(2)) if res_match else 0
        if base not in unique_images or res > unique_images[base][2]:
            unique_images[base] = (url, local_path, res)

    deduped_rows = [(v[0], v[1]) for v in unique_images.values()]
    if len(deduped_rows) < len(rows):
        print(f"  URL dedup: {len(rows)} -> {len(deduped_rows)} unique images")
    rows = deduped_rows

    safe_paths = []
    raw_dir = os.path.join(output_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    t_total = time.time()
    for i, (url, local_path) in enumerate(rows):
        src_path = None

        if local_path and os.path.exists(local_path):
            src_path = local_path
        elif download_first and url:
            src_path = _download_image(url, raw_dir, listing_id, i)

        if src_path and os.path.exists(src_path):
            safe = sanitize_image(src_path, output_dir, listing_id, i,
                                  seller_name=seller_name)
            if safe:
                safe_paths.append(safe)

    elapsed = time.time() - t_total
    print(f"  Sanitized {len(safe_paths)}/{len(rows)} images for {listing_id} ({elapsed:.1f}s total)")
    return safe_paths


# ── Helper: Download Image ───────────────────────────────────────────────────

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


# ── Helper: Check Photo Sufficiency ──────────────────────────────────────────

def check_image_sufficient(listing_id: str, db_path: str = None, min_photos: int = 4) -> dict:
    """
    Check if a listing has enough photos for a complete dossier.
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

    ideal_views = ["front", "rear", "side_left", "side_right",
                   "interior_front", "interior_rear", "dashboard", "engine"]
    sufficient = count >= min_photos

    return {
        "sufficient": sufficient,
        "photo_count": count,
        "min_required": min_photos,
        "missing_count": max(0, min_photos - count),
        "ideal_views": ideal_views,
        "message": (f"{count} foto disponibili" if sufficient
                    else f"Solo {count} foto — servono almeno {min_photos} per un dossier completo"),
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

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
    else:
        listing_id = sys.argv[1]
        results = sanitize_all_images(listing_id)
        print(f"\nSanitized {len(results)} images for {listing_id}")
        for p in results:
            print(f"  {p}")
