#!/usr/bin/env python3
"""Normalize npm CycloneDX output into an exact-source deterministic SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import uuid


SHA_RE = re.compile(r"[0-9a-f]{40}")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(raw: dict, lock_bytes: bytes, source_sha: str, source_epoch: int) -> bytes:
    if not SHA_RE.fullmatch(source_sha):
        raise ValueError("full lowercase source SHA required")
    if source_epoch < 0:
        raise ValueError("source epoch must be nonnegative")
    if raw.get("bomFormat") != "CycloneDX" or raw.get("specVersion") != "1.5":
        raise ValueError("CycloneDX 1.5 input required")
    if not isinstance(raw.get("components"), list) or not isinstance(raw.get("dependencies"), list):
        raise ValueError("SBOM components/dependencies missing")
    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("SBOM metadata missing")

    lock_sha = digest(lock_bytes)
    stable = json.loads(json.dumps(raw))
    stable["serialNumber"] = "urn:uuid:" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"argos:{source_sha}:{lock_sha}")
    )
    stable["metadata"]["timestamp"] = (
        datetime.fromtimestamp(source_epoch, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    properties = stable["metadata"].setdefault("properties", [])
    if not isinstance(properties, list):
        raise ValueError("SBOM metadata properties must be a list")
    properties.extend(
        [
            {"name": "argos:source:git-sha", "value": source_sha},
            {"name": "argos:source:package-lock-sha256", "value": lock_sha},
        ]
    )
    properties.sort(key=lambda item: (item.get("name", ""), item.get("value", "")))
    return (json.dumps(stable, sort_keys=True, indent=2) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-date-epoch", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    data = normalize(raw, args.lock.read_bytes(), args.source_sha, args.source_date_epoch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    checksum = args.output.with_suffix(args.output.suffix + ".sha256")
    checksum.write_text(f"{digest(data)}  {args.output.name}\n", encoding="utf-8")
    print(f"ARGOS_SBOM=PASS COMPONENTS={len(raw['components'])} SHA256={digest(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
