"""
resilient_fetcher.py -- ARGOS Anti-Bot Resilient HTTP Fetcher
CoVe 2026 | Enterprise Grade

Multi-strategy HTTP fetcher che bypassa TUTTE le protezioni anti-bot:
  1. curl_cffi con impersonate Chrome (default, piu' veloce)
  2. cloudscraper (bypass Cloudflare Challenge)
  3. undetected-chromedriver (browser reale headless — bypass WAF aggressivi)
  4. Standard requests con headers evoluti (fallback)

PERSISTENTE: ogni backend viene tentato in sequenza. Quando uno funziona,
viene memorizzato per quel dominio e usato come primo tentativo nelle
richieste successive. Il cache e' persistente tra le esecuzioni.

Il parsing NON dipende da CSS selectors (che cambiano spesso).
Usa SOLO dati strutturati stabili nel tempo.

Author: ARGOS Automotive CTO Stack
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("argos.resilient_fetcher")

# ---------------------------------------------------------------------------
# Persistent domain -> backend cache
# ---------------------------------------------------------------------------
_CACHE_FILE = Path(__file__).parent / ".backend_cache.json"


def _load_backend_cache() -> Dict[str, str]:
    """Load persistent domain -> backend mapping."""
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_backend_cache(cache: Dict[str, str]) -> None:
    """Save persistent domain -> backend mapping."""
    try:
        _CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except OSError:
        pass


# ---------------------------------------------------------------------------
# HTTP Backends
# ---------------------------------------------------------------------------
_backends: Dict[str, Any] = {}

try:
    from curl_cffi import requests as curl_requests
    _backends["curl_cffi"] = curl_requests
except ImportError:
    curl_requests = None

try:
    import cloudscraper
    _backends["cloudscraper"] = cloudscraper
except ImportError:
    cloudscraper = None

# Selenium: browser reale per WAF aggressivi
_selenium_available = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    _selenium_available = True
    _backends["selenium_chrome"] = webdriver
except ImportError:
    webdriver = None

# undetected-chromedriver: alternativa anti-detection
_uc_available = False
try:
    import undetected_chromedriver as uc
    _uc_available = True
    _backends["undetected_chrome"] = uc
except ImportError:
    uc = None

try:
    import requests as std_requests
    _backends["requests"] = std_requests
except ImportError:
    std_requests = None


# ---------------------------------------------------------------------------
# User-Agent pool (aggiornati 2026)
# ---------------------------------------------------------------------------
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]

# Per-domain: quale backend funziona meglio
_domain_backend_cache: Dict[str, str] = {}


def _extract_domain(url: str) -> str:
    """Estrae dominio dall'URL."""
    from urllib.parse import urlparse
    return urlparse(url).netloc


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


class ResilientFetcher:
    """
    Fetcher multi-backend con auto-detection del backend migliore per dominio.

    Ordine di tentativo:
      1. Backend preferito per il dominio (se noto — PERSISTENTE su disco)
      2. curl_cffi con impersonate Chrome
      3. cloudscraper (bypass Cloudflare Challenge)
      4. undetected-chromedriver (browser Chrome reale headless)
      5. Standard requests (fallback)

    Gestisce:
      - Cloudflare Challenge (JS challenge, turnstile)
      - WAF aggressivi (DoneDeal.ie, Hasznaltauto.hu, etc.)
      - Rate limiting con backoff esponenziale
      - Rotazione User-Agent
      - Cache persistente del backend migliore per dominio
    """

    IMPERSONATE = "chrome120"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_base: float = 30.0,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._cloudscraper_session = None
        self._uc_driver = None
        self._domain_cache = _load_backend_cache()

    def _get_cloudscraper_session(self):
        """Lazy-init cloudscraper session (reusabile)."""
        if self._cloudscraper_session is None and cloudscraper is not None:
            self._cloudscraper_session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True,
                }
            )
        return self._cloudscraper_session

    def _make_headers(self, accept_language: str = "en-US,en;q=0.9") -> Dict[str, str]:
        return {
            "User-Agent": _random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": accept_language,
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

    def _get_selenium_driver(self):
        """
        Lazy-init Selenium Chrome con stealth e cookie persistence.

        Usa user-data-dir persistente per mantenere cookie e sessioni
        tra esecuzioni (risolve challenge Cloudflare una volta sola).
        """
        if self._uc_driver is None and _selenium_available:
            try:
                # Directory persistente per profilo Chrome
                profile_dir = Path(__file__).parent / ".chrome_profile"
                profile_dir.mkdir(exist_ok=True)

                options = ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument(f"--user-data-dir={profile_dir}")
                options.add_argument(f"--user-agent={_random_ua()}")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

                # Try system chromedriver
                chromedriver_path = "/usr/local/bin/chromedriver"
                if os.path.exists(chromedriver_path):
                    service = ChromeService(chromedriver_path)
                else:
                    service = ChromeService()

                driver = webdriver.Chrome(service=service, options=options)

                # Stealth: remove automation indicators
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.chrome = { runtime: {} };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en', 'it']
                        });
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) =>
                            parameters.name === 'notifications'
                                ? Promise.resolve({state: Notification.permission})
                                : originalQuery(parameters);
                    """
                })

                self._uc_driver = driver
                logger.info("[resilient] Selenium Chrome inizializzato con profilo persistente")
            except Exception as exc:
                logger.warning("[resilient] Selenium Chrome init fallito: %s", exc)
                self._uc_driver = None
        return self._uc_driver

    def close(self):
        """Chiudi browser e salva cache."""
        if self._uc_driver is not None:
            try:
                self._uc_driver.quit()
            except Exception:
                pass
            self._uc_driver = None
        _save_backend_cache(self._domain_cache)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def fetch(
        self,
        url: str,
        accept_language: str = "en-US,en;q=0.9",
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Fetch URL con multi-backend fallback PERSISTENTE.

        Ordine:
          1. Backend preferito per dominio (dalla cache su disco)
          2. curl_cffi (veloce, anti-bot base)
          3. cloudscraper (bypass Cloudflare)
          4. undetected-chromedriver (browser reale per WAF aggressivi)
          5. Standard requests (fallback)

        Returns HTML string. Raises RuntimeError se tutti i backend falliscono.
        """
        domain = _extract_domain(url)
        headers = self._make_headers(accept_language)
        if extra_headers:
            headers.update(extra_headers)

        # Determine backend order — preferito dal cache persistente
        preferred = self._domain_cache.get(domain)
        backends_order = []
        if preferred:
            backends_order.append(preferred)

        # Standard order: fast -> medium -> slow (browser)
        for name in ["curl_cffi", "cloudscraper", "selenium_chrome", "requests"]:
            if name not in backends_order:
                if name == "selenium_chrome" and not _selenium_available:
                    continue
                if name in _backends:
                    backends_order.append(name)

        last_error = None
        for backend_name in backends_order:
            # Only 1 attempt for fast backends, 2 for browser
            max_attempts = 2 if backend_name == "selenium_chrome" else 1
            for attempt in range(max_attempts):
                try:
                    html, status = self._fetch_with_backend(
                        backend_name, url, headers, attempt
                    )

                    if status == 200 and html and len(html) > 500:
                        # Success — save to persistent cache
                        self._domain_cache[domain] = backend_name
                        _save_backend_cache(self._domain_cache)
                        logger.info(
                            "[resilient] %s OK via %s (%d bytes)",
                            domain, backend_name, len(html)
                        )
                        return html

                    if status in (403, 429):
                        logger.info(
                            "[resilient] %s HTTP %d via %s — trying next backend",
                            domain, status, backend_name,
                        )
                        break  # Don't retry same backend on 403, try next

                    if status == 404:
                        return ""

                    if status >= 500:
                        wait = 5 + random.uniform(0, 5)
                        time.sleep(wait)
                        continue

                    break  # Other status — try next backend

                except Exception as exc:
                    last_error = exc
                    logger.debug(
                        "[resilient] %s failed via %s: %s",
                        domain, backend_name, exc,
                    )
                    break  # Try next backend

            logger.info(
                "[resilient] %s: backend %s esaurito, provo successivo",
                domain, backend_name,
            )

        raise RuntimeError(
            f"Tutti i backend falliti per {url}. Ultimo errore: {last_error}"
        )

    def _fetch_with_backend(
        self, backend_name: str, url: str, headers: Dict[str, str], attempt: int
    ) -> tuple:
        """Fetch con un backend specifico. Returns (html, status_code)."""

        if backend_name == "curl_cffi" and curl_requests is not None:
            resp = curl_requests.get(
                url,
                headers=headers,
                impersonate=self.IMPERSONATE,
                timeout=self.timeout,
                allow_redirects=True,
            )
            return resp.text, resp.status_code

        elif backend_name == "cloudscraper":
            session = self._get_cloudscraper_session()
            if session is None:
                raise RuntimeError("cloudscraper non disponibile")
            resp = session.get(
                url,
                headers={k: v for k, v in headers.items()
                         if k.lower() not in ('user-agent',)},  # cloudscraper gestisce UA
                timeout=self.timeout,
                allow_redirects=True,
            )
            return resp.text, resp.status_code

        elif backend_name == "selenium_chrome":
            driver = self._get_selenium_driver()
            if driver is None:
                raise RuntimeError("Selenium Chrome non disponibile")
            try:
                # Load saved cookies for this domain
                domain = _extract_domain(url)
                self._load_cookies(driver, domain)

                driver.get(url)
                # Attendi rendering JS (WAF challenge resolution)
                time.sleep(4 + random.uniform(1, 3))
                html = driver.page_source

                if html and len(html) > 500:
                    # Check for challenge pages
                    challenge_markers = [
                        "challenge-running", "cf-browser-verification",
                        "Just a moment", "checking your browser",
                        "Verify you are human", "Ci siamo quasi",
                        "Attention Required", "Cloudflare",
                    ]
                    is_challenge = any(m in html for m in challenge_markers)

                    if is_challenge:
                        # Progressive wait: 5s -> 10s -> 20s
                        for wait in [5, 10, 20]:
                            logger.info(
                                "[resilient] Challenge detected for %s, waiting %ds...",
                                domain, wait,
                            )
                            time.sleep(wait)
                            html = driver.page_source
                            is_challenge = any(m in html for m in challenge_markers)
                            if not is_challenge:
                                break

                    if not is_challenge and len(html) > 1000:
                        # Save cookies for future use
                        self._save_cookies(driver, domain)
                        return html, 200

                    # Still on challenge page
                    logger.warning(
                        "[resilient] %s: challenge non risolta dopo 35s",
                        domain,
                    )
                    return html or "", 403

                return html or "", 403

            except Exception as exc:
                logger.warning("[resilient] Selenium error: %s", exc)
                try:
                    self._uc_driver.quit()
                except Exception:
                    pass
                self._uc_driver = None
                raise

        elif backend_name == "requests" and std_requests is not None:
            resp = std_requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            return resp.text, resp.status_code

        raise RuntimeError(f"Backend {backend_name} non disponibile")

    # ----- Cookie Persistence -----

    def _cookies_path(self, domain: str) -> Path:
        """Path per cookie salvati di un dominio."""
        safe_name = domain.replace(".", "_").replace(":", "_")
        return Path(__file__).parent / ".cookies" / f"{safe_name}.json"

    def _save_cookies(self, driver, domain: str) -> None:
        """Salva cookies del browser per riuso futuro."""
        try:
            cookies_dir = Path(__file__).parent / ".cookies"
            cookies_dir.mkdir(exist_ok=True)
            cookies = driver.get_cookies()
            self._cookies_path(domain).write_text(json.dumps(cookies, indent=2))
            logger.info("[resilient] Salvati %d cookies per %s", len(cookies), domain)
        except Exception as exc:
            logger.debug("[resilient] Errore salvataggio cookies: %s", exc)

    def _load_cookies(self, driver, domain: str) -> None:
        """Carica cookies salvati nel browser."""
        path = self._cookies_path(domain)
        if not path.exists():
            return
        try:
            cookies = json.loads(path.read_text())
            # Navigate to domain first (required for cookie injection)
            try:
                current_domain = _extract_domain(driver.current_url)
                if domain not in current_domain:
                    driver.get(f"https://{domain}")
                    time.sleep(1)
            except Exception:
                pass
            for cookie in cookies:
                # Remove problematic fields
                for field in ("sameSite", "expiry", "httpOnly", "storeId"):
                    cookie.pop(field, None)
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
            logger.info("[resilient] Caricati %d cookies per %s", len(cookies), domain)
        except Exception as exc:
            logger.debug("[resilient] Errore caricamento cookies: %s", exc)

    def test_connection(self, url: str) -> Dict[str, Any]:
        """Test di connettivita' con tutti i backend disponibili."""
        domain = _extract_domain(url)
        results = {}

        for backend_name in _backends:
            try:
                headers = self._make_headers()
                html, status = self._fetch_with_backend(
                    backend_name, url, headers, 0
                )
                results[backend_name] = {
                    "status": status,
                    "bytes": len(html) if html else 0,
                    "ok": status == 200 and len(html) > 500,
                }
            except Exception as exc:
                results[backend_name] = {
                    "status": 0,
                    "bytes": 0,
                    "ok": False,
                    "error": str(exc),
                }

        return results
