import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestTooling(unittest.TestCase):
    def test_compile_profiles_are_complete(self):
        profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
        for name in ("cumcm", "mcm_icm", "diangong"):
            self.assertIn(name, profiles["profiles"])
            profile = profiles["profiles"][name]
            self.assertTrue(profile["sequence"])
            self.assertIn(profile["engine"], {"xelatex", "pdflatex", "lualatex"})
        self.assertIn("biber", profiles["profiles"]["cumcm"]["sequence"])

    def test_packager_excludes_multisuffix_latex_files(self):
        module = load_module("hsk_pack_submission", ROOT / "scripts/hsk_pack_submission.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "package.zip"
            for name in ("main.synctex.gz", "main.run.xml", "main.bcf", "main.pdf"):
                (root / name).write_text("x", encoding="utf-8")
            self.assertTrue(module.should_exclude(root / "main.synctex.gz", root, output))
            self.assertTrue(module.should_exclude(root / "main.run.xml", root, output))
            self.assertTrue(module.should_exclude(root / "main.bcf", root, output))
            self.assertFalse(module.should_exclude(root / "main.pdf", root, output))

    def test_matlab_templates_use_root_finder_and_font_fallback(self):
        plotting = (ROOT / "templates/matlab/plot_from_workbook.m").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        self.assertIn("hsk_find_project_root", plotting)
        self.assertIn("listfonts", style)
        self.assertIn("Noto Sans CJK SC", style)


if __name__ == "__main__":
    unittest.main()
