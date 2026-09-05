from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LINT = load_module("lint_skill_v871_fragment", SCRIPTS / "lint_skill.py")


class TestV871CriticalFragmentHealth(unittest.TestCase):
    def test_valid_markdown_fragment_passes(self):
        self.assertTrue(
            LINT._critical_fragment_exists(
                "templates/model/model_paper_framework.md#逐问写作能力预检"
            )
        )

    def test_numbered_markdown_fragment_normalizes_to_heading(self):
        self.assertTrue(
            LINT._critical_fragment_exists(
                "modules/05_writing/latex.md#5-图表命题和算法环境"
            )
        )

    def test_missing_markdown_fragment_fails(self):
        self.assertFalse(
            LINT._critical_fragment_exists(
                "modules/05_writing/latex.md#definitely-missing-fragment-v871"
            )
        )

    def test_valid_yaml_fragment_passes(self):
        self.assertTrue(
            LINT._critical_fragment_exists(
                "core/writing_reasoning_contract.yaml#adaptive_core_model_summary"
            )
        )

    def test_dynamic_yaml_fragment_validates_static_and_dynamic_path(self):
        self.assertTrue(
            LINT._critical_fragment_exists(
                "config/competition_profiles.yaml#profiles.<name>.edition_rules"
            )
        )

    def test_missing_file_fails(self):
        self.assertFalse(
            LINT._critical_fragment_exists(
                "core/definitely_missing_v871.yaml#anything"
            )
        )

    def test_active_critical_registry_scan_is_clean(self):
        errors: list[str] = []
        LINT._check_critical_pointer_fragments(errors)
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
