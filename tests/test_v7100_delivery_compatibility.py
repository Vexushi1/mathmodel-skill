from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/hsk_pack_submission.py"


def load_pack_module():
    spec = importlib.util.spec_from_file_location("pack_v7100_compat", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV7100DeliveryCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_pack_module()

    def test_legacy_no_mode_keeps_historical_default_output_path(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            project = workspace / "project"
            project.mkdir()
            (project / "artifact.txt").write_text("current", encoding="utf-8")
            previous = Path.cwd()
            os.chdir(workspace)
            try:
                with patch.object(sys, "argv", ["hsk_pack_submission.py", str(project)]):
                    self.assertEqual(self.pack.main(), 0)
            finally:
                os.chdir(previous)
            output = workspace / "hsk_submission_backup.zip"
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                manifest = yaml.safe_load(archive.read("submission_manifest.yaml").decode("utf-8"))
            self.assertEqual(manifest["kind"], "reproducibility")

    def test_explicit_reproducibility_mode_uses_new_project_local_default(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / "artifact.txt").write_text("current", encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                ["hsk_pack_submission.py", str(project), "--mode", "reproducibility"],
            ):
                self.assertEqual(self.pack.main(), 0)
            output = project / "submission/reproducibility.zip"
            self.assertTrue(output.is_file())

    def test_explicit_mode_rejects_output_outside_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "project"
            project.mkdir()
            outside = root / "outside.zip"
            with self.assertRaises(SystemExit):
                self.pack.resolve_output(
                    project,
                    str(outside),
                    mode="reproducibility",
                    legacy_compat=False,
                )


if __name__ == "__main__":
    unittest.main()
