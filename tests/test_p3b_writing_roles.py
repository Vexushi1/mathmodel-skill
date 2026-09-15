from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_yaml(relative: str):
    return yaml.safe_load(read(relative))


def load_runtime_module():
    path = ROOT / "scripts" / "resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_p3b", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load resolve_runtime.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["resolve_runtime_p3b"] = module
    spec.loader.exec_module(module)
    return module


class P3BWritingRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime_contract = load_yaml("core/writing_runtime_contract.yaml")
        cls.cleanup = read("modules/05_writing/ai_cleanup.md")
        cls.review = read("modules/06_review_delivery.md")
        cls.protocol = read("modules/05_writing/paper_writing_protocol.md")
        cls.fixture = load_yaml("tests/fixtures/p3b_writing_role_source_map.yaml")
        cls.resolver = load_runtime_module()

    def test_consumer_surfaces_are_materially_smaller_without_shrinking_primary_protocol(self):
        caps = self.fixture["consumer_caps"]
        self.assertLess(len(self.cleanup.encode("utf-8")), caps["ai_cleanup_max_bytes"])
        self.assertLess(len(self.review.encode("utf-8")), caps["review_delivery_max_bytes"])
        self.assertGreater(len(self.protocol.encode("utf-8")), 50000)
        self.assertLess(len(self.cleanup.encode("utf-8")), self.fixture["baseline"]["ai_cleanup_bytes"])
        self.assertLess(len(self.review.encode("utf-8")), self.fixture["baseline"]["review_delivery_bytes"])

    def test_source_map_markers_remain_reachable(self):
        texts = {"cleanup": self.cleanup, "review": self.review, "protocol": self.protocol}
        for group, markers in self.fixture["protected_markers"].items():
            for marker in markers:
                with self.subTest(group=group, marker=marker):
                    self.assertIn(marker, texts[group])

    def test_fw05_planned_proposition_and_pseudocode_auto_activate_without_prompt_keyword(self):
        activation = self.runtime_contract["per_question_writing_capability_preflight"]["activation"]
        proposition = activation["proposition_proof"]["rules"]["planned"]["activate"]
        algorithm = activation["algorithm_presentation"]["rules"]["pseudocode"]["activate"]
        self.assertIn("core/writing_reasoning_contract.yaml", proposition)
        self.assertIn("packs/artifact/proposition_proof.md", proposition)
        self.assertIn("core/writing_reasoning_contract.yaml", algorithm)
        self.assertIn("packs/artifact/algorithm_flow.md", algorithm)
        self.assertIn("modules/05_writing/latex.md#5-图表命题和算法环境", algorithm)

    def test_fw06_missing_state_requires_adjudication(self):
        activation = self.runtime_contract["per_question_writing_capability_preflight"]["activation"]
        for family in ("core_model_summary", "proposition_proof", "algorithm_presentation"):
            with self.subTest(family=family):
                self.assertEqual("needs_adjudication", activation[family]["rules"]["missing"]["status"])
                self.assertIn("silently", activation[family]["rules"]["missing"]["prohibition"])

    def test_fw07_cleanup_cannot_delete_required_bridge_or_expand_local_scope(self):
        self.assertIn("不能仅因“不是最终模型公式”删除", self.cleanup)
        self.assertIn("局部修改默认只读当前目标 fragment", self.cleanup)
        self.assertIn("若只写单问，不需要为了“完整感”重新加载无关问题", self.protocol)
        self.assertIn("不能因为“顺便润色”重写无关章节", self.cleanup)

    def test_fw08_non_cumcm_and_docx_keep_full_reasoning_fallback(self):
        mcm = self.resolver.resolve_runtime("latex", competition="MCM")
        docx = self.resolver.resolve_runtime("docx", competition="CUMCM")
        for plan in (mcm, docx):
            self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        self.assertNotIn("templates/latex/cumcm/hsk/template_manifest.yaml", mcm["load_order"])

    def test_fw09_final_review_may_batch_but_must_cover_every_active_scope(self):
        self.assertIn("可按 physical file / question / check family 分批读取", self.review)
        self.assertIn("coverage ledger", self.review)
        self.assertIn("不得抽样几个章节就宣称全文通过", self.review)
        stages = [s["id"] for s in self.runtime_contract["template_first_progressive_authoring"]["stages"]]
        self.assertLess(stages.index("draft_semantic_review"), stages.index("ai_cleanup"))
        self.assertLess(stages.index("ai_cleanup"), stages.index("final_review_and_delivery"))

    def test_local_scope_expands_only_for_real_dependencies_or_full_review(self):
        self.assertIn("若只写单问，不需要为了“完整感”重新加载无关问题", self.protocol)
        self.assertIn("局部修改默认只读当前目标 fragment", self.cleanup)
        self.assertIn("只有跨问依赖", self.cleanup)
        self.assertIn("final review", self.cleanup)

    def test_cleanup_and_review_are_consumers_not_second_math_authorities(self):
        for text in (self.cleanup, self.review):
            self.assertIn("core/writing_reasoning_contract.yaml", text)
            self.assertIn("paper_writing_protocol.md", text)
            self.assertNotIn("formula_role_taxonomy:", text)
            self.assertNotIn("claim_strength_calibration:", text)


if __name__ == "__main__":
    unittest.main()
