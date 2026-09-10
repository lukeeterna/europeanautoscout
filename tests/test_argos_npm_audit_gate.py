import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "argos_npm_audit_gate", ROOT / "tools/scripts/argos_npm_audit_gate.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def reviewed_audit():
    vulnerabilities = {}
    for name, edges in MODULE.EXPECTED_EDGES.items():
        via = sorted(edges)
        if name == "extract-zip":
            via = [
                {"name": "extract-zip", "url": url}
                for url in sorted(MODULE.EXPECTED_ADVISORIES)
            ]
        vulnerabilities[name] = {"severity": "high", "via": via}
    return {
        "metadata": {
            "vulnerabilities": {
                "info": 0,
                "low": 0,
                "moderate": 0,
                "high": 5,
                "critical": 0,
                "total": 5,
            }
        },
        "vulnerabilities": vulnerabilities,
    }


def reviewed_lock():
    return {
        "packages": {
            f"node_modules/{name}": {"version": version}
            for name, version in MODULE.EXPECTED_VERSIONS.items()
        }
    }


class NpmAuditRegressionGateTests(unittest.TestCase):
    def test_clean_report_passes(self):
        audit = {"metadata": {"vulnerabilities": {"total": 0}}, "vulnerabilities": {}}
        self.assertEqual(MODULE.evaluate(audit, reviewed_lock()), "CLEAN")

    def test_exact_reviewed_chain_remains_open_but_passes_regression_gate(self):
        self.assertEqual(
            MODULE.evaluate(reviewed_audit(), reviewed_lock()), "KNOWN_OPEN_EXCEPTION"
        )

    def test_new_vulnerability_fails_closed(self):
        audit = reviewed_audit()
        audit["vulnerabilities"]["new-package"] = {"severity": "high", "via": []}
        audit["metadata"]["vulnerabilities"]["total"] = 6
        with self.assertRaises(MODULE.GateError):
            MODULE.evaluate(audit, reviewed_lock())

    def test_critical_escalation_fails_closed(self):
        audit = reviewed_audit()
        audit["metadata"]["vulnerabilities"]["critical"] = 1
        with self.assertRaises(MODULE.GateError):
            MODULE.evaluate(audit, reviewed_lock())

    def test_dependency_edge_change_fails_closed(self):
        audit = reviewed_audit()
        audit["vulnerabilities"]["puppeteer"]["via"].append("unexpected")
        with self.assertRaises(MODULE.GateError):
            MODULE.evaluate(audit, reviewed_lock())

    def test_locked_version_change_requires_review(self):
        lock = copy.deepcopy(reviewed_lock())
        lock["packages"]["node_modules/whatsapp-web.js"]["version"] = "1.34.8"
        with self.assertRaises(MODULE.GateError):
            MODULE.evaluate(reviewed_audit(), lock)


if __name__ == "__main__":
    unittest.main()
