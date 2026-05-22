"""
image_downloader.py -- ARGOS HD Image Downloader
CoVe 2026 | Enterprise Grade

Scarica immagini ad ALTA RISOLUZIONE dai portali EU per il dossier dealer.
Ogni portale ha il suo pattern CDN — il downloader sa come ottenere il max.

Strategia: scarica SOLO per listing che passano il CoVe (PROCEED/VIN_CHECK).
Non 640 immagini — solo le 20-30 opportunita' migliori.

Risoluzioni ottenibili:
  AutoScout24:  2560x1920 (upgrade da 250x188 thumbnail)
  OLX Group:    2048x1360 (upgrade da 320x240 thumbnail)
  Finn/Blocket: 1600w (upgrade da 320w)
  Marktplaats:  1024x1024 (upgrade da $_14 thumb)
  Willhaben:    big (rule/big/)
  Generic:      whatever the portal serves

Author: ARGOS CTO Stack
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("argos.image_downloader")

# Base cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "images"

# Portal-specific URL upgrade rules: (pattern_to_find, replacement)
# These transform thumbnail URLs to full-resolution URLs
PORTAL_IMAGE_UPGRADES: Dict[str, List[Tuple[str, str]]] = {
    # AutoScout24: CDN supports SPECIFIC sizes only — verified 2026-05-22:
    # 250x188 (thumb), 800x600 (MD), 1280x960 (HD). Others (640x480, 1024x768,
    # 1600x1200, 2048x1536, 2560x1920) return 404. Use 1280x960 as max.
    "autoscout24": [
        (r"/\d+x\d+\.webp", "/1280x960.webp"),
        (r"/\d+x\d+\.jpg", "/1280x960.jpg"),
        (r"/resize/\d+x\d+>", "/resize/1280x960>"),
    ],
    # OLX Group (Otomoto, Standvirtual, Autovit, OLX PL)
    "olx": [
        (r";s=\d+x\d+", ";s=2048x1360"),
    ],
    "otomoto": [
        (r";s=\d+x\d+", ";s=2048x1360"),
    ],
    "standvirtual": [
        (r";s=\d+x\d+", ";s=2048x1360"),
    ],
    "autovit": [
        (r";s=\d+x\d+", ";s=2048x1360"),
    ],
    # Finn.no / Blocket.se (Schibsted Group)
    "finn": [
        (r"/dynamic/\d+w/", "/dynamic/1600w/"),
        (r"/dynamic/default/", "/dynamic/1600w/"),
    ],
    "blocket": [
        (r"/dynamic/\d+w/", "/dynamic/1600w/"),
        (r"/dynamic/default/", "/dynamic/1600w/"),
    ],
    # Marktplaats / 2dehands
    "marktplaats": [
        (r"\$_\d+\.JPG", "$_85.JPG"),
        (r"\$_\d+\.jpg", "$_85.jpg"),
    ],
    "2dehands": [
        (r"\$_\d+\.JPG", "$_85.JPG"),
        (r"\$_\d+\.jpg", "$_85.jpg"),
    ],
    # Willhaben
    "willhaben": [
        (r"/rule/\w+/", "/rule/big/"),
    ],
}


@dataclass
class DownloadedImage:
    """Immagine scaricata e cached localmente."""
    local_path: str
    original_url: str
    portal: str
    listing_id: str
    width: int = 0
    height: int = 0
    size_bytes: int = 0


def _get_portal_key(portal: str) -> str:
    """Normalizza nome portale per lookup upgrade rules."""
    p = portal.lower().replace("_", "").replace("-", "")
    for key in PORTAL_IMAGE_UPGRADES:
        if key in p:
            return key
    return ""


def _upgrade_url(url: str, portal: str) -> str:
    """Trasforma URL thumbnail in URL full-resolution."""
    key = _get_portal_key(portal)
    if not key:
        return url

    upgraded = url
    for pattern, replacement in PORTAL_IMAGE_UPGRADES[key]:
        upgraded = re.sub(pattern, replacement, upgraded)

    if upgraded != url:
        logger.debug("Image upgrade: %s → %s", url[:80], upgraded[:80])
    return upgraded


class ImageDownloader:
    """
    Scarica e cache immagini HD per dossier dealer.

    Usage:
        dl = ImageDownloader()
        images = dl.download_for_listing(listing_id, portal, image_urls)
        # images[0].local_path → path locale del file immagine
    """

    def __init__(self, cache_dir: Optional[str] = None, max_per_listing: int = 6):
        self._cache_dir = Path(cache_dir) if cache_dir else _CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._max_per_listing = max_per_listing
        self._fetcher = None

    def _get_fetcher(self):
        """Lazy init ResilientFetcher."""
        if self._fetcher is None:
            try:
                from resilient_fetcher import ResilientFetcher
            except ImportError:
                from tools.scrapers.resilient_fetcher import ResilientFetcher
            self._fetcher = ResilientFetcher()
        return self._fetcher

    def download_for_listing(
        self,
        listing_id: str,
        portal: str,
        image_urls: List[str],
        referer: str = "",
    ) -> List[DownloadedImage]:
        """
        Scarica immagini per un listing specifico.

        Args:
            listing_id: ID listing (per directory cache)
            portal: Nome portale (per upgrade URL)
            image_urls: Lista URL immagini (thumbnail o full)
            referer: Referer header (default: auto dal portal)

        Returns: Lista di DownloadedImage con path locali
        """
        if not image_urls:
            return []

        # Directory cache per questo listing
        safe_id = re.sub(r'[^\w\-]', '_', listing_id)[:64]
        listing_dir = self._cache_dir / portal / safe_id
        listing_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        urls_to_fetch = image_urls[:self._max_per_listing]

        for i, url in enumerate(urls_to_fetch):
            if not url or not url.startswith(("http", "//")):
                continue

            if url.startswith("//"):
                url = f"https:{url}"

            # Upgrade a full-res
            full_url = _upgrade_url(url, portal)

            # Check cache
            ext = _guess_extension(full_url)
            filename = f"img_{i:02d}{ext}"
            filepath = listing_dir / filename

            if filepath.exists() and filepath.stat().st_size > 1000:
                downloaded.append(DownloadedImage(
                    local_path=str(filepath),
                    original_url=full_url,
                    portal=portal,
                    listing_id=listing_id,
                    size_bytes=filepath.stat().st_size,
                ))
                continue

            # Download
            try:
                data = self._fetch_image(full_url, portal, referer)
                if data and len(data) > 1000:  # Minimo 1KB (no placeholder)
                    filepath.write_bytes(data)
                    downloaded.append(DownloadedImage(
                        local_path=str(filepath),
                        original_url=full_url,
                        portal=portal,
                        listing_id=listing_id,
                        size_bytes=len(data),
                    ))
                    logger.debug("Scaricata: %s (%d KB)", filename, len(data) // 1024)
                else:
                    # Fallback: prova URL originale se upgrade fallisce
                    if full_url != url:
                        data = self._fetch_image(url, portal, referer)
                        if data and len(data) > 1000:
                            filepath.write_bytes(data)
                            downloaded.append(DownloadedImage(
                                local_path=str(filepath),
                                original_url=url,
                                portal=portal,
                                listing_id=listing_id,
                                size_bytes=len(data),
                            ))
            except Exception as e:
                logger.debug("Errore download %s: %s", url[:60], e)

            # Rate limit
            time.sleep(0.5)

        return downloaded

    def download_for_opportunities(
        self,
        opportunities: list,
        max_images_per_opp: int = 3,
    ) -> Dict[str, List[DownloadedImage]]:
        """
        Scarica immagini per una lista di Opportunity dalla pipeline.

        Returns: {listing_id: [DownloadedImage, ...]}
        """
        result = {}
        for opp in opportunities:
            lid = getattr(opp, 'listing_id', '')
            portal = getattr(opp, 'portal', '')
            urls = getattr(opp, 'image_urls', []) or []

            if not urls:
                # Prova a estrarre dalla detail page se non abbiamo URL
                detail_url = getattr(opp, 'listing_url', '')
                if detail_url:
                    urls = self._extract_images_from_detail(detail_url, portal)

            if urls:
                self._max_per_listing = max_images_per_opp
                images = self.download_for_listing(lid, portal, urls)
                if images:
                    result[lid] = images
                    logger.info("Scaricate %d immagini per %s (%s)", len(images), lid, portal)

            time.sleep(1)  # Rate limit tra listing

        return result

    def _fetch_image(self, url: str, portal: str, referer: str = "") -> Optional[bytes]:
        """Scarica bytes immagine con headers appropriati."""
        if not referer:
            parsed = urlparse(url)
            referer = f"https://{parsed.netloc}/"

        headers = {
            "Referer": referer,
            "Accept": "image/webp,image/avif,image/jxl,image/heic,image/heic-sequence,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }

        # Primary: curl_cffi raw bytes (ResilientFetcher.fetch returns str, mangles binary)
        try:
            from curl_cffi import requests as _creq
            r = _creq.get(url, impersonate="chrome120", headers=headers, timeout=15)
            if r.status_code == 200 and r.content and len(r.content) > 1000:
                return r.content
        except Exception as e:
            logger.debug("curl_cffi image fetch failed: %s", e)

        # Fallback: urllib
        try:
            from urllib.request import Request, urlopen
            req = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                "Referer": referer,
                "Accept": "image/webp,image/*,*/*",
            })
            with urlopen(req, timeout=15) as resp:
                return resp.read()
        except Exception as e:
            logger.debug("urllib fallback failed: %s", e)

        return None

    def _extract_images_from_detail(self, detail_url: str, portal: str) -> List[str]:
        """Estrae URL immagini dalla pagina dettaglio del listing."""
        try:
            fetcher = self._get_fetcher()
            html = fetcher.fetch(detail_url)
            if not html or not isinstance(html, str):
                return []

            images = []

            # JSON-LD images
            for m in re.finditer(r'"image"\s*:\s*"(https?://[^"]+)"', html):
                images.append(m.group(1))
            for m in re.finditer(r'"image"\s*:\s*\[(.*?)\]', html, re.DOTALL):
                for url_m in re.finditer(r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', m.group(1)):
                    images.append(url_m.group(1))

            # og:image
            m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
            if m:
                images.append(m.group(1))

            # Generic large image URLs
            for m in re.finditer(r'(https?://[^"\'>\s]+\.(?:jpg|jpeg|png|webp))', html):
                url = m.group(1)
                if any(s in url for s in ['large', 'full', 'original', '1080', '1280', '1600', '2048', '2560']):
                    images.append(url)

            # Deduplicate preserving order
            seen = set()
            unique = []
            for img in images:
                if img not in seen:
                    seen.add(img)
                    unique.append(img)

            return unique[:6]

        except Exception as e:
            logger.debug("Detail image extraction failed: %s", e)
            return []


def _guess_extension(url: str) -> str:
    """Indovina estensione file dall'URL."""
    url_lower = url.lower().split("?")[0]
    if ".webp" in url_lower:
        return ".webp"
    if ".png" in url_lower:
        return ".png"
    if ".jpeg" in url_lower or ".jpg" in url_lower:
        return ".jpg"
    return ".jpg"


def apply_watermark(
    image_path: str,
    output_path: str = "",
    text: str = "ARGOS AUTOMOTIVE",
    opacity: float = 0.35,
) -> str:
    """
    Applica watermark ARGOS su un'immagine.

    Args:
        image_path: Path immagine sorgente
        output_path: Path output (default: sovrascrive sorgente)
        text: Testo watermark
        opacity: Opacita' (0.0 trasparente - 1.0 opaco)

    Returns: Path immagine con watermark
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.debug("Pillow non installato, skip watermark")
        return image_path

    if not output_path:
        output_path = image_path

    try:
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size

        # Crea overlay trasparente
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Font size proporzionale all'immagine
        font_size = max(20, min(w, h) // 18)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        # Calcola dimensioni testo
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Watermark diagonale al centro
        txt_img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        # Testo bianco con bordo scuro per leggibilita'
        txt_draw.text((12, 12), text, font=font, fill=(0, 0, 0, int(255 * opacity * 0.5)))
        txt_draw.text((10, 10), text, font=font, fill=(255, 255, 255, int(255 * opacity)))

        # Ruota -30 gradi
        txt_img = txt_img.rotate(30, expand=True, resample=Image.BICUBIC)

        # Centra sull'immagine
        paste_x = (w - txt_img.width) // 2
        paste_y = (h - txt_img.height) // 2
        overlay.paste(txt_img, (paste_x, paste_y))

        # Composita
        result = Image.alpha_composite(img, overlay)

        # Salva come JPEG (compatibile con reportlab)
        if output_path.lower().endswith(".webp"):
            output_path = output_path.rsplit(".", 1)[0] + ".jpg"
        result = result.convert("RGB")
        result.save(output_path, "JPEG", quality=90)

        logger.debug("Watermark applicato: %s", output_path)
        return output_path

    except Exception as e:
        logger.debug("Errore watermark: %s", e)
        return image_path
