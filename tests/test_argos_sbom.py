import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("argos_sbom", ROOT / "tools/scripts/argos_sbom.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def fixture():
    return {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:random",
        "version": 1,
        "metadata": {"timestamp": "random", "properties": []},
        "components": [{"type": "library", "name": "fixture", "version": "1"}],
        "dependencies": [{"ref": "fixture@1", "dependsOn": []}],
    }


class DeterministicSbomTests(unittest.TestCase):
    SHA = "a" * 40
    LOCK = b'{"lockfileVersion":3}\n'

    def test_random_npm_fields_normalize_to_identical_bytes(self):
        first = fixture()
        second = fixture()
        second["serialNumber"] = "urn:uuid:different"
        second["metadata"]["timestamp"] = "later"
        self.assertEqual(
            MODULE.normalize(first, self.LOCK, self.SHA, 1_700_000_000),
            MODULE.normalize(second, self.LOCK, self.SHA, 1_700_000_000),
        )

    def test_source_and_lock_are_bound_without_secret_material(self):
        result = json.loads(MODULE.normalize(fixture(), self.LOCK, self.SHA, 0))
        props = {p["name"]: p["value"] for p in result["metadata"]["properties"]}
        self.assertEqual(props["argos:source:git-sha"], self.SHA)
        self.assertEqual(
            props["argos:source:package-lock-sha256"], MODULE.digest(self.LOCK)
        )
        self.assertEqual(result["metadata"]["timestamp"], "1970-01-01T00:00:00Z")

    def test_sha_or_schema_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            MODULE.normalize(fixture(), self.LOCK, "short", 0)
        invalid = copy.deepcopy(fixture())
        invalid["specVersion"] = "1.4"
        with self.assertRaises(ValueError):
            MODULE.normalize(invalid, self.LOCK, self.SHA, 0)

    def test_missing_inventory_fails_closed(self):
        invalid = fixture()
        del invalid["components"]
        with self.assertRaises(ValueError):
            MODULE.normalize(invalid, self.LOCK, self.SHA, 0)
