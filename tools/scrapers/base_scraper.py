"""
base_scraper.py -- ARGOS Market Intelligence Base Scraper
CoVe 2026 | Enterprise Grade

Classe base astratta con anti-bot (curl_cffi), retry, rate limiting.
I portali concreti estendono questa classe.
"""

from __future__ import annotations
import abc
import hashlib
import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    PortalConfig, YEAR_MIN, YEAR_MAX,
    km_limit_for, TARGET_VEHICLES, get_portal,
)
from .models import Listing, ScraperRun, RunStatus, PriceChange
from .db import upsert_listing, mark_inactive, start_run, finish_run

# ---------------------------------------------------------------------------
# HTTP backend: curl_cffi preferito, requests come fallback
# ---------------------------------------------------------------------------
_HTTP_BACKEND: str = "none"

try:
    from curl_cffi import requests as curl_requests  # type: ignore[import-untyped]
    _HTTP_BACKEND = "curl_cffi"
except ImportError:
    curl_requests = None  # type: ignore[assignment]

try:
    import requests as std_requests  # type: ignore[import-untyped]
    if _HTTP_BACKEND == "none":
        _HTTP_BACKEND = "requests"
except ImportError:
    std_requests = None  # type: ignore[assignment]

if _HTTP_BACKEND == "none":
    raise ImportError(
        "Nessun HTTP backend disponibile. Installa curl_cffi (consigliato) o requests: "
        "pip install curl_cffi"
    )

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("argos.scraper")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# User-Agent rotation
# ---------------------------------------------------------------------------
_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


# ---------------------------------------------------------------------------
# Base Scraper (Abstract)
# ---------------------------------------------------------------------------
class BaseScraper(abc.ABC):
    """
    Classe base per scraper portali auto europei.

    Sottoclassi devono implementare:
      - build_search_url(make, model, params) -> str
      - parse_search_results(html) -> list[Listing]
    """

    IMPERSONATE_BROWSER = "chrome120"

    def __init__(
        self,
        portal_key: str,
        *,
        max_retries: int = 3,
        backoff_base_s: float = 30.0,
        request_timeout_s: int = 30,
    ) -> None:
        self.portal_key: str = portal_key
        self.config: PortalConfig = get_portal(portal_key)
        self.max_retries: int = max_retries
        self.backoff_base: float = backoff_base_s
        self.timeout: int = request_timeout_s
        self._request_count: int = 0
        self._session_start: float = time.monotonic()
        self._daily_count: int = 0
        self._last_request_ts: float = 0.0

    # -- Abstract methods --------------------------------------------------

    @abc.abstractmethod
    def build_search_url(
        self,
        make: str,
        model: str,
        params: Dict[str, Any],
    ) -> str:
        """
        Costruisci l'URL di ricerca per il portale.

        params contiene almeno: page, year_min, year_max, km_max.
        """
        ...

    @abc.abstractmethod
    def parse_search_results(self, html: str) -> List[Listing]:
        """
        Parsa l'HTML della pagina risultati e ritorna i listing trovati.

        Ogni Listing deve avere almeno: listing_id, portal, make, model,
        price_eur, year, km, listing_url.
        """
        ...

    def get_total_pages(self, html: str) -> Optional[int]:
        """
        Estrai il numero totale di pagine dalla prima pagina risultati.
        Ritorna None se non determinabile (default: usa max_pages dalla config).
        Sottoclassi possono sovrascrivere.
        """
        return None

    # -- HTTP layer --------------------------------------------------------

    def _fetch(self, url: str, retry: int = 0) -> str:
        """
        Fetch URL con anti-bot, retry esponenziale, rate limiting.
        Ritorna l'HTML della pagina.
        Raises RuntimeError dopo max_retries tentativi falliti.
        """
        headers = {
            "User-Agent": _random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        headers.update(self.config.headers)

        try:
            self._rate_limit_sleep()

            if _HTTP_BACKEND == "curl_cffi" and curl_requests is not None:
                resp = curl_requests.get(
                    url,
                    headers=headers,
                    impersonate=self.IMPERSONATE_BROWSER,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            elif std_requests is not None:
                resp = std_requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            else:
                raise RuntimeError("No HTTP backend available")

            self._request_count += 1
            self._daily_count += 1
            self._last_request_ts = time.time()

            # Retry su rate limit / forbidden / server error
            if resp.status_code in (403, 429):
                wait = self.backoff_base * (2 ** retry) + random.uniform(5, 15)
                logger.warning(
                    "[%s] HTTP %d on attempt %d/%d -- backoff %.0fs -- %s",
                    self.portal_key, resp.status_code, retry + 1,
                    self.max_retries, wait, url,
                )
                if retry < self.max_retries:
                    time.sleep(wait)
                    return self._fetch(url, retry=retry + 1)
                raise RuntimeError(
                    f"HTTP {resp.status_code} persistente dopo {self.max_retries} tentativi: {url}"
                )

            if resp.status_code == 404:
                logger.info("[%s] 404 -- skip: %s", self.portal_key, url)
                return ""

            if resp.status_code >= 500:
                wait = self.backoff_base * (2 ** retry) + random.uniform(0, 5)
                logger.warning(
                    "[%s] HTTP %d server error attempt %d/%d -- retry in %.0fs",
                    self.portal_key, resp.status_code, retry + 1,
                    self.max_retries, wait,
                )
                if retry < self.max_retries:
                    time.sleep(wait)
                    return self._fetch(url, retry=retry + 1)
                raise RuntimeError(
                    f"HTTP {resp.status_code} persistente dopo {self.max_retries} tentativi: {url}"
                )

            if resp.status_code != 200:
                logger.warning(
                    "[%s] HTTP %d per %s", self.portal_key, resp.status_code, url
                )
                return ""

            return resp.text  # type: ignore[no-any-return]

        except (ConnectionError, TimeoutError, OSError) as exc:
            wait = self.backoff_base * (2 ** retry) + random.uniform(5, 15)
            logger.warning(
                "[%s] Errore connessione: %s. Attendo %.0fs (retry %d/%d)",
                self.portal_key, exc, wait, retry + 1, self.max_retries,
            )
            if retry < self.max_retries:
                time.sleep(wait)
                return self._fetch(url, retry=retry + 1)
            raise RuntimeError(
                f"Connessione fallita dopo {self.max_retries} tentativi per {url}: {exc}"
            ) from exc

    def _rate_limit_sleep(self) -> None:
        """Sleep randomico tra richieste + pausa burst."""
        if self._request_count == 0:
            return

        if self._request_count % self.config.burst_size == 0:
            pause = self.config.rate_limit_burst_pause_s + random.uniform(0, 10)
            logger.info(
                "[%s] Burst pause dopo %d richieste: %.0fs",
                self.portal_key, self._request_count, pause,
            )
            time.sleep(pause)
        else:
            delay = random.uniform(
                self.config.rate_limit_min_s,
                self.config.rate_limit_max_s,
            )
            time.sleep(delay)

    def _check_daily_cap(self) -> bool:
        """True se il cap giornaliero non e' stato raggiunto."""
        if self._daily_count >= self.config.daily_request_cap:
            logger.warning(
                "[%s] Cap giornaliero raggiunto (%d/%d). Stop.",
                self.portal_key, self._daily_count, self.config.daily_request_cap,
            )
            return False
        return True

    # -- Scraping make/model -----------------------------------------------

    def scrape_model(
        self,
        make: str,
        model: str,
        year_min: int = YEAR_MIN,
        year_max: int = YEAR_MAX,
        km_max: Optional[int] = None,
    ) -> List[Listing]:
        """
        Scrape tutte le pagine di risultati per un make/model.
        Gestisce paginazione, rate limiting, error handling.
        """
        if km_max is None:
            km_max = km_limit_for(make, model)

        params: Dict[str, Any] = {
            "year_min": year_min,
            "year_max": year_max,
            "km_max": km_max,
            "page": 1,
        }

        all_listings: List[Listing] = []
        seen_ids: set[str] = set()
        max_pages = self.config.max_pages
        pages_scraped = 0

        logger.info(
            "[%s] Scraping %s %s (anno %d-%d, km max %d)",
            self.portal_key, make, model, year_min, year_max, km_max,
        )

        for page_num in range(1, max_pages + 1):
            if not self._check_daily_cap():
                break

            params["page"] = page_num
            url = self.build_search_url(make, model, params)

            try:
                html = self._fetch(url)
            except RuntimeError as exc:
                logger.error(
                    "[%s] Errore fetch pagina %d per %s %s: %s",
                    self.portal_key, page_num, make, model, exc,
                )
                break

            if not html:
                logger.info(
                    "[%s] Pagina %d vuota per %s %s, stop paginazione.",
                    self.portal_key, page_num, make, model,
                )
                break

            if page_num == 1:
                total_pages = self.get_total_pages(html)
                if total_pages is not None and total_pages < max_pages:
                    max_pages = total_pages
                    logger.info(
                        "[%s] Pagine totali rilevate: %d", self.portal_key, max_pages
                    )

            try:
                page_listings = self.parse_search_results(html)
            except Exception as exc:
                logger.error(
                    "[%s] Errore parsing pagina %d per %s %s: %s",
                    self.portal_key, page_num, make, model, exc,
                )
                break

            pages_scraped += 1

            if not page_listings:
                logger.info(
                    "[%s] Nessun listing in pagina %d per %s %s, stop.",
                    self.portal_key, page_num, make, model,
                )
                break

            for lst in page_listings:
                lst.portal = self.portal_key
                lst.country = self.config.countries[0] if self.config.countries else ""
                lst.make = make
                lst.model = model
                if lst.listing_id not in seen_ids:
                    seen_ids.add(lst.listing_id)
                    all_listings.append(lst)

            logger.info(
                "[%s] Pagina %d/%d: %d listing (%d totali unici)",
                self.portal_key, page_num, max_pages,
                len(page_listings), len(all_listings),
            )

            if len(page_listings) < self.config.results_per_page:
                break

        logger.info(
            "[%s] Completato %s %s: %d listing in %d pagine",
            self.portal_key, make, model, len(all_listings), pages_scraped,
        )
        return all_listings

    # -- Full run ----------------------------------------------------------

    def run_full_scrape(
        self,
        makes: Optional[Dict[str, List[str]]] = None,
    ) -> ScraperRun:
        """
        Esegui scraping completo per tutti i veicoli target (o un subset).
        Registra il run nel DB, fa upsert dei listing, rileva price changes.
        """
        if makes is None:
            makes = TARGET_VEHICLES

        country = self.config.countries[0] if self.config.countries else ""
        run_id = start_run(self.portal_key, country)

        run = ScraperRun(
            run_id=run_id,
            portal=self.portal_key,
            country=country,
            started_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        all_active_ids: List[str] = []

        for make, models in makes.items():
            for model_name in models:
                if not self._check_daily_cap():
                    run.errors.append("Daily cap raggiunto")
                    break

                try:
                    listings = self.scrape_model(make, model_name)
                    run.listings_found += len(listings)

                    for lst in listings:
                        status, price_change = upsert_listing(lst)
                        all_active_ids.append(lst.listing_id)

                        if status == "new":
                            run.listings_new += 1
                        elif status == "updated":
                            run.listings_updated += 1
                        if price_change is not None:
                            run.price_changes += 1

                except Exception as exc:
                    err_msg = f"{make} {model_name}: {exc}"
                    logger.error("[%s] Errore scraping: %s", self.portal_key, err_msg)
                    run.errors.append(err_msg)

        if all_active_ids:
            deactivated = mark_inactive(self.portal_key, all_active_ids)
            logger.info(
                "[%s] %d listing segnati inattivi", self.portal_key, deactivated
            )

        run.finished_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        run.status = RunStatus.COMPLETED if not run.errors else RunStatus.PARTIAL
        run.pages_scraped = self._request_count

        finish_run(run)

        logger.info(
            "[%s] Run #%d completato: %d trovati, %d nuovi, %d aggiornati, "
            "%d cambi prezzo, %d errori",
            self.portal_key, run.run_id, run.listings_found,
            run.listings_new, run.listings_updated,
            run.price_changes, len(run.errors),
        )

        return run

    # -- Utility -----------------------------------------------------------

    @staticmethod
    def generate_listing_id(portal: str, url: str) -> str:
        """Genera un listing_id deterministico da portale + URL."""
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
        return f"{portal}_{digest}"

    def test_connection(self) -> bool:
        """Test connettivita al portale. Ritorna True se raggiungibile."""
        try:
            html = self._fetch(self.config.base_url)
            ok = len(html) > 1000
            logger.info(
                "[%s] Test connessione: %s (%d bytes)",
                self.portal_key, "OK" if ok else "FAIL", len(html),
            )
            return ok
        except Exception as exc:
            logger.error("[%s] Test connessione fallito: %s", self.portal_key, exc)
            return False

    def reset_counters(self) -> None:
        """Reset contatori per nuovo ciclo."""
        self._request_count = 0
        self._daily_count = 0
        self._session_start = time.monotonic()

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def stats(self) -> Dict[str, Any]:
        """Statistiche correnti della sessione."""
        elapsed = time.monotonic() - self._session_start
        return {
            "portal": self.portal_key,
            "requests": self._request_count,
            "daily_count": self._daily_count,
            "daily_cap": self.config.daily_request_cap,
            "elapsed_seconds": round(elapsed, 1),
            "backend": _HTTP_BACKEND,
        }
