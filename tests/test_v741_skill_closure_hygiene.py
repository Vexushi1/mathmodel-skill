import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POINTERS = {
    "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",
    "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",
    "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",
    "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",
}


def load_resolver():
    spec = importlib.util.spec_from_file_location("resolve_workflow_v741", ROOT / "scripts/resolve_workflow.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV741SkillClosureHygiene(unittest.TestCase):
    def test_compatibility_pointers_remain_read_only_and_outside_active_index(self):
        active_index = (ROOT / "SKILL_FILE_INDEX.md").read_text(encoding="utf-8")
        manifest = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
        for legacy, target in POINTERS.items():
            text = (ROOT / legacy).read_text(encoding="utf-8")
            self.assertIn("Compatibility Pointer", text)
            self.assertIn(target, text)
            self.assertNotIn(f"`{legacy}`", active_index)
            self.assertFalse(any(line.endswith(f"  {legacy}") for line in manifest.splitlines()))

    def test_default_router_stays_minimal(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.assertEqual(router["default_load"], ["core/hsk_core_policy.md"])
        self.assertEqual(router["load_policy"]["principle"], "minimal_route_specific")
        self.assertNotIn("core/writing_reasoning_contract.yaml", router["default_load"])

    def test_writing_authorities_are_route_specific(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        routes = router["routing"]
        self.assertIn("core/writing_reasoning_contract.yaml", routes["latex"]["load"])
        self.assertIn("core/writing_reasoning_contract.yaml", routes["docx"]["load"])
        self.assertNotIn("core/writing_reasoning_contract.yaml", routes["figures"]["load"])
        self.assertNotIn("core/writing_reasoning_contract.yaml", routes["returned_workbook_validation"]["load"])

    def test_current_writing_consumers_are_not_second_authorities(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        docx = (ROOT / "modules/05_writing/docx.md").read_text(encoding="utf-8")
        review = (ROOT / "modules/06_review_delivery.md").read_text(encoding="utf-8")
        self.assertIn("不建立第二套正文写作规则", cleanup)
        self.assertIn("不复制第二套正文规则", docx)
        self.assertIn("不重新定义正文写作规则", review)
        for text in (cleanup, docx, review):
            self.assertIn("core/writing_reasoning_contract.yaml", text)

    def test_model_design_has_no_fixed_assumption_or_proposition_hard_quota(self):
        text = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        self.assertIn("假设按必要性而非数量保留", text)
        self.assertIn("0--4 是默认正文阅读预算，不是绝对上限", text)
        self.assertNotIn("3--5 个关键假设", text)
        self.assertNotIn("不得超过 4 个", text)

    def test_resolver_still_resolves_latex_and_figures_without_missing_files(self):
        resolver = load_resolver()
        latex = resolver.resolve_workflow("latex", competition="CUMCM")
        figures = resolver.resolve_workflow("figures")
        self.assertFalse(latex["missing_prerequisites"], latex)
        self.assertFalse(figures["missing_prerequisites"], figures)
        self.assertIn("modules/05_writing/latex.md", latex["load_order"])
        self.assertIn("modules/04_figure_evidence.md", figures["load_order"])


if __name__ == "__main__":
    unittest.main()
