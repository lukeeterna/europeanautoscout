#!/usr/bin/env python3
"""Fail closed on strong secret signatures in an exact Git tree.

Only path, line and rule name are emitted. Matching material is never printed.
Historical revocation/scrubbing is a separate gate; this scanner prevents new
current-tree exposure without reading untracked machine files.
"""
from __future__ import annotations

import argparse
import io
import re
import subprocess
from pathlib import Path


RULES = {
    "github-token": re.compile(
        rb"(?<![A-Za-z0-9_])(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
    ),
    "openai-key": re.compile(rb"(?<![A-Za-z0-9_])sk-(?!or-v1-)[A-Za-z0-9_-]{20,}"),
    "openrouter-key": re.compile(rb"(?<![A-Za-z0-9_])sk-or-v1-[A-Za-z0-9_-]{20,}"),
    "telegram-token": re.compile(rb"(?<![0-9])\d{8,10}:AA[A-Za-z0-9_-]{30,}"),
    "aws-access-key": re.compile(rb"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    "gmail-app-password": re.compile(
        rb"(?i)(?:GMAIL[A-Z0-9_]*PASSWORD|GMAIL_[A-Z0-9_]*PWD)\s*=\s*"
        rb"[`\"']?[a-z]{4}(?:\s+[a-z]{4}){3}(?![a-z])"
    ),
    "authorization-bearer": re.compile(
        rb"(?i)Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{20,}"
    ),
    "authorization-basic": re.compile(
        rb"(?i)Authorization\s*:\s*Basic\s+[A-Za-z0-9+/]{20,}={0,2}"
    ),
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

PREFILTERS = {
    "github-token": (b"ghp_", b"github_pat_"),
    "openai-key": (b"sk-",),
    "openrouter-key": (b"sk-or-v1-",),
    "telegram-token": (b":AA",),
    "aws-access-key": (b"AKIA",),
    "gmail-app-password": (b"GMAIL", b"gmail"),
    "authorization-bearer": (b"uthorization", b"UTHORIZATION"),
    "authorization-basic": (b"uthorization", b"UTHORIZATION"),
    "private-key": (b"PRIVATE KEY",),
}


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _blobs(repo: Path, shas: list[str]) -> list[bytes]:
    process = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input="".join(f"{sha}\n" for sha in shas).encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    output = io.BytesIO(process.stdout)
    bodies: list[bytes] = []
    for expected in shas:
        header = output.readline().decode("ascii").strip().split()
        if len(header) != 3 or header[0] != expected or header[1] != "blob":
            raise ValueError("unexpected git cat-file response")
        size = int(header[2])
        body = output.read(size)
        if len(body) != size or output.read(1) != b"\n":
            raise ValueError("truncated git cat-file response")
        bodies.append(body)
    return bodies


def _types(repo: Path, shas: list[str]) -> list[str]:
    process = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch-check=%(objecttype)"],
        input="".join(f"{sha}\n" for sha in shas).encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    result = process.stdout.decode("ascii").splitlines()
    if len(result) != len(shas):
        raise ValueError("unexpected git object type response")
    return result


def _scan_objects(repo: Path, objects: list[tuple[str, str]]) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for (path, _), body in zip(objects, _blobs(repo, [sha for _, sha in objects]), strict=True):
        for rule, pattern in RULES.items():
            if not any(marker in body for marker in PREFILTERS[rule]):
                continue
            for match in pattern.finditer(body):
                line = body.count(b"\n", 0, match.start()) + 1
                findings.append((path, line, rule))
    return sorted(findings)


def scan(repo: Path, rev: str) -> list[tuple[str, int, str]]:
    tree = _git(repo, "ls-tree", "-r", "-z", "--full-tree", rev)
    objects: list[tuple[str, str]] = []
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, obj_type, blob_sha = metadata.decode("ascii").split()
        if obj_type == "blob" and mode != "160000":
            path = raw_path.decode("utf-8", errors="surrogateescape")
            objects.append((path, blob_sha))
    return _scan_objects(repo, objects)


def scan_history(repo: Path) -> list[tuple[str, int, str]]:
    raw = _git(repo, "rev-list", "--objects", "--all").decode(
        "utf-8", errors="surrogateescape"
    )
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        sha, separator, path = line.partition(" ")
        if sha in seen:
            continue
        seen.add(sha)
        candidates.append((path if separator else f"object-{sha}", sha))
    types = _types(repo, [sha for _, sha in candidates])
    blobs = [item for item, obj_type in zip(candidates, types, strict=True) if obj_type == "blob"]
    return _scan_objects(repo, blobs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        resolved = _git(repo, "rev-parse", "--verify", f"{args.rev}^{{commit}}")
    except subprocess.CalledProcessError:
        print("SECRET_SCAN=BLOCKED_INVALID_REV")
        return 2
    sha = resolved.decode("ascii").strip()
    try:
        findings = scan_history(repo) if args.history else scan(repo, sha)
    except (subprocess.CalledProcessError, ValueError, UnicodeError):
        print("SECRET_SCAN=BLOCKED_GIT_READ")
        return 2
    for path, line, rule in findings:
        print(f"SECRET_FINDING={path}:{line}:{rule}:REDACTED")
    label = "HISTORY_SECRET_SCAN" if args.history else "SECRET_SCAN"
    if findings:
        print(f"{label}=RED SHA={sha} FINDINGS={len(findings)}")
        return 1
    print(f"{label}=GREEN SHA={sha} FINDINGS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
