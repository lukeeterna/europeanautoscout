#!/usr/bin/env python3
"""
second_brain.py — ARGOS dealer second brain, Day1 v5.

Fonti ammesse
==============
1. Record dei 44 CONTATTABILI in ``data/recon/mandatari/``. Il record viene
   risolto esclusivamente tramite la coppia ``idx + P.IVA`` e deve rispettare
   la definizione operativa ``solo-anagrafe AND telefono_presente``.
2. Dati camerali gia' presenti in ``data/registry/``, se disponibili.
3. Sito ufficiale del dealer, soltanto tramite richieste HTTP dirette:
   ``robots.txt`` viene letto prima di ogni pagina; 401/403/429, Cloudflare,
   pagine JavaScript-only, errori di rete e robots non determinabile producono
   ``n/d``. Non esistono retry aggressivi, proxy, browser stealth o bypass.
4. ``note_manuali: str`` compilato dal founder dopo lettura umana dei social.
   Questo file NON apre, interroga o scrapa Facebook, Instagram, Meta Ad
   Library, Subito, AutoScout24, PagineGialle o altri portali annunci/social.
5. CRM esistente ``tools/dealer_crm.py`` in sola lettura, se il record contiene
   un ``dealer_id`` gia' noto. Le chiavi CRM riusate restano compatibili con la
   tabella ``dealers`` esistente.

Moduli open source
==================
Il file funziona con la sola standard library. Se ``trafilatura``
(https://github.com/adbar/trafilatura) e' gia' installato, viene usato come
estrattore HTML; in caso contrario usa un parser conservativo interno. Nessun
modulo GitHub che aggira login, ToS, 403, Cloudflare o protezioni Meta viene
importato o eseguito.

Limiti noti
===========
- Nessuna ricerca web per scoprire il sito: l'URL deve gia' essere presente
  nelle fonti locali/CRM. Se manca, la raccolta web e' ``n/d``.
- Le inferenze sul registro comunicativo sono euristiche e vengono emesse solo
  con evidenza testuale citabile; altrimenti restano ``n/d``.
- La personalizzazione e' vietata se non esiste un aggancio specifico con
  fonte. In quel caso il Day1 e' deliberatamente generico.
- Il template v5 usa la CTA ratificata della verifica-targa gratuita. Il file
  pinato ``research/s94_MESSAGGI_DEFINITIVI_V3.md`` conserva il framework
  CHI-PERCHE'-CHIEDI ma non contiene il testo letterale v5; per questo la
  formulazione e' mantenuta minimale, verificabile e senza promesse inventate.
- Ogni artefatto viene scritto soltanto sotto
  ``data/recon/mandatari/`` (directory dichiarata gitignorata dal mandato).
- Un invio reale, se richiesto con ``--send``, usa SEMPRE e soltanto
  ``TEST_FOUNDER_NUM`` da ambiente, esegue il preflight della guardia
  ``.harness/gate_e.py`` e non accetta alcun destinatario da CLI o dai dati.

Segreti e configurazione sensibile
==================================
Nessun segreto e' hardcoded. ``TEST_FOUNDER_NUM`` e' obbligatorio in ogni run
(KeyError deliberato se assente). ``WA_DAEMON_BASE`` e' obbligatorio solo con
``--send``. Non vengono usati token o API Meta.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

ND = "n/d"
USER_AGENT = "ARGOS-SecondBrain/1.0 (+robots-respecting; founder-test-only)"
MAX_SOURCE_FILE_BYTES = 20 * 1024 * 1024
MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_WEBSITE_PAGES = 5
HTTP_TIMEOUT_SECONDS = 12
CRAWL_DELAY_SECONDS = 1.0
ALLOWED_SCHEMES = {"http", "https"}

IDX_KEYS = {
    "idx", "indice", "index", "row", "riga", "record_idx", "dealer_idx",
}
PIVA_KEYS = {
    "piva", "p_iva", "partita_iva", "partitaiva", "vat", "vat_number",
    "vatnumber", "codice_iva",
}
CLASS_KEYS = {
    "classe", "class", "classe_candidata", "classificazione", "icp",
    "icp_class", "target_class", "classe_icp",
}
PHONE_PRESENT_KEYS = {
    "telefono_presente", "phone_present", "has_phone", "tel_presente",
}
PHONE_KEYS = {"telefono", "phone", "tel", "mobile", "wa", "whatsapp"}
WEBSITE_KEYS = {
    "website", "sito", "sito_web", "url_sito", "web", "homepage",
    "official_website",
}
NAME_KEYS = {
    "name", "nome", "denominazione", "ragione_sociale", "dealer_name",
    "business_name",
}
CITY_KEYS = {"city", "citta", "comune", "sede_comune"}
PROVINCE_KEYS = {"province", "provincia", "prov", "sigla_provincia"}
DEALER_ID_KEYS = {"dealer_id", "crm_id"}

SOCIAL_OR_MARKETPLACE_HOSTS = {
    "facebook.com", "www.facebook.com", "m.facebook.com",
    "instagram.com", "www.instagram.com",
    "meta.com", "www.meta.com",
    "subito.it", "www.subito.it",
    "autoscout24.it", "www.autoscout24.it",
    "autoscout24.com", "www.autoscout24.com",
    "paginegialle.it", "www.paginegialle.it",
}

BRANDS = (
    "Abarth", "Alfa Romeo", "Aston Martin", "Audi", "Bentley", "BMW",
    "Citroen", "Cupra", "Dacia", "DS", "Ferrari", "Fiat", "Ford",
    "Honda", "Hyundai", "Infiniti", "Iveco", "Jaguar", "Jeep", "Kia",
    "Lamborghini", "Lancia", "Land Rover", "Lexus", "Maserati", "Mazda",
    "Mercedes", "Mercedes-Benz", "MINI", "Mitsubishi", "Nissan", "Opel",
    "Peugeot", "Porsche", "Renault", "Seat", "Skoda", "Smart", "Subaru",
    "Suzuki", "Tesla", "Toyota", "Volkswagen", "Volvo",
)

SEGMENT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:suv|crossover)\b", "SUV/crossover"),
    (r"\b(?:premium|lusso|luxury)\b", "premium/lusso"),
    (r"\b(?:sportiv[aei]|supercar)\b", "sportive"),
    (r"\b(?:city\s*car|utilitari[ae])\b", "city car/utilitarie"),
    (r"\b(?:berlin[ae]|station\s*wagon|familiare)\b", "berline/familiari"),
    (r"\b(?:fuoristrada|4x4)\b", "fuoristrada/4x4"),
    (r"\b(?:veicoli commerciali|furgoni|van)\b", "commerciali/van"),
    (r"\b(?:elettric[aei]|ibrid[aei]|plug[- ]?in)\b", "elettriche/ibride"),
    (r"\b(?:usato|occasioni|seconda mano)\b", "usato"),
    (r"\b(?:km\s*0|chilometri zero)\b", "km 0"),
)

SERVICE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\busato garantito\b", "propone usato garantito"),
    (r"\bgaranzia(?:\s+fino\s+a\s+\d+\s+mesi)?\b", "mette in evidenza la garanzia"),
    (r"\b(?:ritiro|valutazione)\s+(?:del\s+)?(?:tuo\s+)?usato\b", "offre ritiro o valutazione dell'usato"),
    (r"\bfinanziament[oi]\b", "propone soluzioni di finanziamento"),
    (r"\bnoleggio\b", "propone servizi di noleggio"),
    (r"\b(?:officina|assistenza|tagliando|manutenzione)\b", "affianca vendita e assistenza"),
    (r"\b(?:importazione|importazioni|auto dalla germania|mercato europeo)\b", "comunica attivita' di importazione europea"),
    (r"\bconsegna(?:\s+a\s+domicilio)?\b", "comunica il servizio di consegna"),
)

FORMAL_MARKERS = (
    "la invitiamo", "vi invitiamo", "la nostra clientela", "gentile cliente",
    "contattateci", "richieda", "scopra", "prenoti", "il nostro staff",
)
INFORMAL_MARKERS = (
    "scopri", "scegli", "vieni", "scrivici", "chiamaci", "la tua auto",
    "il tuo usato", "ti aspettiamo", "trova la tua", "per te",
)
TECHNICAL_MARKERS = (
    "chilometri", " km", "cilindrata", "cambio automatico", "cambio manuale",
    "diesel", "benzina", "ibrido", "elettrico", "cavalli", " cv", "euro 6",
    "garanzia", "tagliando", "manutenzione", "finanziamento", "trazione",
)
EMOTIONAL_MARKERS = (
    "passione", "sogno", "emozione", "liberta", "stile", "esperienza",
    "innamor", "cuore", "desider", "avventura", "unica", "esclusiva",
)
UNCERTAIN_MARKERS = (
    "sembra", "forse", "probabilmente", "potrebbe", "pare", "ipotizzo",
    "credo", "suppongo",
)

PRICE_RE = re.compile(
    r"(?:(?:€|EUR)\s*([0-9]{1,3}(?:[.\s][0-9]{3})+|[0-9]{4,6})|"
    r"([0-9]{1,3}(?:[.\s][0-9]{3})+|[0-9]{4,6})\s*(?:€|EUR))",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?39[\s.-]?)?(?:3\d{2}|0\d{1,3})[\s.-]?\d{5,8}(?!\d)")
URL_RE = re.compile(r"https?://[^\s<>\]\[()]+", re.IGNORECASE)
NUMERIC_PHONE_ARG_RE = re.compile(r"^\+?(?:39)?3\d{8,9}$")


@dataclass(frozen=True)
class Evidence:
    value: str
    source: str
    quote: str
    retrieved_at: str


@dataclass
class SourcedField:
    value: str = ND
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        return sorted({item.source for item in self.evidence})

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "sources": self.sources,
            "evidence": [asdict(item) for item in self.evidence],
        }


@dataclass
class PageObservation:
    url: str
    title: str
    text_blocks: list[str]
    links: list[str]
    status: str
    reason: str = ND


@dataclass
class DealerIdentity:
    idx: str
    piva: str
    source_path: str
    record: dict[str, Any]
    all_source_paths: list[str]


class VisibleHTMLParser(HTMLParser):
    """Small fallback extractor; no script/style content, no DOM execution."""

    BLOCK_TAGS = {
        "title", "h1", "h2", "h3", "h4", "p", "li", "article", "section",
        "figcaption", "blockquote", "td", "th",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "template"}

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._skip_depth = 0
        self._current_tag: str | None = None
        self._buffer: list[str] = []
        self.blocks: list[str] = []
        self.title = ""
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self._flush()
            self._current_tag = tag
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(urllib.parse.urljoin(self.base_url, href))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == self._current_tag:
            self._flush()
            self._current_tag = None

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and self._current_tag:
            self._buffer.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return
        text = clean_text(" ".join(self._buffer))
        self._buffer.clear()
        if len(text) < 3:
            return
        if self._current_tag == "title" and not self.title:
            self.title = text[:240]
        self.blocks.append(text[:600])


class SameSiteRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Allow only same-site redirects (www difference ignored), maximum three."""

    def __init__(self, original_host: str) -> None:
        super().__init__()
        self.original_host = normalize_host(original_host)
        self.redirects = 0

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        self.redirects += 1
        new_host = normalize_host(urllib.parse.urlsplit(newurl).hostname or "")
        if self.redirects > 3 or new_host != self.original_host:
            raise urllib.error.HTTPError(newurl, code, "cross-site/too-many redirect blocked", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def normalize_key(value: Any) -> str:
    text = strip_accents(str(value)).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def normalized_mapping(record: Mapping[str, Any]) -> dict[str, Any]:
    return {normalize_key(key): value for key, value in record.items()}


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def redact_contact_pii(value: str) -> str:
    text = EMAIL_RE.sub("[email rimossa]", value)
    text = PHONE_RE.sub("[telefono rimosso]", text)
    return text


def quote_for_evidence(value: str, limit: int = 240) -> str:
    text = redact_contact_pii(clean_text(value))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return normalize_key(value) in {"", "n_d", "nd", "n_c", "nc", "null", "none", "non_disponibile"}
    return False


def first_present(record: Mapping[str, Any], keys: set[str]) -> Any:
    normalized = normalized_mapping(record)
    for key in keys:
        if key in normalized and not is_null(normalized[key]):
            return normalized[key]
    return None


def normalize_idx(value: Any) -> str:
    text = clean_text(value)
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def normalize_piva(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def valid_piva(value: str) -> bool:
    if not re.fullmatch(r"\d{11}", value):
        return False
    total = 0
    for i, char in enumerate(value[:10]):
        digit = int(char)
        if i % 2 == 0:
            total += digit
        else:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
    return (10 - total % 10) % 10 == int(value[-1])


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return normalize_key(value) in {"true", "si", "yes", "y", "1", "presente", "contattabile"}


def discover_project_root(start: Path | None = None) -> Path:
    origin = (start or Path(__file__).resolve()).resolve()
    candidates = [origin.parent, *origin.parents]
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / ".harness" / "gate_e.py").is_file() and (candidate / "tools" / "dealer_crm.py").is_file():
            return candidate
    raise FileNotFoundError("root europeanautoscout non trovato: mancano .harness/gate_e.py e tools/dealer_crm.py")


def reject_recipient_arguments(argv: Sequence[str]) -> None:
    forbidden_flags = {"--recipient", "--phone", "--to", "--numero", "--destinatario", "--dealer-phone"}
    for position, arg in enumerate(argv):
        flag = arg.split("=", 1)[0]
        if flag in forbidden_flags:
            raise SystemExit(
                f"ERRORE: destinatario CLI vietato ({flag}). Il destinatario e' esclusivamente TEST_FOUNDER_NUM."
            )
        if position > 0 and NUMERIC_PHONE_ARG_RE.fullmatch(arg.strip()):
            raise SystemExit(
                "ERRORE: numero telefonico passato da CLI. Il destinatario e' esclusivamente TEST_FOUNDER_NUM."
            )


def founder_recipient() -> str:
    raw = re.sub(r"\D", "", os.environ["TEST_FOUNDER_NUM"])
    if not re.fullmatch(r"(?:39)?3\d{8,9}", raw):
        raise ValueError("TEST_FOUNDER_NUM non e' un cellulare italiano valido")
    return raw if raw.startswith("39") else "39" + raw


def iter_records_from_json(data: Any) -> Iterator[dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
        return
    if isinstance(data, dict):
        preferred = ("records", "rows", "dealers", "items", "data", "results")
        normalized = normalized_mapping(data)
        for key in preferred:
            value = normalized.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                return
        if any(key in normalized for key in PIVA_KEYS):
            yield data
            return
        for key, value in data.items():
            if isinstance(value, dict):
                copy = dict(value)
                if not any(k in normalized_mapping(copy) for k in IDX_KEYS):
                    copy.setdefault("idx", key)
                yield copy


def read_records(path: Path) -> Iterator[dict[str, Any]]:
    try:
        if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            return
    except OSError:
        return
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            with path.open("r", encoding="utf-8") as handle:
                yield from iter_records_from_json(json.load(handle))
        elif suffix == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    if isinstance(item, dict):
                        yield item
        elif suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                sample = handle.read(4096)
                handle.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                except csv.Error:
                    dialect = csv.excel
                for row in csv.DictReader(handle, dialect=dialect):
                    yield dict(row)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
        return


def candidate_data_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    files: list[Path] = []
    for suffix in ("*.json", "*.jsonl", "*.csv"):
        files.extend(directory.rglob(suffix))
    return sorted(
        path for path in set(files)
        if not path.name.startswith("second_brain_") and "second_brain_output" not in path.parts
    )


def record_identity(record: Mapping[str, Any]) -> tuple[str, str]:
    return (
        normalize_idx(first_present(record, IDX_KEYS)),
        normalize_piva(first_present(record, PIVA_KEYS)),
    )


def contactable_evidence(record: Mapping[str, Any]) -> tuple[bool, str]:
    normalized = normalized_mapping(record)
    explicit = None
    for key in ("contattabile", "contattabile_subito", "is_contactable"):
        if key in normalized and not is_null(normalized[key]):
            explicit = truthy(normalized[key])
            break

    class_value = normalize_key(first_present(record, CLASS_KEYS) or "")
    qualified = class_value == "solo_anagrafe"
    for key in ("qualificabile", "is_qualified"):
        if key in normalized and not is_null(normalized[key]):
            qualified = truthy(normalized[key])

    phone_present = False
    for key in PHONE_PRESENT_KEYS:
        if key in normalized and not is_null(normalized[key]):
            phone_present = truthy(normalized[key])
            break
    if not phone_present:
        phone = first_present(record, PHONE_KEYS)
        phone_present = phone is not None and not is_null(phone)

    result = explicit if explicit is not None else (qualified and phone_present)
    detail = f"explicit={explicit!r}; class={class_value or ND}; qualified={qualified}; telefono_presente={phone_present}"
    return bool(result), detail


def find_dealer_identity(root: Path, idx: str, piva: str) -> DealerIdentity:
    if not valid_piva(piva):
        raise ValueError("P.IVA non valida: richieste 11 cifre con checksum italiano corretto")
    source_dir = root / "data" / "recon" / "mandatari"
    files = candidate_data_files(source_dir)
    if not files:
        raise FileNotFoundError(f"nessuna fonte mandatari trovata in {source_dir}")

    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in files:
        for record in read_records(path):
            rec_idx, rec_piva = record_identity(record)
            if rec_idx == idx and rec_piva == piva:
                matches.append((path, record))

    if not matches:
        raise LookupError(f"dealer idx={idx} + P.IVA={piva} non trovato nelle fonti mandatari")

    valid_matches: list[tuple[Path, dict[str, Any]]] = []
    rejection_details: list[str] = []
    for path, record in matches:
        allowed, detail = contactable_evidence(record)
        if allowed:
            valid_matches.append((path, record))
        else:
            rejection_details.append(f"{path}: {detail}")
    if not valid_matches:
        details = " | ".join(rejection_details)
        raise PermissionError(
            "record trovato ma non certificato CONTATTABILE secondo solo-anagrafe AND telefono_presente: " + details
        )

    def richness(item: tuple[Path, dict[str, Any]]) -> tuple[int, int]:
        path, record = item
        populated = sum(1 for value in record.values() if not is_null(value))
        return populated, -len(str(path))

    selected_path, selected_record = max(valid_matches, key=richness)
    return DealerIdentity(
        idx=idx,
        piva=piva,
        source_path=str(selected_path.relative_to(root)),
        record=dict(selected_record),
        all_source_paths=[str(path.relative_to(root)) for path, _ in valid_matches],
    )


def find_registry_records(root: Path, piva: str) -> list[tuple[str, dict[str, Any]]]:
    registry_dir = root / "data" / "registry"
    matches: list[tuple[str, dict[str, Any]]] = []
    for path in candidate_data_files(registry_dir):
        for record in read_records(path):
            if normalize_piva(first_present(record, PIVA_KEYS)) == piva:
                matches.append((str(path.relative_to(root)), record))
    return matches


def load_crm_record(root: Path, dealer_record: Mapping[str, Any]) -> tuple[str, dict[str, Any]] | None:
    dealer_id = first_present(dealer_record, DEALER_ID_KEYS)
    if not dealer_id:
        return None
    crm_path = root / "tools" / "dealer_crm.py"
    if not crm_path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("argos_dealer_crm_readonly", crm_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connection = module.connect()
        try:
            module.ensure_tables(connection)
            row = connection.execute("SELECT * FROM dealers WHERE dealer_id = ?", (str(dealer_id),)).fetchone()
            if row is None:
                return None
            return f"crm://dealers/{dealer_id}", dict(row)
        finally:
            connection.close()
    except (OSError, sqlite3.Error, ImportError, AttributeError):
        return None


def normalize_host(host: str) -> str:
    host = host.lower().strip().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def normalize_http_url(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    if not re.match(r"^https?://", text, flags=re.IGNORECASE):
        text = "https://" + text
    parsed = urllib.parse.urlsplit(text)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    if host in SOCIAL_OR_MARKETPLACE_HOSTS or normalize_host(host) in {normalize_host(h) for h in SOCIAL_OR_MARKETPLACE_HOSTS}:
        return None
    path = parsed.path or "/"
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc, path, parsed.query, ""))


def choose_website_url(
    identity: DealerIdentity,
    registry_records: Sequence[tuple[str, dict[str, Any]]],
    crm_record: tuple[str, dict[str, Any]] | None,
) -> tuple[str | None, str]:
    candidates: list[tuple[Any, str]] = []
    candidates.append((first_present(identity.record, WEBSITE_KEYS), identity.source_path))
    for source, record in registry_records:
        candidates.append((first_present(record, WEBSITE_KEYS), source))
    if crm_record:
        source, record = crm_record
        candidates.append((first_present(record, WEBSITE_KEYS), source))
    for value, source in candidates:
        url = normalize_http_url(value)
        if url:
            return url, source
    return None, ND


def build_opener(url: str) -> urllib.request.OpenerDirector:
    host = urllib.parse.urlsplit(url).hostname or ""
    return urllib.request.build_opener(SameSiteRedirectHandler(host))


def http_get(url: str, *, max_bytes: int = MAX_HTML_BYTES) -> tuple[int, Mapping[str, str], bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.1",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.5",
        },
        method="GET",
    )
    opener = build_opener(url)
    try:
        with opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 200))
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError(f"risposta oltre limite {max_bytes} byte")
            final_url = response.geturl()
            return status, headers, body, final_url
    except urllib.error.HTTPError as exc:
        body = exc.read(4096) if hasattr(exc, "read") else b""
        headers = {str(k).lower(): str(v) for k, v in (exc.headers or {}).items()}
        return int(exc.code), headers, body, exc.geturl()


def robots_permission(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlsplit(url)
    robots_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    try:
        status, headers, body, _ = http_get(robots_url, max_bytes=512 * 1024)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return False, f"robots non determinabile: {type(exc).__name__}: {exc}"
    if status == 404:
        return True, "robots.txt assente (404)"
    if status in {401, 403, 429} or status >= 500:
        return False, f"robots non accessibile: HTTP {status}"
    if status < 200 or status >= 300:
        return False, f"robots stato non gestito: HTTP {status}"
    content_type = headers.get("content-type", "")
    if "text" not in content_type and body:
        return False, f"robots content-type non testuale: {content_type or ND}"
    text = body.decode("utf-8", errors="replace")
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(text.splitlines())
    allowed = parser.can_fetch(USER_AGENT, url)
    return allowed, "robots allow" if allowed else "robots deny"


def looks_cloudflare(headers: Mapping[str, str], body: bytes) -> bool:
    server = headers.get("server", "").lower()
    sample = body[:8192].decode("utf-8", errors="ignore").lower()
    return "cloudflare" in server or "cf-ray" in headers or "attention required! | cloudflare" in sample


def decode_body(body: bytes, headers: Mapping[str, str]) -> str:
    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([\w-]+)", content_type, re.IGNORECASE)
    candidates = [match.group(1)] if match else []
    candidates.extend(["utf-8", "latin-1"])
    for encoding in candidates:
        try:
            return body.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return body.decode("utf-8", errors="replace")


def extract_html(url: str, raw_html: str) -> tuple[str, list[str], list[str]]:
    parser = VisibleHTMLParser(url)
    parser.feed(raw_html)
    parser.close()
    blocks = parser.blocks
    try:
        import trafilatura  # type: ignore

        extracted = trafilatura.extract(
            raw_html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_precision=True,
        )
        if extracted:
            extra_blocks = [clean_text(part) for part in re.split(r"\n+", extracted) if len(clean_text(part)) >= 3]
            blocks = dedupe_preserve([*parser.blocks, *extra_blocks])
    except (ImportError, AttributeError, TypeError, ValueError):
        pass
    blocks = [redact_contact_pii(block)[:600] for block in blocks if not mostly_noise(block)]
    return parser.title, dedupe_preserve(blocks)[:180], dedupe_preserve(parser.links)


def mostly_noise(text: str) -> bool:
    normalized = normalize_key(text)
    if not normalized:
        return True
    noise = {"cookie", "privacy", "accetta", "rifiuta", "menu", "javascript", "copyright"}
    words = set(normalized.split("_"))
    return len(words) <= 4 and bool(words & noise)


def dedupe_preserve(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = clean_text(value).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(clean_text(value))
    return result


def same_site(base_url: str, candidate: str) -> bool:
    base = normalize_host(urllib.parse.urlsplit(base_url).hostname or "")
    other = normalize_host(urllib.parse.urlsplit(candidate).hostname or "")
    return bool(base and base == other)


def selected_internal_links(base_url: str, links: Sequence[str]) -> list[str]:
    keywords = (
        "auto", "usato", "occasion", "stock", "vetture", "servizi", "chi-siamo",
        "azienda", "about", "showroom", "garanzia", "finanziament",
    )
    ranked: list[tuple[int, str]] = []
    for link in links:
        parsed = urllib.parse.urlsplit(link)
        if parsed.scheme.lower() not in ALLOWED_SCHEMES or not same_site(base_url, link):
            continue
        if parsed.fragment:
            link = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
        lower = link.lower()
        score = sum(1 for keyword in keywords if keyword in lower)
        if score:
            ranked.append((-score, link))
    return [url for _, url in sorted(set(ranked))[: MAX_WEBSITE_PAGES - 1]]


def fetch_page(url: str) -> PageObservation:
    allowed, robots_reason = robots_permission(url)
    if not allowed:
        return PageObservation(url=url, title=ND, text_blocks=[], links=[], status="n/d", reason=robots_reason)
    try:
        status, headers, body, final_url = http_get(url)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return PageObservation(
            url=url, title=ND, text_blocks=[], links=[], status="n/d",
            reason=f"fetch fallito: {type(exc).__name__}: {exc}",
        )
    if status in {401, 403, 429}:
        return PageObservation(url=url, title=ND, text_blocks=[], links=[], status="n/d", reason=f"HTTP {status}, nessun bypass")
    if status < 200 or status >= 300:
        return PageObservation(url=url, title=ND, text_blocks=[], links=[], status="n/d", reason=f"HTTP {status}")
    if looks_cloudflare(headers, body):
        return PageObservation(url=url, title=ND, text_blocks=[], links=[], status="n/d", reason="Cloudflare rilevato, nessun bypass")
    content_type = headers.get("content-type", "").lower()
    if "html" not in content_type and "text/plain" not in content_type:
        return PageObservation(url=url, title=ND, text_blocks=[], links=[], status="n/d", reason=f"content-type non HTML: {content_type or ND}")
    raw_html = decode_body(body, headers)
    title, blocks, links = extract_html(final_url, raw_html)
    if not blocks:
        return PageObservation(url=final_url, title=title or ND, text_blocks=[], links=[], status="n/d", reason="nessun testo visibile estraibile")
    return PageObservation(url=final_url, title=title or ND, text_blocks=blocks, links=links, status="ok", reason=robots_reason)


def collect_website(url: str | None) -> list[PageObservation]:
    if not url:
        return []
    homepage = fetch_page(url)
    pages = [homepage]
    if homepage.status != "ok":
        return pages
    for link in selected_internal_links(homepage.url, homepage.links):
        if len(pages) >= MAX_WEBSITE_PAGES:
            break
        time.sleep(CRAWL_DELAY_SECONDS)
        pages.append(fetch_page(link))
    return pages


def source_evidence(value: Any, source: str, quote: Any | None = None) -> Evidence:
    text = clean_text(value)
    return Evidence(
        value=text or ND,
        source=source,
        quote=quote_for_evidence(quote if quote is not None else text),
        retrieved_at=utc_now(),
    )


def values_from_field(record: Mapping[str, Any], possible_keys: set[str]) -> list[str]:
    value = first_present(record, possible_keys)
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if not is_null(item)]
    text = clean_text(value)
    if text.startswith("["):
        try:
            decoded = json.loads(text)
            if isinstance(decoded, list):
                return [clean_text(item) for item in decoded if not is_null(item)]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in re.split(r"[,;/|]", text) if item.strip()]


def website_corpus(pages: Sequence[PageObservation]) -> list[tuple[str, str]]:
    corpus: list[tuple[str, str]] = []
    for page in pages:
        if page.status != "ok":
            continue
        if page.title != ND:
            corpus.append((page.url, page.title))
        corpus.extend((page.url, block) for block in page.text_blocks)
    return corpus


def find_brand_evidence(
    corpus: Sequence[tuple[str, str]],
    identity: DealerIdentity,
    registry_records: Sequence[tuple[str, dict[str, Any]]],
    crm_record: tuple[str, dict[str, Any]] | None,
) -> dict[str, list[Evidence]]:
    found: dict[str, list[Evidence]] = {}

    def add(brand: str, evidence: Evidence) -> None:
        canonical = "Mercedes-Benz" if brand.lower() in {"mercedes", "mercedes-benz"} else brand
        found.setdefault(canonical, []).append(evidence)

    local_sources: list[tuple[str, Mapping[str, Any]]] = [(identity.source_path, identity.record)]
    local_sources.extend(registry_records)
    if crm_record:
        local_sources.append(crm_record)
    for source, record in local_sources:
        for raw in values_from_field(record, {"brands", "marche", "brand", "marchi"}):
            for brand in BRANDS:
                if re.search(rf"(?<!\w){re.escape(brand)}(?!\w)", raw, re.IGNORECASE):
                    add(brand, source_evidence(brand, source, raw))

    for source, text in corpus:
        for brand in BRANDS:
            if re.search(rf"(?<!\w){re.escape(brand)}(?!\w)", text, re.IGNORECASE):
                add(brand, source_evidence(brand, source, text))
    return found


def find_segment_evidence(corpus: Sequence[tuple[str, str]]) -> dict[str, list[Evidence]]:
    found: dict[str, list[Evidence]] = {}
    for source, text in corpus:
        lowered = strip_accents(text).lower()
        for pattern, label in SEGMENT_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                found.setdefault(label, []).append(source_evidence(label, source, text))
    return found


def parse_prices(corpus: Sequence[tuple[str, str]]) -> list[tuple[int, Evidence]]:
    prices: list[tuple[int, Evidence]] = []
    for source, text in corpus:
        for match in PRICE_RE.finditer(text):
            raw = match.group(1) or match.group(2) or ""
            value = int(re.sub(r"\D", "", raw))
            if 1_000 <= value <= 300_000:
                prices.append((value, source_evidence(str(value), source, text)))
    return prices


def synthesize_specialization(
    brand_map: Mapping[str, list[Evidence]],
    segment_map: Mapping[str, list[Evidence]],
    prices: Sequence[tuple[int, Evidence]],
) -> tuple[SourcedField, SourcedField, SourcedField, SourcedField]:
    brands = sorted(brand_map)
    segments = sorted(segment_map)
    brand_field = SourcedField()
    segment_field = SourcedField()
    price_field = SourcedField()

    if brands:
        brand_field = SourcedField(
            value=", ".join(brands),
            evidence=[items[0] for _, items in sorted(brand_map.items())],
        )
    if segments:
        segment_field = SourcedField(
            value=", ".join(segments),
            evidence=[items[0] for _, items in sorted(segment_map.items())],
        )
    distinct_prices = sorted({value for value, _ in prices})
    if len(distinct_prices) >= 2:
        low, high = distinct_prices[0], distinct_prices[-1]
        low_ev = next(ev for value, ev in prices if value == low)
        high_ev = next(ev for value, ev in prices if value == high)
        price_field = SourcedField(
            value=f"€{low:,.0f}–€{high:,.0f}".replace(",", "."),
            evidence=[low_ev, high_ev],
        )

    parts: list[str] = []
    evidence: list[Evidence] = []
    if brand_field.value != ND:
        parts.append(f"marchi rilevati: {brand_field.value}")
        evidence.extend(brand_field.evidence)
    if segment_field.value != ND:
        parts.append(f"segmenti rilevati: {segment_field.value}")
        evidence.extend(segment_field.evidence)
    if price_field.value != ND:
        parts.append(f"fascia prezzi osservata: {price_field.value}")
        evidence.extend(price_field.evidence)
    specialization = SourcedField(value="; ".join(parts), evidence=evidence) if parts else SourcedField()
    return specialization, brand_field, segment_field, price_field


def count_markers(text: str, markers: Sequence[str]) -> tuple[int, list[str]]:
    normalized = strip_accents(text).lower()
    hits = [marker for marker in markers if marker in normalized]
    return len(hits), hits


def synthesize_register(corpus: Sequence[tuple[str, str]], note_manuali: str) -> dict[str, SourcedField]:
    observations = list(corpus)
    note = redact_contact_pii(clean_text(note_manuali))
    if note:
        observations.append(("manual://note_manuali", note))
    if not observations:
        return {
            "formalita": SourcedField(),
            "asse": SourcedField(),
            "lunghezza_tipica": SourcedField(),
            "sintesi": SourcedField(),
        }

    formal_score = informal_score = technical_score = emotional_score = 0
    formal_ev: list[Evidence] = []
    informal_ev: list[Evidence] = []
    technical_ev: list[Evidence] = []
    emotional_ev: list[Evidence] = []
    word_lengths: list[tuple[int, Evidence]] = []

    for source, text in observations:
        if len(text.split()) < 4:
            continue
        fs, _ = count_markers(text, FORMAL_MARKERS)
        ins, _ = count_markers(text, INFORMAL_MARKERS)
        ts, _ = count_markers(text, TECHNICAL_MARKERS)
        es, _ = count_markers(text, EMOTIONAL_MARKERS)
        if fs:
            formal_score += fs
            formal_ev.append(source_evidence(str(fs), source, text))
        if ins:
            informal_score += ins
            informal_ev.append(source_evidence(str(ins), source, text))
        if ts:
            technical_score += ts
            technical_ev.append(source_evidence(str(ts), source, text))
        if es:
            emotional_score += es
            emotional_ev.append(source_evidence(str(es), source, text))
        word_lengths.append((len(text.split()), source_evidence(str(len(text.split())), source, text)))

    formalita = SourcedField()
    if formal_score >= 2 and formal_score > informal_score:
        formalita = SourcedField("formale", formal_ev[:3])
    elif informal_score >= 2 and informal_score > formal_score:
        formalita = SourcedField("informale", informal_ev[:3])

    asse = SourcedField()
    if technical_score >= 3 and technical_score > emotional_score:
        asse = SourcedField("tecnico", technical_ev[:3])
    elif emotional_score >= 2 and emotional_score > technical_score:
        asse = SourcedField("emotivo", emotional_ev[:3])
    elif technical_score >= 2 and emotional_score >= 2:
        asse = SourcedField("tecnico-emotivo", [*technical_ev[:2], *emotional_ev[:2]])

    length_field = SourcedField()
    if len(word_lengths) >= 3:
        median_words = statistics.median(length for length, _ in word_lengths)
        label = "breve" if median_words <= 12 else "media" if median_words <= 25 else "lunga"
        closest = sorted(word_lengths, key=lambda item: abs(item[0] - median_words))[:3]
        length_field = SourcedField(f"{label} (mediana {median_words:g} parole per blocco)", [ev for _, ev in closest])

    parts = [field.value for field in (formalita, asse, length_field) if field.value != ND]
    evidence = [*formalita.evidence, *asse.evidence, *length_field.evidence]
    summary = SourcedField(", ".join(parts), evidence) if parts else SourcedField()
    return {
        "formalita": formalita,
        "asse": asse,
        "lunghezza_tipica": length_field,
        "sintesi": summary,
    }


def grammatical_manual_hook(note_manuali: str) -> tuple[str, Evidence] | None:
    note = redact_contact_pii(clean_text(note_manuali))
    if not note or any(marker in strip_accents(note).lower() for marker in UNCERTAIN_MARKERS):
        return None
    sentences = [clean_text(sentence) for sentence in re.split(r"(?<=[.!?])\s+|\n+", note) if clean_text(sentence)]
    for sentence in sentences:
        if len(sentence.split()) < 5 or len(sentence) > 180:
            continue
        lowered = strip_accents(sentence).lower().rstrip(".!?")
        # Only business/content observations, never people or private details.
        if not any(token in lowered for token in (
            "pubblica", "comunica", "presenta", "tratta", "propone", "mostra",
            "promuove", "punta", "parla", "stock", "auto", "suv", "usato",
            "garanzia", "finanziamento", "consegna", "import",
        )):
            continue
        lowered = re.sub(r"^(il dealer|la concessionaria|l'azienda|azienda)\s+", "", lowered)
        hook = f"sui vostri contenuti social {lowered}"
        return hook, source_evidence(hook, "manual://note_manuali", sentence)
    return None


def synthesize_hook(
    corpus: Sequence[tuple[str, str]],
    brand_map: Mapping[str, list[Evidence]],
    segment_map: Mapping[str, list[Evidence]],
    price_field: SourcedField,
    note_manuali: str,
) -> SourcedField:
    manual = grammatical_manual_hook(note_manuali)
    if manual:
        hook, evidence = manual
        return SourcedField(hook, [evidence])

    service_candidates: list[tuple[str, Evidence]] = []
    for source, text in corpus:
        lowered = strip_accents(text).lower()
        for pattern, phrase in SERVICE_PATTERNS:
            if re.search(pattern, lowered, re.IGNORECASE):
                service_candidates.append((phrase, source_evidence(phrase, source, text)))
    if service_candidates:
        phrase, evidence = service_candidates[0]
        brands = sorted(brand_map)
        if brands:
            selected = " e ".join(brands[:2])
            return SourcedField(
                f"mettete in evidenza {selected} e {phrase}",
                [brand_map[brands[0]][0], evidence],
            )
        return SourcedField(phrase, [evidence])

    brands = sorted(brand_map)
    segments = sorted(segment_map)
    if len(brands) >= 2 and segments:
        return SourcedField(
            f"trattate {brands[0]} e {brands[1]}, con attenzione al segmento {segments[0]}",
            [brand_map[brands[0]][0], brand_map[brands[1]][0], segment_map[segments[0]][0]],
        )
    if len(brands) >= 3:
        return SourcedField(
            f"lo stock online include {brands[0]}, {brands[1]} e {brands[2]}",
            [brand_map[brands[0]][0], brand_map[brands[1]][0], brand_map[brands[2]][0]],
        )
    if segments and price_field.value != ND:
        return SourcedField(
            f"l'offerta online si concentra su {segments[0]} nella fascia {price_field.value}",
            [segment_map[segments[0]][0], *price_field.evidence],
        )
    return SourcedField()


def sanitize_hook_for_message(hook: str) -> str:
    hook = redact_contact_pii(clean_text(hook)).strip(" .;:-")
    hook = re.sub(r"\b(?:P\.?\s*IVA|partita iva)\b.*", "", hook, flags=re.IGNORECASE).strip()
    return hook[:220]


def generate_day1(hook: SourcedField) -> tuple[str, bool]:
    if hook.value != ND and hook.evidence:
        safe_hook = sanitize_hook_for_message(hook.value)
        message = (
            "Buongiorno, sono Luca Ferretti — verifico auto europee per concessionari italiani.\n"
            f"Ho visto che {safe_hook}.\n"
            "Se vuole, mi manda una targa: le faccio gratis una prima verifica e le dico subito se emergono elementi da approfondire.\n"
            "Luca"
        )
        personalized = True
    else:
        message = (
            "Buongiorno, sono Luca Ferretti — verifico auto europee per concessionari italiani.\n"
            "Lavoro su controlli preliminari prima dell'acquisto, senza impegno.\n"
            "Se vuole, mi manda una targa: le faccio gratis una prima verifica e le dico subito se emergono elementi da approfondire.\n"
            "Luca"
        )
        personalized = False
    validate_day1(message, hook, personalized)
    return message, personalized


def validate_day1(message: str, hook: SourcedField, personalized: bool) -> None:
    lowered = strip_accents(message).lower()
    if "targa" not in lowered or "gratis" not in lowered:
        raise AssertionError("Day1 invalido: CTA verifica-targa gratuita assente")
    if "http://" in lowered or "https://" in lowered:
        raise AssertionError("Day1 invalido: link vietato")
    if EMAIL_RE.search(message) or PHONE_RE.search(message):
        raise AssertionError("Day1 invalido: PII/numero rilevato")
    if any(token in lowered for token in ("€800", "€1.200", "fee", "commissione")):
        raise AssertionError("Day1 invalido: fee non ammessa nel Day1")
    word_count = len(re.findall(r"\b\w+[\w'’-]*\b", message, re.UNICODE))
    if word_count > 70:
        raise AssertionError(f"Day1 invalido: {word_count} parole > 70")
    if personalized and (hook.value == ND or not hook.evidence):
        raise AssertionError("finta personalizzazione: aggancio privo di fonte")
    if not personalized:
        forbidden = ("vostro", "vostra", "suo stock", "sua offerta", "ho visto che")
        if any(term in lowered for term in forbidden):
            raise AssertionError("fallback generico contiene riferimento al dealer")


def crm_compatible_projection(
    identity: DealerIdentity,
    registry_records: Sequence[tuple[str, dict[str, Any]]],
    website_url: str | None,
    brand_field: SourcedField,
    specialization: SourcedField,
) -> dict[str, Any]:
    records: list[Mapping[str, Any]] = [identity.record, *(record for _, record in registry_records)]

    def first_across(keys: set[str]) -> str:
        for record in records:
            value = first_present(record, keys)
            if value is not None:
                return clean_text(value)
        return ND

    piva_hash = hashlib.sha256(identity.piva.encode("ascii")).hexdigest()[:12]
    dealer_id = clean_text(first_present(identity.record, DEALER_ID_KEYS) or f"mandatario_{identity.idx}_{piva_hash}")
    brands_json = json.dumps(
        [] if brand_field.value == ND else [item.strip() for item in brand_field.value.split(",")],
        ensure_ascii=False,
    )
    return {
        # Chiavi esistenti in tools/dealer_crm.py; nessun telefono/WA/email viene copiato.
        "dealer_id": dealer_id,
        "name": first_across(NAME_KEYS),
        "city": first_across(CITY_KEYS),
        "province": first_across(PROVINCE_KEYS),
        "brands": brands_json,
        "website": website_url or ND,
        "source_url": website_url or ND,
        "pipeline_status": "NEW",
        "notes": specialization.value,
    }


def on_demand_compatible_hint(brand_field: SourcedField, price_field: SourcedField) -> dict[str, Any]:
    """Keys aligned with tools/on_demand_runner.py; unknowns are n/d, never zero."""
    make = ND
    if brand_field.value != ND:
        make = brand_field.value.split(",", 1)[0].strip()
    price_max: int | str = ND
    if price_field.value != ND:
        numbers = [int(item.replace(".", "")) for item in re.findall(r"€([0-9.]+)", price_field.value)]
        if numbers:
            price_max = max(numbers)
    return {
        "make": make,
        "model": ND,
        "price_max": price_max,
        "year_min": ND,
        "mileage_max": ND,
    }


def gate_e_preflight(root: Path, recipient: str) -> None:
    gate_path = root / ".harness" / "gate_e.py"
    if not gate_path.is_file():
        raise FileNotFoundError("Gate E assente: invio vietato")
    synthetic_command = f"curl :9191/send -d to={recipient}"
    payload = {"tool_name": "Bash", "tool_input": {"command": synthetic_command}}
    result = subprocess.run(
        [sys.executable, str(gate_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(root),
        env=os.environ.copy(),
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Gate E preflight errore rc={result.returncode}: {result.stderr.strip()}")
    stdout = result.stdout.strip()
    if stdout:
        try:
            decision = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gate E output non interpretabile: {stdout}") from exc
        if decision.get("hookSpecificOutput", {}).get("permissionDecision") == "deny":
            reason = decision.get("hookSpecificOutput", {}).get("permissionDecisionReason", "deny")
            raise PermissionError(f"Gate E ha negato l'invio: {reason}")


def daemon_send(root: Path, recipient: str, dealer_id: str, message: str) -> dict[str, Any]:
    gate_e_preflight(root, recipient)
    base = os.environ["WA_DAEMON_BASE"].rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError("WA_DAEMON_BASE non valido")

    # Health check, stesso contratto del sender esistente.
    health_req = urllib.request.Request(base + "/", headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(health_req, timeout=5) as response:
            health = json.loads(response.read(512 * 1024).decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"WA daemon health fallito: {exc}") from exc
    if not health.get("wa_connected", False):
        raise RuntimeError("WA daemon raggiungibile ma wa_connected=false")

    payload = {"phone": recipient, "message": message, "dealer_id": dealer_id}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    send_req = urllib.request.Request(
        base + "/send",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(send_req, timeout=15) as response:
            result = json.loads(response.read(512 * 1024).decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"invio WA fallito: {exc}") from exc
    if result.get("status") != "sent":
        raise RuntimeError(f"WA daemon non ha confermato status=sent: {result}")
    return result


def artifact_path(root: Path, identity: DealerIdentity) -> Path:
    output_dir = root / "data" / "recon" / "mandatari"
    output_dir.mkdir(parents=True, exist_ok=True)
    stable_id = hashlib.sha256(f"{identity.idx}|{identity.piva}".encode("ascii")).hexdigest()[:16]
    path = output_dir / f"second_brain_{stable_id}.json"
    resolved_dir = output_dir.resolve()
    resolved = path.resolve()
    if resolved_dir not in resolved.parents:
        raise RuntimeError("artifact path escape bloccato")
    return path


def build_artifact(
    *,
    root: Path,
    identity: DealerIdentity,
    registry_records: Sequence[tuple[str, dict[str, Any]]],
    crm_record: tuple[str, dict[str, Any]] | None,
    website_url: str | None,
    website_source: str,
    pages: Sequence[PageObservation],
    note_manuali: str,
    recipient: str,
) -> tuple[dict[str, Any], str]:
    corpus = website_corpus(pages)
    brand_map = find_brand_evidence(corpus, identity, registry_records, crm_record)
    segment_map = find_segment_evidence(corpus)
    prices = parse_prices(corpus)
    specialization, brand_field, segment_field, price_field = synthesize_specialization(
        brand_map, segment_map, prices
    )
    register = synthesize_register(corpus, note_manuali)
    hook = synthesize_hook(corpus, brand_map, segment_map, price_field, note_manuali)
    message, personalized = generate_day1(hook)
    crm_projection = crm_compatible_projection(
        identity, registry_records, website_url, brand_field, specialization
    )
    on_demand_hint = on_demand_compatible_hint(brand_field, price_field)

    piva_hash = hashlib.sha256(identity.piva.encode("ascii")).hexdigest()
    source_status = []
    for page in pages:
        source_status.append({
            "source": page.url,
            "status": page.status,
            "reason": page.reason,
            "title": page.title,
            "text_blocks": len(page.text_blocks) if page.status == "ok" else ND,
        })
    if not pages:
        source_status.append({"source": "website", "status": "n/d", "reason": "URL ufficiale assente nelle fonti locali"})

    artifact = {
        "schema_version": "second-brain.v1",
        "generated_at": utc_now(),
        "dealer_key": {
            "idx": identity.idx,
            "piva_sha256": piva_hash,
            "piva_last4": identity.piva[-4:],
            "contactable_validation": "solo-anagrafe AND telefono_presente",
            "source": identity.source_path,
            "matching_sources": identity.all_source_paths,
        },
        "collection": {
            "registry_sources": [source for source, _ in registry_records] or [ND],
            "crm_source": crm_record[0] if crm_record else ND,
            "website": {
                "url": website_url or ND,
                "url_source": website_source,
                "pages": source_status,
            },
            "note_manuali": redact_contact_pii(clean_text(note_manuali)) or ND,
            "prohibited_sources_not_accessed": [
                "Facebook", "Instagram", "Meta Ad Library", "Subito", "AutoScout24", "PagineGialle"
            ],
        },
        "synthesis": {
            "specializzazione_reale": specialization.to_dict(),
            "marche": brand_field.to_dict(),
            "segmenti": segment_field.to_dict(),
            "fascia_prezzo": price_field.to_dict(),
            "registro_comunicativo": {key: value.to_dict() for key, value in register.items()},
            "aggancio_specifico": hook.to_dict(),
        },
        "generation": {
            "template": "Day1 v5 — CTA verifica-targa gratis",
            "personalized": personalized,
            "message": message,
            "recipient_policy": "env:TEST_FOUNDER_NUM only",
            "recipient_fingerprint": hashlib.sha256(recipient.encode("ascii")).hexdigest()[:12],
            "daemon_payload_runtime": {
                "phone": "env:TEST_FOUNDER_NUM",
                "message": message,
                "dealer_id": crm_projection["dealer_id"],
            },
        },
        "compatibility": {
            "dealer_crm": crm_projection,
            "on_demand_runner_search_params": on_demand_hint,
            "gate_e": ".harness/gate_e.py preflight required before --send",
        },
        "null_discipline": "unknown values are n/d; zero is never used as unknown",
    }
    return artifact, message


def write_artifact(path: Path, artifact: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def self_test() -> None:
    assert valid_piva("09248401003")
    assert normalize_piva("IT 092.484.01003") == "09248401003"
    generic, personalized = generate_day1(SourcedField())
    assert not personalized and "Ho visto che" not in generic
    evidence = source_evidence("trattate BMW e Audi", "https://example.test/")
    custom, personalized = generate_day1(SourcedField("trattate BMW e Audi", [evidence]))
    assert personalized and "Ho visto che trattate BMW e Audi" in custom
    test_record = {"classe_candidata": "solo-anagrafe", "telefono_presente": True}
    assert contactable_evidence(test_record)[0]
    assert not contactable_evidence({"classe_candidata": "fuori-target", "telefono_presente": True})[0]
    assert on_demand_compatible_hint(SourcedField(), SourcedField())["price_max"] == ND
    print("SELFTEST PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profilo dealer lecito + Day1 v5 personalizzato, destinatario founder-test soltanto.",
        allow_abbrev=False,
    )
    parser.add_argument("--idx", required=False, help="idx del dealer nei 44 CONTATTABILI")
    parser.add_argument("--piva", required=False, help="P.IVA italiana del dealer")
    parser.add_argument("--note-manuali", default="", help="note social lette e scritte manualmente dal founder")
    parser.add_argument("--send", action="store_true", help="invia al solo TEST_FOUNDER_NUM dopo Gate E")
    parser.add_argument("--json", action="store_true", help="stampa l'artefatto JSON invece del solo messaggio")
    parser.add_argument("--self-test", action="store_true", help="esegue controlli locali senza rete/dati")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    reject_recipient_arguments(actual_argv)
    parser = build_parser()
    args = parser.parse_args(actual_argv)
    if args.self_test:
        self_test()
        return 0
    if args.idx is None or args.piva is None:
        parser.error("--idx e --piva sono obbligatori salvo --self-test")

    # KeyError deliberato anche in dry-run, come richiesto dal mandato.
    recipient = founder_recipient()
    idx = normalize_idx(args.idx)
    piva = normalize_piva(args.piva)
    root = discover_project_root()
    identity = find_dealer_identity(root, idx, piva)
    registry_records = find_registry_records(root, piva)
    crm_record = load_crm_record(root, identity.record)
    website_url, website_source = choose_website_url(identity, registry_records, crm_record)
    pages = collect_website(website_url)
    artifact, message = build_artifact(
        root=root,
        identity=identity,
        registry_records=registry_records,
        crm_record=crm_record,
        website_url=website_url,
        website_source=website_source,
        pages=pages,
        note_manuali=args.note_manuali,
        recipient=recipient,
    )
    out_path = artifact_path(root, identity)
    write_artifact(out_path, artifact)

    if args.send:
        result = daemon_send(
            root,
            recipient,
            artifact["compatibility"]["dealer_crm"]["dealer_id"],
            message,
        )
        artifact["generation"]["send_result"] = {
            "status": result.get("status", ND),
            "msg_id": result.get("msg_id", ND),
            "daily_sent": result.get("daily_sent", ND),
        }
        write_artifact(out_path, artifact)

    if args.json:
        print(json.dumps(artifact, ensure_ascii=False, indent=2))
    else:
        print(message)
    print(f"artifact={out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
