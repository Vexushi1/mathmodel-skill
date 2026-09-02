import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_runtime_module():
    path = ROOT / "scripts" / "resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_v800", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(module)
    return module


class TestV800WritingRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime_module()
        cls.contract = yaml.safe_load(
            (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        )
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(
            encoding="utf-8"
        )
        cls.adapter = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")

    def test_contract_declares_template_first_runtime(self):
        self.assertEqual(self.contract["version"], "8.0.2")
        self.assertEqual(
            self.contract["canonical_template"]["manifest"],
            "templates/latex/cumcm/hsk/template_manifest.yaml",
        )
        self.assertEqual(
            self.contract["writing_module"]["protocol"],
            "modules/05_writing/paper_writing_protocol.md",
        )
        self.assertIn("主工作簿", self.contract["runtime_vocabulary_firewall"]["do_not_surface_as_paper_vocabulary"])
        self.assertEqual(self.contract["document_length_profile"]["default"], "adaptive_coverage_diagnostic")
        self.assertEqual(self.contract["template_override_provenance"]["default"], "none")
        self.assertIn("official_compliance_impact", self.contract["template_override_provenance"]["required_fields"])
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("Template Override（无则写 `none`）", framework)

    def test_pure_latex_runtime_does_not_preload_full_reasoning_authority(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        self.assertIn("core/writing_runtime_contract.yaml", plan["load_order"])
        self.assertIn("templates/latex/cumcm/hsk/template_manifest.yaml", plan["load_order"])
        self.assertIn("modules/05_writing/paper_writing_protocol.md", plan["load_order"])
        self.assertNotIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        self.assertEqual(plan["writing_runtime"]["mode"], "compact")
        self.assertFalse(plan["writing_runtime"]["full_reasoning_authority_preloaded"])

    def test_mixed_or_review_routes_keep_full_reasoning_authority(self):
        review = self.runtime.resolve_runtime("review", competition="CUMCM")
        self.assertIn("core/writing_reasoning_contract.yaml", review["load_order"])
        self.assertEqual(review["writing_runtime"]["mode"], "full_authority")
        self.assertTrue(review["writing_runtime"]["full_reasoning_authority_preloaded"])
        self.assertIn("templates/latex/cumcm/hsk/template_manifest.yaml", review["load_order"])

    def test_protocol_implements_v720_narrative_requirements(self):
        for token in (
            "Local Narrative Chain",
            "Paragraph Handoff Test",
            "Result → Validation Bridge",
            "MODEL → SOLVE → RESULT → VALIDATE",
            "目标函数单独展示",
            "内部工作流词汇防火墙",
            "页数只作为覆盖度诊断",
        ):
            self.assertIn(token, self.protocol)

    def test_latex_is_adapter_not_structure_authority(self):
        self.assertIn("LaTeX Adapter", self.adapter)
        self.assertIn("Template-First", self.adapter)
        self.assertIn("本文件不再拥有正文结构或表达规则", self.adapter)
        self.assertIn("目标函数不得为了大括号整齐而塞进约束系统", self.adapter)
        self.assertIn("template_id / instruction_source / override_scope", self.adapter)

    def test_v7_migration_is_manual_dry_run_and_never_overwrites_body(self):
        reasoning = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )
        migration = reasoning["v8_compatibility"]["project_migration"]
        self.assertFalse(migration["automatic_rewrite"])
        self.assertFalse(migration["overwrite_filled_body"])
        guide = (ROOT / migration["guide"]).read_text(encoding="utf-8")
        self.assertIn("默认 dry-run", guide)
        self.assertIn("任何冲突均停止", guide)


if __name__ == "__main__":
    unittest.main()
