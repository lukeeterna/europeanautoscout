#!/usr/bin/env python3
"""
s183_autogen_zones.py — GATE A2: auto-generazione zones.json + overlay PNG

Genera `tests/uat_golden/<basename>.zones.json` per i 10 sample golden
usando Apple Vision Framework (vision_ocr.detect_text_regions).
Genera anche `tests/uat_golden/overlay/<basename>_overlay.png` per UAT visivo Luke.

Venv obbligatorio: ~/.argos-sanitizer-venv/bin/python s183_autogen_zones.py

CLI:
    python s183_autogen_zones.py              # processa tutti g01..g10
    python s183_autogen_zones.py --force      # sovrascrive .zones.json esistenti
    python s183_autogen_zones.py --only g01,g03,g05
    python s183_autogen_zones.py --dry-run    # verifica schema + exit 0/1

Reference: prompts/s183_resume_a2_b_c_d.md righe 36-72
D-32 sanitizer: vincolo Pillow-only, AVX1 macOS 11 Big Sur
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── sys.path hack per import src.cove da working dir qualsiasi ───────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # tools/scripts/../../
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ── Costanti ─────────────────────────────────────────────────────────────────
GOLDEN_DIR = _REPO_ROOT / "tests" / "uat_golden"
OVERLAY_DIR = GOLDEN_DIR / "overlay"

# Mapping sample_id → (seller_name, image_index)
# image_index = indice usato da sanitize_image (0-based, per file nel listing)
SAMPLE_MAP: Dict[str, Tuple[Optional[str], int]] = {
    "g01": ("Autohaus Isernhagen", 0),
    "g02": ("Autohaus Isernhagen", 1),
    "g03": ("Autohaus Isernhagen", 2),
    "g04": ("Autohaus Isernhagen", 0),
    "g05": ("Autohaus Isernhagen", 1),
    "g06": (None, 0),   # Luke compila A2-bis
    "g07": (None, 0),
    "g08": (None, 0),
    "g09": (None, 0),
    "g10": (None, 0),
}

# Colori overlay per type (RGB per Pillow)
ZONE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "tagline":            (220, 120, 0),    # arancione
    "footer_brand_row":   (200, 200, 0),    # giallo
    "dealer_signage":     (180, 0,  180),   # magenta
    "auto_features_zone": (0,  180, 0),     # verde (solo bordo)
    # NOTA: plate_zone_fallback / real_plate / watermark_plate rimossi S183
    # 2026-05-21 — vedi commento in _generate_zones() per rationale.
}
DEFAULT_COLOR = (100, 100, 220)  # blu — tipo non mappato

# Logica classificazione bbox via y_center / x_center (frazioni H e W)
FOOTER_Y_FRAC    = 0.85   # y_center > H*0.85 → footer_brand_row
PLATE_Y_LOW_FRAC = 0.55   # y_center tra 0.55 e 0.85
PLATE_Y_HIGH_FRAC= 0.85
PLATE_X_LOW_FRAC = 0.25   # x_center tra 0.25 e 0.75
PLATE_X_HIGH_FRAC= 0.75

# Heuristic band: bottom 12% → footer_brand_row deterministic
FOOTER_HEUR_FRAC = 0.88   # y1 = int(H * 0.88)

# Zona auto-features: bbox relativo standard listing dealer
AUTO_FEATURES_ZONE = {"x1": 0.30, "y1": 0.20, "x2": 0.70, "y2": 0.78}

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("s183.autogen")


# ── Classificazione type da posizione bbox ────────────────────────────────────

def _classify_type(x1: int, y1: int, x2: int, y2: int, img_w: int, img_h: int) -> str:
    """Classifica type PII zone in base a posizione relativa.

    NOTA S183 redesign 2026-05-21: Vision Framework rileva testo generico, NON
    oggetti-targa. La classificazione watermark_plate via Vision è rimossa (fail
    mode: faro con testo grafico rilevato come targa). plate_zone_fallback
    heuristic-only rimosso (pre-flight 10/10 sample golden: 0 detection valida).
    Targa coverage ora SOLO via `_apply_whitelist_masks` B1 deterministic
    (bottom 12% + sides 5%) durante sanitize_image.
    """
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    cx_frac = cx / img_w
    cy_frac = cy / img_h

    if cy_frac > FOOTER_Y_FRAC:
        return "footer_brand_row"

    # Zona centrale-bassa (ex watermark_plate): ora → dealer_signage.
    # Vision vede TESTO in questa area = scritta dealer su carrozzeria, non targa.
    if (PLATE_Y_LOW_FRAC <= cy_frac <= PLATE_Y_HIGH_FRAC
            and PLATE_X_LOW_FRAC <= cx_frac <= PLATE_X_HIGH_FRAC):
        return "dealer_signage"

    # Upper third → tendenzialmente banner dealer / header
    if cy_frac < 0.35:
        return "dealer_signage"

    return "tagline"


# ── Generazione zones.json per un singolo sample ─────────────────────────────

def _generate_zones(
    img_path: Path,
    sample_id: str,
    seller_name: Optional[str],
    image_index: int,
) -> Dict:
    """
    Chiama detect_text_regions + applica heuristics.
    Ritorna il dict zones.json completo.
    """
    from PIL import Image as PILImage

    # Dimensioni reali immagine (ground truth per W/H)
    with PILImage.open(img_path) as pil_img:
        img_w, img_h = pil_img.size

    # Importa Vision OCR (lazy, fallisce se Vision Framework non disponibile)
    try:
        from src.cove.vision_ocr import detect_text_regions
    except ImportError as e:
        log.error(f"[{sample_id}] import vision_ocr FAIL: {e}")
        log.error("Assicurati di usare ~/.argos-sanitizer-venv/bin/python")
        sys.exit(1)

    t0 = time.time()
    regions = detect_text_regions(
        str(img_path),
        seller_name=seller_name,
        conf_min=0.50,  # alzato da 0.25 — taglia false positive grafici (es. "COO" su faro conf 0.30)
    )
    elapsed = time.time() - t0

    pii_zones: List[Dict] = []

    # Traccia se abbiamo già una footer_brand_row da Vision (per evitare duplicati)
    has_vision_footer = False

    vision_count = 0
    for r in regions:
        if not r.get("should_mask", False):
            continue

        x1, y1, x2, y2 = r["box"]
        zone_type = _classify_type(x1, y1, x2, y2, img_w, img_h)

        entry: Dict = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "type": zone_type,
            "source": "vision",
            "conf": round(r["conf"], 3),
            "text": r["text"],
        }
        pii_zones.append(entry)

        if zone_type == "footer_brand_row":
            has_vision_footer = True

        vision_count += 1

    # Heuristic deterministic: footer_brand_row bottom 12%
    # Aggiunge SEMPRE — è l'ancora sicura indipendente da Vision.
    # Il sanitizer applicherà mask dall'unione; duplicati sovrapposti non danneggiano.
    heuristic_count = 0
    footer_heur: Dict = {
        "x1": 0,
        "y1": int(img_h * FOOTER_HEUR_FRAC),
        "x2": "W",
        "y2": "H",
        "type": "footer_brand_row",
        "source": "heuristic",
    }
    pii_zones.append(footer_heur)
    heuristic_count += 1

    # S183 redesign 2026-05-21 (CTO Opus): plate_zone_fallback hardcoded RIMOSSO.
    # Pre-flight 10 sample golden: Vision OCR 0/10 detect targhe (font condensato
    # non riconosciuto come testo); color-signature white-rect 2/10 ma false
    # positive (carrozzeria bianca/sfondo aspect 5.5+). Targa = oggetto a
    # posizione variabile non rilevabile heuristic-only su Big Sur Pillow-only.
    # Bbox fisso 35%-65%w × 62%-90%h copriva area random carrozzeria → fail mode.
    #
    # Decisione: NO plate zone iniettato. Targa watermark coverage delegata a
    # `_apply_whitelist_masks` B1 (bottom 12% + sides 5% deterministic) che copre
    # area inferiore tipica targa frontale EU 3-quarti.
    #
    # Vera plate detection (ML/CV) deferita BACKLOG S184+ se UAT produzione
    # rivela leak targa concreto. Documentato in commit GATE D.

    out = {
        "image": img_path.name,
        "seller_name": seller_name,
        "image_index": image_index,
        "pii_zones": pii_zones,
        "auto_features_zone": AUTO_FEATURES_ZONE,
        "_meta": {
            "img_w": img_w,
            "img_h": img_h,
            "vision_elapsed_s": round(elapsed, 2),
            "vision_regions_total": len(regions),
            "vision_should_mask": vision_count,
            "heuristic_count": heuristic_count,
            "generated_by": "s183_autogen_zones.py",
        },
    }

    return out, vision_count, heuristic_count, img_w, img_h


# ── Generazione overlay PNG ───────────────────────────────────────────────────

def _generate_overlay(
    img_path: Path,
    zones_data: Dict,
    overlay_path: Path,
    img_w: int,
    img_h: int,
) -> None:
    """
    Copia immagine originale, disegna bbox colorati per ogni zona.
    Solo Pillow — zero opencv, zero torch.
    """
    from PIL import Image as PILImage, ImageDraw, ImageFont

    img = PILImage.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # Font di sistema (fallback a default se non disponibile)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=14)
    except Exception:
        font = ImageFont.load_default()

    for zone in zones_data.get("pii_zones", []):
        ztype = zone.get("type", "unknown")
        source = zone.get("source", "?")
        conf = zone.get("conf")
        text_label = zone.get("text", "")

        # Risolvi "W"/"H" placeholder a pixel reali
        x1 = int(zone["x1"]) if zone["x1"] != "W" else img_w
        y1 = int(zone["y1"]) if zone["y1"] != "H" else img_h
        x2 = int(zone["x2"]) if zone["x2"] != "W" else img_w
        y2 = int(zone["y2"]) if zone["y2"] != "H" else img_h

        color_rgb = ZONE_COLORS.get(ztype, DEFAULT_COLOR)
        color_fill = color_rgb + (40,)   # RGBA semi-trasparente fill
        color_border = color_rgb + (200,)

        draw.rectangle([(x1, y1), (x2, y2)], fill=color_fill, outline=color_border, width=2)

        # Label: "type:conf" o "type:heuristic"
        if conf is not None:
            label = f"{ztype}:{conf:.2f}"
        else:
            label = f"{ztype}:heur"

        # Testo abbreviato del testo rilevato (max 30 char)
        if text_label:
            short_text = text_label[:30].replace("\n", " ")
            label += f' "{short_text}"'

        # Sfondo bianco opaco per leggibilità testo
        label_x = max(0, x1 + 2)
        label_y = max(0, y1 - 16)
        draw.rectangle(
            [(label_x, label_y), (label_x + len(label) * 7 + 4, label_y + 14)],
            fill=(255, 255, 255, 180),
        )
        draw.text((label_x + 2, label_y), label, fill=(0, 0, 0, 255), font=font)

    # auto_features_zone: bbox relativo → pixel, solo bordo verde
    afz = zones_data.get("auto_features_zone")
    if afz:
        ax1 = int(afz["x1"] * img_w)
        ay1 = int(afz["y1"] * img_h)
        ax2 = int(afz["x2"] * img_w)
        ay2 = int(afz["y2"] * img_h)
        green = ZONE_COLORS["auto_features_zone"] + (180,)
        draw.rectangle([(ax1, ay1), (ax2, ay2)], fill=None, outline=green, width=3)
        draw.text(
            (ax1 + 2, ay1 + 2),
            "auto_features_zone",
            fill=(0, 180, 0, 220),
            font=font,
        )

    img.save(str(overlay_path), "JPEG", quality=90)


# ── Smoke / dry-run ───────────────────────────────────────────────────────────

def _dry_run(only_ids: Optional[List[str]]) -> int:
    """
    Verifica:
    1. Tutti i file golden presenti
    2. Tutti i .zones.json presenti e schema valido (roundtrip json)
    3. Conta zone totali
    Exit 0 se tutto OK, exit 1 se qualcosa fail.
    """
    errors = 0
    total_zones = 0

    ids = only_ids if only_ids else sorted(SAMPLE_MAP.keys())

    print("=== DRY-RUN S183 zones.json verification ===")

    for sid in ids:
        pattern = str(GOLDEN_DIR / f"{sid}_*.jpg")
        matches = sorted(glob.glob(pattern))
        if not matches:
            print(f"[FAIL] {sid}: jpg non trovato in {GOLDEN_DIR}")
            errors += 1
            continue

        img_path = Path(matches[0])
        zones_path = img_path.with_suffix("") .parent / (img_path.stem + ".zones.json")

        if not zones_path.exists():
            print(f"[FAIL] {sid}: {zones_path.name} non esiste — esegui senza --dry-run prima")
            errors += 1
            continue

        try:
            raw = zones_path.read_text()
            data = json.loads(raw)
            # Roundtrip verifica
            _ = json.dumps(data)
            nzones = len(data.get("pii_zones", []))
            total_zones += nzones
            # Verifica campi obbligatori
            for required_key in ("image", "image_index", "pii_zones", "auto_features_zone"):
                if required_key not in data:
                    raise ValueError(f"campo mancante: {required_key}")
            print(f"[OK]   {sid}: {zones_path.name} — {nzones} zones")
        except Exception as e:
            print(f"[FAIL] {sid}: schema error in {zones_path.name}: {e}")
            errors += 1

    print(f"\nTotale zone: {total_zones}")
    print(f"Errori: {errors}")

    if errors == 0:
        print("DRY-RUN: PASS")
        return 0
    else:
        print("DRY-RUN: FAIL")
        return 1


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="S183 GATE A2 — auto-generazione zones.json + overlay PNG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sovrascrive .zones.json esistenti (default: skip se esiste)",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Processa solo subset, es: g01,g03,g05",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verifica schema JSON esistente senza generare nulla",
    )
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Salta generazione overlay PNG (solo zones.json)",
    )

    args = parser.parse_args()

    only_ids: Optional[List[str]] = None
    if args.only:
        only_ids = [s.strip() for s in args.only.split(",") if s.strip()]
        # Valida che siano nel SAMPLE_MAP
        for sid in only_ids:
            if sid not in SAMPLE_MAP:
                print(f"ERROR: --only contiene '{sid}' non riconosciuto. Validi: {sorted(SAMPLE_MAP.keys())}")
                return 1

    if args.dry_run:
        return _dry_run(only_ids)

    # Crea overlay dir se non esiste
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    ids_to_process = only_ids if only_ids else sorted(SAMPLE_MAP.keys())

    overall_ok = True
    results_log = []

    for sid in ids_to_process:
        seller_name, image_index = SAMPLE_MAP[sid]

        # Trova file jpg
        pattern = str(GOLDEN_DIR / f"{sid}_*.jpg")
        matches = sorted(glob.glob(pattern))
        if not matches:
            entry = {
                "file": sid,
                "status": "ERROR",
                "reason": f"jpg non trovato con pattern {sid}_*.jpg in {GOLDEN_DIR}",
            }
            print(json.dumps(entry))
            results_log.append(entry)
            overall_ok = False
            continue

        img_path = Path(matches[0])
        basename = img_path.stem  # es: g01_isernhagen_smoke_00

        zones_path = GOLDEN_DIR / f"{basename}.zones.json"
        overlay_path = OVERLAY_DIR / f"{basename}_overlay.png"

        # Skip se già esiste e non --force
        if zones_path.exists() and not args.force:
            entry = {
                "file": img_path.name,
                "status": "skipped",
                "reason": "exists — usa --force per sovrascrivere",
                "out": str(zones_path.relative_to(_REPO_ROOT)),
            }
            print(json.dumps(entry))
            results_log.append(entry)
            continue

        try:
            zones_data, vision_count, heuristic_count, img_w, img_h = _generate_zones(
                img_path=img_path,
                sample_id=sid,
                seller_name=seller_name,
                image_index=image_index,
            )

            # Scrivi zones.json
            zones_path.write_text(json.dumps(zones_data, indent=2, ensure_ascii=False))

            # Genera overlay PNG
            if not args.no_overlay:
                _generate_overlay(
                    img_path=img_path,
                    zones_data=zones_data,
                    overlay_path=overlay_path,
                    img_w=img_w,
                    img_h=img_h,
                )

            entry = {
                "file": img_path.name,
                "seller": seller_name,
                "image_index": image_index,
                "img_size": f"{img_w}x{img_h}",
                "vision_count": vision_count,
                "heuristic_count": heuristic_count,
                "total_zones": vision_count + heuristic_count,
                "out": str(zones_path.relative_to(_REPO_ROOT)),
                "overlay": str(overlay_path.relative_to(_REPO_ROOT)) if not args.no_overlay else None,
                "status": "OK",
            }
            print(json.dumps(entry))
            results_log.append(entry)

        except Exception as e:
            import traceback
            entry = {
                "file": img_path.name,
                "status": "ERROR",
                "reason": str(e),
                "traceback": traceback.format_exc().splitlines()[-3:],
            }
            print(json.dumps(entry))
            results_log.append(entry)
            overall_ok = False

    # Sommario finale
    ok_count = sum(1 for r in results_log if r.get("status") == "OK")
    skip_count = sum(1 for r in results_log if r.get("status") == "skipped")
    err_count = sum(1 for r in results_log if r.get("status") == "ERROR")
    total_zones_gen = sum(r.get("total_zones", 0) for r in results_log if r.get("status") == "OK")

    summary = {
        "summary": True,
        "processed": ok_count,
        "skipped": skip_count,
        "errors": err_count,
        "total_zones_generated": total_zones_gen,
        "overlay_dir": str(OVERLAY_DIR) if not args.no_overlay else None,
        "next_step": "open tests/uat_golden/overlay/ per UAT visivo Luke",
    }
    print(json.dumps(summary))

    if not args.no_overlay and ok_count > 0:
        print(f"\nAprire overlay: open {OVERLAY_DIR}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
