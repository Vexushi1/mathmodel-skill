"""Parser equivalence, bounded reuse and current-byte isolation."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import safe_yaml
from runtime_assurance import ProjectStateSnapshot, ProjectStateReadError


class SafeYamlTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {"HSK_YAML_PURE_PYTHON": "0", "HSK_YAML_DISABLE_CACHE": "0"})
        environment.start()
        self.addCleanup(environment.stop)
        safe_yaml.clear_cache()
        self.addCleanup(safe_yaml.clear_cache)

    def test_safe_python_and_c_values_match_on_ordinary_yaml(self) -> None:
        documents = ["", "# empty\n", "null\n", "[1, true, null, 2.5]\n",
                     "name: 数学\nwhen: 2024-02-29\nvalues: &values [1, 2]\ncopy: *values\n",
                     "defaults: &defaults {a: 1}\nmerged: {<<: *defaults, b: 2}\n"]
        for text in documents:
            expected = yaml.safe_load(text)
            for use_c in (False, True):
                with self.subTest(text=text, use_c=use_c):
                    self.assertEqual(safe_yaml.safe_load(text, use_c=use_c), expected)

    def test_unsafe_tags_and_invalid_yaml_never_enter_cache(self) -> None:
        for text in ("!!python/object/apply:os.system ['echo unsafe']", "value: [1, 2"):
            for use_c in (False, True):
                with self.subTest(text=text, use_c=use_c):
                    with self.assertRaises(yaml.YAMLError):
                        safe_yaml.safe_load(text, use_c=use_c)
                    self.assertEqual(safe_yaml.cache_info()["entries"], 0)
        with self.assertRaises(UnicodeDecodeError):
            safe_yaml.safe_load(b"name: \xff")

    def test_results_do_not_share_mutable_subtrees(self) -> None:
        text = "items: &items [{nested: [1]}]\ncopy: *items\n"
        first = safe_yaml.safe_load(text)
        first["items"][0]["nested"].append(9)
        first["new"] = True
        second = safe_yaml.safe_load(text)
        self.assertEqual(second["items"][0]["nested"], [1])
        self.assertNotIn("new", second)
        self.assertIs(second["items"], second["copy"])
        self.assertIsNot(first["items"], second["items"])

    def test_file_content_change_with_same_mtime_is_not_reused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.yaml"
            path.write_text("value: 1\n", encoding="utf-8")
            original = path.stat()
            self.assertEqual(safe_yaml.safe_load(path.read_bytes()), {"value": 1})
            path.write_text("value: 2\n", encoding="utf-8")
            os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
            self.assertEqual(path.stat().st_mtime_ns, original.st_mtime_ns)
            self.assertEqual(safe_yaml.safe_load(path.read_bytes()), {"value": 2})

    def test_hash_collision_still_compares_actual_bytes(self) -> None:
        with patch.object(safe_yaml.hashlib, "sha256") as digest:
            digest.return_value.hexdigest.return_value = "collision"
            self.assertEqual(safe_yaml.safe_load("value: 1"), {"value": 1})
            self.assertEqual(safe_yaml.safe_load("value: 2"), {"value": 2})
            self.assertEqual(safe_yaml.safe_load("value: 1"), {"value": 1})

    def test_cache_bounds_and_large_document_bypass(self) -> None:
        with patch.object(safe_yaml, "MAX_CACHE_ENTRIES", 2), \
                patch.object(safe_yaml, "MAX_CACHE_BYTES", 24), \
                patch.object(safe_yaml, "MAX_ENTRY_BYTES", 20):
            for value in range(5):
                self.assertEqual(safe_yaml.safe_load(f"value: {value}\n"), {"value": value})
                self.assertLessEqual(safe_yaml.cache_info()["entries"], 2)
                self.assertLessEqual(safe_yaml.cache_info()["source_bytes"], 24)
            before = safe_yaml.cache_info()
            self.assertEqual(safe_yaml.safe_load("value: " + "x" * 21)["value"], "x" * 21)
            self.assertEqual(safe_yaml.cache_info(), before)

    def test_environment_rollback_and_c_extension_fallback(self) -> None:
        with patch.dict(os.environ, {"HSK_YAML_PURE_PYTHON": "1", "HSK_YAML_DISABLE_CACHE": "1"}):
            self.assertEqual(safe_yaml.loader_name(), "SafeLoader")
            self.assertEqual(safe_yaml.safe_load("value: 1"), {"value": 1})
            self.assertEqual(safe_yaml.cache_info()["entries"], 0)
        with patch.dict(yaml.__dict__):
            yaml.__dict__.pop("CSafeLoader", None)
            self.assertEqual(safe_yaml.loader_name(use_c=True), "SafeLoader")
            self.assertEqual(safe_yaml.safe_load("value: 2", use_c=True), {"value": 2})

    @unittest.skipUnless(hasattr(yaml, "CSafeLoader"), "PyYAML C extension is unavailable")
    def test_loader_semantics_have_distinct_cache_entries(self) -> None:
        safe_yaml.safe_load("value: 1", use_c=False)
        safe_yaml.safe_load("value: 1", use_c=True)
        self.assertEqual(safe_yaml.cache_info()["entries"], 2)

    def test_threaded_callers_get_independent_values(self) -> None:
        def load_and_mutate(index: int) -> tuple[int, list[int]]:
            value = safe_yaml.safe_load("nested: {items: [0]}\n")
            value["nested"]["items"].append(index)
            return index, value["nested"]["items"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(load_and_mutate, range(32)))
        self.assertEqual(rows, [(index, [0, index]) for index in range(32)])
        self.assertEqual(safe_yaml.safe_load("nested: {items: [0]}\n"), {"nested": {"items": [0]}})

    def test_snapshot_payload_is_fresh_and_currentness_still_rejects_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()
            path = root / "state/project_state.yaml"
            path.write_text("project: {name: original}\n", encoding="utf-8")
            snapshot = ProjectStateSnapshot.capture(root)
            snapshot.payload()["project"]["name"] = "mutated"
            self.assertEqual(snapshot.payload()["project"]["name"], "original")
            path.write_text("project: {name: changed}\n", encoding="utf-8")
            with self.assertRaises(ProjectStateReadError):
                snapshot.assert_current()


if __name__ == "__main__":
    unittest.main()
