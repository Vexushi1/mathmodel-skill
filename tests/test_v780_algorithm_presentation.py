from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV780AlgorithmPresentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        cls.output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        cls.framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        cls.latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        cls.design = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        cls.pack = (ROOT / "packs/artifact/algorithm_flow.md").read_text(encoding="utf-8")
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))

    def test_algorithm_presentation_authority_is_adaptive(self):
        contract = self.reasoning["algorithm_presentation"]
        self.assertEqual(contract["governance_level"], "default")
        self.assertEqual(contract["modes"], ["not_needed", "stepwise", "pseudocode"])
        self.assertEqual(
            contract["closure_chain"],
            [
                "model_structure",
                "algorithm_trace",
                "paper_algorithm_presentation",
                "python_implementation",
                "workbook_result_or_validation",
            ],
        )
        self.assertIn("不把 Python 源码压缩成论文伪代码", contract["principle"])

    def test_algorithm_trace_has_model_code_result_anchors(self):
        trace = self.reasoning["algorithm_presentation"]["internal_trace"]
        required = set(trace["required_fields"])
        self.assertTrue(
            {"algorithm_id", "question", "role", "inputs", "core_operations", "termination", "outputs", "presentation_mode", "status"}.issubset(required)
        )
        optional = set(trace["optional_fields"])
        self.assertTrue({"formula_anchors", "proposition_anchors", "constraint_anchors", "code_anchors", "workbook_evidence"}.issubset(optional))

    def test_router_uses_precise_paper_algorithm_triggers(self):
        route = self.router["routing"]["algorithm_presentation"]
        for token in ("算法流程", "伪代码", "论文算法", "算法步骤"):
            self.assertIn(token, route["infer_keywords"])
        self.assertNotIn("算法", route["infer_keywords"])
        self.assertIn("packs/artifact/algorithm_flow.md", route["load"])
        self.assertIn("core/writing_reasoning_contract.yaml", route["load"])
        self.assertIn("modules/05_writing/latex.md", route["load"])
        self.assertEqual(route["delivery_scope"], "design")

    def test_framework_records_trace_without_new_state_schema_contract(self):
        self.assertIn("### Algorithm Trace", self.framework)
        self.assertIn("算法流程呈现：`not_needed / stepwise / pseudocode`", self.framework)
        self.assertIn("关联 Algorithm ID", self.framework)
        self.assertIn("Formula / Proposition / Constraint 锚点", self.framework)
        semantic_categories = self.schema["$defs"]["semantic_change_category"]["enum"]
        self.assertIn("algorithm", semantic_categories)
        self.assertNotIn("algorithm_trace", self.schema["properties"]["paper_framework"]["properties"])

    def test_latex_and_design_delegate_detailed_presentation_to_pack(self):
        for text in (self.latex, self.design):
            self.assertIn("not_needed", text)
            self.assertIn("stepwise", text)
            self.assertIn("pseudocode", text)
            self.assertIn("Algorithm Trace", text)
            self.assertIn("packs/artifact/algorithm_flow.md", text)
        self.assertIn("伪代码写数学对象与控制逻辑", self.latex)

    def test_pack_supports_both_requested_styles_without_raw_python(self):
        self.assertIn("控制流伪代码版", self.pack)
        self.assertIn("分阶段数学步骤版", self.pack)
        self.assertIn("range(len(...))", self.pack)
        self.assertIn("不把 Python 源码改写成缩进版论文", self.pack)
        self.assertIn("Algorithm Trace 不替代 Formula Trace", self.pack)

    def test_output_contract_exposes_single_authority_pointer(self):
        policy = self.output["writing_policy"]
        self.assertEqual(
            policy["algorithm_presentation_contract"],
            "core/writing_reasoning_contract.yaml#algorithm_presentation",
        )
        self.assertEqual(
            policy["carrier_specific"]["algorithm_flow"],
            "packs/artifact/algorithm_flow.md",
        )
        contract = self.output["algorithm_presentation_contract"]
        self.assertEqual(contract["modes"], ["not_needed", "stepwise", "pseudocode"])
        self.assertTrue(contract["no_new_project_state_field_required"])

    def test_upgrade_preserves_numerical_interfaces(self):
        self.assertEqual(
            self.output["per_question"]["exact_default_files"],
            [
                "问题{中文序号}求解.py",
                "问题{中文序号}求解结果.xlsx",
                "问题{中文序号}结果深化分析.py",
                "问题{中文序号}结果深化分析.xlsx",
                "q{阿拉伯序号}_plot.m",
            ],
        )
        self.assertEqual(self.output["semantic_governance"]["version"], "1.0.0")
        self.assertEqual(self.output["model_paper_framework"]["current_template_version"], "v0.8-project-memory")


if __name__ == "__main__":
    unittest.main()
