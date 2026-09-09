#!/usr/bin/env python3
"""Fail closed when the locked ARGOS npm audit exceeds its reviewed exception.

This is a regression boundary, not a vulnerability waiver.  A clean report is
accepted.  The only non-clean report accepted is the exact, documented optional
WhatsApp/Puppeteer/extract-zip chain in WORK-SECURITY-REVIEW.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


EXPECTED_VERSIONS = {
    "whatsapp-web.js": "1.34.7",
    "puppeteer": "24.38.0",
    "puppeteer-core": "24.38.0",
    "@puppeteer/browsers": "2.13.0",
    "extract-zip": "2.0.1",
}
EXPECTED_VULNERABILITIES = set(EXPECTED_VERSIONS)
EXPECTED_ADVISORIES = {
    "https://github.com/advisories/GHSA-jmr9-qjv8-65gv",
    "https://github.com/advisories/GHSA-7pqw-9j4j-h8q3",
}
EXPECTED_EDGES = {
    "whatsapp-web.js": {"puppeteer"},
    "puppeteer": {"@puppeteer/browsers", "puppeteer-core"},
    "puppeteer-core": {"@puppeteer/browsers"},
    "@puppeteer/browsers": {"extract-zip"},
    # npm represents advisory records in `via` using the affected package name.
    "extract-zip": {"extract-zip"},
}


class GateError(ValueError):
    pass


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GateError(f"JSON root must be an object: {path}")
    return value


def _locked_versions(lock: dict) -> dict[str, str]:
    packages = lock.get("packages")
    if not isinstance(packages, dict):
        raise GateError("lockfile packages map missing")
    found = {}
    for name in EXPECTED_VERSIONS:
        entry = packages.get(f"node_modules/{name}")
        if not isinstance(entry, dict) or not isinstance(entry.get("version"), str):
            raise GateError(f"locked package missing: {name}")
        found[name] = entry["version"]
    return found


def _via_names_and_urls(vulnerability: dict) -> tuple[set[str], set[str]]:
    names: set[str] = set()
    urls: set[str] = set()
    via = vulnerability.get("via")
    if not isinstance(via, list):
        raise GateError("audit vulnerability via field must be a list")
    for item in via:
        if isinstance(item, str):
            names.add(item)
        elif isinstance(item, dict):
            name, url = item.get("name"), item.get("url")
            if isinstance(name, str):
                names.add(name)
            if isinstance(url, str):
                urls.add(url)
        else:
            raise GateError("audit vulnerability via entry is malformed")
    return names, urls


def evaluate(audit: dict, lock: dict) -> str:
    vulnerabilities = audit.get("vulnerabilities")
    metadata = audit.get("metadata")
    counts = metadata.get("vulnerabilities") if isinstance(metadata, dict) else None
    if not isinstance(vulnerabilities, dict) or not isinstance(counts, dict):
        raise GateError("npm audit vulnerability data missing")

    total = counts.get("total")
    if not isinstance(total, int) or total < 0:
        raise GateError("npm audit total is invalid")
    if total == 0:
        if vulnerabilities:
            raise GateError("clean audit count disagrees with vulnerability map")
        return "CLEAN"

    if counts.get("critical", 0) != 0:
        raise GateError("critical npm vulnerability present")
    if set(vulnerabilities) != EXPECTED_VULNERABILITIES or total != 5:
        raise GateError("npm vulnerability set differs from reviewed exception")
    if any(v.get("severity") != "high" for v in vulnerabilities.values() if isinstance(v, dict)):
        raise GateError("reviewed vulnerabilities must remain exactly high severity")
    if any(not isinstance(v, dict) for v in vulnerabilities.values()):
        raise GateError("audit vulnerability entry is malformed")

    versions = _locked_versions(lock)
    if versions != EXPECTED_VERSIONS:
        raise GateError("locked versions differ from reviewed exception")

    advisory_urls: set[str] = set()
    for name, vulnerability in vulnerabilities.items():
        via_names, via_urls = _via_names_and_urls(vulnerability)
        advisory_urls.update(via_urls)
        if via_names != EXPECTED_EDGES[name]:
            raise GateError(f"dependency edge differs for {name}")
    if advisory_urls != EXPECTED_ADVISORIES:
        raise GateError("advisory identifiers differ from reviewed exception")
    return "KNOWN_OPEN_EXCEPTION"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = evaluate(_load_json(args.audit), _load_json(args.lock))
    except GateError as exc:
        print(f"ARGOS_NPM_AUDIT_REGRESSION=RED reason={exc}", file=sys.stderr)
        return 1
    print(f"ARGOS_NPM_AUDIT_REGRESSION=PASS status={result}")
    if result != "CLEAN":
        print("ARGOS_RELEASE_SECURITY=OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
