from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.scripts import argos_secret_scan


class ExactTreeSecretScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email", "fixture@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "ARGOS fixture"], check=True
        )

    def commit(self, name: str, body: bytes) -> str:
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        subprocess.run(["git", "-C", str(self.repo), "add", "--", name], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", name], check=True)
        return subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()

    def test_safe_exact_tree_is_green(self) -> None:
        sha = self.commit("safe.txt", b"ARGOS_API_KEY=<machine-local-secret>\n")
        self.assertEqual(argos_secret_scan.scan(self.repo, sha), [])

    def test_dirty_worktree_cannot_change_exact_revision_result(self) -> None:
        sha = self.commit("safe.txt", b"safe\n")
        (self.repo / "safe.txt").write_text("ghp_" + "A" * 36 + "\n")
        self.assertEqual(argos_secret_scan.scan(self.repo, sha), [])

    def test_token_is_reported_without_matching_material(self) -> None:
        token = "ghp_" + "A" * 36
        sha = self.commit("credential.txt", (token + "\n").encode())
        findings = argos_secret_scan.scan(self.repo, sha)
        self.assertEqual(findings, [("credential.txt", 1, "github-token")])
        self.assertNotIn(token, repr(findings))

    def test_gmail_app_password_shape_is_blocked(self) -> None:
        value = " ".join(["a" * 4, "b" * 4, "c" * 4, "d" * 4])
        sha = self.commit("notes.md", f"GMAIL_APP_PASSWORD={value}\n".encode())
        self.assertEqual(argos_secret_scan.scan(self.repo, sha)[0][2], "gmail-app-password")

    def test_binary_blob_is_scanned_without_rendering_secret(self) -> None:
        token = b"ghp_" + b"A" * 36
        sha = self.commit("image.bin", b"\x00" + token)
        findings = argos_secret_scan.scan(self.repo, sha)
        self.assertEqual(findings, [("image.bin", 1, "github-token")])
        self.assertNotIn(token.decode(), repr(findings))

    def test_history_scan_retains_redacted_revision_finding(self) -> None:
        token = "ghp_" + "A" * 36
        self.commit("credential.txt", (token + "\n").encode())
        current = self.commit("credential.txt", b"<REDACTED-ROTATE-REQUIRED>\n")
        self.assertEqual(argos_secret_scan.scan(self.repo, current), [])
        findings = argos_secret_scan.scan_history(self.repo)
        self.assertEqual(findings, [("credential.txt", 1, "github-token")])
        self.assertNotIn(token, repr(findings))
