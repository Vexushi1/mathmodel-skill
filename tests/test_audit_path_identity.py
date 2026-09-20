"""An equivalent root spelling must not change provenance or hide required files."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from artifact_fingerprint import combined_hash
from project_snapshot import data_source_files
from hsk_pack_submission import _expand_allowlist, build_manifest


class CanonicalPathIdentityTests(unittest.TestCase):
    def test_equivalent_root_spellings_preserve_file_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "nested").mkdir()
            alias = root / "nested" / ".."
            data = root / "data.csv"
            data.write_text("x\n1\n", encoding="utf-8")
            self.assertEqual(combined_hash([alias / "data.csv"], alias), combined_hash([data], root))
            files, _, issues, _ = data_source_files(alias, {"data": {"sources": [{"path": "data.csv"}]}})
            self.assertEqual(issues, [])
            self.assertEqual(files, [data])
            self.assertEqual(_expand_allowlist(alias, ["data.csv"]), [data])
            manifest = build_manifest(alias, [data], kind="official", metadata={})
            self.assertEqual(manifest["files"][0]["path"], "data.csv")
            _, _, issues, _ = data_source_files(alias, {"data": {"sources": [{"path": "../outside.csv"}]}})
            self.assertTrue(issues)

    def test_measurement_normalizes_canonical_and_supplied_root(self):
        spec = importlib.util.spec_from_file_location("audit_path_baseline", ROOT / "tests/optimization_baseline.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "nested").mkdir()
            alias = root / "nested" / ".."
            normalized = helper.normalize([str(root), str(alias)], ROOT, alias)
            self.assertEqual(normalized, ["<PROJECT_ROOT>", "<PROJECT_ROOT>"])


if __name__ == "__main__":
    unittest.main()
