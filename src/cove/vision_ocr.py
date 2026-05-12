"""
vision_ocr.py — Apple Vision Framework OCR per image_sanitizer

Drop-in replacement per PaddleOCR su macOS 11 Big Sur (AVX1, no Apple Silicon).
Risolve blocker S159 (paddle dylib minos 12.3) + S162 (iMac AVX1) in modo
strutturale: usa Vision.framework built-in macOS 10.13+ via pyobjc, zero ML
deps installate, zero CUDA/AVX2 requirements.

Stack:
  - pyobjc-framework-Vision (Apache 2.0)
  - macOS Vision.framework (system, free)
  - VNRecognizeTextRequest accurate level: equivalente a PaddleOCR PP-OCRv5
    su testo overlay (watermark, targhe, banner dealer)

API:
  detect_text_regions(image_path: str, seller_name: Optional[str] = None,
                      keep_words: frozenset = frozenset(),
                      conf_min: float = 0.25) -> List[Dict]

  Returns: stesso formato di paddleocr-based detector:
    [{box: (x1,y1,x2,y2), text: str, conf: float,
      is_seller: bool, should_mask: bool}]

Reference:
  - Apple Vision: https://developer.apple.com/documentation/vision/vnrecognizetextrequest
  - pyobjc: https://pyobjc.readthedocs.io/
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

log = logging.getLogger("argos.sanitizer.vision")

# Lazy import — only if explicitly called (consente fallback graceful)
_VISION_AVAILABLE = None


def _check_vision_available() -> bool:
    global _VISION_AVAILABLE
    if _VISION_AVAILABLE is not None:
        return _VISION_AVAILABLE
    try:
        import Vision  # noqa: F401
        import Quartz  # noqa: F401
        _VISION_AVAILABLE = True
    except ImportError as e:
        log.warning(f"Vision/Quartz not available: {e}")
        _VISION_AVAILABLE = False
    return _VISION_AVAILABLE


def detect_text_regions(
    image_path: str,
    seller_name: Optional[str] = None,
    keep_words: FrozenSet[str] = frozenset(),
    conf_min: float = 0.25,
    min_text_len: int = 2,
) -> List[Dict]:
    """
    Detect text regions in image via Apple Vision Framework.

    Returns same shape as paddleocr-based detector:
      [{box: (x1,y1,x2,y2), text, conf, is_seller, should_mask}]
    """
    if not _check_vision_available():
        return []

    if not Path(image_path).exists():
        log.warning(f"image not found: {image_path}")
        return []

    import Vision
    import Quartz
    from Foundation import NSURL

    # Load image via Quartz (CGImage)
    url = NSURL.fileURLWithPath_(str(image_path))
    src = Quartz.CGImageSourceCreateWithURL(url, None)
    if src is None:
        log.error(f"CGImageSource cannot read {image_path}")
        return []
    cg_image = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    if cg_image is None:
        log.error(f"CGImageSourceCreateImageAtIndex failed for {image_path}")
        return []

    img_w = Quartz.CGImageGetWidth(cg_image)
    img_h = Quartz.CGImageGetHeight(cg_image)

    # Build Vision request
    req = Vision.VNRecognizeTextRequest.alloc().init()
    # Accuracy level: VNRequestTextRecognitionLevelAccurate = 0, Fast = 1
    req.setRecognitionLevel_(0)  # Accurate
    req.setUsesLanguageCorrection_(True)
    # Vision will pick best supported langs; for DE/IT/EN dealer text
    try:
        req.setRecognitionLanguages_(["en-US", "de-DE", "it-IT"])
    except Exception:
        pass

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    success, err = handler.performRequests_error_([req], None)
    if not success:
        log.error(f"Vision request failed: {err}")
        return []

    observations = req.results() or []

    # Build seller words blocklist
    seller_words = set()
    if seller_name:
        for sw in seller_name.lower().split():
            if len(sw) >= 3:
                seller_words.add(sw)

    results: List[Dict] = []

    for obs in observations:
        # Top candidate
        candidates = obs.topCandidates_(1)
        if not candidates:
            continue
        candidate = candidates[0]
        text = str(candidate.string())
        conf = float(candidate.confidence())

        if conf < conf_min:
            continue
        if len(text.strip()) < min_text_len:
            continue

        # Vision returns boundingBox in normalized coordinates [0,1] with
        # origin at BOTTOM-LEFT. Convert to pixel coordinates with TOP-LEFT origin.
        bb = obs.boundingBox()
        # bb is a CGRect: origin.x, origin.y (bottom-left), size.width, size.height
        x_norm = bb.origin.x
        y_norm_bl = bb.origin.y  # bottom-left
        w_norm = bb.size.width
        h_norm = bb.size.height

        x1 = int(x_norm * img_w)
        x2 = int((x_norm + w_norm) * img_w)
        # Flip Y: top-left y = img_h - (bottom-left y + height)
        y1 = int(img_h - (y_norm_bl + h_norm) * img_h)
        y2 = int(img_h - y_norm_bl * img_h)

        # Clamp
        x1 = max(0, min(img_w, x1))
        x2 = max(0, min(img_w, x2))
        y1 = max(0, min(img_h, y1))
        y2 = max(0, min(img_h, y2))

        words_lower = text.lower().strip().split()

        is_seller = False
        if seller_words:
            for wl in words_lower:
                for sw in seller_words:
                    if sw in wl or wl in sw:
                        is_seller = True
                        break
                if is_seller:
                    break

        # Decide mask (mirror paddle-based logic)
        should_mask = True
        if not is_seller:
            if all(w in keep_words for w in words_lower):
                should_mask = False
            elif len(text.strip()) <= 2:
                should_mask = False
            elif all(w.replace('.', '').replace(',', '').replace('-', '').isdigit()
                     for w in words_lower):
                should_mask = False

        results.append({
            'box': (x1, y1, x2, y2),
            'text': text,
            'conf': conf,
            'is_seller': is_seller,
            'should_mask': should_mask,
        })

    return results


# ── Smoke CLI ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python3 vision_ocr.py <image_path> [seller_name]")
        sys.exit(2)

    img = sys.argv[1]
    seller = sys.argv[2] if len(sys.argv) >= 3 else None

    if not _check_vision_available():
        print("ERROR: Vision framework unavailable")
        sys.exit(1)

    import time
    t0 = time.time()
    regions = detect_text_regions(img, seller_name=seller)
    elapsed = time.time() - t0

    print(f"\nVision OCR — {img}")
    print(f"Elapsed: {elapsed*1000:.0f}ms")
    print(f"Regions: {len(regions)}")
    print("-" * 72)
    for i, r in enumerate(regions):
        seller_tag = " [SELLER]" if r['is_seller'] else ""
        mask_tag = " (mask)" if r['should_mask'] else " (keep)"
        print(f"  {i:2d}. conf={r['conf']:.2f} box={r['box']}{seller_tag}{mask_tag}")
        print(f"       text: {r['text']!r}")
