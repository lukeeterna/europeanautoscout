"""ARGOS image-shield — D-25 implementation.

Pipeline Pillow-only Big Sur safe (no OpenCV, no GPU) per proteggere foto
annuncio EU da reverse-search (Google Lens / TinEye / Yandex) mantenendo
info-value ispezione per il dealer.

Spec da D-25 (DECISIONS.md ARGOS):
  1. crop centrale 65% area (rimuove targa + landmark contesto)
  2. watermark testo "ARGOS PREVIEW — DOSSIER #{id}" tilted 35°, font 48pt,
     alpha 0.28, ripetuto griglia 3x3
  3. HSV shift hue+5° / sat-8%
  4. JPEG re-encode quality=72, EXIF stripped

Source: research Thread 1 (S167) Pillow-only stack. Adversarial perturbation
scartato (BlurGuard 2025 rompe protezione). SD img2img scartato (rompe trust
+ GPU cost).
"""
from __future__ import annotations

import argparse
import io
import sys
import math
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageChops

# Default config — tunable per D-25 trade-off review
DEFAULT_CROP_RATIO = 0.65       # mantieni 65% area centrale
DEFAULT_WATERMARK_ALPHA = 72    # 0-255 (~0.28 alpha)
DEFAULT_WATERMARK_FONT_SIZE = 48
DEFAULT_WATERMARK_TILT = 35     # gradi
DEFAULT_WATERMARK_GRID = (3, 3) # 3x3 ripetizioni
DEFAULT_HSV_HUE_SHIFT = 5       # gradi (0-360)
DEFAULT_HSV_SAT_SCALE = 0.92    # 0.92 = -8%
DEFAULT_JPEG_QUALITY = 72


def _find_font(size: int) -> ImageFont.ImageFont:
    """Best-effort sans-serif on macOS Big Sur, fallback default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Avenir.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _strip_exif(img: Image.Image) -> Image.Image:
    """Rimuovi EXIF (geo location, camera info) — bool flag rispetto a info dict."""
    data = list(img.getdata())
    clean = Image.new(img.mode, img.size)
    clean.putdata(data)
    return clean


def _center_crop(img: Image.Image, ratio: float) -> Image.Image:
    """Crop centrale mantenendo `ratio` dell'area originale.

    Area = w * h. Per mantenere `ratio` area mantenendo aspect ratio:
    fattore_lato = sqrt(ratio).
    """
    w, h = img.size
    scale = math.sqrt(ratio)
    new_w, new_h = int(w * scale), int(h * scale)
    left = (w - new_w) // 2
    top = (h - new_h) // 2
    return img.crop((left, top, left + new_w, top + new_h))


def _hsv_shift(img: Image.Image, hue_shift_deg: int, sat_scale: float) -> Image.Image:
    """Shift HSV: hue rotation + saturation scale.

    Implementazione manuale Pillow (HSV mode + arithmetic).
    """
    rgb = img.convert("RGB")
    hsv = rgb.convert("HSV")
    h, s, v = hsv.split()

    # Hue shift: H è 0-255 (mapped to 0-360°). Conversione: 1° = 255/360 ~ 0.708.
    hue_offset = int(hue_shift_deg * 255 / 360) & 0xFF
    h_shifted = h.point(lambda px: (px + hue_offset) & 0xFF)

    # Saturation scale: clip a 0-255.
    s_scaled = s.point(lambda px: min(255, max(0, int(px * sat_scale))))

    hsv_new = Image.merge("HSV", (h_shifted, s_scaled, v))
    return hsv_new.convert("RGB")


def _add_watermark_grid(
    img: Image.Image,
    text: str,
    font_size: int,
    alpha: int,
    tilt_deg: int,
    grid: tuple[int, int],
) -> Image.Image:
    """Aggiungi watermark testo ripetuto su griglia, tilted.

    Watermark renderizzato su layer RGBA trasparente, poi ruotato e composto.
    """
    base = img.convert("RGBA")
    w, h = base.size

    # Layer trasparente full-size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = _find_font(font_size)

    rows, cols = grid
    # Bounding box testo per spacing
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except AttributeError:
        tw, th = draw.textsize(text, font=font)

    cell_w = layer.size[0] // cols
    cell_h = layer.size[1] // rows
    for r in range(rows):
        for c in range(cols):
            x = c * cell_w + (cell_w - tw) // 2
            y = r * cell_h + (cell_h - th) // 2
            # Doppio layer per leggibilità: stroke scuro + fill chiaro
            draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, alpha // 2))
            draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))

    # Rotate
    rotated = layer.rotate(tilt_deg, resample=Image.BICUBIC, expand=False)

    # Crop centrato a dimensione originale
    rx, ry = rotated.size
    rotated_cropped = rotated.crop(
        ((rx - w) // 2, (ry - h) // 2, (rx - w) // 2 + w, (ry - h) // 2 + h)
    )

    return Image.alpha_composite(base, rotated_cropped).convert("RGB")


def protect(
    input_path: str | Path,
    output_path: str | Path,
    dossier_id: str,
    *,
    crop_ratio: float = DEFAULT_CROP_RATIO,
    watermark_alpha: int = DEFAULT_WATERMARK_ALPHA,
    font_size: int = DEFAULT_WATERMARK_FONT_SIZE,
    tilt_deg: int = DEFAULT_WATERMARK_TILT,
    grid: tuple[int, int] = DEFAULT_WATERMARK_GRID,
    hue_shift: int = DEFAULT_HSV_HUE_SHIFT,
    sat_scale: float = DEFAULT_HSV_SAT_SCALE,
    jpeg_quality: int = DEFAULT_JPEG_QUALITY,
) -> dict:
    """Applica pipeline image-shield D-25.

    Returns dict con metadata operazione (sizes, hash pre/post per validation).
    """
    src = Image.open(input_path)
    src.load()
    orig_size = src.size

    # 1. Center crop 65% area
    cropped = _center_crop(src, crop_ratio)

    # 2. HSV shift
    hsv_shifted = _hsv_shift(cropped, hue_shift, sat_scale)

    # 3. Watermark grid
    watermark_text = f"ARGOS PREVIEW — DOSSIER #{dossier_id}"
    watermarked = _add_watermark_grid(
        hsv_shifted,
        watermark_text,
        font_size,
        watermark_alpha,
        tilt_deg,
        grid,
    )

    # 4. Strip EXIF + JPEG re-encode quality 72
    clean = _strip_exif(watermarked)
    out_buffer = io.BytesIO()
    clean.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    out_buffer.seek(0)
    final = Image.open(out_buffer)
    final.save(output_path, format="JPEG", quality=jpeg_quality, optimize=True)

    # Validation hashes
    try:
        import imagehash
        h_orig = str(imagehash.phash(src))
        h_proc = str(imagehash.phash(final))
        hamming = imagehash.phash(src) - imagehash.phash(final)
    except ImportError:
        h_orig = h_proc = "imagehash_not_available"
        hamming = -1

    return {
        "input": str(input_path),
        "output": str(output_path),
        "orig_size": orig_size,
        "final_size": final.size,
        "phash_orig": h_orig,
        "phash_processed": h_proc,
        "hamming_distance": int(hamming) if isinstance(hamming, int) else hamming,
        "dossier_id": dossier_id,
        "params": {
            "crop_ratio": crop_ratio,
            "watermark_alpha": watermark_alpha,
            "tilt_deg": tilt_deg,
            "grid": list(grid),
            "hue_shift": hue_shift,
            "sat_scale": sat_scale,
            "jpeg_quality": jpeg_quality,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="ARGOS image-shield D-25")
    ap.add_argument("input", help="Path foto annuncio originale (JPEG/PNG)")
    ap.add_argument("output", help="Path output JPEG protetto")
    ap.add_argument("--dossier-id", required=True, help="ID dossier per watermark")
    ap.add_argument("--crop-ratio", type=float, default=DEFAULT_CROP_RATIO)
    ap.add_argument("--alpha", type=int, default=DEFAULT_WATERMARK_ALPHA)
    ap.add_argument("--jpeg-q", type=int, default=DEFAULT_JPEG_QUALITY)
    args = ap.parse_args()

    result = protect(
        args.input,
        args.output,
        args.dossier_id,
        crop_ratio=args.crop_ratio,
        watermark_alpha=args.alpha,
        jpeg_quality=args.jpeg_q,
    )
    print(f"Output: {result['output']}")
    print(f"Size: {result['orig_size']} -> {result['final_size']}")
    print(f"phash Hamming distance: {result['hamming_distance']}")
    print(f"Target distance ≥20 bit per evasione (vedi D-25 validation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
