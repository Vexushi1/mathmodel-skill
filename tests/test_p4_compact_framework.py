from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "instantiate_model_paper_framework.py"
OUTPUT = ROOT / "core" / "output_contract.yaml"
BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"


def load_module():
    spec = importlib.util.spec_from_file_location("p4_framework_instantiator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestP4CompactFramework(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()
        cls.contract = yaml.safe_load(OUTPUT.read_text(encoding="utf-8"))["model_paper_framework"]

    def test_contract_default_now_has_an_executable_projection(self):
        self.assertEqual(self.contract["default_mode"], "compact")
        compact = self.mod.instantiate()
        self.assertEqual(self.mod.infer_mode(compact), "compact")
        self.assertEqual(self.mod.validate_projection(compact, "compact"), [])

    def test_compact_contains_only_contract_common_top_level_sections(self):
        compact = self.mod.instantiate("compact")
        parts = self.mod.split_top_level(compact)
        expected = tuple(self.contract["modes"]["compact"]["required_sections"])
        self.assertEqual(parts.order, expected)
        for forbidden in ("论文整体框架", "综合检验与跨问判断", "同步检查"):
            self.assertNotIn(forbidden, parts.sections)
        self.assertIn("### Terminology Registry", compact)
        self.assertIn("### Numeric Profile", compact)
        self.assertIn("#### 当前模型口径", compact)
        self.assertIn("#### 结果摘要", compact)

    def test_full_projection_keeps_canonical_superset_and_validates(self):
        full = self.mod.instantiate("full")
        parts = self.mod.split_top_level(full)
        self.assertEqual(self.mod.infer_mode(full), "full")
        self.assertIn("论文整体框架", parts.sections)
        self.assertIn("综合检验与跨问判断", parts.sections)
        self.assertIn("同步检查", parts.sections)
        self.assertIn("### 命题与证明规划", full)
        self.assertEqual(self.mod.validate_projection(full, "full"), [])

    def test_compact_to_full_preserves_every_common_section_byte_for_byte(self):
        compact = self.mod.instantiate("compact").replace("- 研究对象：", "- 研究对象：药材", 1)
        before = self.mod.split_top_level(compact)
        expanded = self.mod.expand_to_full(compact)
        after = self.mod.split_top_level(expanded)
        for name in before.order:
            with self.subTest(section=name):
                self.assertEqual(before.sections[name], after.sections[name])
        self.assertEqual(self.mod.infer_mode(expanded), "full")
        self.assertIn("研究对象：药材", expanded)

    def test_full_transition_is_idempotent(self):
        expanded = self.mod.expand_to_full(self.mod.instantiate("compact"))
        self.assertEqual(self.mod.transition(expanded, "full"), expanded)

    def test_full_to_compact_is_fail_closed(self):
        with self.assertRaisesRegex(self.mod.FrameworkInstantiationError, "full->compact"):
            self.mod.transition(self.mod.instantiate("full"), "compact")

    def test_unknown_duplicate_and_mode_inconsistent_compact_fail_closed(self):
        compact = self.mod.instantiate("compact")
        cases = (
            compact + "\n## 私有未登记块\n不要静默保留。\n",
            compact + "\n## 当前有效口径\n重复。\n",
            compact + "\n## 论文整体框架\n不应存在于 compact live framework。\n",
        )
        for text in cases:
            with self.subTest(kind=text[-30:]):
                with self.assertRaises(self.mod.FrameworkInstantiationError):
                    self.mod.expand_to_full(text)

    def test_fenced_fake_h2_is_not_treated_as_a_real_section(self):
        compact = self.mod.instantiate("compact")
        fake = compact.replace(
            "## 待办与缺口",
            "```text\n## 伪标题\n```\n\n## 待办与缺口",
            1,
        )
        parts = self.mod.split_top_level(fake)
        self.assertNotIn("伪标题", parts.sections)
        self.assertIn("待办与缺口", parts.sections)

    def test_cli_defaults_to_compact_and_expands_without_touching_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            compact = root / "framework.md"
            expanded = root / "full.md"
            create = subprocess.run(
                [sys.executable, str(SCRIPT), "new", "--output", str(compact)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            self.assertEqual(self.mod.infer_mode(compact.read_text(encoding="utf-8")), "compact")
            transition = subprocess.run(
                [sys.executable, str(SCRIPT), "expand", str(compact), "--output", str(expanded)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(transition.returncode, 0, transition.stdout + transition.stderr)
            self.assertEqual(self.mod.infer_mode(expanded.read_text(encoding="utf-8")), "full")
            self.assertFalse((root / "state").exists())

    def test_bootstrap_exposes_framework_instantiation_entrypoint(self):
        bootstrap = yaml.safe_load(BOOTSTRAP.read_text(encoding="utf-8"))
        self.assertEqual(
            bootstrap["entrypoints"]["instantiate_framework"],
            "python scripts/instantiate_model_paper_framework.py",
        )


if __name__ == "__main__":
    unittest.main()
