"""
COMBARETROVAMIAUTO — Real-Time Price Validator v2.0
Production-grade: scraping AutoScout24 reale, non simulazione

ARCHITETTURA:
- Usa la tua infrastruttura Camoufox/curl_cffi esistente
- Integra con dealer_network.duckdb (vehicle_data_locked table)
- Compatibile con n8n via HTTP call a FastAPI wrapper

Author: COMBARETROVAMIAUTO CTO Stack
"""

import time
import hashlib
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

# ── usa l'infrastruttura esistente nel tuo stack ──
try:
    from curl_cffi import requests as cf_requests  # 0.14.0+
    CURL_AVAILABLE = True
except ImportError:
    import requests as cf_requests
    CURL_AVAILABLE = False

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    ACTIVE     = "ACTIVE"       # Veicolo disponibile, prezzo stabile
    SOLD       = "SOLD"         # Veicolo venduto
    REPRICED   = "REPRICED"     # Prezzo cambiato
    UNAVAILABLE= "UNAVAILABLE"  # Listing non raggiungibile
    ERROR      = "ERROR"        # Errore tecnico


@dataclass
class ValidationResult:
    is_valid:             bool
    status:               ValidationStatus
    current_price:        Optional[int]
    original_price:       int
    price_change_pct:     Optional[float]
    km_current:           Optional[int]
    listing_url:          str
    checked_at:           datetime = field(default_factory=datetime.now)
    error_message:        Optional[str] = None
    should_proceed_msg3:  bool = False

    def __post_init__(self):
        self.should_proceed_msg3 = (
            self.is_valid and
            self.status in (ValidationStatus.ACTIVE, ValidationStatus.REPRICED) and
            (self.price_change_pct is None or abs(self.price_change_pct) <= 5.0)
        )


class AutoScoutValidator:
    """
    Validatore reale contro AutoScout24.
    Usa curl_cffi con browser impersonation per evitare Cloudflare.
    
    NOTA: per Mobile.de usa Carapis API (€45/mese) già nel tuo stack.
    """

    BASE_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
    }

    def __init__(
        self,
        db_path: str = "/Users/macbook/Documents/combaretrovamiauto/python/cove/data/cove_tracker.duckdb",
        cache_ttl_minutes: int = 30,
        max_price_change_pct: float = 5.0,
        semaphore_limit: int = 3,   # allineato con Semaphore(5) del tuo stack
        sleep_between_requests: int = 15,  # allineato con sleep(15) del tuo stack
    ):
        self.db_path = db_path
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.max_price_change_pct = max_price_change_pct
        self.sleep_between = sleep_between_requests
        self._cache: Dict[str, ValidationResult] = {}

    # ────────────────────────────────────────────
    # METODO PRINCIPALE — chiamare prima di MSG3
    # ────────────────────────────────────────────
    def validate_before_pitch(
        self,
        listing_id: str,
        listing_url: str,
        original_price: int,
        original_km: int,
        dealer_id: Optional[str] = None,
    ) -> ValidationResult:
        """
        CALL THIS before every MSG3.
        Returns ValidationResult.should_proceed_msg3 as go/no-go.
        """

        # 1. Check cache
        cache_key = f"{listing_id}_{original_price}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached.checked_at < self.cache_ttl:
                logger.info(f"Cache hit: {listing_id}")
                return cached

        # 2. Fetch listing
        try:
            result = self._fetch_and_parse(
                listing_url, original_price, original_km
            )
        except Exception as e:
            logger.error(f"Validation error for {listing_id}: {e}")
            result = ValidationResult(
                is_valid=False,
                status=ValidationStatus.ERROR,
                current_price=None,
                original_price=original_price,
                price_change_pct=None,
                km_current=None,
                listing_url=listing_url,
                error_message=str(e),
            )

        # 3. Cache result
        self._cache[cache_key] = result

        # 4. Persist to DuckDB
        if DUCKDB_AVAILABLE and dealer_id:
            self._persist_validation(listing_id, dealer_id, result)

        # 5. Rate limiting — rispetta i limiti del tuo stack
        time.sleep(self.sleep_between)

        return result

    # ────────────────────────────────────────────
    # SCRAPING AutoScout24
    # ────────────────────────────────────────────
    def _fetch_and_parse(
        self,
        url: str,
        original_price: int,
        original_km: int,
    ) -> ValidationResult:
        """
        Fetch AutoScout24 listing e parsa prezzo + km.
        Usa curl_cffi con browser impersonation Chrome 120.
        """

        if CURL_AVAILABLE:
            resp = cf_requests.get(
                url,
                headers=self.BASE_HEADERS,
                impersonate="chrome120",
                timeout=20,
            )
        else:
            resp = cf_requests.get(url, headers=self.BASE_HEADERS, timeout=20)

        if resp.status_code == 404:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.SOLD,
                current_price=None,
                original_price=original_price,
                price_change_pct=None,
                km_current=None,
                listing_url=url,
            )

        if resp.status_code != 200:
            raise ConnectionError(f"HTTP {resp.status_code} on {url}")

        html = resp.text

        # ── Parse prezzo ──
        # AutoScout24 DE: cerca pattern "€ 27.800" o "27800"
        import re

        price_match = re.search(
            r'"price"[:\s]+["\']?(\d[\d.,]+)["\']?',
            html,
            re.IGNORECASE
        )
        if not price_match:
            # Fallback: cerca nel body
            price_match = re.search(
                r'(\d{2,3}[\.,]\d{3})\s*€',
                html
            )

        current_price = None
        if price_match:
            raw = price_match.group(1).replace('.', '').replace(',', '').replace(' ', '')
            try:
                current_price = int(raw)
            except ValueError:
                pass

        # ── Parse km ──
        km_match = re.search(
            r'"mileage"[:\s]+["\']?(\d[\d.,]+)["\']?',
            html,
            re.IGNORECASE
        )
        current_km = None
        if km_match:
            raw_km = km_match.group(1).replace('.', '').replace(',', '')
            try:
                current_km = int(raw_km)
            except ValueError:
                pass

        # ── Sold detection ──
        sold_indicators = [
            'sold', 'verkauft', 'nicht mehr verfügbar',
            'this listing is no longer', 'annuncio non disponibile'
        ]
        is_sold = any(ind in html.lower() for ind in sold_indicators)
        if is_sold:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.SOLD,
                current_price=None,
                original_price=original_price,
                price_change_pct=None,
                km_current=current_km,
                listing_url=url,
            )

        # ── Price change analysis ──
        if current_price is None:
            # Non riusciamo a parsare il prezzo = unavailable
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.UNAVAILABLE,
                current_price=None,
                original_price=original_price,
                price_change_pct=None,
                km_current=current_km,
                listing_url=url,
                error_message="Could not parse price from listing",
            )

        price_change_pct = ((current_price - original_price) / original_price) * 100

        if abs(price_change_pct) > 0.5:
            status = ValidationStatus.REPRICED
        else:
            status = ValidationStatus.ACTIVE

        is_valid = abs(price_change_pct) <= self.max_price_change_pct

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            current_price=current_price,
            original_price=original_price,
            price_change_pct=round(price_change_pct, 2),
            km_current=current_km,
            listing_url=url,
        )

    # ────────────────────────────────────────────
    # DUCKDB INTEGRATION
    # ────────────────────────────────────────────
    def _persist_validation(
        self,
        listing_id: str,
        dealer_id: str,
        result: ValidationResult,
    ):
        """Persiste il risultato di validazione in DuckDB."""
        if not DUCKDB_AVAILABLE:
            return

        try:
            con = duckdb.connect(self.db_path)

            # Upsert in vehicle_data_locked
            con.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_data_locked (
                    vehicle_id          VARCHAR PRIMARY KEY,
                    km_verified         INTEGER,
                    km_source           VARCHAR,
                    price_verified      INTEGER,
                    price_source        VARCHAR,
                    validation_status   VARCHAR,
                    locked_at           TIMESTAMP,
                    last_validated_at   TIMESTAMP,
                    modification_blocked BOOLEAN DEFAULT TRUE
                )
            """)

            if result.status == ValidationStatus.ACTIVE:
                con.execute("""
                    INSERT INTO vehicle_data_locked
                        (vehicle_id, km_verified, km_source, price_verified,
                         price_source, validation_status, locked_at, last_validated_at)
                    VALUES (?, ?, 'autoscout24_realtime', ?, 'autoscout24_realtime',
                            ?, ?, ?)
                    ON CONFLICT (vehicle_id) DO UPDATE SET
                        price_verified = excluded.price_verified,
                        validation_status = excluded.validation_status,
                        last_validated_at = excluded.last_validated_at
                """, [
                    listing_id,
                    result.km_current or 0,
                    result.current_price or 0,
                    result.status.value,
                    datetime.now(),
                    datetime.now(),
                ])

            # Log event
            con.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id    VARCHAR,
                    dealer_id   VARCHAR,
                    event_type  VARCHAR,
                    event_data  VARCHAR,
                    created_at  TIMESTAMP
                )
            """)
            con.execute("""
                INSERT INTO events VALUES (?, ?, 'PRICE_VALIDATION', ?, ?)
            """, [
                f"{listing_id}_{int(datetime.now().timestamp())}",
                dealer_id,
                str({
                    "status": result.status.value,
                    "price_change_pct": result.price_change_pct,
                    "should_proceed": result.should_proceed_msg3,
                }),
                datetime.now(),
            ])

            con.close()
            logger.info(f"Validation persisted: {listing_id} → {result.status.value}")

        except Exception as e:
            logger.warning(f"DuckDB persist failed: {e}")

    # ────────────────────────────────────────────
    # FALLBACK VEHICLE
    # ────────────────────────────────────────────
    def get_fallback_vehicle(
        self,
        make: str,
        model: str,
        year: int,
        max_price: int,
    ) -> Optional[Dict]:
        """
        Cerca veicolo alternativo in DuckDB se originale venduto.
        Query su vehicles table del tuo stack esistente.
        """
        if not DUCKDB_AVAILABLE:
            return None

        try:
            con = duckdb.connect(self.db_path)
            rows = con.execute("""
                SELECT listing_url, price_eur, km, argos_score
                FROM vehicles
                WHERE make = ?
                  AND model LIKE ?
                  AND year >= ?
                  AND price_eur <= ?
                  AND recommendation = 'CERTIFICATO'
                  AND listing_url NOT IN (
                      SELECT source_url FROM proposals WHERE status = 'PROPOSED'
                  )
                ORDER BY argos_score DESC
                LIMIT 1
            """, [make, f"%{model}%", year - 1, max_price + 2000]).fetchall()
            con.close()

            if rows:
                r = rows[0]
                return {
                    "listing_url": r[0],
                    "price_eur": r[1],
                    "km": r[2],
                    "argos_score": r[3],
                }
        except Exception as e:
            logger.warning(f"Fallback query failed: {e}")

        return None


# ────────────────────────────────────────────
# n8n INTEGRATION — FastAPI wrapper
# Esponi questo endpoint, chiamalo dal nodo HTTP Request in n8n
# ────────────────────────────────────────────
def create_api():
    """
    FastAPI micro-service per n8n integration.
    
    Avvio: uvicorn price_validator_v2:app --host 0.0.0.0 --port 8090
    n8n node: GET http://localhost:8090/validate?url=...&price=27800&km=45200
    """
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn

        app = FastAPI(title="ARGOS Price Validator", version="2.0")
        validator = AutoScoutValidator()

        @app.get("/validate")
        def validate(
            url: str,
            price: int,
            km: int,
            listing_id: str = "",
            dealer_id: str = "",
        ):
            if not listing_id:
                listing_id = hashlib.md5(url.encode()).hexdigest()[:12]

            result = validator.validate_before_pitch(
                listing_id=listing_id,
                listing_url=url,
                original_price=price,
                original_km=km,
                dealer_id=dealer_id or None,
            )

            return JSONResponse({
                "should_proceed_msg3": result.should_proceed_msg3,
                "status": result.status.value,
                "current_price": result.current_price,
                "price_change_pct": result.price_change_pct,
                "km_current": result.km_current,
                "checked_at": result.checked_at.isoformat(),
                "error": result.error_message,
            })

        @app.get("/health")
        def health():
            return {"status": "ok", "curl_available": CURL_AVAILABLE}

        return app

    except ImportError:
        logger.warning("FastAPI not installed. Run: pip install fastapi uvicorn")
        return None


app = create_api()


# ────────────────────────────────────────────
# TEST LOCALE
# ────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    validator = AutoScoutValidator()

    # Test con URL reale AutoScout (esempio BMW 330i type)
    TEST_URL = "https://www.autoscout24.de/angebote/bmw-3er-reihe-330i-touring-m-sport-benzin-weiss-f69dde39-6b5c-4b90-9850-f7b8c3a2e1b5"
    TEST_PRICE = 27800
    TEST_KM = 45200

    print("=== ARGOS Price Validator v2.0 ===")
    print(f"Testing: {TEST_URL}")
    print(f"Original: €{TEST_PRICE}, {TEST_KM}km\n")

    result = validator.validate_before_pitch(
        listing_id="bmw_330i_mario_001",
        listing_url=TEST_URL,
        original_price=TEST_PRICE,
        original_km=TEST_KM,
        dealer_id="mario_orefice",
    )

    print(f"Status:              {result.status.value}")
    print(f"Current price:       €{result.current_price}")
    print(f"Price change:        {result.price_change_pct}%")
    print(f"KM current:          {result.km_current}")
    print(f"Should proceed MSG3: {result.should_proceed_msg3}")
    if result.error_message:
        print(f"Error: {result.error_message}")
