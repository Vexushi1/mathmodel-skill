import importlib.util
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    spec = importlib.util.spec_from_file_location(
        "resolve_workflow", ROOT / "scripts/resolve_workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )

    def test_output_contract(self):
        contract = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )
        per_question = contract["per_question"]
        self.assertEqual(per_question["question_directory"], "结果数据表/问题{中文序号}/")
        self.assertEqual(per_question["matlab_script"], "q{阿拉伯序号}_plot.m")
        self.assertEqual(per_question["figure_directory"], "图表/")
        self.assertEqual(
            per_question["mandatory_workbooks"]["solution"],
            "问题{中文序号}求解结果.xlsx",
        )
        self.assertEqual(
            per_question["mandatory_workbooks"]["sensitivity_robustness"],
            "问题{中文序号}敏感性与鲁棒性结果.xlsx",
        )

    def test_latex_cleanup_precedes_compile(self):
        latex_route = self.router["routing"]["latex"]["load"]
        self.assertLess(
            latex_route.index("modules/05_writing/ai_cleanup.md"),
            latex_route.index("modules/05_latex_compile_quality.md"),
        )

    def test_no_legacy_route(self):
        text = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        self.assertNotIn("legacy/", text)

    def test_default_load_includes_manifest(self):
        self.assertIn("core/module_manifest.yaml", self.router["default_load"])

    def test_full_solution_reaches_solver(self):
        route = self.router["routing"]["full_solution"]
        sequence = route["load"] + route["then"]
        self.assertLess(sequence.index("modules/01_problem_audit.md"), sequence.index("modules/02_model_design.md"))
        self.assertLess(sequence.index("modules/02_model_design.md"), sequence.index("modules/03_solve_validate.md"))

    def test_full_workflow_reaches_review_in_order(self):
        route = self.router["routing"]["full_workflow"]
        sequence = route["load"] + route["then"]
        expected = [
            "modules/01_problem_audit.md", "modules/02_model_design.md",
            "modules/03_solve_validate.md", "modules/04_figure_evidence.md",
            "modules/05_writing/docx.md", "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md", "modules/05_latex_compile_quality.md",
            "modules/06_review_delivery.md",
        ]
        positions = [sequence.index(item) for item in expected]
        self.assertEqual(positions, sorted(positions))

    def test_resolver_expands_primary_secondary_and_competition(self):
        resolver = load_resolver()
        plan = resolver.resolve_workflow(
            "full_solution",
            primary="mechanism",
            secondary=["optimization"],
            competition="CUMCM",
        )
        self.assertIn("packs/task/mechanism.md", plan["packs"])
        self.assertIn("packs/task/optimization.md", plan["packs"])
        self.assertIn("packs/competition/cumcm.md", plan["packs"])
        self.assertEqual(plan["load_order"].count("packs/task/mechanism.md"), 1)

    def test_resolver_rejects_too_many_task_packs(self):
        resolver = load_resolver()
        with self.assertRaisesRegex(ValueError, "at most"):
            resolver.resolve_workflow(
                "full_solution",
                primary="mechanism",
                secondary=["optimization", "simulation", "spatial"],
            )


if __name__ == "__main__":
    unittest.main()
