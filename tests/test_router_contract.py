import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )

    def test_output_contract(self):
        text = (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        self.assertIn("结果数据表/问题{中文序号}/问题{中文序号}结果数据/", text)
        self.assertIn("问题{中文序号}求解结果.xlsx", text)
        self.assertIn("问题{中文序号}敏感性与鲁棒性结果.xlsx", text)

    def test_latex_compile_route(self):
        latex_route = self.router["routing"]["latex"]["load"]
        self.assertIn("modules/05_latex_compile_quality.md", latex_route)

    def test_no_legacy_route(self):
        text = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        self.assertNotIn("legacy/", text)

    def test_default_load_includes_manifest(self):
        self.assertIn("core/module_manifest.yaml", self.router["default_load"])

    def test_full_solution_reaches_solver(self):
        route = self.router["routing"]["full_solution"]
        sequence = route["load"] + route["then"]
        self.assertLess(
            sequence.index("modules/01_problem_audit.md"),
            sequence.index("modules/02_model_design.md"),
        )
        self.assertLess(
            sequence.index("modules/02_model_design.md"),
            sequence.index("modules/03_solve_validate.md"),
        )

    def test_full_workflow_reaches_review_in_order(self):
        route = self.router["routing"]["full_workflow"]
        sequence = route["load"] + route["then"]
        expected = [
            "modules/01_problem_audit.md",
            "modules/02_model_design.md",
            "modules/03_solve_validate.md",
            "modules/04_figure_evidence.md",
            "modules/05_writing/docx.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md",
            "modules/06_review_delivery.md",
        ]
        positions = [sequence.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
